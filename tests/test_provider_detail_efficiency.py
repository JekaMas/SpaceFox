"""Real disposable Git/loopback witnesses; no live provider or publication.

The exact g9 bundle is a captured durable authority. Its upcoming reconstruction
is explicitly authored, and the HTTP server is the only substituted service.
"""
import copy
from contextlib import contextmanager
from dataclasses import replace
from datetime import datetime, timezone
from email.utils import format_datetime
import hashlib
import gzip
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import subprocess
import threading
import unittest
from urllib.parse import parse_qs, urlsplit

from tests import test_schedule_provider as support
from tools.spacefox.provider import LL2Client, ProviderError, MAX_RESPONSE_BYTES
from tools.spacefox.publisher import GitState, Publisher, LiveRevision
from tools.spacefox.schedule import LaunchStatus
from tools.spacefox.wire import build_artifact
from tools.spacefox.visual_bridge import build_artifact as build_visual_artifact
from tools.update_feed import update

FIXTURES = Path(__file__).parent / 'fixtures/provider/detail-efficiency'
G9 = 'ec1dd79d57ef89d60a1606ac19f6f0ab91738205'
ANCHOR = '5dd986f4cb6fc1bf4df96a89675c53d5625da425'
OLD_ID = 'd66590ab-b273-47ff-b85a-608b62851b4b'
NOW = support.NOW


def row(number, status=1, mode='normal', modified='2026-11-10T00:00:00Z'):
    value = copy.deepcopy(support.FIXTURE['results'][0])
    value.update(id=f'00000000-0000-4000-8000-{number:012d}',
                 response_mode=mode, status={'id': status, 'name': f'Sourced phase {status}'},
                 last_updated=modified)
    return value


class DetailEfficiencyTest(unittest.TestCase):
    setUpClass = classmethod(support.ScheduleProviderTest.setUpClass.__func__)
    setUp = support.ScheduleProviderTest.setUp
    tearDown = support.ScheduleProviderTest.tearDown
    promote = support.ScheduleProviderTest.promote

    @contextmanager
    def server(self, rows, *, now=NOW, details=None, detail_status=200, detail_headers=None, raw=None):
        calls, permissions = [], []
        state = {'rows': rows, 'now': now, 'details': details or {}, 'status': detail_status,
                 'headers': detail_headers or {}, 'raw': raw}
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                parsed = urlsplit(self.path)
                upcoming = parsed.path.endswith('/upcoming/')
                calls.append(self.path)
                ledger = owner.store.load()[1]
                permissions.append(ledger['requests'][-1]['outcome'])
                owner.assertEqual(permissions[-1], 'reserved')
                self.send_response_only(200 if upcoming else state['status'])
                self.send_header('Content-Type', 'application/json')
                headers = {'Date': format_datetime(datetime.fromtimestamp(state['now'], timezone.utc), usegmt=True)}
                if not upcoming:
                    headers.update(state['headers'])
                for name, value in headers.items():
                    if value is not None:
                        self.send_header(name, value)
                if upcoming:
                    offset = int(parse_qs(parsed.query).get('offset', ['0'])[0])
                    page_rows = state['rows'][offset:offset + 10]
                    next_url = None if offset + len(page_rows) == len(state['rows']) else (
                        origin + '/2.3.0/launches/upcoming/?mode=normal&limit=10&ordering=net&include_suborbital=true&hide_recent_previous=false&offset=' + str(offset + 10))
                    body = json.dumps({'count': len(state['rows']), 'next': next_url,
                                       'previous': None, 'results': page_rows}).encode()
                else:
                    identity = parsed.path.split('/')[-2]
                    body = state['raw'] if state['raw'] is not None else json.dumps(state['details'].get(identity)).encode()
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                try:
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError):
                    pass  # The production bounded reader may reject before EOF.

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        origin = f'http://127.0.0.1:{server.server_port}'
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield LL2Client(origin=origin, local_http=True), state, calls, permissions
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def reopen(self):
        self.pub = Publisher(self.store, self.code)
        active = self.pub.ledger['active']
        self.pub.reconcile(None if active is None else LiveRevision(active['generation'], active['artifact_revision']))

    def seed(self, values):
        with self.server(values) as (client, _, calls, permissions):
            update(self.pub, client, NOW, self.catalog, detail_limit=0)
            self.assertEqual(len(calls), 1)
            self.assertEqual(permissions, ['reserved'])
        self.promote()

    def test_exact_g9_terminal_omission_issues_only_two_primary_requests(self):
        provenance = json.loads((FIXTURES / 'provenance.json').read_text())
        for name, digest in provenance['digests'].items():
            self.assertEqual(hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest(), digest)
        self.store.close()
        captured = self.root / 'captured.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(captured)], check=True)
        support.git(captured, 'fetch', '-q', str(FIXTURES / 'g9.bundle'),
                    'refs/remotes/origin/feed-state:refs/heads/feed-state',
                    'refs/tags/spacefox-state-bootstrap-v1:refs/tags/spacefox-state-bootstrap-v1')
        support.git(self.source, 'push', '-q', str(captured), 'HEAD:refs/heads/main')
        self.store = GitState(str(captured))
        self.assertEqual(self.store.load()[0], G9)
        self.assertEqual(support.git(captured, 'rev-parse', 'refs/tags/spacefox-state-bootstrap-v1'), ANCHOR)
        self.pub = Publisher(self.store, self.code)
        self.assertEqual(self.pub.ledger['accepted'], json.loads((FIXTURES / 'accepted-g9.json').read_text()))
        self.pub.adopt_code(self.pub.head)  # Local test source only; captured history stays exact.
        self.reopen()
        original = next(e for e in self.pub.schedule.entries if e.record.launch_id.value == OLD_ID)
        self.assertEqual((original.record.status, original.record.source_status_id,
                          original.record.source_validated_utc), (LaunchStatus.COMPLETED, 3, 1794481322))
        at = 1794488575  # One hour after g9; the old validation is not renewed.
        with self.server(json.loads((FIXTURES / 'upcoming-projection.json').read_text()), now=at,
                         detail_status=500) as (client, _, calls, permissions):
            result = update(self.pub, client, at, self.catalog,
                            artifact_builder=lambda *args, **kwargs: build_visual_artifact(
                                *args, **kwargs, root=support.ROOT), artifact_profile='visual-v2')
            print('DETAIL_G9_HTTP ' + json.dumps(calls), flush=True)
        self.assertEqual(result['result'], 'pending')
        self.assertEqual(result['requests'], 2)
        self.assertEqual(result['traversal']['detailRequests'], 0)
        self.assertEqual(result['detailFailures'], [])
        self.assertEqual(len(calls), 2)
        self.assertTrue(all('/upcoming/' in url for url in calls))
        self.assertEqual(permissions, ['reserved', 'reserved'])
        self.assertEqual(len(self.pub.schedule.entries), 21)
        self.assertEqual(next(e for e in self.pub.schedule.entries if e.record.launch_id.value == OLD_ID), original)
        self.assertEqual(self.pub.ledger['selection_validated_utc'], at)
        self.assertEqual(self.pub.ledger['backoff_until_utc'], 1794485272)
        self.assertEqual([r['outcome'] for r in self.pub.ledger['requests']], ['success', 'success'])
        saved = self.pub.schedule
        self.promote()
        self.reopen()
        self.assertEqual(self.pub.schedule, saved)
        print('DETAIL_G9 ' + json.dumps({'requests': 2, 'detailRequests': 0, 'retainedValidation': 1794481322,
                                         'acceptedEntries': 21, 'source': at}), flush=True)

    def test_nonterminal_omissions_use_budget_before_any_terminal_history(self):
        statuses = (3, 4, 7, 1, 6, 9, 42)
        values = [row(i + 1, phase) for i, phase in enumerate(statuses)]
        self.seed(values)
        at = NOW + 3600
        details = {v['id']: v for v in values[3:]}
        with self.server([row(99)], now=at, details=details) as (client, _, calls, permissions):
            result = update(self.pub, client, at, self.catalog, detail_limit=4)
        self.assertEqual(result['traversal']['detailRequests'], 4)
        self.assertEqual(result['detailFailures'], [])
        self.assertEqual([urlsplit(url).path.split('/')[-2] for url in calls[1:]], [v['id'] for v in values[3:]])
        self.assertEqual(permissions, ['reserved'] * 5)
        records = {e.record.launch_id.value: e.record for e in self.pub.schedule.entries}
        for index, value in enumerate(values):
            self.assertEqual(records[value['id']].source_validated_utc, NOW if index < 3 else at)
            self.assertEqual(records[value['id']].source_status_id, statuses[index])
        self.assertEqual(records[values[-1]['id']].status, LaunchStatus.UNKNOWN)

    def test_explicit_cancelled_omission_never_spends_detail_budget(self):
        record = replace(support.normalize_launch(row(1), NOW), status=LaunchStatus.CANCELLED)
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        candidate = self.pub.preview_source((record,), NOW)
        publisher = self.pub.publisher_envelope(NOW, selection_validated_utc=NOW)
        files, digest = build_artifact(candidate, self.catalog, NOW, publisher=publisher)
        self.pub.accept_and_prepare(self.pub.head, token, (record,), NOW, files, digest,
                                    selection_validated_utc=NOW, feed_publisher=publisher)
        self.promote()
        with self.server([row(2)], now=NOW + 3600, detail_status=500) as (client, _, calls, _):
            result = update(self.pub, client, NOW + 3600, self.catalog)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result['traversal']['detailRequests'], 0)
        retained = next(e.record for e in self.pub.schedule.entries if e.record.launch_id.value == record.launch_id.value)
        self.assertEqual(retained, record)

    def test_normal_and_documented_detailed_detail_keep_source_facts_and_age(self):
        documented = json.loads(gzip.decompress((FIXTURES / 'official-openapi.json.gz').read_bytes()))
        response = documented['paths']['/2.3.0/launches/{id}/']['get']['responses']['200']
        self.assertEqual(response['content']['application/json']['schema']['$ref'], '#/components/schemas/LaunchDetailed')
        self.assertEqual(documented['components']['schemas']['LaunchDetailed']['properties']['response_mode']['default'], 'detailed')
        self.assertEqual(documented['components']['schemas']['LaunchNormal']['properties']['response_mode']['default'], 'normal')
        values = [row(1), row(2)]
        self.seed(values)
        at = NOW + 3600
        details = {v['id']: {**v, 'response_mode': mode, 'status': {'id': 3, 'name': 'Launch Successful'},
                             'last_updated': '2026-11-12T00:30:00Z'}
                   for v, mode in zip(values, ('normal', 'detailed'))}
        with self.server([row(3)], now=at, details=details, detail_headers={'Age': '30'}) as (client, _, calls, _):
            result = update(self.pub, client, at, self.catalog)
        self.assertEqual(result['requests'], 3)
        self.assertEqual(result['detailFailures'], [])
        records = {e.record.launch_id.value: e.record for e in self.pub.schedule.entries}
        for value in values:
            record = records[value['id']]
            self.assertEqual(record.status, LaunchStatus.COMPLETED)
            self.assertEqual(record.source_status_id, 3)
            self.assertEqual(record.source_validated_utc, at - 30)
            self.assertEqual(record.source_updated_utc, NOW + 1800)
            self.assertEqual(record.mission_name, 'Луна')
            self.assertEqual(record.configuration_id.value, '99999')
        self.assertTrue(all(url.endswith('?mode=normal') for url in calls[1:]))
        self.assertEqual(self.pub.ledger['selection_validated_utc'], at)

    def test_detailed_mode_is_refused_in_upcoming_context(self):
        before = self.pub.schedule
        with self.server([row(1, mode='detailed')]) as (client, _, calls, _):
            with self.assertRaisesRegex(ProviderError, 'normal launch mode required'):
                update(self.pub, client, NOW, self.catalog)
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.pub.schedule, before)
        self.assertIsNone(self.pub.ledger['pending'])
        self.assertEqual(self.pub.ledger['requests'][-1]['outcome'], 'failed')

    def test_optional_detail_refusals_keep_primary_and_old_facts_with_consumed_slot(self):
        bad = row(1, mode='detailed')
        cases = [
            ('wrong_uuid', {'details': {bad['id']: row(999, mode='detailed')}}),
            ('unsupported', {'details': {bad['id']: {**bad, 'response_mode': 'future'}}}),
            ('minimal', {'details': {bad['id']: {**bad, 'response_mode': 'list'}}}),
            ('missing_status', {'details': {bad['id']: {'id': bad['id'], 'response_mode': 'detailed'}}}),
            ('malformed_nested', {'details': {bad['id']: {**bad, 'rocket': []}}}),
            ('malformed_json', {'raw': b'{'}),
            ('oversize', {'raw': b' ' * (MAX_RESPONSE_BYTES + 1)}),
            ('future_date', {'details': {bad['id']: bad}, 'detail_headers': {'Date': 'Thu, 12 Nov 2026 02:00:01 GMT'}}),
            ('missing_date', {'details': {bad['id']: bad}, 'detail_headers': {'Date': None}}),
            ('bad_age', {'details': {bad['id']: bad}, 'detail_headers': {'Age': '-1'}}),
            ('old_date_age', {'details': {bad['id']: bad}, 'detail_headers': {'Age': '3601'}}),
            ('http404', {'detail_status': 404}), ('http304', {'detail_status': 304}),
            ('http500', {'detail_status': 500}), ('http429', {'detail_status': 429, 'detail_headers': {'Retry-After': '7200'}}),
        ]
        self.seed([bad | {'response_mode': 'normal'}])
        original = self.pub.schedule.entries[0].record
        for index, (label, settings) in enumerate(cases):
            with self.subTest(label=label):
                at = NOW + (index + 1) * 14400
                if label == 'future_date':
                    settings['detail_headers']['Date'] = format_datetime(datetime.fromtimestamp(at + 1, timezone.utc), usegmt=True)
                if label == 'old_date_age':
                    settings['detail_headers']['Age'] = str(at - NOW + 1)
                with self.server([row(2)], now=at, **settings) as (client, _, calls, permissions):
                    result = update(self.pub, client, at, self.catalog, detail_limit=1)
                self.assertEqual(result['result'], 'pending')
                self.assertEqual(result['requests'], 2)
                self.assertEqual(result['traversal']['detailRequests'], 1)
                self.assertEqual(len(result['detailFailures']), 1)
                self.assertEqual(len(calls), 2)
                self.assertEqual(permissions, ['reserved', 'reserved'])
                records = {e.record.launch_id.value: e for e in self.pub.schedule.entries}
                self.assertEqual(records[original.launch_id.value].record, original)
                self.assertTrue(records[original.launch_id.value].stale)
                self.assertEqual(records[row(2)['id']].record.source_validated_utc, at)
                self.assertEqual(self.pub.ledger['requests'][-1]['outcome'], 'throttled' if label == 'http429' else 'failed')
                self.assertEqual(len(self.pub.ledger['requests']), 2)
                self.assertGreaterEqual(self.pub.ledger['backoff_until_utc'], at + (7200 if label == 'http429' else 300))
                self.promote()
                self.reopen()

    def test_newer_primary_correction_reopens_detail_eligibility_after_terminal_omission(self):
        self.seed([row(1, 3)])
        dispositions = {}
        expected = [(NOW + 3600, [row(2)], {}, 0, 3, NOW),
                    (NOW + 7200, [row(1, 1, modified='2026-11-12T01:30:00Z'), row(2)], {}, 0, 1, NOW + 7200),
                    (NOW + 10800, [row(2)], {row(1)['id']: row(1, 3, mode='detailed', modified='2026-11-12T02:30:00Z')}, 1, 3, NOW + 10800)]
        for label, (at, upcoming, details, extras, phase, validation) in zip(('terminal_omitted', 'primary_corrected', 'pending_reconciled'), expected):
            with self.server(upcoming, now=at, details=details, detail_status=200 if details else 500) as (client, _, calls, _):
                result = update(self.pub, client, at, self.catalog)
            self.assertEqual(result['detailFailures'], [])
            self.assertEqual(result['traversal']['detailRequests'], extras)
            self.assertEqual(len(calls), 1 + extras)
            actual = next(e.record for e in self.pub.schedule.entries if e.record.launch_id.value == row(1)['id'])
            self.assertEqual((actual.source_status_id, actual.source_validated_utc), (phase, validation))
            dispositions[label] = 'observed_no_mutation' if label == 'terminal_omitted' else 'applied'
            self.promote()
            self.reopen()
        self.assertEqual(dispositions, {'terminal_omitted': 'observed_no_mutation', 'primary_corrected': 'applied', 'pending_reconciled': 'applied'})


if __name__ == '__main__':
    unittest.main()
