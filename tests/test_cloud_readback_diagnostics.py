"""Captured G10 authority + real bounded HTTP; remote CDN alone is substituted."""
import copy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest

from tools.spacefox.cloud import CloudError, Site, delivery_files, snapshot_files
from tools.spacefox.publisher import GitState, LiveRevision, Publisher

FIXTURE = Path(__file__).parent / 'fixtures/cloud-readback-diagnostics/g10-state.bundle'
ACCEPTED = '1df5c70012504024df1aaea549e30d7b7d8f3fd5'
RED_STATE = '9982b26e7fcdc55f228fa46d90b267e25dab38c0'
ANCHOR = '5dd986f4cb6fc1bf4df96a89675c53d5625da425'


class CloudReadbackDiagnosticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='spacefox-readback-')
        cls.remote = Path(cls.tmp.name) / 'authority.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(cls.remote)], check=True)
        cls.git('fetch', '-q', str(FIXTURE.resolve()),
                'refs/remotes/origin/feed-state:refs/heads/feed-state',
                'refs/tags/spacefox-state-bootstrap-v1:refs/tags/spacefox-state-bootstrap-v1')
        cls.store = GitState(str(cls.remote))
        cls.pub = Publisher(cls.store, 'b4e7837f39dc203678d8ea8a4081f462f9085bbb')
        cls.doc = cls.pub.ledger
        cls.cloud = json.loads(cls.store._blob(RED_STATE, 'cloud.json', 1048576))
        cls.files = delivery_files(cls.pub, cls.cloud['files'])
        cls.active, cls.snapshot = snapshot_files(cls.store, RED_STATE, 10)
        cls.refs = cls.git('show-ref')
        cls.tree = cls.git('ls-tree', '-r', RED_STATE)

    @classmethod
    def tearDownClass(cls):
        cls.store.close()
        cls.tmp.cleanup()

    @classmethod
    def git(cls, *args):
        return subprocess.check_output(['git', '--git-dir=' + str(cls.remote), *args])

    def setUp(self):
        self.live = dict(self.files)
        self.reads, self.writes = [], []
        self.counts, self.replacements, self.statuses = {}, {}, {}
        test = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                path = self.path.removeprefix('/site/')
                test.reads.append(path)
                test.counts[path] = test.counts.get(path, 0) + 1
                raw = test.replacements.get((path, test.counts[path]), test.live.get(path))
                status = test.statuses.get(path, 404 if raw is None else 200)
                raw = b'' if raw is None else raw
                self.send_response(status)
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_POST(self):
                test.writes.append(self.path)
                self.send_error(405)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.site = Site('http://127.0.0.1:' + str(self.server.server_port) + '/site', local_http=True)

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.assertEqual(self.refs, self.git('show-ref'))
        self.assertEqual(self.tree, self.git('ls-tree', '-r', RED_STATE))
        self.assertEqual(self.doc, self.pub.ledger)
        self.assertEqual((1794484952, 1794484947),
                         (self.pub.ledger['selection_validated_utc'], self.pub.ledger['last_poll_utc']))
        self.assertEqual([], self.writes)
        self.assertFalse(any('/2.3.0/' in p or '/repos/' in p for p in self.reads))

    def observe(self):
        return self.site.observe(self.pub, self.cloud['files'])

    def assert_diagnostic(self, action, *, path, kind, status, actual, phase='closure'):
        with self.assertRaises(CloudError) as caught:
            action()
        message = str(caught.exception)
        self.assertLess(len(message.encode()), 1024)
        self.assertIn('; readback=', message, 'exact-path failure requires bounded readback context')
        context = json.loads(message.split('; readback=', 1)[1])
        expected = self.files[path]
        self.assertEqual(dict(path=path, kind=kind, phase=phase, status=status,
                              expected={'bytes': len(expected), 'sha256': hashlib.sha256(expected).hexdigest()},
                              actual={'bytes': len(actual), 'sha256': hashlib.sha256(actual).hexdigest()}), context)
        self.assertNotIn('response-body-secret', message)
        self.assertNotIn(self.site.base, message)

    def test_exact_g10_readback_and_code_adoption_preserve_delivery(self):
        self.assertEqual(RED_STATE, self.pub.head)
        self.assertEqual((108, 361900, 106, 359792),
                         (len(self.files), sum(map(len, self.files.values())),
                          len(self.snapshot), sum(map(len, self.snapshot.values()))))
        before = self.store._ledger_at(ACCEPTED)
        after = copy.deepcopy(self.doc)
        self.assertEqual(['code_revision'], [key for key in before if before[key] != after[key]])
        self.assertEqual(self.active, snapshot_files(self.store, ACCEPTED, 10)[0])
        self.assertEqual(self.snapshot, snapshot_files(self.store, ACCEPTED, 10)[1])
        self.assertEqual(self.cloud, json.loads(self.store._blob(ACCEPTED, 'cloud.json', 1048576)))
        self.assertEqual(LiveRevision(10, '6e0048f1dd3861848b3e732f8a3ee4d885a4051b98404fb1f0b0fc038838da03'), self.observe())
        self.assertEqual(set(self.files), set(self.reads))
        self.assertEqual((2, 2, 110), (self.counts['feed.json'], self.counts['wire2/feed.json'], len(self.reads)))

    def test_missing_immutable_reports_path_status_and_bounded_digest(self):
        path = 'catalogs/2685b32616d1641f4e079a779d564cca1925ffb423e8d814238acc088f6eaaac.json'
        self.live.pop(path)
        self.assert_diagnostic(self.observe, path=path, kind='immutable-file', status=404, actual=b'')
        self.assertEqual(1, self.counts[path])

    def test_mixed_wire2_reports_mutable_root_without_body_or_retry(self):
        path = 'wire2/feed.json'
        self.live[path] = b'response-body-secret'
        self.assert_diagnostic(self.observe, path=path, kind='mutable-root', status=200, actual=self.live[path])
        self.assertEqual(1, self.counts[path])

    def test_wire2_after_closure_change_keeps_exact_two_root_guards(self):
        path = 'wire2/feed.json'
        self.replacements[(path, 2)] = b'{}'
        self.assert_diagnostic(self.observe, path=path, kind='mutable-root', status=200, actual=b'{}', phase='after-closure')
        self.assertEqual((1, 2), (self.counts['feed.json'], self.counts[path]))

    def test_feed_after_closure_change_keeps_exact_two_root_guards(self):
        path = 'feed.json'
        self.replacements[(path, 2)] = b'{}'
        self.assert_diagnostic(self.observe, path=path, kind='mutable-root', status=200, actual=b'{}', phase='after-closure')
        self.assertEqual((2, 2), (self.counts[path], self.counts['wire2/feed.json']))


if __name__ == '__main__':
    unittest.main()
