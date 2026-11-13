"""Current publisher/clock witnesses; retained observations are never replayed live.

Real local Git, current producer and loopback HTTP exercise new assertions. Saved
clock/hosted observations keep their original source and observation boundaries.
No provider, deployment, credential, SDK or phone operation is performed here.
"""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import unittest

from tests.test_current_motion_publisher import captured_starship, git, NOW
from tools.spacefox.catalog import build_catalog, canonical_bytes, CatalogError, loads_json
from tools.spacefox.cloud import CloudError, HTTP, Site
from tools.spacefox.native_motion import build_artifact, validate_feed, PROFILE
from tools.spacefox.provider import normalize_launch
from tools.spacefox.publisher import GitState, Publisher

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'openspec/changes/spacefox-watchface/evidence'
PACKET = EVIDENCE / 'basic-publisher-clock-whole'
PUBLICATION = EVIDENCE / 'basic-publication-20261113'
CLOCK = EVIDENCE / 'alternative-schedule-trigger'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(path.read_bytes())


def source_at(revision, name):
    return subprocess.run(['git', 'show', revision + ':' + name], cwd=ROOT,
                          check=True, capture_output=True).stdout


@contextmanager
def http_site(responder):
    requests = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests.append((self.command, self.path))
            status, body, headers = responder(self.path, len(requests))
            self.send_response(status)
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(body)
            self.close_connection = True

        def log_message(self, *_):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}', requests
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def current_source_closure():
    """Independent declarative JSON-pin walk, without materializer reports."""
    result = {'catalog/source.json': (ROOT / 'catalog/source.json').read_bytes()}
    recipe = json.loads(result['catalog/source.json'])
    curations = {item['path'] for item in recipe['curations']}

    def pins(value):
        if isinstance(value, dict):
            if {'path', 'sha256'} <= value.keys():
                yield value
            for child in value.values():
                yield from pins(child)
        elif isinstance(value, list):
            for child in value:
                yield from pins(child)

    pending, visited = ['catalog/source.json'], set()
    while pending:
        name = pending.pop()
        if name in visited:
            continue
        visited.add(name)
        try:
            row = json.loads(result[name])
        except (ValueError, UnicodeDecodeError):
            continue
        for pin in pins(row):
            raw = (ROOT / pin['path']).read_bytes()
            if sha(raw) != pin['sha256']:
                raise AssertionError('independent input pin: ' + pin['path'])
            result[pin['path']] = raw
            pending.append(pin['path'])
        assets = ([r for kind in ('models', 'countries', 'companies') for r in row[kind]]
                  if name == recipe['assetSeed']['path'] else
                  [r['facts'] for r in row['assets']] if name in curations else [])
        for facts in assets:
            path = (Path(name).parent / facts['file']).as_posix()
            raw = (ROOT / path).read_bytes()
            if 'sourceSha256' in facts and sha(raw) != facts['sourceSha256']:
                raise AssertionError('independent SVG pin: ' + path)
            result[path] = raw
    return result


def qualify_observation(observation, before, after, complete, jobs, events, configuration):
    """Independent evidence oracle; no product/service behavior is substituted."""
    assert observation['allFiveJobsPassed'] is True
    assert jobs['conclusion'] == 'success'
    assert {j['name'] for j in jobs['jobs'] if j['conclusion'] == 'success'} == {
        'prepare', 'arm', 'deploy', 'promote', 'metadata'}
    assert len(events['events']) >= 2
    assert len({e['runId'] for e in events['events']}) >= 2
    assert all(e['eventType'] == 'scheduled' and e['outcome'] == 'ok'
               and e['cron'] == '7,22,37,52 * * * *' for e in events['events'])
    assert configuration['bindingNamesAndTypes'] == [
        {'name': 'GITHUB_DISPATCH_TOKEN', 'type': 'secret_text'}]
    assert before['publisher']['instance'] == after['publisher']['instance']
    assert after['publisher']['generation'] > before['publisher']['generation']
    assert after['launch']['source_validated_utc'] > before['launch']['source_validated_utc']
    assert observation['sourceValidatedUtc'] == [before['launch']['source_validated_utc'], after['launch']['source_validated_utc']]
    assert observation['feedSha256'] == sha(canonical_bytes(after))
    assert complete['completeCurrentArtifactValidated'] is True
    assert complete['files'] == observation['currentCompleteArtifactValidation']['files']
    assert complete['totalBytes'] == observation['currentCompleteArtifactValidation']['bytes']
    assert complete['files'] <= 256 and complete['totalBytes'] <= 1048576
    assert before['nativeTransfer'] == after['nativeTransfer']
    assert before['visualSelection'] == after['visualSelection']
    assert before['catalogDigest'] == after['catalogDigest']


class BasicPublisherClockTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        cls.record = normalize_launch(captured_starship(), NOW)
        cls.temp = tempfile.TemporaryDirectory(prefix='spacefox-basic-publisher-')
        path = Path(cls.temp.name)
        remote, source = path / 'remote.git', path / 'source'
        source.mkdir()
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
        git(source, 'init', '-q')
        git(source, 'config', 'user.name', 'Local qualification')
        git(source, 'config', 'user.email', 'local@example.invalid')
        git(source, 'commit', '--allow-empty', '-qm', 'source')
        code = git(source, 'rev-parse', 'HEAD')
        git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
        cls.store = GitState(str(remote))
        cls.store.bootstrap(code)
        cls.pub = Publisher(cls.store, code)
        cls.pub.reconcile(None)
        token = cls.pub.reserve(cls.pub.head, NOW, trigger='scheduled')
        cls.pub.accept_source(cls.pub.head, token, (cls.record,), NOW, selection_validated_utc=NOW)
        cls.files, digest = build_artifact(cls.pub.schedule, cls.catalog, NOW,
            publisher=cls.pub.publisher_envelope(NOW), root=ROOT)
        cls.revision = cls.pub.prepare(cls.pub.head, NOW, cls.files, digest, artifact_profile=PROFILE)

    @classmethod
    def tearDownClass(cls):
        cls.store.close()
        cls.temp.cleanup()

    def unchanged(self):
        self.assertEqual(self.store.load()[0], self.pub.head)
        self.assertEqual(self.pub.ledger['selection_validated_utc'], NOW)
        self.assertEqual(len(self.pub.ledger['requests']), 1)
        self.assertEqual(self.pub.pending_files(), self.files)

    def test_personal_publication_positive(self):
        # Actual current G1/G2, complete artifact and unchanged deployed owners.
        observation = self.operational()
        self.assertEqual(observation['workflowRun'], 43433017023)
        public = read(PUBLICATION / 'twelve-closure-publication.json')
        self.assertFalse(public['privateHistoryAncestor'])
        # Check actual public ancestry from local objects; do not export private
        # history or turn an old snapshot's exact parent into a current contract.
        roots = subprocess.check_output(['git', 'rev-list', '--max-parents=0', 'HEAD'], cwd=ROOT).decode().splitlines()
        for root in roots:
            result = subprocess.run(['git', 'merge-base', '--is-ancestor', root, public['publicCommit']], cwd=ROOT)
            self.assertEqual(result.returncode, 1)
        bindings = read(PACKET / 'source-bindings.json')
        for name, digest in bindings['deployedRuntime'].items():
            self.assertEqual(sha((ROOT / name).read_bytes()), digest, name)
            self.assertEqual(sha(source_at(observation['sourceCommit'], name)), digest, name)

    def test_personal_privacy_positive(self):
        # Technical injection into an actual provider record: normalization has
        # no personal-data input channel and preserves the exact launch facts.
        row = captured_starship()
        row.update(heartRate=173, steps=9876, personalIdentifier='private-test-sentinel')
        self.assertEqual(normalize_launch(row, NOW), self.record)
        encoded = b''.join(self.files.values())
        for forbidden in (b'private-test-sentinel', b'heartRate', b'personalIdentifier'):
            self.assertNotIn(forbidden, encoded)
        feed = validate_feed(self.files['feed.json'])
        self.assertEqual(feed['launch']['launch_id'], 'll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b')
        self.assertEqual(feed['launch']['source_validated_utc'], NOW)

    def test_personal_privacy_negative(self):
        feed = json.loads(self.files['feed.json'])
        for key, value in [('heartRate', 173), ('personalIdentifier', 'private-test-sentinel')]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_feed(canonical_bytes(dict(feed, **{key: value})))
        for base in ('https://user:secret@example.invalid', 'http://example.invalid', 'https://example.invalid/?secret=x'):
            with self.subTest(base=base), self.assertRaises(CloudError):
                Site(base)
        self.unchanged()

    def test_http404_positive(self):
        with http_site(lambda *_: (404, b'x' * 9115, {'Content-Length': '9115'})) as (base, requests):
            self.assertEqual(HTTP().request('GET', base + '/feed.json', limit=8192), (404, b''))
            self.assertIsNone(Site(base, local_http=True).observe(type('Empty', (), {'ledger': {'active': None}})()))
            self.assertEqual(requests, [('GET', '/feed.json')] * 2)

    def test_http_admission_negative(self):
        for body, headers, status in [(b'x' * 8193, {'Content-Length': '8193'}, 200),
                                      (b'{}', {'Content-Length': '9'}, 200),
                                      (b'secret-body', {'Location': '/credential-sink'}, 302)]:
            with self.subTest(status=status, size=len(body)):
                with http_site(lambda *_: (status, body, headers)) as (base, requests):
                    with self.assertRaises(CloudError) as error:
                        HTTP().request('GET', base + '/feed.json', limit=8192)
                    self.assertNotIn('secret-body', str(error.exception))
                    self.assertEqual(requests, [('GET', '/feed.json')])

    def test_recipe_closure_and_rights(self):
        expected = current_source_closure()
        seed = (ROOT / '.github/spacefox-inputs.txt').read_bytes()
        for name in seed.decode().splitlines():
            path = ROOT / name.removeprefix('/')
            if path.is_file():
                expected[name.removeprefix('/')] = path.read_bytes()
        with tempfile.TemporaryDirectory(prefix='spacefox-basic-sparse-') as tmp:
            root = Path(tmp)
            for name, raw in expected.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
            git(root, 'init', '-q')
            git(root, 'config', 'user.name', 'Local qualification')
            git(root, 'config', 'user.email', 'local@example.invalid')
            git(root, 'add', '.')
            git(root, 'commit', '-qm', 'exact current declarative closure')
            subprocess.run(['git', 'sparse-checkout', 'set', '--no-cone', '--stdin'], cwd=root, input=seed, check=True, capture_output=True)
            command = [sys.executable, '-B', str(root / 'tools/cloud_inputs.py')]
            result = subprocess.run(command, cwd=root, capture_output=True, timeout=180)
            self.assertEqual(result.returncode, 0, result.stderr)
            actual = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*')
                      if p.is_file() and '.git' not in p.relative_to(root).parts}
            self.assertEqual(actual, expected)
            help_result = subprocess.run([sys.executable, '-B', str(root / 'tools/cloud_feed.py'), '--help'],
                                         cwd=root, capture_output=True, timeout=30)
            self.assertEqual(help_result.returncode, 0, help_result.stderr)
            self.assertEqual(git(root, 'status', '--porcelain'), '')
            # Corrupt a real source while skip-worktree conceals it from diff.
            recipe = read(root / 'catalog/source.json')
            name = recipe['curations'][0]['path']
            git(root, 'update-index', '--skip-worktree', name)
            before = git(root, 'rev-parse', 'HEAD')
            (root / name).write_bytes(b'corrupt-private-sentinel')
            result = subprocess.run(command, cwd=root, capture_output=True, timeout=180)
            self.assertEqual(result.returncode, 2)
            self.assertEqual((root / name).read_bytes(), b'corrupt-private-sentinel')
            self.assertNotIn(b'corrupt-private-sentinel', result.stderr)
            self.assertEqual(git(root, 'rev-parse', 'HEAD'), before)
            # Freshly pin an actual curation with unapproved rights, so the
            # rights guard, rather than a stale digest, must reject it.
            row = loads_json(expected[name])
            row['assets'][0]['facts']['license'] = 'unreviewed'
            raw = canonical_bytes(row)
            (root / name).write_bytes(raw)
            recipe['curations'][0]['sha256'] = sha(raw)
            (root / 'catalog/source.json').write_bytes(canonical_bytes(recipe))
            with self.assertRaisesRegex(CatalogError, 'MIT rights'):
                build_catalog(root)

    def test_readback_positive(self):
        with http_site(lambda path, _: (200, self.files[path[1:]], {})) as (base, requests):
            self.assertEqual(Site(base, local_http=True).observe(self.pub), self.revision)
            self.assertEqual([p for _, p in requests].count('/feed.json'), 2)
            self.assertEqual(set(p for _, p in requests), {'/' + p for p in self.files})
        self.unchanged()

    def test_readback_immutable_negative(self):
        target = next(p for p in self.files if p != 'feed.json')
        for status, raw in [(404, b''), (200, self.files[target] + b'private-test-sentinel')]:
            with self.subTest(status=status):
                def respond(path, _):
                    name = path[1:]
                    return (status, raw, {}) if name == target else (200, self.files[name], {})
                # Equal-length corrupt bytes reach readback diagnostics rather
                # than failing the transport's successful response size bound.
                if status == 200:
                    raw = b'x' * len(self.files[target])
                with http_site(respond) as (base, _), self.assertRaises(CloudError) as error:
                    Site(base, local_http=True).observe(self.pub)
                diagnostic = json.loads(str(error.exception).split('; readback=')[1])
                self.assertEqual(diagnostic, {'path': target, 'kind': 'immutable-file', 'phase': 'closure',
                    'status': status, 'expected': {'bytes': len(self.files[target]), 'sha256': sha(self.files[target])},
                    'actual': {'bytes': len(raw), 'sha256': sha(raw)}})
                self.assertNotIn('127.0.0.1', str(error.exception))
                self.assertNotIn('private-test-sentinel', str(error.exception))
                self.unchanged()

    def test_readback_root_negative(self):
        changed = b'x' * len(self.files['feed.json'])
        root_count = 0
        def respond(path, _):
            nonlocal root_count
            if path == '/feed.json':
                root_count += 1
                if root_count == 2:
                    return 200, changed, {}
            return 200, self.files[path[1:]], {}
        with http_site(respond) as (base, _), self.assertRaises(CloudError) as error:
            Site(base, local_http=True).observe(self.pub)
        row = json.loads(str(error.exception).split('; readback=')[1])
        self.assertEqual((row['path'], row['kind'], row['phase'], row['status']),
                         ('feed.json', 'mutable-root', 'after-closure', 200))
        self.assertEqual(row['actual'], {'bytes': len(changed), 'sha256': sha(changed)})
        self.unchanged()

    def test_readback_unavailable_negative(self):
        with http_site(lambda *_: (503, b'private-test-sentinel', {})) as (base, _):
            with self.assertRaises(CloudError) as error:
                Site(base, local_http=True).observe(self.pub)
        row = json.loads(str(error.exception).split('; readback=')[1])
        self.assertEqual((row['path'], row['kind'], row['phase'], row['status']),
                         ('feed.json', 'mutable-root', 'root', 503))
        self.assertNotIn('private-test-sentinel', str(error.exception))
        self.unchanged()

    def operational(self):
        for name, digest in read(PACKET / 'source-bindings.json')['operationalReceipts'].items():
            self.assertEqual(sha((ROOT / name).read_bytes()), digest, name)
        observation = read(PUBLICATION / 'AUTO-DUE-ACCEPTANCE.json')
        args = [observation, read(PUBLICATION / 'map-only-public-feed.json'),
                read(PUBLICATION / 'auto-due-feed.json'), read(PUBLICATION / 'map-only-complete-artifact-readback.json'),
                read(PUBLICATION / 'auto-due-jobs.json'), read(CLOCK / 'live-qualification-r1/clock-events.json'),
                read(CLOCK / 'root-live/16-server-configuration-audit.json')]
        qualify_observation(*args)
        deployed = read(CLOCK / 'root-live/fixed-runtime/42-deployed-source-readback.json')
        self.assertEqual(deployed['sourceSha256'], sha((ROOT / 'deploy/cloudflare-schedule/worker.mjs').read_bytes()))
        return observation

    def test_current_linux_retained(self):
        # Reuse actual Ubuntu11 with exact source/data/renderer inputs.
        text = (PUBLICATION / 'ubuntu-43417089608.log').read_text(encoding='utf-8-sig')
        original = '4db280e92f8cd29f5523a15d9f8b239a7733bba6'
        self.assertIn(original, text)
        self.assertIn('rsvg-convert version 2.58.0', text)
        observed = re.findall(r'Z (test_\w+) \((tests\.test_current_\w+\.\w+\.test_\w+)\) \.\.\. ok', text)
        expected = {
            'test_actual_launch_whole_publication_and_refusal', 'test_cloud_journal_updates_current_state_ref',
            'test_current_integer_discriminators', 'test_current_policy_requires_complete_explicit_envelope',
            'test_durable_policy_and_selected_cadence_bind_current_artifact', 'test_operator_cli_prepares_current_artifact',
            'test_shared_rolling_hour_quota_survives_reopen',
            'test_captured_whole_traversal_reopens_preserves_ages_and_source_headroom',
            'test_current_policy_is_the_only_default', 'test_expired_current_prefix_restarts_without_renewing_source_or_quota',
            'test_obsolete_metadata_journals_are_refused'}
        self.assertEqual({name for name, _ in observed}, expected)
        self.assertEqual(len(observed), 11)
        self.assertRegex(text, r'Ran 11 tests in [0-9.]+s')
        self.assertNotIn('FAILED (', text)
        names = set(read(PACKET / 'source-bindings.json')['deployedRuntime']) | set(current_source_closure()) | {
            'tests/test_current_motion_publisher.py', 'tests/test_current_metadata_publisher.py',
            'tests/fixtures/provider/current-starship/captured-page.json.gz',
            'tests/fixtures/provider/current-starship/receipt.json',
            'tests/fixtures/metadata-current/captured-schema3.zip',
            'tests/fixtures/metadata-current/captured-schema3-receipt.json'}
        for name in sorted(names):
            self.assertEqual((ROOT / name).read_bytes(), source_at(original, name), name)

    def test_clock_operational_positive(self):
        self.operational()

    def test_clock_operational_negative(self):
        args = [read(PUBLICATION / 'AUTO-DUE-ACCEPTANCE.json'), read(PUBLICATION / 'map-only-public-feed.json'),
                read(PUBLICATION / 'auto-due-feed.json'), read(PUBLICATION / 'map-only-complete-artifact-readback.json'),
                read(PUBLICATION / 'auto-due-jobs.json'), read(CLOCK / 'live-qualification-r1/clock-events.json'),
                read(CLOCK / 'root-live/16-server-configuration-audit.json')]
        for defect in ('dispatch-only', 'one-event', 'not-due', 'incomplete', 'plain-secret'):
            changed = deepcopy(args)
            if defect == 'dispatch-only':
                changed[0]['allFiveJobsPassed'] = False
            elif defect == 'one-event':
                changed[5]['events'] = changed[5]['events'][:1]
            elif defect == 'not-due':
                changed[2]['launch']['source_validated_utc'] = changed[1]['launch']['source_validated_utc']
            elif defect == 'incomplete':
                changed[3]['completeCurrentArtifactValidated'] = False
            else:
                changed[6]['bindingNamesAndTypes'][0]['type'] = 'plain_text'
            with self.subTest(defect=defect), self.assertRaises(AssertionError):
                qualify_observation(*changed)

    def retained_tap(self, name, expected):
        bindings = read(PACKET / 'source-bindings.json')
        for path, digest in bindings['clockSources'].items():
            self.assertEqual(sha((ROOT / path).read_bytes()), digest, path)
        for receipt in bindings['clockReceipts']:
            if receipt['kind'] != name:
                continue
            raw = (ROOT / receipt['path']).read_bytes()
            self.assertEqual(sha(raw), receipt['sha256'])
            text = raw.decode()
            self.assertEqual(re.findall(r'^ok \d+ - (.+)$', text, re.M), expected)
            self.assertRegex(text, rf'(?m)^# pass {len(expected)}$')
            self.assertRegex(text, r'(?m)^# fail 0$')
            self.assertRegex(text, r'(?m)^# skipped 0$')
            return
        self.fail('missing original TAP binding: ' + name)

    def test_clock_retained_dispatch_deadline(self):
        self.retained_tap('dispatch', ['scheduled boundary, failures, concurrency and secret safety',
            'dispatch uses a Workers-supported redirect mode',
            'clock aborts a stalled real HTTP dispatch near ten seconds',
            'clock isolates rejected wakeups and never follows redirect destinations'])

    def test_clock_retained_configuration(self):
        self.retained_tap('configuration', [
            'clock configuration explicitly disables public URLs and has only the Cron trigger',
            'clock configuration checker rejects an omitted preview switch or added route'])

    def test_clock_retained_isolation_negative(self):
        self.retained_tap('dispatch', ['scheduled boundary, failures, concurrency and secret safety',
            'dispatch uses a Workers-supported redirect mode',
            'clock aborts a stalled real HTTP dispatch near ten seconds',
            'clock isolates rejected wakeups and never follows redirect destinations'])

    def test_clock_retained_configuration_negative(self):
        self.retained_tap('configuration', [
            'clock configuration explicitly disables public URLs and has only the Cron trigger',
            'clock configuration checker rejects an omitted preview switch or added route'])
