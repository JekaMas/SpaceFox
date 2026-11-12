"""Independent R3 save refusal after a successful HTTP-result commit."""
from copy import deepcopy
import hashlib
import json
import unittest
from unittest.mock import patch

from tests.test_catalog_refresh_independent_r3 import IndependentCatalogR3Test
from tools.spacefox.catalog_refresh import CatalogRefresh, RefreshError


class IndependentCatalogR3SaveTest(unittest.TestCase):
    def test_page_save_object_limit_preserves_prior_prefix_and_consumed_success_then_retries(self):
        harness = IndependentCatalogR3Test()
        with harness.world() as (pub, store, world, origin, _, _):
            collector = CatalogRefresh(pub, origin=origin, local_http=True)
            preserved = harness.preserved(pub)
            self.assertEqual('partial', collector.run(1002).status)
            prefix = deepcopy(collector.journal)
            journal_ref = pub.ledger['catalog_refresh']
            paths = store._git('ls-tree', '-r', '--name-only', pub.head, 'catalog-refresh').stdout
            self.assertEqual(2, len(paths.splitlines()))  # One journal, one country body.
            world['now'] = 1003
            # Real preflight now needs three retained objects: journal + two
            # pages. Only the numerical4096-object threshold becomes2.
            with patch('tools.spacefox.catalog_refresh.MAX_CATALOG_OBJECTS', 2):
                with self.assertRaisesRegex(RefreshError, 'catalog corpus exceeds finite working-set bound'):
                    collector.run(1003)
            self.assertEqual({}, collector.objects)
            self.assertIsNone(collector.current())
            self.assertEqual(prefix, collector.journal)
            self.assertEqual(prefix, CatalogRefresh(pub, origin=origin, local_http=True).journal)
            self.assertEqual(journal_ref, pub.ledger['catalog_refresh'])
            self.assertEqual(paths, store._git('ls-tree', '-r', '--name-only', pub.head, 'catalog-refresh').stdout)
            self.assertEqual([(1000, 'schedule', 'success'), (1002, 'catalog', 'success'),
                              (1003, 'catalog', 'success')],
                             [(item['at_utc'], item['purpose'], item['outcome']) for item in pub.ledger['requests']])
            self.assertIsNone(pub.ledger['backoff_until_utc'])
            self.assertEqual(2, len(world['calls']))
            self.assertEqual(preserved, harness.preserved(pub))
            world['now'] = 1004
            outcome = collector.run(1004, max_requests=4)
            self.assertEqual(('complete', 3), (outcome.status, outcome.requests))
            harness.assert_complete(collector, world, [1000, 1002, 1002, 1002])
            self.assertEqual(world['calls'][1]['path'], world['calls'][2]['path'])
            self.assertEqual([None] * 5, [call['etag'] for call in world['calls']])
            self.assertEqual([1000, 1002, 1003, 1004, 1004, 1004],
                             [item['at_utc'] for item in pub.ledger['requests']])
            self.assertEqual(['success'] * 6, [item['outcome'] for item in pub.ledger['requests']])
            self.assertEqual(preserved, harness.preserved(pub))
            rejected_hash = hashlib.sha256(world['bodies']['/2.3.0/agencies/']).hexdigest()
            self.assertEqual(rejected_hash, collector.current()['coverage']['pages'][1]['body']['sha256'])
            print(json.dumps(dict(control='intermediate-page-save-object-count-refusal',
                                  calls=world['calls'], slots=6, objectCountLimit=2,
                                  sourceEpochs=[1000, 1002, 1002, 1002])))


if __name__ == '__main__':
    unittest.main()
