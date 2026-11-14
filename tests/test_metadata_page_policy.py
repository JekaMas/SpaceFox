"""Current captured metadata through actual loopback HTTP and Git authority."""
from copy import deepcopy
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from tests import test_current_metadata_publisher as fixture

NOW = fixture.NOW
from tools.spacefox import catalog_refresh as refresh_module
from tools.spacefox.catalog_refresh import CatalogRefresh, RefreshError
from tools.spacefox.publisher import Publisher
from tools.spacefox.provider import Response


class MetadataPagePolicyTest(unittest.TestCase):
    def test_captured_page_rejects_count_drift_and_unsafe_or_truncated_next(self):
        candidate, files = fixture.captured()
        pages = [p for p in candidate['coverage']['pages'] if p['collection'] == 'countries']
        raw = files['objects/' + pages[1]['body']['sha256'] + '.json']
        original = json.loads(raw)
        helper = fixture.CurrentMetadataPublisherTest()
        with helper.authority() as (pub, store, code):
            collector = CatalogRefresh(pub)
            head = pub.head
            # Captured page 2 starts at offset 20 and has a total of 103.
            self.assertEqual((103, 20), (original['count'], len(original['results'])))
            self.assertEqual(103, collector._page('countries', raw, 20, 103)[0])
            for defect in ('count', 'origin', 'nonadvancing', 'truncated'):
                doc = deepcopy(original)
                if defect == 'count': doc['count'] = 104
                elif defect == 'origin': doc['next'] = 'https://example.invalid/2.3.0/config/countries/?format=json&limit=20&offset=40'
                elif defect == 'nonadvancing': doc['next'] = 'https://ll.thespacedevs.com/2.3.0/config/countries/?format=json&limit=20&offset=20'
                else: doc['next'] = None
                with self.subTest(defect=defect), self.assertRaises(RefreshError):
                    collector._page('countries', json.dumps(doc).encode(), 20, 103)
                self.assertEqual(head, store.load()[0])

    def test_omissions_keep_original_record_dates_and_facts(self):
        candidate, files = fixture.captured()
        selected = {'countries': {1, 2}, 'organizations': {121},
                    'models': {133, 522}, 'sites': {235}}
        rows = {}
        for kind, ids in selected.items():
            rows[kind] = [r for page in candidate['coverage']['pages'] if page['collection'] == kind
                          for r in json.loads(files['objects/' + page['body']['sha256'] + '.json'])['results']
                          if r['id'] in ids]
            self.assertEqual(ids, {r['id'] for r in rows[kind]})
        class CapturedSubset:
            def __init__(self): self.now = NOW; self.omit = False; self.calls = []
            def get(self, url, etag):
                self.calls.append((url, etag))
                paths = {'/2.3.0/config/countries/': 'countries', '/2.3.0/agencies/': 'organizations',
                         '/2.3.0/launcher_configurations/': 'models', '/2.3.0/pads/': 'sites'}
                kind = paths[urlsplit(url).path]
                current = [r for r in rows[kind] if not self.omit or
                           (kind, r['id']) not in {('countries', 1), ('models', 133)}]
                body = json.dumps(dict(count=len(current), next=None, previous=None, results=current)).encode()
                return Response(200, {'date': formatdate(self.now, usegmt=True), 'content-type': 'application/json'}, body)
        helper = fixture.CurrentMetadataPublisherTest()
        with helper.authority() as (pub, store, code):
            helper.primary(pub, NOW, accept=True)
            transport = CapturedSubset()
            for step in range(4):
                transport.now = NOW + step + 1
                result = CatalogRefresh(pub, transport=transport).run(transport.now)
            self.assertEqual('complete', result.status)
            first = CatalogRefresh(pub).current()
            country = next(r for r in first['reference']['countries'] if r['sourceId'] == 1)
            model = next(r for r in first['reference']['models'] if r['sourceId'] == 133)
            preserved = deepcopy(helper.preserved(pub))
            pub = Publisher(store, code); pub.reconcile(None)
            helper.primary(pub, NOW + 3600)
            transport.omit = True
            for step in range(3):
                transport.now = NOW + 3601 + step
                self.assertEqual('partial', CatalogRefresh(pub, transport=transport).run(transport.now, restart=(step == 0)).status)
            transport.now = NOW + 3604
            collector = CatalogRefresh(pub, transport=transport)
            build = collector._candidate
            def fail_final_save(*args):
                value = build(*args)
                refresh_module.MAX_CATALOG_OBJECTS = 1
                return value
            # Lower only the final candidate's save capacity, after the fourth
            # page itself has durably checkpointed. This is a technical fault.
            with patch.object(refresh_module, 'MAX_CATALOG_OBJECTS', refresh_module.MAX_CATALOG_OBJECTS):
                with patch.object(collector, '_candidate', side_effect=fail_final_save):
                    with self.assertRaisesRegex(RefreshError, 'catalog corpus exceeds'):
                        collector.run(transport.now)
            self.assertEqual({}, collector.objects)
            durable = CatalogRefresh(Publisher(store, code))
            self.assertEqual(first, collector.current())
            self.assertEqual(first, durable.current())
            self.assertEqual(durable.journal, collector.journal)
            self.assertEqual(4, len(durable.journal['staging']['pages']))
            calls = len(transport.calls)
            self.assertEqual('complete', collector.run(transport.now).status)
            self.assertEqual(calls, len(transport.calls))
            second = CatalogRefresh(Publisher(store, code)).current()
            self.assertEqual([1], second['missingComparedToPrevious']['countries'])
            self.assertEqual([133], second['missingComparedToPrevious']['models'])
            self.assertEqual([{'fact': country, 'lastObservedUtc': NOW + 1}], second['retainedMissing']['countries'])
            self.assertEqual([{'fact': model, 'lastObservedUtc': NOW + 3}], second['retainedMissing']['models'])
            self.assertEqual(NOW + 3604, second['source']['completedUtc'])
            self.assertEqual(preserved, helper.preserved(pub))
            self.assertEqual(8, len(transport.calls))

    def test_url_scoped_304_reuses_exact_bodies_and_source_dates(self):
        candidate, files = fixture.captured()
        ids = {'countries': 2, 'organizations': 121, 'models': 522, 'sites': 235}
        rows = {}
        for kind, identity in ids.items():
            found = [r for page in candidate['coverage']['pages'] if page['collection'] == kind
                     for r in json.loads(files['objects/' + page['body']['sha256'] + '.json'])['results']
                     if r['id'] == identity]
            self.assertEqual(1, len(found)); rows[kind] = found
        paths = ['/2.3.0/config/countries/?format=json&limit=20',
                 '/2.3.0/agencies/?format=json&limit=20&mode=normal',
                 '/2.3.0/launcher_configurations/?format=json&limit=100&mode=detailed',
                 '/2.3.0/pads/?format=json&limit=100&mode=detailed&ordering=id']
        kinds = ['countries', 'organizations', 'models', 'sites']
        tags = ['"capture-' + str(i) + '"' for i in range(4)]
        state = {'now': NOW + 5, 'reuse': False, 'calls': []}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                index = paths.index(self.path); etag = self.headers.get('If-None-Match')
                state['calls'].append((self.path, etag))
                body = raw[kinds[index]]
                valid = etag == tags[index] if state['reuse'] else etag is None
                self.send_response_only((304 if state['reuse'] else 200) if valid else 412)
                self.send_header('Date', formatdate(state['now'], usegmt=True))
                self.send_header('Age', '5'); self.send_header('ETag', tags[index])
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(0 if state['reuse'] else len(body)))
                self.end_headers()
                if not state['reuse']: self.wfile.write(body)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        origin = 'http://127.0.0.1:' + str(server.server_port)
        raw = {k: json.dumps(dict(count=1, next=None, previous=None, results=rows[k])).replace(
               'https://ll.thespacedevs.com', origin).encode() for k in kinds}
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            helper = fixture.CurrentMetadataPublisherTest()
            with helper.authority() as (pub, store, code):
                helper.primary(pub, NOW, accept=True)
                preserved = deepcopy(helper.preserved(pub)); opts = dict(origin=origin, local_http=True)
                self.assertEqual('complete', CatalogRefresh(pub, **opts).run(NOW + 5, max_requests=4).status)
                first = CatalogRefresh(pub, **opts).current()
                self.assertEqual([hashlib.sha256(raw[k]).hexdigest() for k in kinds],
                                 [p['body']['sha256'] for p in first['coverage']['pages']])
                self.assertEqual([NOW] * 4, [p['validatedUtc'] for p in first['coverage']['pages']])
                pub = Publisher(store, code); pub.reconcile(None); helper.primary(pub, NOW + 3600)
                state['reuse'] = True; state['now'] = NOW + 3605
                self.assertEqual('complete', CatalogRefresh(pub, **opts).run(NOW + 3605, max_requests=4, restart=True).status)
                second = CatalogRefresh(Publisher(store, code), **opts).current()
                self.assertEqual([304] * 4, [p['status'] for p in second['coverage']['pages']])
                self.assertEqual([NOW + 3600] * 4, [p['validatedUtc'] for p in second['coverage']['pages']])
                self.assertEqual([p['body'] for p in first['coverage']['pages']], [p['body'] for p in second['coverage']['pages']])
                self.assertEqual(list(zip(paths, [None] * 4)) + list(zip(paths, tags)), state['calls'])
                self.assertEqual(preserved, helper.preserved(pub))
        finally:
            server.shutdown(); thread.join(); server.server_close()

    def test_cli_duplicate_refusal_and_retry(self):
        candidate, files = fixture.captured()
        pages = [p for p in candidate['coverage']['pages'] if p['collection'] == 'countries']
        state = {'now': NOW, 'bad': False, 'calls': []}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                state['calls'].append(self.path)
                page = next(p for p in pages if urlsplit(p['url']).path + '?' + urlsplit(p['url']).query == self.path)
                doc = json.loads(files['objects/' + page['body']['sha256'] + '.json'])
                if state['bad']:
                    first = json.loads(files['objects/' + pages[0]['body']['sha256'] + '.json'])
                    doc['results'][0] = first['results'][0]
                raw = json.dumps(doc).replace('https://ll.thespacedevs.com', origin).encode()
                self.send_response_only(200)
                self.send_header('Date', formatdate(state['now'], usegmt=True))
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers(); self.wfile.write(raw)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        origin = 'http://127.0.0.1:' + str(server.server_port)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            with tempfile.TemporaryDirectory(prefix='spacefox-metadata-cli-') as folder:
                root = Path(__file__).resolve().parents[1]; remote = Path(folder) / 'remote.git'
                code = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
                subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
                subprocess.run(['git', '-C', str(remote), 'fetch', '-q', str(root), code + ':refs/heads/main'], check=True)
                from tools.spacefox.publisher import GitState
                store = GitState(str(remote))
                try:
                    store.bootstrap(code); pub = Publisher(store, code); pub.reconcile(None)
                    helper = fixture.CurrentMetadataPublisherTest(); helper.primary(pub, NOW, accept=True)
                    preserved = deepcopy(helper.preserved(pub))
                    live = Path(folder) / 'live.json'; live.write_text('null')
                    def invoke(head, now):
                        return subprocess.run([sys.executable, '-B', str(root / 'tools/refresh_catalog.py'), 'collect',
                            '--remote', str(remote), '--origin', origin, '--local-http', '--now', str(now),
                            '--expected-head', head, '--live-observation', str(live)], capture_output=True, text=True)
                    stale_head = pub.head
                    result = invoke(stale_head, NOW)
                    self.assertEqual(0, result.returncode, result.stderr)
                    actual_head = store.load()[0]
                    result = invoke(stale_head, NOW + 1)
                    self.assertEqual(2, result.returncode, result.stderr)
                    self.assertEqual(actual_head, store.load()[0])
                    self.assertEqual(1, len(state['calls']))
                    state['bad'] = True
                    result = invoke(store.load()[0], NOW + 1)
                    self.assertEqual(2, result.returncode, result.stderr)
                    self.assertIn('duplicate source identity', result.stderr)
                    pub = Publisher(store, code); pub.reconcile(None)
                    collector = CatalogRefresh(pub, origin=origin, local_http=True)
                    self.assertEqual([], collector.journal['staging']['pages'])
                    self.assertEqual('failed', pub.ledger['requests'][-1]['outcome'])
                    self.assertEqual(preserved, helper.preserved(pub))
                    state['bad'] = False; state['now'] = NOW + 301
                    result = invoke(pub.head, state['now'])
                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual('partial', json.loads(result.stdout)['status'])
                    self.assertEqual(['/2.3.0/config/countries/?format=json&limit=20',
                        '/2.3.0/config/countries/?format=json&limit=20&offset=20',
                        '/2.3.0/config/countries/?format=json&limit=20'], state['calls'])
                    pub = Publisher(store, code)
                    self.assertEqual(NOW + 301, CatalogRefresh(pub, origin=origin, local_http=True).journal['staging']['pages'][0]['validatedUtc'])
                    self.assertEqual(preserved, helper.preserved(pub))
                finally: store.close()
        finally:
            server.shutdown(); thread.join(); server.server_close()

    def test_duplicate_discards_only_current_collection_and_preserves_epochs(self):
        expected, files = fixture.captured()
        pages = expected['coverage']['pages']
        calls = []
        state = {'now': NOW, 'bad': False}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                calls.append(self.path)
                page = next(p for p in pages if urlsplit(p['url']).path + '?' + urlsplit(p['url']).query == self.path)
                raw = files['objects/' + page['body']['sha256'] + '.json']
                doc = json.loads(raw)
                if state['bad'] and self.path.endswith('offset=20') and self.path.startswith('/2.3.0/agencies/'):
                    first = next(p for p in pages if p['collection'] == 'organizations')
                    firstdoc = json.loads(files['objects/' + first['body']['sha256'] + '.json'])
                    doc['results'][0] = firstdoc['results'][0]
                raw = json.dumps(doc, separators=(',', ':')).replace('https://ll.thespacedevs.com', origin).encode()
                self.send_response_only(200)
                self.send_header('Date', formatdate(state['now'], usegmt=True))
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers(); self.wfile.write(raw)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        origin = 'http://127.0.0.1:' + str(server.server_port)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            helper = fixture.CurrentMetadataPublisherTest()
            with helper.authority() as (pub, store, code):
                helper.primary(pub, NOW, accept=True)
                preserved = deepcopy(helper.preserved(pub))
                opts = dict(origin=origin, local_http=True)
                # Six country pages use the available catalog headroom.
                for _ in range(6):
                    self.assertEqual('partial', CatalogRefresh(pub, **opts).run(NOW).status)
                pub = Publisher(store, code); pub.reconcile(None)
                state['now'] = NOW + 3600; helper.primary(pub, state['now'])
                collector = CatalogRefresh(pub, **opts)
                self.assertEqual('partial', collector.run(state['now']).status)
                prior = deepcopy(collector.journal['staging']['pages'])
                self.assertEqual(['countries'] * 6 + ['organizations'], [p['collection'] for p in prior])
                self.assertEqual([NOW] * 6, [p['validatedUtc'] for p in prior[:6]])
                state['bad'] = True
                with self.assertRaisesRegex(RefreshError, 'duplicate source identity'):
                    collector.run(state['now'] + 1)
                reopened = CatalogRefresh(Publisher(store, code), **opts)
                self.assertEqual(prior[:6], reopened.journal['staging']['pages'])
                self.assertFalse(any('/agencies/' in u for u in reopened.journal['cache']))
                ledger = store.load()[1]
                self.assertEqual('failed', ledger['requests'][-1]['outcome'])
                self.assertEqual(3, len(ledger['requests']))
                self.assertEqual(['schedule', 'catalog', 'catalog'],
                                 [r['purpose'] for r in ledger['requests']])
                self.assertEqual(8, len(calls))
                self.assertEqual(preserved, helper.preserved(pub))
                self.assertEqual('/2.3.0/agencies/?format=json&limit=20&mode=normal&offset=20', calls[-1])
                state['bad'] = False; state['now'] = NOW + 3901
                pub = Publisher(store, code); pub.reconcile(None)
                self.assertEqual('partial', CatalogRefresh(pub, **opts).run(state['now']).status)
                self.assertEqual('/2.3.0/agencies/?format=json&limit=20&mode=normal', calls[-1])
                stage = CatalogRefresh(Publisher(store, code), **opts).journal['staging']['pages']
                self.assertEqual(prior[:6], stage[:6])
                self.assertEqual(NOW + 3901, stage[-1]['validatedUtc'])
                self.assertEqual(preserved, helper.preserved(pub))
                # The same overlap a second time must not poison the durable
                # prefix or make the next traversal repeat offset 20 forever.
                state['bad'] = True
                with self.assertRaisesRegex(RefreshError, 'duplicate source identity'):
                    CatalogRefresh(pub, **opts).run(state['now'] + 1)
                self.assertEqual('failed', pub.ledger['requests'][-1]['outcome'])
                self.assertEqual(prior[:6], CatalogRefresh(pub, **opts).journal['staging']['pages'])
                state['bad'] = False
                complete = False
                for hour in range(2, 9):
                    state['now'] = NOW + hour * 3600
                    pub = Publisher(store, code); pub.reconcile(None)
                    helper.primary(pub, state['now'])
                    for _ in range(7):
                        collector = CatalogRefresh(pub, **opts)
                        result = collector.run(state['now'])
                        if result.status == 'complete':
                            complete = True
                            break
                        if result.status == 'yielded':
                            break
                    if complete: break
                self.assertTrue(complete)
                current = CatalogRefresh(Publisher(store, code), **opts).current()
                self.assertEqual({'countries': 103, 'organizations': 350, 'models': 532, 'sites': 251},
                                 current['coverage']['counts'])
                self.assertEqual(prior[:6], current['coverage']['pages'][:6])
                self.assertEqual(preserved, helper.preserved(pub))
        finally:
            server.shutdown(); thread.join(); server.server_close()

if __name__ == '__main__': unittest.main()
