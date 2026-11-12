"""Independent R3 recovery controls at real local Git and loopback HTTP.

Literal source facts, JSON, hashes and event times supply the oracle. Only one
numeric journal limit is reduced; no collector/storage/request owner is replaced.
These directed real-I/O traces do not claim generated or all-interleaving PBT.
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
from tools.spacefox.publisher import (AllowanceUnavailable, GitState, Publisher,
                                     StateError)
from tools.spacefox.schedule import (IdKind, LaunchRecord, LaunchStatus,
                                     StableId, TimePrecision, Timing)


def git(path, *args):
    return subprocess.run(['git', '-C', str(path), *args], check=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout.decode().strip()


def encoded(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


class IndependentCatalogR3Test(unittest.TestCase):
    @contextmanager
    def world(self):
        with tempfile.TemporaryDirectory(prefix='spacefox-independent-r3-') as folder:
            root = Path(folder)
            source, remote = root / 'source', root / 'authority.git'
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            git(source, 'config', 'user.name', 'Independent R3')
            git(source, 'config', 'user.email', 'r3@example.invalid')
            git(source, 'commit', '--allow-empty', '-qm', 'R3 literal source authority')
            code = git(source, 'rev-parse', 'HEAD')
            git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            store.bootstrap(code)
            pub = Publisher(store, code)
            pub.reconcile(None)
            record = LaunchRecord(
                StableId(IdKind.LAUNCH, 'll2', 'literal-r3-flight'),
                Timing(TimePrecision.EXACT, 20000), LaunchStatus.PENDING, 1000,
                configuration_id=StableId(IdKind.CONFIGURATION, 'll2', '283'),
                operator_id=StableId(IdKind.ORGANIZATION, 'll2', '183'),
                site_id=StableId(IdKind.SITE, 'll2', '383'),
                country_id=StableId(IdKind.COUNTRY, 'll2', '83'))
            slot = pub.reserve(pub.head, 1000, trigger='manual')
            pub.accept_source(pub.head, slot, (record,), 1000)
            world = dict(now=1002, calls=[], hook=None, errors=[])

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_GET(self):
                    check = GitState(str(remote))
                    try:
                        _, ledger = check.load()
                        request = ledger['requests'][-1]
                        assert request['purpose'] == 'catalog'
                        assert request['outcome'] == 'reserved'
                        world['calls'].append(dict(path=self.path,
                            etag=self.headers.get('If-None-Match'), at=request['at_utc']))
                        if world['hook'] is not None:
                            hook, world['hook'] = world['hook'], None
                            hook()
                        body = world['bodies'][self.path.split('?')[0]]
                        self.send_response_only(200)
                        self.send_header('Date', formatdate(world['now'], usegmt=True))
                        self.send_header('Age', '2')
                        self.send_header('Content-Type', 'application/json')
                        self.send_header('Content-Length', str(len(body)))
                        self.send_header('ETag', '"' + hashlib.sha256(body).hexdigest() + '"')
                        self.end_headers()
                        self.wfile.write(body)
                    except Exception as error:
                        world['errors'].append(repr(error))
                        raise
                    finally:
                        check.close()

            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            origin = 'http://127.0.0.1:' + str(server.server_port)
            rows = {
                '/2.3.0/config/countries/': [dict(id=83, name='R3 unknown territory',
                    alpha_2_code='??', alpha_3_code='???')],
                '/2.3.0/agencies/': [dict(id=183, name='R3 separate operator',
                    url=origin + '/2.3.0/agencies/183/', response_mode='normal',
                    abbrev='R3', type=None, country=[{'id': 83}])],
                '/2.3.0/launcher_configurations/': [dict(id=283, name='R3 pending variant',
                    url=origin + '/2.3.0/launcher_configurations/283/', response_mode='detailed',
                    full_name='R3 pending exact variant', variant='', active=False,
                    pending_launches=1, is_placeholder=False, families=[{'id': 783}],
                    manufacturer={'id': 183, 'country': [{'id': 83}]})],
                '/2.3.0/pads/': [dict(id=383, name='R3 inactive referenced pad',
                    url=origin + '/2.3.0/pads/383/', active=False, location=None,
                    country={'id': 83}, latitude=None, longitude=None, agencies=[{'id': 183}])],
            }
            world['rows'] = rows
            world['bodies'] = {path: encoded(dict(count=1, next=None, previous=None, results=value))
                               for path, value in rows.items()}
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                yield pub, store, world, origin, source, remote
                self.assertEqual([], world['errors'])
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
                store.close()

    def preserved(self, pub):
        return {key: pub.ledger[key] for key in ('accepted', 'active', 'pending', 'generation',
                                               'selection_validated_utc', 'last_poll_utc')}

    def assert_complete(self, collector, world, epochs):
        current = collector.current()
        self.assertEqual({'countries': [83], 'organizations': [183], 'models': [283], 'sites': [383]},
                         current['coverage']['distinctIds'])
        self.assertEqual([hashlib.sha256(body).hexdigest() for body in world['bodies'].values()],
                         [page['body']['sha256'] for page in current['coverage']['pages']])
        self.assertEqual(epochs, [page['validatedUtc'] for page in current['coverage']['pages']])
        self.assertEqual([283], current['coverage']['requiredModelIds'])
        self.assertEqual([383], current['coverage']['requiredSiteIds'])
        self.assertEqual([83], current['coverage']['unknownJurisdictionIds'])
        self.assertEqual(1000, current['coverage']['upcomingReferences'][0]['sourceValidatedUtc'])
        self.assertEqual({'families': [783], 'locations': [], 'celestialBodies': []},
                         current['coverage']['externalRelationIds'])
        self.assertEqual((False, False, False), tuple(current['coverage'][key] for key in
                         ('worldwideOfficialSupplementClosure', 'artworkQualification', 'coordinateAccuracyQualification')))
        self.assertEqual((None, None), (current['reference']['sites'][0]['latitude'],
                                       current['reference']['sites'][0]['longitude']))

    def test_durable_prefix_survives_rejected_pages_backoff_and_same_instance_completion(self):
        with self.world() as (pub, store, world, origin, _, _):
            collector = CatalogRefresh(pub, origin=origin, local_http=True)
            preserved = self.preserved(pub)
            first = collector.run(1002)
            self.assertEqual(('partial', 1), (first.status, first.requests))
            prefix = deepcopy(collector.journal)
            first_hash = hashlib.sha256(world['bodies']['/2.3.0/config/countries/']).hexdigest()
            self.assertEqual(first_hash, prefix['staging']['pages'][0]['body']['sha256'])
            self.assertEqual(1000, prefix['staging']['pages'][0]['validatedUtc'])
            journal_ref = pub.ledger['catalog_refresh']
            durable_raw = store._blob(pub.head, 'catalog-refresh/journals/' + journal_ref['sha256'] + '.json', 1048576)
            self.assertLess(len(durable_raw), 1200, 'literal durable prefix fits the reduced journal budget')
            rejected_hashes = []
            for now, label in ((1003, 'Rejected R3 operator A'), (1303, 'Rejected R3 operator B')):
                world['rows']['/2.3.0/agencies/'][0]['name'] = label
                body = encoded(dict(count=1, next=None, previous=None, results=world['rows']['/2.3.0/agencies/']))
                world['bodies']['/2.3.0/agencies/'] = body
                rejected_hashes.append(hashlib.sha256(body).hexdigest())
                world['now'] = now
                with patch('tools.spacefox.catalog_refresh.MAX_CATALOG_JOURNAL_BYTES', 1200):
                    with self.assertRaisesRegex(RefreshError, 'catalog journal byte budget exhausted'):
                        collector.run(now)
                self.assertEqual({}, collector.objects)
                self.assertEqual(prefix, collector.journal)
                self.assertEqual(prefix, CatalogRefresh(pub, origin=origin, local_http=True).journal)
                self.assertIsNone(collector.current())
                self.assertEqual('failed', pub.ledger['requests'][-1]['outcome'])
                self.assertEqual(now + 300, pub.ledger['backoff_until_utc'])
                self.assertEqual(journal_ref, pub.ledger['catalog_refresh'])
                self.assertEqual(preserved, self.preserved(pub))
                paths = store._git('ls-tree', '-r', '--name-only', pub.head, 'catalog-refresh').stdout.decode()
                self.assertTrue(all(digest not in paths for digest in rejected_hashes))
                before_head, before_calls = pub.head, len(world['calls'])
                with self.assertRaises(AllowanceUnavailable):
                    collector.run(now + 299)
                self.assertEqual(before_head, pub.head)
                self.assertEqual(before_calls, len(world['calls']))
                self.assertEqual({'catalog-refresh/objects/' + first_hash + '.json'}, set(collector.objects))
            self.assertEqual(3, len(world['calls']))
            self.assertEqual(4, len(pub.ledger['requests']))
            world['now'] = 1603
            outcome = collector.run(1603, max_requests=4)
            self.assertEqual(('complete', 3), (outcome.status, outcome.requests))
            self.assert_complete(collector, world, [1000, 1601, 1601, 1601])
            self.assertEqual(6, len(world['calls']))
            self.assertEqual([None] * 6, [item['etag'] for item in world['calls']])
            self.assertEqual([1000, 1002, 1003, 1303, 1603, 1603, 1603],
                             [request['at_utc'] for request in pub.ledger['requests']])
            self.assertEqual(['success', 'success', 'failed', 'failed', 'success', 'success', 'success'],
                             [request['outcome'] for request in pub.ledger['requests']])
            self.assertEqual(preserved, self.preserved(pub))
            self.assertEqual(collector.current(), CatalogRefresh(pub, origin=origin, local_http=True).current())
            head = pub.head
            unchanged = collector.run(1604)
            self.assertEqual(('complete', 0), (unchanged.status, unchanged.requests))
            self.assertEqual(head, pub.head)
            self.assertEqual(6, len(world['calls']))
            print(json.dumps(dict(control='durable-prefix-journal-rejection', rejected=rejected_hashes,
                                  calls=world['calls'], slots=7, sourceEpochs=[1000, 1601, 1601, 1601])))

    def test_source_advance_during_http_consumes_uncertain_slot_then_adopted_owner_retries(self):
        with self.world() as (pub, store, world, origin, source, remote):
            collector = CatalogRefresh(pub, origin=origin, local_http=True)
            preserved = self.preserved(pub)
            self.assertEqual('partial', collector.run(1002).status)
            prefix = deepcopy(collector.journal)

            def advance_source():
                git(source, 'commit', '--allow-empty', '-qm', 'R3 source advances during HTTP')
                git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')

            world['hook'], world['now'] = advance_source, 1003
            with self.assertRaisesRegex(StateError, 'queued source code is stale'):
                collector.run(1003)
            self.assertEqual({}, collector.objects)
            self.assertEqual(prefix, collector.journal)
            self.assertIsNone(collector.current())
            self.assertEqual(3, len(pub.ledger['requests']))
            self.assertEqual('reserved', pub.ledger['requests'][-1]['outcome'])
            self.assertEqual(2, len(world['calls']))
            stale_head = pub.head
            with self.assertRaisesRegex(StateError, 'queued source code is stale'):
                collector.run(1063)
            self.assertEqual(stale_head, store.load()[0])
            self.assertEqual(2, len(world['calls']))
            current_code = git(source, 'rev-parse', 'HEAD')
            owner = Publisher(store, current_code)
            with self.assertRaisesRegex(StateError, 'explicitly adopt'):
                owner.reconcile(None)
            owner.adopt_code(owner.head)
            owner.reconcile(None)
            recovered = CatalogRefresh(owner, origin=origin, local_http=True)
            self.assertEqual(prefix, recovered.journal)
            before_head = owner.head
            with self.assertRaisesRegex(StateError, 'uncertain'):
                recovered.run(1062)
            self.assertEqual(before_head, owner.head)
            self.assertEqual(2, len(world['calls']))
            world['now'] = 1063
            outcome = recovered.run(1063, max_requests=4)
            self.assertEqual(('complete', 3), (outcome.status, outcome.requests))
            self.assert_complete(recovered, world, [1000, 1061, 1061, 1061])
            self.assertEqual(5, len(world['calls']))
            self.assertEqual(world['calls'][1]['path'], world['calls'][2]['path'])
            self.assertEqual([1000, 1002, 1003, 1063, 1063, 1063],
                             [request['at_utc'] for request in owner.ledger['requests']])
            self.assertEqual(['success', 'success', 'reserved', 'success', 'success', 'success'],
                             [request['outcome'] for request in owner.ledger['requests']])
            self.assertEqual(preserved, self.preserved(owner))
            print(json.dumps(dict(control='source-advance-http-result-recovery', calls=world['calls'],
                                  slots=6, sourceEpochs=[1000, 1061, 1061, 1061],
                                  codeAdopted=current_code)))


if __name__ == '__main__':
    unittest.main()
