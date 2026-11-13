"""Current source-to-durable-delivery integration using a retained real launch.

The fixture is an exact captured raw provider page; tests extract its unchanged
Starship record at the recorded Date validation epoch. It is a controlled replay,
not a new provider observation. Git and the local renderer run for real; HTTP and
Pages finality are controlled ports. No provider or hosted service is called.
"""
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.spacefox.catalog import build_catalog
from tools.spacefox.cloud import arm, delivery, delivery_files, journal, recover, Site
from tools.spacefox.native_motion import PROFILE, build_artifact, validate_artifact, validate_feed
from tools.spacefox.provider import normalize_launch
from tools.spacefox.publisher import AllowanceUnavailable, GitState, Publisher

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/provider/current-starship/captured-page.json.gz'
FIXTURE_SHA = 'b8193158aa573007aa47c2bff7993171056c72876dc5992e4b4794cbb7dff4a9'
NOW = 1794551192  # Fri, 13 Nov 2026 06:26:32 GMT: captured response Date.


def captured_starship():
    from tools.spacefox.provider import Response, validation_epoch
    receipt = json.loads(FIXTURE.with_name('receipt.json').read_bytes())
    compressed = FIXTURE.read_bytes()
    if hashlib.sha256(compressed).hexdigest() != receipt['compressedSha256']:
        raise AssertionError('compressed source page changed')
    raw = gzip.decompress(compressed)
    if len(raw) != receipt['rawPageBytes'] or hashlib.sha256(raw).hexdigest() != FIXTURE_SHA:
        raise AssertionError('raw source page changed')
    # This captured broad-query response exceeds the upcoming adapter's page
    # bound. Extract one exact record; do not pass it off as an upcoming page.
    row = next(r for r in json.loads(raw)['results'] if r['id'] == receipt['launchId'])
    encoded = json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    if hashlib.sha256(encoded).hexdigest() != receipt['recordSha256']:
        raise AssertionError('source record changed')
    if validation_epoch(Response(200, receipt['sourceHeaders'], b''), NOW) != NOW:
        raise AssertionError('captured validation epoch changed')
    return row


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], stderr=subprocess.DEVNULL).decode().strip()


class MemoryHTTP:
    def __init__(self, files): self.files = files
    def request(self, method, url, *, limit):
        name = url.split('/site/', 1)[1]
        raw = self.files.get(name)
        return (404, b'') if raw is None else (200, raw)


class CurrentMotionPublisherTest(unittest.TestCase):
    def test_operator_cli_prepares_current_artifact(self):
        import sys
        with tempfile.TemporaryDirectory(prefix='spacefox-operator-') as tmp:
            path = Path(tmp); remote = path / 'remote.git'; source = path / 'source'; source.mkdir()
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            git(source, 'init', '-q'); git(source, 'config', 'user.name', 'Local qualification')
            git(source, 'config', 'user.email', 'local@example.invalid')
            git(source, 'commit', '--allow-empty', '-qm', 'source')
            code = git(source, 'rev-parse', 'HEAD')
            git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            try:
                store.bootstrap(code)
                pub = Publisher(store, code); pub.reconcile(None)
                files, digest = build_artifact(pub.schedule, build_catalog(ROOT), NOW,
                    publisher=pub.publisher_envelope(NOW), root=ROOT)
                directory = path / 'candidate'; directory.mkdir()
                for name, raw in files.items():
                    target = directory / name; target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(raw)
                result = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/publisher_state.py'),
                    '--remote', str(remote), '--running-code', code, '--expected-base', pub.head,
                    'prepare', '--now', str(NOW), '--catalog-revision', digest,
                    '--directory', str(directory)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                reopened = Publisher(store, code)
                self.assertEqual(reopened.ledger['pending']['artifact_profile'], PROFILE)
                self.assertEqual(reopened.pending_files(), files)
                self.assertEqual(json.loads(result.stdout)['result']['generation'], 1)
            finally:
                store.close()

    def test_cloud_journal_updates_current_state_ref(self):
        from tools.spacefox.cloud import write_journal
        from tools.spacefox.publisher import ANCHOR_REF, STATE_REF, Conflict
        self.assertEqual(STATE_REF, 'refs/heads/feed-state-map-v3')
        self.assertEqual(ANCHOR_REF, 'refs/tags/spacefox-state-bootstrap-map-v3')
        with tempfile.TemporaryDirectory(prefix='spacefox-journal-') as tmp:
            path = Path(tmp); remote = path / 'remote.git'; source = path / 'source'; source.mkdir()
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            git(source, 'init', '-q'); git(source, 'config', 'user.name', 'Local qualification')
            git(source, 'config', 'user.email', 'local@example.invalid')
            git(source, 'commit', '--allow-empty', '-qm', 'source')
            code = git(source, 'rev-parse', 'HEAD')
            git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            old_state = 'refs/heads/feed-state-motion-v3'
            old_anchor = 'refs/tags/spacefox-state-bootstrap-motion-v3'
            git(source, 'push', '-q', str(remote), code+':'+old_state, code+':'+old_anchor)
            store = GitState(str(remote))
            try:
                store.bootstrap(code)
                pub = Publisher(store, code)
                before = pub.head
                self.assertEqual(store._refs(ANCHOR_REF)[ANCHOR_REF], before)
                updated = write_journal(pub, {'test': 'journal'})
                self.assertNotEqual(updated.head, before)
                self.assertEqual(store._refs(STATE_REF)[STATE_REF], updated.head)
                self.assertEqual(store._blob(updated.head, 'cloud.json', 1024), b'{"test":"journal"}')
                with self.assertRaises(Conflict):
                    write_journal(pub, {'test': 'stale'})
                self.assertEqual(store._refs(STATE_REF)[STATE_REF], updated.head)
                self.assertEqual(store._refs(ANCHOR_REF)[ANCHOR_REF], before)
                self.assertEqual(store._refs('refs/heads/feed-state'), {})
                self.assertEqual(store._refs(old_state, old_anchor), {old_state: code, old_anchor: code})
            finally:
                store.close()

    def test_current_policy_requires_complete_explicit_envelope(self):
        from tools.spacefox.catalog import canonical_bytes
        from tools.spacefox.schedule import ScheduleState
        files, _ = build_artifact(ScheduleState(), build_catalog(ROOT), NOW,
            publisher=dict(instance='a'*64, generation=1, selectionValidatedUtc=None), root=ROOT)
        feed = validate_artifact(files)
        self.assertEqual(feed['refreshPolicy'], dict(normal_interval_seconds=3600,
            near_interval_seconds=900, fast_interval_seconds=None, stale_cycles=3))
        for incomplete in ({}, {'normal_interval_seconds': 3600}):
            with self.subTest(policy=incomplete):
                altered = dict(feed, refreshPolicy=incomplete)
                with self.assertRaises(ValueError):
                    validate_artifact(dict(files, **{'feed.json': canonical_bytes(altered)}))

    def test_durable_policy_and_selected_cadence_bind_current_artifact(self):
        from copy import deepcopy
        from tools.spacefox.catalog import canonical_bytes
        from tools.spacefox.cloud import snapshot_files
        from tools.spacefox.publisher import STATE_REF, StateError, _canonical, _sha
        from tools.spacefox.schedule import RefreshPolicy
        with tempfile.TemporaryDirectory(prefix='spacefox-policy-binding-') as tmp:
            path = Path(tmp); remote = path / 'remote.git'; source = path / 'source'; source.mkdir()
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            git(source, 'init', '-q'); git(source, 'config', 'user.name', 'Local qualification')
            git(source, 'config', 'user.email', 'local@example.invalid')
            git(source, 'commit', '--allow-empty', '-qm', 'source')
            code = git(source, 'rev-parse', 'HEAD')
            git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            try:
                # A nondefault bootstrap policy must survive every admission
                # boundary; an artifact's own valid policy is not authority.
                policy = RefreshPolicy(normal_interval_seconds=7200, near_interval_seconds=1800, stale_cycles=4)
                anchor = store.bootstrap(code, policy)
                pub = Publisher(store, code); pub.reconcile(None)
                files, digest = build_artifact(pub.schedule, build_catalog(ROOT), NOW,
                    publisher=pub.publisher_envelope(NOW), policy=policy, root=ROOT)
                original = validate_artifact(files)
                self.assertEqual(original['pollIntervalSeconds'], 7200)
                cases = [('policy', dict(original, refreshPolicy=dict(vars(policy), stale_cycles=3))),
                         ('cadence', dict(original, pollIntervalSeconds=1800))]
                for name, feed in cases:
                    with self.subTest(boundary='prepare', mutation=name):
                        altered = dict(files, **{'feed.json': canonical_bytes(feed)})
                        validate_artifact(altered)  # Structurally valid current packet.
                        before = store.load()[0]
                        try:
                            with self.assertRaises(StateError):
                                pub.prepare(pub.head, NOW, altered, digest, artifact_profile=PROFILE)
                            self.assertEqual(store.load()[0], before)
                        finally:
                            # Isolate negative cases even on the expected red run.
                            head = store._refs(STATE_REF)[STATE_REF]
                            store._git('push', f'--force-with-lease={STATE_REF}:{head}', str(remote), f'{anchor}:{STATE_REF}')
                            pub = Publisher(store, code); pub.reconcile(None)
                pub.prepare(pub.head, NOW, files, digest, artifact_profile=PROFILE)
                good = pub.head
                doc = pub.ledger
                self.assertEqual(Publisher(store, code).pending_files(), files)
                self.assertEqual(snapshot_files(store, good, 1)[1], files)
                for name, feed in cases:
                    # Re-pin actual current bytes and snapshot hash so ordinary
                    # hash/transition checks cannot mask the semantic guard.
                    changed = deepcopy(doc)
                    altered = dict(files, **{'feed.json': canonical_bytes(feed)})
                    snap = changed['pending']
                    snap['files']['feed.json'] = dict(sha256=_sha(altered['feed.json']), bytes=len(altered['feed.json']))
                    snap['artifact_revision'] = _sha(_canonical({k: v for k, v in snap.items() if k != 'artifact_revision'}))
                    bad = store._commit(changed, anchor, {f'artifacts/1/{k}': v for k, v in altered.items()})
                    for boundary in ('reopen', 'cloud-origin'):
                        with self.subTest(boundary=boundary, mutation=name):
                            try:
                                if boundary == 'reopen':
                                    store._git('push', f'--force-with-lease={STATE_REF}:{good}', str(remote), f'{bad}:{STATE_REF}')
                                    with self.assertRaises(StateError):
                                        Publisher(store, code)
                                else:
                                    with self.assertRaises(StateError):
                                        snapshot_files(store, bad, 1)
                            finally:
                                head = store._refs(STATE_REF)[STATE_REF]
                                if head != good:
                                    store._git('push', f'--force-with-lease={STATE_REF}:{head}', str(remote), f'{good}:{STATE_REF}')
                self.assertEqual(Publisher(store, code).pending_files(), files)
            finally:
                store.close()

    def test_current_integer_discriminators(self):
        from tools.spacefox.schedule import ScheduleState, merge_schedule
        record = normalize_launch(captured_starship(), NOW)
        state = merge_schedule(ScheduleState(), (record,), NOW)
        files, _ = build_artifact(state, build_catalog(ROOT), NOW,
            publisher=dict(instance='a'*64, generation=1, selectionValidatedUtc=NOW), root=ROOT)
        self.assert_current_integer_discriminators(files)

    def assert_current_integer_discriminators(self, files):
        from decimal import Decimal
        from tools.spacefox.catalog import canonical_bytes, loads_json
        from tools.spacefox.native_motion import _index

        def altered_artifact(target, field, value):
            # Rewrite only the selected value, then re-pin every ancestor and
            # transfer index so digest/closure failures cannot mask the guard.
            rebuilt, memo = {}, {}
            def document(path):
                if path in memo:
                    return memo[path]
                raw = files[path]
                if path.endswith('.json'):
                    row = loads_json(raw)
                    row = walk(row)
                    if isinstance(row, dict) and row.get('type') == 'native-transfer':
                        row = _index(rebuilt, row['scene'])
                    if path == target:
                        row[field] = value
                    raw = canonical_bytes(row)
                digest = hashlib.sha256(raw).hexdigest()
                name = 'feed.json' if path == 'feed.json' else path.rsplit('/', 1)[0] + '/' + digest + Path(path).suffix
                rebuilt[name] = raw
                memo[path] = dict(path=name, sha256=digest, decodedBytes=len(raw))
                return memo[path]
            def walk(row):
                if isinstance(row, list):
                    return [walk(v) for v in row]
                if not isinstance(row, dict):
                    return row
                if set(row) == {'path', 'sha256', 'decodedBytes'}:
                    return document(row['path'])
                row = {k: walk(v) for k, v in row.items()}
                if 'catalogPath' in row:
                    pin = document(row['catalogPath'])
                    row.update(catalogPath=pin['path'], catalogDigest=pin['sha256'])
                return row
            document('feed.json')
            return rebuilt

        feed = loads_json(files['feed.json'])
        scene_path = feed['visualSelection']['path']
        scene = loads_json(files[scene_path])
        rocket_path = scene['roles']['rocket']['descriptor']['path']
        rocket = loads_json(files[rocket_path])
        map_path = scene['roles']['map']['descriptor']['path']
        self.assertEqual(altered_artifact(scene_path, 'schemaVersion', 3), files)
        mutations = [
            ('feed', 'feed.json', 'schemaVersion', Decimal('3.0')),
            ('feed-bool', 'feed.json', 'schemaVersion', True),
            ('catalog', feed['catalogPath'], 'schemaVersion', Decimal('3.0')),
            ('scene', scene_path, 'schemaVersion', Decimal('3.0')),
            ('source-schema', scene['sourceSelection']['path'], 'schemaVersion', Decimal('3.0')),
            ('source-renderer', scene['sourceSelection']['path'], 'rendererVersion', True),
            ('origin-schema', scene['origins']['model']['sourceRecord']['path'], 'schemaVersion', True),
            ('map-schema', loads_json(files[map_path])['sourceDescriptor']['path'], 'schemaVersion', Decimal('2.0')),
            ('raster-schema', rocket_path, 'schemaVersion', Decimal('2.0')),
            ('raster-channels', rocket_path, 'channels', Decimal('4.0')),
            ('raster-canvas', rocket_path, 'canvas', [Decimal('54.0'), 124]),
            ('motion-canvas', rocket_path, 'sourceCanvas', [Decimal(str(rocket['sourceCanvas'][0]) + '.0'), rocket['sourceCanvas'][1]]),
            ('motion-schema', rocket['motionSource']['path'], 'schemaVersion', True),
            ('static-animation', map_path, 'animation', [False, []]),
            ('transfer-schema', feed['nativeTransfer']['path'], 'schemaVersion', True),
        ]
        for name, target, field, value in mutations:
            with self.subTest(discriminator=name):
                candidate = altered_artifact(target, field, value)
                with self.assertRaises(ValueError):
                    validate_artifact(candidate)

    def test_actual_launch_whole_publication_and_refusal(self):
        row = captured_starship()
        self.assertEqual(row['id'], '0f867f0c-5422-4d44-93b8-d7faaae7019b')
        record = normalize_launch(row, NOW)
        self.assertEqual(record.mission_purpose, 'Communications')
        self.assertEqual(record.timing.source_net, '2026-11-13T22:45:00Z')
        self.assertEqual(record.configuration_id.value, '522')
        self.assertEqual(record.source_validated_utc, NOW)
        with tempfile.TemporaryDirectory(prefix='spacefox-current-') as tmp:
            path = Path(tmp); remote = path / 'remote.git'; source = path / 'source'; source.mkdir()
            subprocess.run(['git','init','--bare','-q',str(remote)], check=True)
            git(source, 'init', '-q'); git(source, 'config', 'user.name', 'Local qualification')
            git(source, 'config', 'user.email', 'local@example.invalid')
            git(source, 'commit', '--allow-empty', '-qm', 'source')
            code = git(source, 'rev-parse', 'HEAD'); git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            try:
                store.bootstrap(code)
                pub = Publisher(store, code); self.assertEqual(pub.reconcile(None), 'ready')
                token = pub.reserve(pub.head, NOW, trigger='manual')
                pub.accept_source(pub.head, token, (record,), NOW, selection_validated_utc=NOW)
                catalog = build_catalog(ROOT)
                envelope = pub.publisher_envelope(NOW)
                files, digest = build_artifact(pub.schedule, catalog, NOW, publisher=envelope, root=ROOT)
                feed = validate_feed(files['feed.json'])
                self.assertEqual((feed['schemaVersion'], feed['rendererProfile']), (3, 'SFR1M'))
                self.assertNotIn('compatibility', feed)
                self.assertEqual(feed['launch']['launch_id'], 'll2:launch:' + row['id'])
                self.assertEqual(feed['publisher']['selectionValidatedUtc'], NOW)
                self.assertFalse(any(p.startswith(('wire2/', 'catalogs/')) or p in ('wire3/feed.json','wire3/motion/feed.json') for p in files))
                self.assertEqual(digest, feed['catalogDigest'])
                broken = dict(files); raster = next(p for p in files if p.startswith('rasters/'))
                broken[raster] += b'x'
                with self.assertRaises(ValueError): validate_artifact(broken)
                wrong = json.loads(files['feed.json']); wrong['schemaVersion'] = 2
                from tools.spacefox.catalog import canonical_bytes
                with self.assertRaises(ValueError): validate_feed(canonical_bytes(wrong))
                wrong=json.loads(files['feed.json']);wrong['launch']=list(wrong['launch'].items())
                with self.assertRaises(ValueError): validate_feed(canonical_bytes(wrong))
                revision = pub.prepare(pub.head, NOW, files, digest, feed_publisher=envelope, artifact_profile=PROFILE)
                delivered = delivery_files(pub, delivery(pub))
                self.assertEqual(delivered, files)
                pub, intent = arm(pub, expected=pub.head, repository='local/spacefox',
                                  run_id=1, run_attempt=1, artifact_id=1, now=NOW)
                pub = Publisher(store, code)
                self.assertEqual(journal(pub)['intent'], intent)
                class FinalPages:
                    repository = 'local/spacefox'
                    def wait(self, build_version):
                        self.build_version = build_version
                        return 'succeed'
                pages = FinalPages()
                site = Site('http://127.0.0.1:12345/site', local_http=True, http=MemoryHTTP(delivered))
                self.assertEqual(site.observe(pub), revision)
                pub = recover(pub, site, pages)
                pub = Publisher(store, code)
                self.assertEqual(pages.build_version, intent['buildVersion'])
                self.assertEqual(journal(pub)['status'], 'succeed')
                self.assertEqual(pub.ledger['active']['generation'], 1)
                self.assertEqual(pub.ledger['selection_validated_utc'], NOW)
                self.assertEqual(len(pub.ledger['requests']), 1)
                self.assertEqual(pub.reconcile(revision), 'ready')
                # Rebuild from the same accepted source, with its original validation
                # epoch, and recover after reopening while the next candidate waits.
                second_envelope=pub.publisher_envelope(NOW+1)
                second, second_digest=build_artifact(pub.schedule,catalog,NOW+1,publisher=second_envelope,root=ROOT)
                second_revision=pub.prepare(pub.head,NOW+1,second,second_digest,
                                            feed_publisher=second_envelope,artifact_profile=PROFILE)
                retained=delivery_files(pub,delivery(pub))
                self.assertTrue(all(retained[p]==v for p,v in files.items() if p!='feed.json'))
                self.assertEqual(retained['feed.json'],second['feed.json'])
                pub=Publisher(store,code)
                self.assertEqual(pub.reconcile(revision),'retry_pending')
                self.assertEqual(pub.pending_files(),second)
                self.assertEqual(pub.ledger['selection_validated_utc'],NOW)
                current_site=Site('http://127.0.0.1:12345/site',local_http=True,http=MemoryHTTP(retained))
                self.assertEqual(current_site.observe(pub),second_revision)
                self.assertEqual(pub.reconcile(second_revision),'promoted')
                self.assertEqual(pub.ledger['active']['generation'],2)
                self.assertEqual(pub.ledger['selection_validated_utc'],NOW)
                self.assertEqual(len(pub.ledger['requests']),1)
            finally:
                store.close()

    def test_shared_rolling_hour_quota_survives_reopen(self):
        with tempfile.TemporaryDirectory(prefix='spacefox-quota-') as tmp:
            path=Path(tmp); remote=path/'remote.git'; source=path/'source'; source.mkdir()
            subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
            git(source,'init','-q');git(source,'config','user.name','Local qualification')
            git(source,'config','user.email','local@example.invalid');git(source,'commit','--allow-empty','-qm','source')
            code=git(source,'rev-parse','HEAD');git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
            store=GitState(str(remote))
            try:
                store.bootstrap(code);pub=Publisher(store,code);pub.reconcile(None)
                for _ in range(15):
                    token=pub.reserve(pub.head,NOW,trigger='extra')
                    pub.finish_request(pub.head,token,NOW,'success')
                saved=pub.head;pub=Publisher(store,code);pub.reconcile(None)
                with self.assertRaises(AllowanceUnavailable): pub.reserve(pub.head,NOW+1,trigger='extra')
                self.assertEqual(pub.head,saved)
                self.assertEqual(len(pub.ledger['requests']),15)
                token=pub.reserve(pub.head,NOW+3600,trigger='extra')
                self.assertIsNotNone(token)
                self.assertEqual(len(pub.ledger['requests']),1)
            finally:
                store.close()
