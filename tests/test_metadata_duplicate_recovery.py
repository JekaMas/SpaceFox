"""Duplicate refusal and traversal recovery through real Git and loopback HTTP."""
from copy import deepcopy
import json
import subprocess
import sys
import unittest

from tests.test_catalog_refresh import CatalogRefreshTest
from tests.test_metadata_page_policy import MetadataPagePolicyTest, source_server, suffix, encoded
from tools.spacefox.catalog_refresh import CatalogRefresh, RefreshError


class MetadataDuplicateRecoveryTest(unittest.TestCase):
    def test_repeated_overlap_abandons_prefix_then_completes_without_freshening(self):
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, store, pub, _):
            with source_server(remote, counts=dict(countries=2, organizations=1, models=1, sites=1)) as (state, _, origin):
                options = dict(origin=origin, local_http=True, page_size=1)
                before = MetadataPagePolicyTest().preserve(pub)
                first, second = suffix(0, 1), suffix(0, 1, 1)
                duplicate = dict(count=2, next=None, previous=origin + first,
                                 results=[deepcopy(state['rows']['countries'][0])])
                state['overrides'][second] = encoded(duplicate)
                for now in (1001, 1303):
                    state['now'] = now
                    collector = CatalogRefresh(pub, **options)
                    self.assertEqual('partial', collector.run(now).status)
                    self.assertEqual(1, len(collector.journal['staging']['pages']))
                    with self.assertRaisesRegex(RefreshError, 'duplicate source identity'):
                        collector.run(now + 1)
                    reopened = CatalogRefresh(pub, **options)
                    self.assertEqual([], reopened.journal['staging']['pages'])
                    self.assertEqual({}, reopened.journal['cache'])
                    self.assertEqual('failed', pub.ledger['requests'][-1]['outcome'])
                    self.assertEqual(before, MetadataPagePolicyTest().preserve(pub))
                del state['overrides'][second]
                state['now'] = 1605
                # Quota may yield after six attempts; service launch authority
                # through the real publisher before continuing at the next hour.
                self.assertEqual('partial', CatalogRefresh(pub, **options).run(1605).status)
                self.assertEqual('partial', CatalogRefresh(pub, **options).run(1605).status)
                state['now'] = 5300
                MetadataPagePolicyTest().primary(pub, 5300)
                before2 = MetadataPagePolicyTest().preserve(pub)
                result = CatalogRefresh(pub, **options).run(5300, max_requests=4)
                self.assertEqual('complete', result.status)
                current = CatalogRefresh(pub, **options).current()
                self.assertEqual(dict(countries=2, organizations=1, models=1, sites=1), current['coverage']['counts'])
                self.assertEqual(before2, MetadataPagePolicyTest().preserve(pub))
                self.assertEqual([first, second, first, second, first, second], [path for path, _ in state['calls'][:6]])
                self.assertTrue(all(tag is None for _, tag in state['calls']))
                self.assertEqual(1605, current['coverage']['pages'][0]['validatedUtc'])

    def test_duplicate_retains_completed_tables_and_original_epochs(self):
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, store, pub, _):
            with source_server(remote, counts=dict(countries=1, organizations=1, models=1, sites=2)) as (state, _, origin):
                options = dict(origin=origin, local_http=True, page_size=1)
                self.assertEqual('partial', CatalogRefresh(pub, **options).run(1001, max_requests=4).status)
                prior = deepcopy(CatalogRefresh(pub, **options).journal['staging']['pages'])
                self.assertEqual(['countries', 'organizations', 'models', 'sites'], [p['collection'] for p in prior])
                path = suffix(3, 1, 1)
                state['overrides'][path] = encoded(dict(count=2, next=None, previous=origin + suffix(3, 1),
                                                        results=[deepcopy(state['rows']['sites'][0])]))
                before = MetadataPagePolicyTest().preserve(pub)
                with self.assertRaisesRegex(RefreshError, 'duplicate source identity'):
                    CatalogRefresh(pub, **options).run(1002)
                stage = CatalogRefresh(pub, **options).journal['staging']
                self.assertEqual(prior[:3], stage['pages'])
                self.assertEqual([1001] * 3, [p['validatedUtc'] for p in stage['pages']])
                self.assertEqual(before, MetadataPagePolicyTest().preserve(pub))
                self.assertEqual('failed', pub.ledger['requests'][-1]['outcome'])
                self.assertFalse(any('/pads/' in key for key in CatalogRefresh(pub, **options).journal['cache']))
                del state['overrides'][path]
                state['now'] = 4602
                MetadataPagePolicyTest().primary(pub, 4602)
                before = MetadataPagePolicyTest().preserve(pub)
                result = CatalogRefresh(pub, **options).run(4602, max_requests=4)
                self.assertEqual('complete', result.status)
                candidate = CatalogRefresh(pub, **options).current()
                self.assertEqual(prior[:3], candidate['coverage']['pages'][:3])
                self.assertEqual(dict(countries=1, organizations=1, models=1, sites=2), candidate['coverage']['counts'])
                self.assertEqual(before, MetadataPagePolicyTest().preserve(pub))

    def test_cli_duplicate_refusal_and_recovery(self):
        with CatalogRefreshTest().authority(real_source=True, with_launch=False) as (root, source, remote, store, pub, _):
            with source_server(remote, counts=dict(countries=2, organizations=1, models=1, sites=1)) as (state, _, origin):
                live = root / 'live.json'
                live.write_text('null')
                def collect(head, now, limit=1):
                    return subprocess.run([sys.executable, '-B', str(source / 'tools/refresh_catalog.py'), 'collect',
                        '--remote', str(remote), '--local-http', '--origin', origin, '--page-size', '1',
                        '--expected-head', head, '--live-observation', str(live), '--now', str(now),
                        '--max-requests', str(limit)], capture_output=True, text=True, timeout=90)
                first = collect(pub.head, 1001)
                self.assertEqual(0, first.returncode, first.stderr)
                second = suffix(0, 1, 1)
                state['overrides'][second] = encoded(dict(count=2, next=None, previous=origin + suffix(0, 1),
                                                          results=[deepcopy(state['rows']['countries'][0])]))
                failed = collect(store.load()[0], 1002)
                self.assertEqual(2, failed.returncode)
                self.assertIn('duplicate source identity', failed.stderr)
                pub = MetadataPagePolicyTest().reopen(store, pub)
                self.assertEqual([], CatalogRefresh(pub, origin=origin, local_http=True, page_size=1).journal['staging']['pages'])
                before = MetadataPagePolicyTest().preserve(pub)
                del state['overrides'][second]
                state['now'] = 1302
                resumed = collect(pub.head, 1302, 4)
                self.assertEqual(0, resumed.returncode, resumed.stderr)
                pub = MetadataPagePolicyTest().reopen(store, pub)
                self.assertEqual(before, MetadataPagePolicyTest().preserve(pub))
                MetadataPagePolicyTest().primary(pub, 5000)
                before = MetadataPagePolicyTest().preserve(pub)
                state['now'] = 5000
                finish = collect(pub.head, 5000, 4)
                self.assertEqual(0, finish.returncode, finish.stderr)
                self.assertEqual('complete', json.loads(finish.stdout)['status'])
                pub = MetadataPagePolicyTest().reopen(store, pub)
                self.assertEqual(before, MetadataPagePolicyTest().preserve(pub))

    def test_expired_prefix_restarts_without_renewing_old_page_dates(self):
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, store, pub, _):
            with source_server(remote, counts=dict(countries=2, organizations=1, models=1, sites=1)) as (state, _, origin):
                options = dict(origin=origin, local_http=True, page_size=1, max_source_age_seconds=60)
                self.assertEqual('partial', CatalogRefresh(pub, **options).run(1001).status)
                old = deepcopy(CatalogRefresh(pub, **options).journal['staging']['pages'][0])
                before = MetadataPagePolicyTest().preserve(pub)
                state['now'] = 1062
                self.assertEqual('partial', CatalogRefresh(pub, **options).run(1062).status)
                stage = CatalogRefresh(pub, **options).journal['staging']
                self.assertEqual([suffix(0, 1), suffix(0, 1)], [p for p, _ in state['calls']])
                self.assertEqual(1001, old['validatedUtc'])
                self.assertEqual(1062, stage['pages'][0]['validatedUtc'])
                self.assertEqual(before, MetadataPagePolicyTest().preserve(pub))


if __name__ == '__main__':
    unittest.main()
