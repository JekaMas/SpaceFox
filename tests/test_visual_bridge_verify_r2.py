"""R2 independent durable/profile challenges; only local Git/HTTP are used."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from tests import test_visual_bridge_verify_r1 as prior
from tests.test_visual_bridge import NOW, NoProvider
from tools.cloud_feed import prepare_content
from tools.spacefox.catalog import build_catalog
from tools.spacefox.publisher import Publisher, StateError
from tests.test_cloud_delivery import World, git


ROOT = Path(__file__).resolve().parents[1]


def literal(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class VisualBridgeDurableReviewR2(unittest.TestCase):
    setUp = prior.VisualBridgeDurableReviewR1.setUp
    tearDown = prior.VisualBridgeDurableReviewR1.tearDown

    def candidate(self, label='a', generation=1):
        files = prior.fixture(label)
        publisher = {'instance': self.pub.ledger['instance_id'], 'generation': generation,
                     'selectionValidatedUtc': 1794438000}
        for path in ('feed.json', 'wire2/feed.json'):
            feed = json.loads(files[path])
            feed['publisher'] = publisher
            files[path] = literal(feed)
        return files, publisher, json.loads(files['feed.json'])['catalogDigest']

    def snapshot(self, files, generation=1):
        value = {'generation': generation, 'code_revision': self.code,
                 'catalog_revision': json.loads(files['feed.json'])['catalogDigest'],
                 'files': {path: {'sha256': digest(raw), 'bytes': len(raw)} for path, raw in files.items()},
                 'schedule': self.pub.ledger['accepted']}
        value['artifact_revision'] = digest(literal(value))
        return value

    def pending(self, files):
        doc = self.pub.ledger
        doc['generation'] = 1
        doc['pending'] = self.snapshot(files)
        raw = {f'artifacts/1/{path}': data for path, data in files.items()}
        return doc, raw

    def mark_profile(self, doc, profile):
        snap = doc['pending']
        snap['artifact_profile'] = profile
        snap['artifact_revision'] = digest(literal({k: v for k, v in snap.items() if k != 'artifact_revision'}))

    def install_historical(self, files):
        doc, raw = self.pending(files)
        commit = self.store._commit(doc, self.pub.head, raw)
        self.store._git('push', f'--force-with-lease=refs/heads/feed-state:{self.pub.head}',
                        self.store.remote, f'{commit}:refs/heads/feed-state')
        self.pub = Publisher(self.store, self.code)
        return doc['pending']

    def test_explicit_profile_and_source_facts_survive_write_and_load(self):
        valid, publisher, revision = self.candidate()
        for mode in ('missing-root', 'missing-object', 'unknown-profile', 'profile-type', 'wrong-source-fact'):
            with self.subTest(mode=mode):
                files = dict(valid)
                if mode == 'missing-root':
                    # A fully closed legacy artifact is still wrong for v2.
                    root = json.loads(files['feed.json'])
                    files = {p: files[p] for p in ('feed.json', root['catalogPath'])}
                elif mode == 'missing-object':
                    del files[next(p for p in files if p.startswith('objects/'))]
                elif mode == 'wrong-source-fact':
                    for path in ('feed.json', 'wire2/feed.json'):
                        root = json.loads(files[path])
                        root['launch']['mission_name'] = 'Unaccepted relabeling'
                        files[path] = literal(root)
                profile = 'visual-v3' if mode == 'unknown-profile' else [] if mode == 'profile-type' else 'visual-v2'
                doc, raw = self.pending(files)
                self.mark_profile(doc, profile)
                before = self.pub.head
                with self.assertRaises(StateError):
                    self.store.write(before, doc, raw)
                self.assertEqual(before, self.store.load()[0])
        doc, raw = self.pending(valid)
        self.mark_profile(doc, 'visual-v2')
        # A complete, manually hashed known-good snapshot passes the same store
        # boundary; no production snapshot builder supplied the expected pins.
        head, saved = self.store.write(self.pub.head, doc, raw)
        self.assertEqual(doc, saved)
        reopened = Publisher(self.store, self.code)
        self.assertEqual(head, reopened.head)
        self.assertEqual(valid, reopened.pending_files())
        self.assertEqual('visual-v2', reopened.ledger['pending']['artifact_profile'])

    def test_legacy_v1_pending_adoption_recovery_then_visual_migration(self):
        files, _, _ = self.candidate()
        root = json.loads(files['feed.json'])
        old = {p: files[p] for p in ('feed.json', root['catalogPath'])}
        historical = self.install_historical(old)
        self.assertNotIn('artifact_profile', historical)
        ages = (self.pub.ledger['selection_validated_utc'], self.pub.schedule.entries[0].record.source_validated_utc)
        quota = self.pub.ledger['requests']
        # Adoption of new code must leave a legitimate old pending artifact
        # exact, before a later deliberate v2 output generation exists.
        git(self.source, 'commit', '--allow-empty', '-qm', 'new producer code')
        self.code = git(self.source, 'rev-parse', 'HEAD')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.pub = Publisher(self.store, self.code)
        self.pub.adopt_code(self.pub.head)
        self.assertEqual(historical, self.pub.ledger['pending'])
        self.assertEqual('retry_pending', self.pub.reconcile(None))
        before = self.pub.head
        self.assertEqual('recovered_pending', prepare_content(self.pub, NoProvider(), NOW + 1, build_catalog(ROOT), root=ROOT)['result'])
        self.assertEqual(before, self.pub.head)
        self.assertEqual(old, self.pub.pending_files())
        from tools.spacefox.cloud import Site, delivery, delivery_files
        from tools.spacefox.publisher import LiveRevision
        world = World(self.remote)
        try:
            world.live = old
            expected = LiveRevision(1, historical['artifact_revision'])
            self.assertEqual(old, delivery_files(self.pub, delivery(self.pub)))
            self.assertEqual(expected, Site(world.base + '/site', local_http=True).observe(self.pub))
            self.pub.reconcile(expected)
            self.assertEqual(historical, self.pub.ledger['active'])
            result = prepare_content(self.pub, NoProvider(), NOW + 2, build_catalog(ROOT), root=ROOT)
            self.assertEqual(('content_pending', 0), (result['result'], result['requests']))
            self.assertEqual(2, self.pub.ledger['generation'])
            self.assertEqual('visual-v2', self.pub.ledger['pending']['artifact_profile'])
            self.assertEqual(quota, self.pub.ledger['requests'])
            new = self.pub.pending_files()
            feed = json.loads(new['wire2/feed.json'])
            self.assertEqual(ages, (feed['publisher']['selectionValidatedUtc'], feed['launch']['source_validated_utc']))
            self.assertEqual(old[root['catalogPath']], delivery_files(self.pub, delivery(self.pub))[root['catalogPath']])
            world.live = delivery_files(self.pub, delivery(self.pub))
            self.assertEqual(2, Site(world.base + '/site', local_http=True).observe(self.pub, delivery(self.pub)).generation)
        finally:
            world.close()

    def test_historical_dual_profile_recovery_and_explicit_downgrade_refusal(self):
        files, _, _ = self.candidate()
        historical = self.install_historical(files)
        self.assertEqual(files, self.pub.pending_files())
        from tools.spacefox.publisher import LiveRevision
        self.pub.reconcile(LiveRevision(1, historical['artifact_revision']))
        next_files, publisher, revision = self.candidate('b', 2)
        root = json.loads(next_files['feed.json'])
        legacy = {p: next_files[p] for p in ('feed.json', root['catalogPath'])}
        before = self.pub.head
        with self.assertRaises(StateError):
            self.pub.prepare(before, NOW + 1, legacy, revision, feed_publisher=publisher, artifact_profile='feed-v1')
        self.assertEqual(before, self.pub.head)
        self.assertEqual(historical, self.pub.ledger['active'])
        self.assertIsNone(self.pub.ledger['pending'])

    def test_durable_profile_refuses_whole_v2_subset_removal(self):
        files, _, _ = self.candidate()
        root = json.loads(files['feed.json'])
        legacy = {p: files[p] for p in ('feed.json', root['catalogPath'])}
        doc, raw = self.pending(legacy)
        self.mark_profile(doc, 'visual-v2')
        from tools.spacefox.cloud import CloudError, validate_snapshot
        with self.assertRaises(CloudError):
            validate_snapshot(doc['pending'], legacy)
        commit = self.store._commit(doc, self.pub.head, raw)
        self.store._git('push', f'--force-with-lease=refs/heads/feed-state:{self.pub.head}',
                        self.store.remote, f'{commit}:refs/heads/feed-state')
        with self.assertRaises(StateError):
            Publisher(self.store, self.code)

    def test_legacy_implicit_dual_cannot_strip_current_profile(self):
        files, publisher, revision = self.candidate()
        self.pub.prepare(self.pub.head, NOW, files, revision, feed_publisher=publisher)
        self.assertEqual('visual-v2', self.pub.ledger['pending']['artifact_profile'])
        self.assertEqual(files, Publisher(self.store, self.code).pending_files())
        doc = self.pub.ledger
        snap = doc['pending']
        del snap['artifact_profile']
        snap['artifact_revision'] = digest(literal({k: v for k, v in snap.items() if k != 'artifact_revision'}))
        before = self.pub.head
        with self.assertRaises(StateError):
            self.store.write(before, doc)
        self.assertEqual(before, self.store.load()[0])
        raw = self.store._files(before, self.pub.ledger)
        commit = self.store._commit(doc, before, raw)
        self.store._git('push', f'--force-with-lease=refs/heads/feed-state:{before}',
                        self.store.remote, f'{commit}:refs/heads/feed-state')
        with self.assertRaises(StateError):
            Publisher(self.store, self.code)

    def test_legacy_unqualified_complete_v1_records_concrete_profile(self):
        files, publisher, revision = self.candidate()
        root = json.loads(files['feed.json'])
        old = {p: files[p] for p in ('feed.json', root['catalogPath'])}
        self.pub.prepare(self.pub.head, NOW, old, revision, feed_publisher=publisher)
        self.assertEqual('feed-v1', self.pub.ledger['pending']['artifact_profile'])
        self.assertEqual(old, Publisher(self.store, self.code).pending_files())

    def test_direct_state_cannot_renew_selection_age(self):
        files, _, _ = self.candidate()
        for path in ('feed.json', 'wire2/feed.json'):
            feed = json.loads(files[path])
            feed['publisher']['selectionValidatedUtc'] = NOW
            files[path] = literal(feed)
        doc, raw = self.pending(files)
        self.mark_profile(doc, 'visual-v2')
        before = self.pub.head
        with self.assertRaises(StateError):
            self.store.write(before, doc, raw)
        self.assertEqual(before, self.store.load()[0])
        commit = self.store._commit(doc, before, raw)
        self.store._git('push', f'--force-with-lease=refs/heads/feed-state:{before}',
                        self.store.remote, f'{commit}:refs/heads/feed-state')
        with self.assertRaises(StateError):
            Publisher(self.store, self.code)

    def test_real_cli_profile_fault_recovery_and_legacy_adoption(self):
        clone = self.root / 'current-producer'
        subprocess.run(['git', 'clone', '-q', str(ROOT), str(clone)], check=True)
        current_code = git(clone, 'rev-parse', 'HEAD')
        remote = self.root / 'cli.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
        git(clone, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
        world = World(remote)

        def invoke(remote, output, *, bootstrap=False, fault=False):
            args = ['--repository', 'owner/SpaceFox', '--remote', str(remote),
                    '--site', world.base + '/site', '--api', world.base, '--origin', world.base,
                    '--local-qualification', '--now', str(NOW + 1), 'prepare', '--output', str(output)]
            if bootstrap:
                args.append('--bootstrap')
            if fault:
                # Only the actual producer's result is faulted. The real CLI,
                # update, atomic accept, writer and quota paths still execute.
                code = ('import json,sys; import tools.cloud_feed as c; original=c.build_visual_artifact\n'
                        'def broken(*a,**k):\n'
                        ' files,digest=original(*a,**k); root=json.loads(files["feed.json"]); '
                        'return {p:files[p] for p in ("feed.json",root["catalogPath"])},digest\n'
                        'c.build_visual_artifact=broken\nraise SystemExit(c.main(sys.argv[1:]))')
                command = [sys.executable, '-B', '-c', code, *args]
            else:
                command = [sys.executable, '-B', 'tools/cloud_feed.py', *args]
            return subprocess.run(command, cwd=clone, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        try:
            output = self.root / 'cli-output'
            run = invoke(remote, output, bootstrap=True)
            self.assertEqual(0, run.returncode, run.stderr.decode())
            self.assertEqual(('true', 1, 4), tuple(json.loads(run.stdout)[k] for k in ('pending', 'requests', 'exportedFiles')))
            from tools.spacefox.publisher import GitState
            store = GitState(str(remote))
            try:
                pub = Publisher(store, current_code)
                saved = pub.ledger['pending']
                self.assertEqual('visual-v2', saved['artifact_profile'])
                expected = pub.pending_files()
            finally:
                store.close()
            again = self.root / 'cli-again'
            run = invoke(remote, again)
            self.assertEqual(0, run.returncode, run.stderr.decode())
            self.assertEqual('recovered_pending', json.loads(run.stdout)['result'])
            self.assertEqual(expected, {p.relative_to(again).as_posix(): p.read_bytes() for p in again.rglob('*.json')})
            self.assertEqual(1, world.provider_calls)

            bad_remote = self.root / 'cli-fault.git'
            subprocess.run(['git', 'init', '--bare', '-q', str(bad_remote)], check=True)
            git(clone, 'push', '-q', str(bad_remote), 'HEAD:refs/heads/main')
            world.remote = bad_remote
            run = invoke(bad_remote, self.root / 'refused-output', bootstrap=True, fault=True)
            self.assertEqual(2, run.returncode)
            store = GitState(str(bad_remote))
            try:
                _, doc = store.load()
                self.assertEqual(0, doc['generation'])
                self.assertIsNone(doc['pending'])
                self.assertEqual([], doc['accepted']['entries'])
                self.assertIsNone(doc['selection_validated_utc'])
                self.assertEqual(1, len(doc['requests']))
                self.assertEqual('failed', doc['requests'][0]['outcome'])
            finally:
                store.close()

            old, _, _ = self.candidate()
            feed = json.loads(old['feed.json'])
            legacy = {p: old[p] for p in ('feed.json', feed['catalogPath'])}
            historical = self.install_historical(legacy)
            quota = self.pub.ledger['requests']
            git(clone, 'push', '-q', '--force', str(self.remote), 'HEAD:refs/heads/main')
            world.remote = self.remote
            provider_count = world.provider_calls
            run = invoke(self.remote, self.root / 'cli-legacy')
            self.assertEqual(0, run.returncode, run.stderr.decode())
            self.assertEqual(('recovered_pending', 2), tuple(json.loads(run.stdout)[k] for k in ('result', 'exportedFiles')))
            reopened = Publisher(self.store, current_code)
            self.assertEqual(historical, reopened.ledger['pending'])
            self.assertEqual(legacy, reopened.pending_files())
            self.assertEqual(quota, reopened.ledger['requests'])
            self.assertEqual(provider_count, world.provider_calls)
            self.assertEqual([], world.errors)
        finally:
            world.close()


    def test_cloud_expected_profile_refuses_entire_v1_subset(self):
        files, publisher, revision = self.candidate()
        # A valid baseline, with no old candidate to recover or provider due.
        self.pub.prepare(self.pub.head, NOW, files, revision, feed_publisher=publisher, artifact_profile='visual-v2')
        active = self.pub.ledger['pending']
        from tools.spacefox.publisher import LiveRevision
        self.pub.reconcile(LiveRevision(1, active['artifact_revision']))
        next_files, _, next_digest = self.candidate('b', 2)
        root = json.loads(next_files['feed.json'])
        legacy_only = {p: next_files[p] for p in ('feed.json', root['catalogPath'])}
        before = self.pub.head
        before_doc = self.pub.ledger
        source = build_catalog(ROOT)
        source['catalogVersion'] = 'r2-explicit-profile-fault'
        # Fault replaces only the producer result. Real prepare_content and
        # Publisher.prepare must carry their independent expected v2 profile.
        with patch('tools.cloud_feed.build_visual_artifact', return_value=(legacy_only, next_digest)):
            with self.assertRaises(StateError):
                prepare_content(self.pub, NoProvider(), NOW + 1, source, root=ROOT)
        self.assertEqual(before, self.pub.head)
        self.assertEqual(before_doc, self.pub.ledger)

    def test_prepare_without_envelope_cannot_bypass_product_admission(self):
        files, _, revision = self.candidate()
        del files['wire2/feed.json']
        before = self.pub.head
        with self.assertRaises(StateError):
            self.pub.prepare(before, NOW, files, revision)
        self.assertEqual(before, self.pub.head)
        self.assertIsNone(self.pub.ledger['pending'])

    def test_direct_store_write_refuses_rehashed_incomplete_product(self):
        files, _, _ = self.candidate()
        del files['wire2/feed.json']
        doc, raw = self.pending(files)
        before = self.pub.head
        with self.assertRaises(StateError):
            self.store.write(before, doc, raw)
        self.assertEqual(before, self.store.load()[0])

    def test_durable_reopen_refuses_authenticated_incomplete_product(self):
        files, _, _ = self.candidate()
        del files['wire2/feed.json']
        doc, raw = self.pending(files)
        # Bypass the public writer to represent already-durable corruption.
        # Real load must authenticate AND reject incomplete product closure.
        commit = self.store._commit(doc, self.pub.head, raw)
        result = self.store._git('push', f'--force-with-lease=refs/heads/feed-state:{self.pub.head}',
                                 self.store.remote, f'{commit}:refs/heads/feed-state')
        self.assertEqual(0, result.returncode)
        with self.assertRaises(StateError):
            Publisher(self.store, self.code)


class VisualBridgeGrammarReviewR2(unittest.TestCase):
    def test_compatibility_json_types_are_closed(self):
        from tools.spacefox.visual_bridge import validate_artifact
        files = prior.fixture('a')
        self.assertEqual(2, validate_artifact(files)['schemaVersion'])
        for field, value in (('previousMajor', True), ('currentMajor', 2.0),
                             ('announcedUtc', 1794441600.0), ('retainPreviousThroughUtc', 1802217600.0)):
            with self.subTest(field=field):
                modified = dict(files)
                feed = json.loads(files['wire2/feed.json'])
                feed['compatibility'][field] = value
                modified['wire2/feed.json'] = literal(feed)
                with self.assertRaises(ValueError):
                    validate_artifact(modified)

