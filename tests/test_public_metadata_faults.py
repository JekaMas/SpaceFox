"""Current schema-3 save/refusal controls over the finite captured 33-page corpus.

A committed valid prefix is seeded through the real journal/save/normalizer.
These tests qualify the following HTTP and save boundary, not earlier traversal.
All page bodies are unchanged captures; response dates and faults are controlled.
"""
from copy import deepcopy
import hashlib
import unittest
from unittest.mock import patch

from tests import test_current_metadata_publisher as fixture
from tools.spacefox import catalog_refresh as owner
from tools.spacefox.catalog_refresh import CatalogRefresh, RefreshError
from tools.spacefox.provider import Response
from tools.spacefox.publisher import Publisher

NOW = fixture.NOW


class Transport(fixture.CapturedTransport):
    bad = None
    conditional = False

    def get(self, url, etag):
        response = super().get(url, etag)
        headers = dict(response.headers, etag='"captured-' + hashlib.sha256(url.encode()).hexdigest() + '"')
        if self.bad is not None:
            return Response(200, headers, self.bad)
        if self.conditional:
            if etag != headers['etag']:
                raise AssertionError('exact URL cache condition absent')
            return Response(304, headers, b'')
        return Response(200, headers, response.body)


class PublicMetadataFaults(unittest.TestCase):
    def seeded(self, pub, *, complete=False, prefix=0):
        candidate, files = fixture.captured()
        transport = Transport(pub, candidate, files)
        transport.epoch = NOW
        collector = CatalogRefresh(pub, transport=transport)
        pages = deepcopy(candidate['coverage']['pages'])
        self.assertEqual(len(pages), 33)
        for page in pages:
            raw = files['objects/' + page['body']['sha256'] + '.json']
            self.assertEqual(collector._put(raw), page['body'])
            page.update(validatedUtc=NOW, receivedUtc=NOW, status=200,
                        etag='"captured-' + hashlib.sha256(page['url'].encode()).hexdigest() + '"')
        collector.journal['staging'] = dict(startedUtc=NOW, pages=pages,
                                            pageSizes=dict(fixture.SIZES))
        collector.journal['cache'] = {p['url']: collector._cache_entry(p, fixture.SIZES[p['collection']])
                                      for p in pages}
        if complete:
            collector._save(NOW)
            self.assertEqual(collector.run(NOW).status, 'complete')
        collector.journal['staging'] = dict(startedUtc=NOW, pages=pages[:prefix],
                                            pageSizes=dict(fixture.SIZES))
        # Cache entries outside a partial prefix exist only when a complete
        # previous generation actually supplied their conditional raw bodies.
        if not complete:
            collector.journal['cache'] = {p['url']: collector._cache_entry(p, fixture.SIZES[p['collection']])
                                          for p in pages[:prefix]}
        collector._save(NOW)
        return collector, transport, pages

    def assert_preserved(self, pub, expected, source=NOW):
        self.assertEqual(fixture.CurrentMetadataPublisherTest().preserved(pub), expected)
        self.assertEqual(pub.ledger['selection_validated_utc'], source)

    def test_completion_refusal_keeps_four_304_pages_and_retries_without_http(self):
        helper = fixture.CurrentMetadataPublisherTest()
        with helper.authority() as (pub, store, code):
            helper.primary(pub, NOW, accept=True)
            accepted = deepcopy(helper.preserved(pub))
            c, transport, pages = self.seeded(pub, complete=True, prefix=29)
            old_current = deepcopy(c.journal['current'])
            transport.epoch = NOW + 1
            transport.conditional = True
            # 33 raw pages + previous candidate + journal fit; a second
            # complete candidate exceeds this exact finite save boundary.
            with patch.object(owner, 'MAX_CATALOG_OBJECTS', 35):
                with self.assertRaisesRegex(RefreshError, 'finite working-set'):
                    c.run(NOW + 1, max_requests=4)
            self.assertEqual(c.objects, {})
            self.assertEqual(c.journal['current'], old_current)
            staged = deepcopy(c.journal['staging']['pages'])
            self.assertEqual(len(staged), 33)
            self.assertEqual([p['status'] for p in staged[-4:]], [304] * 4)
            self.assertEqual([p['body'] for p in staged], [p['body'] for p in pages])
            self.assertEqual([p['validatedUtc'] for p in staged], [NOW] * 29 + [NOW + 1] * 4)
            reopened = CatalogRefresh(Publisher(store, code))
            self.assertEqual(reopened.journal, c.journal)
            self.assertEqual(len(transport.calls), 4)
            self.assertEqual(c.run(NOW + 1).requests, 0)
            self.assertEqual(len(transport.calls), 4)
            self.assertEqual(c.journal['previous'], old_current)
            self.assertIsNone(c.journal['staging'])
            self.assertEqual(c.current()['coverage']['counts'],
                             {'countries': 103, 'organizations': 350, 'models': 532, 'sites': 251})
            self.assertEqual(len(pub.ledger['requests']), 5)
            self.assert_preserved(pub, accepted)

    def test_five_bad_bodies_leave_no_scratch_and_consume_exact_failed_slots(self):
        helper = fixture.CurrentMetadataPublisherTest()
        with helper.authority() as (pub, store, code):
            helper.primary(pub, NOW, accept=True)
            accepted = deepcopy(helper.preserved(pub))
            c, transport, _ = self.seeded(pub)
            for index in range(5):
                transport.epoch = NOW + 1 + index * 300
                # Technical malformed bounded JSON, no invented display text.
                transport.bad = b'{' + b' ' * index
                with self.assertRaises(RefreshError):
                    c.run(transport.epoch)
                self.assertEqual(c.objects, {})
                fresh = CatalogRefresh(Publisher(store, code))
                self.assertEqual(fresh.journal['staging']['pages'], [])
                self.assertEqual(fresh.journal['cache'], {})
                self.assertEqual(fresh.journal['current'], None)
                self.assertEqual(pub.ledger['backoff_until_utc'], NOW + 301 + index * 300)
                self.assertEqual([r['outcome'] for r in pub.ledger['requests']],
                                 ['success'] + ['failed'] * (index + 1))
                self.assert_preserved(pub, accepted)
            transport.bad = None
            transport.epoch = NOW + 1501
            self.assertEqual(c.run(transport.epoch).status, 'partial')
            self.assertEqual(c.journal['staging']['pages'][0]['validatedUtc'], NOW + 1501)
            self.assertEqual(len(transport.calls), 6)
            self.assertEqual(len(pub.ledger['requests']), 7)
            self.assertEqual([r['outcome'] for r in pub.ledger['requests']],
                             ['success'] + ['failed'] * 5 + ['success'])
            self.assert_preserved(pub, accepted)

    def test_two_bad_pages_keep_prefix_then_complete_with_six_http_seven_slots(self):
        helper = fixture.CurrentMetadataPublisherTest()
        with helper.authority() as (pub, store, code):
            helper.primary(pub, NOW, accept=True)
            accepted = deepcopy(helper.preserved(pub))
            c, transport, _ = self.seeded(pub, prefix=29)
            self.assertEqual(c.run(NOW).status, 'partial')
            prefix = deepcopy(c.journal['staging']['pages'])
            self.assertEqual(len(prefix), 30)
            for instant, bad in [(NOW + 1, b'{'), (NOW + 301, b'[]')]:
                transport.epoch, transport.bad = instant, bad
                with self.assertRaises(RefreshError):
                    c.run(instant)
                self.assertEqual(c.objects, {})
                self.assertEqual(c.journal['staging']['pages'], prefix)
                self.assertEqual(CatalogRefresh(Publisher(store, code)).journal, c.journal)
            transport.epoch, transport.bad = NOW + 601, None
            self.assertEqual(c.run(NOW + 601, max_requests=3).status, 'complete')
            self.assertEqual(len(transport.calls), 6)
            self.assertEqual(len(pub.ledger['requests']), 7)
            self.assertEqual([p['validatedUtc'] for p in c.current()['coverage']['pages']],
                             [NOW] * 30 + [NOW + 601] * 3)
            self.assertEqual(transport.calls[1]['url'], transport.calls[2]['url'])
            self.assertEqual(transport.calls[2]['url'], transport.calls[3]['url'])
            self.assert_preserved(pub, accepted)

    def test_save_preflight_restores_prefix_and_repeats_only_uncommitted_url(self):
        helper = fixture.CurrentMetadataPublisherTest()
        with helper.authority() as (pub, store, code):
            helper.primary(pub, NOW, accept=True)
            accepted = deepcopy(helper.preserved(pub))
            c, transport, _ = self.seeded(pub, prefix=29)
            self.assertEqual(c.run(NOW).status, 'partial')
            prefix = deepcopy(c.journal['staging']['pages'])
            # 30 retained raw pages + journal fit, the next raw page does not.
            with patch.object(owner, 'MAX_CATALOG_OBJECTS', 31):
                with self.assertRaisesRegex(RefreshError, 'finite working-set'):
                    c.run(NOW + 1)
            self.assertEqual(c.objects, {})
            self.assertEqual(c.journal['staging']['pages'], prefix)
            self.assertEqual(CatalogRefresh(Publisher(store, code)).journal, c.journal)
            self.assertEqual(pub.ledger['requests'][-1]['outcome'], 'success')
            self.assertIsNone(pub.ledger['backoff_until_utc'])
            transport.epoch = NOW + 2
            self.assertEqual(c.run(NOW + 2, max_requests=3).status, 'complete')
            self.assertEqual(len(transport.calls), 5)
            self.assertEqual(len(pub.ledger['requests']), 6)
            self.assertEqual(transport.calls[1]['url'], transport.calls[2]['url'])
            self.assertEqual(len({x['url'] for x in transport.calls}), 4)
            self.assertEqual([r['outcome'] for r in pub.ledger['requests']], ['success'] * 6)
            self.assert_preserved(pub, accepted)
