"""Clock causality witnesses: real default CLI and independent event timestamps.

Only LL2 and Pages readback are substituted. Git authority, runtime, wire bytes
and public CLI are real. Deterministic cases use event-controlled time; the
delayed-HTTP CLI witness separately exercises actual wall time and scheduling.
"""
import copy
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import shutil
import subprocess
import sys
import threading
import time
import unittest

from tests import test_schedule_provider as support
from tools.spacefox.provider import LL2Client, ProviderError, Throttled
from tools.spacefox.publisher import Publisher, StateError, AllowanceUnavailable
from tools.update_feed import update

NOW = support.NOW


def page(rows, next_url=None, count=None):
    return {'count': len(rows) if count is None else count, 'next': next_url, 'previous': None, 'results': rows}


def row(number):
    result = copy.deepcopy(support.FIXTURE['results'][0])
    result['id'] = f'00000000-0000-4000-8000-{number:012d}'
    result['net'] = result['window_start'] = '2026-11-12T01:00:00Z'
    result['window_end'] = '2026-11-12T02:00:00Z'
    return result


class EventClock:
    """Time advances only when the external response/failure event arrives."""
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now


class EventTransport:
    def __init__(self, store, clock, events):
        self.store, self.clock, self.events = store, clock, list(events)
        self.calls = []

    def get(self, url):
        request = self.store.load()[1]['requests'][-1]
        if request['outcome'] != 'reserved' or request['at_utc'] != self.clock.now:
            raise AssertionError('HTTP requires a committed reservation at the modeled request time')
        self.calls.append(url)
        arrived_at, result = self.events.pop(0)
        self.clock.now = arrived_at
        if isinstance(result, Exception):
            raise result
        return result


class ProviderClockTest(unittest.TestCase):
    setUpClass = classmethod(support.ScheduleProviderTest.setUpClass.__func__)
    setUp = support.ScheduleProviderTest.setUp
    tearDown = support.ScheduleProviderTest.tearDown

    def portable_source(self):
        for rel in ('tools/spacefox', 'tools/update_feed.py', 'schemas'):
            src, dst = support.ROOT / rel, self.source / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__'))
            else:
                shutil.copyfile(src, dst)
        for rel in {*self.catalog['inputDigests'], 'catalog/source.json'}:
            dst = self.source / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(support.ROOT / rel, dst)
        support.git(self.source, 'add', '.')
        support.git(self.source, 'commit', '-qm', 'actual clock-qualified producer')
        code = support.git(self.source, 'rev-parse', 'HEAD')
        support.git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        return code

    @contextmanager
    def delayed_server(self, *, age=31, skew=0, status=200):
        observed, permissions = [], []
        owner = self
        started = int(time.time())
        source = copy.deepcopy(support.FIXTURE['results'][0])
        source['last_updated'] = datetime.fromtimestamp(started - 3600, timezone.utc).isoformat()
        source['net'] = source['window_start'] = datetime.fromtimestamp(started + 3600, timezone.utc).isoformat()
        source['window_end'] = datetime.fromtimestamp(started + 7200, timezone.utc).isoformat()

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                from urllib.parse import parse_qs, urlsplit
                ledger = owner.store.load()[1]
                permissions.append(ledger['requests'][-1]['outcome'])
                time.sleep(2)  # Deliberate real transport latency, not model time.
                at = int(time.time()) + skew
                offset = int(parse_qs(urlsplit(self.path).query).get('offset', ['0'])[0])
                page_age = age[offset // 10] if type(age) is tuple else age
                observed.append({'date': at, 'age': page_age, 'offset': offset})
                records = []
                for index in range(offset + 1, offset + 11):
                    row = copy.deepcopy(source)
                    row['id'] = f'00000000-0000-4000-8000-{index:012d}'
                    records.append(row)
                next_url = None if offset else origin + self.path + '&offset=10'
                body = json.dumps({'count': 20, 'next': next_url, 'previous': None, 'results': records}).encode()
                self.send_response_only(status)
                self.send_header('Date', format_datetime(datetime.fromtimestamp(at, timezone.utc), usegmt=True))
                self.send_header('Age', str(page_age))
                self.send_header('Content-Type', 'application/json')
                self.send_header('Retry-After', '60')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        origin = f'http://127.0.0.1:{server.server_port}'
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield LL2Client(origin=origin, local_http=True), observed, permissions, started
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def cli(self, origin, head, output):
        # No --now: this is the production default wall-clock branch.
        argv = [sys.executable, '-B', str(self.source / 'tools/update_feed.py'),
                '--remote', str(self.remote), '--expected-base', head,
                '--origin', origin, '--local-http', 'run', '--output', str(output)]
        return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_default_cli_delayed_dates_preserve_per_page_age(self):
        code = self.portable_source()
        with self.delayed_server(age=(0, 31)) as (client, observations, permissions, started):
            ran = self.cli(client.origin, self.pub.head, self.root / 'artifact')
            print('PP_REAL_CLOCK ' + json.dumps({'start': started, 'responses': observations,
                  'exit': ran.returncode, 'stderr': ran.stderr.decode()}, sort_keys=True), flush=True)
            self.assertEqual(ran.returncode, 0, ran.stderr.decode())
            result = json.loads(ran.stdout)
            self.assertEqual(result['requests'], 2)
            current = Publisher(self.store, code)
            self.assertGreater(observations[0]['date'], started)
            self.assertGreater(observations[1]['date'], observations[0]['date'])
            self.assertEqual(permissions, ['reserved', 'reserved'])
            for entry in current.schedule.entries:
                page = 0 if int(entry.record.launch_id.value[-12:]) <= 10 else 1
                self.assertEqual(entry.record.source_validated_utc, observations[page]['date'] - observations[page]['age'])
            self.assertGreaterEqual(current.ledger['last_event_utc'], observations[-1]['date'])
            self.assertEqual(len(current.schedule.entries), 20)
            self.assertLessEqual(self.store.measure()['ledger_bytes'], 65536)

    def test_default_cli_future_date_rejected_after_delayed_completion(self):
        code = self.portable_source()
        with self.delayed_server(age=0, skew=600) as (client, observations, permissions, started):
            output = self.root / 'invalid-artifact'
            ran = self.cli(client.origin, self.pub.head, output)
            self.assertEqual(ran.returncode, 2)
            self.assertIn(b'provider Date exceeds clock tolerance', ran.stderr)
            current = Publisher(self.store, code)
            self.assertEqual(len(current.schedule.entries), 0)
            self.assertIsNone(current.ledger['pending'])
            self.assertFalse(output.exists())
            self.assertEqual(permissions, ['reserved'])
            self.assertEqual(len(observations), 1)
            self.assertEqual(current.ledger['requests'][0]['outcome'], 'failed')
            self.assertGreater(current.ledger['last_event_utc'], started)

    def test_default_cli_429_backoff_starts_at_response_and_survives_restart(self):
        code = self.portable_source()
        with self.delayed_server(age=0, status=429) as (client, observations, permissions, started):
            output = self.root / 'throttled-artifact'
            ran = self.cli(client.origin, self.pub.head, output)
            self.assertEqual(ran.returncode, 2)
            self.assertIn(b'provider throttled', ran.stderr)
            current = Publisher(self.store, code)
            self.assertEqual(permissions, ['reserved'])
            self.assertEqual(current.ledger['requests'][0]['outcome'], 'throttled')
            self.assertGreaterEqual(current.ledger['backoff_until_utc'], observations[0]['date'] + 60)
            self.assertFalse(output.exists())
            head = current.head
            restarted = self.cli(client.origin, head, output)
            self.assertEqual(restarted.returncode, 0, restarted.stderr.decode())
            self.assertEqual(json.loads(restarted.stdout)['result'], 'not_due')
            self.assertEqual(self.store.load()[0], head)
            self.assertEqual(len(observations), 1)
            self.assertFalse(output.exists())

    def advancing_optional(self, optional):
        # Independent event oracle: accepted A at t0; primary B at t902-Age120;
        # primary C at t904; optional A unchanged at t907-Age907=t0.
        update(self.pub, LL2Client(support.Responses(self.store, [support.response(page([row(1)]))])), NOW, self.catalog)
        pending = self.pub.ledger['pending']
        from tools.spacefox.publisher import LiveRevision
        self.pub.reconcile(LiveRevision(pending['generation'], pending['artifact_revision']))
        clock = EventClock(NOW + 900)
        client = LL2Client(page_size=1)
        next_url = client.first_url + '&offset=1'
        events = [(NOW + 902, support.response(page([row(2)], next_url, 2), now=NOW + 902, headers={'age': '120'})),
                  (NOW + 904, support.response(page([row(3)], count=2), now=NOW + 904)),
                  (NOW + 907, optional)]
        transport = EventTransport(self.store, clock, events)
        client.transport = transport
        result = update(self.pub, client, NOW + 900, self.catalog, clock=clock)
        self.assertEqual(result['result'], 'pending')
        self.assertEqual(result['requests'], 3)
        self.assertEqual(result['revision']['generation'], 2)
        self.assertEqual(len(transport.calls), 3)
        self.assertEqual(transport.events, [])
        observed = {e.record.launch_id.value: e.record.source_validated_utc for e in self.pub.schedule.entries}
        self.assertEqual(observed, {row(1)['id']: NOW, row(2)['id']: NOW + 782, row(3)['id']: NOW + 904})
        self.assertEqual([r['at_utc'] for r in self.pub.ledger['requests']], [NOW, NOW + 900, NOW + 902, NOW + 904])
        self.assertEqual(self.pub.ledger['last_event_utc'], NOW + 907)
        self.assertTrue(self.pub.ledger['requests'][2]['accepted_source'])
        return result

    def test_advancing_clock_two_pages_optional_success_keeps_origin_age(self):
        self.advancing_optional(support.response(row(1), now=NOW + 907, headers={'age': '907'}))
        self.assertTrue(all(r['outcome'] == 'success' for r in self.pub.ledger['requests']))

    def test_advancing_clock_optional_429_keeps_primary_and_response_backoff(self):
        result = self.advancing_optional(support.response(status=429, now=NOW + 907, headers={'retry-after': '60'}))
        self.assertEqual(len(result['detailFailures']), 1)
        self.assertEqual(self.pub.ledger['requests'][-1]['outcome'], 'throttled')
        self.assertEqual(self.pub.ledger['backoff_until_utc'], NOW + 967)
        reopened = Publisher(self.store, self.code)
        self.assertEqual(reopened.ledger['backoff_until_utc'], NOW + 967)

    def test_429_crossing_second_uses_single_response_instant(self):
        ticks, reads = iter((NOW + 2, NOW + 3)), []
        def clock():
            value = next(ticks)
            reads.append(value)
            return value
        transport = support.Responses(self.store, [support.response(status=429, headers={'retry-after': '60'})])
        with self.assertRaises(Throttled) as raised:
            LL2Client(transport).request(self.pub, NOW, clock=clock)
        self.assertEqual(raised.exception.retry_at, NOW + 62)
        self.assertEqual(reads, [NOW + 2])
        self.assertEqual(self.pub.ledger['last_event_utc'], NOW + 2)
        self.assertEqual(self.pub.ledger['backoff_until_utc'], NOW + 62)
        self.assertEqual(self.pub.ledger['requests'][0]['outcome'], 'throttled')
        self.assertEqual(len(transport.urls), 1)

    def test_advancing_failure_clock_and_monotonic_restart(self):
        clock = EventClock(NOW)
        transport = EventTransport(self.store, clock, [(NOW + 20, ProviderError('timeout event'))])
        with self.assertRaisesRegex(ProviderError, 'timeout event'):
            update(self.pub, LL2Client(transport), NOW, self.catalog, clock=clock)
        self.assertEqual(self.pub.ledger['backoff_until_utc'], NOW + 320)
        self.assertEqual(self.pub.ledger['last_event_utc'], NOW + 20)
        reopened = Publisher(self.store, self.code)
        reopened.reconcile(None)
        head = reopened.head
        clock.now = NOW + 319
        with self.assertRaises(AllowanceUnavailable):
            update(reopened, LL2Client(transport), NOW + 319, self.catalog, clock=clock, trigger='manual')
        self.assertEqual(reopened.head, head)
        clock.now = NOW + 19
        with self.assertRaisesRegex(StateError, 'logical UTC cannot regress'):
            update(reopened, LL2Client(transport), NOW + 19, self.catalog, clock=clock)
        self.assertEqual(reopened.head, head)
        self.assertEqual(len(transport.calls), 1)
        clock.now = NOW + 320
        transport.events = [(NOW + 322, support.response(page([row(1)]), now=NOW + 322))]
        update(reopened, LL2Client(transport), NOW + 320, self.catalog, clock=clock, trigger='retry')
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(reopened.ledger['last_event_utc'], NOW + 322)

    def test_explicit_fixed_now_and_future_or_source_modification_rejection(self):
        # Direct replay stays fixed. Neither true future validation nor content
        # modified after Date-Age may be accepted, even after delayed transport.
        for index, kind in enumerate(('future_one_second', 'future_skew', 'newer_content')):
            at = NOW + index * 3600
            clock = EventClock(at)
            record = row(index + 1)
            date = at + (3 if kind == 'future_one_second' else 63 if kind == 'future_skew' else 2)
            if kind == 'newer_content':
                record['last_updated'] = datetime.fromtimestamp(at + 3, timezone.utc).isoformat()
            transport = EventTransport(self.store, clock, [(at + 2, support.response(page([record]), now=date))])
            with self.assertRaisesRegex(ProviderError, 'future|clock tolerance|modification exceeds'):
                update(self.pub, LL2Client(transport), at, self.catalog, clock=clock)
            self.assertIsNone(self.pub.ledger['pending'])
            self.assertEqual(len(self.pub.schedule.entries), 0)
            self.assertEqual(self.pub.ledger['requests'][-1]['outcome'], 'failed')
            self.assertEqual(self.pub.ledger['last_event_utc'], at + 2)
        at = NOW + 10800
        clock = EventClock(at)
        transport = EventTransport(self.store, clock, [(at + 10, support.response(page([row(9)]), now=at))])
        update(self.pub, LL2Client(transport), at, self.catalog)
        self.assertEqual(self.pub.schedule.entries[0].record.source_validated_utc, at)
        self.assertEqual(self.pub.ledger['last_event_utc'], at)

    def test_completed_primary_invocation_anchor_is_exact_expiring_and_single_use(self):
        record = support.normalize_launch(row(1), NOW)
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        self.pub.finish_request(self.pub.head, token, NOW + 2, 'success', retain_for_acceptance=True)
        head = self.pub.head
        for anchor in (None, NOW + 1):
            with self.assertRaises(StateError):
                self.pub.accept_and_prepare(head, token, (record,), NOW + 4, {'feed.json': b'bad'}, 'c' * 64,
                                            invocation_utc=anchor)
            self.assertEqual(self.pub.head, head)
        with self.assertRaises(StateError):
            self.pub.accept_and_prepare(head, token, (record,), NOW + 3600, {'feed.json': b'expired'}, 'c' * 64,
                                        invocation_utc=NOW)
        revision = self.pub.accept_and_prepare(head, token, (record,), NOW + 5, {'feed.json': b'good'}, 'c' * 64,
                                               invocation_utc=NOW)
        self.pub.reconcile(revision)
        head = self.pub.head
        with self.assertRaises(StateError):
            self.pub.accept_and_prepare(head, token, (record,), NOW + 6, {'feed.json': b'replay'}, 'c' * 64,
                                        invocation_utc=NOW)
        self.assertEqual(self.pub.head, head)
        self.assertEqual(len(self.pub.ledger['requests']), 1)
        self.assertTrue(self.pub.ledger['requests'][0]['accepted_source'])
