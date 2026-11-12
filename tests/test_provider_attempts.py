"""HTTP-attempt accounting across quota expiry, failure and pre-HTTP guards."""
import unittest
from unittest.mock import patch

from tests import test_schedule_provider as support
from tests.test_provider_clock import EventClock, EventTransport, page, row
from tools.spacefox.provider import LL2Client, Throttled
from tools.spacefox.publisher import AllowanceUnavailable, LiveRevision, StateError
from tools.update_feed import update

NOW = support.NOW


class ProviderAttemptsTest(unittest.TestCase):
    setUpClass = classmethod(support.ScheduleProviderTest.setUpClass.__func__)
    setUp = support.ScheduleProviderTest.setUp
    tearDown = support.ScheduleProviderTest.tearDown

    def rollover(self, status):
        # Two original requests expire when the later primary response arrives.
        # Their removal is not a negative number of newly started HTTP attempts.
        client = LL2Client(page_size=1)
        client.transport = support.Responses(self.store, [
            support.response(page([row(1)], client.first_url + '&offset=1', 2)),
            support.response(page([row(2)], count=2))])
        update(self.pub, client, NOW, self.catalog)
        pending = self.pub.ledger['pending']
        self.pub.reconcile(LiveRevision(pending['generation'], pending['artifact_revision']))
        clock = EventClock(NOW + 3599)
        events = [(NOW + 3601, support.response(page([row(3)]), now=NOW + 3599))]
        if status == 404:
            events.append((NOW + 3602, support.response(status=404, now=NOW + 3602)))
        else:
            events.extend((NOW + 3601 + i, support.response(row(i), now=NOW + 3601 + i,
                           headers={'age': str(3601 + i)})) for i in (1, 2))
        transport = EventTransport(self.store, clock, events)
        client.transport = transport
        result = update(self.pub, client, NOW + 3599, self.catalog, clock=clock)
        expected_details = 1 if status == 404 else 2
        self.assertEqual(result['result'], 'pending')
        self.assertEqual(result['requests'], 1 + expected_details)
        self.assertEqual(result['traversal']['detailRequests'], expected_details)
        self.assertEqual(client.requests_started, 3 + expected_details)  # Includes original two.
        self.assertEqual(len(transport.calls), 1 + expected_details)
        self.assertEqual(len(self.pub.ledger['requests']), 1 + expected_details)
        self.assertEqual(result['revision']['generation'], 2)
        self.assertEqual(self.pub.ledger['selection_validated_utc'], NOW + 3599)
        observed = {entry.record.launch_id.value: entry.record.source_validated_utc
                    for entry in self.pub.schedule.entries}
        self.assertEqual(observed, {row(1)['id']: NOW, row(2)['id']: NOW, row(3)['id']: NOW + 3599})
        self.assertEqual(len(result['detailFailures']), int(status == 404))
        if status == 404:
            self.assertEqual(self.pub.ledger['backoff_until_utc'], NOW + 3902)
            self.assertEqual(self.pub.ledger['requests'][-1]['outcome'], 'failed')

    def test_optional_404_across_hourly_pruning_keeps_primary(self):
        self.rollover(404)

    def test_optional_success_across_hourly_pruning_counts_each_started_request(self):
        self.rollover(200)

    def test_backoff_and_quota_denials_do_not_start_or_refund_http(self):
        transport = support.Responses(self.store, [support.response(status=429, headers={'retry-after': '60'})]
                                      + [support.response(status=304)] * 14)
        client = LL2Client(transport)
        with self.assertRaises(Throttled):
            client.request(self.pub, NOW, trigger='manual')
        self.assertEqual(client.requests_started, 1)
        head = self.pub.head
        with self.assertRaises(AllowanceUnavailable):
            client.request(self.pub, NOW + 1, trigger='retry')
        self.assertEqual((client.requests_started, len(transport.urls), self.pub.head), (1, 1, head))
        for _ in range(14):
            token, response = client.request(self.pub, NOW + 60, trigger='manual')
            self.assertEqual(response.status, 304)
            self.pub.finish_request(self.pub.head, token, NOW + 60, 'success')
        head = self.pub.head
        with self.assertRaises(AllowanceUnavailable):
            client.request(self.pub, NOW + 60, trigger='manual')
        self.assertEqual((client.requests_started, len(transport.urls), len(self.pub.ledger['requests'])), (15, 15, 15))
        self.assertEqual(self.pub.head, head)
        self.assertEqual(self.pub.ledger['requests'][0]['outcome'], 'throttled')

    def test_source_advance_after_reservation_starts_no_http_and_keeps_slot(self):
        transport = support.Responses(self.store, [])
        client = LL2Client(transport)
        original_save = self.pub._save
        def advance_after_save(doc, files=None):
            result = original_save(doc, files)
            support.git(self.source, 'commit', '--allow-empty', '-qm', 'source advanced after reservation')
            support.git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
            return result
        with patch.object(self.pub, '_save', advance_after_save), self.assertRaisesRegex(StateError, 'source advanced'):
            client.request(self.pub, NOW, trigger='manual')
        self.assertEqual(client.requests_started, 0)
        self.assertEqual(transport.urls, [])
        requests = self.store.load()[1]['requests']
        self.assertEqual(len(requests), 1)
        self.assertEqual((requests[0]['at_utc'], requests[0]['outcome']), (NOW, 'reserved'))


if __name__ == '__main__':
    unittest.main()
