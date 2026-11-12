"""Regression: omission dates come from that record's own source page."""
from copy import deepcopy
import unittest

from tests.test_catalog_refresh import CatalogRefreshTest


class RetainedSourceDateTest(unittest.TestCase):
    def test_missing_ids_retain_unequal_page_validation_dates(self):
        fixture = CatalogRefreshTest()
        with fixture.authority() as (_, _, _, _, pub, transport):
            for now in (1001, 1002, 1003, 1004):
                transport.now = now
                fixture.collector(pub, transport).run(now)
            prior = fixture.collector(pub, transport).current()
            self.assertEqual(1004, prior['source']['observedToUtc'])
            self.assertEqual(1001, prior['coverage']['recordValidatedUtc']['countries']['999'])
            self.assertEqual(1003, prior['coverage']['recordValidatedUtc']['models']['72'])
            now = fixture.next_hour(pub, transport, 4600)
            transport.data = deepcopy(transport.data)
            transport.data['countries'] = [transport.data['countries'][0]]
            transport.data['models'] = [transport.data['models'][0]]
            collector = fixture.collector(pub, transport)
            result = collector.run(now, restart=True, max_requests=4)
            # Literal prior attempt times1001..1004 do not all expire at4601.
            # The fourth request yields to reserved launch headroom; the old
            # complete snapshot is correctly still current until resumption.
            self.assertEqual(('yielded', 3), (result.status, result.requests))
            self.assertEqual(prior, collector.current())
            self.assertEqual(7, len(pub.ledger['requests']))
            transport.now = 4604
            result = fixture.collector(pub, transport).run(4604)
            self.assertEqual(('complete', 1), (result.status, result.requests))
            collector = fixture.collector(pub, transport)
            current = collector.current()
            self.assertEqual(1001, current['retainedMissing']['countries'][0]['lastObservedUtc'])
            self.assertEqual(1003, current['retainedMissing']['models'][0]['lastObservedUtc'])
            self.assertEqual(prior['reference']['models'][1], current['retainedMissing']['models'][0]['fact'])
            self.assertEqual(1000, pub.ledger['accepted']['entries'][0]['record']['source_validated_utc'])


if __name__ == '__main__':
    unittest.main()
