"""R3 cloud-origin namespace parity and literal local Git/HTTP witnesses.

The frozen source/visual corpus is input, never rebuilt as an expected oracle.
Only remote Git/Pages are replaced; actual durable and HTTP readers execute.
"""
from copy import deepcopy
import hashlib
import json
import unittest

from tests import test_visual_bridge_verify_r1 as r1
from tests.test_cloud_delivery import World
from tests.test_visual_bridge import NOW
from tools.spacefox.cloud import CloudError, Site, delivery, delivery_files, snapshot_files
from tools.spacefox.publisher import LiveRevision, Publisher, StateError


def literal(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def pin(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def repin(snapshot, files):
    snapshot['files'] = {path: pin(raw) for path, raw in files.items()}
    snapshot['artifact_revision'] = hashlib.sha256(literal({k: v for k, v in snapshot.items()
                                                          if k != 'artifact_revision'})).hexdigest()


class VisualBridgeOriginReviewR3(unittest.TestCase):
    setUp = r1.VisualBridgeDurableReviewR1.setUp
    tearDown = r1.VisualBridgeDurableReviewR1.tearDown

    def candidate(self, label='a', generation=1, *, legacy=False):
        files = r1.fixture(label)
        for path in ('feed.json', 'wire2/feed.json'):
            root = json.loads(files[path])
            root['publisher'] = {'instance': self.pub.ledger['instance_id'], 'generation': generation,
                                 'selectionValidatedUtc': 1794438000}
            files[path] = literal(root)
        if legacy:
            root = json.loads(files['feed.json'])
            files = {p: files[p] for p in ('feed.json', root['catalogPath'])}
        return files

    def pending_document(self, files, *, profile='visual-v2'):
        doc = self.pub.ledger
        snapshot = {'generation': 1, 'code_revision': self.code,
                    'catalog_revision': json.loads(files['feed.json'])['catalogDigest'],
                    'schedule': deepcopy(doc['accepted'])}
        if profile is not None:
            snapshot['artifact_profile'] = profile
        repin(snapshot, files)
        doc.update(generation=1, pending=snapshot)
        return doc, {f'artifacts/1/{p}': raw for p, raw in files.items()}

    def prepare(self, label, generation):
        files = self.candidate(label, generation)
        root = json.loads(files['feed.json'])
        self.pub.prepare(self.pub.head, NOW + generation, files, root['catalogDigest'],
                         feed_publisher=root['publisher'], artifact_profile='visual-v2')
        return files

    def test_origin_namespace_current_and_historical_profiles(self):
        # Valid current and unmarked historical roots share the same literal
        # identity rule. Rehash every file/snapshot so byte integrity cannot
        # conceal the missing semantic check on authenticated origin reads.
        for legacy, profile in ((False, 'visual-v2'), (False, None), (True, None), (True, 'feed-v1')):
            with self.subTest(legacy=legacy, profile=profile):
                good = self.candidate(legacy=legacy)
                doc, raw = self.pending_document(good, profile=profile)
                origin = self.store._commit(doc, self.pub.head, raw)
                saved, observed = snapshot_files(self.store, origin, 1)
                self.assertEqual(doc['pending'], saved)
                self.assertEqual(good, observed)
                bad = dict(good)
                for path in ('feed.json', 'wire2/feed.json'):
                    if path in bad:
                        feed = json.loads(bad[path])
                        feed['publisher']['instance'] = 'f' * 64
                        bad[path] = literal(feed)
                doc, raw = self.pending_document(bad, profile=profile)
                origin = self.store._commit(doc, self.pub.head, raw)
                with self.assertRaises(CloudError):
                    snapshot_files(self.store, origin, 1)
                # Current explicitly profiled public writer rejects the same
                # independently rehashed semantic mismatch before a state CAS.
                if profile is not None:
                    before = self.pub.head
                    with self.assertRaises(StateError):
                        self.store.write(before, doc, raw)
                    self.assertEqual(before, self.store.load()[0])

    def test_retained_origin_namespace_rejected_at_delivery_and_http(self):
        first = self.prepare('a', 1)
        snap = self.pub.ledger['pending']
        self.pub.reconcile(LiveRevision(1, snap['artifact_revision']))
        second = self.prepare('b', 2)
        union = {**{p: raw for p, raw in first.items() if p not in ('feed.json', 'wire2/feed.json')}, **second}
        self.assertEqual(union, delivery_files(self.pub, delivery(self.pub)))
        doc = self.pub.ledger
        prior = dict(first)
        for path in ('feed.json', 'wire2/feed.json'):
            root = json.loads(prior[path])
            root['publisher']['instance'] = 'e' * 64
            prior[path] = literal(root)
        repin(doc['active'], prior)
        durable = {**{f'artifacts/1/{p}': raw for p, raw in prior.items()},
                   **{f'artifacts/2/{p}': raw for p, raw in second.items()}}
        origin = self.store._commit(doc, self.pub.head, durable)
        # The pending snapshot is the real current one. The origin's retained
        # snapshot alone has a namespace mismatch, with correct raw pins.
        self.assertEqual(second, snapshot_files(self.store, origin, 2)[1])
        manifest = {p: dict(meta, state=origin, generation=1, role='previous')
                    for p, meta in doc['active']['files'].items() if p not in ('feed.json', 'wire2/feed.json')}
        manifest.update({p: dict(meta, state=origin, generation=2, role='current')
                         for p, meta in doc['pending']['files'].items()})
        with self.subTest(port='complete-delivery'):
            with self.assertRaises(CloudError):
                delivery_files(self.pub, manifest)
        world = World(self.remote)
        try:
            world.live = union
            with self.subTest(port='actual-http-observe'):
                with self.assertRaises(CloudError):
                    Site(world.base + '/site', local_http=True).observe(self.pub, manifest)
            self.assertEqual([], world.posts)
            self.assertEqual(0, world.provider_calls)
        finally:
            world.close()

    def test_valid_reopen_source_age_complete_http_and_both_root_rereads(self):
        first = self.prepare('a', 1)
        snap = self.pub.ledger['pending']
        self.pub.reconcile(LiveRevision(1, snap['artifact_revision']))
        second = self.prepare('b', 2)
        quota = self.pub.ledger['requests']
        self.pub = Publisher(self.store, self.code)
        self.assertEqual(second, self.pub.pending_files())
        self.assertEqual(quota, self.pub.ledger['requests'])
        for path in ('feed.json', 'wire2/feed.json'):
            root = json.loads(second[path])
            self.assertEqual(1794438000, root['publisher']['selectionValidatedUtc'])
            self.assertEqual(1794438000, root['launch']['source_validated_utc'])
            self.assertEqual('Луна 零', root['launch']['mission_name'])
        union = {**{p: raw for p, raw in first.items() if p not in ('feed.json', 'wire2/feed.json')}, **second}
        manifest = delivery(self.pub)
        self.assertEqual(union, delivery_files(self.pub, manifest))
        world = World(self.remote)
        try:
            world.live = dict(union)
            site = Site(world.base + '/site', local_http=True)
            original_get = site.get
            reads = []

            def recording_get(path, limit):
                response = original_get(path, limit)
                reads.append((path, response))
                return response

            site.get = recording_get
            expected = LiveRevision(2, self.pub.ledger['pending']['artifact_revision'])
            self.assertEqual(expected, site.observe(self.pub, manifest))
            self.assertEqual(set(union), {path for path, _ in reads})
            for path, response in reads:
                self.assertEqual((200, union[path]), response)
            self.assertEqual(2, sum(path == 'feed.json' for path, _ in reads))
            self.assertEqual(2, sum(path == 'wire2/feed.json' for path, _ in reads))
            # Mutate after an actual HTTP response has returned. Each root's
            # second real GET must see the stale generation and refuse it.
            for root in ('feed.json', 'wire2/feed.json'):
                with self.subTest(switched_root=root):
                    world.live = dict(union)
                    switched = False

                    def switching_get(path, limit):
                        nonlocal switched
                        response = original_get(path, limit)
                        if path == root and not switched:
                            switched = True
                            world.live[root] = first[root]
                        return response

                    site.get = switching_get
                    with self.assertRaises(CloudError):
                        site.observe(self.pub, manifest)
                    self.assertTrue(switched)
            # Exact complete readback includes prior-only immutable files.
            world.live = dict(union)
            site.get = original_get
            retained = next(p for p in first if p not in second and p not in ('feed.json', 'wire2/feed.json'))
            del world.live[retained]
            with self.assertRaises(CloudError):
                site.observe(self.pub, manifest)
            self.assertEqual(quota, self.pub.ledger['requests'])
            self.assertEqual([], world.posts)
            self.assertEqual(0, world.provider_calls)
        finally:
            world.close()
