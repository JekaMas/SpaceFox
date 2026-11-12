"""Independent default-workload regressions: actual Git and loopback HTTP only.

LL2 responses and the explicit --live observation are substituted; no production
provider, authenticated Pages or native qualification is claimed.
"""
import copy
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import types
import shutil
import subprocess
import sys
import threading
import unittest

from tests import test_schedule_provider as support
from tools.spacefox.publisher import Publisher, LiveRevision, StateError, decode_ledger
from tools.spacefox.provider import LL2Client
from tools.spacefox.wire import validate_feed
from tools.update_feed import update

NOW = support.NOW


def rows(start, count):
    result = []
    for number in range(start, start + count):
        row = copy.deepcopy(support.FIXTURE['results'][0])
        row['id'] = f'00000000-0000-4000-8000-{number:012d}'
        row['mission'] = {'name': f'Lunar survey {number}',
                          'description': 'Measure lunar radiation and characterize the plasma environment.'}
        row['net'] = row['window_start'] = '2026-11-12T01:00:00Z'
        row['window_end'] = '2026-11-12T02:00:00Z'
        result.append(row)
    return result


class ProviderLivenessTest(unittest.TestCase):
    setUpClass = classmethod(support.ScheduleProviderTest.setUpClass.__func__)
    setUp = support.ScheduleProviderTest.setUp
    tearDown = support.ScheduleProviderTest.tearDown
    client = support.ScheduleProviderTest.client
    promote = support.ScheduleProviderTest.promote

    @contextmanager
    def server(self, upcoming, *, detail_status=404):
        calls, permissions = [], []
        state = {'rows': upcoming, 'now': NOW, 'detail_status': detail_status, 'details': {}, 'detail_epoch': None}
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                from urllib.parse import parse_qs, urlsplit
                calls.append(self.path)
                ledger = owner.store.load()[1]
                permissions.append(ledger['requests'][-1]['outcome'])
                self.send_response_only(200 if '/upcoming/' in self.path else state['detail_status'])
                epoch = state['now'] if '/upcoming/' in self.path or state['detail_epoch'] is None else state['detail_epoch']
                self.send_header('Date', format_datetime(datetime.fromtimestamp(epoch, timezone.utc), usegmt=True))
                self.send_header('Content-Type', 'application/json')
                if '/upcoming/' in self.path:
                    offset = int(parse_qs(urlsplit(self.path).query).get('offset', ['0'])[0])
                    page_rows = state['rows'][offset:offset + 10]
                    next_url = None
                    if offset + len(page_rows) < len(state['rows']):
                        next_url = origin + '/2.3.0/launches/upcoming/?mode=normal&limit=10&ordering=net&include_suborbital=true&hide_recent_previous=false&offset=' + str(offset + 10)
                    body = json.dumps({'count': len(state['rows']), 'next': next_url,
                                       'previous': None, 'results': page_rows}).encode()
                else:
                    identity = urlsplit(self.path).path.split('/')[-2]
                    body = json.dumps(state['details'][identity]).encode() if identity in state['details'] else b''
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
            yield LL2Client(origin=origin, local_http=True), state, calls, permissions
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def test_optional_missing_id_does_not_starve_new_primary_default(self):
        with self.server(rows(1, 1)) as (client, state, calls, permissions):
            update(self.pub, client, NOW, self.catalog)
            self.promote()
            state.update(rows=rows(2, 20), now=NOW + 14400)
            result = update(self.pub, client, NOW + 14400, self.catalog)
            self.assertEqual(result['result'], 'pending')
            by_id = {e.record.launch_id.value: e for e in self.pub.schedule.entries}
            self.assertEqual(len(by_id), 21)
            old = by_id['00000000-0000-4000-8000-000000000001']
            self.assertEqual(old.record.source_validated_utc, NOW)
            self.assertTrue(old.stale)
            self.assertEqual(old.record.status.value, 'pending')
            self.assertTrue(all(by_id[row['id']].record.source_validated_utc == NOW + 14400 for row in rows(2, 20)))
            self.assertEqual(result['requests'], 3)
            self.assertEqual(permissions, ['reserved'] * 4)
            self.assertEqual(len(calls), 4)
            self.assertEqual(self.pub.ledger['requests'][-1]['outcome'], 'failed')
            self.assertGreaterEqual(self.pub.ledger['backoff_until_utc'], NOW + 14700)

    def test_full_default_twenty_record_generations_and_reopen(self):
        with self.server(rows(1, 20)) as (client, state, calls, permissions):
            first = update(self.pub, client, NOW, self.catalog)
            self.assertEqual(first['requests'], 2)
            self.promote()
            state['now'] = NOW + 900
            second = update(self.pub, client, NOW + 900, self.catalog)
            self.assertEqual(second['result'], 'pending')
            self.assertEqual(second['requests'], 2)
            self.assertEqual(second['revision']['generation'], 2)
            self.assertEqual(len(self.pub.schedule.entries), 20)
            files = self.pub.pending_files()
            reopened = Publisher(self.store, self.code)
            active = reopened.ledger['active']
            self.assertEqual(reopened.reconcile(LiveRevision(active['generation'], active['artifact_revision'])), 'retry_pending')
            self.assertEqual(reopened.pending_files(), files)
            self.assertEqual(reopened.schedule, self.pub.schedule)
            feed = validate_feed(files['feed.json'])
            self.assertEqual(feed['selection']['acceptedRecords'], 20)
            self.assertLessEqual(len(files['feed.json']), 8192)
            self.assertLessEqual(self.store.measure()['ledger_bytes'], 65536)
            print('PP_DEFAULT20_METRICS ' + json.dumps(self.store.measure(), sort_keys=True), flush=True)
            self.assertEqual(permissions, ['reserved'] * 4)
            self.assertEqual(len(calls), 4)

    def test_four_near_default_updates_do_not_discard_primary_at_fifteen_calls(self):
        with self.server(rows(1, 2), detail_status=200) as (client, state, calls, permissions):
            update(self.pub, client, NOW, self.catalog)
            self.promote()
            state.update(rows=rows(3, 20), details={r['id']: r for r in rows(1, 2)}, detail_epoch=NOW)
            dispositions = {'origin': 'applied'}
            for generation, delta in enumerate((900, 1800, 2700, 3600), 2):
                state['now'] = NOW + delta
                result = update(self.pub, client, NOW + delta, self.catalog)
                self.assertEqual(result['revision']['generation'], generation)
                self.assertEqual(result['requests'], 4 if delta < 3600 else 3)
                self.assertEqual(len(self.pub.schedule.entries), 22)
                for entry in self.pub.schedule.entries:
                    number = int(entry.record.launch_id.value[-12:])
                    self.assertEqual(entry.record.source_validated_utc, NOW if number < 3 else NOW + delta)
                    self.assertEqual(entry.stale, number < 3 and delta >= 2700)
                dispositions['quota_limited' if delta == 3600 else f'poll_{delta}'] = 'applied'
                self.promote()
                self.pub = Publisher(self.store, self.code)
                active = self.pub.ledger['active']
                self.pub.reconcile(LiveRevision(active['generation'], active['artifact_revision']))
            self.assertEqual(len(calls), 16)  # Bootstrap call expires at the final poll.
            self.assertEqual(permissions, ['reserved'] * 16)
            self.assertEqual(len(self.pub.ledger['requests']), 15)
            print('PP_ROLLING_QUOTA ' + json.dumps({'allHttpCalls': len(calls), 'currentHourReservations': 15,
                  'lastPollRequests': result['requests'], 'generation': result['revision']['generation']}, sort_keys=True), flush=True)
            self.assertIn('allowance exhausted', result['detailFailures'][0]['reason'])
            self.assertEqual(dispositions, {'origin': 'applied', 'poll_900': 'applied', 'poll_1800': 'applied',
                                           'poll_2700': 'applied', 'quota_limited': 'applied'})

    def test_optional_failure_kinds_keep_primary_and_preserve_age(self):
        from tools.spacefox.provider import ProviderError
        cases = [('cache304', support.response(status=304, now=NOW + 3600)),
                 ('timeout', ProviderError('local injected timeout')),
                 ('throttle', support.response(status=429, now=NOW + 3600, headers={'retry-after': '7200'})),
                 ('malformed', support.response({'id': 'invalid'}, now=NOW + 3600))]
        for index, (label, optional) in enumerate(cases):
            with self.subTest(label=label):
                at = NOW + index * 14400
                old = rows(100 + index * 2, 1)[0]
                body = {'count': 1, 'next': None, 'previous': None, 'results': [old]}
                update(self.pub, self.client(support.response(body, now=at)), at, self.catalog, detail_limit=0)
                self.promote()
                new = rows(101 + index * 2, 1)[0]
                body['results'] = [new]
                # A fresh named request failure is substituted at the transport
                # boundary; real HTTP404 is exercised by the default witness.
                if not isinstance(optional, Exception):
                    optional = support.response(None if label != 'malformed' else {'id': 'invalid'},
                                                now=at + 3600, status=optional.status,
                                                headers={'retry-after': '7200'} if label == 'throttle' else None)
                result = update(self.pub, self.client(support.response(body, now=at + 3600), optional),
                                at + 3600, self.catalog)
                self.assertEqual(result['result'], 'pending')
                retained = {e.record.launch_id.value: e for e in self.pub.schedule.entries}
                self.assertEqual(retained[old['id']].record.source_validated_utc, at)
                self.assertEqual(retained[new['id']].record.source_validated_utc, at + 3600)
                self.assertEqual(len(result['detailFailures']), 1)
                self.assertEqual(self.pub.ledger['requests'][-1]['outcome'], 'throttled' if label == 'throttle' else 'failed')
                if label == 'throttle':
                    self.assertEqual(self.pub.ledger['backoff_until_utc'], at + 10800)
                self.promote()

    def test_completed_primary_token_is_single_use_and_bound(self):
        record = support.normalize_launch(rows(1, 1)[0], NOW)
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        self.pub.finish_request(self.pub.head, token, NOW, 'success', retain_for_acceptance=True)
        revision = self.pub.accept_and_prepare(self.pub.head, token, (record,), NOW, {'feed.json': b'actual'}, 'c' * 64)
        self.pub.reconcile(revision)
        for bad_token, at in ((token, NOW), (token, NOW + 3600), ('f' * 64, NOW)):
            before = self.pub.head
            with self.assertRaises(StateError):
                self.pub.accept_and_prepare(before, bad_token, (record,), at, {'feed.json': b'replay'}, 'c' * 64)
            self.assertEqual(self.pub.head, before)
        for purpose, outcome in (('catalog', 'success'), ('schedule', 'success'), ('schedule', 'failed')):
            token = self.pub.reserve(self.pub.head, NOW + 7200, purpose=purpose, trigger='manual')
            self.pub.finish_request(self.pub.head, token, NOW + 7200, outcome)
            with self.assertRaises(StateError):
                self.pub.accept_and_prepare(self.pub.head, token, (record,), NOW + 7200, {'feed.json': b'invalid'}, 'c' * 64)
        # A still-reserved successful HTTP result may finish later in the same
        # hour, preserving the original API's non-instantaneous request input.
        token = self.pub.reserve(self.pub.head, NOW + 10800, trigger='manual')
        revision = self.pub.accept_and_prepare(self.pub.head, token, (record,), NOW + 10830,
                                               {'feed.json': b'delayed-result'}, 'c' * 64)
        self.pub.reconcile(revision)
        token = self.pub.reserve(self.pub.head, NOW + 14400, trigger='manual')
        self.pub.finish_request(self.pub.head, token, NOW + 14400, 'success', retain_for_acceptance=True)
        with self.assertRaises(StateError):
            self.pub.accept_and_prepare(self.pub.head, token, (record,), NOW + 18000, {'feed.json': b'expired'}, 'c' * 64)

    def test_real_legacy_v1_empty_active_pending_migrate_losslessly(self):
        # Execute the actual pre-migration writer to produce schema1 histories.
        # It is a frozen repository source, not a second implementation/oracle.
        legacy = types.ModuleType('tools.spacefox.legacy_publisher')
        legacy.__package__ = 'tools.spacefox'
        import hashlib
        source = (support.ROOT / 'tests/fixtures/state/publisher-schema1.py.txt').read_bytes()
        self.assertEqual(hashlib.sha256(source).hexdigest(), 'fde559d768f6e4e0f6f45833c39f88605255bc8c63d86c1700fa837dd4736bb0')
        sys.modules[legacy.__name__] = legacy
        exec(compile(source, '<frozen-schema1-writer>', 'exec'), legacy.__dict__)
        for phase in ('empty', 'active', 'pending'):
            with self.subTest(phase=phase):
                remote = self.root / (phase + '.git')
                subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
                support.git(self.source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
                old_store = legacy.GitState(str(remote))
                new_store = None
                try:
                    legacy_code = support.git(self.source, 'rev-parse', 'HEAD')
                    old_store.bootstrap(legacy_code)
                    old = legacy.Publisher(old_store, legacy_code)
                    old.reconcile(None)
                    if phase != 'empty':
                        from tests.test_publisher_state import record
                        token = old.reserve(old.head, 1000, trigger='manual')
                        old.accept_source(old.head, token, (record(),), 1000)
                        # Legacy omission of optional defaults is part of the
                        # literal snapshot hash and must survive migration.
                        doc = old.ledger
                        for entry in doc['accepted']['entries']:
                            for key in ('source_updated_utc', 'source_updated_subsecond', 'source_updated_iso',
                                        'source_status_id', 'source_status_name', 'site_name', 'country_name'):
                                entry['record'].pop(key, None)
                            for key in ('nominal_utc', 'source_net', 'source_precision_id', 'source_precision_name',
                                        'source_precision_abbrev', 'source_precision_description'):
                                entry['record']['timing'].pop(key, None)
                        old._save(doc)
                        revision = old.prepare(old.head, 1000, {'feed.json': b'legacy-exact-artifact'}, 'c' * 64)
                        if phase == 'active':
                            old.reconcile(revision)
                    before = old.ledger
                    files = old_store._files(old.head, before)
                    # Actual current source revision changes; candidate remains
                    # pinned to the exact original producer and digest.
                    support.git(self.source, 'commit', '--allow-empty', '-qm', 'new producer ' + phase)
                    code = support.git(self.source, 'rev-parse', 'HEAD')
                    support.git(self.source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
                    from tools.spacefox.publisher import GitState
                    new_store = GitState(str(remote))
                    current = Publisher(new_store, code)
                    current.adopt_code(current.head)
                    after = current.ledger
                    self.assertEqual(after['schema_version'], 2)
                    for field in ('accepted', 'active', 'pending', 'generation', 'refresh_policy', 'requests'):
                        self.assertEqual(after[field], before[field])
                    self.assertEqual(new_store._files(current.head, after), files)
                    if phase == 'active':
                        before_replay = current.head
                        with self.assertRaises(StateError):
                            current.accept_and_prepare(current.head, before['requests'][-1]['id'],
                                                       tuple(e.record for e in current.schedule.entries), 1000,
                                                       {'feed.json': b'legacy-token-replay'}, 'c' * 64)
                        self.assertEqual(current.head, before_replay)
                    if phase == 'pending':
                        self.assertEqual(current.reconcile(None), 'retry_pending')
                        self.assertEqual(current.pending_files(), {'feed.json': b'legacy-exact-artifact'})
                        pending = before['pending']
                        self.assertEqual(current.reconcile(LiveRevision(pending['generation'], pending['artifact_revision'])), 'promoted')
                    else:
                        active = before['active']
                        self.assertEqual(current.reconcile(None if active is None else LiveRevision(active['generation'], active['artifact_revision'])), 'ready')
                finally:
                    old_store.close()
                    if new_store is not None:
                        new_store.close()
        sys.modules.pop(legacy.__name__, None)

    def test_schema2_snapshot_dedup_and_missing_or_corrupt_object_rejected(self):
        import hashlib
        from tools.spacefox.publisher import MAX_LEDGER_BYTES, MAX_ARTIFACT_BYTES
        with self.server(rows(1, 20)) as (client, state, calls, permissions):
            update(self.pub, client, NOW, self.catalog)
        raw = self.store._blob(self.pub.head, 'ledger.json', MAX_LEDGER_BYTES)
        disk = json.loads(raw)
        self.assertEqual(disk['schema_version'], 2)
        self.assertEqual(disk['accepted'], disk['pending']['schedule'])
        ref = disk['accepted']
        path = 'schedules/' + ref['sha256'] + '.json'
        data = self.store._blob(self.pub.head, path, MAX_ARTIFACT_BYTES)
        self.assertEqual(hashlib.sha256(data).hexdigest(), ref['sha256'])
        self.assertEqual(len(data), ref['bytes'])
        self.assertEqual(len(json.loads(data)['entries']), 20)
        self.assertEqual(self.store.measure()['schedule_objects'], 1)
        for bad in (data + b' ', b'{}'):
            with self.assertRaises(StateError):
                decode_ledger(raw, lambda ignored: bad)
        # Remove the actual authoritative object, then reopen through GitState.
        self.store._git('read-tree', self.pub.head)
        self.store._git('update-index', '--index-info', data=('0 ' + '0' * 40 + '\t' + path + '\n').encode())
        tree = self.store._git('write-tree').stdout.decode().strip()
        commit = self.store._git('commit-tree', tree, '-p', self.pub.head, data=b'fixture: missing schedule object').stdout.decode().strip()
        self.store._git('push', f'--force-with-lease=refs/heads/feed-state:{self.pub.head}', str(self.remote),
                        commit + ':refs/heads/feed-state')
        with self.assertRaises(StateError):
            Publisher(self.store, self.code)
        self.assertEqual(permissions, ['reserved', 'reserved'])
        self.assertEqual(len(calls), 2)

    def test_actual_clean_cli_default_twenty_two_generations_and_recovery(self):
        for rel in ('tools/spacefox', 'tools/update_feed.py', 'schemas'):
            src, dst = support.ROOT / rel, self.source / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns('__pycache__'))
            else:
                shutil.copyfile(src, dst)
        for rel in self.catalog['inputDigests']:
            dst = self.source / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(support.ROOT / rel, dst)
        (self.source / 'catalog').mkdir(exist_ok=True)
        shutil.copyfile(support.ROOT / 'catalog/source.json', self.source / 'catalog/source.json')
        support.git(self.source, 'add', '.')
        support.git(self.source, 'commit', '-qm', 'actual default producer')
        code = support.git(self.source, 'rev-parse', 'HEAD')
        support.git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        with self.server(rows(1, 20)) as (client, state, calls, permissions):
            def run(head, output, now, live=None):
                argv = [sys.executable, '-B', str(self.source / 'tools/update_feed.py'),
                        '--remote', str(self.remote), '--expected-base', head,
                        '--origin', client.origin, '--local-http', '--now', str(now)]
                if live is not None:
                    argv += ['--live', str(live['generation']) + ':' + live['artifact_revision']]
                argv += ['run', '--output', str(output)]
                ran = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                self.assertEqual(ran.returncode, 0, ran.stderr.decode())
                return json.loads(ran.stdout)
            first = run(self.pub.head, self.root / 'first', NOW)
            self.assertEqual(first['requests'], 2)
            state['now'] = NOW + 900
            second = run(first['head'], self.root / 'second', NOW + 900, first['revision'])
            self.assertEqual(second['revision']['generation'], 2)
            self.assertEqual(second['requests'], 2)
            recovered = run(second['head'], self.root / 'recovered', NOW + 1800, first['revision'])
            self.assertEqual(recovered['result'], 'recovered_pending')
            self.assertEqual(len(calls), 4)
            self.assertEqual(permissions, ['reserved'] * 4)
            current = Publisher(self.store, code)
            durable = current.pending_files()
            for relative, content in durable.items():
                self.assertEqual((self.root / 'second' / relative).read_bytes(), content)
                self.assertEqual((self.root / 'recovered' / relative).read_bytes(), content)
            self.assertEqual(len(current.schedule.entries), 20)
            self.assertEqual({e.record.source_validated_utc for e in current.schedule.entries}, {NOW + 900})
            self.assertLessEqual(self.store.measure()['ledger_bytes'], 65536)
            print('PP_CLI20_METRICS ' + json.dumps(self.store.measure(), sort_keys=True), flush=True)

    def test_authority_snapshot_and_record_budgets_preserve_old_state(self):
        from dataclasses import replace
        base = support.normalize_launch(rows(1, 1)[0], NOW)
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (base,), NOW)
        before = self.pub.schedule
        individual = (replace(base, launch_id=replace(base.launch_id, value='oversize'), mission_purpose='x' * 66000),)
        aggregate = tuple(replace(base, launch_id=replace(base.launch_id, value=str(number)),
                                  mission_purpose='x' * 60000, source_validated_utc=NOW + 3600)
                          for number in range(20))
        for candidate in (individual, aggregate):
            token = self.pub.reserve(self.pub.head, NOW + 3600, trigger='manual')
            reserved_head = self.pub.head
            with self.assertRaisesRegex(StateError, 'archive budget' if candidate is individual else 'invalid bounded integer'):
                self.pub.accept_source(self.pub.head, token, candidate, NOW + 3600)
            self.assertEqual(self.pub.head, reserved_head)
            self.assertEqual(self.pub.schedule, before)
            self.assertIsNone(self.pub.ledger['pending'])
            self.assertEqual(self.pub.ledger['requests'][-1]['outcome'], 'reserved')
            self.pub.finish_request(self.pub.head, token, NOW + 3600, 'success')


if __name__ == '__main__':
    unittest.main()
