"""Fresh review regressions using the frozen A/B corpus and literal contracts.

These tests do not regenerate the corpus or use its producer as the oracle.
Local bare Git/loopback HTTP replace hosted services; there is no native claim.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json
from tools.spacefox.cloud import CloudError, Site, delivery, delivery_files
from tools.spacefox.publisher import GitState, LiveRevision, Publisher, StateError
from tools.spacefox.visual_bridge import build_artifact, validate_artifact
from tests.test_cloud_delivery import World, git
from tests.test_visual_bridge import NOW, envelope, record, sid, state
from tools.spacefox.schedule import IdKind


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/bridge-v2'


def fixture(label):
    return {p.relative_to(FIXTURES / label).as_posix(): p.read_bytes()
            for p in (FIXTURES / label).rglob('*.json')}


def address(files, old_path, value):
    """Readdress a DAG mutation so hash rejection cannot mask schema admission.

    This is test transport, not an expected semantic-validation implementation.
    All immutable parents get their new raw addresses; unreachable bytes drop.
    """
    output, memo = {}, {}

    def visit(path):
        if path in memo:
            return memo[path]
        source = files[path]
        doc = value if path == old_path else loads_json(source)

        def rewrite(obj):
            if type(obj) is dict:
                if set(obj) == {'path', 'sha256', 'decodedBytes'} and obj['path'] in files:
                    child, raw = visit(obj['path'])
                    return {'path': child, 'sha256': hashlib.sha256(raw).hexdigest(), 'decodedBytes': len(raw)}
                result = {k: rewrite(v) for k, v in obj.items()}
                if result.get('catalogPath') in files:
                    child, raw = visit(result['catalogPath'])
                    result.update(catalogPath=child, catalogDigest=hashlib.sha256(raw).hexdigest())
                return result
            if type(obj) is list:
                return [rewrite(v) for v in obj]
            return obj

        updated = canonical_bytes(rewrite(doc))
        # Preserve existing raw SFV formatting unless this file actually changed.
        raw = source if path != old_path and loads_json(source) == loads_json(updated) else updated
        target = path if path in ('feed.json', 'wire2/feed.json') else path.rsplit('/', 1)[0] + '/' + hashlib.sha256(raw).hexdigest() + '.json'
        memo[path] = target, raw
        output[target] = raw
        return target, raw

    visit('feed.json')
    visit('wire2/feed.json')
    return output


class VisualBridgeReviewR1(unittest.TestCase):
    def test_mobile_source_point_stays_bound_without_active_point(self):
        files, _ = build_artifact(state(record(site_id=sid(IdKind.SITE, '13'))), build_catalog(ROOT),
                                  NOW, publisher=envelope(), root=ROOT)
        feed = json.loads(files['wire2/feed.json'])
        selection = json.loads(files[feed['visualSelection']['path']])
        path = selection['roles']['geography']['descriptor']['path']
        value = json.loads(files[path])
        self.assertEqual('ll2:site:13', value['siteId'])
        self.assertEqual(('0.0', '-154.0'), (value['sourcePosition']['latitude'], value['sourcePosition']['longitude']))
        self.assertIsNone(value['position'])
        self.assertIsNone(value['marker'])
        value['sourcePosition']['longitude'] = '0.0'
        with self.assertRaises(ValueError):
            validate_artifact(address(files, path, value))

    def test_unbound_dictionary_visual_reference_is_refused(self):
        original = fixture('a')
        feed = json.loads(original['wire2/feed.json'])
        dictionary = json.loads(original[feed['catalogPath']])
        dictionary['entries']['ll2:site:80']['visual'] = {
            'path': 'descriptors/' + '0' * 64 + '.json', 'sha256': '0' * 64, 'decodedBytes': 1}
        with self.assertRaises(ValueError):
            validate_artifact(address(original, feed['catalogPath'], dictionary))

    def test_frozen_corpus_literal_limits_and_raw_pins(self):
        index = json.loads((FIXTURES / 'index.json').read_bytes())
        for label in ('a', 'b', 'rollback'):
            with self.subTest(label=label):
                files = fixture(label)
                self.assertEqual(set(index[label]['files']), set(files))
                for path, pin in index[label]['files'].items():
                    self.assertEqual(pin['bytes'], len(files[path]))
                    self.assertEqual(pin['sha256'], hashlib.sha256(files[path]).hexdigest())
                feed = validate_artifact(files)
                self.assertEqual(1794438000, feed['launch']['source_validated_utc'])
                self.assertEqual(1794438000, feed['publisher']['selectionValidatedUtc'])
                self.assertLessEqual(len(files), 256)
                self.assertLessEqual(sum(map(len, files.values())), 1048576)
        self.assertEqual(76, len(fixture('a')))
        self.assertEqual(524776, sum(map(len, fixture('a').values())))

    def test_rehashed_map_grammar_is_closed(self):
        original = fixture('a')
        feed = json.loads(original['wire2/feed.json'])
        selection = json.loads(original[feed['visualSelection']['path']])
        path = selection['roles']['geography']['descriptor']['path']
        self.assertEqual(original, address(original, path, json.loads(original[path])))
        for mutation in ('projection', 'major', 'style-boolean', 'marker-boolean', 'context-object', 'world-digest', 'recipe-digest'):
            with self.subTest(mutation=mutation):
                value = json.loads(original[path])
                if mutation == 'projection':
                    value['style']['projection'] = 'unsupported-projection'
                elif mutation == 'major':
                    value['schemaVersion'] = 3
                elif mutation == 'style-boolean':
                    value['style']['markerFade'] = 0
                elif mutation == 'marker-boolean':
                    value['marker']['colors'][0] = False
                elif mutation == 'context-object':
                    value['contextLimits'] = {'untrusted': 'not the declared string array'}
                elif mutation == 'world-digest':
                    value['source']['worldSha256'] = '0' * 64
                else:
                    value['source']['recipeSha256'] = None
                with self.assertRaises(ValueError):
                    validate_artifact(address(original, path, value))

    def test_rehashed_role_kinds_and_compact_catalog_facts(self):
        original = fixture('a')
        feed = json.loads(original['wire2/feed.json'])
        selected_path = feed['visualSelection']['path']
        selection = json.loads(original[selected_path])
        self.assertEqual(original, address(original, selected_path, selection))
        for role in ('origin', 'siteCountry'):
            with self.subTest(role=role):
                value = copy.deepcopy(selection)
                value[role + 'Id'] = 'll2:organization:121'
                value['roles'][role] = copy.deepcopy(value['roles']['operator'])
                with self.assertRaises(ValueError):
                    validate_artifact(address(original, selected_path, value))
        rocket_path = selection['roles']['rocket']['descriptor']['path']
        for bad_id in ('spacefox:asset:../escape', 'spacefox:map-layer:fill-0'):
            with self.subTest(asset=bad_id):
                value = json.loads(original[rocket_path])
                value['assetId'] = bad_id
                with self.assertRaises(ValueError):
                    validate_artifact(address(original, rocket_path, value))
        for mutation in ('name', 'unselected-entry', 'site-source'):
            with self.subTest(catalog=mutation):
                value = json.loads(original[feed['catalogPath']])
                if mutation == 'name':
                    value['entries']['ll2:configuration:164']['name'] = 'Saturn V'
                elif mutation == 'unselected-entry':
                    value['entries']['ll2:country:999'] = {'kind': 'country', 'name': 'Unselected', 'visual': None}
                else:
                    value['entries']['ll2:site:80']['sourcePosition']['latitude'] = '0'
                    value['entries']['ll2:site:80']['positionMode'] = 'mobile-reference-no-event'
                    value['entries']['ll2:site:80']['position'] = None
                    # Remove optional geography honestly; it cannot hide altered
                    # canonical source facts behind the same typed site ID.
                    selection2 = copy.deepcopy(selection)
                    selection2['roles']['geography'] = None
                    selection2['gaps'] = ['geography']
                    altered = address(original, selected_path, selection2)
                    selected_feed = json.loads(altered['wire2/feed.json'])
                    value['visualSelection'] = selected_feed['visualSelection']
                    with self.assertRaises(ValueError):
                        validate_artifact(address(altered, selected_feed['catalogPath'], value))
                    continue
                with self.assertRaises(ValueError):
                    validate_artifact(address(original, feed['catalogPath'], value))


class VisualBridgeDurableReviewR1(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='spacefox-bridge-review-')
        self.root = Path(self.tmp.name)
        self.remote, self.source = self.root / 'remote.git', self.root / 'source'
        subprocess.run(['git', 'init', '--bare', '-q', str(self.remote)], check=True)
        subprocess.run(['git', 'init', '-q', str(self.source)], check=True)
        git(self.source, 'config', 'user.name', 'Independent bridge review')
        git(self.source, 'config', 'user.email', 'review@example.invalid')
        git(self.source, 'commit', '--allow-empty', '-qm', 'source')
        self.code = git(self.source, 'rev-parse', 'HEAD')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.store = GitState(str(self.remote))
        self.store.bootstrap(self.code)
        self.pub = Publisher(self.store, self.code)
        self.pub.reconcile(None)
        token = self.pub.reserve(self.pub.head, NOW - 60, trigger='manual')
        self.pub.accept_source(self.pub.head, token, (record(),), NOW, selection_validated_utc=1794438000)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def candidate(self, label, generation):
        files = fixture(label)
        publisher = {'instance': self.pub.ledger['instance_id'], 'generation': generation,
                     'selectionValidatedUtc': 1794438000}
        for path in ('feed.json', 'wire2/feed.json'):
            feed = json.loads(files[path])
            feed['publisher'] = publisher
            files[path] = canonical_bytes(feed)
        return files, publisher, json.loads(files['feed.json'])['catalogDigest']

    def prepare(self, label, generation):
        files, publisher, digest = self.candidate(label, generation)
        self.pub.prepare(self.pub.head, NOW + generation, files, digest, feed_publisher=publisher)
        return files

    def test_missing_wire_root_cannot_be_persisted(self):
        files, publisher, digest = self.candidate('a', 1)
        del files['wire2/feed.json']
        before = self.pub.head
        with self.assertRaises(StateError):
            self.pub.prepare(before, NOW + 1, files, digest, feed_publisher=publisher)
        self.assertEqual(before, self.pub.head)
        self.assertEqual(0, self.pub.ledger['generation'])
        self.assertIsNone(self.pub.ledger['pending'])

    def test_exact_union_wrong_origin_replay_and_second_mutable_root(self):
        first = self.prepare('a', 1)
        first_manifest = delivery(self.pub)
        first_origin = self.pub.head
        snap = self.pub.ledger['pending']
        self.pub.reconcile(LiveRevision(1, snap['artifact_revision']))
        second = self.prepare('b', 2)
        manifest = delivery(self.pub)
        literal_union = {**{p: raw for p, raw in first.items() if p not in ('feed.json', 'wire2/feed.json')}, **second}
        self.assertEqual(literal_union, delivery_files(self.pub, manifest))
        common = next(p for p in first if p.startswith('objects/') and p in second and first[p] == second[p])
        wrong = copy.deepcopy(manifest)
        wrong[common] = dict(first_manifest[common], state=first_origin)
        with self.assertRaises(CloudError):
            delivery_files(self.pub, wrong)
        extra = copy.deepcopy(manifest)
        extra['unexpected.json'] = dict(manifest[common])
        with self.assertRaises(CloudError):
            delivery_files(self.pub, extra)
        # An actual HTTP reader switches only the versioned mutable root after
        # its first read. Re-reading root v1 alone must not approve mixed wire2.
        world = World(self.remote)
        try:
            world.live = literal_union
            site = Site(world.base + '/site', local_http=True)
            expected = LiveRevision(2, self.pub.ledger['pending']['artifact_revision'])
            self.assertEqual(expected, site.observe(self.pub, manifest))
            original_get = site.get
            seen_wire2 = False

            def switching_get(path, limit):
                nonlocal seen_wire2
                response = original_get(path, limit)
                if path == 'wire2/feed.json' and not seen_wire2:
                    seen_wire2 = True
                    world.live['wire2/feed.json'] = first['wire2/feed.json']
                return response
            site.get = switching_get
            with self.assertRaises(CloudError):
                site.observe(self.pub, manifest)
            self.assertTrue(seen_wire2)
        finally:
            world.close()
        snap = self.pub.ledger['pending']
        self.pub.reconcile(LiveRevision(2, snap['artifact_revision']))
        with self.assertRaises(CloudError):
            delivery_files(self.pub, first_manifest)


if __name__ == '__main__':
    unittest.main()
