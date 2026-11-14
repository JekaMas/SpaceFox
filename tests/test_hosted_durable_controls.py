"""Current-format Git authority witnesses; external hosting is not exercised."""
from pathlib import Path
import subprocess
import sys
import tempfile
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


    def test_rescheduled_flag_and_age_survive_http_then_process_death(self):
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading
        from tools.spacefox.provider import normalize_launch
        from tests.test_current_motion_publisher import captured_starship, NOW
        row = captured_starship()
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (normalize_launch(row, NOW),), NOW,
                               selection_validated_utc=NOW)
        changed = dict(row, net='2026-11-13T23:00:00Z', window_start='2026-11-13T23:00:00Z',
                       last_updated='2026-11-13T06:40:00Z')
        changed_at = NOW + 1000
        token = self.pub.reserve(self.pub.head, changed_at, trigger='retry')
        self.pub.accept_source(self.pub.head, token, (normalize_launch(changed, changed_at),), changed_at,
                               selection_validated_utc=changed_at)
        self.assertTrue(self.pub.schedule.entries[0].rescheduled)
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                self.send_response_only(200)
                self.send_header('Content-Length', '2')
                self.end_headers()
                self.wfile.write(b'{}')
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        script = '''import os,sys\nfrom tools.spacefox.publisher import GitState,Publisher\nfrom tools.spacefox.provider import LL2Client\ns=GitState(sys.argv[1]);p=Publisher(s,sys.argv[2]);p.reconcile(None)\nLL2Client(origin=sys.argv[3],local_http=True).request(p,int(sys.argv[4]),trigger="retry")\nos._exit(9)\n'''
        try:
            child = subprocess.run([sys.executable, '-B', '-c', script, str(self.remote), self.code,
                                    f'http://127.0.0.1:{server.server_port}', str(NOW + 2000)],
                                   capture_output=True, text=True, timeout=30)
            self.assertEqual(9, child.returncode, child.stderr)
            self.assertEqual(1, len(calls))
            reopened = Publisher(self.store, self.code)
            reopened.reconcile(None)
            before = reopened.head
            self.assertEqual(3, len(reopened.ledger['requests']))
            self.assertEqual('reserved', reopened.ledger['requests'][-1]['outcome'])
            self.assertEqual(changed_at, reopened.ledger['selection_validated_utc'])
            self.assertEqual(changed_at, reopened.schedule.entries[0].record.source_validated_utc)
            self.assertTrue(reopened.schedule.entries[0].rescheduled)
            with self.assertRaises(StateError):
                reopened.reserve(before, NOW + 2001, trigger='retry')
            self.assertEqual(before, reopened.head)
            self.assertEqual(1, len(calls))
        finally:
            server.shutdown()
            thread.join()
            server.server_close()
