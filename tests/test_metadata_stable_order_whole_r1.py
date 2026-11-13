"""Whole-review discriminators at real Git and loopback boundaries."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from tests.test_catalog_refresh import CatalogRefreshTest
from tests.test_metadata_page_policy import MetadataPagePolicyTest, source_server, suffix
from tools.spacefox.catalog_refresh import CatalogRefresh
from tools.spacefox.publisher import StateError


class MetadataStableOrderWholeR1Test(unittest.TestCase):
    def test_abandoned_complete_legacy_stage_selects_ordering_before_new_traversal(self):
        for reason in ('expired', 'explicit-restart'):
            with self.subTest(reason=reason):
                with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, _, pub, _):
                    with source_server(remote, counts=dict(countries=1, organizations=1, models=1, sites=1)) as (state, _, origin):
                        options = dict(origin=origin, local_http=True, page_size=1,
                                       max_source_age_seconds=60 if reason == 'expired' else 86400)
                        old = CatalogRefresh(pub, **options)
                        with patch.object(old, '_candidate', side_effect=RuntimeError('crash after durable final page')):
                            with self.assertRaises(RuntimeError):
                                old.run(1001, max_requests=4)
                        original_pages = deepcopy(old.journal['staging']['pages'])
                        MetadataPagePolicyTest().primary(pub, 4601)
                        accepted = deepcopy(pub.ledger['accepted'])
                        state['now'] = 4602
                        stable = CatalogRefresh(pub, stable_sites_order=True, **options)
                        self.assertEqual('partial', stable.run(4602, max_requests=1,
                                         restart=reason == 'explicit-restart').status)
                        self.assertEqual(3, stable.journal['schemaVersion'])
                        # Reopen actual durable state; a rollback writer cannot resume
                        # a fresh traversal after the requested policy took effect.
                        with self.assertRaises(StateError):
                            CatalogRefresh(pub, **options)
                        reopened = CatalogRefresh(pub, stable_sites_order=True, **options)
                        self.assertEqual('complete', reopened.run(4602, max_requests=3).status)
                        self.assertEqual(3, reopened.current()['schemaVersion'])
                        self.assertEqual((suffix(3, 1, 0, True), None), state['calls'][-1])
                        self.assertEqual([1001] * 4, [p['validatedUtc'] for p in original_pages])
                        self.assertEqual([4602] * 4, [p['validatedUtc'] for p in reopened.current()['coverage']['pages']])
                        self.assertEqual(accepted, pub.ledger['accepted'])

    def test_scheduled_size_migration_expiry_commits_policy_before_http(self):
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, store, pub, _):
            with source_server(remote, counts=dict(countries=1, organizations=1, models=1, sites=1)) as (state, _, origin):
                old = CatalogRefresh(pub, origin=origin, local_http=True, page_size=1, max_source_age_seconds=60)
                with patch.object(old, '_candidate', side_effect=RuntimeError('crash after durable final page')):
                    with self.assertRaises(RuntimeError):
                        old.run(1001, max_requests=4)
                MetadataPagePolicyTest().primary(pub, 4601)
                state['now'] = 4602
                options = dict(origin=origin, local_http=True, page_size=100, migrate_page_size=True,
                               stable_sites_order=True, max_source_age_seconds=60)
                # Observe schema at the real source's request boundary, before a
                # new page exists. State load/replay is the production reader.
                def inspect_durable_policy():
                    from tools.spacefox.publisher import Publisher
                    other = Publisher(store, pub.running_code)
                    other.reconcile(None)
                    with self.assertRaises(StateError):
                        CatalogRefresh(other, origin=origin, local_http=True, page_size=100, max_source_age_seconds=60)
                    durable = CatalogRefresh(other, **options)
                    self.assertEqual(3, durable.journal['schemaVersion'])
                    self.assertEqual([], durable.journal['staging']['pages'])
                    state['policy_checked_before_http'] = True
                state['hook'] = inspect_durable_policy
                stable = CatalogRefresh(pub, **options)
                self.assertEqual('complete', stable.run(4602, max_requests=4).status)
                self.assertTrue(state.get('policy_checked_before_http'))
                self.assertEqual((suffix(3, 100, 0, True), None), state['calls'][-1])
                self.assertEqual(dict.fromkeys(('countries', 'organizations', 'models', 'sites'), 100),
                                 stable.current()['queryPolicy']['pageSizes'])

    def test_complete_legacy_candidate_checkpoint_failure_rolls_back_atomically(self):
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, store, pub, _):
            with source_server(remote, counts=dict(countries=1, organizations=1, models=1, sites=1)) as (state, _, origin):
                options = dict(origin=origin, local_http=True, page_size=1)
                old = CatalogRefresh(pub, **options)
                with patch.object(old, '_candidate', side_effect=RuntimeError('crash after durable final page')):
                    with self.assertRaises(RuntimeError):
                        old.run(1001, max_requests=4)
                original = deepcopy(old.journal)
                head, calls = pub.head, list(state['calls'])
                stable = CatalogRefresh(pub, stable_sites_order=True, **options)
                # Fault injection stops the actual atomic persistence entry. It
                # does not fabricate a committed candidate or successful CAS.
                with patch.object(pub, 'checkpoint_catalog', side_effect=RuntimeError('checkpoint unavailable')):
                    with self.assertRaisesRegex(RuntimeError, 'checkpoint unavailable'):
                        stable.run(1002)
                self.assertEqual((head, calls), (store.load()[0], state['calls']))
                self.assertEqual(original, stable.journal)
                self.assertEqual({}, stable.objects)
                reopened = CatalogRefresh(pub, stable_sites_order=True, **options)
                self.assertEqual('complete', reopened.run(1002).status)
                self.assertEqual(calls, state['calls'])
                self.assertEqual(original['staging']['pages'], reopened.current()['coverage']['pages'])
                self.assertEqual(1, reopened.current()['schemaVersion'])
                self.assertEqual(3, reopened.journal['schemaVersion'])
                with self.assertRaises(StateError):
                    CatalogRefresh(pub, **options)
