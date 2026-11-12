"""Publisher revision/empty-selection bridge: real Git and bounded loopback HTTP.

Directed source-response traces carry literal epochs/generations; no native or
Pages acceptance is implied. PP_FEED_FIXTURE lines expose actual pending bytes
for the separately owned native parser/cache integration tests.
"""
import copy
from contextlib import contextmanager
from datetime import datetime, timezone
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
import sys
import threading
import unittest
from unittest.mock import patch

from tests import test_schedule_provider as support
from tests import test_provider_clock as clocks
from tests import test_provider_liveness as liveness
from tools.spacefox.catalog import canonical_bytes
from tools.spacefox.provider import LL2Client
from tools.spacefox.publisher import Publisher, StateError, Conflict, LiveRevision, decode_ledger
from tools.spacefox.schedule import ScheduleState
from tools.spacefox.wire import build_artifact, validate_feed
from tools.update_feed import update

NOW = support.NOW


def page(rows):
    return dict(count=len(rows), next=None, previous=None, results=rows)


class ProviderRevisionTest(unittest.TestCase):
    setUpClass = classmethod(support.ScheduleProviderTest.setUpClass.__func__)
    setUp = support.ScheduleProviderTest.setUp
    tearDown = support.ScheduleProviderTest.tearDown
    client = support.ScheduleProviderTest.client
    promote = support.ScheduleProviderTest.promote
    portable_source = clocks.ProviderClockTest.portable_source

    @contextmanager
    def server(self, events):
        calls, permissions = [], []
        owner = self
        events = list(events)

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                permissions.append(owner.store.load()[1]['requests'][-1]['outcome'])
                status, at, age, body = events.pop(0)
                body = json.dumps(body).encode()
                self.send_response_only(status)
                self.send_header('Date', format_datetime(datetime.fromtimestamp(at, timezone.utc), usegmt=True))
                self.send_header('Age', str(age))
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            yield LL2Client(origin=f'http://127.0.0.1:{server.server_port}', local_http=True), calls, permissions
        finally:
            server.shutdown()
            server.server_close()
            thread.join()

    def assert_feed(self, generation, epoch, launch_id):
        raw = self.pub.pending_files()['feed.json']
        feed = validate_feed(raw)
        self.assertEqual(feed['publisher'], {'instance': self.pub.ledger['instance_id'],
                         'generation': generation, 'selectionValidatedUtc': epoch})
        self.assertEqual(feed['publisher']['generation'], self.pub.ledger['pending']['generation'])
        self.assertEqual(self.pub.ledger['selection_validated_utc'], epoch)
        self.assertEqual(None if feed['launch'] is None else feed['launch']['launch_id'], launch_id)
        self.assertLessEqual(len(raw), 8192)
        return raw

    def test_real_http_empty_nonempty_terminal_empty_new_and_old200(self):
        row = copy.deepcopy(support.FIXTURE['results'][0])
        terminal = copy.deepcopy(row)
        terminal.update(status={'id': 3, 'name': 'Launch Successful'}, last_updated='2026-11-12T01:00:00Z')
        new = copy.deepcopy(row)
        new['id'] = '00000000-0000-4000-8000-000000000002'
        events = [(200, NOW, 0, page([])), (200, NOW + 3600, 0, page([row])),
                  (200, NOW + 7200, 0, page([terminal])), (200, NOW + 10800, 0, page([new])),
                  (200, NOW + 14400, 14400, page([])), (304, NOW + 18000, 0, None)]
        dispositions = {}
        with self.server(events) as (client, calls, permissions):
            instance = self.pub.ledger['instance_id']
            for gen, at, label, identity in ((1, NOW, 'initial-empty', None),
                    (2, NOW + 3600, 'nonempty', 'll2:launch:' + row['id']),
                    (3, NOW + 7200, 'terminal-empty', None),
                    (4, NOW + 10800, 'new', 'll2:launch:' + new['id'])):
                update(self.pub, client, at, self.catalog, detail_limit=0)
                raw = self.assert_feed(gen, at, identity)
                print('PP_FEED_FIXTURE ' + json.dumps({'name': label, 'bytes': raw.decode()}, sort_keys=True), flush=True)
                self.promote()
                self.pub = Publisher(self.store, self.code)
                active = self.pub.ledger['active']
                self.pub.reconcile(LiveRevision(active['generation'], active['artifact_revision']))
                self.assertEqual(self.pub.ledger['instance_id'], instance)
                dispositions[label] = 'applied'
            before = self.pub.schedule
            with self.assertRaises(StateError):
                update(self.pub, client, NOW + 14400, self.catalog, detail_limit=0)
            self.assertEqual(self.pub.schedule, before)
            self.assertEqual(self.pub.ledger['generation'], 4)
            self.assertEqual(self.pub.ledger['selection_validated_utc'], NOW + 10800)
            self.assertIsNone(self.pub.ledger['pending'])
            dispositions['old200'] = 'observed_no_mutation'
            result = update(self.pub, client, NOW + 18000, self.catalog, detail_limit=0)
            self.assertEqual(result['result'], 'not_modified_without_record_validation')
            self.assertEqual(self.pub.ledger['generation'], 4)
            self.assertEqual(self.pub.ledger['selection_validated_utc'], NOW + 10800)
            dispositions['cache304'] = 'observed_no_mutation'
            self.assertEqual(len(calls), 6)
            self.assertEqual(permissions, ['reserved'] * 6)
        self.assertEqual(dispositions, {'initial-empty': 'applied', 'nonempty': 'applied',
               'terminal-empty': 'applied', 'new': 'applied', 'old200': 'observed_no_mutation',
               'cache304': 'observed_no_mutation'})

    def test_primary_minimum_epoch_and_optional_detail_never_renews_selection(self):
        old = copy.deepcopy(support.FIXTURE['results'][0])
        update(self.pub, self.client(support.response(page([old]))), NOW, self.catalog)
        self.promote()
        a, b = copy.deepcopy(old), copy.deepcopy(old)
        a['id'], b['id'] = '00000000-0000-4000-8000-000000000002', '00000000-0000-4000-8000-000000000003'
        client = LL2Client(page_size=1)
        first = dict(page([a]), count=2, next=client.first_url + '&offset=1')
        second = dict(page([b]), count=2)
        client = self.client(support.response(first, now=NOW + 3600, headers={'age': '17'}),
                             support.response(second, now=NOW + 3600, headers={'age': '61'}),
                             support.response(old, now=NOW + 3600), page_size=1)
        update(self.pub, client, NOW + 3600, self.catalog)
        self.assert_feed(2, NOW + 3539, 'll2:launch:' + old['id'])
        self.assertEqual([e.record.source_validated_utc for e in self.pub.schedule.entries],
                         [NOW + 3600, NOW + 3583, NOW + 3539])
        self.assertEqual(len(self.transport.urls), 3)

    def test_validation_only_and_metadata_only_keep_distinct_ages(self):
        update(self.pub, self.client(support.response(support.FIXTURE)), NOW, self.catalog)
        initial_content = self.pub.schedule.content_revision
        self.promote()
        update(self.pub, self.client(support.response(support.FIXTURE, now=NOW + 3600)), NOW + 3600, self.catalog)
        self.assertEqual(self.pub.schedule.content_revision, initial_content)
        self.assert_feed(2, NOW + 3600, 'll2:launch:' + support.FIXTURE['results'][0]['id'])
        self.promote()
        self.pub.observe_age(self.pub.head, NOW + 14400)
        catalog = copy.deepcopy(self.catalog)
        catalog['catalogVersion'] += '-metadata-only'
        envelope = self.pub.publisher_envelope(NOW + 14400)
        files, digest = build_artifact(self.pub.schedule, catalog, NOW + 14400, publisher=envelope)
        self.pub.prepare(self.pub.head, NOW + 14400, files, digest, feed_publisher=envelope)
        raw = self.assert_feed(3, NOW + 3600, 'll2:launch:' + support.FIXTURE['results'][0]['id'])
        feed = validate_feed(raw)
        self.assertEqual(feed['launch']['source_validated_utc'], NOW + 3600)
        self.assertTrue(feed['launch']['stale'])
        self.assertEqual(len(self.pub.ledger['requests']), 1)  # First slot expired at second poll.
        reopened = Publisher(self.store, self.code)
        self.assertEqual(reopened.pending_files(), files)
        self.assertEqual(reopened.ledger['selection_validated_utc'], NOW + 3600)
        print('PP_FEED_FIXTURE ' + json.dumps({'name': 'metadata-only', 'bytes': raw.decode()}, sort_keys=True), flush=True)
        instance = self.pub.ledger['instance_id']
        self.promote()
        support.git(self.source, 'commit', '--allow-empty', '-qm', 'compatible new producer')
        code = support.git(self.source, 'rev-parse', 'HEAD')
        support.git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.pub = Publisher(self.store, code)
        self.pub.adopt_code(self.pub.head)
        active = self.pub.ledger['active']
        self.pub.reconcile(LiveRevision(active['generation'], active['artifact_revision']))
        self.assertEqual(self.pub.publisher_envelope(NOW + 14400),
                         dict(instance=instance, generation=4, selectionValidatedUtc=NOW + 3600))

    def test_empty_cached200_preserves_age_and_retained_record_age_is_independent(self):
        update(self.pub, self.client(support.response(page([]))), NOW, self.catalog)
        self.promote()
        update(self.pub, self.client(support.response(page([]), now=NOW + 3600, headers={'age': '3600'})),
               NOW + 3600, self.catalog)
        self.assert_feed(2, NOW, None)
        self.promote()
        update(self.pub, self.client(support.response(support.FIXTURE, now=NOW + 7200)), NOW + 7200, self.catalog)
        self.promote()
        update(self.pub, self.client(support.response(page([]), now=NOW + 21600)), NOW + 21600,
               self.catalog, detail_limit=0)
        feed = validate_feed(self.assert_feed(4, NOW + 21600, 'll2:launch:' + support.FIXTURE['results'][0]['id']))
        self.assertEqual(feed['launch']['source_validated_utc'], NOW + 7200)
        self.assertTrue(feed['launch']['stale'])

    def test_reserved_next_generation_race_and_envelope_mismatch_reject_atomically(self):
        token = self.pub.reserve(self.pub.head, NOW, trigger='manual')
        envelope = self.pub.publisher_envelope(NOW, selection_validated_utc=NOW)
        files, digest = build_artifact(ScheduleState(), self.catalog, NOW, publisher=envelope)
        head = self.pub.head
        for key, bad in (('generation', 2), ('instance', 'f' * 64), ('selectionValidatedUtc', NOW - 1)):
            wrong = dict(envelope, **{key: bad})
            bad_files, bad_digest = build_artifact(ScheduleState(), self.catalog, NOW, publisher=wrong)
            with self.assertRaises(StateError):
                self.pub.accept_and_prepare(head, token, (), NOW, bad_files, bad_digest,
                         selection_validated_utc=NOW, feed_publisher=wrong)
            self.assertEqual(self.pub.head, head)
            self.assertEqual(self.pub.ledger['generation'], 0)
            self.assertIsNone(self.pub.ledger['selection_validated_utc'])
        rival = Publisher(self.store, self.code)
        rival.reconcile(None)
        winner = rival.accept_and_prepare(head, token, (), NOW, files, digest,
                      selection_validated_utc=NOW, feed_publisher=envelope)
        with self.assertRaises(Conflict):
            self.pub.accept_and_prepare(head, token, (), NOW, files, digest,
                       selection_validated_utc=NOW, feed_publisher=envelope)
        self.assertEqual(Publisher(self.store, self.code).ledger['generation'], 1)
        rival.reconcile(winner)
        self.assertEqual(rival.publisher_envelope(NOW)['generation'], 2)

    def test_null_zero_negative_and_future_typed_epochs(self):
        # Signed UTC and zero are real values, never falsey unknown sentinels.
        for epoch, at in ((None, -2), (-1, -1), (0, 0)):
            with self.subTest(epoch=epoch):
                envelope = self.pub.publisher_envelope(at, selection_validated_utc=epoch)
                files, digest = build_artifact(ScheduleState(), self.catalog, at, publisher=envelope)
                if epoch is None:
                    self.pub.prepare(self.pub.head, at, files, digest, feed_publisher=envelope)
                else:
                    token = self.pub.reserve(self.pub.head, at, trigger='manual')
                    self.pub.accept_and_prepare(self.pub.head, token, (), at, files, digest,
                                selection_validated_utc=epoch, feed_publisher=envelope)
                self.assertEqual(validate_feed(self.pub.pending_files()['feed.json'])['publisher']['selectionValidatedUtc'], epoch)
                self.promote()
        before = self.pub.head
        for epoch in (-1, 1, True, 0.0, '0', -62135596801, 253402300800):
            with self.subTest(reject=epoch), self.assertRaises(StateError):
                self.pub.publisher_envelope(0, selection_validated_utc=epoch)
        self.assertEqual(self.pub.head, before)
        self.assertEqual(self.pub.publisher_envelope(0)['selectionValidatedUtc'], 0)
        doc = self.pub.ledger
        for bad in (None, -1):
            with self.subTest(regress=bad), self.assertRaises(StateError):
                self.store.write(self.pub.head, dict(doc, selection_validated_utc=bad))
        envelope = self.pub.publisher_envelope(0)
        raw = self.pub.store._blob(self.pub.head, 'ledger.json', 65536)
        disk = json.loads(raw)
        objects = lambda path: self.store._blob(self.pub.head, path, 1048576)
        for value in (True, '0', 0.0, 1, -62135596801):
            with self.subTest(ledger=value), self.assertRaises(StateError):
                decode_ledger(json.dumps(dict(disk, selection_validated_utc=value)).encode(), objects)
        for value in (True, '0', 0.0, 1, -62135596801):
            bad = dict(envelope, selectionValidatedUtc=value)
            with self.subTest(wire=value), self.assertRaises(ValueError):
                build_artifact(ScheduleState(), self.catalog, 0, publisher=bad)

    def test_actual_cli_always_emits_and_recovers_required_envelope(self):
        code = self.portable_source()
        with self.server([(200, NOW, 0, page([]))]) as (client, calls, permissions):
            output = self.root / 'out'
            result = subprocess.run([sys.executable, '-B', str(self.source / 'tools/update_feed.py'),
                    '--remote', str(self.remote), '--expected-base', self.pub.head, '--now', str(NOW),
                    '--origin', client.origin, '--local-http', 'run', '--output', str(output)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.pub = Publisher(self.store, code)
            self.assertEqual((output / 'feed.json').read_bytes(), self.assert_feed(1, NOW, None))
            feed = json.loads((output / 'feed.json').read_bytes())
            for bad in (dict(feed, publisher=None), {k: v for k, v in feed.items() if k != 'publisher'},
                        dict(feed, publisher=dict(feed['publisher'], generation=0))):
                with self.assertRaises(ValueError):
                    validate_feed(canonical_bytes(bad))
            recovered = self.root / 'recovered'
            result = subprocess.run([sys.executable, '-B', str(self.source / 'tools/update_feed.py'),
                    '--remote', str(self.remote), '--expected-base', self.pub.head,
                    'export-pending', '--output', str(recovered)],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertEqual((recovered / 'feed.json').read_bytes(), (output / 'feed.json').read_bytes())
            self.assertEqual(len(calls), 1)
            self.assertEqual(permissions, ['reserved'])

    def test_real_updater_rejects_missing_or_mismatched_builder_envelope(self):
        original = build_artifact
        for mode in ('missing', 'mismatch'):
            def broken(*args, **kwargs):
                files, digest = original(*args, **kwargs)
                feed = json.loads(files['feed.json'])
                if mode == 'missing':
                    feed.pop('publisher')
                else:
                    feed['publisher']['generation'] += 1
                files['feed.json'] = canonical_bytes(feed)
                return files, digest
            at = NOW if mode == 'missing' else NOW + 3600
            with patch('tools.update_feed.build_artifact', broken), self.assertRaises(StateError):
                update(self.pub, self.client(support.response(page([]), now=at)), at, self.catalog)
            self.assertEqual(self.pub.ledger['generation'], 0)
            self.assertIsNone(self.pub.ledger['pending'])
            self.assertIsNone(self.pub.ledger['selection_validated_utc'])
            self.assertEqual(self.pub.ledger['requests'][-1]['outcome'], 'failed')

    def test_legacy_frozen_schema1_snapshot_recovery_stays_exact_and_unknown(self):
        # Reuse the frozen real writer witness; it validates actual absent fields,
        # artifact hashes/bytes, generation, code adoption and pending promotion.
        liveness.ProviderLivenessTest.test_real_legacy_v1_empty_active_pending_migrate_losslessly(self)
        # The old writer has no global epoch. Its absence is preserved through
        # additive-schema adoption, not guessed from evaluation/per-record times.
        from tools.spacefox.publisher import GitState
        for phase in ('empty', 'active', 'pending'):
            store = GitState(str(self.root / (phase + '.git')))
            try:
                pub = Publisher(store, store.current_code())
                self.assertNotIn('selection_validated_utc', pub.ledger)
                active = pub.ledger['active']
                pub.reconcile(None if active is None else LiveRevision(active['generation'], active['artifact_revision']))
                self.assertIsNone(pub.publisher_envelope(2000)['selectionValidatedUtc'])
            finally:
                store.close()


if __name__ == '__main__':
    unittest.main()
