"""Independent directed local metadata orchestration witnesses.

Only the external HTTP services are substituted. Expected IDs, times, tags,
body hashes and forbidden effects are literal; production Git, CLI, HTTP,
validation, source authority, reservation and cadence owners execute unchanged.
"""
from contextlib import contextmanager
from email.utils import formatdate
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import unittest
from urllib.parse import parse_qs, urlsplit

from tests import test_catalog_refresh as fixtures
from tests import test_cloud_runtime_checkout as runtime
from tests import test_metadata_cloud as metadata_fixture
from tools.refresh_catalog import scheduled
from tools.spacefox.catalog_refresh import CatalogRefresh
from tools.spacefox.cloud import arm
from tools.spacefox.publisher import GitState, LiveRevision, Publisher, StateError
from tools.spacefox.schedule import IdKind, LaunchRecord, LaunchStatus, StableId, Timing, TimePrecision

ROOT = Path(__file__).resolve().parents[1]
PATHS = ('/2.3.0/config/countries/', '/2.3.0/agencies/',
         '/2.3.0/launcher_configurations/', '/2.3.0/pads/')


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


def record(at):
    def identity(kind, value):
        return StableId(kind, 'll2', str(value))
    return LaunchRecord(identity(IdKind.LAUNCH, 'r1-orchestration'),
        Timing(TimePrecision.EXACT, exact_utc=at + 172800), LaunchStatus.PENDING, at - 123,
        configuration_id=identity(IdKind.CONFIGURATION, 303),
        operator_id=identity(IdKind.ORGANIZATION, 203),
        site_id=identity(IdKind.SITE, 403), country_id=identity(IdKind.COUNTRY, 103))


@contextmanager
def server(remote, now):
    world = dict(now=now, calls=[], conditional=False, failures=[])

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            store = GitState(str(remote))
            try:
                _, ledger = store.load()
                request = ledger['requests'][-1]
                valid = request['purpose'] == 'catalog' and request['outcome'] == 'reserved'
                if not valid:
                    world['failures'].append(request)
            finally:
                store.close()
            index = PATHS.index(urlsplit(self.path).path)
            query = parse_qs(urlsplit(self.path).query)
            expected = {'format': ['json'], 'limit': ['100']}
            if index:
                expected['mode'] = ['normal' if index == 1 else 'detailed']
            if index == 3:
                expected['ordering'] = ['id']
            if query != expected:
                world['failures'].append(query)
            tag = '"metadata-r1-' + str(index) + '"'
            conditional = self.headers.get('If-None-Match')
            status = 304 if world['conditional'] and conditional == tag else 200
            raw = world['bodies'][index] if status == 200 else b''
            world['calls'].append(dict(path=self.path, tag=conditional, status=status,
                                       reservedUtc=request['at_utc']))
            self.send_response_only(status)
            self.send_header('Date', formatdate(world['now'], usegmt=True))
            self.send_header('Age', '2')
            self.send_header('Content-Type', 'application/json')
            self.send_header('ETag', tag)
            self.send_header('Content-Length', str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

    service = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    origin = f'http://127.0.0.1:{service.server_port}'
    rows = [
        [dict(id=103, name='R1 country', alpha_2_code='XZ', alpha_3_code='XZZ')],
        [dict(id=203, name='R1 organization', url=origin + PATHS[1] + '203/',
              response_mode='normal', abbrev='', type=None, country=[{'id': 103}])],
        [dict(id=303, name='R1 inactive pending model', url=origin + PATHS[2] + '303/',
              response_mode='detailed', full_name='R1 exact model', variant='', active=False,
              pending_launches=2, is_placeholder=False, families=[],
              manufacturer={'id': 203, 'country': [{'id': 103}]})],
        [dict(id=403, name='R1 inactive referenced pad', url=origin + PATHS[3] + '403/',
              active=False, location=None, country={'id': 103}, latitude=None, longitude=None,
              agencies=[{'id': 203}])],
    ]
    world['bodies'] = [encode(dict(count=1, next=None, previous=None, results=values)) for values in rows]
    world['hashes'] = [hashlib.sha256(raw).hexdigest() for raw in world['bodies']]
    thread = threading.Thread(target=service.serve_forever, daemon=True)
    thread.start()
    try:
        yield origin, world
    finally:
        service.shutdown()
        service.server_close()
        thread.join()


class IndependentMetadataCadenceR1(unittest.TestCase):
    def test_literal_deadline_due_interruption_resume_and_conditional_replacement(self):
        with fixtures.CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, _, pub, _):
            slot = pub.reserve(pub.head, 1000, trigger='manual')
            pub.accept_source(pub.head, slot, (record(1000),), 1000, selection_validated_utc=877)
            with server(remote, 1003) as (origin, world):
                options = dict(origin=origin, local_http=True)
                before = pub.head
                for options_bad in ({'interval_seconds': 3599}, {'interval_seconds': 604801},
                                    {'max_requests': 0}, {'max_requests': 5}):
                    with self.assertRaises(StateError):
                        scheduled(pub, 1003, **options, **options_bad)
                    self.assertEqual(before, pub.head)
                    self.assertEqual([], world['calls'])
                first = scheduled(pub, 1003, max_requests=1, **options)
                self.assertEqual(('partial', 1), (first['status'], first['requests']))
                prefix = runtime.git(remote, 'ls-tree', '-r', pub.head, 'catalog-refresh')
                head = pub.head
                # Source becomes due while traversal is partial: no checkpoint,
                # allowance mutation or HTTP may precede source-writer work.
                blocked = scheduled(pub, 4600, **options)
                self.assertEqual(('yielded', 0, head), (blocked['status'], blocked['requests'], pub.head))
                self.assertEqual(prefix, runtime.git(remote, 'ls-tree', '-r', pub.head, 'catalog-refresh'))
                self.assertEqual(1, len(world['calls']))
                slot = pub.reserve(pub.head, 4600, trigger='manual')
                pub.accept_source(pub.head, slot, (record(1000),), 4600, selection_validated_utc=877)
                world['now'] = 4603
                second = scheduled(pub, 4603, max_requests=3, **options)
                self.assertEqual(('complete', 3), (second['status'], second['requests']))
                candidate = CatalogRefresh(pub, stable_sites_order=True, **options).current()
                self.assertEqual([1001, 4601, 4601, 4601], [p['validatedUtc'] for p in candidate['coverage']['pages']])
                self.assertEqual(world['hashes'], [p['body']['sha256'] for p in candidate['coverage']['pages']])
                self.assertEqual({'countries': [103], 'organizations': [203], 'models': [303], 'sites': [403]},
                                 candidate['coverage']['distinctIds'])
                self.assertEqual([303], candidate['coverage']['requiredModelIds'])
                self.assertEqual([403], candidate['coverage']['requiredSiteIds'])
                # The smallest supported cadence has an exact completion-based
                # boundary. Default daily cadence still suppresses the same tick.
                head = pub.head
                for at, interval in ((8202, 3600), (91002, 86400), (609402, 604800)):
                    idle = scheduled(pub, at, interval_seconds=interval, **options)
                    self.assertEqual(('not_due', 0, head), (idle['status'], idle['requests'], pub.head))
                self.assertEqual(4, len(world['calls']))
                slot = pub.reserve(pub.head, 8203, trigger='manual')
                pub.accept_source(pub.head, slot, (record(1000),), 8203, selection_validated_utc=877)
                preserved = {k: pub.ledger[k] for k in ('accepted', 'active', 'pending', 'generation',
                             'last_poll_utc', 'selection_validated_utc')}
                world.update(now=8203, conditional=True)
                replacement = scheduled(pub, 8203, interval_seconds=3600, **options)
                self.assertEqual(('complete', 4), (replacement['status'], replacement['requests']))
                candidate = CatalogRefresh(pub, stable_sites_order=True, **options).current()
                self.assertEqual([304] * 4, [p['status'] for p in candidate['coverage']['pages']])
                self.assertEqual([8201] * 4, [p['validatedUtc'] for p in candidate['coverage']['pages']])
                self.assertEqual(['"metadata-r1-' + str(i) + '"' for i in range(4)],
                                 [call['tag'] for call in world['calls'][4:]])
                self.assertEqual(preserved, {k: pub.ledger[k] for k in preserved})
                self.assertEqual([], world['failures'])
                self.assertEqual(8, len(world['calls']))
                print('R1_CADENCE_TRACE ' + json.dumps({'http': 8, 'partialDueYield': True,
                    'completionUtc': [4603, 8203], 'launchSourceUtc': 877, 'conditional': 4}, sort_keys=True))


class IndependentMetadataCliR1(unittest.TestCase):
    setUp = runtime.CloudRuntimeCheckoutTest.setUp
    tearDown = runtime.CloudRuntimeCheckoutTest.tearDown
    cli = runtime.CloudRuntimeCheckoutTest.cli
    snapshot = runtime.CloudRuntimeCheckoutTest.snapshot
    runtime = runtime.CloudRuntimeCheckoutTest.runtime

    def arguments(self, *command):
        args = runtime.CloudRuntimeCheckoutTest.arguments(self, *command)
        if hasattr(self, 'origin'):
            args[args.index('--origin') + 1] = self.origin
        return args

    def publisher(self):
        store = GitState(str(self.remote))
        self.stores.append(store)
        return Publisher(store, self.code)

    def reviewed_runtime(self):
        self.runtime('metadata')
        # The fixture clone starts at committed input HEAD. Copy only the
        # reviewed dirty repair owner, then commit/push to its local source ref;
        # the real CLI clean/source-authority checks still execute unchanged.
        path = 'tools/cloud_feed.py'
        raw = (ROOT / path).read_bytes()
        if (self.source / path).read_bytes() != raw:
            (self.source / path).write_bytes(raw)
            runtime.git(self.source, 'add', path)
            runtime.git(self.source, 'commit', '-qm', 'Exact reviewed metadata armed gate')
            self.code = runtime.git(self.source, 'rev-parse', 'HEAD')
            runtime.git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')

    @contextmanager
    def rich_server(self):
        # Reuse the prior independently authored tiny literal fixture matching
        # the frozen rich artifact. No validator/normalizer supplies these rows.
        world = metadata_fixture.MetadataCloudTest.metadata_server(self)
        world['hashes'] = [hashlib.sha256(raw).hexdigest() for raw in world['bodies'].values()]
        yield self.metadata_origin, world

    def test_rich_cli_unsafe_context_and_auxiliary_isolation(self):
        self.runtime('metadata')  # actual YAML sparse shell, never materializer
        store = GitState(str(self.remote))
        self.stores.append(store)
        store.bootstrap(self.code)
        pub = Publisher(store, self.code)
        pub.reconcile(None)
        def identity(kind, value):
            return StableId(kind, 'll2', str(value))
        launch = LaunchRecord(identity(IdKind.LAUNCH, 'bridge-literal'),
            Timing(TimePrecision.EXACT, exact_utc=runtime.NOW + 7200), LaunchStatus.PENDING, runtime.NOW - 3600,
            configuration_id=identity(IdKind.CONFIGURATION, 164), operator_id=identity(IdKind.ORGANIZATION, 121),
            site_id=identity(IdKind.SITE, 80), country_id=identity(IdKind.COUNTRY, 2),
            configuration_name='Falcon 9', operator_name='SpaceX', mission_name='Луна 零',
            mission_purpose='Measure lunar radiation', country_code='USA', site_location_name='Florida')
        slot = pub.reserve(pub.head, runtime.NOW, trigger='manual')
        pub.accept_source(pub.head, slot, (launch,), runtime.NOW,
                          selection_validated_utc=runtime.NOW - 3600)
        corpus = ROOT / 'tests/fixtures/bridge-v2/a'
        files = {p.relative_to(corpus).as_posix(): p.read_bytes() for p in corpus.rglob('*') if p.is_file()}
        self.assertEqual((76, 524776), (len(files), sum(map(len, files.values()))))
        for path in ('feed.json', 'wire2/feed.json'):
            value = json.loads(files[path])
            value['publisher'] = pub.publisher_envelope(runtime.NOW)
            files[path] = runtime.encoded(value)
        pub.prepare(pub.head, runtime.NOW, files, json.loads(files['feed.json'])['catalogDigest'],
                    feed_publisher=pub.publisher_envelope(runtime.NOW), artifact_profile='visual-v2')
        self.service.live = dict(files)
        pub, intent = arm(pub, expected=pub.head, repository='owner/SpaceFox',
                          run_id=85, run_attempt=1, artifact_id=899, now=runtime.NOW)
        self.service.statuses[intent['buildVersion']] = 'succeed'
        self.cli('recover')
        with self.rich_server() as (self.origin, world):
            before = self.snapshot()
            reads = len(self.service.reads)
            recipe = self.source / 'tools/refresh_catalog.py'
            raw = recipe.read_bytes()
            recipe.write_bytes(raw + b'\n# independent dirty guard\n')
            try:
                self.assertIn('committed and clean', self.cli('metadata', success=False))
            finally:
                recipe.write_bytes(raw)
            # Trusted-runtime context must fail before authority/HTTP. The URL,
            # remote and API remain loopback/local even in this invalid context.
            args = self.arguments('metadata')
            args.remove('--local-qualification')
            env = dict(os.environ, GITHUB_REPOSITORY='other/SpaceFox', GITHUB_REF='refs/heads/main',
                       GITHUB_SHA=self.code, GITHUB_EVENT_NAME='schedule')
            for key in ('GH_TOKEN', 'GITHUB_OUTPUT', 'GIT_CONFIG_COUNT'):
                env.pop(key, None)
            refusal = subprocess.run([sys.executable, '-B', 'tools/cloud_feed.py', *args],
                                      cwd=self.source, env=env, capture_output=True)
            self.assertEqual(2, refusal.returncode)
            self.assertIn(b'exact trusted main', refusal.stderr)
            for options in (('--interval-seconds', '3599'), ('--max-requests', '5')):
                self.assertIn('bounded metadata', self.cli('metadata', *options, success=False))
            self.assertEqual(reads, len(self.service.reads))
            self.assertEqual(before, self.snapshot())
            # A mixed mutable wire root refuses before metadata, even with an
            # otherwise exact rich immutable closure and source authority.
            self.service.live['wire2/feed.json'] += b' '
            self.cli('metadata', success=False)
            self.service.live['wire2/feed.json'] = files['wire2/feed.json']
            self.assertEqual(before, self.snapshot())
            self.assertEqual([], world['calls'])
            pub = self.publisher()
            original = {k: pub.ledger[k] for k in ('accepted', 'active', 'pending', 'generation',
                        'last_poll_utc', 'selection_validated_utc')}
            cloud = runtime.git(self.remote, 'show', f'{pub.head}:cloud.json')
            result = self.cli('metadata')
            self.assertEqual(('complete', 4), (result['status'], result['requests']))
            pub = self.publisher()
            candidate = CatalogRefresh(pub, origin=self.origin, local_http=True, stable_sites_order=True).current()
            self.assertEqual(world['hashes'], [p['body']['sha256'] for p in candidate['coverage']['pages']])
            self.assertEqual([runtime.NOW - 2] * 4, [p['validatedUtc'] for p in candidate['coverage']['pages']])
            self.assertEqual(original, {k: pub.ledger[k] for k in original})
            self.assertEqual(cloud, runtime.git(self.remote, 'show', f'{pub.head}:cloud.json'))
            self.assertEqual(files, {p.split('/', 2)[2]: raw for p, raw in pub.store._files(pub.head, pub.ledger).items()})
            before = self.snapshot()
            idle = self.cli('metadata')
            self.assertEqual(('not_due', 0), (idle['status'], idle['requests']))
            self.assertEqual(before, self.snapshot())
            auxiliary = runtime.git(self.remote, 'ls-tree', '-r', pub.head, 'catalog-refresh')
            pub.reconcile(LiveRevision(1, pub.ledger['active']['artifact_revision']))
            slot = pub.reserve(pub.head, runtime.NOW, trigger='manual')
            pub.accept_source(pub.head, slot, (launch,), runtime.NOW,
                              selection_validated_utc=runtime.NOW - 3600)
            self.assertEqual(auxiliary, runtime.git(self.remote, 'ls-tree', '-r', pub.head, 'catalog-refresh'))
            replacement = dict(files)
            for path in ('feed.json', 'wire2/feed.json'):
                value = json.loads(replacement[path])
                value['publisher'] = pub.publisher_envelope(runtime.NOW)
                replacement[path] = runtime.encoded(value)
            pub.prepare(pub.head, runtime.NOW, replacement, json.loads(replacement['feed.json'])['catalogDigest'],
                        feed_publisher=pub.publisher_envelope(runtime.NOW), artifact_profile='visual-v2')
            pub, _ = arm(pub, expected=pub.head, repository='owner/SpaceFox',
                         run_id=87, run_attempt=1, artifact_id=901, now=runtime.NOW)
            before, reads = self.snapshot(), len(self.service.reads)
            pending = self.cli('metadata')
            self.assertEqual(('yielded_pending', 0), (pending['status'], pending['requests']))
            runtime.git(self.source, 'commit', '--allow-empty', '-qm', 'R1 source authority event')
            old = self.code
            self.code = runtime.git(self.source, 'rev-parse', 'HEAD')
            runtime.git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
            self.assertIn('source writer adoption', self.cli('metadata', success=False))
            runtime.git(self.source, 'checkout', '-q', old)
            self.assertIn('queued source code is stale', self.cli('metadata', success=False))
            self.assertEqual(before, self.snapshot())
            self.assertEqual(reads, len(self.service.reads))
            self.assertEqual((4, 0, 0), (len(world['calls']), self.service.provider_calls, len(self.service.posts)))
            print('R1_RICH_CLI_TRACE ' + json.dumps({'richFiles': 76, 'metadataHttp': 4,
                'launchSourceUtc': runtime.NOW - 3600, 'metadataSourceUtc': runtime.NOW - 2,
                'primaryHttp': 0, 'posts': 0, 'notDueWrites': 0,
                'unsafeContextAndMixedLiveRefused': True, 'pendingAndAdoptionRefused': True}, sort_keys=True))

    def test_armed_active_journal_yields_before_recovery_then_explicit_owner_recovers(self):
        self.reviewed_runtime()
        pub, _, files = runtime.CloudRuntimeCheckoutTest.authority(self)
        pub, intent = arm(pub, expected=pub.head, repository='owner/SpaceFox',
                          run_id=85, run_attempt=1, artifact_id=899, now=runtime.NOW)
        # Legal core event, not private-state injection: trusted exact live
        # promotion does not itself own or finalize the separate cloud journal.
        pending = pub.ledger['pending']
        self.service.live = dict(files)
        self.service.statuses[intent['buildVersion']] = 'succeed'
        pub.reconcile(LiveRevision(1, pending['artifact_revision']))
        self.assertIsNone(pub.ledger['pending'])
        before, reads = self.snapshot(), len(self.service.reads)
        result = self.cli('metadata')
        observed = dict(status=result['status'], requests=result['requests'],
                        headUnchanged=self.snapshot() == before,
                        serviceReads=len(self.service.reads) - reads)
        print('R1_ARMED_GATE ' + json.dumps(observed, sort_keys=True))
        self.assertEqual(dict(status='yielded_armed', requests=0, headUnchanged=True, serviceReads=0), observed)
        # Explicit recovery still owns finality/readback and remains available;
        # afterward normal metadata may pass its new read-only armed gate.
        self.cli('recover')
        pub = self.publisher()
        pub.reconcile(LiveRevision(1, pub.ledger['active']['artifact_revision']))
        slot = pub.reserve(pub.head, runtime.NOW, trigger='manual')
        pub.accept_source(pub.head, slot, (), runtime.NOW, selection_validated_utc=runtime.NOW - 3600)
        result = self.cli('metadata')
        self.assertEqual(('complete', 4), (result['status'], result['requests']))
        self.assertEqual(4, self.service.provider_calls)
        metadata_paths = [urlsplit(p).path for p in self.service.reads if p.startswith('/2.3.0/')]
        self.assertEqual(list(PATHS), metadata_paths)
        before = self.snapshot()
        result = self.cli('metadata')
        self.assertEqual(('not_due', 0), (result['status'], result['requests']))
        self.assertEqual(before, self.snapshot())
        self.assertEqual((4, 0), (self.service.provider_calls, len(self.service.posts)))

    def test_no_journal_normal_metadata_retains_live_readback_and_no_due_effects(self):
        self.reviewed_runtime()
        pub, _, files = runtime.CloudRuntimeCheckoutTest.authority(self)
        self.service.live = dict(files)
        pub.reconcile(LiveRevision(1, pub.ledger['pending']['artifact_revision']))
        slot = pub.reserve(pub.head, runtime.NOW, trigger='manual')
        pub.accept_source(pub.head, slot, (), runtime.NOW, selection_validated_utc=runtime.NOW - 3600)
        result = self.cli('metadata')
        self.assertEqual(('complete', 4), (result['status'], result['requests']))
        before, reads = self.snapshot(), len(self.service.reads)
        result = self.cli('metadata')
        self.assertEqual(('not_due', 0), (result['status'], result['requests']))
        self.assertEqual(before, self.snapshot())
        # Exact live readback still occurs even though collector cadence is idle.
        self.assertGreater(len(self.service.reads), reads)
        self.assertEqual((4, 0), (self.service.provider_calls, len(self.service.posts)))
        pub = self.publisher()
        self.assertNotEqual(0, pub.store._git('cat-file', '-e', f'{pub.head}:cloud.json', check=False).returncode)
