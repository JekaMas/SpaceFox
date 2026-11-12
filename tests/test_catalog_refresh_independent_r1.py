"""Independent literal controls for final-save refusal and concurrent recovery.

Real temporary Git authority and loopback HTTP execute the production adapters.
Reduced corpus limit substitutes only the 64 MiB threshold, not the owner.
"""
from contextlib import contextmanager
from email.utils import formatdate
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch

from tools.spacefox.catalog_refresh import CatalogRefresh, RefreshError
from tools.spacefox.publisher import Conflict, GitState, Publisher


def git(path, *args):
    return subprocess.run(['git', '-C', str(path), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()


class IndependentCatalogR1Test(unittest.TestCase):
    @contextmanager
    def world(self):
        with tempfile.TemporaryDirectory(prefix='spacefox-independent-r1-') as folder:
            root = Path(folder)
            source, remote = root / 'source', root / 'authority.git'
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            git(source, 'config', 'user.name', 'Independent local verifier')
            git(source, 'config', 'user.email', 'verifier@example.invalid')
            git(source, 'commit', '--allow-empty', '-qm', 'independent source')
            code = git(source, 'rev-parse', 'HEAD')
            git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            store.bootstrap(code)
            pub = Publisher(store, code)
            pub.reconcile(None)
            slot = pub.reserve(pub.head, 1000, trigger='manual')
            pub.accept_source(pub.head, slot, (), 1000)
            state = {'now': 1001, 'calls': [], 'hook': None}

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_GET(self):
                    # Observe the actual remote authority, before any body is sent.
                    check = GitState(str(remote))
                    try:
                        _, ledger = check.load()
                        assert ledger['requests'][-1]['purpose'] == 'catalog'
                        assert ledger['requests'][-1]['outcome'] == 'reserved'
                    finally:
                        check.close()
                    state['calls'].append(self.path)
                    if state['hook'] is not None:
                        hook, state['hook'] = state['hook'], None
                        hook()
                    body = state['bodies'][self.path.split('?')[0]]
                    self.send_response_only(200)
                    self.send_header('Date', formatdate(state['now'], usegmt=True))
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(body)))
                    self.send_header('ETag', '"' + hashlib.sha256(body).hexdigest() + '"')
                    self.end_headers()
                    self.wfile.write(body)

            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            origin = 'http://127.0.0.1:' + str(server.server_port)
            rows = {
                '/2.3.0/config/countries/': [dict(id=3, name='Literal island', alpha_2_code='XY', alpha_3_code='XYZ')],
                '/2.3.0/agencies/': [dict(id=13, name='Literal operator', url=origin + '/2.3.0/agencies/13/',
                    response_mode='normal', abbrev='LO', type=None, country=[{'id': 3}])],
                '/2.3.0/launcher_configurations/': [dict(id=23, name='Literal vehicle',
                    url=origin + '/2.3.0/launcher_configurations/23/', response_mode='detailed',
                    full_name='Literal vehicle variant', variant='', active=False,
                    pending_launches=1, is_placeholder=False, families=[], manufacturer=None)],
                '/2.3.0/pads/': [dict(id=33, name='Literal pad', url=origin + '/2.3.0/pads/33/',
                    active=False, location=None, country={'id': 3}, latitude=None, longitude=None, agencies=[{'id': 13}])],
            }
            state['bodies'] = {path: json.dumps(dict(count=1, next=None, previous=None, results=value),
                                                separators=(',', ':')).encode() for path, value in rows.items()}
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                yield pub, store, state, origin, str(remote), code
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
                store.close()

    def test_final_corpus_refusal_restores_public_durable_state_then_completes_without_http(self):
        with self.world() as (pub, store, world, origin, _, _):
            collector = CatalogRefresh(pub, origin=origin, local_http=True)
            preserved = {key: pub.ledger[key] for key in
                         ('accepted', 'active', 'pending', 'generation', 'last_poll_utc', 'selection_validated_utc')}
            self.assertEqual('partial', collector.run(1001, max_requests=3).status)
            with patch('tools.spacefox.catalog_refresh.MAX_CATALOG_CORPUS_BYTES', 6000):
                with self.assertRaisesRegex(RefreshError, 'catalog corpus exceeds finite working-set bound'):
                    collector.run(1002)
            reopened = CatalogRefresh(pub, origin=origin, local_http=True)
            # The final raw page did commit. The over-budget candidate did not.
            self.assertIsNone(reopened.current())
            self.assertEqual(4, len(reopened.journal['staging']['pages']))
            self.assertEqual([hashlib.sha256(body).hexdigest() for body in world['bodies'].values()],
                             [page['body']['sha256'] for page in reopened.journal['staging']['pages']])
            self.assertEqual(5, len(pub.ledger['requests']))
            self.assertTrue(all(request['outcome'] == 'success' for request in pub.ledger['requests']))
            self.assertEqual(preserved, {key: pub.ledger[key] for key in preserved})
            self.assertEqual(reopened.current(), collector.current(),
                             'a refused final candidate must not become visible in the same instance')
            self.assertEqual(reopened.journal, collector.journal)
            # Event: capacity becomes sufficient. All four durable pages suffice.
            result = collector.run(1003)
            self.assertEqual(('complete', 0), (result.status, result.requests))
            self.assertEqual(4, len(world['calls']))
            self.assertEqual({'countries': [3], 'organizations': [13], 'models': [23], 'sites': [33]},
                             collector.current()['coverage']['distinctIds'])
            self.assertEqual(1001, collector.current()['source']['observedFromUtc'])
            self.assertEqual(1001, collector.current()['source']['observedToUtc'])
            self.assertEqual(preserved, {key: pub.ledger[key] for key in preserved})
            raw = store._blob(pub.head, 'catalog-refresh/objects/' + result.completed['sha256'] + '.json', 16777216)
            self.assertEqual(result.completed['sha256'], hashlib.sha256(raw).hexdigest())

    def test_concurrent_authority_advance_after_http_retains_slot_and_repeats_only_uncommitted_page(self):
        with self.world() as (pub, store, world, origin, remote, code):
            collector = CatalogRefresh(pub, origin=origin, local_http=True)

            def concurrent_request_completes():
                other_store = GitState(remote)
                try:
                    other = Publisher(other_store, code)
                    other.reconcile(None)
                    # The first catalog request is uncertain until exactly1061.
                    slot = other.reserve(other.head, 1061, purpose='version', trigger='manual')
                    other.finish_request(other.head, slot, 1061, 'success')
                finally:
                    other_store.close()

            world['hook'] = concurrent_request_completes
            with self.assertRaises(Conflict):
                collector.run(1001)
            pub = Publisher(store, code)
            pub.reconcile(None)
            reopened = CatalogRefresh(pub, origin=origin, local_http=True)
            self.assertEqual([], reopened.journal['staging']['pages'])
            self.assertIsNone(reopened.current())
            self.assertEqual([(1000, 'schedule', 'success'), (1001, 'catalog', 'reserved'),
                              (1061, 'version', 'success')],
                             [(r['at_utc'], r['purpose'], r['outcome']) for r in pub.ledger['requests']])
            self.assertEqual(1, len(world['calls']))
            world['now'] = 1061
            self.assertEqual('complete', reopened.run(1061, max_requests=4).status)
            self.assertEqual(5, len(world['calls']))
            self.assertEqual(world['calls'][0], world['calls'][1])
            self.assertEqual(7, len(pub.ledger['requests']))
            self.assertEqual('reserved', pub.ledger['requests'][1]['outcome'])
            self.assertEqual(1000, pub.ledger['last_poll_utc'])
            self.assertEqual(1061, reopened.current()['source']['observedFromUtc'])


if __name__ == '__main__':
    unittest.main()
