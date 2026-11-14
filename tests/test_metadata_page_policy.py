"""Current captured metadata through actual loopback HTTP and Git authority."""
from copy import deepcopy
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import unittest
from urllib.parse import urlsplit

from tests import test_current_metadata_publisher as fixture

NOW = fixture.NOW
from tools.spacefox.catalog_refresh import CatalogRefresh, RefreshError
from tools.spacefox.publisher import Publisher


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
        finally:
            server.shutdown(); thread.join(); server.server_close()

if __name__ == '__main__': unittest.main()
