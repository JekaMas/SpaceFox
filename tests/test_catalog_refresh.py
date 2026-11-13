"""Independent literal LL2 pages at real Git authority and HTTP/CLI boundaries."""
from contextlib import contextmanager
from copy import deepcopy
from email.utils import formatdate
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from tools.spacefox.catalog_refresh import (CatalogRefresh, RefreshError,
                                           reference_inventory,
                                           MAX_PAGE_BYTES)
from tools.spacefox.catalog import REFERENCE_FIELDS, _check_reference_row
from tools.spacefox.provider import Response
from tools.spacefox.publisher import (GitState, Publisher, Conflict, StateError,
                                      AllowanceUnavailable)
from tools.spacefox.schedule import (StableId, IdKind, LaunchRecord, Timing,
                                     TimePrecision, LaunchStatus, RefreshPolicy)

ROOT = Path(__file__).resolve().parents[1]
ORIGIN = 'https://ll.thespacedevs.com'
COLLECTIONS = ('countries', 'organizations', 'models', 'sites')
PATHS = {'countries': '/2.3.0/config/countries/', 'organizations': '/2.3.0/agencies/',
         'models': '/2.3.0/launcher_configurations/', 'sites': '/2.3.0/pads/'}


def literal_bytes(value):
    # Independent serialization; expected hashes never use collector helpers.
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


def git(path, *args):
    result = subprocess.run(['git', '-C', str(path), *args], check=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return result.stdout.decode().strip()


def facts(origin=ORIGIN):
    country = {'id': 7, 'name': 'New Territory', 'alpha_2_code': 'XZ', 'alpha_3_code': 'XZZ'}
    unknown = {'id': 999, 'name': 'Unknown', 'alpha_2_code': '??', 'alpha_3_code': '???'}
    organization = {'response_mode': 'normal', 'id': 70, 'url': origin + '/2.3.0/agencies/70/?format=json',
                    'name': 'New Public Organization', 'abbrev': 'NPO',
                    'type': {'id': 1, 'name': 'Government'}, 'country': [deepcopy(country)]}
    model = {'response_mode': 'detailed', 'id': 71,
             'url': origin + '/2.3.0/launcher_configurations/71/?format=json',
             'name': 'Exact New Model A', 'full_name': 'Exact New Model A Booster 2', 'variant': '2',
             'active': False, 'is_placeholder': False, 'pending_launches': 2,
             'families': [{'id': 90, 'name': 'Family with independent identity'}],
             'manufacturer': deepcopy(organization)}
    model2 = deepcopy(model)
    model2.update(id=72, url=origin + '/2.3.0/launcher_configurations/72/?format=json',
                  full_name='Exact New Model A Booster 4', variant='4', active=True, pending_launches=0)
    site = {'id': 80, 'url': origin + '/2.3.0/pads/80/?format=json', 'name': 'Inactive future launch site',
            'active': False, 'agencies': [deepcopy(organization)], 'country': deepcopy(country),
            'latitude': None, 'longitude': None, 'total_launch_count': 0, 'orbital_launch_attempt_count': 0,
            'location': {'id': 99, 'name': 'Island by the date line', 'celestial_body': {'id': 1, 'name': 'Earth'}}}
    return {'countries': [country, unknown], 'organizations': [organization],
            'models': [model, model2], 'sites': [site]}


def launch(at=1000):
    return LaunchRecord(StableId(IdKind.LAUNCH, 'll2', 'a-literal-upcoming-id'),
                        Timing(TimePrecision.EXACT, 20000), LaunchStatus.PENDING, at,
                        configuration_id=StableId(IdKind.CONFIGURATION, 'll2', '71'),
                        operator_id=StableId(IdKind.ORGANIZATION, 'll2', '70'),
                        site_id=StableId(IdKind.SITE, 'll2', '80'), country_id=StableId(IdKind.COUNTRY, 'll2', '7'))


class LiteralSource:
    def __init__(self, publisher, data=None):
        self.publisher = publisher
        self.data = facts() if data is None else data
        self.calls = []
        self.now = 1001
        self.age = 0
        self.date = None
        self.conditional = False
        self.failure = None
        self.mutate = None

    def get(self, url, etag=None):
        # Observe committed authority BEFORE pretending that HTTP starts.
        head, ledger = self.publisher.store.load()
        assert head == self.publisher.head
        assert ledger['requests'][-1]['purpose'] == 'catalog'
        assert ledger['requests'][-1]['outcome'] == 'reserved'
        self.calls.append((url, etag, ledger['requests'][-1]['at_utc']))
        if self.failure is not None:
            raise self.failure
        parsed = urlsplit(url)
        collection = next(c for c, path in PATHS.items() if parsed.path == path)
        query = parse_qs(parsed.query)
        offset = int(query.get('offset', ['0'])[0])
        size = int(query['limit'][0])
        rows = deepcopy(self.data[collection][offset:offset + size])
        def link(at):
            values = {'format': 'json', 'limit': str(size)}
            if collection != 'countries':
                values['mode'] = 'normal' if collection == 'organizations' else 'detailed'
            if at:
                values['offset'] = str(at)
            from urllib.parse import urlencode
            return parsed.scheme + '://' + parsed.netloc + parsed.path + '?' + urlencode(values)
        page = dict(count=len(self.data[collection]), next=link(offset + len(rows)) if offset + len(rows) < len(self.data[collection]) else None,
                    previous=None if offset == 0 else link(max(0, offset - size)), results=rows)
        if self.mutate is not None:
            page = self.mutate(collection, offset, page)
        body = literal_bytes(page)
        tag = '"' + hashlib.sha256(body).hexdigest() + '"'
        headers = {'date': formatdate(self.now if self.date is None else self.date, usegmt=True),
                   'age': str(self.age), 'content-type': 'application/json', 'etag': tag}
        if self.conditional and etag == tag:
            return Response(304, headers, b'')
        return Response(200, headers, body)


class CatalogRefreshTest(unittest.TestCase):
    @contextmanager
    def authority(self, *, at=1000, policy=None, real_source=False, with_launch=True):
        with tempfile.TemporaryDirectory(prefix='spacefox-refresh-test-') as folder:
            root = Path(folder)
            remote, source = root / 'remote.git', root / 'source'
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            subprocess.run(['git', 'init', '-q', str(source)], check=True)
            git(source, 'config', 'user.name', 'Test')
            git(source, 'config', 'user.email', 'test@example.invalid')
            if real_source:
                for name in ['tools/__init__.py', 'tools/refresh_catalog.py', 'tools/spacefox/__init__.py',
                             'tools/spacefox/catalog_refresh.py', 'tools/spacefox/publisher.py',
                             'tools/spacefox/provider.py', 'tools/spacefox/schedule.py']:
                    destination = source / name
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if (ROOT / name).exists():
                        shutil.copyfile(ROOT / name, destination)
                    else:
                        destination.write_bytes(b'')
                git(source, 'add', '.')
            git(source, 'commit', '--allow-empty', '-qm', 'literal source authority')
            code = git(source, 'rev-parse', 'HEAD')
            git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            store.bootstrap(code, policy or RefreshPolicy())
            pub = Publisher(store, code)
            pub.reconcile(None)
            token = pub.reserve(pub.head, at, trigger='manual')
            pub.accept_source(pub.head, token, (launch(at),) if with_launch else (), at)
            transport = LiteralSource(pub)
            transport.now = at + 1
            try:
                yield root, source, remote, store, pub, transport
            finally:
                store.close()

    def collector(self, pub, transport, **options):
        return CatalogRefresh(pub, transport=transport, **options)

    def next_hour(self, pub, transport, at):
        token = pub.reserve(pub.head, at, trigger='manual')
        pub.accept_source(pub.head, token, (launch(1000),), at)
        transport.now = at + 1
        return at + 1

    def preserved(self, pub):
        ledger = pub.ledger
        return {k: ledger[k] for k in ('accepted', 'active', 'pending', 'generation', 'selection_validated_utc', 'last_poll_utc')}

    def test_complete_resume_relations_and_immutable_adapter(self):
        with self.authority() as (_, _, _, store, pub, transport):
            before = self.preserved(pub)
            for i in range(6):
                collector = self.collector(pub, transport, page_size=1)
                result = collector.run(1001 + i)
                self.assertEqual(i + 1, len(transport.calls))
                self.assertEqual('complete' if i == 5 else 'partial', result.status)
                # Reopen the actual Git authority after every page.
                pub = Publisher(store, pub.running_code)
                pub.reconcile(None)
                transport.publisher = pub
            candidate = self.collector(pub, transport, page_size=1).current()
            self.assertEqual({'countries': 2, 'organizations': 1, 'models': 2, 'sites': 1}, candidate['coverage']['counts'])
            self.assertEqual([71, 72], candidate['coverage']['requiredModelIds'])
            self.assertEqual([80], candidate['coverage']['requiredSiteIds'])
            self.assertEqual([999], candidate['coverage']['unknownJurisdictionIds'])
            self.assertEqual([7, 999], candidate['coverage']['distinctIds']['countries'])
            self.assertFalse(candidate['reference']['models'][0]['providerActive'])
            self.assertEqual(2, candidate['reference']['models'][0]['providerPendingLaunches'])
            self.assertEqual([90], candidate['reference']['models'][0]['familyIds'])
            self.assertEqual(70, candidate['reference']['models'][0]['manufacturerId'])
            self.assertEqual([7], candidate['reference']['organizations'][0]['countryIds'])
            self.assertEqual('missing-or-invalid', candidate['reference']['sites'][0]['coordinateStatus'])
            self.assertIsNone(candidate['reference']['sites'][0]['latitude'])
            self.assertEqual(1000, candidate['coverage']['upcomingReferences'][0]['sourceValidatedUtc'])
            self.assertEqual({'7': 1001, '999': 1001}, candidate['coverage']['recordValidatedUtc']['countries'])
            self.assertFalse(candidate['coverage']['worldwideOfficialSupplementClosure'])
            self.assertFalse(candidate['coverage']['artworkQualification'])
            self.assertEqual(before, self.preserved(pub))
            adapter = reference_inventory(candidate)
            for collection in COLLECTIONS:
                for row in adapter[collection]:
                    self.assertEqual(REFERENCE_FIELDS[collection], set(row))
                    _check_reference_row(row, collection)
            adapter['models'][0]['name'] = 'caller mutation'
            self.assertEqual('Exact New Model A', candidate['reference']['models'][0]['name'])
            ref = pub.ledger['catalog_refresh']
            snapshot_raw = store._blob(pub.head, 'catalog-refresh/objects/' + result.completed['sha256'] + '.json', 16777216)
            self.assertEqual(result.completed['sha256'], hashlib.sha256(snapshot_raw).hexdigest())
            # Schedule writes preserve every exact offwatch object and journal.
            before_objects = store._git('ls-tree', '-r', pub.head, 'catalog-refresh').stdout
            token = pub.reserve(pub.head, 1010, trigger='manual')
            pub.finish_request(pub.head, token, 1010, 'success')
            self.assertEqual(ref, pub.ledger['catalog_refresh'])
            self.assertEqual(before_objects, store._git('ls-tree', '-r', pub.head, 'catalog-refresh').stdout)
            stable_head = pub.head
            self.assertEqual('complete', self.collector(pub, transport, page_size=1).run(1011).status)
            self.assertEqual(stable_head, pub.head)
            self.assertEqual(6, len(transport.calls))
        # Exercise the actual cloud journal writer and nonempty active artifact
        # preservation in both directions, rather than merely asserting nulls.
        from tools.spacefox.cloud import arm, write_journal, journal
        from tools.spacefox.publisher import LiveRevision
        from tests.test_cloud_delivery import literal_files
        with self.authority(with_launch=False) as (_, _, _, store, pub, transport):
            files, digest = literal_files(pub.ledger['instance_id'])
            pending = pub.prepare(pub.head, 1000, files, digest,
                                  feed_publisher={'instance': pub.ledger['instance_id'],
                                                  'generation': 1, 'selectionValidatedUtc': None})
            before = pub.ledger
            with self.assertRaisesRegex(StateError, 'reconcile'):
                self.collector(pub, transport).run(1001)
            self.assertEqual(before, pub.ledger)
            self.assertEqual([], transport.calls)
            pub, _ = arm(pub, expected=pub.head, repository='owner/SpaceFox', run_id=1,
                         run_attempt=1, artifact_id=1, now=1000)
            pub.reconcile(LiveRevision(pending.generation, pending.artifact_revision))
            cloud = journal(pub)
            pub = write_journal(pub, dict(cloud, status='succeed'))
            live = LiveRevision(pending.generation, pending.artifact_revision)
            pub.reconcile(live)
            transport.publisher = pub
            original = self.preserved(pub)
            cloud_bytes = store._blob(pub.head, 'cloud.json', 1048576)
            artifact_tree = store._git('ls-tree', '-r', pub.head, 'artifacts').stdout
            self.collector(pub, transport).run(1001, max_requests=4)
            self.assertEqual(original, self.preserved(pub))
            self.assertEqual(artifact_tree, store._git('ls-tree', '-r', pub.head, 'artifacts').stdout)
            self.assertEqual(cloud_bytes, store._blob(pub.head, 'cloud.json', 1048576))
            catalog_tree = store._git('ls-tree', '-r', pub.head, 'catalog-refresh').stdout
            pub = write_journal(pub, journal(pub))
            pub.reconcile(live)
            self.assertEqual(catalog_tree, store._git('ls-tree', '-r', pub.head, 'catalog-refresh').stdout)
            self.assertEqual(original, self.preserved(pub))
            for path, raw in files.items():
                self.assertEqual(raw, store._blob(pub.head, 'artifacts/1/' + path, 1048576))
            old_size = store.measure()['catalog_blob_bytes']
            token = pub.reserve(pub.head, 4600, trigger='manual')
            pub.accept_source(pub.head, token, (), 4600)
            original = self.preserved(pub)
            transport.now = 4601
            for identity in range(901, 911):
                row = deepcopy(transport.data['models'][0])
                row.update(id=identity, url=ORIGIN + '/2.3.0/launcher_configurations/' + str(identity) + '/?format=json',
                           full_name='New unrelated exact configuration ' + str(identity))
                transport.data['models'].append(row)
            transport.publisher = pub
            collector = self.collector(pub, transport)
            self.assertEqual('complete', collector.run(4601, restart=True, max_requests=4).status)
            self.assertEqual(12, collector.current()['coverage']['counts']['models'])
            self.assertGreater(store.measure()['catalog_blob_bytes'], old_size)
            self.assertEqual(original, self.preserved(pub))
            self.assertEqual(artifact_tree, store._git('ls-tree', '-r', pub.head, 'artifacts').stdout)
            self.assertEqual(cloud_bytes, store._blob(pub.head, 'cloud.json', 1048576))
            print(json.dumps({'globalGrowthOnlyOffwatch': {'beforeBytes': old_size,
                  'after': store.measure(), 'unchangedServedArtifactBytes': sum(map(len, files.values()))}}))

    def test_invalid_pages_preserve_complete_and_checkpoint(self):
        mutations = {
            'truncated': lambda c, o, p: dict(p, count=p['count'] + 1, next=None),
            'duplicate': lambda c, o, p: dict(p, results=[p['results'][0], p['results'][0]]) if c == 'countries' else p,
            'wrong-origin': lambda c, o, p: dict(p, next='https://evil.invalid/2.3.0/config/countries/?format=json&limit=20&offset=2'),
            'nonadvancing': lambda c, o, p: dict(p, next=ORIGIN + '/2.3.0/config/countries/?format=json&limit=20&offset=0'),
            'bad-type': lambda c, o, p: dict(p, results=[dict(p['results'][0], id=True)]) if c == 'countries' else p,
            'wrong-row-origin': lambda c, o, p: dict(p, results=[dict(p['results'][0], url='https://evil.invalid/70/')]) if c == 'organizations' else p,
        }
        for name, mutate in mutations.items():
            with self.subTest(name=name), self.authority() as (_, _, _, store, pub, transport):
                self.collector(pub, transport).run(1001, max_requests=4)
                previous = self.collector(pub, transport).current()
                now = self.next_hour(pub, transport, 4600)
                transport.mutate = mutate
                collector = self.collector(pub, transport)
                prior_cache = deepcopy(collector.journal['cache'])
                preserved = self.preserved(pub)
                with self.assertRaises(StateError):
                    collector.run(now, restart=True, max_requests=4)
                reopened = self.collector(pub, transport)
                self.assertEqual(previous, reopened.current())
                self.assertEqual(preserved, self.preserved(pub))
                if name == 'duplicate':
                    self.assertEqual([], reopened.journal['staging']['pages'])
                    self.assertEqual({url: entry for url, entry in prior_cache.items()
                                      if '/config/countries/' not in url}, reopened.journal['cache'])
                else:
                    self.assertIsNotNone(reopened.journal['staging'])
                self.assertEqual('failed', pub.ledger['requests'][-1]['outcome'])
        with self.authority() as (_, _, _, _, pub, transport):
            collector = self.collector(pub, transport, page_size=1)
            collector.run(1001)
            prefix = deepcopy(collector.journal['staging'])
            transport.mutate = lambda c, o, p: dict(p, count=3) if c == 'countries' and o else p
            with self.assertRaisesRegex(RefreshError, 'drifting'):
                collector.run(1002)
            self.assertEqual(prefix, self.collector(pub, transport, page_size=1).journal['staging'])
        with self.authority() as (_, _, _, _, pub, transport):
            collector = self.collector(pub, transport, page_size=1)
            collector.run(1001)
            prefix = deepcopy(collector.journal['staging'])
            transport.mutate = lambda c, o, p: dict(p, results=[deepcopy(transport.data['countries'][0])]) if c == 'countries' and o else p
            with self.assertRaisesRegex(RefreshError, 'duplicate'):
                collector.run(1002)
            reopened = self.collector(pub, transport, page_size=1)
            self.assertEqual([], reopened.journal['staging']['pages'])
            self.assertEqual({}, reopened.journal['cache'])
        for issue in ('dangling-manufacturer', 'dangling-country', 'dangling-upcoming'):
            with self.subTest(issue=issue), self.authority() as (_, _, _, _, pub, transport):
                if issue == 'dangling-manufacturer':
                    transport.data['models'][0]['manufacturer']['id'] = 7777
                elif issue == 'dangling-country':
                    transport.data['organizations'][0]['country'][0]['id'] = 7777
                else:
                    transport.data['models'] = [transport.data['models'][1]]
                with self.assertRaisesRegex(RefreshError, 'dangling'):
                    self.collector(pub, transport).run(1001, max_requests=4)
                self.assertIsNone(self.collector(pub, transport).current())
        with self.authority() as (_, _, _, _, pub, transport):
            transport.mutate = lambda c, o, p: dict(p, padding='x' * MAX_PAGE_BYTES)
            with self.assertRaisesRegex(RefreshError, 'byte bound'):
                self.collector(pub, transport).run(1001)
            self.assertEqual([], self.collector(pub, transport).journal['staging']['pages'])

    def test_conditional_cache_dates_retention_and_growth(self):
        with self.authority() as (_, _, _, store, pub, transport):
            collector = self.collector(pub, transport)
            collector.run(1001, max_requests=4)
            first = collector.current()
            first_ref = collector.journal['current']
            first_bytes = store._blob(pub.head, 'catalog-refresh/objects/' + first_ref['sha256'] + '.json', 16777216)
            saved_age = self.preserved(pub)
            now = self.next_hour(pub, transport, 4600)
            transport.conditional = True
            transport.age = 300
            collector = self.collector(pub, transport)
            result = collector.run(now, restart=True, max_requests=4)
            self.assertEqual('complete', result.status)
            second = collector.current()
            self.assertEqual([304] * 4, [p['status'] for p in second['coverage']['pages']])
            self.assertEqual(first['reference'], second['reference'])
            self.assertEqual(4301, second['source']['observedFromUtc'])
            self.assertEqual([p['body'] for p in first['coverage']['pages']], [p['body'] for p in second['coverage']['pages']])
            self.assertTrue(all(call[1] is not None for call in transport.calls[-4:]))
            self.assertEqual(first_bytes, store._blob(pub.head, 'catalog-refresh/objects/' + first_ref['sha256'] + '.json', 16777216))
            self.assertEqual(saved_age['accepted']['entries'][0]['record']['source_validated_utc'],
                             pub.ledger['accepted']['entries'][0]['record']['source_validated_utc'])
            self.assertEqual(saved_age['selection_validated_utc'], pub.ledger['selection_validated_utc'])
            now = self.next_hour(pub, transport, 8200)
            transport.age = 0
            transport.data['models'] = [transport.data['models'][0]]
            transport.data['countries'] = [transport.data['countries'][0]]
            collector = self.collector(pub, transport)
            collector.run(now, restart=True, max_requests=4)
            missing = collector.current()
            self.assertEqual([72], missing['missingComparedToPrevious']['models'])
            self.assertEqual([999], missing['missingComparedToPrevious']['countries'])
            self.assertEqual('Exact New Model A Booster 4', missing['retainedMissing']['models'][0]['fact']['fullName'])
            self.assertEqual(4301, missing['retainedMissing']['models'][0]['lastObservedUtc'])
            self.assertNotIn('retired', literal_bytes(missing['retainedMissing']).decode())
            # A source-only catalog corpus grows without a served artifact or
            # accepted schedule/selection-size change. Actual finite cap enforced.
            sizes = store.measure()
            self.assertLessEqual(sizes['ledger_bytes'], 65536)
            self.assertLess(sizes['catalog_blob_bytes'], 67108864)
            self.assertGreater(sizes['history_object_bytes'], sizes['catalog_blob_bytes'])
            self.assertIsNone(pub.ledger['active'])
            self.assertIsNone(pub.ledger['pending'])
            stable_complete = deepcopy(collector.current())
            now = self.next_hour(pub, transport, 11800)
            with patch('tools.spacefox.catalog_refresh.MAX_CATALOG_CORPUS_BYTES', 100):
                with self.assertRaisesRegex(RefreshError, 'working-set'):
                    self.collector(pub, transport).run(now, restart=True)
            self.assertEqual(stable_complete, self.collector(pub, transport).current())
        for kind in ('stale-date', 'future-date', 'invalid-age', 'uncached-304'):
            with self.subTest(kind=kind), self.authority() as (_, _, _, _, pub, transport):
                if kind == 'stale-date':
                    transport.date = -90000
                elif kind == 'future-date':
                    transport.date = 1100
                elif kind == 'invalid-age':
                    transport.age = -1
                else:
                    transport.get = lambda url, etag=None: Response(304, {'date': formatdate(1001, usegmt=True)}, b'')
                with self.assertRaises((StateError, ValueError)):
                    self.collector(pub, transport).run(1001)
                self.assertIsNone(self.collector(pub, transport).current())
        with self.authority() as (_, _, _, _, pub, transport):
            collector = self.collector(pub, transport, max_source_age_seconds=60)
            collector.run(1001, max_requests=3)
            transport.now = 1100
            with self.assertRaisesRegex(RefreshError, 'source-date age'):
                collector.run(1100)
            self.assertIsNone(self.collector(pub, transport, max_source_age_seconds=60).current())

    def test_shared_quota_clock_loss_priority_and_cas(self):
        with self.authority() as (_, source, remote, store, pub, transport):
            before = self.preserved(pub)
            transport.failure = KeyboardInterrupt('request disappeared')
            with self.assertRaises(KeyboardInterrupt):
                self.collector(pub, transport).run(1001)
            self.assertEqual(2, len(pub.ledger['requests']))
            self.assertEqual('reserved', pub.ledger['requests'][-1]['outcome'])
            pub = Publisher(store, pub.running_code)
            pub.reconcile(None)
            transport.publisher, transport.failure = pub, None
            with self.assertRaisesRegex(StateError, 'uncertain'):
                self.collector(pub, transport).run(1060)
            self.assertEqual(1, len(transport.calls))
            transport.now = 1061
            self.assertEqual('partial', self.collector(pub, transport).run(1061).status)
            self.assertEqual(3, len(pub.ledger['requests']))
            self.assertEqual(before, self.preserved(pub))
            # Catalog cannot obtain launch acceptance rights, even after200.
            token = pub.ledger['requests'][-1]['id']
            with self.assertRaises(StateError):
                pub.accept_source(pub.head, token, (launch(),), 1061)
            # Real external writer changes the authority; stale collector must
            # refuse before transport or metadata mutation.
            stale = self.collector(pub, transport)
            other = Publisher(store, pub.running_code)
            other.reconcile(None)
            slot = other.reserve(other.head, 1062, purpose='version', trigger='manual')
            other.finish_request(other.head, slot, 1062, 'success')
            calls = len(transport.calls)
            with self.assertRaises(Conflict):
                stale.run(1062)
            self.assertEqual(calls, len(transport.calls))
            pub = Publisher(store, pub.running_code)
            pub.reconcile(None)
            transport.publisher = pub
            git(source, 'commit', '--allow-empty', '-qm', 'new source authority')
            git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            head = pub.head
            with self.assertRaisesRegex(StateError, 'stale'):
                self.collector(pub, transport).run(1063)
            self.assertEqual(head, store.load()[0])
            self.assertEqual(calls, len(transport.calls))
        with self.authority() as (_, _, _, _, pub, transport):
            # Six catalog calls plus initial schedule request exhaust only the
            # metadata share; eight slots remain for four2-page near polls.
            collector = self.collector(pub, transport, page_size=1)
            for now in range(1001, 1007):
                transport.now = now
                self.assertEqual(1, collector.run(now).requests)
            head = pub.head
            self.assertEqual('yielded', collector.run(1007, restart=True).status)
            self.assertEqual(7, len(pub.ledger['requests']))
            self.assertEqual(6, len(transport.calls))
            for now in range(1008, 1016):
                slot = pub.reserve(pub.head, now, trigger='extra')
                pub.finish_request(pub.head, slot, now, 'success')
            self.assertEqual(15, len(pub.ledger['requests']))
            with self.assertRaises(AllowanceUnavailable):
                pub.reserve(pub.head, 1016, trigger='extra')
            self.assertEqual(6, len(transport.calls))
            now = self.next_hour(pub, transport, 4616)
            self.assertEqual(1, self.collector(pub, transport, page_size=1).run(now).requests)
            self.assertEqual(2, len(pub.ledger['requests']))
        with self.authority() as (_, _, _, _, pub, transport):
            calls = len(transport.calls)
            result = self.collector(pub, transport).run(4600)
            self.assertEqual('yielded', result.status)
            self.assertEqual(calls, len(transport.calls))
            self.assertEqual(1000, pub.ledger['last_poll_utc'])
            self.assertEqual(1, len(pub.ledger['requests']))
            # Source clock is sampled again per page, not frozen at invocation.
        with self.authority() as (_, _, _, _, pub, transport):
            times = iter([1001, 1001, 1001, 4600, 4600])
            result = self.collector(pub, transport).run(1001, max_requests=4, clock=lambda: next(times))
            self.assertEqual('yielded', result.status)
            self.assertEqual(1, result.requests)
            self.assertEqual(1, len(transport.calls))
        with self.authority(policy=RefreshPolicy(fast_interval_seconds=300)) as (_, _, _, _, pub, transport):
            self.assertEqual('yielded', self.collector(pub, transport).run(1001).status)
            self.assertEqual([], transport.calls)
        with self.authority() as (_, _, _, _, pub, transport):
            transport.get = lambda url, etag=None: Response(429, {'retry-after': '60'}, b'')
            ticks = iter([1001, 1001, 1001, 1010])
            with self.assertRaises(RefreshError):
                self.collector(pub, transport).run(1001, clock=lambda: next(ticks))
            self.assertEqual(1070, pub.ledger['backoff_until_utc'])
            self.assertEqual('throttled', pub.ledger['requests'][-1]['outcome'])
            with self.assertRaises(AllowanceUnavailable):
                self.collector(pub, transport).run(1069)
        with self.authority() as (_, _, _, _, pub, transport):
            head = pub.head
            with self.assertRaisesRegex(StateError, 'regress'):
                self.collector(pub, transport).run(999)
            self.assertEqual(head, pub.head)
            self.assertEqual([], transport.calls)

    def test_event_sequences(self):
        # Seeded domain traces, deterministic clocks. Required typed dispositions
        # are checked independently in EACH run; no skipped event counts.
        contract = {'page': 'applied', 'reopen': 'observed_no_mutation', 'lost': 'applied',
                    'clock': 'applied', 'quota': 'observed_no_mutation', 'source': 'observed_no_mutation',
                    'cas': 'observed_no_mutation', 'due': 'observed_no_mutation',
                    'final': 'applied', 'invalid': 'observed_no_mutation'}
        for seed in (19, 71, 20261112):
            dispositions = {event: 0 for event in contract}
            rng = random.Random(seed)
            with self.subTest(seed=seed), self.authority() as (_, source, remote, store, pub, transport):
                model_times = [1000]
                model_age = 1000
                trace = []
                model_pages = []
                model_complete_pages = []
                now = 1001
                def compare():
                    self.assertEqual(model_times, [r['at_utc'] for r in pub.ledger['requests']], (seed, model_times))
                    self.assertEqual(model_age, pub.ledger['accepted']['entries'][0]['record']['source_validated_utc'])
                    self.assertEqual(1000, pub.ledger['last_poll_utc'])
                    self.assertIsNone(pub.ledger['active'])
                    self.assertIsNone(pub.ledger['pending'])
                    ref = pub.ledger.get('catalog_refresh')
                    if ref is not None:
                        journal_raw = store._blob(pub.head, 'catalog-refresh/journals/' + ref['sha256'] + '.json', 1048576)
                        observed = json.loads(journal_raw)
                        if observed['staging'] is not None and observed['staging']['pages']:
                            self.assertEqual(model_pages, [(p['collection'], p['body']['sha256'], p['validatedUtc'])
                                                          for p in observed['staging']['pages']])
                        if observed['current'] is not None:
                            complete_raw = store._blob(pub.head, 'catalog-refresh/objects/' + observed['current']['sha256'] + '.json', 16777216)
                            self.assertEqual(model_complete_pages, [(p['collection'], p['body']['sha256'], p['validatedUtc'])
                                                                   for p in json.loads(complete_raw)['coverage']['pages']])
                transport.failure = KeyboardInterrupt('literal request loss')
                with self.assertRaises(KeyboardInterrupt):
                    self.collector(pub, transport).run(now)
                model_times.append(now)
                dispositions['lost'] += 1
                trace.append(['lost', now, 'applied'])
                compare()
                # A clock event permits recovery, while the lost slot stays used.
                now += 60
                transport.now, transport.failure = now, None
                dispositions['clock'] += 1
                trace.append(['clock', now, 'applied'])
                compare()
                # Required prefix has actual applied pages and restart observations.
                for i in range(4):
                    now += rng.randint(1, 7)
                    transport.now = now
                    dispositions['clock'] += 1
                    trace.append(['clock', now, 'applied'])
                    compare()
                    for _ in range(rng.randint(1, 3)):
                        pub = Publisher(store, pub.running_code)
                        pub.reconcile(None)
                        transport.publisher = pub
                        dispositions['reopen'] += 1
                        trace.append(['reopen', now, 'observed_no_mutation'])
                        compare()
                    collector = self.collector(pub, transport)
                    collector.run(now)
                    model_times.append(now)
                    dispositions['final' if i == 3 else 'page'] += 1
                    collection = COLLECTIONS[i]
                    body = literal_bytes(dict(count=len(transport.data[collection]), next=None, previous=None,
                                              results=transport.data[collection]))
                    model_pages.append((collection, hashlib.sha256(body).hexdigest(), now))
                    if i == 3:
                        model_complete_pages = list(model_pages)
                    trace.append(['final' if i == 3 else 'page', now, 'applied'])
                    compare()
                    expected_pages = i + 1
                    if i < 3:
                        self.assertEqual(expected_pages, len(collector.journal['staging']['pages']))
                    else:
                        self.assertEqual({'countries': [7, 999], 'organizations': [70], 'models': [71, 72], 'sites': [80]},
                                         collector.current()['coverage']['distinctIds'])
                    pub = Publisher(store, pub.running_code)
                    pub.reconcile(None)
                    transport.publisher = pub
                    dispositions['reopen'] += 1
                    trace.append(['reopen', now, 'observed_no_mutation'])
                    compare()
                # One independently selected invalid event uses the last spare
                # metadata slot. Failure is real and applies durable backoff.
                transport.mutate = rng.choice([
                    lambda c, o, p: dict(p, count=999),
                    lambda c, o, p: dict(p, results=[dict(p['results'][0], id=False)])])
                with self.assertRaises(StateError):
                    self.collector(pub, transport).run(now, restart=True)
                model_times.append(now)
                dispositions['invalid'] += 1
                model_pages = []
                trace.append(['invalid', now, 'observed_no_mutation'])
                compare()
                prior_calls = len(transport.calls)
                self.assertEqual('yielded', self.collector(pub, transport).run(now + 1).status)
                dispositions['quota'] += 1
                trace.append(['quota', now + 1, 'observed_no_mutation'])
                compare()
                self.assertEqual(prior_calls, len(transport.calls))
                self.assertEqual('yielded', self.collector(pub, transport).run(4600).status)
                dispositions['due'] += 1
                trace.append(['due', 4600, 'observed_no_mutation'])
                compare()
                stale = self.collector(pub, transport)
                other = Publisher(store, pub.running_code)
                other.reconcile(None)
                # Backoff has expired; real other writer mutates state authority.
                token = other.reserve(other.head, 1400, purpose='version', trigger='manual')
                other.finish_request(other.head, token, 1400, 'success')
                with self.assertRaises(Conflict):
                    stale.run(1400)
                dispositions['cas'] += 1
                trace.append(['cas', 1400, 'observed_no_mutation'])
                pub = Publisher(store, pub.running_code)
                pub.reconcile(None)
                transport.publisher = pub
                model_times.append(1400)
                compare()
                git(source, 'commit', '--allow-empty', '-qm', 'source advances')
                git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
                with self.assertRaisesRegex(StateError, 'stale'):
                    self.collector(pub, transport).run(1401)
                dispositions['source'] += 1
                trace.append(['source', 1401, 'observed_no_mutation'])
                compare()
                self.assertEqual(prior_calls, len(transport.calls))
            self.assertEqual(set(contract), {event for event, count in dispositions.items() if count > 0}, (seed, dispositions))
            self.assertTrue(all(value in ('applied', 'observed_no_mutation') for value in contract.values()))
            print(json.dumps({'seed': seed, 'trace': trace, 'typedDispositions': dispositions,
                              'independentFacts': ['literal pages/counts/IDs/body SHA', 'event request times',
                                                   'source UTC1000', 'last poll1000', 'no active/pending publication']}))

    def test_real_loopback_cli_and_reopen(self):
        requests = []
        data_holder = {}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_GET(self):
                path = urlsplit(self.path).path
                collection = next(c for c, value in PATHS.items() if value == path)
                body = literal_bytes(dict(count=len(data_holder['facts'][collection]), next=None, previous=None,
                                          results=data_holder['facts'][collection]))
                tag = '"' + hashlib.sha256(body).hexdigest() + '"'
                requests.append((self.path, self.headers.get('If-None-Match')))
                self.send_response(304 if self.headers.get('If-None-Match') == tag else 200)
                self.send_header('Date', formatdate(data_holder['now'], usegmt=True))
                self.send_header('Content-Type', 'application/json')
                self.send_header('ETag', tag)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                if self.headers.get('If-None-Match') != tag:
                    self.wfile.write(body)
        # Avoid BaseHTTPRequestHandler adding an uncontrolled second Date.
        Handler.send_response = lambda self, code, message=None: self.send_response_only(code, message)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        origin = 'http://127.0.0.1:' + str(server.server_port)
        data_holder.update(facts=facts(origin), now=1001)
        try:
            with self.authority(real_source=True) as (root, source, remote, store, pub, _):
                live = root / 'live.json'
                live.write_text('null')
                def cli(command, *extra):
                    args = [sys.executable, '-B', str(source / 'tools/refresh_catalog.py'), command,
                            '--remote', str(remote), '--local-http', '--origin', origin, *extra]
                    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
                    self.assertEqual(0, result.returncode, result.stderr.decode())
                    return json.loads(result.stdout)
                for i in range(4):
                    head = store.load()[0]
                    result = cli('collect', '--expected-head', head, '--live-observation', str(live), '--now', '1001')
                    self.assertEqual('complete' if i == 3 else 'partial', result['status'])
                self.assertEqual(4, len(requests))
                self.assertTrue(all(tag is None for _, tag in requests))
                candidate_path = root / 'candidate.json'
                reference_path = root / 'reference.json'
                cli('export', '--output', str(candidate_path))
                cli('export', '--output', str(reference_path), '--reference-inventory')
                raw = candidate_path.read_bytes()
                complete = json.loads(raw)
                self.assertEqual(result['completed']['sha256'], hashlib.sha256(raw).hexdigest())
                self.assertEqual(complete['reference']['models'], json.loads(reference_path.read_bytes())['models'])
                self.assertEqual(4, len(requests))
                # Reopen/default no restart is read-only and consumes no quota.
                head = store.load()[0]
                cli('collect', '--expected-head', head, '--live-observation', str(live), '--now', '1002')
                self.assertEqual(head, store.load()[0])
                self.assertEqual(4, len(requests))
                pub = Publisher(store, pub.running_code)
                pub.reconcile(None)
                slot = pub.reserve(pub.head, 4600, trigger='manual')
                pub.accept_source(pub.head, slot, (launch(1000),), 4600)
                data_holder['now'] = 4601
                cli('collect', '--expected-head', pub.head, '--live-observation', str(live),
                    '--now', '4601', '--restart', '--max-requests', '4')
                self.assertEqual(8, len(requests))
                self.assertTrue(all(tag is not None for _, tag in requests[4:]))
                status = cli('status')
                self.assertLessEqual(status['measure']['ledger_bytes'], 65536)
                self.assertGreater(status['measure']['catalog_blob_bytes'], 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == '__main__':
    unittest.main()
