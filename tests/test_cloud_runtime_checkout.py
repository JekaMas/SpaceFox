"""Sparse real CLI/bare-Git/HTTP witnesses for non-builder Actions jobs.

Only external LL2/Pages/artifact transport and the Actions OIDC response are
substituted. The CLI parser, source guard, Git authority, saved-file validators,
intent, deployment HTTP, finality, site readback and promotion execute unchanged.
"""
from datetime import datetime, timezone
from email.utils import format_datetime
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile
import threading
import unittest

from tools.spacefox.publisher import GitState, LiveRevision, Publisher

ROOT = Path(__file__).resolve().parents[1]
NOW = 1794441600


def git(root, *args):
    return subprocess.run(['git', '-C', str(root), *args], check=True,
                          capture_output=True).stdout.decode().strip()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def files(instance, generation, version, source_utc):
    # Authored independently of build_catalog/build_artifact/validate_snapshot.
    catalog = encoded({'schemaVersion': 1, 'catalogVersion': version,
                       'qualification': 'publisher-metadata-only', 'entries': {}, 'unresolved': []})
    digest = hashlib.sha256(catalog).hexdigest()
    path = f'catalogs/{digest}.json'
    feed = encoded({'schemaVersion': 1,
                    'publisher': {'instance': instance, 'generation': generation,
                                  'selectionValidatedUtc': source_utc},
                    'catalogRevision': version, 'catalogDigest': digest, 'catalogPath': path,
                    'dictionaries': {}, 'unresolvedCatalogIds': [], 'launch': None,
                    'timingState': 'no-schedule',
                    'refreshPolicy': {'normal_interval_seconds': 3600, 'near_interval_seconds': 900,
                                      'fast_interval_seconds': None, 'stale_cycles': 3},
                    'pollIntervalSeconds': 3600,
                    'sourceContentRevision': hashlib.sha256(b'[]').hexdigest(),
                    'selection': {'acceptedRecords': 0, 'includedRecords': 0,
                                  'scope': 'selected-launch', 'worldwideCompleteness': False},
                    'providerTraversal': None})
    return {'feed.json': feed, path: catalog}, digest


def job_script(job, marker):
    """Execute the actual YAML shell body, rather than duplicate its checkout."""
    text = (ROOT / '.github/workflows/update-feed.yml').read_text()
    # Next jobs begin at exactly two spaces, while each step is six spaces.
    lines = text.split(f'\n  {job}:\n', 1)[1].splitlines()
    start = next(i for i, line in enumerate(lines) if marker in line)
    run = next(i for i in range(start + 1, len(lines)) if lines[i] == '        run: |')
    body = []
    for line in lines[run + 1:]:
        if line and not line.startswith('          '):
            break
        body.append(line[10:])
    return '\n'.join(body)


class Service:
    def __init__(self, remote):
        self.remote, self.live, self.artifact = remote, {}, {}
        self.reads, self.posts, self.provider_calls, self.statuses = [], [], 0, {}
        self.read_hook = None
        self.actions = {}
        service = self

        class Handler(BaseHTTPRequestHandler):
            def date_time_string(self, timestamp=None):
                return format_datetime(datetime.fromtimestamp(NOW, timezone.utc), usegmt=True)

            def log_message(self, *args):
                pass

            def send(self, status, raw=b''):
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_GET(self):
                service.reads.append(self.path)
                if service.read_hook is not None:
                    service.read_hook(self.path)
                if '/actions/' in self.path:
                    value = service.actions.get(self.path)
                    self.send(404 if value is None else 200, b'' if value is None else encoded(value))
                elif self.path.startswith('/2.3.0/'):
                    service.provider_calls += 1
                    ledger = json.loads(git(service.remote, 'show', 'refs/heads/feed-state:ledger.json'))
                    if not ledger['requests'] or ledger['requests'][-1]['outcome'] != 'reserved':
                        self.send(500)
                        return
                    self.send(200, encoded({'count': 0, 'next': None, 'previous': None, 'results': []}))
                elif '/pages/deployments/' in self.path:
                    status = service.statuses.get(self.path.rsplit('/', 1)[-1])
                    self.send(404 if status is None else 200,
                              b'' if status is None else encoded({'status': status}))
                else:
                    raw = service.live.get(self.path.removeprefix('/site/'))
                    self.send(404 if raw is None else 200, b'' if raw is None else raw)

            def do_POST(self):
                data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                service.posts.append((self.path, data))
                service.statuses[data['pages_build_version']] = 'succeed'
                service.live = dict(service.artifact)
                self.send(200, encoded({'id': 'qualification-only'}))

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base = f'http://127.0.0.1:{self.server.server_port}'

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


# Fail-only observers: no builder/parser/validator is replaced. The one positive
# substitution is the external Actions OIDC response, unsupported on loopback by
# the real host allowlist. Its invocation count is explicit, not claimed absent.
RUNTIME_DRIVER = '''
import json,sys
from pathlib import Path
root=Path.cwd().resolve()
seen={'builderCalls':0,'oidcCalls':0,'nodeCalls':0,'sourceDataReads':0}
def profile(frame,event,arg):
    if event=='call' and frame.f_code.co_name=='build_catalog':
        seen['builderCalls']+=1
        raise AssertionError('non-builder command called catalog builder')
def audit(event,args):
    if event=='subprocess.Popen' and Path(str(args[0])).name in ('node','nodejs'):
        seen['nodeCalls']+=1
        raise AssertionError('non-builder command invoked Node')
    if event=='open' and isinstance(args[0],(str,bytes)):
        path=Path(args[0].decode() if isinstance(args[0],bytes) else args[0]).resolve()
        if path.is_relative_to(root) and path.relative_to(root).parts[:1] in [
            ('catalog',),('assets',),('openspec',),('.agents',),('tests',)]:
            seen['sourceDataReads']+=1
            raise AssertionError('non-builder command read source/private data')
def oidc():
    seen['oidcCalls']+=1
    return 'qualification-only-oidc'
sys.addaudithook(audit)
sys.setprofile(profile)
try:
    import tools.cloud_feed as cli
    cli.oidc_token=oidc
    result=cli.main(sys.argv[1:])
finally:
    sys.setprofile(None)
    print('RUNTIME_BOUNDARY '+json.dumps(seen,sort_keys=True),file=sys.stderr)
raise SystemExit(result)
'''


class CloudRuntimeCheckoutTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='spacefox-runtime-checkout-')
        self.base = Path(self.tmp.name)
        self.source = self.base / 'source'
        subprocess.run(['git', 'clone', '-q', '--no-checkout', str(ROOT), str(self.source)], check=True)
        git(self.source, 'config', 'user.name', 'Sparse runtime qualification')
        git(self.source, 'config', 'user.email', 'runtime@example.invalid')
        git(self.source, 'sparse-checkout', 'init', '--no-cone')
        git(self.source, 'sparse-checkout', 'set', '--no-cone', '/.github/spacefox-inputs.txt')
        git(self.source, 'checkout', '-q')
        self.remote = self.base / 'authority.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.code = git(self.source, 'rev-parse', 'HEAD')
        self.service = Service(self.remote)
        self.stores = []

    def tearDown(self):
        self.service.close()
        for store in self.stores:
            store.close()
        self.tmp.cleanup()

    def arguments(self, *command):
        return ['--repository', 'owner/SpaceFox', '--remote', str(self.remote),
                '--site', self.service.base + '/site', '--api', self.service.base,
                '--origin', self.service.base, '--local-qualification', '--now', str(NOW), *command]

    def runtime(self, job='arm'):
        script = job_script(job, 'Check out runtime seed for exact saved-state validation')
        result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script],
                                cwd=self.source, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        tracked = set(git(self.source, 'ls-tree', '-r', '--name-only', 'HEAD').splitlines())
        expected = {p.removeprefix('/') for p in (self.source / '.github/spacefox-inputs.txt').read_text().splitlines()
                    if p != '/catalog/source.json' and p.removeprefix('/') in tracked}
        actual = {p.relative_to(self.source).as_posix() for p in self.source.rglob('*')
                  if p.is_file() and '.git' not in p.relative_to(self.source).parts}
        self.assertEqual(expected, actual)
        for path in ('catalog', 'assets', 'openspec', '.agents', 'tests', 'prototype', 'watchface', '.github/workflows'):
            self.assertFalse((self.source / path).exists(), path)
        self.assertEqual('', git(self.source, 'status', '--porcelain'))

    def cli(self, *command, success=True, oidc_calls=None):
        env = dict(os.environ, GITHUB_RUN_ID=str(getattr(self, 'run_id', 87)), GITHUB_RUN_ATTEMPT='1')
        for key in ('GH_TOKEN', 'GITHUB_OUTPUT', 'GIT_CONFIG_COUNT'):
            env.pop(key, None)
        result = subprocess.run([sys.executable, '-B', '-c', RUNTIME_DRIVER, *self.arguments(*command)],
                                cwd=self.source, env=env, capture_output=True)
        self.assertEqual(0 if success else 2, result.returncode, result.stderr.decode())
        boundary = json.loads(result.stderr.decode().split('RUNTIME_BOUNDARY ', 1)[1])
        self.assertEqual(0, boundary['builderCalls'])
        self.assertEqual(0, boundary['nodeCalls'])
        self.assertEqual(0, boundary['sourceDataReads'])
        expected_oidc = int(command[0] == 'deploy') if oidc_calls is None else oidc_calls
        self.assertEqual(expected_oidc, boundary['oidcCalls'])
        return json.loads(result.stdout) if success else result.stderr.decode()

    def authority(self, previous=False):
        store = GitState(str(self.remote))
        self.stores.append(store)
        store.bootstrap(self.code)
        pub = Publisher(store, self.code)
        pub.reconcile(None)
        # Authored source-validation epoch; no live provider claim. Runtime jobs
        # must preserve it, the accepted empty schedule, and the quota record.
        token = pub.reserve(pub.head, NOW - 3600)
        pub.accept_source(pub.head, token, (), NOW - 3600, selection_validated_utc=NOW - 3600)
        first, digest = files(pub.ledger['instance_id'], 1, 'saved-A', NOW - 3600)
        pub.prepare(pub.head, NOW, first, digest, feed_publisher=json.loads(first['feed.json'])['publisher'])
        if previous:
            snap = pub.ledger['pending']
            pub.reconcile(LiveRevision(1, snap['artifact_revision']))
            self.service.live = dict(first)
            second, digest = files(pub.ledger['instance_id'], 2, 'saved-B', NOW - 3600)
            pub.prepare(pub.head, NOW, second, digest, feed_publisher=json.loads(second['feed.json'])['publisher'])
            return pub, first, second
        return pub, {}, first

    def snapshot(self):
        head = git(self.remote, 'rev-parse', 'refs/heads/feed-state')
        return head, git(self.remote, 'ls-tree', '-r', head)

    def poison(self, path, raw):
        root = self.base / 'poison'
        if not root.exists():
            git(self.base, 'clone', '-q', '--branch', 'feed-state', str(self.remote), str(root))
            git(root, 'config', 'user.name', 'Malformed authenticated fixture')
            git(root, 'config', 'user.email', 'malformed@example.invalid')
        git(root, 'fetch', '-q', 'origin', 'feed-state')
        git(root, 'reset', '--hard', 'FETCH_HEAD')
        (root / path).write_bytes(raw)
        git(root, 'add', path)
        git(root, 'commit', '-qm', 'malformed saved bytes fixture')
        git(root, 'push', '-q', 'origin', 'HEAD:feed-state')

    def test_prepare_keeps_real_materializer_and_source_validation(self):
        script = job_script('prepare', 'Materialize exact reviewed runtime and catalog closure')
        materialize = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script],
                                     cwd=self.source, capture_output=True)
        self.assertEqual(0, materialize.returncode, materialize.stderr.decode())
        self.assertEqual({'catalogVersion': '2026-11-12.global.14.current-context1', 'catalogInputs': 684},
                         json.loads(materialize.stdout))
        self.assertEqual('', git(self.source, 'status', '--porcelain'))
        output = self.base / 'prepared-site'
        result = subprocess.run([sys.executable, '-B', 'tools/cloud_feed.py',
                                 *self.arguments('prepare', '--bootstrap', '--output', str(output))],
                                cwd=self.source, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertEqual(('true', 1, 4), tuple(json.loads(result.stdout)[k]
                         for k in ('pending', 'requests', 'exportedFiles')))
        self.assertEqual(1, self.service.provider_calls)
        feed = json.loads((output / 'feed.json').read_bytes())
        self.assertEqual((1, NOW), (feed['publisher']['generation'], feed['publisher']['selectionValidatedUtc']))
        self.assertEqual([], self.service.posts)

    def test_invalid_source_stops_prepare_before_authority_or_provider(self):
        git(self.source, 'sparse-checkout', 'set', '--no-cone', '/.github/spacefox-inputs.txt', '/catalog/source.json')
        recipe = json.loads((self.source / 'catalog/source.json').read_bytes())
        recipe['reference']['sha256'] = '0' * 64
        (self.source / 'catalog/source.json').write_bytes(encoded(recipe))
        git(self.source, 'add', '--sparse', 'catalog/source.json')
        git(self.source, 'commit', '-qm', 'wrong authenticated source pin')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        script = job_script('prepare', 'Materialize exact reviewed runtime and catalog closure')
        # The shell must stop at the actual materializer; bootstrap below is a
        # forbidden side effect if source validation is omitted or disconnected.
        tail = '\n' + shlex.join(['python3', '-B', 'tools/cloud_feed.py',
                                *self.arguments('prepare', '--bootstrap', '--output', str(self.base / 'forbidden-site'))])
        result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script + tail],
                                cwd=self.source, capture_output=True)
        self.assertEqual(2, result.returncode)
        self.assertIn(b'cloud-inputs: tracked catalog closure could not be materialized', result.stderr)
        self.assertEqual('', git(self.remote, 'for-each-ref', '--format=%(refname)', 'refs/heads/feed-state',
                                 'refs/tags/spacefox-state-bootstrap-v1'))
        self.assertEqual(([], [], 0), (self.service.reads, self.service.posts, self.service.provider_calls))
        self.assertFalse((self.base / 'forbidden-site').exists())

    def test_runtime_only_arm_deploy_recover_validate_complete_saved_files(self):
        self.runtime('arm')
        pub, first, second = self.authority(previous=True)
        before = pub.ledger
        armed = self.cli('arm', '--expected-base', pub.head, '--artifact-id', '99')
        self.runtime('deploy')
        self.service.artifact = {**{p: b for p, b in first.items() if p != 'feed.json'}, **second}
        self.assertEqual({'status': 'succeed'}, self.cli('deploy', '--expected-base', armed['head']))
        self.runtime('promote')
        self.cli('recover')
        after = Publisher(pub.store, self.code).ledger
        self.assertEqual((2, None), (after['active']['generation'], after['pending']))
        self.assertEqual(NOW - 3600, after['selection_validated_utc'])
        for key in ('accepted', 'requests', 'last_poll_utc', 'backoff_until_utc'):
            self.assertEqual(before[key], after[key], key)
        self.assertEqual(self.service.artifact, self.service.live)
        self.assertEqual((1, 0), (len(self.service.posts), self.service.provider_calls))
        for path in self.service.artifact:
            self.assertIn('/site/' + path, self.service.reads)
        self.assertEqual('', git(self.source, 'status', '--porcelain'))

    def test_malformed_unsupported_or_corrupt_saved_state_cannot_publish(self):
        self.runtime()
        pub, first, second = self.authority(previous=True)
        armed = self.cli('arm', '--expected-base', pub.head, '--artifact-id', '99')
        baseline = armed['head']
        raw = git(self.remote, 'show', baseline + ':ledger.json').encode()
        ledger = json.loads(raw)
        unsupported = dict(ledger, schema_version=99)
        journal = json.loads(git(self.remote, 'show', baseline + ':cloud.json'))
        journal['schemaVersion'] = 99
        prior_catalog = next(p for p in first if p != 'feed.json')
        variants = [('ledger.json', b'{'), ('ledger.json', encoded(unsupported)),
                    ('artifacts/2/feed.json', second['feed.json'] + b' '),
                    ('artifacts/1/' + prior_catalog, first[prior_catalog] + b' '),
                    ('cloud.json', encoded(journal))]
        for path, broken in variants:
            with self.subTest(path=path, digest=hashlib.sha256(broken).hexdigest()):
                git(self.remote, 'update-ref', 'refs/heads/feed-state', baseline)
                self.poison(path, broken)
                snapshot = self.snapshot()
                for command in ('arm', 'deploy', 'recover'):
                    args = ([command, '--expected-base', snapshot[0]] if command != 'recover' else [command])
                    if command == 'arm':
                        args += ['--artifact-id', '99']
                    self.cli(*args, success=False,
                             oidc_calls=int(command == 'deploy' and path == 'cloud.json'))
                    self.assertEqual(snapshot, self.snapshot())
                self.assertEqual(([], [], 0), (self.service.reads, self.service.posts, self.service.provider_calls))

    def test_unsupported_saved_feed_is_not_promoted_after_readonly_observation(self):
        self.runtime()
        pub, _, valid = self.authority()
        # Create a hash-consistent unsupported candidate using the lower-level
        # state fixture API. Normal prepare's feed envelope does not admit it.
        original = pub.head
        parent = git(self.remote, 'rev-parse', original + '^')
        git(self.remote, 'update-ref', 'refs/heads/feed-state', parent)
        pub = Publisher(pub.store, self.code)
        pub.reconcile(None)
        doc = json.loads(valid['feed.json'])
        doc['schemaVersion'] = 99
        invalid = dict(valid, **{'feed.json': encoded(doc)})
        pub.prepare(pub.head, NOW, invalid, doc['catalogDigest'])
        self.service.live = invalid
        before = self.snapshot()
        self.cli('arm', '--expected-base', pub.head, '--artifact-id', '99', success=False)
        self.assertEqual([], self.service.reads)
        self.cli('recover', success=False)
        self.assertEqual(['/site/feed.json'], self.service.reads)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(([], 0), (self.service.posts, self.service.provider_calls))

    def test_old_source_cannot_mutate_quota_or_start_publication(self):
        self.runtime()
        pub, _, _ = self.authority()
        armed = self.cli('arm', '--expected-base', pub.head, '--artifact-id', '99')
        before = self.snapshot()
        git(self.source, 'commit', '--allow-empty', '-qm', 'new source authority')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        git(self.source, 'checkout', '-q', self.code)
        for command in ('arm', 'deploy', 'recover'):
            args = [command] if command == 'recover' else [command, '--expected-base', armed['head']]
            if command == 'arm':
                args += ['--artifact-id', '99']
            result = self.cli(*args, success=False)
            self.assertIn('queued source code is stale before work permission', result)
            self.assertEqual(before, self.snapshot())
        self.assertEqual(([], [], 0), (self.service.reads, self.service.posts, self.service.provider_calls))


if __name__ == '__main__':
    unittest.main()
