"""Versioned ordering policy at the real publisher/Git boundary."""
import unittest
from tests.test_catalog_refresh import CatalogRefreshTest
from tools.spacefox.catalog_refresh import CatalogRefresh

class MetadataStableOrderTest(unittest.TestCase):
    def test_new_policy_is_explicit_and_legacy_url_stays_unchanged(self):
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, _, _, pub, _):
            legacy = CatalogRefresh(pub)
            self.assertNotIn('ordering=', legacy._url('sites', 0))
            ordered = CatalogRefresh(pub, stable_sites_order=True)
            self.assertEqual(3, ordered.journal['schemaVersion'])
            self.assertIn('ordering=id', ordered._url('sites', 0))

    def test_migrate_partial_prefix_and_complete_ordered_sites(self):
        from copy import deepcopy
        from tests.test_metadata_page_policy import source_server, encoded, suffix
        from tools.spacefox.publisher import StateError
        from urllib.parse import urlsplit
        counts = dict(countries=1, organizations=1, models=1, sites=4)
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, _, pub, _):
            with source_server(remote, counts=counts) as (state, _, origin):
                options = dict(origin=origin, local_http=True, page_size=2)
                legacy = CatalogRefresh(pub, **options)
                self.assertEqual('partial', legacy.run(1001, max_requests=4).status)
                prefix = deepcopy(legacy.journal['staging']['pages'])
                cache = deepcopy(legacy.journal['cache'])
                self.assertEqual(['countries','organizations','models','sites'], [p['collection'] for p in prefix])
                stable = CatalogRefresh(pub, stable_sites_order=True, **options)
                self.assertEqual(prefix[:3], stable.journal['staging']['pages'])
                self.assertEqual(cache, {u: {k:v for k,v in m.items() if k != 'pageSize'} for u,m in stable.journal['cache'].items()})
                rows = state['rows']['sites']
                def path(offset):
                    return suffix(3, 2, offset) + '&ordering=id'
                for offset in (0, 2):
                    raw = dict(count=4, results=rows[offset:offset+2],
                               next=origin+path(2) if offset == 0 else None,
                               previous=None if offset == 0 else origin+path(0))
                    state['overrides'][path(offset)] = encoded(raw)
                # Query parameter order is irrelevant to validation; match the
                # actual canonical request when preparing loopback responses.
                for offset in (0, 2):
                    actual = urlsplit(stable._url('sites', offset, 2)).path + '?' + urlsplit(stable._url('sites', offset, 2)).query
                    state['overrides'][actual] = state['overrides'][path(offset)]
                self.assertEqual('complete', stable.run(1001, max_requests=2).status)
                candidate = stable.current()
                self.assertEqual(counts, candidate['coverage']['counts'])
                self.assertEqual(prefix[:3], candidate['coverage']['pages'][:3])
                self.assertEqual('id', candidate['queryPolicy']['sitesOrdering'])
                self.assertTrue(all('ordering=id' in p['url'] for p in candidate['coverage']['pages'] if p['collection'] == 'sites'))
                head, calls = pub.head, len(state['calls'])
                with self.assertRaises(StateError):
                    CatalogRefresh(pub, **options)
                self.assertEqual((head, calls), (pub.head, len(state['calls'])))
                reopened = CatalogRefresh(pub, stable_sites_order=True, **options)
                self.assertEqual(candidate, reopened.current())

    def test_legacy_complete_candidate_survives_and_304_is_query_scoped(self):
        from copy import deepcopy
        from tests.test_metadata_page_policy import source_server, encoded, MetadataPagePolicyTest
        from tools.spacefox.publisher import StateError
        from urllib.parse import urlsplit
        counts = dict(countries=1, organizations=1, models=1, sites=1)
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, _, pub, _):
            with source_server(remote, counts=counts) as (state, _, origin):
                options = dict(origin=origin, local_http=True, page_size=2)
                old = CatalogRefresh(pub, **options)
                self.assertEqual('complete', old.run(1001, max_requests=4).status)
                old_ref, old_candidate = deepcopy(old.journal['current']), deepcopy(old.current())
                stable = CatalogRefresh(pub, stable_sites_order=True, **options)
                site_url = stable._url('sites', 0, 2)
                actual = urlsplit(site_url).path + '?' + urlsplit(site_url).query
                state['overrides'][actual] = encoded(dict(count=1, next=None, previous=None, results=state['rows']['sites']))
                MetadataPagePolicyTest().primary(pub, 4602)
                state['conditional'] = True
                state['now'] = 4603
                self.assertEqual('complete', stable.run(4603, max_requests=4, restart=True).status)
                self.assertEqual(old_ref, stable.journal['previous'])
                self.assertEqual(old_candidate, __import__('json').loads(stable._read(old_ref)))
                self.assertEqual([304,304,304,200], [p['status'] for p in stable.current()['coverage']['pages']])
                self.assertIsNone(state['calls'][-1][1])
                reopened = CatalogRefresh(pub, stable_sites_order=True, **options)
                self.assertEqual(old_ref, reopened.journal['previous'])
                self.assertEqual(old_candidate, __import__('json').loads(reopened._read(old_ref)))
                head = pub.head
                with self.assertRaises(StateError):
                    CatalogRefresh(pub, stable_sites_order=True, page_size=3, origin=origin, local_http=True)
                self.assertEqual(head, pub.head)

    def test_bad_order_and_altered_next_refuse_before_page_commit(self):
        from tests.test_metadata_page_policy import source_server, encoded
        from tools.spacefox.publisher import StateError
        from urllib.parse import urlsplit
        for failure in ('misordered', 'altered-next'):
            with self.subTest(failure=failure):
                counts = dict(countries=1, organizations=1, models=1, sites=3)
                with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, _, pub, _):
                    with source_server(remote, counts=counts) as (state, _, origin):
                        collector = CatalogRefresh(pub, stable_sites_order=True, origin=origin, local_http=True, page_size=2)
                        url = collector._url('sites', 0, 2)
                        parsed = urlsplit(url)
                        path = parsed.path + '?' + parsed.query
                        rows = state['rows']['sites'][:2]
                        if failure == 'misordered':
                            rows = rows[::-1]
                        next_url = collector._url('sites', 2, 2)
                        if failure == 'altered-next':
                            next_url = next_url.replace('ordering=id', 'ordering=name')
                        state['overrides'][path] = encoded(dict(count=3, next=next_url, previous=None, results=rows))
                        with self.assertRaises(StateError):
                            collector.run(1001, max_requests=4)
                        reopened = CatalogRefresh(pub, stable_sites_order=True, origin=origin, local_http=True, page_size=2)
                        self.assertEqual(['countries','organizations','models'], [p['collection'] for p in reopened.journal['staging']['pages']])
                        self.assertEqual('failed', pub.ledger['requests'][-1]['outcome'])

    def test_default_overlap_then_ordered_walk_completes_after_backoff(self):
        from copy import deepcopy
        from tests.test_metadata_page_policy import source_server, encoded, suffix, MetadataPagePolicyTest
        from tools.spacefox.catalog_refresh import DuplicateSourceIdentity
        from tools.spacefox.publisher import AllowanceUnavailable
        counts = dict(countries=1, organizations=1, models=1, sites=2)
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, _, pub, _):
            with source_server(remote, counts=counts) as (state, _, origin):
                options = dict(origin=origin, local_http=True, page_size=1)
                old = CatalogRefresh(pub, **options)
                self.assertEqual('partial', old.run(1001, max_requests=4).status)
                prefix = deepcopy(old.journal['staging']['pages'][:3])
                MetadataPagePolicyTest().primary(pub, 4600)
                state['now'] = 4601
                path = suffix(3,1,1)
                state['overrides'][path] = encoded(dict(count=2,next=None,previous=origin+suffix(3,1),
                                                        results=[state['rows']['sites'][0]]))
                with self.assertRaises(DuplicateSourceIdentity):
                    old.run(4601)
                self.assertEqual('failed',pub.ledger['requests'][-1]['outcome'])
                self.assertEqual(4901,pub.ledger['backoff_until_utc'])
                before = len(state['calls'])
                stable = CatalogRefresh(pub, stable_sites_order=True, **options)
                head = pub.head
                with self.assertRaises(AllowanceUnavailable):
                    stable.run(4602)
                self.assertEqual((head,before),(pub.head,len(state['calls'])))
                state['now'] = 4901
                self.assertEqual('complete',stable.run(4901,max_requests=2).status)
                self.assertEqual(prefix,stable.current()['coverage']['pages'][:3])
                self.assertEqual([(suffix(3,1,0,True),None),(suffix(3,1,1,True),None)],state['calls'][-2:])
                self.assertEqual(counts,stable.current()['coverage']['counts'])

    def test_complete_legacy_stage_finalizes_before_new_policy(self):
        from unittest.mock import patch
        from copy import deepcopy
        from tests.test_metadata_page_policy import source_server
        counts = dict(countries=1, organizations=1, models=1, sites=1)
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, _, pub, _):
            with source_server(remote, counts=counts) as (state, _, origin):
                options = dict(origin=origin, local_http=True, page_size=1)
                old = CatalogRefresh(pub, **options)
                # Simulate a crash after the final page's real durable save and
                # before complete-candidate construction.
                with patch.object(old, '_candidate', side_effect=RuntimeError('interrupted after final save')):
                    with self.assertRaises(RuntimeError):
                        old.run(1001, max_requests=4)
                pages = deepcopy(old.journal['staging']['pages'])
                calls = list(state['calls'])
                stable = CatalogRefresh(pub, stable_sites_order=True, origin=origin, local_http=True,
                                        page_size=100, migrate_page_size=True)
                self.assertEqual('complete', stable.run(1002).status)
                self.assertEqual(calls, state['calls'])
                self.assertEqual(2, stable.current()['schemaVersion'])
                self.assertEqual(3, stable.journal['schemaVersion'])
                self.assertEqual(pages, stable.current()['coverage']['pages'])
                self.assertEqual(counts, stable.current()['coverage']['counts'])
                reopened = CatalogRefresh(pub, stable_sites_order=True, origin=origin, local_http=True, page_size=100)
                self.assertEqual(pages, reopened.current()['coverage']['pages'])
                from tools.spacefox.publisher import StateError
                with self.assertRaises(StateError):
                    CatalogRefresh(pub, origin=origin, local_http=True, page_size=100)
                self.assertEqual(calls, state['calls'])

    def test_ordered_stage_page_size_migration_keeps_schema_and_started_policy(self):
        from tests.test_metadata_page_policy import source_server
        from tools.spacefox.publisher import StateError
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, _, pub, _):
            with source_server(remote, counts=dict(countries=2, organizations=1, models=1, sites=1)) as (state, _, origin):
                initial = CatalogRefresh(pub, origin=origin, local_http=True, page_size=1, stable_sites_order=True)
                self.assertEqual('partial', initial.run(1001).status)
                prefix = initial.journal['staging']['pages'][:]
                migrated = CatalogRefresh(pub, origin=origin, local_http=True, page_size=100,
                                          migrate_page_size=True, stable_sites_order=True)
                self.assertEqual(3, migrated.journal['schemaVersion'])
                self.assertEqual(prefix, migrated.journal['staging']['pages'])
                self.assertEqual(dict(countries=1, organizations=100, models=100, sites=100),
                                 migrated.journal['staging']['pageSizes'])
                self.assertEqual('partial', migrated.run(1001).status)
                head, calls = pub.head, len(state['calls'])
                with self.assertRaises(StateError):
                    CatalogRefresh(pub, origin=origin, local_http=True, page_size=1, stable_sites_order=True)
                # Execute the actual pre-policy public writer against schema 3.
                import hashlib, types, sys
                from pathlib import Path
                raw = (Path(__file__).resolve().parent / 'fixtures/metadata-stable-order/legacy_catalog_refresh.py.txt').read_bytes()
                self.assertEqual('6b3323c1c116e00f438cd1c04fb98c891376b0fdf18d31cbbb35169e7a8835c2',
                                 hashlib.sha256(raw).hexdigest())
                module = types.ModuleType('tools.spacefox._legacy_catalog_refresh_for_policy_test')
                module.__package__ = 'tools.spacefox'
                sys.modules[module.__name__] = module
                try:
                    exec(compile(raw, 'frozen-public-catalog-refresh.py', 'exec'), module.__dict__)
                    with self.assertRaises(StateError):
                        module.CatalogRefresh(pub, origin=origin, local_http=True, page_size=100)
                finally:
                    del sys.modules[module.__name__]
                self.assertEqual((head, calls), (pub.head, len(state['calls'])))
