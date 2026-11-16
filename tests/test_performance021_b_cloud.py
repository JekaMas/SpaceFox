"""Real sparse Git, loopback cloud stages for the scheduling witness."""
import json
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import time
from tests.test_autonomous_publisher_whole import git

from tests.test_autonomous_publisher_whole import AutonomousPublisherWholeTest, Service, shell_step
from tests.test_current_motion_publisher import captured_starship
from tools.spacefox.catalog_refresh import CatalogRefresh
from tools.spacefox.cloud import Pages, Site, SCHEDULING_WITNESS, arm, delivery, delivery_files, recover
from tools.spacefox.native_motion import PROFILE, _RepositoryCatalogOperation
from tools.spacefox.provider import normalize_launch
from tools.spacefox.publisher import Publisher, LiveRevision, STATE_REF, _canonical, _schedule_due
from tools.spacefox.schedule import RefreshPolicy


class RealCloudSchedulingTest(AutonomousPublisherWholeTest):
    def test_active_full_admission_then_sparse_cli_no_work(self):
        now=int(time.time())
        with self.authority() as (source, remote, store, pub), Service().serving() as service:
            service.epoch=now
            token=pub.reserve(pub.head,now,trigger='manual')
            pub.accept_source(pub.head,token,(normalize_launch(captured_starship(),now),),now,selection_validated_utc=now)
            owner=_RepositoryCatalogOperation(Path(__file__).resolve().parents[1])
            envelope=pub.publisher_envelope(now)
            files,digest=owner.build(pub.schedule,None,now,publisher=envelope,policy=pub.policy,traversal=None)
            pub.prepare(pub.head,now,files,digest,feed_publisher=envelope,artifact_profile=PROFILE)
            service.files=delivery_files(pub,delivery(pub))
            pub,_=arm(pub,expected=pub.head,repository='local/spacefox',run_id=42,run_attempt=1,artifact_id=77,now=now)
            pub=recover(pub,Site(service.url+'/site',local_http=True),Pages('local/spacefox','local',api=service.url,local_http=True))
            result=CatalogRefresh(pub,origin=service.url,local_http=True).run(now+5,max_requests=4)
            self.assertEqual(result.status,'complete')
            before=pub.ledger; oldhead=pub.head
            preliminary=self.cli(source,remote,service,'probe',now=now+10,runtime=False)
            self.assertEqual(preliminary['no_work'],'false')
            self.assertEqual(store._refs('refs/heads/feed-state-map-v3')['refs/heads/feed-state-map-v3'],oldhead)
            # Execute the checked-in workflow's actual source materialization step.
            subprocess.run(['bash','-c',shell_step('Materialize exact reviewed runtime and catalog closure')],cwd=source,check=True,capture_output=True)
            service.calls.clear();out=source/'never-created'
            prepared=self.cli(source,remote,service,'prepare','--output',out,now=now+10,runtime=False)
            self.assertEqual(prepared['result'],'not_due');self.assertEqual(prepared['requests'],0);self.assertFalse(out.exists())
            self.assertFalse(any('/2.3.0/' in call[1] or call[0]=='POST' for call in service.calls))
            after=Publisher(store,self.code);self.assertNotEqual(after.head,oldhead)
            self.assertEqual(after.ledger,before)
            sparse=self.checkout(runtime=True);service.calls.clear()
            launcher='''import sys\nimport tools.cloud_feed as c\nimport tools.spacefox.geographic_context as g\nimport tools.spacefox.provider as p\ndef forbidden(*a,**k): raise AssertionError("forbidden work on sparse no-op")\ng._load_source=forbidden\nc._RepositoryCatalogOperation=forbidden\np.LL2Client.request=forbidden\ndef audit(event,args):\n if event=="subprocess.Popen":\n  argv=args[1]\n  if argv and (argv[0] in ("node","rsvg-convert") or argv[0]=="git" and "push" in argv): raise AssertionError("forbidden process")\nsys.addaudithook(audit)\nsys.exit(c.main())'''
            env={k:v for k,v in os.environ.items() if not k.startswith(('GITHUB_','GH_TOKEN','ACTIONS_','GIT_CONFIG_'))}
            command=[sys.executable,'-B','-c',launcher,'--repository','local/spacefox','--remote',str(remote),'--site',service.url+'/site','--api',service.url,'--origin',service.url,'--local-qualification','--now',str(now+11),'probe']
            run=subprocess.run(command,cwd=sparse,env=env,capture_output=True,text=True,timeout=120)
            self.assertEqual(run.returncode,0,run.stderr);answer=json.loads(run.stdout.splitlines()[-1])
            self.assertEqual(answer['no_work'],'true');self.assertEqual(answer['head'],after.head)
            self.assertEqual(store._refs('refs/heads/feed-state-map-v3')['refs/heads/feed-state-map-v3'],after.head)
            self.assertEqual(len(service.calls),2)
            self.assertTrue(all(call[0]=='GET' and call[1]=='/site/feed.json' for call in service.calls))
            self.assertEqual(Publisher(store,self.code).ledger,before)
            original=store._blob(after.head,SCHEDULING_WITNESS,4096)
            stale=json.loads(original);stale['date']='2000-01-01'
            wrong=json.loads(original);wrong['artifactRevision']='0'*64
            def replace_witness(raw):
                nonlocal after
                head=after.head;doc=after.ledger;objects=store._files(head,doc)
                objects[SCHEDULING_WITNESS]=raw
                commit=store._commit(doc,head,objects)
                pushed=store._git('push',f'--force-with-lease={STATE_REF}:{head}',store.remote,f'{commit}:{STATE_REF}',check=False)
                self.assertEqual(pushed.returncode,0)
                after=Publisher(store,self.code);self.assertEqual(after.ledger,before)
            for invalid in (b'{',_canonical(stale),_canonical(wrong)):
                replace_witness(invalid);service.calls.clear();untouched=after.head
                refused=subprocess.run(command,cwd=sparse,env=env,capture_output=True,text=True,timeout=120)
                self.assertEqual(refused.returncode,0,refused.stderr);self.assertEqual(json.loads(refused.stdout.splitlines()[-1])['no_work'],'false')
                self.assertEqual(store._refs(STATE_REF)[STATE_REF],untouched)
                self.assertFalse(any('/2.3.0/' in call[1] or call[0]=='POST' for call in service.calls))
            replace_witness(original)
            service.calls.clear();service.root_reads=0;service.after_root=b'{}'
            raced=subprocess.run(command,cwd=sparse,env=env,capture_output=True,text=True,timeout=120)
            self.assertEqual(raced.returncode,0,raced.stderr);self.assertEqual(json.loads(raced.stdout.splitlines()[-1])['no_work'],'false')
            self.assertEqual(store._refs('refs/heads/feed-state-map-v3')['refs/heads/feed-state-map-v3'],after.head)
            self.assertFalse(any('/2.3.0/' in call[1] or call[0]=='POST' for call in service.calls))
            service.after_root=None
            # The durable launch cadence is independently due two hours later.
            self.assertTrue(_schedule_due(before,now+7200,RefreshPolicy(**before['refresh_policy'])))
            self.assertEqual(time.gmtime(now).tm_yday,time.gmtime(now+7200).tm_yday,'due witness needs a same-UTC-date interval')
            service.calls.clear();command[command.index(str(now+11))]=str(now+7200)
            due=subprocess.run(command,cwd=sparse,env=env,capture_output=True,text=True,timeout=120)
            self.assertEqual(due.returncode,0,due.stderr);self.assertEqual(json.loads(due.stdout.splitlines()[-1])['no_work'],'false')
            self.assertEqual(store._refs('refs/heads/feed-state-map-v3')['refs/heads/feed-state-map-v3'],after.head)
            self.assertFalse(any('/2.3.0/' in call[1] or call[0]=='POST' for call in service.calls))
            command[command.index(str(now+7200))]=str(now+11)
            # Actual metadata restart creates a durable partial traversal; the
            # same sparse probe must now escalate without polling the provider.
            after.reconcile(LiveRevision(before['active']['generation'],before['active']['artifact_revision']))
            partial=CatalogRefresh(after,origin=service.url,local_http=True).run(now+12,max_requests=1,restart=True)
            self.assertEqual(partial.status,'partial')
            partial_head=after.head; service.calls.clear()
            command[command.index(str(now+11))]=str(now+13)
            run=subprocess.run(command,cwd=sparse,env=env,capture_output=True,text=True,timeout=120)
            self.assertEqual(run.returncode,0,run.stderr);answer=json.loads(run.stdout.splitlines()[-1])
            self.assertEqual(answer['no_work'],'false')
            self.assertEqual(store._refs('refs/heads/feed-state-map-v3')['refs/heads/feed-state-map-v3'],partial_head)
            self.assertFalse(any('/2.3.0/' in call[1] or call[0]=='POST' for call in service.calls))
            # An actual tracked catalog-only source change must progress to a
            # new pending artifact without a provider request or source-age reset.
            recipe_path=source/'catalog/source.json';recipe=json.loads(recipe_path.read_bytes())
            recipe['catalogVersion'] += '.btest'
            eligibility=source/recipe['eligibility']['path'];registry=json.loads(eligibility.read_bytes())
            registry['catalogVersion']=recipe['catalogVersion']
            registry_raw=json.dumps(registry,sort_keys=True,separators=(',',':')).encode()
            eligibility.write_bytes(registry_raw);recipe['eligibility']['sha256']=hashlib.sha256(registry_raw).hexdigest()
            recipe_path.write_text(json.dumps(recipe,sort_keys=True,separators=(',',':')))
            git(source,'add','--sparse','catalog/source.json',recipe['eligibility']['path']);git(source,'commit','-qm','catalog version change')
            git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
            service.calls.clear();destination=source/'catalog-pending'
            changed=self.cli(source,remote,service,'prepare','--output',destination,now=now+13,runtime=False)
            self.assertEqual(changed['result'],'content_pending');self.assertEqual(changed['requests'],0)
            latest=Publisher(store,git(source,'rev-parse','HEAD').decode().strip())
            self.assertIsNotNone(latest.ledger['pending']);self.assertEqual(latest.ledger['active'],before['active'])
            self.assertEqual(latest.ledger['selection_validated_utc'],before['selection_validated_utc'])
            self.assertTrue((destination/'feed.json').is_file())
            self.assertFalse(any('/2.3.0/' in call[1] or call[0]=='POST' for call in service.calls))
            pending_sparse=self.base/'pending-sparse'
            git(self.base,'clone','-q','--no-checkout','--shared',str(source),str(pending_sparse))
            git(pending_sparse,'sparse-checkout','init','--no-cone')
            git(pending_sparse,'sparse-checkout','set','--no-cone','--stdin',data=self.seed.replace(b'/catalog/source.json\n',b''))
            git(pending_sparse,'checkout','-q')
            service.calls.clear();pending_head=latest.head
            run=subprocess.run(command,cwd=pending_sparse,env=env,capture_output=True,text=True,timeout=120)
            self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(json.loads(run.stdout.splitlines()[-1])['no_work'],'false')
            self.assertEqual(store._refs('refs/heads/feed-state-map-v3')['refs/heads/feed-state-map-v3'],pending_head)
            self.assertFalse(any('/2.3.0/' in call[1] or call[0]=='POST' for call in service.calls))
            print('real cloud stages: old witness escalated; full same-content admission wrote only scheduling witness; sparse probe 2 root GETs, zero provider/render/push, unchanged ledger and source age; metadata staging and pending forced full path; catalog change created pending without provider or age reset')
