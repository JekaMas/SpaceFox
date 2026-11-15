"""Directed controls for the retained catalog/schedule shared-quota scenarios."""
from copy import deepcopy
import unittest

from tests import test_current_metadata_publisher as metadata
from tools.spacefox.catalog_refresh import CatalogRefresh
from tools.spacefox.publisher import Publisher, StateError


class CatalogQuotaPeerTest(unittest.TestCase):
    def test_four_schedule_reservations_reopen_then_catalog_and_due_schedule(self):
        helper = metadata.CurrentMetadataPublisherTest()
        pages, files = metadata.captured()
        now = metadata.NOW
        with helper.authority() as (pub, store, code):
            helper.primary(pub, now, accept=True)
            for _ in range(3):
                helper.primary(pub, now)
            preserved = deepcopy(helper.preserved(pub))
            transport = metadata.CapturedTransport(pub, pages, files)
            first = CatalogRefresh(pub, transport=transport)
            self.assertEqual(first.run(now, max_requests=2).requests, 2)
            prefix = deepcopy(first.journal['staging']['pages'])
            pub = Publisher(store, code)
            pub.reconcile(None)
            transport.pub = pub
            resumed = CatalogRefresh(pub, transport=transport)
            self.assertEqual(resumed.run(now).requests, 1)
            self.assertEqual(resumed.journal['staging']['pages'][:2], prefix)
            self.assertEqual([x['url'] for x in transport.calls],
                             [x['url'] for x in pages['coverage']['pages'][:3]])
            self.assertEqual([r['purpose'] for r in pub.ledger['requests']],
                             ['schedule'] * 4 + ['catalog'] * 3)
            self.assertEqual(resumed.run(now).status, 'yielded')
            due = now + pub.policy.normal_interval_seconds
            token = pub.reserve(pub.head, due)
            self.assertIsNotNone(token)
            pub.finish_request(pub.head, token, due, 'success')
            self.assertEqual(helper.preserved(pub), preserved)

    def test_manual_fifteenth_slot_blocks_queued_stale_and_fresh_collectors(self):
        helper = metadata.CurrentMetadataPublisherTest()
        pages, files = metadata.captured()
        now = metadata.NOW
        with helper.authority() as (pub, store, code):
            helper.primary(pub, now, accept=True)
            transport = metadata.CapturedTransport(pub, pages, files)
            collector = CatalogRefresh(pub, transport=transport)
            self.assertEqual(collector.run(now, max_requests=1).requests, 1)
            prefix = deepcopy(collector.journal['staging']['pages'])
            preserved = deepcopy(helper.preserved(pub))
            for _ in range(12):
                token = pub.reserve(pub.head, now, trigger='extra')
                pub.finish_request(pub.head, token, now, 'success')
            self.assertEqual(len(pub.ledger['requests']), 14)
            stale = Publisher(store, code)
            stale.reconcile(None)
            token = pub.reserve(pub.head, now, trigger='manual')
            pub.finish_request(pub.head, token, now, 'success')
            final_head = pub.head
            self.assertEqual(len(pub.ledger['requests']), 15)
            self.assertEqual(pub.ledger['requests'][-1]['trigger'], 'manual')
            transport.pub = stale
            with self.assertRaises(StateError):
                CatalogRefresh(stale, transport=transport).run(now)
            fresh = Publisher(store, code)
            fresh.reconcile(None)
            transport.pub = fresh
            queued = CatalogRefresh(fresh, transport=transport)
            self.assertEqual(queued.run(now).status, 'yielded')
            self.assertEqual(queued.journal['staging']['pages'], prefix)
            self.assertEqual(len(transport.calls), 1)
            self.assertEqual(fresh.head, final_head)
            self.assertEqual(helper.preserved(fresh), preserved)


if __name__ == '__main__':
    unittest.main()
