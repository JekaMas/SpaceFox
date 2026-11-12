"""Actual bare Git + local HTTP/async Pages faults, with literal state oracles.

Only GitHub/Pages/LL2 services and artifact upload are substituted. These are
local delivery observations, never authentic Actions/Pages or device acceptance.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import format_datetime
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from tools.cloud_feed import context
from tools.spacefox.cloud import (CloudError, HTTP, Pages, Site, arm, delivery,
                                  delivery_files, deploy, journal, recover)
from tools.spacefox.publisher import Conflict, GitState, Publisher, StateError
from tools.spacefox.provider import LL2Client, ProviderError
from tools.spacefox.catalog import build_catalog
from tools.update_feed import update

ROOT = Path(__file__).resolve().parents[1]
NOW = 1794441600


def git(path, *args):
    return subprocess.run(['git', '-C', str(path), *args], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout.decode().strip()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def literal_files(instance, generation=1, version='A'):
    # Independently authored empty wire values, not build_artifact/roundtrip.
    catalog = encoded({'schemaVersion': 1, 'catalogVersion': version,
                       'qualification': 'publisher-metadata-only', 'entries': {}, 'unresolved': []})
    digest = hashlib.sha256(catalog).hexdigest()
    path = f'catalogs/{digest}.json'
    feed = encoded({'schemaVersion': 1, 'publisher': {'instance': instance, 'generation': generation,
                    'selectionValidatedUtc': None}, 'catalogRevision': version,
                    'catalogDigest': digest, 'catalogPath': path, 'dictionaries': {},
                    'unresolvedCatalogIds': [], 'launch': None, 'timingState': 'no-schedule',
                    'refreshPolicy': {'normal_interval_seconds': 3600, 'near_interval_seconds': 900,
                                      'fast_interval_seconds': None, 'stale_cycles': 3},
                    'pollIntervalSeconds': 3600, 'sourceContentRevision': hashlib.sha256(b'[]').hexdigest(),
                    'selection': {'acceptedRecords': 0, 'includedRecords': 0,
                                  'scope': 'selected-launch', 'worldwideCompleteness': False},
                    'providerTraversal': None})
    return {'feed.json': feed, path: catalog}, digest


class World:
    def __init__(self, remote):
        self.remote, self.live, self.artifact = remote, {}, {}
        self.posts, self.gets, self.statuses, self.errors = [], [], {}, []
        self.status = 'succeed'
        self.override_status = False
        self.drop_post = False
        self.drop_provider = False
        self.provider_calls = 0
        self.cancel_final = 'deployment_cancelled'
        world = self

        class Handler(BaseHTTPRequestHandler):
            def date_time_string(self, timestamp=None):
                return format_datetime(datetime.fromtimestamp(NOW, timezone.utc), usegmt=True)

            def log_message(self, *args):
                pass

            def send(self, status, raw=b'', declared=None):
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw) if declared is None else declared))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                world.gets.append(self.path)
                if '/pages/deployments/' in self.path:
                    version = self.path.rsplit('/', 1)[-1]
                    state = world.status if world.override_status else world.statuses.get(version)
                    self.send(404 if state is None else 200, b'' if state is None else encoded({'status': state}))
                elif self.path.startswith('/2.3.0/'):
                    world.provider_calls += 1
                    raw = git(world.remote, 'show', 'refs/heads/feed-state:ledger.json')
                    ledger = json.loads(raw)
                    if not ledger['requests'] or ledger['requests'][-1]['outcome'] != 'reserved':
                        world.errors.append('provider request had no committed reservation')
                    if world.drop_provider:
                        self.close_connection = True
                        return
                    self.send(200, encoded({'count': 0, 'next': None, 'previous': None, 'results': []}))
                else:
                    path = self.path.removeprefix('/site/')
                    raw = world.live.get(path)
                    self.send(404 if raw is None else 200, b'' if raw is None else raw)

            def do_POST(self):
                if self.path.endswith('/cancel'):
                    version = self.path.split('/')[-2]
                    world.statuses[version] = world.cancel_final
                    self.send(200, encoded({'status': 'cancel_pending'}))
                    return
                data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                durable = json.loads(git(world.remote, 'show', 'refs/heads/feed-state:cloud.json'))
                intent = durable['intent']
                if (durable['status'] != 'armed' or data.get('pages_build_version') != intent['buildVersion']
                        or data.get('artifact_id') != intent['artifactId']):
                    world.errors.append('POST preceded exact committed intent')
                world.posts.append(data)
                version = data['pages_build_version']
                world.statuses[version] = world.status
                world.live = dict(world.artifact)
                if world.drop_post:
                    self.close_connection = True
                    return
                self.send(200, encoded({'id': 'remote-id-not-needed-for-recovery'}))

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.server.server_port)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class CloudDeliveryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.remote, self.source = self.root / 'remote.git', self.root / 'source'
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        git(self.source, 'config', 'user.name', 'Delivery test')
        git(self.source, 'config', 'user.email', 'test@example.invalid')
        git(self.source, 'commit', '--allow-empty', '-qm', 'source1')
        self.code = git(self.source, 'rev-parse', 'HEAD')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.store = GitState(str(self.remote))
        self.store.bootstrap(self.code)
        self.pub = Publisher(self.store, self.code)
        self.pub.reconcile(None)
        self.world = World(self.remote)
        self.pages = Pages('owner/SpaceFox', 'local-test-token', api=self.world.base, local_http=True)
        self.site = Site(self.world.base + '/site', local_http=True)
        self.instance = self.pub.ledger['instance_id']

    def tearDown(self):
        self.world.close()
        self.store.close()
        self.tmp.cleanup()

    def pending(self, generation=1, version='A', now=NOW):
        files, digest = literal_files(self.instance, generation, version)
        self.pub.prepare(self.pub.head, now, files, digest,
                         feed_publisher={'instance': self.instance, 'generation': generation,
                                         'selectionValidatedUtc': None})
        return files

    def armed(self, run=10):
        self.pub, intent = arm(self.pub, expected=self.pub.head, repository='owner/SpaceFox',
                               run_id=run, run_attempt=1, artifact_id=99, now=NOW)
        return intent

    def send(self):
        return deploy(self.pub, self.pages, self.site, expected=self.pub.head, repository='owner/SpaceFox',
                      run_id=10, run_attempt=1, id_token='local-oidc', polls=1)

    def test_first_second_exact_delivery(self):
        first = self.pending()
        before = self.pub.head
        self.assertEqual(first, delivery_files(self.pub, delivery(self.pub)))
        intent = self.armed()
        self.assertEqual(before, intent['buildVersion'])
        self.world.artifact = first
        self.assertEqual('succeed', self.send())
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual(1, self.pub.ledger['active']['generation'])
        self.assertIsNone(self.pub.ledger['pending'])
        second = self.pending(2, 'B', NOW + 3600)
        expected = {**first, **second}
        self.assertEqual(expected, delivery_files(self.pub, delivery(self.pub)))
        self.armed()
        self.world.artifact = expected
        self.assertEqual('succeed', self.send())
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual((2, None, []), (self.pub.ledger['active']['generation'],
                                       self.pub.ledger['pending'], self.pub.ledger['requests']))
        self.assertIsNone(self.pub.ledger['selection_validated_utc'])
        self.assertEqual(2, len(self.world.posts))
        self.assertEqual(2, len({p['pages_build_version'] for p in self.world.posts}))
        self.assertEqual([], self.world.errors)
        third = self.pending(3, 'C', NOW + 7200)
        third_delivery = delivery_files(self.pub, delivery(self.pub))
        self.assertEqual({**second, **third}, third_delivery)
        first_catalog = next(path for path in first if path != 'feed.json')
        self.assertNotIn(first_catalog, third_delivery)

    def test_lost_post_response_reopens_same_pending(self):
        expected = self.pending()
        self.armed()
        self.world.artifact, self.world.drop_post = expected, True
        with self.assertRaises(CloudError):
            self.send()
        self.assertEqual(1, len(self.world.posts))
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual(1, self.pub.ledger['active']['generation'])
        self.assertEqual(expected, self.world.live)
        self.assertEqual(1, len(self.world.posts))

    def test_404_unknown_blocks_even_visible_pending(self):
        expected = self.pending()
        self.armed()
        self.world.artifact = expected
        self.send()
        for status in (None, 'deployment_lost', 'unknown_status'):
            with self.subTest(status=status):
                self.world.override_status, self.world.status = True, status
                head = self.pub.head
                with self.assertRaises(CloudError):
                    with patch('tools.spacefox.cloud.time.sleep'):
                        recover(Publisher(self.store, self.code), self.site, self.pages)
                self.assertEqual(head, self.store.load()[0])
                self.assertIsNone(self.store.load()[1]['active'])
                self.assertEqual('armed', journal(Publisher(self.store, self.code))['status'])
        self.assertEqual(1, len(self.world.posts))

    def test_cancel_requires_terminal_status(self):
        self.pending()
        intent = self.armed()
        version = intent['buildVersion']
        self.world.cancel_final = 'cancel_pending'
        with self.assertRaises(CloudError), patch('tools.spacefox.cloud.time.sleep'):
            self.pages.cancel(version)
        self.assertEqual('armed', journal(self.pub)['status'])
        self.world.cancel_final = 'deployment_cancelled'
        self.assertEqual('deployment_cancelled', self.pages.cancel(version))
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertIsNotNone(self.pub.ledger['pending'])
        self.assertIsNone(self.pub.ledger['active'])
        self.assertEqual([], self.world.posts)

    def test_failed_attempt_retries_same_candidate_new_version(self):
        expected = self.pending()
        original = dict(self.pub.ledger['pending'])
        intent = self.armed()
        self.world.statuses[intent['buildVersion']] = 'deployment_failed'
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        second = self.armed()
        self.assertNotEqual(intent['buildVersion'], second['buildVersion'])
        self.assertEqual(original, self.pub.ledger['pending'])
        self.world.artifact = expected
        self.send()
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual(original, self.pub.ledger['active'])
        self.assertEqual(1, len(self.world.posts))

    def test_corrupt_missing_mixed_and_truncated_files(self):
        expected = self.pending()
        path = next(p for p in expected if p != 'feed.json')
        self.armed()
        self.world.artifact = expected
        self.send()
        faults = [{**expected, path: b'corrupt'}, {'feed.json': expected['feed.json']},
                  {**expected, path: expected[path][:-1]}, {**expected, 'feed.json': b'{"wrong":1}'}]
        for files in faults:
            self.world.live = files
            with self.assertRaises((CloudError, ValueError)):
                recover(Publisher(self.store, self.code), self.site, self.pages)
            self.assertIsNone(self.store.load()[1]['active'])
            self.assertEqual(1, self.store.load()[1]['pending']['generation'])
        self.world.live = expected
        pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual(1, pub.ledger['active']['generation'])

    def test_reconstruction_after_expiry_and_adoption(self):
        expected = self.pending()
        self.armed()
        original = self.pub.ledger['pending']
        original_bytes = self.pub.pending_files()
        git(self.source, 'commit', '--allow-empty', '-qm', 'compatible source2')
        code = git(self.source, 'rev-parse', 'HEAD')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.store.close()
        self.store = GitState(str(self.remote))  # No prior work/artifact directory.
        self.pub = Publisher(self.store, code)
        self.pub.adopt_code(self.pub.head)
        saved = journal(self.pub)
        self.assertEqual(expected, delivery_files(self.pub, saved['files']))
        self.assertEqual(original, self.pub.ledger['pending'])
        self.assertEqual(original_bytes, self.pub.pending_files())
        self.assertIsNone(self.pub.ledger['selection_validated_utc'])
        with self.assertRaises(CloudError):
            recover(self.pub, self.site, self.pages)  # Never-POSTed intent404 is uncertain.

    def test_old_source_and_stale_cas(self):
        self.pending()
        stale = Publisher(self.store, self.code)
        self.armed()
        with self.assertRaises(Conflict):
            arm(stale, expected=stale.head, repository='owner/SpaceFox', run_id=11,
                run_attempt=1, artifact_id=99, now=NOW)
        git(self.source, 'commit', '--allow-empty', '-qm', 'source advance')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        with self.assertRaises(StateError):
            self.send()
        self.assertEqual([], self.world.posts)

    def test_missing_authority_stops_without_bootstrap(self):
        expected = self.pending()
        anchor = git(self.remote, 'rev-parse', 'refs/tags/spacefox-state-bootstrap-v1')
        git(self.remote, 'update-ref', '-d', 'refs/heads/feed-state')
        self.world.live = expected
        with self.assertRaises(StateError):
            recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual(anchor, git(self.remote, 'rev-parse', 'refs/tags/spacefox-state-bootstrap-v1'))
        self.assertEqual([], self.world.posts)

    def test_simultaneous_intents_one_cas_winner(self):
        self.pending()
        def worker(run):
            store = GitState(str(self.remote))
            try:
                pub = Publisher(store, self.code)
                barrier.wait()
                arm(pub, expected=pub.head, repository='owner/SpaceFox', run_id=run,
                    run_attempt=1, artifact_id=99, now=NOW)
                return 'committed'
            except StateError:
                return 'denied'
            finally:
                store.close()
        barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(worker, (10, 11)))
        self.assertEqual(['committed', 'denied'], sorted(outcomes))
        self.assertEqual(1, self.store.load()[1]['generation'])
        self.assertEqual([], self.world.posts)

    def test_provider_crashes_and_no_forced_poll(self):
        token = self.pub.reserve(self.pub.head, NOW)
        self.assertIsNotNone(token)
        reopened = Publisher(self.store, self.code)
        reopened.reconcile(None)
        before = reopened.head
        self.assertIsNone(reopened.reserve(reopened.head, NOW + 1))
        self.assertEqual(before, reopened.head)
        with self.assertRaises(StateError):
            reopened.reserve(reopened.head, NOW + 1, trigger='retry')
        self.assertEqual(0, self.world.provider_calls)
        self.assertEqual(1, len(reopened.ledger['requests']))
        self.world.drop_provider = True
        client = LL2Client(origin=self.world.base, local_http=True)
        with self.assertRaises(ProviderError):
            update(reopened, client, NOW + 61, build_catalog(ROOT), trigger='retry')
        self.assertEqual(1, self.world.provider_calls)
        self.assertEqual(2, len(reopened.ledger['requests']))
        self.assertIsNone(reopened.ledger['pending'])
        self.assertEqual([], self.world.errors)
        # A successful real provider path is performed only after failure backoff.
        self.world.drop_provider = False
        # A literal source Date is served over real HTTP; operation time cannot
        # renew it. Normal polling only resumes after its original due instant.
        now = NOW + 3661
        result = update(reopened, client, now, build_catalog(ROOT))
        self.assertEqual('pending', result['result'])
        self.assertEqual(2, self.world.provider_calls)
        files = reopened.pending_files()
        feed = json.loads(files['feed.json'])
        self.assertEqual(1, feed['publisher']['generation'])
        self.assertEqual(NOW, feed['publisher']['selectionValidatedUtc'])
        self.world.live = files
        reopened = recover(reopened, self.site, self.pages)
        before = reopened.head
        result = update(reopened, client, now + 1, build_catalog(ROOT), trigger='scheduled')
        self.assertEqual('not_due', result['result'])
        self.assertEqual(before, reopened.head)
        self.assertEqual(2, self.world.provider_calls)

    def test_cli_sparse_runtime_and_workflow(self):
        inputs = (ROOT / '.github/spacefox-inputs.txt').read_text().splitlines()
        self.assertEqual(len(inputs), len(set(inputs)))
        closure = set(build_catalog(ROOT)['inputDigests'])
        self.assertIn('/catalog/source.json', inputs)
        self.assertIn('/tools/cloud_inputs.py', inputs)
        clone = self.root / 'sparse'
        subprocess.run(['git', 'clone', '-q', '--no-checkout', str(ROOT), str(clone)], check=True)
        git(clone, 'sparse-checkout', 'init', '--no-cone')
        subprocess.run(['git', '-C', str(clone), 'sparse-checkout', 'set', '--no-cone', '--stdin'],
                       input=('\n'.join(inputs) + '\n').encode(), check=True, stdout=subprocess.PIPE)
        git(clone, 'checkout', '-q')
        materialized = subprocess.run([sys.executable, '-B', 'tools/cloud_inputs.py'], cwd=clone,
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, materialized.returncode, materialized.stderr.decode())
        self.assertTrue(all((clone / relative).is_file() for relative in closure))
        # Added files need a committed source before this boundary is meaningful.
        result = subprocess.run([sys.executable, '-B', 'tools/cloud_feed.py', '--help'], cwd=clone,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertFalse((clone / 'prototype').exists())
        self.assertFalse((clone / 'watchface').exists())
        self.assertFalse((clone / '.agents').exists())
        cli_remote = self.root / 'cli-remote.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(cli_remote)], check=True)
        git(clone, 'push', '-q', str(cli_remote), 'HEAD:refs/heads/main')
        self.world.remote = cli_remote
        args = [sys.executable, '-B', 'tools/cloud_feed.py', '--repository', 'owner/SpaceFox',
                '--remote', str(cli_remote), '--site', self.world.base + '/site',
                '--api', self.world.base, '--origin', self.world.base,
                '--local-qualification', '--now', str(NOW), 'prepare']
        out = self.root / 'cli-artifact'
        run = subprocess.run(args + ['--bootstrap', '--output', str(out)], cwd=clone,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, run.returncode, run.stderr.decode())
        result = json.loads(run.stdout)
        self.assertEqual(('true', 1, 4), (result['pending'], result['requests'], result['exportedFiles']))
        from tools.spacefox.visual_bridge import validate_feed as validate_v2
        visual = validate_v2((out / 'wire2/feed.json').read_bytes())
        self.assertEqual('immutable-catalog', visual['dictionaryMode'])
        feed = json.loads((out / 'feed.json').read_bytes())
        self.assertEqual((1, NOW), (feed['publisher']['generation'], feed['publisher']['selectionValidatedUtc']))
        self.assertEqual(feed['publisher'], visual['publisher'])
        again = self.root / 'cli-recovered'
        run = subprocess.run(args + ['--output', str(again)], cwd=clone,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, run.returncode, run.stderr.decode())
        self.assertEqual('recovered_pending', json.loads(run.stdout)['result'])
        self.assertEqual((out / 'feed.json').read_bytes(), (again / 'feed.json').read_bytes())
        self.assertEqual(1, self.world.provider_calls)
        self.assertEqual([], self.world.errors)
        workflow = (ROOT / '.github/workflows/update-feed.yml').read_text()
        self.assertEqual(1, workflow.count('concurrency:'))
        self.assertIn('cancel-in-progress: false', workflow)
        self.assertIn("7,22,37,52 * * * *", workflow)
        self.assertEqual(4, workflow.count('ref: ${{ github.sha }}'))
        self.assertIn('retention-days: 1', workflow)
        self.assertNotIn('uses: actions/deploy-pages@', workflow)
        self.assertNotIn('pip install', workflow)
        self.assertNotIn('npm', workflow)
        self.assertIn('id-token: write', workflow)
        self.assertNotIn('pages: write', workflow.split('  deploy:')[0])
        self.assertIn('permissions: {}', workflow)

    def test_lost_git_ack_after_intent_and_promotion(self):
        expected = self.pending()
        original_git = self.store._git
        remaining = [1]
        def lost_ack(*args, **kwargs):
            result = original_git(*args, **kwargs)
            if args[0] == 'push' and result.returncode == 0:
                remaining[0] -= 1
                if remaining[0] == 0:
                    raise CloudError('local simulated lost Git acknowledgement after successful remote CAS')
            return result
        with patch.object(self.store, '_git', lost_ack):
            with self.assertRaises(CloudError):
                self.armed()
        self.pub = Publisher(self.store, self.code)
        self.assertEqual('armed', journal(self.pub)['status'])
        self.assertEqual(expected, self.pub.pending_files())
        with self.assertRaises(CloudError):
            recover(self.pub, self.site, self.pages)
        self.world.artifact = expected
        self.send()
        remaining[0] = 2  # Terminal journal CAS succeeds, then promotion ack is lost.
        with patch.object(self.store, '_git', lost_ack):
            with self.assertRaises(CloudError):
                recover(Publisher(self.store, self.code), self.site, self.pages)
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual((1, None, []), (self.pub.ledger['active']['generation'],
                                       self.pub.ledger['pending'], self.pub.ledger['requests']))
        self.assertEqual(1, len(self.world.posts))

    def test_seeded_async_event_sequences(self):
        # Per-run directed witnesses, followed by seeded terminal outcomes. Model
        # facts are literal generation/request counts; observations follow every
        # actual boundary, never skip preconditions or derive expected counters.
        rng = random.Random(20261112)
        expected = self.pending()
        self.armed()
        dispositions = {'unknown:observed_no_mutation': 0, 'final:observed_no_mutation': 0,
                        'visible:applied': 0}
        head = self.pub.head
        for status in [None, 'deployment_lost'] + [rng.choice([None, 'unknown_status']) for _ in range(2)]:
            self.world.override_status, self.world.status = True, status
            with self.assertRaises(CloudError), patch('tools.spacefox.cloud.time.sleep'):
                recover(Publisher(self.store, self.code), self.site, self.pages)
            dispositions['unknown:observed_no_mutation'] += 1
            doc = self.store.load()[1]
            self.assertEqual((1, None, 0), (doc['generation'], doc['active'], len(doc['requests'])))
            self.assertEqual(head, self.store.load()[0])
            self.assertEqual(0, len(self.world.posts))
        self.world.status = 'deployment_cancelled'
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        dispositions['final:observed_no_mutation'] += 1
        self.assertIsNone(self.pub.ledger['active'])
        self.assertEqual(1, self.pub.ledger['pending']['generation'])
        self.world.live = expected
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        dispositions['visible:applied'] += 1
        self.assertEqual((1, None, []), (self.pub.ledger['active']['generation'],
                                       self.pub.ledger['pending'], self.pub.ledger['requests']))
        self.assertTrue(all(dispositions.values()), dispositions)

    def test_bounds_credentials_and_identity(self):
        self.pending()
        head = self.pub.head
        with self.assertRaises(CloudError):
            arm(self.pub, expected=head, repository='owner/SpaceFox', run_id=0,
                run_attempt=1, artifact_id=99, now=NOW)
        self.assertEqual(head, self.store.load()[0])
        with self.assertRaises(CloudError):
            delivery_files(self.pub, {f'p/{n}': {} for n in range(257)})
        with self.assertRaises(CloudError):
            Site('https://user:secret@example.com/path')
        self.armed()
        with self.assertRaises(CloudError):
            deploy(self.pub, self.pages, self.site, expected=self.pub.head, repository='owner/SpaceFox',
                   run_id=11, run_attempt=1, id_token='local-oidc', polls=1)
        self.assertEqual([], self.world.posts)
        with patch.dict(os.environ, {'GITHUB_REF': 'refs/heads/untrusted', 'GITHUB_SHA': self.code,
                                     'GITHUB_REPOSITORY': 'owner/SpaceFox', 'GITHUB_EVENT_NAME': 'workflow_dispatch'}):
            with self.assertRaises(CloudError):
                context('owner/SpaceFox', self.code)
        # Direct local HTTP proves redirect refusal and a strict body limit.
        self.world.live['oversized'] = b'x' * 8193
        with self.assertRaises(CloudError):
            HTTP().request('GET', self.world.base + '/site/oversized', limit=8192)


if __name__ == '__main__':
    unittest.main()
