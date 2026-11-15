"""Current-format Git authority witnesses; external hosting is not exercised."""
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from tools.spacefox.publisher import GitState, Publisher, StateError, STATE_REF, ANCHOR_REF
from tests.test_current_motion_publisher import git


class DurableAuthorityWholeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='durable-authority-')
        self.root = Path(self.tmp.name)
        self.remote = self.root / 'remote.git'
        source = self.root / 'source'
        source.mkdir()
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        git(source, 'init', '-q')
        git(source, 'config', 'user.name', 'Local qualification')
        git(source, 'config', 'user.email', 'local@example.invalid')
        git(source, 'commit', '--allow-empty', '-qm', 'source')
        self.code = git(source, 'rev-parse', 'HEAD')
        git(source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.store = GitState(str(self.remote))
        self.anchor = self.store.bootstrap(self.code)
        self.pub = Publisher(self.store, self.code)
        self.pub.reconcile(None)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_anchor_missing_state_refuses_reset(self):
        self.assertEqual(self.anchor, git(self.remote, 'rev-parse', ANCHOR_REF))
        self.assertEqual(self.anchor, git(self.remote, 'rev-parse', STATE_REF))
        with self.assertRaises(StateError):
            self.store.bootstrap(self.code)
        git(self.remote, 'update-ref', '-d', STATE_REF, self.anchor)
        with self.assertRaises(StateError):
            Publisher(self.store, self.code)
        with self.assertRaises(StateError):
            self.store.bootstrap(self.code)
        self.assertEqual(self.anchor, git(self.remote, 'rev-parse', ANCHOR_REF))
        self.assertEqual({}, self.store._refs(STATE_REF))
        git(self.remote, 'update-ref', STATE_REF, self.anchor)
        self.assertEqual(self.anchor, Publisher(self.store, self.code).head)

    def test_two_process_reservation_cas(self):
        script = '''import sys\nfrom pathlib import Path\nfrom tools.spacefox.publisher import GitState,Publisher,Conflict\ns=GitState(sys.argv[1]);p=Publisher(s,sys.argv[2]);p.reconcile(None)\nPath(sys.argv[3]).write_text(p.head)\nsys.stdin.readline()\ntry:\n p.reserve(sys.argv[4],1000,trigger="manual");print("winner",flush=True)\nexcept Conflict:print("conflict",flush=True)\nfinally:s.close()\n'''
        workers = []
        try:
            for i in range(2):
                ready = self.root / f'ready{i}'
                proc = subprocess.Popen([sys.executable, '-B', '-c', script, str(self.remote),
                                         self.code, str(ready), self.anchor], stdin=subprocess.PIPE,
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                workers.append((proc, ready))
            deadline = time.monotonic() + 20
            while not all(ready.exists() for _, ready in workers):
                if time.monotonic() >= deadline:
                    self.fail('worker barrier timed out')
                time.sleep(.01)
            self.assertEqual([self.anchor, self.anchor], [r.read_text() for _, r in workers])
            for proc, _ in workers:
                proc.stdin.write('go\n')
                proc.stdin.flush()
            outputs = []
            for proc, _ in workers:
                out, err = proc.communicate(timeout=30)
                self.assertEqual(0, proc.returncode, err)
                outputs.append(out.strip())
            self.assertEqual(['conflict', 'winner'], sorted(outputs))
            reopened = Publisher(self.store, self.code)
            self.assertEqual(1, len(reopened.ledger['requests']))
            self.assertEqual('reserved', reopened.ledger['requests'][0]['outcome'])
            self.assertEqual(1000, reopened.ledger['requests'][0]['at_utc'])
            self.assertEqual(self.anchor, git(self.remote, 'rev-parse', ANCHOR_REF))
        finally:
            for proc, _ in workers:
                if proc.poll() is None:
                    proc.kill()
                    proc.communicate()

    def test_process_death_keeps_reservation_and_real_source_age(self):
        from tools.spacefox.provider import normalize_launch
        from tests.test_current_motion_publisher import captured_starship, NOW
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (normalize_launch(captured_starship(), NOW),), NOW,
                               selection_validated_utc=NOW)
        script = '''import os,sys\nfrom tools.spacefox.publisher import GitState,Publisher\ns=GitState(sys.argv[1]);p=Publisher(s,sys.argv[2]);p.reconcile(None)\np.reserve(p.head,int(sys.argv[3]),trigger="retry")\nos._exit(9)\n'''
        result = subprocess.run([sys.executable, '-B', '-c', script, str(self.remote), self.code,
                                 str(NOW + 1000)], capture_output=True, text=True)
        self.assertEqual(9, result.returncode, result.stderr)
        pub = Publisher(self.store, self.code)
        pub.reconcile(None)
        before = pub.head
        with self.assertRaises(StateError):
            pub.reserve(before, NOW + 1001, trigger='retry')
        self.assertEqual(before, pub.head)
        self.assertEqual(2, len(pub.ledger['requests']))
        self.assertEqual('reserved', pub.ledger['requests'][-1]['outcome'])
        self.assertEqual(NOW, pub.ledger['selection_validated_utc'])
        self.assertEqual(NOW, pub.schedule.entries[0].record.source_validated_utc)
        pub.reserve(pub.head, NOW + 1061, trigger='retry')
        self.assertEqual(3, len(pub.ledger['requests']))
        self.assertEqual(NOW, pub.ledger['selection_validated_utc'])

    def test_failure_clock_backoff_survives_restart_and_rejects_time_regression(self):
        from tools.spacefox.publisher import AllowanceUnavailable
        token = self.pub.reserve(self.pub.head, 1000, trigger='manual')
        self.pub.finish_request(self.pub.head, token, 1020, 'failed')
        reopened = Publisher(self.store, self.code)
        reopened.reconcile(None)
        self.assertEqual(1320, reopened.ledger['backoff_until_utc'])
        before = reopened.head
        with self.assertRaises(AllowanceUnavailable):
            reopened.reserve(before, 1319, trigger='manual')
        self.assertEqual(before, reopened.head)
        with self.assertRaises(StateError):
            reopened.reserve(before, 1019, trigger='manual')
        self.assertEqual(before, reopened.head)
        self.assertIsNotNone(reopened.reserve(before, 1320, trigger='manual'))
        self.assertEqual(2, len(reopened.ledger['requests']))

    def test_reservation_push_fault_before_and_after_acknowledgement(self):
        real_git = self.store._git
        def fail_before(*args, **kwargs):
            if args[0] == 'push':
                raise RuntimeError('before push')
            return real_git(*args, **kwargs)
        self.store._git = fail_before
        with self.assertRaisesRegex(RuntimeError, 'before push'):
            self.pub.reserve(self.pub.head, 1000, trigger='manual')
        self.store._git = real_git
        self.assertEqual(self.anchor, git(self.remote, 'rev-parse', STATE_REF))
        reopened = Publisher(self.store, self.code)
        reopened.reconcile(None)
        self.assertEqual([], reopened.ledger['requests'])
        def lose_ack(*args, **kwargs):
            result = real_git(*args, **kwargs)
            if args[0] == 'push':
                raise RuntimeError('ack lost')
            return result
        self.store._git = lose_ack
        with self.assertRaisesRegex(RuntimeError, 'ack lost'):
            reopened.reserve(reopened.head, 1000, trigger='manual')
        self.store._git = real_git
        recovered = Publisher(self.store, self.code)
        recovered.reconcile(None)
        self.assertNotEqual(self.anchor, recovered.head)
        self.assertEqual(1, len(recovered.ledger['requests']))
        self.assertEqual('reserved', recovered.ledger['requests'][0]['outcome'])
        before = recovered.head
        with self.assertRaises(StateError):
            recovered.reserve(before, 1001, trigger='retry')
        self.assertEqual(before, recovered.head)

    def test_corrupt_authority_reopen_refuses_without_rewriting_ref(self):
        git(self.remote, 'config', 'user.name', 'Local qualification')
        git(self.remote, 'config', 'user.email', 'local@example.invalid')
        import json
        original = json.loads(self.store._blob(self.anchor, 'ledger.json', 65536))
        original['schema_version'] = 999
        for raw in (b'{"schema_version":2,"schema_version":2}', b'{"x":NaN}',
                    '{"schema_version":2}'.encode('utf-16'), b'[]',
                    b'{' + b' ' * 65536 + b'}', json.dumps(original).encode()):
            with self.subTest(raw=raw[:20]):
                def input_git(args, data):
                    return subprocess.run(['git', '-C', str(self.remote), *args], input=data,
                                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                          check=True).stdout.decode().strip()
                blob = input_git(['hash-object', '-w', '--stdin'], raw)
                tree = input_git(['mktree'], f'100644 blob {blob}\tledger.json\n'.encode())
                bad = input_git(['commit-tree', tree, '-p', self.anchor], b'corrupt checkpoint\n')
                git(self.remote, 'update-ref', STATE_REF, bad, self.anchor)
                try:
                    with self.assertRaises(StateError):
                        Publisher(self.store, self.code)
                    self.assertEqual(bad, git(self.remote, 'rev-parse', STATE_REF))
                    self.assertEqual(self.anchor, git(self.remote, 'rev-parse', ANCHOR_REF))
                finally:
                    git(self.remote, 'update-ref', STATE_REF, self.anchor, bad)
        self.assertEqual(self.anchor, Publisher(self.store, self.code).head)

    def test_terminal_archive_exact_and_old_revision_refusal(self):
        from dataclasses import replace
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.schedule import LaunchStatus
        from tests.test_current_motion_publisher import captured_starship, NOW
        import gzip, json
        from tests.test_current_motion_publisher import FIXTURE, FIXTURE_SHA
        import hashlib
        raw = gzip.decompress(FIXTURE.read_bytes())
        self.assertEqual(FIXTURE_SHA, hashlib.sha256(raw).hexdigest())
        cancelled_row = next(r for r in json.loads(raw)['results']
                             if r['id'] == 'ef9850ad-1096-425b-9d27-f7bbd186e61a')
        record = replace(normalize_launch(captured_starship(), NOW), status=LaunchStatus.COMPLETED,
                         source_updated_utc=NOW, source_updated_iso=None, source_updated_subsecond=0)
        cancelled = replace(normalize_launch(cancelled_row, NOW), status=LaunchStatus.CANCELLED,
                            source_updated_utc=NOW, source_updated_iso=None, source_updated_subsecond=0)
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (record, cancelled), NOW, selection_validated_utc=NOW)
        originals = {e.record.launch_id: e for e in self.pub.schedule.entries}
        original = originals[record.launch_id]
        token = self.pub.reserve(self.pub.head, NOW + 86399, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (), NOW + 86399)
        self.assertEqual({record.launch_id, cancelled.launch_id},
                         {e.record.launch_id for e in self.pub.schedule.entries})
        self.assertIsNone(self.store.archived(record.launch_id, self.pub.head))
        before_retirement = {e.record.launch_id: e for e in self.pub.schedule.entries}
        token = self.pub.reserve(self.pub.head, NOW + 86400, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (), NOW + 86400)
        reopened = Publisher(self.store, self.code)
        reopened.reconcile(None)
        self.assertEqual((), reopened.schedule.entries)
        archived = self.store.archived(record.launch_id, reopened.head)
        self.assertEqual(before_retirement[record.launch_id], archived)
        self.assertEqual(original.record, archived.record)
        self.assertEqual(NOW, archived.record.source_validated_utc)
        measurement = self.store.measure()
        self.assertEqual(before_retirement[cancelled.launch_id], self.store.archived(cancelled.launch_id, reopened.head))
        self.assertEqual(2, measurement['archive_records'])
        self.assertGreater(measurement['archive_blob_bytes'], 0)
        self.assertLessEqual(measurement['ledger_bytes'], 65536)
        self.assertGreater(measurement['history_object_bytes'], measurement['ledger_bytes'])
        token = reopened.reserve(reopened.head, NOW + 86401, trigger='manual')
        before = reopened.head
        old = replace(record, source_updated_utc=NOW - 1, source_validated_utc=NOW + 86401)
        with self.assertRaises(StateError):
            reopened.accept_source(before, token, (old,), NOW + 86401)
        self.assertEqual(before, reopened.head)
        self.assertEqual(original.record, self.store.archived(record.launch_id, before).record)
        self.assertEqual(NOW, reopened.ledger['selection_validated_utc'])
        unseen_row = next(r for r in json.loads(raw)['results']
                          if r['id'] == 'bff2fc91-eddd-4dfc-af26-ac0674cfab4d')
        unseen = normalize_launch(unseen_row, NOW + 86401)
        self.assertLess(unseen.source_updated_utc, NOW + 86400)
        reopened.accept_source(before, token, (unseen,), NOW + 86401)
        self.assertEqual({unseen.launch_id}, {e.record.launch_id for e in reopened.schedule.entries})
        self.assertEqual(unseen.source_updated_utc, reopened.schedule.entries[0].record.source_updated_utc)
        self.assertEqual(NOW, reopened.ledger['selection_validated_utc'])

    def test_schedule_catalog_version_share_rolling_quota(self):
        from tools.spacefox.publisher import AllowanceUnavailable
        for i in range(15):
            purpose = ('schedule', 'catalog', 'version')[i % 3]
            token = self.pub.reserve(self.pub.head, 1000, purpose=purpose, trigger='extra')
            self.pub.finish_request(self.pub.head, token, 1000, 'success')
        reopened = Publisher(self.store, self.code)
        reopened.reconcile(None)
        self.assertEqual(['schedule', 'catalog', 'version'] * 5,
                         [entry['purpose'] for entry in reopened.ledger['requests']])
        before = reopened.head
        for purpose in ('schedule', 'catalog', 'version'):
            with self.subTest(purpose=purpose), self.assertRaises(AllowanceUnavailable):
                reopened.reserve(before, 1001, purpose=purpose, trigger='manual')
            self.assertEqual(before, reopened.head)
        reopened.reserve(before, 4600, purpose='version', trigger='manual')
        self.assertEqual(1, len(reopened.ledger['requests']))
        self.assertEqual('version', reopened.ledger['requests'][0]['purpose'])

    def test_source_advances_during_reservation_consumes_slot_without_permission(self):
        source = self.root / 'source'
        real_git = self.store._git
        advanced = False
        def source_advances(*args, **kwargs):
            nonlocal advanced
            result = real_git(*args, **kwargs)
            if args[0] == 'push' and not advanced:
                advanced = True
                git(source, 'commit', '--allow-empty', '-qm', 'new source')
                git(source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
            return result
        self.store._git = source_advances
        with self.assertRaisesRegex(StateError, 'source advanced'):
            self.pub.reserve(self.pub.head, 1000, trigger='manual')
        self.store._git = real_git
        self.assertTrue(advanced)
        newer_code = git(source, 'rev-parse', 'HEAD')
        reopened = Publisher(self.store, newer_code)
        self.assertEqual(1, len(reopened.ledger['requests']))
        self.assertEqual('reserved', reopened.ledger['requests'][0]['outcome'])
        before = reopened.head
        with self.assertRaises(StateError):
            self.pub.reserve(before, 1061, trigger='manual')
        self.assertEqual(before, git(self.remote, 'rev-parse', STATE_REF))
        reopened.adopt_code(before)
        reopened.reconcile(None)
        self.assertEqual(1, len(reopened.ledger['requests']))
        self.assertEqual(newer_code, reopened.ledger['code_revision'])

    def test_unresolved_omission_keeps_identity_age_and_latches(self):
        from dataclasses import replace
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.schedule import LaunchStatus
        from tests.test_current_motion_publisher import captured_starship, NOW
        record = replace(normalize_launch(captured_starship(), NOW), status=LaunchStatus.UNKNOWN)
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (record,), NOW, selection_validated_utc=NOW)
        token = self.pub.reserve(self.pub.head, NOW + 86400, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (), NOW + 86400)
        reopened = Publisher(self.store, self.code)
        self.assertEqual(1, len(reopened.schedule.entries))
        retained = reopened.schedule.entries[0]
        self.assertEqual(record.launch_id, retained.record.launch_id)
        self.assertEqual(NOW, retained.record.source_validated_utc)
        self.assertEqual(LaunchStatus.UNKNOWN, retained.record.status)
        self.assertFalse(retained.rescheduled)
        self.assertTrue(retained.stale)
        self.assertIsNone(self.store.archived(record.launch_id, reopened.head))
        self.assertEqual(NOW, reopened.ledger['selection_validated_utc'])

    def test_regressing_git_authority_refuses_reopen_without_rewriting(self):
        from copy import deepcopy
        token = self.pub.reserve(self.pub.head, 1000, trigger='manual')
        self.pub.finish_request(self.pub.head, token, 1000, 'success')
        good = self.pub.head
        invalid = deepcopy(self.pub.ledger)
        invalid['requests'] = []  # Structurally valid alone, but drops an unexpired reservation.
        bad = self.store._commit(invalid, good, {})
        self.store._git('push', f'--force-with-lease={STATE_REF}:{good}', str(self.remote), f'{bad}:{STATE_REF}')
        try:
            with self.assertRaises(StateError):
                Publisher(self.store, self.code)
            self.assertEqual(bad, git(self.remote, 'rev-parse', STATE_REF))
        finally:
            self.store._git('push', f'--force-with-lease={STATE_REF}:{bad}', str(self.remote), f'{good}:{STATE_REF}')
        reopened = Publisher(self.store, self.code)
        self.assertEqual(good, reopened.head)
        self.assertEqual(1000, reopened.ledger['last_event_utc'])
        self.assertEqual(1, len(reopened.ledger['requests']))

    def test_actual_429_samples_completion_once_and_persists_backoff(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading
        from tools.spacefox.provider import LL2Client, Throttled
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                self.send_response_only(429)
                self.send_header('Retry-After', '60')
                self.end_headers()
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            samples = []
            def clock():
                samples.append(1002 + len(samples))
                return samples[-1]
            client = LL2Client(origin=f'http://127.0.0.1:{server.server_port}', local_http=True)
            with self.assertRaises(Throttled):
                client.request(self.pub, 1000, trigger='manual', clock=clock)
            reopened = Publisher(self.store, self.code)
            self.assertEqual([1002], samples)
            self.assertEqual(1, len(calls))
            self.assertEqual(1062, reopened.ledger['backoff_until_utc'])
            self.assertEqual('throttled', reopened.ledger['requests'][0]['outcome'])
            self.assertEqual(1000, reopened.ledger['requests'][0]['at_utc'])
            reopened.reconcile(None)
            before = reopened.head
            with self.assertRaises(StateError):
                client.request(reopened, 1061, trigger='manual', clock=clock)
            self.assertEqual(before, reopened.head)
            self.assertEqual([1002], samples)
            self.assertEqual(1, len(calls))
        finally:
            server.shutdown()
            thread.join()
            server.server_close()

    def test_required_authority_bounds_reject_without_eviction_or_refund(self):
        from dataclasses import replace
        from uuid import UUID
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.schedule import LaunchStatus
        from tests.test_current_motion_publisher import captured_starship, NOW
        base = replace(normalize_launch(captured_starship(), NOW), status=LaunchStatus.UNKNOWN)
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (base,), NOW, selection_validated_utc=NOW)
        previous = self.pub.schedule
        def technical_record(index, size=0):
            return replace(base, launch_id=replace(base.launch_id, value=str(UUID(int=index + 1))),
                           mission_purpose='x' * size if size else base.mission_purpose,
                           source_validated_utc=NOW + 3600)
        cases = [
            ('individual', (technical_record(0, 66000),)),
            ('aggregate', tuple(technical_record(i, 60000) for i in range(20))),
            ('unresolved', tuple(technical_record(i) for i in range(129))),
        ]
        for label, incoming in cases:
            with self.subTest(bound=label):
                token = self.pub.reserve(self.pub.head, NOW + 3600, trigger='manual')
                reserved = self.pub.head
                expected = {'individual': 'archive budget', 'aggregate': 'invalid bounded integer',
                            'unresolved': 'bounded schedule entries required'}[label]
                with self.assertRaisesRegex(StateError, expected):
                    self.pub.accept_source(reserved, token, incoming, NOW + 3600)
                self.assertEqual(reserved, self.pub.head)
                self.assertEqual(previous, self.pub.schedule)
                self.assertEqual('reserved', self.pub.ledger['requests'][-1]['outcome'])
                self.assertEqual(NOW, self.pub.ledger['selection_validated_utc'])
                self.pub.finish_request(self.pub.head, token, NOW + 3600, 'success')
        token = self.pub.reserve(self.pub.head, NOW + 3600, trigger='manual')
        self.pub.accept_source(self.pub.head, token, tuple(technical_record(i) for i in range(127)), NOW + 3600)
        self.assertEqual(128, len(self.pub.schedule.entries))
        self.assertIn(base.launch_id, {entry.record.launch_id for entry in self.pub.schedule.entries})
        self.assertEqual(NOW, self.pub.ledger['selection_validated_utc'])
        token = self.pub.reserve(self.pub.head, NOW + 3600, trigger='manual')
        reserved = self.pub.head
        with self.assertRaisesRegex(StateError, 'bounded schedule entries required'):
            self.pub.accept_source(reserved, token, (technical_record(127),), NOW + 3600)
        self.assertEqual(reserved, self.pub.head)
        self.assertEqual(128, len(self.pub.schedule.entries))
        self.assertEqual('reserved', self.pub.ledger['requests'][-1]['outcome'])

    def test_actual_http_then_process_death_retains_consumed_permission(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading
        from tools.spacefox.provider import normalize_launch
        from tests.test_current_motion_publisher import captured_starship, NOW
        token=self.pub.reserve(self.pub.head,NOW,trigger='manual')
        self.pub.accept_source(self.pub.head,token,(normalize_launch(captured_starship(),NOW),),NOW,
                               selection_validated_utc=NOW)
        calls=[]
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                self.send_response_only(200)
                self.send_header('Content-Length','2')
                self.end_headers()
                self.wfile.write(b'{}')
            def log_message(self,*args): pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        script='''import os,sys\nfrom tools.spacefox.publisher import GitState,Publisher\nfrom tools.spacefox.provider import LL2Client\ns=GitState(sys.argv[1]);p=Publisher(s,sys.argv[2]);p.reconcile(None)\nc=LL2Client(origin=sys.argv[3],local_http=True);c.request(p,int(sys.argv[4]),trigger="retry")\nos._exit(9)\n'''
        try:
            child=subprocess.run([sys.executable,'-B','-c',script,str(self.remote),self.code,
                                  f'http://127.0.0.1:{server.server_port}',str(NOW+1000)],
                                 capture_output=True,text=True,timeout=30)
            self.assertEqual(9,child.returncode,child.stderr)
            self.assertEqual(1,len(calls))
            reopened=Publisher(self.store,self.code);reopened.reconcile(None)
            before=reopened.head
            self.assertEqual(2,len(reopened.ledger['requests']))
            self.assertEqual('reserved',reopened.ledger['requests'][-1]['outcome'])
            self.assertEqual(NOW,reopened.ledger['selection_validated_utc'])
            self.assertEqual(NOW,reopened.schedule.entries[0].record.source_validated_utc)
            with self.assertRaises(StateError):
                reopened.reserve(before,NOW+1001,trigger='retry')
            self.assertEqual(before,reopened.head)
            self.assertEqual(1,len(calls))
        finally:
            server.shutdown();thread.join();server.server_close()
