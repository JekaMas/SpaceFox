"""Independent R2 literal controls, with real local Git and loopback HTTP.

Only numeric storage thresholds and source responses are controlled. Collector,
HTTP worker, shared allowance, checkpoint/CAS and durable reopen are production.
"""
from contextlib import contextmanager
from copy import deepcopy
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
from tools.spacefox.publisher import GitState, Publisher
from tools.spacefox.schedule import (IdKind, LaunchRecord, LaunchStatus,
                                     StableId, TimePrecision, Timing)


def git(path, *args):
    return subprocess.run(['git', '-C', str(path), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


class IndependentCatalogR2Test(unittest.TestCase):
    @contextmanager
    def world(self):
        with tempfile.TemporaryDirectory(prefix='spacefox-independent-r2-') as folder:
            root = Path(folder)
            source, remote = root / 'source', root / 'state.git'
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            git(source, 'config', 'user.name', 'Independent R2')
            git(source, 'config', 'user.email', 'r2@example.invalid')
            git(source, 'commit', '--allow-empty', '-qm', 'independent R2 authority')
            code = git(source, 'rev-parse', 'HEAD')
            git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            store.bootstrap(code)
            pub = Publisher(store, code)
            pub.reconcile(None)
            record = LaunchRecord(
                StableId(IdKind.LAUNCH, 'll2', 'independent-r2-launch'),
                Timing(TimePrecision.EXACT, 20000), LaunchStatus.PENDING, 1000,
                configuration_id=StableId(IdKind.CONFIGURATION, 'll2', '267'),
                operator_id=StableId(IdKind.ORGANIZATION, 'll2', '167'),
                site_id=StableId(IdKind.SITE, 'll2', '367'),
                country_id=StableId(IdKind.COUNTRY, 'll2', '67'))
            slot = pub.reserve(pub.head, 1000, trigger='manual')
            pub.accept_source(pub.head, slot, (record,), 1000)
            world = {'now': 1001, 'calls': [], 'conditional': False}

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_GET(self):
                    # Read the actual shared remote before sending the response.
                    check = GitState(str(remote))
                    try:
                        _, ledger = check.load()
                        assert ledger['requests'][-1]['purpose'] == 'catalog'
                        assert ledger['requests'][-1]['outcome'] == 'reserved'
                    finally:
                        check.close()
                    path = self.path.split('?')[0]
                    body = world['bodies'][path]
                    tag = '"' + hashlib.sha256(body).hexdigest() + '"'
                    supplied = self.headers.get('If-None-Match')
                    status = 304 if world['conditional'] and supplied == tag else 200
                    world['calls'].append((self.path, supplied, status))
                    self.send_response_only(status)
                    self.send_header('Date', formatdate(world['now'], usegmt=True))
                    self.send_header('Age', '1')
                    self.send_header('ETag', tag)
                    if status == 200:
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    if status == 200:
                        self.wfile.write(body)

            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            origin = 'http://127.0.0.1:' + str(server.server_port)
            rows = {
                '/2.3.0/config/countries/': [dict(id=67, name='Unknown R2 jurisdiction',
                    alpha_2_code='??', alpha_3_code='???')],
                '/2.3.0/agencies/': [dict(id=167, name='R2 public operator',
                    url=origin + '/2.3.0/agencies/167/', response_mode='normal',
                    abbrev='R2', type=None, country=[{'id': 67}])],
                '/2.3.0/launcher_configurations/': [dict(id=267, name='R2 exact configuration',
                    url=origin + '/2.3.0/launcher_configurations/267/', response_mode='detailed',
                    full_name='R2 exact configuration pending', variant='', active=False,
                    pending_launches=2, is_placeholder=False, families=[{'id': 767}],
                    manufacturer={'id': 167, 'country': [{'id': 67}]})],
                '/2.3.0/pads/': [dict(id=367, name='R2 inactive upcoming pad',
                    url=origin + '/2.3.0/pads/367/', active=False, location=None,
                    country={'id': 67}, latitude=None, longitude=None, agencies=[{'id': 167}])],
            }
            world['bodies'] = {path: encoded(dict(count=1, next=None, previous=None, results=value))
                               for path, value in rows.items()}
            world['rows'] = rows
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                yield pub, store, world, origin, record
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
                store.close()

    def preserved(self, pub):
        return {key: pub.ledger[key] for key in ('accepted', 'active', 'pending', 'generation',
                                               'selection_validated_utc', 'last_poll_utc')}

    def test_initial_preflight_refusal_has_no_durable_candidate_or_http_then_valid_retry(self):
        with self.world() as (pub, store, world, origin, _):
            collector = CatalogRefresh(pub, origin=origin, local_http=True)
            original = self.preserved(pub)
            head = pub.head
            initial = deepcopy(collector.journal)
            with patch('tools.spacefox.catalog_refresh.MAX_CATALOG_CORPUS_BYTES', 1):
                with self.assertRaisesRegex(RefreshError, 'catalog corpus exceeds finite working-set bound'):
                    collector.run(1001)
            self.assertEqual(head, store.load()[0])
            self.assertNotIn('catalog_refresh', pub.ledger)
            self.assertEqual(initial, collector.journal)
            self.assertEqual({}, collector.objects)
            self.assertIsNone(collector.current())
            self.assertEqual([], world['calls'])
            self.assertEqual(1, len(pub.ledger['requests']))
            self.assertEqual(original, self.preserved(pub))
            # Four primary pages need16 slots/hour, so metadata has no share.
            collector.schedule_max_pages = 4
            outcome = collector.run(1001, max_requests=4)
            self.assertEqual(('yielded', 0), (outcome.status, outcome.requests))
            self.assertEqual([], world['calls'])
            self.assertIsNone(collector.current())
            self.assertEqual(original, self.preserved(pub))
            # Same persisted traversal, legal primary bound1, no reset of quota.
            collector.schedule_max_pages = 1
            outcome = collector.run(1002, max_requests=4)
            self.assertEqual(('complete', 4), (outcome.status, outcome.requests))
            expected_hashes = [hashlib.sha256(body).hexdigest() for body in world['bodies'].values()]
            current = collector.current()
            self.assertEqual(expected_hashes, [page['body']['sha256'] for page in current['coverage']['pages']])
            self.assertEqual([1000] * 4, [page['validatedUtc'] for page in current['coverage']['pages']])
            self.assertEqual({'countries': [67], 'organizations': [167], 'models': [267], 'sites': [367]},
                             current['coverage']['distinctIds'])
            self.assertEqual([267], current['coverage']['requiredModelIds'])
            self.assertEqual([367], current['coverage']['requiredSiteIds'])
            self.assertEqual([67], current['coverage']['unknownJurisdictionIds'])
            self.assertEqual(1000, current['coverage']['upcomingReferences'][0]['sourceValidatedUtc'])
            self.assertEqual(5, len(pub.ledger['requests']))
            self.assertEqual(original, self.preserved(pub))

    def test_replacement_corpus_refusal_retains_old_complete_and_four_staged_304_pages(self):
        with self.world() as (pub, store, world, origin, record):
            collector = CatalogRefresh(pub, origin=origin, local_http=True)
            self.assertEqual('complete', collector.run(1001, max_requests=4).status)
            first = collector.current()
            first_ref = deepcopy(collector.journal['current'])
            first_raw = store._blob(pub.head, 'catalog-refresh/objects/' + first_ref['sha256'] + '.json', 16777216)
            token = pub.reserve(pub.head, 4600, trigger='manual')
            pub.accept_source(pub.head, token, (record,), 4600)
            original = self.preserved(pub)
            world['now'], world['conditional'] = 4601, True
            self.assertEqual('partial', collector.run(4601, restart=True, max_requests=3).status)
            # Only the numeric corpus threshold changes. Raw pages are cached,
            # so a rejected second candidate cannot erase the first complete one.
            with patch('tools.spacefox.catalog_refresh.MAX_CATALOG_CORPUS_BYTES', 12000):
                with self.assertRaisesRegex(RefreshError, 'catalog corpus exceeds finite working-set bound'):
                    collector.run(4602)
            self.assertEqual({}, collector.objects)
            reopened = CatalogRefresh(pub, origin=origin, local_http=True)
            self.assertEqual(first, collector.current())
            self.assertEqual(first, reopened.current())
            self.assertEqual(reopened.journal, collector.journal)
            self.assertEqual(4, len(reopened.journal['staging']['pages']))
            self.assertEqual([304] * 4, [p['status'] for p in reopened.journal['staging']['pages']])
            self.assertEqual([4600] * 4, [p['validatedUtc'] for p in reopened.journal['staging']['pages']])
            self.assertEqual([hashlib.sha256(body).hexdigest() for body in world['bodies'].values()],
                             [p['body']['sha256'] for p in reopened.journal['staging']['pages']])
            self.assertEqual(8, len(world['calls']))
            self.assertEqual([304] * 4, [status for _, _, status in world['calls'][-4:]])
            self.assertEqual(5, len(pub.ledger['requests']))
            self.assertEqual(original, self.preserved(pub))
            outcome = collector.run(4603)
            self.assertEqual(('complete', 0), (outcome.status, outcome.requests))
            second = collector.current()
            self.assertEqual(first_ref, second['previousComplete'])
            self.assertEqual(first_ref, collector.journal['previous'])
            self.assertEqual(first['reference'], second['reference'])
            self.assertEqual((4600, 4600), (second['source']['observedFromUtc'], second['source']['observedToUtc']))
            self.assertEqual(1000, second['coverage']['upcomingReferences'][0]['sourceValidatedUtc'])
            self.assertEqual(8, len(world['calls']))
            self.assertEqual(first_raw, store._blob(pub.head, 'catalog-refresh/objects/' + first_ref['sha256'] + '.json', 16777216))
            self.assertEqual(original, self.preserved(pub))


if __name__ == '__main__':
    unittest.main()
