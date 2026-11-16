"""Independent B regressions: full observation deadline and workflow routing."""
import re
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.spacefox import cloud


class PeerBTest(unittest.TestCase):
    def test_deadline_includes_both_root_requests(self):
        for slow_root in (1, 2):
            requests = []
            children = []
            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *args): pass
                def do_GET(self):
                    requests.append(self.path)
                    if self.path == '/feed.json' and requests.count('/feed.json') == slow_root:
                        time.sleep(1.2)
                    raw = b'root' if self.path == '/feed.json' else b'x'
                    try:
                        self.send_response(200); self.send_header('Content-Length', str(len(raw))); self.end_headers(); self.wfile.write(raw)
                    except (BrokenPipeError, ConnectionResetError): pass
                def do_POST(self): requests.append('POST'); self.send_error(405)
            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            site = cloud.Site(f'http://127.0.0.1:{server.server_port}', local_http=True)
            files = {'feed.json': b'root', 'one': b'x'}
            pub = SimpleNamespace(ledger={'active': {'generation': 1, 'artifact_revision': 'a'*64}, 'pending': None}, store=None, head=None)
            real_popen = cloud.subprocess.Popen
            def capture(*args, **kwargs):
                child = real_popen(*args, **kwargs); children.append(child); return child
            try:
                with patch.object(cloud, 'READBACK_DEADLINE_SECONDS', .5), patch.object(cloud, 'snapshot_files', return_value=(None, files)), patch.object(cloud.subprocess, 'Popen', side_effect=capture):
                    start = time.monotonic()
                    with self.assertRaises(cloud.CloudError): site.observe(pub)
                    self.assertLess(time.monotonic() - start, 1.0)
                self.assertTrue(children); self.assertTrue(all(child.poll() is not None for child in children))
                self.assertNotIn('POST', requests)
            finally:
                server.shutdown(); server.server_close(); thread.join()

    def test_deadline_cancels_queued_requests_and_reaps_workers(self):
        requests = []
        children = []
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                requests.append(self.path)
                raw = b'root' if self.path == '/feed.json' else b'xy'
                try:
                    self.send_response(200); self.send_header('Content-Length', str(len(raw))); self.end_headers()
                    self.wfile.write(raw[:1]); self.wfile.flush()
                    if self.path != '/feed.json': time.sleep(1.5)
                    self.wfile.write(raw[1:])
                except (BrokenPipeError, ConnectionResetError): pass
            def do_POST(self): requests.append('POST'); self.send_error(405)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        site = cloud.Site(f'http://127.0.0.1:{server.server_port}', local_http=True)
        files = {'feed.json': b'root', **{f'f{i}': b'xy' for i in range(12)}}
        pub = SimpleNamespace(ledger={'active': {'generation': 1, 'artifact_revision': 'a'*64}, 'pending': None}, store=None, head=None)
        real_popen = cloud.subprocess.Popen
        def capture(*args, **kwargs):
            child = real_popen(*args, **kwargs); children.append(child); return child
        try:
            with patch.object(cloud, 'READBACK_DEADLINE_SECONDS', .5), patch.object(cloud, 'snapshot_files', return_value=(None, files)), patch.object(cloud.subprocess, 'Popen', side_effect=capture):
                start = time.monotonic()
                with self.assertRaises(cloud.CloudError): site.observe(pub)
                self.assertLess(time.monotonic() - start, 1.0)
            self.assertTrue(children); self.assertTrue(all(child.poll() is not None for child in children))
            self.assertGreater(len(requests), 1); self.assertLessEqual(len(requests), 5)
            self.assertNotIn('POST', requests)
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_full_payload_budget_includes_duplicate_root(self):
        root = b'r' * 8192
        files = {'feed.json': root, 'data': b'x' * (1048576 - len(root))}
        observed = []
        class Transport:
            def request(self, method, url, *, limit):
                name = url.rsplit('/', 1)[-1]
                raw = files[name]
                observed.append((method, name, limit, len(raw)))
                return 200, raw
        pub = SimpleNamespace(ledger={'active': {'generation': 1, 'artifact_revision': 'a'*64}, 'pending': None}, store=None, head=None)
        site = cloud.Site('http://127.0.0.1:1', local_http=True, http=Transport())
        with patch.object(cloud, 'snapshot_files', return_value=(None, files)):
            site.observe(pub)
        self.assertEqual(sorted((name, limit) for _, name, limit, _ in observed),
                         [('data', len(files['data'])), ('feed.json', 8192), ('feed.json', 8192)])
        self.assertEqual(sum(row[3] for row in observed), 1048576 + len(root))
        self.assertTrue(all(row[0] == 'GET' for row in observed))

    def test_failed_probe_routes_to_full_prepare(self):
        workflow = Path('.github/workflows/update-feed.yml').read_text()
        probe = workflow.split('      - name: Observe whether all work is excluded\n', 1)[1].split('      - name:', 1)[0]
        self.assertRegex(probe, r'(?m)^        continue-on-error: true$')
        self.assertIn("steps.probe.outcome == 'success'", workflow)
        self.assertGreaterEqual(len(re.findall(r"steps\.probe\.outcome != 'success'.*steps\.probe\.outputs\.no_work != 'true'", workflow)), 3)
