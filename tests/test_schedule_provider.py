"""Literal LL2 fixtures + real loopback HTTP + actual Git reservation authority.

No live provider, cloud deployment or watch is replaced by a passing claim.
"""
import copy
from datetime import datetime, timezone
from email.utils import format_datetime
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from dataclasses import replace
from decimal import Decimal

from tools.spacefox.catalog import build_catalog
from tools.spacefox.feed import FeedTooLargeError, encode_feed
from tools.spacefox.provider import (LL2Client, Response, ProviderError,
                                    Throttled, bounded_json, normalize_launch, MAX_RESPONSE_BYTES)
from tools.spacefox.publisher import (GitState, Publisher, StateError, LiveRevision,
                                     )
from tools.spacefox.schedule import (TimePrecision, LaunchStatus, TimingState, select_next,
                                    merge_schedule)
from tools.spacefox.wire import build_artifact, validate_feed
from tools.update_feed import update, export_pending

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / 'tests/fixtures/provider/page-normal.json').read_bytes())
NOW = 1794441600  # 2026-11-12T00:00:00Z, independent literal UTC witness.
MODIFIED = 1794268800  # 2026-11-10T00:00:00Z.


def git(path, *args):
    return subprocess.run(['git', '-C', str(path), *args], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout.decode().strip()


def response(document=None, *, now=NOW, status=200, headers=None):
    fields = {'date': format_datetime(datetime.fromtimestamp(now, timezone.utc), usegmt=True),
              'content-type': 'application/json'}
    fields.update(headers or {})
    return Response(status, fields, b'' if document is None else json.dumps(document).encode())


class Responses:
    """Only substitutes LL2; observes durable reservation before every call."""
    def __init__(self, store, items):
        self.store, self.items, self.urls, self.tokens = store, list(items), [], []

    def get(self, url):
        _, ledger = self.store.load()
        reserved = [r for r in ledger['requests'] if r['outcome'] == 'reserved']
        latest = ledger['requests'][-1]
        if (not reserved or latest['outcome'] != 'reserved' or latest['id'] in self.tokens
                or any(r['id'] != latest['id'] and r['at_utc'] + 60 > latest['at_utc'] for r in reserved)):
            raise AssertionError('HTTP lacks a new persisted permission or bypassed crash delay')
        self.tokens.append(latest['id'])
        self.urls.append(url)
        item = self.items.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


class ScheduleProviderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source, self.remote = self.root / 'source', self.root / 'remote.git'
        self.source.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        git(self.source, 'config', 'user.name', 'Provider qualification')
        git(self.source, 'config', 'user.email', 'test@example.invalid')
        git(self.source, 'commit', '--allow-empty', '-qm', 'current source')
        self.code = git(self.source, 'rev-parse', 'HEAD')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.store = GitState(str(self.remote))
        self.store.bootstrap(self.code)
        self.pub = Publisher(self.store, self.code)
        self.pub.reconcile(None)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def client(self, *items, page_size=10):
        self.transport = Responses(self.store, items)
        return LL2Client(self.transport, page_size=page_size)

    def promote(self):
        pending = self.pub.ledger['pending']
        self.pub.reconcile(LiveRevision(pending['generation'], pending['artifact_revision']))

    def test_previously_unseen_organization_or_site_positive(self):
        result = update(self.pub, self.client(response(FIXTURE)), NOW, self.catalog)
        self.assertEqual(result['result'], 'pending')
        self.assertEqual(len(self.transport.urls), 1)
        feed = validate_feed(self.pub.pending_files()['feed.json'])
        launch = feed['launch']
        self.assertEqual(launch['launch_id'], 'll2:launch:00000000-0000-4000-8000-000000000001')
        self.assertEqual(launch['configuration_id'], 'll2:configuration:99999')
        self.assertEqual(launch['operator_id'], 'll2:organization:88888')
        self.assertEqual(launch['site_id'], 'll2:site:77777')
        self.assertEqual(launch['country_id'], 'll2:country:9999')
        self.assertEqual(launch['mission_name'], 'Луна')
        self.assertEqual(launch['source_updated_utc'], MODIFIED)
        self.assertEqual(launch['source_validated_utc'], NOW)
        self.assertEqual(launch['timing']['exact_utc'], 1794484800)
        self.assertEqual(len(feed['unresolvedCatalogIds']), 4)
        self.assertFalse(feed['selection']['worldwideCompleteness'])
        self.assertEqual(feed['dictionaries'], {})
        self.assertEqual(feed['selection']['includedRecords'], 1)
        self.assertLessEqual(result['feedBytes'], 8192)
        self.assertEqual(self.pub.ledger['requests'][0]['outcome'], 'success')
        reopened = Publisher(self.store, self.code)
        self.assertEqual(reopened.schedule, self.pub.schedule)

    def test_previously_unseen_organization_or_site_negative(self):
        bad = copy.deepcopy(FIXTURE)
        bad['results'][0]['launch_service_provider']['id'] = True
        before = self.pub.schedule
        with self.assertRaises(ProviderError):
            update(self.pub, self.client(response(bad)), NOW, self.catalog)
        self.assertEqual(self.pub.schedule, before)
        self.assertIsNone(self.pub.ledger['pending'])
        self.assertEqual(self.pub.ledger['requests'][0]['outcome'], 'failed')
        self.assertGreaterEqual(self.pub.ledger['backoff_until_utc'], NOW + 60)

    def test_successful_unchanged_provider_data_positive(self):
        update(self.pub, self.client(response(FIXTURE)), NOW, self.catalog)
        original = self.pub.schedule.content_revision
        self.promote()
        self.pub = Publisher(self.store, self.code)
        active = self.pub.ledger['active']
        self.pub.reconcile(LiveRevision(active['generation'], active['artifact_revision']))
        update(self.pub, self.client(response(FIXTURE, now=NOW + 3600)), NOW + 3600, self.catalog)
        self.assertEqual(self.pub.schedule.content_revision, original)
        entry = self.pub.schedule.entries[0]
        self.assertEqual(entry.record.source_validated_utc, NOW + 3600)
        self.assertEqual(entry.record.source_updated_utc, MODIFIED)
        self.assertFalse(entry.rescheduled)
        self.assertFalse(entry.stale)

    def test_successful_unchanged_provider_data_negative(self):
        update(self.pub, self.client(response(FIXTURE)), NOW, self.catalog)
        self.promote()
        before = self.pub.schedule
        with self.assertRaises(StateError):
            update(self.pub, self.client(response(FIXTURE, now=NOW - 1)), NOW + 3600, self.catalog)
        self.assertEqual(self.pub.schedule, before)
        self.assertIsNone(self.pub.ledger['pending'])
        # A cache304 carries no record validation, even with a current Date.
        result = update(self.pub, self.client(response(now=NOW + 7200, status=304)), NOW + 7200, self.catalog)
        self.assertEqual(result['result'], 'not_modified_without_record_validation')
        self.assertEqual(self.pub.schedule, before)

    def test_provider_omits_mission_details_positive(self):
        data = copy.deepcopy(FIXTURE)
        data['results'][0].update(mission=None, launch_service_provider=None, rocket=None, pad=None)
        update(self.pub, self.client(response(data)), NOW, self.catalog)
        record = self.pub.schedule.entries[0].record
        self.assertIsNone(record.mission_name)
        self.assertIsNone(record.mission_purpose)
        self.assertIsNone(record.operator_name)
        self.assertIsNone(record.site_id)
        self.assertIsNotNone(select_next(self.pub.schedule).entry)

    def test_provider_omits_mission_details_negative(self):
        a = normalize_launch(FIXTURE['results'][0], NOW)
        b = copy.deepcopy(FIXTURE['results'][0])
        b.update(id='00000000-0000-4000-8000-000000000002', mission={'name': ' ', 'description': ''},
                 launch_service_provider=None, rocket=None, pad=None)
        b['net'] = '2026-11-12T01:00:00Z'
        b['window_start'] = b['net']
        record = normalize_launch(b, NOW)
        state = merge_schedule(self.pub.schedule, (a, record), NOW)
        chosen = select_next(state).entry.record
        self.assertEqual(chosen.launch_id.value, '00000000-0000-4000-8000-000000000002')
        self.assertIsNone(chosen.mission_name)
        self.assertIsNone(chosen.configuration_name)
        self.assertIsNone(chosen.operator_name)

    def test_precision_and_started_phases_positive(self):
        source = FIXTURE['results'][0]
        for precision in ({'id': 1, 'name': 'Minute', 'abbrev': 'MIN'},
                          {'id': 3, 'name': 'Morning', 'abbrev': 'AM', 'description': 'Expected in the morning (local time).'},
                          {'id': 5, 'name': 'Day', 'abbrev': 'DAY'},
                          {'id': 17, 'name': 'Future precision', 'abbrev': 'NEW'}, None):
            row = copy.deepcopy(source)
            row['net_precision'] = precision
            row['window_start'] = row['window_end'] = None
            record = normalize_launch(row, NOW)
            self.assertEqual(record.timing.precision, TimePrecision.SOURCE_COARSE)
            self.assertEqual(record.timing.nominal_utc, 1794484800)
            self.assertEqual(record.timing.source_net, '2026-11-12T12:00:00Z')
            self.assertIsNone(record.timing.exact_utc)
            self.assertIsNone(record.timing.date_utc)
            if precision is not None and precision['id'] == 3:
                self.assertEqual(record.timing.source_precision_description, 'Expected in the morning (local time).')
            self.assertIsNone(record.timing.window_start_utc)
            self.assertEqual(select_next(merge_schedule(self.pub.schedule, (record,), NOW)).timing_state, TimingState.UNCERTAIN)
        for code, name in ((6, 'In Flight'), (9, 'Payload Deployed')):
            row = copy.deepcopy(source)
            row['status'] = dict(id=code, name=name)
            record = normalize_launch(row, NOW)
            self.assertEqual(record.status, LaunchStatus.STARTED)
            self.assertEqual(record.source_status_id, code)
            self.assertEqual(record.source_status_name, name)
            self.assertIsNone(select_next(merge_schedule(self.pub.schedule, (record,), NOW)).entry)

    def test_precision_and_started_phases_negative(self):
        for changes in ({'net': '2026-11-12'}, {'net': '2026-11-12T12:00:00'},
                        {'net_precision': {'id': True, 'name': 'Second', 'abbrev': 'SEC'}},
                        {'window_end': '2026-11-11T00:00:00Z'},
                        {'last_updated': '2026-11-13T00:00:00Z'}):
            row = copy.deepcopy(FIXTURE['results'][0]); row.update(changes)
            with self.subTest(changes=changes), self.assertRaises(ProviderError):
                normalize_launch(row, NOW)
        row = copy.deepcopy(FIXTURE['results'][0]); row['net'] = '2026-11-12T12:00:00.123456Z'
        self.assertIsNone(normalize_launch(row, NOW).timing.exact_utc)
        # An elapsed exact clock never changes the provider phase.
        record = normalize_launch(FIXTURE['results'][0], NOW)
        self.assertEqual(select_next(merge_schedule(self.pub.schedule, (record,), NOW + 50000)).timing_state,
                         TimingState.AWAITING_UPDATE)

    def test_due_no_fetch_and_throttle(self):
        update(self.pub, self.client(response(FIXTURE)), NOW, self.catalog)
        self.promote()
        before = self.pub.head
        result = update(self.pub, self.client(), NOW + 3599, self.catalog)
        self.assertEqual(result['result'], 'not_due')
        self.assertEqual(self.transport.urls, [])
        self.assertEqual(self.pub.head, before)
        with self.assertRaises(Throttled):
            update(self.pub, self.client(response(status=429, headers={'retry-after': '7200'})), NOW + 3600, self.catalog)
        self.assertEqual(self.pub.ledger['backoff_until_utc'], NOW + 10800)
        self.assertEqual(self.pub.ledger['requests'][-1]['outcome'], 'throttled')
        self.pub = Publisher(self.store, self.code)
        active = self.pub.ledger['active']
        self.pub.reconcile(LiveRevision(active['generation'], active['artifact_revision']))
        result = update(self.pub, self.client(), NOW + 7200, self.catalog)
        self.assertEqual(result['result'], 'not_due')
        self.assertEqual(self.transport.urls, [])
        self.assertEqual(self.pub.schedule.entries[0].record.source_validated_utc, NOW)

    def test_pagination_and_retained_detail_positive(self):
        first, second = copy.deepcopy(FIXTURE), copy.deepcopy(FIXTURE)
        client = self.client(page_size=1)
        first.update(count=2, next=client.first_url + '&offset=1')
        second['count'] = 2
        second['results'][0]['id'] = '00000000-0000-4000-8000-000000000002'
        second['results'][0]['net'] = second['results'][0]['window_start'] = '2026-11-12T01:00:00Z'
        client.transport.items = [response(first), response(second)]
        result = update(self.pub, client, NOW, self.catalog)
        self.assertTrue(result['traversal']['complete'])
        self.assertEqual(result['requests'], 2)
        self.assertEqual(select_next(self.pub.schedule).entry.record.launch_id.value,
                         '00000000-0000-4000-8000-000000000002')
        self.promote()
        # Omitted A is explicitly confirmed completed through its stable-ID detail.
        detail = copy.deepcopy(FIXTURE['results'][0]); detail['status'] = {'id': 3, 'name': 'Launch Successful'}
        detail['last_updated'] = '2026-11-12T00:30:00Z'
        remaining = copy.deepcopy(second); remaining['count'] = 1
        result = update(self.pub, self.client(response(remaining, now=NOW + 3600), response(detail, now=NOW + 3600)),
                        NOW + 3600, self.catalog)
        self.assertEqual(result['requests'], 2)
        self.assertIn('/launches/00000000-0000-4000-8000-000000000001/', self.transport.urls[1])
        by_id = {e.record.launch_id.value: e.record for e in self.pub.schedule.entries}
        self.assertEqual(by_id[detail['id']].status, LaunchStatus.COMPLETED)

    def test_pagination_partial_and_failure_negative(self):
        first = copy.deepcopy(FIXTURE)
        client = self.client(page_size=1)
        first.update(count=2, next=client.first_url + '&offset=1')
        client.transport.items = [response(first)]
        result = update(self.pub, client, NOW, self.catalog, max_pages=1)
        self.assertFalse(result['traversal']['complete'])
        self.assertEqual(result['traversal']['reportedCount'], 2)
        self.assertEqual(result['traversal']['receivedUpcoming'], 1)
        self.promote()
        before = self.pub.schedule
        # Foreign pagination is refused without an outbound call to that host.
        first['next'] = 'https://example.invalid/steal'
        with self.assertRaises(ProviderError):
            update(self.pub, self.client(response(first, now=NOW + 3600), page_size=1), NOW + 3600, self.catalog)
        self.assertEqual(len(self.transport.urls), 1)
        self.assertEqual(self.pub.schedule, before)
        self.assertIsNone(self.pub.ledger['pending'])

    def test_strict_parse_and_invalid_wire_negative(self):
        for raw in (b'{"count":1,"count":2}', b'{"a":NaN}', b'[' * 33 + b']' * 33,
                    b'{}' * (MAX_RESPONSE_BYTES // 2 + 1), '{}'.encode('utf-16')):
            with self.subTest(length=len(raw)), self.assertRaises(ProviderError):
                bounded_json(raw)
        update(self.pub, self.client(response(FIXTURE)), NOW, self.catalog)
        raw = self.pub.pending_files()['feed.json']
        doc = json.loads(raw)
        doc['schemaVersion'] = 2
        with self.assertRaises(ValueError):
            validate_feed(encode_feed(doc))
        doc = json.loads(raw); doc['launch']['timing']['exact_utc'] = True
        with self.assertRaises(ValueError):
            validate_feed(encode_feed(doc))
        with self.assertRaises(ValueError):
            validate_feed(raw + b' ')
        doc = json.loads(raw); doc['catalogDigest'] = 'f' * 64
        with self.assertRaises(ValueError):
            validate_feed(encode_feed(doc))

    def test_regressing_content_and_overflow_negative(self):
        update(self.pub, self.client(response(FIXTURE)), NOW, self.catalog)
        original_publisher = validate_feed(self.pub.pending_files()['feed.json'])['publisher']
        self.promote()
        before = self.pub.schedule
        old = copy.deepcopy(FIXTURE)
        old['results'][0].update(last_updated='2026-11-09T00:00:00Z', mission={'name': 'Conflicting old body'})
        with self.assertRaises((StateError, ValueError)):
            update(self.pub, self.client(response(old, now=NOW + 3600)), NOW + 3600, self.catalog)
        self.assertEqual(self.pub.schedule, before)
        huge = copy.deepcopy(FIXTURE)
        huge['results'][0].update(last_updated='2026-11-12T01:00:00Z',
                                  mission={'name': '長' * 80, 'description': '🚀' * 1025})
        with self.assertRaises(ProviderError):
            update(self.pub, self.client(response(huge, now=NOW + 7200)), NOW + 7200, self.catalog)
        self.assertEqual(self.pub.schedule, before)
        self.assertIsNone(self.pub.ledger['pending'])
        oversized = replace(before.entries[0].record, mission_purpose='x' * 9000)
        state = merge_schedule(type(before)(), (oversized,), NOW)
        with self.assertRaises(FeedTooLargeError):
            build_artifact(state, self.catalog, NOW, publisher=original_publisher)

    def test_data_artifact_is_deterministic_complete_and_recoverable(self):
        known = copy.deepcopy(FIXTURE)
        known['results'][0]['rocket']['configuration']['id'] = 121
        known['results'][0]['launch_service_provider']['id'] = 121
        update(self.pub, self.client(response(known)), NOW, self.catalog)
        first = self.pub.pending_files()
        feed = validate_feed(first['feed.json'])
        self.assertIn('ll2:configuration:121', feed['dictionaries'])
        self.assertIn('ll2:organization:121', feed['dictionaries'])
        self.assertNotEqual(feed['dictionaries']['ll2:configuration:121']['kind'],
                            feed['dictionaries']['ll2:organization:121']['kind'])
        self.assertTrue(all(row['visual'] is None for row in feed['dictionaries'].values()))
        self.assertEqual(set(first), {'feed.json', feed['catalogPath']})
        self.assertEqual(hashlib.sha256(first[feed['catalogPath']]).hexdigest(), feed['catalogDigest'])
        result, _digest = build_artifact(self.pub.schedule, self.catalog, NOW,
                                       publisher=feed['publisher'],
                                       traversal=feed['providerTraversal'])
        self.assertEqual(result, first)
        self.pub = Publisher(self.store, self.code)
        self.assertEqual(self.pub.pending_files(), first)
        export = self.root / 'artifact'
        self.assertEqual(export_pending(self.pub, export), 2)
        self.assertEqual((export / 'feed.json').read_bytes(), first['feed.json'])

    def test_actual_catalog_known_site_decimal_precision(self):
        known = copy.deepcopy(FIXTURE)
        row = known['results'][0]
        row['rocket']['configuration']['id'] = 164
        row['launch_service_provider']['id'] = 121
        row['pad']['id'] = 65
        row['pad']['country']['id'] = 2
        update(self.pub, self.client(response(known)), NOW, self.catalog)
        raw = self.pub.pending_files()['feed.json']
        feed = validate_feed(raw)
        site = feed['dictionaries']['ll2:site:65']
        self.assertIsNone(site['position'])
        self.assertEqual(site['sourcePosition'], {'encoding': 'decimal-text-v1',
            'latitude': '-39.262833', 'longitude': '177.864469', 'units': 'degrees',
            'qualification': 'unverified-reference'})
        self.assertLessEqual(len(raw), 8192)
        from tools.spacefox.wire import _source_position, _validate_source_position
        self.assertIsNone(_source_position(None))
        precise = _source_position({'latitude': Decimal('-0.000000000000'),
            'longitude': Decimal('179.0000000000000000000001'), 'units': 'degrees',
            'qualification': 'unverified-reference'})
        self.assertEqual(precise['latitude'], '-0E-12')
        self.assertEqual(Decimal(precise['latitude']).as_tuple(), Decimal('-0.000000000000').as_tuple())
        self.assertEqual(precise['longitude'], '179.0000000000000000000001')
        _validate_source_position(precise)
        for invalid in ('NaN', '91', '00', '1.', '-39.262833x', -39.262833):
            bad = copy.deepcopy(feed)
            bad['dictionaries']['ll2:site:65']['sourcePosition']['latitude'] = invalid
            # Recompute only the independently specified catalog hash so the
            # position validator, not a stale digest, must reject this field.
            dictionary = {'schemaVersion': 1, 'catalogVersion': bad['catalogRevision'],
                          'qualification': 'publisher-metadata-only', 'entries': bad['dictionaries'],
                          'unresolved': bad['unresolvedCatalogIds']}
            digest = hashlib.sha256(json.dumps(dictionary, ensure_ascii=False, sort_keys=True,
                                                separators=(',', ':')).encode()).hexdigest()
            bad['catalogDigest'] = digest; bad['catalogPath'] = f'catalogs/{digest}.json'
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                validate_feed(encode_feed(bad))

    def test_artifact_export_refuses_existing_or_symlink_destination(self):
        update(self.pub, self.client(response(FIXTURE)), NOW, self.catalog)
        before, files = self.pub.head, self.pub.pending_files()
        existing = self.root / 'existing'; existing.mkdir()
        marker = existing / 'keep.txt'; marker.write_text('retained')
        link = self.root / 'link'; link.symlink_to(existing, target_is_directory=True)
        for target in (existing, link):
            with self.assertRaises(FileExistsError): export_pending(self.pub, target)
            self.assertEqual(marker.read_text(), 'retained')
            self.assertEqual(self.pub.head, before)
            self.assertEqual(self.pub.pending_files(), files)
        self.assertEqual(len(self.transport.urls), 1)

    def test_terminal_retention_archive_and_unresolved_overflow(self):
        from dataclasses import replace
        first = normalize_launch(FIXTURE['results'][0], NOW)
        terminal = replace(first, status=LaunchStatus.COMPLETED, source_status_id=3, source_status_name='Launch Successful')
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (terminal,), NOW)
        token = self.pub.reserve(self.pub.head, NOW + 86400, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (), NOW + 86400)
        self.assertEqual(self.pub.schedule.entries, ())
        self.assertEqual(self.store.archived(first.launch_id).record, terminal)
        reopened = Publisher(self.store, self.code); reopened.reconcile(None)
        # Old terminal identity cannot be resurrected by a fresh200/pending body.
        token = reopened.reserve(reopened.head, NOW + 86401, trigger='manual')
        with self.assertRaises(StateError):
            reopened.accept_source(reopened.head, token, (replace(first, source_validated_utc=NOW + 86401),), NOW + 86401)
        self.assertEqual(reopened.schedule.entries, ())
        reopened.finish_request(reopened.head, token, NOW + 86401, 'failed')
        # A genuinely unseen old-authored launch remains valid after compaction.
        new = replace(first, launch_id=replace(first.launch_id, value='00000000-0000-4000-8000-000000000002'),
                      source_validated_utc=NOW + 87000)
        token = reopened.reserve(reopened.head, NOW + 87000, trigger='manual')
        reopened.accept_source(reopened.head, token, (new,), NOW + 87000)
        self.assertEqual(reopened.schedule.entries[0].record, new)
        # Omission is never pruning: unresolved age survives even after90days.
        token = reopened.reserve(reopened.head, NOW + 90 * 86400, trigger='manual')
        reopened.accept_source(reopened.head, token, (), NOW + 90 * 86400)
        self.assertEqual(reopened.schedule.entries[0].record.source_validated_utc, NOW + 87000)
        self.assertTrue(reopened.schedule.entries[0].stale)
        # Explicit bound:129unresolved IDs is rejected by the actual Git write.
        token = reopened.reserve(reopened.head, NOW + 91 * 86400, trigger='manual')
        before = reopened.schedule
        values = tuple(replace(new, launch_id=replace(new.launch_id, value=str(i)),
                               source_validated_utc=NOW + 91 * 86400) for i in range(129))
        with self.assertRaises(StateError):
            reopened.accept_source(reopened.head, token, values, NOW + 91 * 86400)
        self.assertEqual(reopened.schedule, before)
        self.assertIsNotNone(self.store.archived(first.launch_id))

    def test_real_http_reservation_redirect_size_timeout(self):
        payloads = [(200, json.dumps(FIXTURE).encode(), {}),
                    (302, b'', {'Location': 'http://127.0.0.1:1/forbidden'}),
                    (200, b'x' * (MAX_RESPONSE_BYTES + 1), {}),
                    (200, json.dumps(FIXTURE).encode(), {})]
        calls, permissions = [], []
        store = self.store

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                _, ledger = store.load()
                permissions.append([r['outcome'] for r in ledger['requests']][-1])
                code, body, headers = payloads.pop(0)
                self.send_response(code)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                for key, value in headers.items(): self.send_header(key, value)
                self.end_headers()
                try: self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError): pass

            def log_message(self, *args): pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        origin = f'http://127.0.0.1:{server.server_port}'
        try:
            # Direct real HTTP Date is the server clock; logical time follows it.
            now = int(datetime.now(timezone.utc).timestamp()) + 1
            client = LL2Client(origin=origin, local_http=True)
            update(self.pub, client, now, self.catalog)
            self.promote()
            before = self.pub.schedule
            for at in (now + 3600, now + 7200):
                with self.assertRaises(ProviderError): update(self.pub, client, at, self.catalog)
                self.assertEqual(self.pub.schedule, before)
            self.assertEqual(permissions, ['reserved'] * 3)
            self.assertEqual(len(calls), 3)  #302was not followed.
            with patch('tools.spacefox.provider.TOTAL_TIMEOUT_SECONDS', 0.001):
                with self.assertRaises(ProviderError): update(self.pub, client, now + 10800, self.catalog)
            self.assertEqual(self.pub.ledger['requests'][-1]['outcome'], 'failed')
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_cli_end_to_end_actual_clean_checkout(self):
        # Copy the actual portable runtime and its pinned catalog inputs, commit
        # them, and execute the public CLI in a separate process. No .agents.
        for rel in ('tools/spacefox', 'tools/update_feed.py', 'schemas'):
            src, dst = ROOT / rel, self.source / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir(): shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__'))
            else: shutil.copyfile(src, dst)
        for rel in self.catalog['inputDigests']:
            dst = self.source / rel; dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / rel, dst)
        (self.source / 'catalog').mkdir(exist_ok=True)
        shutil.copyfile(ROOT / 'catalog/source.json', self.source / 'catalog/source.json')
        git(self.source, 'add', '.')
        git(self.source, 'commit', '-qm', 'actual portable producer')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        # Existing state is adopted explicitly by the CLI before permission.
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200); self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps(FIXTURE).encode())
            def log_message(self, *args): pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            now = int(datetime.now(timezone.utc).timestamp()) + 1
            command = [sys.executable, '-B', str(self.source / 'tools/update_feed.py'), '--remote', str(self.remote),
                       '--expected-base', self.pub.head, '--origin', f'http://127.0.0.1:{server.server_port}',
                       '--local-http', '--now', str(now), 'run', '--output', str(self.root / 'cli-output')]
            ran = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(ran.returncode, 0, ran.stderr.decode())
            result = json.loads(ran.stdout)
            self.assertEqual(result['result'], 'pending')
            self.assertLessEqual(len((self.root / 'cli-output/feed.json').read_bytes()), 8192)
            self.assertEqual(result['exportedFiles'], 2)
            # Recovery exports durable exact pending bytes with zero provider call.
            before_calls = len(self.store.load()[1]['requests'])
            command[command.index('--expected-base') + 1] = result['head']
            command[command.index(str(self.root / 'cli-output'))] = str(self.root / 'cli-recovered')
            recovered = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(recovered.returncode, 0, recovered.stderr.decode())
            self.assertEqual(json.loads(recovered.stdout)['result'], 'recovered_pending')
            self.assertEqual((self.root / 'cli-recovered/feed.json').read_bytes(), (self.root / 'cli-output/feed.json').read_bytes())
            self.assertEqual(len(self.store.load()[1]['requests']), before_calls)
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def test_crash_after_reserved_http_and_shared_quota(self):
        class CrashAfterSend:
            calls = 0
            def get(inner, url):
                inner.calls += 1
                _, ledger = self.store.load()
                self.assertEqual(ledger['requests'][-1]['outcome'], 'reserved')
                raise SystemExit('lost runner after request was sent')
        crash = CrashAfterSend()
        with self.assertRaises(SystemExit):
            update(self.pub, LL2Client(crash), NOW, self.catalog)
        self.assertEqual(crash.calls, 1)
        self.assertEqual(self.store.load()[1]['requests'][0]['outcome'], 'reserved')
        self.pub = Publisher(self.store, self.code); self.pub.reconcile(None)
        blocked = self.client(response(FIXTURE))
        with self.assertRaises(StateError):
            update(self.pub, blocked, NOW + 1, self.catalog, trigger='retry')
        self.assertEqual(blocked.transport.urls, [])
        # The uncertain slot is never refunded. Catalog/version uses same ledger.
        token = self.pub.reserve(self.pub.head, NOW + 60, purpose='catalog', trigger='manual')
        self.pub.finish_request(self.pub.head, token, NOW + 60, 'success')
        for _ in range(13):
            update(self.pub, self.client(response(status=304, now=NOW + 60)), NOW + 60, self.catalog, trigger='manual')
        self.assertEqual(len(self.pub.ledger['requests']), 15)
        blocked = self.client()
        with self.assertRaises(StateError):
            update(self.pub, blocked, NOW + 60, self.catalog, trigger='manual')
        self.assertEqual(blocked.transport.urls, [])
        self.assertEqual(self.pub.schedule.entries, ())

    def test_ordered_provider_events_preserve_per_record_facts(self):
        a = copy.deepcopy(FIXTURE)
        moved = copy.deepcopy(a)
        moved['results'][0].update(net='2026-11-12T12:20:00Z', window_start='2026-11-12T12:20:00Z',
                                   last_updated='2026-11-12T01:00:00Z')
        b = copy.deepcopy(a)
        b['results'][0].update(id='00000000-0000-4000-8000-000000000002',
                               net='2026-11-13T12:00:00Z', window_start='2026-11-13T12:00:00Z',
                               window_end='2026-11-13T13:00:00Z')
        # Independent literal model checkpoints, never derived from SUT state.
        events = [
            ('origin', 0, a, 'pending', NOW, 1794484800, False, False),
            ('not_due', 1, None, 'not_due', NOW, 1794484800, False, False),
            ('move', 3600, moved, 'pending', NOW + 3600, 1794486000, True, False),
            ('omit', 14400, b, 'pending', NOW + 3600, 1794486000, True, True),
            ('cache304', 18000, None, 'not_modified_without_record_validation', NOW + 3600, 1794486000, True, True),
            ('origin_renewal', 21600, moved, 'pending', NOW + 21600, 1794486000, True, False),
        ]
        dispositions = {}
        for name, offset, body, expected, validated, target, rescheduled, stale in events:
            now = NOW + offset
            before = self.pub.head
            client = self.client() if name == 'not_due' else self.client(response(body, now=now, status=304 if name == 'cache304' else 200))
            actual = update(self.pub, client, now, self.catalog, detail_limit=0)
            self.assertEqual(actual['result'], expected, name)
            entry = next(e for e in self.pub.schedule.entries if e.record.launch_id.value.endswith('000001'))
            self.assertEqual((entry.record.source_validated_utc, entry.record.timing.exact_utc,
                              entry.rescheduled, entry.stale), (validated, target, rescheduled, stale), name)
            if name == 'not_due':
                self.assertEqual(self.pub.head, before)
                self.assertEqual(client.transport.urls, [])
                disposition = 'observed_no_mutation'
            else:
                self.assertEqual(len(client.transport.urls), 1)
                disposition = 'applied'
            dispositions[name] = disposition
            if actual['result'] == 'pending': self.promote()
            # Actual process-style reopen/reconcile after every event.
            self.pub = Publisher(self.store, self.code)
            active = self.pub.ledger['active']
            self.pub.reconcile(None if active is None else LiveRevision(active['generation'], active['artifact_revision']))
        self.assertEqual(dispositions, {'origin': 'applied', 'not_due': 'observed_no_mutation',
            'move': 'applied', 'omit': 'applied', 'cache304': 'applied', 'origin_renewal': 'applied'})
        other = next(e for e in self.pub.schedule.entries if e.record.launch_id.value.endswith('000002'))
        self.assertEqual(other.record.source_validated_utc, NOW + 14400)
        self.assertFalse(other.rescheduled)

    def test_omitted_unknown_record_never_renews_from_other_origin(self):
        initial = copy.deepcopy(FIXTURE)
        initial['results'][0].update(net=None, net_precision=None, window_start=None, window_end=None,
                                    status={'id': 999, 'name': 'Unknown future phase'})
        update(self.pub, self.client(response(initial)), NOW, self.catalog)
        self.promote()
        other = copy.deepcopy(FIXTURE)
        other['results'][0]['id'] = '00000000-0000-4000-8000-000000000002'
        update(self.pub, self.client(response(other, now=NOW + 14400)), NOW + 14400,
               self.catalog, detail_limit=0)
        by_id = {e.record.launch_id.value: e for e in self.pub.schedule.entries}
        old = by_id['00000000-0000-4000-8000-000000000001']
        self.assertEqual(old.record.source_validated_utc, NOW)
        self.assertEqual(old.record.status, LaunchStatus.UNKNOWN)
        self.assertEqual(old.record.source_status_id, 999)
        self.assertTrue(old.stale)
        self.assertIsNone(old.record.timing.exact_utc)
        self.assertEqual(by_id['00000000-0000-4000-8000-000000000002'].record.source_validated_utc, NOW + 14400)
        self.assertEqual(len(by_id), 2)

    def test_atomic_source_pending_survives_lost_commit_acknowledgement(self):
        original_write = self.store.write
        lost = False
        def lose_ack(expected, document, new_files=None):
            nonlocal lost
            result = original_write(expected, document, new_files)
            if not lost and document['pending'] is not None:
                lost = True
                raise RuntimeError('runner lost durable candidate acknowledgement')
            return result
        self.store.write = lose_ack
        with self.assertRaises(StateError):
            update(self.pub, self.client(response(FIXTURE)), NOW, self.catalog)
        self.assertTrue(lost)
        self.store.write = original_write
        reopened = Publisher(self.store, self.code)
        self.assertEqual(reopened.reconcile(None), 'retry_pending')
        self.assertEqual(reopened.ledger['requests'][-1]['outcome'], 'success')
        self.assertEqual(reopened.schedule.entries[0].record.source_validated_utc, NOW)
        feed = validate_feed(reopened.pending_files()['feed.json'])
        self.assertEqual(feed['launch']['source_validated_utc'], NOW)
        self.assertEqual(reopened.ledger['pending']['generation'], 1)
        self.assertEqual(export_pending(reopened, self.root / 'recovered-after-ack-loss'), 2)
        self.assertEqual(len(self.transport.urls), 1)

    def test_retirement_longevity_crosses_128_events_without_active_growth(self):
        source = normalize_launch(FIXTURE['results'][0], NOW)
        for batch in range(9):
            now = NOW + batch * 86400
            records = tuple(replace(source, launch_id=replace(source.launch_id,
                             value=f'00000000-0000-4000-8000-{batch * 16 + i + 1:012d}'),
                             source_validated_utc=now, status=LaunchStatus.COMPLETED,
                             source_status_id=3, source_status_name='Launch Successful') for i in range(16))
            token = self.pub.reserve(self.pub.head, now, trigger='manual')
            self.pub.accept_source(self.pub.head, token, records, now)
            self.assertEqual(len(self.pub.schedule.entries), 16)
            self.assertTrue(all(e.record.source_validated_utc == now for e in self.pub.schedule.entries))
        measure = self.store.measure()
        self.assertEqual(measure['archive_records'], 128)
        self.assertLessEqual(measure['ledger_bytes'], 65536)
        self.assertGreater(measure['archive_blob_bytes'], 65536)
        self.assertEqual(self.store.archived(source.launch_id).record.source_updated_utc, MODIFIED)
        print('PROVIDER_RETENTION_MEASUREMENT ' + json.dumps(measure, sort_keys=True))

    def test_fractional_source_modification_is_lossless_and_monotonic(self):
        a = copy.deepcopy(FIXTURE['results'][0]); a['last_updated'] = '2026-11-10T00:00:00.123456Z'
        first = normalize_launch(a, NOW)
        self.assertEqual(first.source_updated_iso, '2026-11-10T00:00:00.123456Z')
        self.assertEqual(first.source_updated_subsecond, 123456)
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (first,), NOW)
        b = copy.deepcopy(a); b['last_updated'] = '2026-11-10T00:00:00.123457Z'
        b['mission']['name'] = 'New subsecond revision'
        second = normalize_launch(b, NOW + 3600)
        token = self.pub.reserve(self.pub.head, NOW + 3600, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (second,), NOW + 3600)
        self.assertEqual(self.pub.schedule.entries[0].record.source_updated_subsecond, 123457)
        token = self.pub.reserve(self.pub.head, NOW + 7200, trigger='manual')
        with self.assertRaises(StateError):
            self.pub.accept_source(self.pub.head, token, (replace(first, source_validated_utc=NOW + 7200),), NOW + 7200)
        self.assertEqual(self.pub.schedule.entries[0].record.source_updated_subsecond, 123457)
        with self.assertRaises(ValueError):
            replace(second, source_updated_iso='2026-11-10T00:00:00.123456Z')


if __name__ == '__main__':
    unittest.main()
