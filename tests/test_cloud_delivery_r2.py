"""R2 literal Git/HTTP witnesses; GitHub/Pages/Actions alone are substituted."""
import copy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.spacefox.cloud import (CloudError, Pages, Site, arm, delivery,
                                  delivery_files, deploy, journal, recover)
from tools.spacefox.publisher import GitState, Publisher, StateError

NOW = 1794441600


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()


def literal(instance, generation, letter):
    catalog = encoded({'schemaVersion': 1, 'catalogVersion': letter,
                       'qualification': 'publisher-metadata-only', 'entries': {}, 'unresolved': []})
    digest = hashlib.sha256(catalog).hexdigest()
    path = 'catalogs/' + digest + '.json'
    feed = encoded({'schemaVersion': 1,
                    'publisher': {'instance': instance, 'generation': generation, 'selectionValidatedUtc': None},
                    'catalogRevision': letter, 'catalogDigest': digest, 'catalogPath': path,
                    'dictionaries': {}, 'unresolvedCatalogIds': [], 'launch': None, 'timingState': 'no-schedule',
                    'refreshPolicy': {'normal_interval_seconds': 3600, 'near_interval_seconds': 900,
                                      'fast_interval_seconds': None, 'stale_cycles': 3},
                    'pollIntervalSeconds': 3600, 'sourceContentRevision': hashlib.sha256(b'[]').hexdigest(),
                    'selection': {'acceptedRecords': 0, 'includedRecords': 0,
                                  'scope': 'selected-launch', 'worldwideCompleteness': False},
                    'providerTraversal': None})
    return {'feed.json': feed, path: catalog}, digest


class CloudDeliveryR2Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='spacefox-cloud-r2-')
        self.root = Path(self.tmp.name)
        self.remote, self.source = self.root / 'authority.git', self.root / 'source'
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        git(self.source, 'config', 'user.name', 'Independent cloud R2')
        git(self.source, 'config', 'user.email', 'r2@example.invalid')
        git(self.source, 'commit', '--allow-empty', '-qm', 'review source')
        self.code = git(self.source, 'rev-parse', 'HEAD')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.store = GitState(str(self.remote))
        self.store.bootstrap(self.code)
        self.pub = Publisher(self.store, self.code)
        self.pub.reconcile(None)
        self.live, self.artifact, self.statuses, self.actions = {}, {}, {}, {}
        self.feed_sequence, self.reads, self.posts = [], [], []
        test = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def send(self, status, raw=b''):
                self.send_response(status)
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                test.reads.append(self.path)
                if '/actions/' in self.path:
                    value = test.actions.get(self.path)
                    self.send(404 if value is None else 200, b'' if value is None else encoded(value))
                elif '/pages/deployments/' in self.path:
                    value = test.statuses.get(self.path.rsplit('/', 1)[-1])
                    self.send(404 if value is None else 200, b'' if value is None else encoded({'status': value}))
                else:
                    path = self.path.removeprefix('/site/')
                    raw = test.feed_sequence.pop(0) if path == 'feed.json' and test.feed_sequence else test.live.get(path)
                    self.send(404 if raw is None else 200, b'' if raw is None else raw)

            def do_POST(self):
                value = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                test.posts.append(value)
                test.statuses[value['pages_build_version']] = 'succeed'
                test.live = dict(test.artifact)
                self.send(201, encoded({'id': 'substituted-service'}))

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = 'http://127.0.0.1:' + str(self.server.server_port)
        self.pages = Pages('owner/SpaceFox', 'local-r2', api=self.base, local_http=True)
        self.site = Site(self.base + '/site', local_http=True)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.store.close()
        self.tmp.cleanup()

    def prepare(self, generation, letter):
        files, digest = literal(self.pub.ledger['instance_id'], generation, letter)
        self.pub.prepare(self.pub.head, NOW + generation * 3600, files, digest,
                         feed_publisher={'instance': self.pub.ledger['instance_id'],
                                         'generation': generation, 'selectionValidatedUtc': None})
        return files

    def arm(self, run=20):
        self.pub, intent = arm(self.pub, expected=self.pub.head, repository='owner/SpaceFox',
                               run_id=run, run_attempt=1, artifact_id=123, now=NOW)
        return intent

    def promote_a(self):
        first = self.prepare(1, 'A')
        intent = self.arm()
        self.live = first
        self.statuses[intent['buildVersion']] = 'succeed'
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual((1, None, []), (self.pub.ledger['active']['generation'],
                                       self.pub.ledger['pending'], self.pub.ledger['requests']))
        return first

    def test_switch_to_pending_cannot_skip_retained_catalog(self):
        first = self.promote_a()
        second = self.prepare(2, 'B')
        intent = self.arm(21)
        before = copy.deepcopy(self.pub.ledger)
        self.statuses[intent['buildVersion']] = 'succeed'
        # The old feed is served once, then the mutable CDN root switches to B.
        # The artifact has lost A's catalog; literal contract forbids promotion.
        self.live = second
        self.feed_sequence = [first['feed.json']]
        self.reads.clear()
        with self.assertRaises(CloudError):
            recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual(before, self.store.load()[1])
        old_path = next(path for path in first if path != 'feed.json')
        self.assertIn('/site/' + old_path, self.reads)
        self.assertEqual([], self.posts)

    def test_complete_switch_retry_preserves_three_generation_closure(self):
        first = self.promote_a()
        second = self.prepare(2, 'B')
        intent = self.arm(21)
        before = copy.deepcopy(self.pub.ledger)
        self.statuses[intent['buildVersion']] = 'succeed'
        complete_b = {**first, **second}
        self.live = complete_b
        self.feed_sequence = [first['feed.json']]
        # The mutable root switches during this observation: preserve active A
        # and pending B, then allow a fresh stable exact closure observation.
        with self.assertRaises(CloudError):
            recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual(before, self.store.load()[1])
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual(before['pending'], self.pub.ledger['active'])
        self.assertIsNone(self.pub.ledger['pending'])
        self.assertEqual(complete_b, delivery_files(self.pub, journal(self.pub)['files']))

        third = self.prepare(3, 'C')
        expected_c = {**second, **third}
        self.assertEqual(3, len(expected_c))
        self.assertEqual(expected_c, delivery_files(self.pub, delivery(self.pub)))
        self.assertNotIn(next(path for path in first if path != 'feed.json'), expected_c)
        self.arm(22)
        self.artifact = expected_c
        self.assertEqual('succeed', deploy(self.pub, self.pages, self.site, expected=self.pub.head,
                         repository='owner/SpaceFox', run_id=22, run_attempt=1,
                         id_token='local-r2', polls=1))
        self.assertEqual(1, len(self.posts))
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        saved = copy.deepcopy(self.pub.ledger)
        self.assertEqual((3, None, [], None), (saved['active']['generation'], saved['pending'],
                                             saved['requests'], saved['selection_validated_utc']))
        git(self.source, 'commit', '--allow-empty', '-qm', 'compatible source adoption')
        self.code = git(self.source, 'rev-parse', 'HEAD')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.store.close()
        self.store = GitState(str(self.remote))
        self.pub = Publisher(self.store, self.code)
        self.pub.adopt_code(self.pub.head)
        self.assertEqual(saved['active'], self.pub.ledger['active'])
        self.assertEqual(expected_c, delivery_files(self.pub, journal(self.pub)['files']))
        self.pub = recover(self.pub, self.site, self.pages)
        self.assertEqual(saved['active'], self.pub.ledger['active'])
        self.assertEqual(1, len(self.posts))

    def test_actions_faults_and_prepost_guards_have_no_publication(self):
        self.prepare(1, 'A')
        intent = self.arm()
        prefix = '/repos/owner/SpaceFox/actions/runs/20/attempts/1'
        run = {'id': 20, 'run_attempt': 1, 'head_sha': self.code, 'head_branch': 'main',
               'event': 'push', 'status': 'completed', 'path': '.github/workflows/update-feed.yml',
               'repository': {'full_name': 'owner/SpaceFox'}}
        jobs = {'total_count': 1, 'jobs': [{'run_id': 20, 'head_sha': self.code, 'name': 'deploy',
                 'status': 'completed', 'conclusion': 'cancelled', 'steps': [{
                     'name': 'POST once, then bound async polling and cancellation finality',
                     'status': 'completed', 'conclusion': 'skipped'}]}]}
        valid = {prefix: run, prefix + '/jobs?per_page=100': jobs}
        mutations = [
            ('absent-run', lambda x: x.pop(prefix)),
            ('wrong-branch', lambda x: x[prefix].update(head_branch='other')),
            ('wrong-job-run', lambda x: x[prefix + '/jobs?per_page=100']['jobs'][0].update(run_id=21)),
            ('wrong-job-source', lambda x: x[prefix + '/jobs?per_page=100']['jobs'][0].update(head_sha='f' * 40)),
            ('duplicate-post-step', lambda x: x[prefix + '/jobs?per_page=100']['jobs'][0]['steps'].append(
                copy.deepcopy(x[prefix + '/jobs?per_page=100']['jobs'][0]['steps'][0]))),
            ('started-step', lambda x: x[prefix + '/jobs?per_page=100']['jobs'][0]['steps'][0].update(conclusion='success')),
            ('cancelled-step', lambda x: x[prefix + '/jobs?per_page=100']['jobs'][0]['steps'][0].update(conclusion='cancelled')),
        ]
        before = self.store.load()
        for name, mutate in mutations:
            with self.subTest(name=name):
                self.actions = copy.deepcopy(valid)
                mutate(self.actions)
                self.reads.clear()
                with self.assertRaises(CloudError):
                    recover(Publisher(self.store, self.code), self.site, self.pages)
                self.assertEqual(before, self.store.load())
                self.assertFalse(any(path.startswith('/site/') for path in self.reads))
                self.assertEqual('armed', journal(Publisher(self.store, self.code))['status'])
                self.assertEqual([], self.posts)
        self.reads.clear()
        with self.assertRaises(CloudError):
            deploy(self.pub, self.pages, self.site, expected=self.pub.head,
                   repository='owner/SpaceFox', run_id=20, run_attempt=2,
                   id_token='local-r2', polls=1)
        self.assertEqual([], self.reads)
        # Same run/attempt with an unauthenticated live root is also refused.
        self.live = {'feed.json': b'{"unexpected":true}'}
        with self.assertRaises(CloudError):
            deploy(self.pub, self.pages, self.site, expected=self.pub.head,
                   repository='owner/SpaceFox', run_id=20, run_attempt=1,
                   id_token='local-r2', polls=1)
        self.assertEqual(before, self.store.load())
        self.assertEqual([], self.posts)
        git(self.source, 'commit', '--allow-empty', '-qm', 'source advanced beforePOST')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        with self.assertRaises(StateError):
            deploy(self.pub, self.pages, self.site, expected=self.pub.head,
                   repository='owner/SpaceFox', run_id=20, run_attempt=1,
                   id_token='local-r2', polls=1)
        self.assertEqual(before, self.store.load())
        self.assertEqual([], self.posts)
        self.assertEqual(intent['buildVersion'], journal(self.pub)['intent']['buildVersion'])

    def test_terminal_failure_keeps_active_and_retries_exact_pending(self):
        first = self.promote_a()
        second = self.prepare(2, 'B')
        pending = copy.deepcopy(self.pub.ledger['pending'])
        first_intent = self.arm(21)
        before = copy.deepcopy(self.pub.ledger)
        self.statuses[first_intent['buildVersion']] = 'deployment_failed'
        self.live = first
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual(before, self.pub.ledger)
        self.assertEqual('deployment_failed', journal(self.pub)['status'])
        self.assertEqual([], self.posts)
        retry = self.arm(22)
        self.assertNotEqual(first_intent['buildVersion'], retry['buildVersion'])
        self.assertEqual(first_intent['artifactRevision'], retry['artifactRevision'])
        self.assertEqual(pending, self.pub.ledger['pending'])
        self.artifact = {**first, **second}
        self.assertEqual('succeed', deploy(self.pub, self.pages, self.site, expected=self.pub.head,
                         repository='owner/SpaceFox', run_id=22, run_attempt=1,
                         id_token='local-r2', polls=1))
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual(pending, self.pub.ledger['active'])
        self.assertIsNone(self.pub.ledger['pending'])
        self.assertEqual([], self.pub.ledger['requests'])
        self.assertEqual(1, len(self.posts))


if __name__ == '__main__':
    unittest.main(verbosity=2)
