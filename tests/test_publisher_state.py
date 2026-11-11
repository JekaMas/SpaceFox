"""Real local-Git state authority tests; deployment port is deliberately controlled."""
import copy
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from tools.spacefox.publisher import (GitState, Publisher, StateError, Conflict,
                                     LiveRevision, decode_ledger)
from tools.spacefox.schedule import (IdKind, StableId, Timing, TimePrecision,
                                    LaunchRecord, LaunchStatus, RefreshPolicy)


def git(path, *args, data=None):
    return subprocess.run(['git', '-C', str(path), *args], input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=True).stdout.decode().strip()


def record(at=1000, target=9000, name='A'):
    return LaunchRecord(StableId(IdKind.LAUNCH, 'll2', name),
                        Timing(TimePrecision.EXACT, target), LaunchStatus.PENDING, at,
                        configuration_id=StableId(IdKind.CONFIGURATION, 'll2', 'zero'),
                        mission_name='Луна')


class ConditionalSite:
    """Replaces the serialized deployment/readback owner, never Git state."""
    def __init__(self):
        self.live = None
        self.files = {}
        self.calls = 0
        self.crash = False
        self.wrong_readback = False

    def readback(self):
        if self.wrong_readback:
            return LiveRevision(999, 'f' * 64)
        return self.live

    def deploy(self, expected_live, revision, files):
        if self.live != expected_live:
            raise StateError('conditional deployment lost expected live revision')
        if self.live is not None and revision.generation < self.live.generation:
            raise StateError('site cannot regress')
        self.calls += 1
        self.live, self.files = revision, dict(files)
        if self.crash:
            raise RuntimeError('runner lost after externally visible deploy')


class PublisherStateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.remote = self.root / 'remote.git'
        self.source = self.root / 'source'
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        git(self.source, 'config', 'user.name', 'Test')
        git(self.source, 'config', 'user.email', 'test@example.invalid')
        git(self.source, 'commit', '--allow-empty', '-qm', 'source one')
        self.code = git(self.source, 'rev-parse', 'HEAD')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.store = GitState(str(self.remote))
        self.store.bootstrap(self.code)
        self.site = ConditionalSite()
        self.pub = Publisher(self.store, self.code)
        self.pub.reconcile(self.site.readback())

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def reopen(self):
        self.pub = Publisher(self.store, self.code)
        return self.pub

    def reserve(self, now=1000, **kwargs):
        return self.pub.reserve(self.pub.head, now, **kwargs)

    def accept(self, at=1000, target=9000):
        token = self.reserve(at, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (record(at, target),), at)

    def prepare(self, now=1000):
        return self.pub.prepare(self.pub.head, now, {'feed.json': b'{"utc":1000}',
                                'images/unchanged.svg': b'<svg/>'}, 'c' * 64)

    def test_shared_budget_and_no_due_positive(self):
        self.accept()
        before = self.pub.head
        self.assertIsNone(self.reserve(1100))
        self.assertEqual(before, self.pub.head)
        self.assertEqual(0, self.site.calls)
        for i in range(14):
            token = self.reserve(1100 + i, purpose=('catalog' if i % 2 else 'version'),
                                 trigger='manual')
            self.pub.finish_request(self.pub.head, token, 1100 + i, 'success')
        self.assertEqual(15, len(self.pub.ledger['requests']))
        with self.assertRaises(StateError):
            self.reserve(1200, trigger='retry')
        self.assertEqual(1000, self.pub.schedule.entries[0].record.source_validated_utc)
        self.reopen().reconcile(None)
        with self.assertRaises(StateError):
            self.reserve(1300, purpose='catalog', trigger='manual')
        token = self.reserve(4800, purpose='catalog', trigger='manual')
        self.assertIsNotNone(token)
        self.assertEqual(1, len(self.pub.ledger['requests']))

    def test_shared_budget_and_no_due_negative(self):
        self.accept()
        before = self.pub.head
        token = self.reserve(2000, trigger='retry')
        durable = self.pub.head
        self.assertNotEqual(before, durable)
        self.reopen().reconcile(None)
        with self.assertRaises(StateError):
            self.reserve(2001, trigger='retry')
        self.assertEqual(durable, self.pub.head)
        self.pub.finish_request(self.pub.head, token, 2002, 'throttled', retry_after_utc=3000)
        self.reopen().reconcile(None)
        before = self.pub.head
        with self.assertRaises(StateError):
            self.reserve(2999, purpose='version', trigger='manual')
        self.assertEqual(before, self.pub.head)
        self.assertEqual(3000, self.pub.ledger['backoff_until_utc'])
        self.assertEqual(1000, self.pub.schedule.entries[0].record.source_validated_utc)

    def test_zero_utc_backoff_is_retained(self):
        # Two real outstanding requests can finish while the shared deadline is
        # UTC zero. Zero is a valid deadline, distinct from no deadline (None).
        first = self.reserve(-1000, trigger='manual')
        second = self.reserve(-900, trigger='manual')
        self.pub.finish_request(self.pub.head, first, -300, 'failed', retry_after_utc=0)
        self.reopen().reconcile(None)
        self.assertEqual(0, self.pub.ledger['backoff_until_utc'])
        before = self.pub.head
        self.pub.finish_request(self.pub.head, second, -200, 'throttled', retry_after_utc=-100)
        self.assertNotEqual(before, self.pub.head)
        self.reopen().reconcile(None)
        self.assertEqual(0, self.pub.ledger['backoff_until_utc'])
        self.assertEqual(['failed', 'throttled'],
                         [request['outcome'] for request in self.pub.ledger['requests']])
        before = self.pub.head
        with self.assertRaises(StateError):
            self.reserve(-1, purpose='catalog', trigger='manual')
        self.assertEqual(before, self.pub.head)
        self.assertIsNotNone(self.reserve(0, purpose='catalog', trigger='manual'))
        self.assertEqual(3, len(self.pub.ledger['requests']))

    def test_durable_source_state_positive(self):
        self.accept()
        token = self.reserve(2000, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (record(2000, 10200),), 2000)
        token = self.reserve(3000, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (record(3000, 10200), record(2500, 11000, 'B')), 3000)
        self.pub.observe_age(self.pub.head, 18000)
        self.reopen().reconcile(None)
        a, b = self.pub.schedule.entries
        self.assertEqual((3000, 2500), (a.record.source_validated_utc, b.record.source_validated_utc))
        self.assertEqual((True, True, False, True), (a.rescheduled, a.stale, b.rescheduled, b.stale))
        self.assertIsNone(a.record.site_id)
        self.assertEqual((IdKind.CONFIGURATION, 'll2', 'zero'),
                         (a.record.configuration_id.kind, *a.record.configuration_id.key))
        self.assertEqual('Луна', a.record.mission_name)
        self.prepare(18000)
        self.pub.deploy_pending(self.pub.head, self.site)
        self.reopen().reconcile(self.site.readback())
        self.assertEqual((3000, 2500), tuple(x.record.source_validated_utc for x in self.pub.schedule.entries))

    def test_durable_source_state_negative(self):
        self.accept()
        token = self.reserve(2000, trigger='manual')
        before = self.pub.head
        with self.assertRaises(StateError):
            self.pub.accept_source(self.pub.head, token, (record(999),), 2000)
        self.assertEqual(before, self.pub.head)
        self.pub.finish_request(self.pub.head, token, 2000, 'success')
        self.assertEqual(1000, self.pub.schedule.entries[0].record.source_validated_utc)
        self.prepare(2000)
        self.pub.deploy_pending(self.pub.head, self.site)
        self.assertEqual(1000, self.pub.schedule.entries[0].record.source_validated_utc)
        with self.assertRaises(StateError):
            self.pub.finish_request(self.pub.head, token, 2100, 'success')

    def test_authority_reopen_positive(self):
        self.accept()
        head = self.pub.head
        other = GitState(str(self.remote))
        try:
            pub = Publisher(other, self.code)
            self.assertEqual(head, pub.head)
            self.assertEqual(1000, pub.schedule.entries[0].record.source_validated_utc)
            self.assertEqual(1, len(pub.ledger['requests']))
        finally:
            other.close()
        with self.assertRaises(StateError):
            self.store.bootstrap(self.code)

    def test_lost_reservation_negative(self):
        self.accept()
        code = '''import os,sys\nfrom tools.spacefox.publisher import GitState,Publisher\ns=GitState(sys.argv[1]);p=Publisher(s,sys.argv[2]);p.reconcile(None)\np.reserve(p.head,2000,trigger="retry")\nos._exit(9)\n'''
        lost = subprocess.run([sys.executable, '-B', '-c', code, str(self.remote), self.code],
                              capture_output=True, text=True)
        self.assertEqual(9, lost.returncode, lost.stderr)
        self.reopen().reconcile(None)
        before = self.pub.head
        with self.assertRaises(StateError):self.reserve(2001, trigger='retry')
        self.assertEqual(before, self.pub.head)
        self.assertEqual(2, len(self.pub.ledger['requests']))
        self.assertEqual('reserved', self.pub.ledger['requests'][-1]['outcome'])
        self.assertEqual(1000, self.pub.schedule.entries[0].record.source_validated_utc)
        self.assertIsNotNone(self.reserve(2061, trigger='retry'))
        self.assertEqual(3, len(self.pub.ledger['requests']))

    def test_authority_reopen_negative(self):
        self.accept()
        old = self.pub.head
        git(self.remote, 'update-ref', '-d', 'refs/heads/feed-state')
        with self.assertRaises(StateError):
            Publisher(self.store, self.code)
        with self.assertRaises(StateError):
            self.store.bootstrap(self.code)
        git(self.remote, 'update-ref', 'refs/heads/feed-state', old)
        self.reopen().reconcile(None)
        before = self.pub.head
        cases = [b'{"schema_version":1,"schema_version":1}', b'{"a":NaN}',
                 b'[]', b'{' + b' ' * 65536 + b'}']
        doc = copy.deepcopy(self.pub.ledger)
        doc['schema_version'] = 999
        cases.append(json.dumps(doc).encode())
        doc = copy.deepcopy(self.pub.ledger)
        doc['accepted']['entries'][0]['record']['source_validated_utc'] = 999
        cases.append(json.dumps(doc).encode())
        for raw in cases:
            with self.subTest(raw=raw[:60]):
                with self.assertRaises(StateError):
                    self.pub.import_ledger(before, raw)
                self.assertEqual(before, git(self.remote, 'rev-parse', 'refs/heads/feed-state'))

    def test_pending_recovery_positive(self):
        self.accept()
        expected_schedule = json.loads((Path(__file__).parent / 'fixtures/state/accepted-literal.json').read_bytes())
        self.assertEqual(expected_schedule, self.pub.ledger['accepted'])
        self.prepare()
        independent = {'generation': 1, 'code_revision': self.code, 'catalog_revision': 'c' * 64,
                       'schedule': expected_schedule,
                       'files': {'feed.json': {'sha256': hashlib.sha256(b'{"utc":1000}').hexdigest(), 'bytes': 12},
                                 'images/unchanged.svg': {'sha256': hashlib.sha256(b'<svg/>').hexdigest(), 'bytes': 6}}}
        expected_digest = hashlib.sha256(json.dumps(independent, ensure_ascii=False, sort_keys=True,
                                                   separators=(',', ':')).encode()).hexdigest()
        self.assertEqual(expected_digest, self.pub.ledger['pending']['artifact_revision'])
        self.assertEqual(1, self.pub.ledger['generation'])
        pending_head = self.pub.head
        self.site.crash = True
        with self.assertRaises(RuntimeError):
            self.pub.deploy_pending(self.pub.head, self.site)
        self.assertEqual(pending_head, self.pub.head)
        self.reopen().reconcile(self.site.readback())
        self.assertIsNone(self.pub.ledger['pending'])
        self.assertEqual(1, self.pub.ledger['active']['generation'])
        self.assertEqual(1, self.site.calls)
        self.prepare(1001)
        self.assertEqual(2, self.pub.ledger['pending']['generation'])

    def test_pending_recovery_negative(self):
        self.accept()
        stale = self.pub.head
        self.prepare()
        self.reopen()
        before = self.pub.head
        with self.assertRaises(StateError):
            self.reserve(2000, trigger='manual')
        self.assertEqual('retry_pending', self.pub.reconcile(None))
        with self.assertRaises(StateError):
            self.prepare(2000)
        with self.assertRaises(Conflict):
            self.pub.deploy_pending(stale, self.site)
        self.assertEqual(0, self.site.calls)
        self.site.wrong_readback = True
        with self.assertRaises(StateError):
            self.pub.deploy_pending(self.pub.head, self.site)
        self.assertEqual(before, self.pub.head)
        self.assertIsNone(self.pub.ledger['active'])

    def test_git_cas_positive(self):
        # Two independent Python workers, each holding the same real remote base.
        base = self.pub.head
        code = '''import sys\nfrom pathlib import Path\nfrom tools.spacefox.publisher import GitState,Publisher,Conflict\ns=GitState(sys.argv[1]);p=Publisher(s,sys.argv[2]);p.reconcile(None)\nPath(sys.argv[3]).write_text(p.head)\nsys.stdin.readline()\ntry:\n p.reserve(sys.argv[4],1000,trigger="manual");print("winner",flush=True)\nexcept Conflict:print("conflict",flush=True)\nfinally:s.close()\n'''
        procs = []
        for i in range(2):
            ready = self.root / f'ready{i}'
            proc = subprocess.Popen([sys.executable, '-B', '-c', code, str(self.remote), self.code,
                                     str(ready), base], stdin=subprocess.PIPE,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            procs.append((proc, ready))
        # Readiness is a real process barrier; bounded process wait, no model sleep.
        import time
        deadline = time.monotonic() + 10
        while not all(p.exists() for _, p in procs):
            if time.monotonic() > deadline:
                self.fail('worker barrier timed out')
            time.sleep(.01)
        outputs = []
        for p, _ in procs:
            p.stdin.write('go\n');p.stdin.flush()
        for p, _ in procs:
            out, err = p.communicate(timeout=15)
            self.assertEqual(0, p.returncode, err)
            outputs.append(out.strip())
        self.assertEqual(['conflict', 'winner'], sorted(outputs))
        self.reopen().reconcile(None)
        self.assertEqual(1, len(self.pub.ledger['requests']))

    def test_git_cas_negative(self):
        old = self.pub.head
        self.accept()
        current = self.pub.head
        with self.assertRaises(Conflict):
            self.pub.reserve(old, 2000, trigger='manual')
        self.prepare()
        current = self.pub.head
        git(self.source, 'commit', '--allow-empty', '-qm', 'source two')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        with self.assertRaises(StateError):
            self.reserve(2000, trigger='manual')
        self.assertEqual(current, git(self.remote, 'rev-parse', 'refs/heads/feed-state'))
        new_code = git(self.source, 'rev-parse', 'HEAD')
        newer = Publisher(self.store, new_code)
        newer.adopt_code(newer.head)
        self.assertEqual(self.code, newer.ledger['pending']['code_revision'])
        self.assertEqual('retry_pending', newer.reconcile(None))
        newer.deploy_pending(newer.head, self.site)
        self.assertIsNotNone(newer.reserve(newer.head, 2000, trigger='manual'))
        real_git = self.store._git
        advanced = False

        def advancing_git(*args, **kwargs):
            nonlocal advanced
            result = real_git(*args, **kwargs)
            if args[0] == 'push' and not advanced:
                advanced = True
                git(self.source, 'commit', '--allow-empty', '-qm', 'source three')
                git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
            return result

        self.store._git = advancing_git
        with self.assertRaises(StateError):newer.reserve(newer.head, 2061, trigger='manual')
        # An acknowledgement/code race consumes quota, but gives no request token.
        self.assertEqual(3, len(Publisher(self.store, new_code).ledger['requests']))

    def test_artifact_reconstruction_and_growth(self):
        self.accept()
        self.prepare()
        expected = {'feed.json': b'{"utc":1000}', 'images/unchanged.svg': b'<svg/>'}
        self.reopen().reconcile(None)
        self.assertEqual(expected, self.pub.pending_files())
        self.pub.deploy_pending(self.pub.head, self.site)
        for t in range(1001, 1011):
            self.prepare(t)
            self.pub.deploy_pending(self.pub.head, self.site)
        measurement = self.store.measure()
        self.assertLessEqual(measurement['ledger_bytes'], 65536)
        self.assertEqual(25, measurement['commits'])
        self.assertGreater(measurement['history_object_bytes'], measurement['ledger_bytes'])
        print('STATE_GROWTH ' + json.dumps(measurement, sort_keys=True))

    def test_push_fault_boundaries(self):
        real_git = self.store._git
        phase = None

        def faulting_git(*args, **kwargs):
            nonlocal phase
            if args[0] == 'push' and phase == 'before':
                phase = None
                raise StateError('injected process loss before remote push')
            result = real_git(*args, **kwargs)
            if args[0] == 'push' and phase == 'after':
                phase = None
                raise StateError('injected lost acknowledgement after actual remote push')
            return result

        self.store._git = faulting_git
        before = self.pub.head
        phase = 'before'
        with self.assertRaises(StateError):self.reserve(1000, trigger='manual')
        self.reopen().reconcile(None)
        self.assertEqual(before, self.pub.head)
        self.assertEqual([], self.pub.ledger['requests'])
        phase = 'after'
        with self.assertRaises(StateError):self.reserve(1000, trigger='manual')
        self.reopen().reconcile(None)
        self.assertNotEqual(before, self.pub.head)
        self.assertEqual(1, len(self.pub.ledger['requests']))
        with self.assertRaises(StateError):self.reserve(1001, trigger='manual')
        phase = 'before'
        before = self.pub.head
        with self.assertRaises(StateError):self.prepare(1061)
        self.reopen().reconcile(None)
        self.assertEqual(before, self.pub.head)
        self.assertIsNone(self.pub.ledger['pending'])
        phase = 'after'
        with self.assertRaises(StateError):self.prepare(1061)
        self.reopen().reconcile(None)
        self.assertEqual(1, self.pub.ledger['pending']['generation'])
        self.site.live = LiveRevision(1, self.pub.ledger['pending']['artifact_revision'])
        phase = 'before'
        before = self.pub.head
        with self.assertRaises(StateError):self.pub.reconcile(self.site.readback())
        self.assertEqual(before, self.pub.head)
        phase = 'after'
        with self.assertRaises(StateError):self.pub.reconcile(self.site.readback())
        self.reopen().reconcile(self.site.readback())
        self.assertIsNone(self.pub.ledger['pending'])
        self.assertEqual(1, self.pub.ledger['active']['generation'])

    def test_artifact_and_corrupt_authority_negative(self):
        self.accept()
        before = self.pub.head
        bad_files = ({'../outside': b'x'}, {'x': b'x' * 1048577},
                     {'x': b'a', 'x/nested': b'b'}, {'x': 'not bytes'})
        for files in bad_files:
            with self.assertRaises(StateError):self.pub.prepare(before, 1000, files, 'c' * 64)
            self.assertEqual(before, git(self.remote, 'rev-parse', 'refs/heads/feed-state'))
        # Corrupt the actual authority through real Git objects. This is a test
        # administrator, not a permitted product recovery path.
        regressing = copy.deepcopy(self.pub.ledger)
        regressing['accepted']['entries'][0]['record']['source_validated_utc'] = 999
        corrupt_inputs = (b'{"x":NaN}', b'{"schema_version":1,"schema_version":1}',
                          b'[]', json.dumps(regressing).encode())
        for raw in corrupt_inputs:
            blob = git(self.remote, 'hash-object', '-w', '--stdin', data=raw)
            tree = git(self.remote, 'mktree', data=f'100644 blob {blob}\tledger.json\n'.encode())
            # commit-tree needs an identity, supplied only to this local bare repo.
            git(self.remote, 'config', 'user.name', 'Corrupt fixture')
            git(self.remote, 'config', 'user.email', 'fixture@example.invalid')
            corrupt = git(self.remote, 'commit-tree', tree, '-p', before, data=b'corrupt fixture\n')
            git(self.remote, 'update-ref', 'refs/heads/feed-state', corrupt, before)
            with self.assertRaises(StateError):Publisher(self.store, self.code)
            self.assertEqual(corrupt, git(self.remote, 'rev-parse', 'refs/heads/feed-state'))
            git(self.remote, 'update-ref', 'refs/heads/feed-state', before, corrupt)
        self.reopen().reconcile(None)
        self.assertEqual(1000, self.pub.schedule.entries[0].record.source_validated_utc)

    def test_strict_utf8_ledger_admission(self):
        # Only instance/source identity comes from setup; the malformed wire and
        # expected rejection are independent of the production serializer.
        before = self.pub.head
        literal_record = {
            'launch_id': {'kind': 'launch', 'namespace': 'literal', 'value': 'one'},
            'configuration_id': None, 'operator_id': None, 'site_id': None, 'country_id': None,
            'configuration_name': None, 'operator_name': None, 'mission_name': '月' * 22000,
            'mission_purpose': None, 'timing': {'precision': 'unknown', 'exact_utc': None,
                'date_utc': None, 'window_start_utc': None, 'window_end_utc': None},
            'status': 'unknown', 'source_validated_utc': 0}
        literal = {'schema_version': 1, 'instance_id': self.pub.ledger['instance_id'],
                   'code_revision': self.code, 'refresh_policy': {'normal_interval_seconds': 3600,
                       'near_interval_seconds': 900, 'fast_interval_seconds': None, 'stale_cycles': 3},
                   'generation': 0, 'accepted': {'entries': [{'record': literal_record,
                       'rescheduled': False, 'stale': False}], 'evaluated_at_utc': 0},
                   'active': None, 'pending': None, 'last_event_utc': 0,
                   'last_poll_utc': None, 'backoff_until_utc': None, 'requests': []}
        text = json.dumps(literal, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        self.assertGreater(len(text.encode('utf-8')), 65536)
        utf16 = text.encode('utf-16')
        self.assertLess(len(utf16), 65536)
        small = dict(literal, accepted={'entries': [], 'evaluated_at_utc': 0})
        utf32 = json.dumps(small, separators=(',', ':')).encode('utf-32')
        git(self.remote, 'config', 'user.name', 'Malformed encoding fixture')
        git(self.remote, 'config', 'user.email', 'fixture@example.invalid')
        for raw in (utf16, utf32):
            with self.subTest(encoding='utf16' if raw is utf16 else 'utf32'):
                with self.assertRaises(StateError):
                    decode_ledger(raw)
                blob = git(self.remote, 'hash-object', '-w', '--stdin', data=raw)
                tree = git(self.remote, 'mktree', data=f'100644 blob {blob}\tledger.json\n'.encode())
                invalid = git(self.remote, 'commit-tree', tree, '-p', before,
                              data=b'malformed encoding fixture\n')
                git(self.remote, 'update-ref', 'refs/heads/feed-state', invalid, before)
                with self.assertRaises(StateError):
                    Publisher(self.store, self.code)
                self.assertEqual(invalid, git(self.remote, 'rev-parse', 'refs/heads/feed-state'))
                git(self.remote, 'update-ref', 'refs/heads/feed-state', before, invalid)
        self.reopen().reconcile(None)
        self.assertEqual(before, self.pub.head)

    def test_persisted_fast_policy(self):
        # A separate instance has explicit bootstrap policy, recovered by default.
        remote = self.root / 'fast.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
        git(self.source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
        store = GitState(str(remote))
        try:
            store.bootstrap(self.code, RefreshPolicy(fast_interval_seconds=300))
            pub = Publisher(store, self.code)
            pub.reconcile(None)
            token = pub.reserve(pub.head, 1000)
            pub.accept_source(pub.head, token, (record(),), 1000)
            pub = Publisher(store, self.code)
            pub.reconcile(None)
            self.assertEqual(300, pub.policy.fast_interval_seconds)
            for index in range(1, 12):
                token = pub.reserve(pub.head, 1000 + 300 * index)
                pub.finish_request(pub.head, token, 1000 + 300 * index, 'success')
            self.assertEqual(12, len(pub.ledger['requests']))
            before = pub.head
            self.assertIsNone(pub.reserve(pub.head, 4599))
            self.assertEqual(before, pub.head)
            pub.observe_age(pub.head, 4600)
            self.assertTrue(Publisher(store, self.code).schedule.entries[0].stale)
            with self.assertRaises(StateError):Publisher(store, self.code, RefreshPolicy())
        finally:
            store.close()

    def test_portable_local_cli(self):
        import shutil
        portable = self.root / 'portable'
        (portable / 'tools/spacefox').mkdir(parents=True)
        repo = Path(__file__).resolve().parents[1]
        for relative in ('tools/__init__.py', 'tools/spacefox/__init__.py',
                         'tools/spacefox/schedule.py', 'tools/spacefox/publisher.py',
                         'tools/publisher_state.py'):
            # tools is a namespace package in this checkout.
            source = repo / relative
            if source.exists():shutil.copyfile(source, portable / relative)
        entry = portable / 'tools/publisher_state.py'

        def command(*args, expected=None, success=True):
            argv = [sys.executable, '-B', str(entry), '--remote', str(self.remote),
                    '--running-code', self.code]
            if expected is not None:argv.extend(['--expected-base', expected])
            result = subprocess.run(argv + list(args), cwd=portable, capture_output=True, text=True)
            self.assertEqual(0 if success else 2, result.returncode, result.stderr)
            return json.loads(result.stdout) if success else result

        status = command('status')
        reserved = command('reserve', '--now', '1000', '--trigger', 'manual', expected=status['head'])
        self.assertIsInstance(reserved['result'], str)
        fixture = repo / 'tests/fixtures/state/accepted-literal.json'
        accepted = command('accept-source', '--now', '1000', '--token', reserved['result'],
                           '--schedule', str(fixture), expected=reserved['head'])
        directory = self.root / 'input'
        directory.mkdir()
        (directory / 'feed.json').write_bytes(b'{"value":0}')
        pending = command('prepare', '--now', '1000', '--catalog-revision', 'c' * 64,
                          '--directory', str(directory), expected=accepted['head'])
        output = self.root / 'recovered'
        command('export-pending', '--directory', str(output), expected=pending['head'])
        self.assertEqual(b'{"value":0}', (output / 'feed.json').read_bytes())
        command('reserve', '--now', '2000', expected=status['head'], success=False)
        self.assertFalse((portable / '.agents').exists())

    def test_event_trace_model(self):
        # Literal oracle: requests consume15 slots, each accepted candidate gets
        # one generation, exact live visibility alone promotes. Compare each step.
        required = {'request': {'applied', 'observed_no_mutation'},
                    'source': {'applied', 'observed_no_mutation'},
                    'opaque_success': {'applied'},
                    'candidate': {'applied', 'observed_no_mutation'},
                    'readback': {'applied', 'observed_no_mutation'},
                    'restart': {'observed_no_mutation'}}
        seen = {k: set() for k in required}
        events = ['request', 'source', 'request', 'source_moved', 'invalid_source',
                  'request', 'opaque_success', 'candidate', 'request', 'candidate',
                  'restart', 'bad_readback', 'deploy_crash', 'restart', 'readback']
        rng = random.Random(83115)
        events += [rng.choice(['request', 'candidate', 'restart', 'readback']) for _ in range(24)]
        pending = False
        generation = active = requests = 0
        source_time = 0
        evaluated_time = None
        source_target = 9000
        rescheduled = False
        token = None
        revisions = {}
        literal = json.loads((Path(__file__).parent / 'fixtures/state/accepted-literal.json').read_bytes())

        def expected_schedule():
            if source_time == 0:return {'entries': [], 'evaluated_at_utc': evaluated_time}
            expected = copy.deepcopy(literal)
            expected['evaluated_at_utc'] = evaluated_time
            expected['entries'][0]['record']['source_validated_utc'] = source_time
            expected['entries'][0]['record']['timing']['exact_utc'] = source_target
            expected['entries'][0]['rescheduled'] = rescheduled
            return expected

        def expected_revision(number):
            facts = {'generation': number, 'code_revision': self.code, 'catalog_revision': 'c' * 64,
                     'schedule': expected_schedule(),
                     'files': {'feed.json': {'sha256': hashlib.sha256(b'{"utc":1000}').hexdigest(), 'bytes': 12},
                               'images/unchanged.svg': {'sha256': hashlib.sha256(b'<svg/>').hexdigest(), 'bytes': 6}}}
            return hashlib.sha256(json.dumps(facts, ensure_ascii=False, sort_keys=True,
                                              separators=(',', ':')).encode()).hexdigest()
        now = 1000
        trace = []
        for index, event in enumerate(events):
            now += 61
            before = self.pub.head
            disposition = 'observed_no_mutation'
            try:
                if event == 'request':
                    allowed = not pending and requests < 15
                    if allowed:
                        token = self.reserve(now, trigger='manual');requests += 1;disposition = 'applied'
                    else:
                        with self.assertRaises(StateError):self.reserve(now, trigger='manual')
                elif event in ('source', 'source_moved'):
                    source_time = now
                    evaluated_time = now
                    if event == 'source_moved':source_target = 10200;rescheduled = True
                    self.pub.accept_source(self.pub.head, token, (record(now, source_target),), now)
                    disposition = 'applied'
                elif event == 'invalid_source':
                    with self.assertRaises(StateError):
                        self.pub.accept_source(self.pub.head, token, (record(999),), now)
                elif event == 'opaque_success':
                    self.pub.finish_request(self.pub.head, token, now, 'success')
                    disposition = 'applied'
                elif event == 'candidate':
                    if pending:
                        with self.assertRaises(StateError):self.prepare(now)
                    else:
                        self.prepare(now);generation += 1;pending = True;disposition = 'applied'
                        evaluated_time = now
                        revisions[generation] = expected_revision(generation)
                elif event == 'restart':
                    self.reopen()
                    # Reconcile against active visibility, without a deployment.
                    self.pub.reconcile(None if active == 0 else LiveRevision(active, revisions[active]))
                elif event == 'bad_readback':
                    with self.assertRaises(StateError):self.pub.reconcile(LiveRevision(999, 'f' * 64))
                elif event == 'deploy_crash':
                    self.site.crash = True
                    with self.assertRaises(RuntimeError):self.pub.deploy_pending(self.pub.head, self.site)
                    self.site.crash = False
                elif event == 'readback':
                    if pending:
                        # The site may already contain the crash-visible candidate.
                        self.pub.deploy_pending(self.pub.head, self.site)
                        pending = False;active = generation;disposition = 'applied'
                    else:
                        self.pub.reconcile(self.site.readback())
                key = ('readback' if event in ('bad_readback', 'deploy_crash') else
                       'source' if event in ('source_moved', 'invalid_source') else event)
                seen[key].add(disposition)
                if disposition == 'observed_no_mutation':self.assertEqual(before, self.pub.head)
                self.assertEqual(generation, self.pub.ledger['generation'])
                self.assertEqual(active, 0 if self.pub.ledger['active'] is None else self.pub.ledger['active']['generation'])
                self.assertEqual(pending, self.pub.ledger['pending'] is not None)
                self.assertEqual(requests, len(self.pub.ledger['requests']))
                self.assertEqual(expected_schedule(), self.pub.ledger['accepted'])
                for field in ('active', 'pending'):
                    snapshot = self.pub.ledger[field]
                    if snapshot is not None:
                        self.assertEqual(revisions[snapshot['generation']], snapshot['artifact_revision'])
                trace.append([event, disposition, generation, active, requests])
            except Exception as error:
                self.fail(f'seed83115 index{index} events={events!r} trace={trace!r} error={error!r}')
        for event, dispositions in required.items():
            self.assertTrue(dispositions <= seen[event], (event, seen, trace))


if __name__ == '__main__':
    unittest.main()
