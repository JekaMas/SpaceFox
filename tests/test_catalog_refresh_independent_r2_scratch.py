"""Independent rejected-page memory witness using real local Git and HTTP."""
import hashlib
import unittest
from unittest.mock import patch

from tests import test_catalog_refresh_independent_r2 as controls
from tools.spacefox.catalog_refresh import CatalogRefresh, RefreshError


class IndependentCatalogR2ScratchTest(unittest.TestCase):
    def test_tentative_journal_refusal_cannot_accumulate_rejected_raw_bodies(self):
        harness = controls.IndependentCatalogR2Test()
        with harness.world() as (pub, _, world, origin, _):
            collector = CatalogRefresh(pub, origin=origin, local_http=True)
            preserved = harness.preserved(pub)
            hashes = []
            # These numeric thresholds cheaply reach the real journal refusal
            # before checkpoint; no collector/save/store/HTTP owner is replaced.
            with patch('tools.spacefox.catalog_refresh.MAX_CATALOG_JOURNAL_BYTES', 600), \
                    patch('tools.spacefox.catalog_refresh.MAX_CATALOG_CORPUS_BYTES', 600):
                for index in range(5):
                    now = 1001 + index * 300
                    world['now'] = now
                    rows = world['rows']['/2.3.0/config/countries/']
                    rows[0]['name'] = 'Rejected literal jurisdiction ' + str(index)
                    body = controls.encoded(dict(count=1, next=None, previous=None, results=rows))
                    hashes.append(hashlib.sha256(body).hexdigest())
                    world['bodies']['/2.3.0/config/countries/'] = body
                    with self.assertRaisesRegex(RefreshError, 'catalog journal byte budget exhausted'):
                        collector.run(now)
                    self.assertEqual(index + 1, len(world['calls']))
                    self.assertEqual(index + 2, len(pub.ledger['requests']))
                    self.assertEqual('failed', pub.ledger['requests'][-1]['outcome'])
                    self.assertEqual(now + 300, pub.ledger['backoff_until_utc'])
                    self.assertEqual([], collector.journal['staging']['pages'])
                    self.assertIsNone(collector.current())
                    self.assertEqual(preserved, harness.preserved(pub))
                    self.assertLessEqual(
                        sum(map(len, collector.objects.values())), 600,
                        'rejected raw bodies cannot grow beyond the finite loaded-corpus bound')
                self.assertEqual(5, len(set(hashes)))
            self.assertEqual({}, collector.objects)
            self.assertIsNone(CatalogRefresh(pub, origin=origin, local_http=True).current())
            # At the exact backoff boundary, the same object may retain a valid
            # page after capacity is sufficient. All five failed slots survive.
            world['now'] = 2501
            outcome = collector.run(2501)
            self.assertEqual(('partial', 1), (outcome.status, outcome.requests))
            self.assertEqual(6, len(world['calls']))
            self.assertEqual(7, len(pub.ledger['requests']))
            self.assertEqual('success', pub.ledger['requests'][-1]['outcome'])
            page = collector.journal['staging']['pages'][0]
            self.assertEqual(hashes[-1], page['body']['sha256'])
            self.assertEqual(2500, page['validatedUtc'])
            self.assertEqual(preserved, harness.preserved(pub))


if __name__ == '__main__':
    unittest.main()
