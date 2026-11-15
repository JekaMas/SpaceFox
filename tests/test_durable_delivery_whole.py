"""Current-format delivery retention over real local Git and loopback readback."""
from copy import deepcopy

from tests.test_autonomous_publisher_whole import AutonomousPublisherWholeTest, Service, git
from tests.test_current_motion_publisher import NOW
from tools.spacefox.cloud import Pages, Site, arm, delivery, delivery_files, journal, recover, snapshot_files
from tools.spacefox.native_motion import PROFILE, build_artifact
from tools.spacefox.publisher import Publisher


class DurableDeliveryWholeTest(AutonomousPublisherWholeTest):
    def candidate(self, pub, now=NOW):
        import json
        from tools.spacefox.catalog import canonical_bytes
        from tools.spacefox.native_motion import validate_artifact, with_text_transport
        logical = {k: v for k, v in self.template.items() if not k.endswith('.txt')}
        feed = json.loads(logical['feed.json'])
        feed['publisher'] = pub.publisher_envelope(now)
        logical['feed.json'] = canonical_bytes(feed)
        files = with_text_transport(logical)
        validate_artifact(files)
        return files

    def test_three_promotions_drop_first_closure_and_survive_adoption(self):
        with self.authority() as (source, remote, store, pub), Service().serving() as service:
            self.accept(pub)
            candidates = []
            for generation in (1, 2, 3):
                catalog = deepcopy(self.catalog)
                # Technical version differentiates real captured catalog content;
                # the verbatim launch and every display string remain unchanged.
                catalog['catalogVersion'] += f'.delivery{generation}'
                envelope = pub.publisher_envelope(NOW + generation)
                files, digest = build_artifact(pub.schedule, catalog, NOW + generation,
                                               publisher=envelope, root=self.fixture)
                revision = pub.prepare(pub.head, NOW + generation, files, digest,
                                       feed_publisher=envelope, artifact_profile=PROFILE)
                candidates.append(files)
                manifest = delivery(pub)
                service.files = delivery_files(pub, manifest)
                pub, intent = arm(pub, expected=pub.head, repository='local/spacefox',
                                  run_id=40 + generation, run_attempt=1,
                                  artifact_id=70 + generation, now=NOW + generation)
                pages = Pages('local/spacefox', 'local', api=service.url, local_http=True)
                pub = recover(pub, Site(service.url + '/site', local_http=True), pages)
                self.assertEqual(generation, pub.ledger['active']['generation'])
                self.assertIsNone(pub.ledger['pending'])
                self.assertEqual(NOW, pub.ledger['selection_validated_utc'])
                self.assertEqual(1, len(pub.ledger['requests']))
                self.assertEqual(revision.generation, generation)
            paths = [set(x) - {'feed.json', 'feed.json.txt'} for x in candidates]
            self.assertTrue(paths[0] - paths[1] - paths[2])
            delivered = delivery_files(pub, journal(pub)['files'])
            self.assertTrue(all(delivered[p] == raw for p, raw in candidates[2].items()))
            self.assertFalse(any(p in delivered for p in paths[0] - paths[1] - paths[2]))
            self.assertTrue(all(delivered[p] == candidates[1][p] for p in paths[1]))
            reopened = Publisher(store, self.code)
            self.assertEqual(3, reopened.ledger['active']['generation'])
            self.assertEqual(candidates[2], snapshot_files(store, reopened.head, 3)[1])
            self.assertEqual(NOW, reopened.ledger['selection_validated_utc'])
            git(source, 'commit', '--allow-empty', '-qm', 'new source')
            git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            newer_code = git(source, 'rev-parse', 'HEAD').decode().strip()
            adopted = Publisher(store, newer_code)
            adopted.adopt_code(adopted.head)
            self.assertEqual(candidates[2], snapshot_files(store, adopted.head, 3)[1])
            adopted_delivery = delivery_files(adopted, journal(adopted)['files'])
            self.assertEqual(delivered, adopted_delivery)
            self.assertEqual(NOW, adopted.ledger['selection_validated_utc'])
            self.assertEqual(1, len(adopted.ledger['requests']))

    def test_root_switch_while_pending_cannot_promote_or_post(self):
        from tools.spacefox.cloud import CloudError
        with self.authority() as (source, remote, store, pub), Service().serving() as service:
            first, first_revision = self.active(pub, service)
            second, second_revision = self.prepare(pub, NOW + 1)
            pub, intent = arm(pub, expected=pub.head, repository='local/spacefox',
                              run_id=42, run_attempt=1, artifact_id=77, now=NOW + 1)
            before_active = pub.ledger['active']
            before_pending = pub.ledger['pending']
            service.files = first
            service.after_root = second['feed.json']
            service.root_reads = 0
            pages = Pages('local/spacefox', 'local', api=service.url, local_http=True)
            with self.assertRaisesRegex(CloudError, 'changed during'):
                recover(pub, Site(service.url + '/site', local_http=True), pages)
            reopened = Publisher(store, self.code)
            self.assertEqual(before_active, reopened.ledger['active'])
            self.assertEqual(before_pending, reopened.ledger['pending'])
            self.assertEqual(first, snapshot_files(store, reopened.head, 1)[1])
            self.assertEqual(second, reopened.pending_files())
            self.assertEqual(NOW, reopened.ledger['selection_validated_utc'])
            self.assertEqual(1, len(reopened.ledger['requests']))
            self.assertFalse(any(call[0] == 'POST' for call in service.calls))


    def test_missing_previous_catalog_cannot_promote_pending(self):
        from tools.spacefox.cloud import CloudError
        with self.authority() as (source, remote, store, pub), Service().serving() as service:
            first, first_revision = self.active(pub, service)
            catalog = deepcopy(self.catalog)
            catalog['catalogVersion'] += '.delivery-retained'
            envelope = pub.publisher_envelope(NOW + 1)
            second, digest = build_artifact(pub.schedule, catalog, NOW + 1,
                                            publisher=envelope, root=self.fixture)
            pub.prepare(pub.head, NOW + 1, second, digest,
                        feed_publisher=envelope, artifact_profile=PROFILE)
            manifest = delivery(pub)
            complete = delivery_files(pub, manifest)
            old_only = set(first) - set(second)
            prior_catalogs = [p for p in old_only if p.startswith('wire3/catalogs/') and p.endswith('.json')]
            self.assertEqual(1, len(prior_catalogs))
            service.files = dict(complete)
            del service.files[prior_catalogs[0]]
            pub, intent = arm(pub, expected=pub.head, repository='local/spacefox',
                              run_id=42, run_attempt=1, artifact_id=77, now=NOW + 1)
            active, pending = pub.ledger['active'], pub.ledger['pending']
            pages = Pages('local/spacefox', 'local', api=service.url, local_http=True)
            with self.assertRaisesRegex(CloudError, 'missing, mixed or corrupt'):
                recover(pub, Site(service.url + '/site', local_http=True), pages)
            reopened = Publisher(store, self.code)
            self.assertEqual(active, reopened.ledger['active'])
            self.assertEqual(pending, reopened.ledger['pending'])
            self.assertEqual(first, snapshot_files(store, reopened.head, 1)[1])
            self.assertEqual(second, reopened.pending_files())
            self.assertEqual(NOW, reopened.ledger['selection_validated_utc'])
            self.assertEqual(1, len(reopened.ledger['requests']))
            self.assertFalse(any(call[0] == 'POST' for call in service.calls))


    def test_default_twenty_two_generations_with_shared_quota_and_pending_recovery(self):
        import gzip
        import hashlib
        import json
        import os
        import subprocess
        import sys
        from email.utils import formatdate
        from urllib.parse import parse_qs, urlsplit
        from tests.test_autonomous_publisher_whole import shell_step
        from tests.test_current_motion_publisher import FIXTURE, FIXTURE_SHA
        from tools.spacefox.provider import LL2Client
        raw = gzip.decompress(FIXTURE.read_bytes())
        self.assertEqual(FIXTURE_SHA, hashlib.sha256(raw).hexdigest())
        records = [r for r in json.loads(raw)['results'] if (r.get('net') or '') >= '2026-11-13T06:26:32Z'][:22]
        ids = ['ef9850ad-1096-425b-9d27-f7bbd186e61a','0f867f0c-5422-4d44-93b8-d7faaae7019b','bff2fc91-eddd-4dfc-af26-ac0674cfab4d','db3500ac-965b-4ad8-b417-cb8d8d005586','76617033-4dc0-4448-b50c-e5b0d5a18539','460d9db7-eaf6-4cd9-b095-cff433534c09','e0a11eb1-0bda-4872-b36b-140247fd5c60','a2975167-7c6f-4403-99e1-b40df17c8140','951a341f-236b-42fe-a667-4ab2fcf36eac','7bdc412b-c965-4517-a131-f57a01189803','8dd5de11-831b-445f-86f0-bffefe0550d9','5ce59e3a-c343-430f-ae4e-e608ba536754','c9605b67-8a53-4239-a8ae-577fe3b79799','dff42a2e-f047-48d7-b260-3888d3a4fe33','d74afbc7-0de5-491c-be05-4e9c31f736ac','3cdb9dee-b5cb-406c-bbd1-06a219930fb7','56ca6058-7ccc-4ec0-b1b0-fb49f3bfee49','9e27a1ed-e81a-4918-b32b-0380cf3a9f8f','b0dc988c-ea4a-423f-81b6-6b0fbe7cc17c','b5a9bccb-30d7-4af6-8ad1-fabb563be53c','dfac5ab7-7017-454f-b6cf-eeed277a97b5','e2523821-9760-4cb4-ad1f-7ce2e30419bd']
        self.assertEqual(ids, [r['id'] for r in records])
        class TwoPages(Service):
            def answer(self, method, path, headers, body):
                if path.startswith('/2.3.0/launches/upcoming/'):
                    self.calls.append((method, path, dict(headers), body))
                    offset = int(parse_qs(urlsplit(path).query).get('offset', ['0'])[0])
                    selected = records[self.start:self.start + 20]
                    client = LL2Client(origin=self.url, local_http=True)
                    next_url = client.first_url + '&offset=10' if offset == 0 else None
                    payload = dict(count=20, next=next_url, previous=None, results=selected[offset:offset + 10])
                    return 200, json.dumps(payload, separators=(',', ':')).encode(), {'Date':formatdate(self.epoch,usegmt=True),'Content-Type':'application/json'}
                return super().answer(method, path, headers, body)
        with self.authority(runtime=False) as (source, remote, store, pub), TwoPages().serving() as service:
            materialize = subprocess.run(['bash','-ec',shell_step('Materialize exact reviewed runtime and catalog closure')], cwd=source, capture_output=True)
            self.assertEqual(0, materialize.returncode, materialize.stderr)
            environment = {k:v for k,v in os.environ.items() if not k.startswith(('GITHUB_', 'GH_TOKEN', 'ACTIONS_', 'GIT_CONFIG_'))}
            def run(head, now, directory, live=None):
                cmd=[sys.executable,'-B','tools/update_feed.py','--remote',str(remote),'--expected-base',head,
                     '--origin',service.url,'--local-http','--now',str(now)]
                if live is not None: cmd += ['--live', f'{live.generation}:{live.artifact_revision}']
                result=subprocess.run(cmd+['run','--trigger','manual','--output',str(directory)],cwd=source,env=environment,capture_output=True,text=True,timeout=300)
                self.assertEqual(0,result.returncode,result.stderr)
                return json.loads(result.stdout)
            service.start=0
            first_result=run(pub.head,NOW,self.base/'default-first')
            first=Publisher(store,self.code); first_files=first.pending_files()
            self.assertEqual(2,first_result['requests'])
            self.assertEqual(set(ids[:20]),{e.record.launch_id.value for e in first.schedule.entries})
            first_feed=json.loads(first_files['feed.json'])
            self.assertEqual(3,first_feed['schemaVersion'])
            self.assertEqual(1,first_feed['publisher']['generation'])
            self.assertEqual(NOW,first_feed['publisher']['selectionValidatedUtc'])
            active=first_result['revision']; from tools.spacefox.publisher import LiveRevision
            first_revision=LiveRevision(**active);self.assertEqual('promoted',first.reconcile(first_revision))
            for _ in range(13):
                token=first.reserve(first.head,NOW+1,trigger='extra')
                first.finish_request(first.head,token,NOW+1,'success')
            service.start=2;service.epoch=NOW+3600
            second_result=run(first.head,NOW+3600,self.base/'default-second',first_revision)
            second=Publisher(store,self.code); second_files=second.pending_files()
            self.assertEqual('pending',second_result['result'])
            self.assertEqual(2,second_result['requests'])
            self.assertEqual(2,second_result['revision']['generation'])
            self.assertEqual(set(ids),{e.record.launch_id.value for e in second.schedule.entries})
            self.assertEqual(15,len(second.ledger['requests']))
            self.assertEqual(4,len([call for call in service.calls if '/launches/upcoming/' in call[1]]))
            self.assertEqual(4,len(service.calls))
            self.assertTrue(second_result['detailFailures'])
            self.assertIn('allowance',second_result['detailFailures'][0]['reason'])
            self.assertEqual(NOW+3600,second.ledger['selection_validated_utc'])
            feed=json.loads(second_files['feed.json'])
            self.assertEqual(3,feed['schemaVersion'])
            self.assertEqual(2,feed['publisher']['generation'])
            self.assertEqual(NOW+3600,feed['publisher']['selectionValidatedUtc'])
            self.assertEqual('retry_pending',second.reconcile(first_revision))
            self.assertEqual(second_files,second.pending_files())
            self.assertEqual(first_files['feed.json'],snapshot_files(store,second.head,1)[1]['feed.json'])
            self.assertLessEqual(len(second_files['feed.json']),8192)
            self.assertLessEqual(store.measure()['ledger_bytes'],65536)


    def test_pending_and_promotion_survive_before_and_lost_push_ack(self):
        with self.authority() as (source, remote, store, pub):
            self.accept(pub)
            files = self.candidate(pub)
            envelope = pub.publisher_envelope(NOW)
            before = pub.head
            real_git = store._git
            def fail_before(*args, **kwargs):
                if args[0] == 'push':
                    raise RuntimeError('before push')
                return real_git(*args, **kwargs)
            def lose_ack(*args, **kwargs):
                result = real_git(*args, **kwargs)
                if args[0] == 'push':
                    raise RuntimeError('ack lost')
                return result
            try:
                store._git = fail_before
                with self.assertRaisesRegex(RuntimeError, 'before push'):
                    pub.prepare(before, NOW, files, self.digest, feed_publisher=envelope, artifact_profile=PROFILE)
                store._git = real_git
                reopened = Publisher(store, self.code)
                self.assertEqual(before, reopened.head)
                self.assertIsNone(reopened.ledger['pending'])
                reopened.reconcile(None)
                store._git = lose_ack
                with self.assertRaisesRegex(RuntimeError, 'ack lost'):
                    reopened.prepare(reopened.head, NOW, files, self.digest, feed_publisher=envelope, artifact_profile=PROFILE)
                store._git = real_git
                pending = Publisher(store, self.code)
                self.assertEqual(1, pending.ledger['pending']['generation'])
                self.assertEqual(files, pending.pending_files())
                self.assertEqual('retry_pending', pending.reconcile(None))
                from tools.spacefox.publisher import LiveRevision
                revision = LiveRevision(1, pending.ledger['pending']['artifact_revision'])
                pending_head = pending.head
                store._git = fail_before
                with self.assertRaisesRegex(RuntimeError, 'before push'):
                    pending.reconcile(revision)
                store._git = real_git
                self.assertEqual(pending_head, Publisher(store, self.code).head)
                store._git = lose_ack
                with self.assertRaisesRegex(RuntimeError, 'ack lost'):
                    Publisher(store, self.code).reconcile(revision)
                store._git = real_git
                active = Publisher(store, self.code)
                self.assertEqual(1, active.ledger['active']['generation'])
                self.assertIsNone(active.ledger['pending'])
                self.assertEqual(files, snapshot_files(store, active.head, 1)[1])
                self.assertEqual(NOW, active.ledger['selection_validated_utc'])
                self.assertEqual(1, len(active.ledger['requests']))
                self.assertEqual('ready', active.reconcile(revision))
            finally:
                store._git = real_git


    def test_new_run_attempt_cannot_post_old_intent(self):
        from tools.spacefox.cloud import CloudError, deploy
        with self.authority() as (source, remote, store, pub), Service().serving() as service:
            self.accept(pub)
            files, revision = self.prepare(pub)
            pub, intent = arm(pub, expected=pub.head, repository='local/spacefox',
                              run_id=42, run_attempt=1, artifact_id=77, now=NOW)
            before, pending = pub.head, pub.ledger['pending']
            pages = Pages('local/spacefox', 'local', api=service.url, local_http=True)
            with self.assertRaisesRegex(CloudError, 'different source/run/attempt'):
                deploy(pub, pages, Site(service.url + '/site', local_http=True), expected=before,
                       repository='local/spacefox', run_id=42, run_attempt=2, id_token='local')
            reopened = Publisher(store, self.code)
            self.assertEqual(before, reopened.head)
            self.assertEqual(pending, reopened.ledger['pending'])
            self.assertEqual(files, reopened.pending_files())
            self.assertEqual(NOW, reopened.ledger['selection_validated_utc'])
            self.assertEqual(1, len(reopened.ledger['requests']))
            self.assertEqual([], service.calls)


    def test_404_requires_exact_completed_skipped_post_witness(self):
        from tools.spacefox.cloud import DeploymentNotFound
        with self.authority() as (source, remote, store, pub), Service().serving() as service:
            self.accept(pub)
            files, revision = self.prepare(pub)
            pub, intent = arm(pub, expected=pub.head, repository='local/spacefox',
                              run_id=42, run_attempt=1, artifact_id=77, now=NOW)
            before, ledger = pub.head, pub.ledger
            service.status_code=404
            pages=Pages('local/spacefox','local',api=service.url,local_http=True)
            with self.assertRaises(DeploymentNotFound):
                recover(pub,Site(service.url+'/site',local_http=True),pages)
            self.assertEqual(before,Publisher(store,self.code).head)
            self.assertEqual([], [call for call in service.calls if call[0]=='POST'])
            service.witness(intent)
            job=service.jobs['jobs'][0]
            job['conclusion']='success'
            job['steps']=[dict(name='POST once, then bound async polling and cancellation finality',status='completed',conclusion='skipped')]
            service.run['run_attempt']=2
            with self.assertRaises(DeploymentNotFound):
                recover(pub,Site(service.url+'/site',local_http=True),pages)
            self.assertEqual(before,Publisher(store,self.code).head)
            service.run['run_attempt']=1
            recovered=recover(pub,Site(service.url+'/site',local_http=True),pages)
            self.assertEqual('not_started',journal(recovered)['status'])
            self.assertEqual(ledger,recovered.ledger)
            self.assertEqual(files,recovered.pending_files())
            self.assertEqual([], [call for call in service.calls if call[0]=='POST'])


    def test_terminal_failed_attempt_preserves_active_then_new_intent_posts_once(self):
        from tools.spacefox.cloud import deploy
        with self.authority() as (source, remote, store, pub), Service().serving() as service:
            first, first_revision = self.active(pub, service)
            second, second_revision = self.prepare(pub, NOW + 1)
            pub, old = arm(pub, expected=pub.head, repository='local/spacefox',
                           run_id=42, run_attempt=1, artifact_id=77, now=NOW + 1)
            service.files=first
            service.statuses=['deployment_failed']
            pages=Pages('local/spacefox','local',api=service.url,local_http=True)
            site=Site(service.url+'/site',local_http=True)
            pub=recover(pub,site,pages)
            self.assertEqual('deployment_failed',journal(pub)['status'])
            self.assertEqual(1,pub.ledger['active']['generation'])
            self.assertEqual(2,pub.ledger['pending']['generation'])
            self.assertEqual(first,snapshot_files(store,pub.head,1)[1])
            self.assertEqual(second,pub.pending_files())
            self.assertEqual(NOW,pub.ledger['selection_validated_utc'])
            self.assertEqual(1,len(pub.ledger['requests']))
            self.assertFalse(any(c[0]=='POST' for c in service.calls))
            pub,new=arm(pub,expected=pub.head,repository='local/spacefox',
                        run_id=43,run_attempt=1,artifact_id=78,now=NOW+1)
            self.assertNotEqual(old['buildVersion'],new['buildVersion'])
            self.assertEqual(old['artifactRevision'],new['artifactRevision'])
            service.statuses=['succeed']
            self.assertEqual('succeed',deploy(pub,pages,site,expected=pub.head,
                             repository='local/spacefox',run_id=43,run_attempt=1,id_token='local'))
            self.assertEqual(1,len([c for c in service.calls if c[0]=='POST']))
            service.files=delivery_files(pub,journal(pub)['files'])
            pub=recover(pub,site,pages)
            self.assertEqual(2,pub.ledger['active']['generation'])
            self.assertIsNone(pub.ledger['pending'])
            self.assertEqual(second,snapshot_files(store,pub.head,2)[1])
            self.assertEqual(NOW,pub.ledger['selection_validated_utc'])
            self.assertEqual(1,len(pub.ledger['requests']))


    def test_pending_source_adoption_portable_cli_and_export_refusals(self):
        import json
        import shutil
        import subprocess
        import sys
        from tests.test_autonomous_publisher_whole import ROOT
        with self.authority() as (source, remote, store, pub):
            self.accept(pub)
            files, revision = self.prepare(pub)
            source_dir=self.base/'lost-artifact';source_dir.mkdir()
            for name, raw in files.items():
                path=source_dir/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            shutil.rmtree(source_dir)
            git(source,'commit','--allow-empty','-qm','new source')
            git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
            newcode=git(source,'rev-parse','HEAD').decode().strip()
            adopted=Publisher(store,newcode);adopted.adopt_code(adopted.head)
            before=adopted.head; self.assertEqual('retry_pending',adopted.reconcile(None))
            self.assertEqual(files,adopted.pending_files())
            self.assertEqual(NOW,adopted.ledger['selection_validated_utc'])
            self.assertEqual(1,len(adopted.ledger['requests']))
            portable=self.base/'portable';portable.mkdir();shutil.copytree(ROOT/'tools',portable/'tools')
            self.assertFalse((portable/'.agents').exists())
            def cli(code,base,target):
                return subprocess.run([sys.executable,'-B','tools/publisher_state.py','--remote',str(remote),
                    '--running-code',code,'--expected-base',base,'export-pending','--directory',str(target)],
                    cwd=portable,capture_output=True,text=True,timeout=120)
            dest=self.base/'recovered-output'
            out=cli(newcode,before,dest)
            self.assertEqual(0,out.returncode,out.stderr)
            self.assertEqual(len(files),json.loads(out.stdout)['result']['files'])
            exported={p.relative_to(dest).as_posix():p.read_bytes() for p in dest.rglob('*') if p.is_file()}
            self.assertEqual(files,exported)
            self.assertEqual(2,cli(newcode,before,dest).returncode)
            link=self.base/'symlink-output';link.symlink_to(dest,target_is_directory=True)
            self.assertEqual(2,cli(newcode,before,link).returncode)
            self.assertEqual(2,cli(newcode,'0'*40,self.base/'stale-output').returncode)
            self.assertEqual(2,cli(self.code,before,self.base/'old-code-output').returncode)
            self.assertFalse((self.base/'stale-output').exists())
            self.assertFalse((self.base/'old-code-output').exists())
            self.assertEqual(before,Publisher(store,newcode).head)
            self.assertEqual(files,Publisher(store,newcode).pending_files())


    def test_packed_schedule_dedup_and_missing_or_bad_object_refusal(self):
        import hashlib, json
        from tools.spacefox.publisher import StateError, decode_ledger, STATE_REF
        with self.authority() as (source,remote,store,pub):
            self.accept(pub)
            files, revision = self.prepare(pub)
            good = pub.head
            raw = store._blob(good,'ledger.json',65536)
            ledger=json.loads(raw)
            self.assertEqual(ledger['accepted'],ledger['pending']['schedule'])
            ref=ledger['accepted']; path='schedules/'+ref['sha256']+'.json'
            data=store._blob(good,path,1048576)
            self.assertEqual(ref['sha256'],hashlib.sha256(data).hexdigest())
            self.assertEqual(ref['bytes'],len(data))
            self.assertEqual(1,store.measure()['schedule_objects'])
            for bad in (data+b' ',b'{}'):
                with self.subTest(bad=bad[:5]),self.assertRaises(StateError):
                    decode_ledger(raw,lambda ignored:bad)
            store._git('read-tree',good)
            store._git('update-index','--index-info',data=('0 '+'0'*40+'\t'+path+'\n').encode())
            tree=store._git('write-tree').stdout.decode().strip()
            invalid=store._git('commit-tree',tree,'-p',good,data=b'missing schedule object\n').stdout.decode().strip()
            store._git('push',f'--force-with-lease={STATE_REF}:{good}',str(remote),f'{invalid}:{STATE_REF}')
            try:
                with self.assertRaises(StateError):Publisher(store,self.code)
                self.assertEqual(invalid,store._refs(STATE_REF)[STATE_REF])
            finally:
                store._git('push',f'--force-with-lease={STATE_REF}:{invalid}',str(remote),f'{good}:{STATE_REF}')
            restored=Publisher(store,self.code)
            self.assertEqual(files,restored.pending_files())
            self.assertEqual(NOW,restored.ledger['selection_validated_utc'])
            self.assertEqual(1,len(restored.ledger['requests']))


    def test_visible_pending_without_finality_cannot_promote_or_start_work(self):
        from tools.spacefox.cloud import CloudError
        from tools.spacefox.publisher import StateError
        with self.authority() as (source,remote,store,pub),Service().serving() as service:
            first,first_revision=self.active(pub,service)
            second,second_revision=self.prepare(pub,NOW+1)
            pub,intent=arm(pub,expected=pub.head,repository='local/spacefox',
                           run_id=42,run_attempt=1,artifact_id=77,now=NOW+1)
            service.files=delivery_files(pub,journal(pub)['files'])
            service.statuses=['queued','in_progress']
            pages=Pages('local/spacefox','local',api=service.url,local_http=True)
            wait=pages.wait
            pages.wait=lambda version:wait(version,polls=2,delay=0)
            before=pub.head;state=pub.ledger
            with self.assertRaises(CloudError):recover(pub,Site(service.url+'/site',local_http=True),pages)
            reopened=Publisher(store,self.code)
            self.assertEqual(before,reopened.head)
            self.assertEqual(state,reopened.ledger)
            self.assertEqual('armed',journal(reopened)['status'])
            self.assertEqual(first,snapshot_files(store,before,1)[1])
            self.assertEqual(second,reopened.pending_files())
            self.assertEqual('retry_pending',reopened.reconcile(first_revision))
            with self.assertRaises(StateError):reopened.reserve(before,NOW+2,trigger='manual')
            self.assertEqual(before,reopened.head)
            self.assertFalse(any(c[0]=='POST' or '/2.3.0/' in c[1] for c in service.calls))


    def test_atomic_source_and_pending_survive_lost_push_ack(self):
        import json
        from tools.spacefox.catalog import canonical_bytes
        from tools.spacefox.native_motion import with_text_transport
        from tools.spacefox.provider import normalize_launch
        from tests.test_current_motion_publisher import captured_starship
        with self.authority() as (source,remote,store,pub):
            token=pub.reserve(pub.head,NOW,trigger='manual')
            record=normalize_launch(captured_starship(),NOW)
            envelope=pub.publisher_envelope(NOW,selection_validated_utc=NOW)
            files={k:v for k,v in self.template.items() if not k.endswith('.txt')}
            feed=json.loads(files['feed.json']);feed['publisher']=envelope
            files['feed.json']=canonical_bytes(feed);files=with_text_transport(files)
            real_git=store._git
            def lose_ack(*args,**kwargs):
                result=real_git(*args,**kwargs)
                if args[0]=='push':raise RuntimeError('ack lost')
                return result
            try:
                store._git=lose_ack
                with self.assertRaisesRegex(RuntimeError,'ack lost'):
                    pub.accept_and_prepare(pub.head,token,(record,),NOW,files,self.digest,
                        selection_validated_utc=NOW,feed_publisher=envelope,artifact_profile=PROFILE)
            finally:store._git=real_git
            reopened=Publisher(store,self.code)
            self.assertEqual('retry_pending',reopened.reconcile(None))
            self.assertEqual(1,reopened.ledger['pending']['generation'])
            self.assertEqual('success',reopened.ledger['requests'][0]['outcome'])
            self.assertTrue(reopened.ledger['requests'][0]['accepted_source'])
            self.assertEqual(NOW,reopened.ledger['selection_validated_utc'])
            self.assertEqual(record,reopened.schedule.entries[0].record)
            self.assertEqual(files,reopened.pending_files())


    def test_completed_primary_reservation_requires_exact_unexpired_invocation(self):
        import json
        from tools.spacefox.catalog import canonical_bytes
        from tools.spacefox.native_motion import with_text_transport
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.publisher import StateError
        from tests.test_current_motion_publisher import captured_starship
        with self.authority() as (source,remote,store,pub):
            token=pub.reserve(pub.head,NOW,trigger='manual')
            pub.finish_request(pub.head,token,NOW+2,'success',retain_for_acceptance=True)
            record=normalize_launch(captured_starship(),NOW)
            envelope=pub.publisher_envelope(NOW+5,selection_validated_utc=NOW)
            files={k:v for k,v in self.template.items() if not k.endswith('.txt')}
            feed=json.loads(files['feed.json']);feed['publisher']=envelope
            files['feed.json']=canonical_bytes(feed);files=with_text_transport(files)
            before=pub.head
            for label,instant,anchor in [('missing',NOW+5,None),('wrong',NOW+5,NOW+1),('expired',NOW+3600,NOW)]:
                with self.subTest(label=label),self.assertRaises(StateError):
                    pub.accept_and_prepare(before,token,(record,),instant,files,self.digest,
                        invocation_utc=anchor,selection_validated_utc=NOW,
                        feed_publisher=envelope,artifact_profile=PROFILE)
                self.assertEqual(before,pub.head)
            wrong=dict(feed);wrong['publisher']=dict(envelope,generation=2)
            invalid={k:v for k,v in files.items() if not k.endswith('.txt')}
            invalid['feed.json']=canonical_bytes(wrong);invalid=with_text_transport(invalid)
            with self.assertRaises(StateError):
                pub.accept_and_prepare(before,token,(record,),NOW+5,invalid,self.digest,
                    invocation_utc=NOW,selection_validated_utc=NOW,
                    feed_publisher=envelope,artifact_profile=PROFILE)
            self.assertEqual(before,pub.head)
            with self.assertRaises(StateError):
                pub.accept_and_prepare('0'*40,token,(record,),NOW+5,files,self.digest,
                    invocation_utc=NOW,selection_validated_utc=NOW,
                    feed_publisher=envelope,artifact_profile=PROFILE)
            self.assertEqual(before,pub.head)
            revision=pub.accept_and_prepare(before,token,(record,),NOW+5,files,self.digest,
                invocation_utc=NOW,selection_validated_utc=NOW,
                feed_publisher=envelope,artifact_profile=PROFILE)
            self.assertEqual(1,revision.generation)
            self.assertEqual(1,len(pub.ledger['requests']))
            self.assertTrue(pub.ledger['requests'][0]['accepted_source'])
            saved=pub.head
            with self.assertRaises(StateError):
                pub.accept_and_prepare(saved,token,(record,),NOW+5,files,self.digest,
                    invocation_utc=NOW,selection_validated_utc=NOW,
                    feed_publisher=envelope,artifact_profile=PROFILE)
            self.assertEqual(saved,pub.head)
            self.assertEqual(files,Publisher(store,self.code).pending_files())


    def test_updater_rejects_missing_or_wrong_builder_envelope(self):
        import json
        from tools.spacefox.catalog import canonical_bytes
        from tools.spacefox.native_motion import with_text_transport
        from tools.spacefox.provider import LL2Client
        from tools.spacefox.publisher import StateError
        from tools.update_feed import update
        for fault in ('missing','wrong_generation'):
            with self.subTest(fault=fault),self.authority() as (source,remote,store,pub),Service().serving() as service:
                def bad_builder(state,catalog,instant,*,publisher,policy,traversal):
                    files={k:v for k,v in self.template.items() if not k.endswith('.txt')}
                    feed=json.loads(files['feed.json'])
                    if fault=='missing':feed.pop('publisher')
                    else:feed['publisher']=dict(publisher,generation=2)
                    files['feed.json']=canonical_bytes(feed)
                    return with_text_transport(files),self.digest
                client=LL2Client(origin=service.url,local_http=True)
                with self.assertRaises(StateError) as rejected:
                    update(pub,client,NOW,self.catalog,trigger='manual',max_pages=1,detail_limit=0,
                           artifact_builder=bad_builder,artifact_profile=PROFILE)
                expected='invalid complete native-motion-v3 artifact' if fault=='missing' else 'feed does not bind'
                self.assertIn(expected,str(rejected.exception))
                reopened=Publisher(store,self.code)
                self.assertEqual(1,len([c for c in service.calls if '/launches/upcoming/' in c[1]]))
                self.assertEqual(1,len(reopened.ledger['requests']))
                self.assertEqual('failed',reopened.ledger['requests'][0]['outcome'])
                self.assertNotIn('accepted_source',reopened.ledger['requests'][0])
                self.assertEqual(NOW+300,reopened.ledger['backoff_until_utc'])
                self.assertEqual((),reopened.schedule.entries)
                self.assertIsNone(reopened.ledger['selection_validated_utc'])
                self.assertIsNone(reopened.ledger['pending'])


    def test_updater_cli_recovers_pending_before_any_http(self):
        import json, os, subprocess, sys
        with self.authority(runtime=False) as (source,remote,store,pub),Service().serving() as service:
            self.accept(pub)
            files,revision=self.prepare(pub)
            before=pub.head
            environment={k:v for k,v in os.environ.items() if not k.startswith(('GITHUB_','GH_TOKEN','ACTIONS_','GIT_CONFIG_'))}
            output=self.base/'updater-pending-recovery'
            result=subprocess.run([sys.executable,'-B','tools/update_feed.py','--remote',str(remote),
                '--expected-base',before,'--origin',service.url,'--local-http','--now',str(NOW+1),
                'run','--output',str(output)],cwd=source,env=environment,capture_output=True,text=True,timeout=120)
            self.assertEqual(0,result.returncode,result.stderr)
            self.assertEqual('recovered_pending',json.loads(result.stdout)['result'])
            exported={p.relative_to(output).as_posix():p.read_bytes() for p in output.rglob('*') if p.is_file()}
            self.assertEqual(files,exported)
            reopened=Publisher(store,self.code)
            self.assertEqual(before,reopened.head)
            self.assertEqual(files,reopened.pending_files())
            self.assertEqual(NOW,reopened.ledger['selection_validated_utc'])
            self.assertEqual(1,len(reopened.ledger['requests']))
            self.assertEqual([],service.calls)


def load_tests(loader, standard_tests, pattern):
    # Reuse the integration fixture without rediscovering its inherited suite.
    import unittest
    return unittest.TestSuite(loader.loadTestsFromName(name, DurableDeliveryWholeTest)
                              for name in DurableDeliveryWholeTest.__dict__ if name.startswith('test_'))
