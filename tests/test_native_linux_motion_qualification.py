"""Negative witnesses for the offline qualification's independent boundary."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tools.qualify_native_linux import QualificationError, pixels, tree, checked_tree
from tools.qualify_native_linux_motion import (CAPS, FEEDS, cache_union, compare, inspect, pin, read_ref)

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT / 'tests/fixtures/native-linux-motion/retained-macos'


def replace_scene(files, edit):
    data = dict(files); feed = json.loads(data[FEEDS[3]])
    old = feed['visualSelection']; scene = json.loads(data[old['path']]); edit(scene)
    raw = json.dumps(scene, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    digest = hashlib.sha256(raw).hexdigest(); path = 'descriptors/' + digest + '.json'
    data[path] = raw; feed['visualSelection'] = dict(path=path, sha256=digest, decodedBytes=len(raw))
    data[FEEDS[3]] = json.dumps(feed, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    return data


class MotionQualificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = tree(REF / 'a')
        cls.missing = tree(REF / 'missing')
        cls.shared = tree(REF / 'shared')

    def test_frozen_cohort_independent_pixels_roles_and_budgets(self):
        for label in ('a','timeline-b','image-b','rollback','missing','shared'):
            with self.subTest(label=label):
                data = tree(REF / label); report = inspect(data,label)
                self.assertTrue(compare(data,data,label)['exact'])
                self.assertLessEqual(report['files'],256)
                self.assertEqual(set(report['pixels']), {'visualSelection','globeSelection'})
                self.assertLessEqual(len(report['cache']),96)
                self.assertLessEqual(sum(report['cache'].values()),393216)

    def test_bad_source_link_roles_age_and_budget_are_refused(self):
        source = json.loads(self.a[FEEDS[3]])['visualSelection']
        broken = dict(self.a); broken[source['path']] += b' '
        self.assertIn('reference bytes', compare(broken,self.a,'a')['candidateDecodeError'])
        bad_role = replace_scene(self.a, lambda scene: scene['roles'].pop('operatorOrigin'))
        self.assertIn('roles', compare(bad_role,self.a,'a')['candidateDecodeError'])
        bad_origin = replace_scene(self.a, lambda scene: scene['origins']['model'].update(countryId='ll2:country:2'))
        self.assertIn('distinct origins', compare(bad_origin,self.a,'a')['candidateDecodeError'])
        altered = dict(self.a); feed = json.loads(altered[FEEDS[3]]); scene = json.loads(altered[feed['visualSelection']['path']]); binding = scene['roles']['rocket']
        descriptor = json.loads(altered[binding['descriptor']['path']]); descriptor['animation'] = [0, []]
        raw = json.dumps(descriptor, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode(); digest = hashlib.sha256(raw).hexdigest(); path = 'descriptors/'+digest+'.json'; altered[path] = raw
        binding['descriptor'] = dict(path=path,sha256=digest,decodedBytes=len(raw))
        altered = replace_scene(altered, lambda target: target['roles'].update(rocket=binding))
        self.assertIn('timeline', compare(altered,self.a,'a')['candidateDecodeError'])
        aged = dict(self.a); feed = json.loads(aged[FEEDS[3]]); feed['publisher']['selectionValidatedUtc'] += 1
        aged[FEEDS[3]] = json.dumps(feed).encode()
        self.assertIn('source age', compare(aged,self.a,'a')['candidateDecodeError'])
        oversized = dict(self.a); oversized['extra'] = b'x' * CAPS['artifactBytes']
        self.assertIn('artifact bound', compare(oversized,self.a,'a')['candidateDecodeError'])
        self.assertFalse(compare(dict(self.a, **{'extra':b'x'}),self.a,'a')['exact'])

    def test_current_prior_cache_union_is_bounded(self):
        caches = {label: inspect(tree(REF/label),label)['cache'] for label in ('a','timeline-b','image-b','rollback')}
        for prior, current in [('a','timeline-b'),('timeline-b','image-b'),('image-b','rollback')]:
            actual = cache_union(caches[current],caches[prior])
            self.assertLessEqual(actual['objects'],96)
            self.assertLessEqual(actual['bytes'],393216)
        with self.assertRaisesRegex(QualificationError,'cache budget'):
            cache_union({str(n):4096 for n in range(97)}, {})
        with self.assertRaisesRegex(QualificationError,'cache digest size collision'):
            cache_union({'same':2},{'same':1})

    def test_truncated_sfr_token_reports_bounded_decode_error(self):
        # A literal one-row stream with an incomplete color, independent of the encoder.
        shard = b'SFR1:0:1:' + base64.b64encode(bytes([0, 255]))
        desc = dict(canvas=[1,1],channels=4,shards=[{'path':'r'}],pixelSha256='0'*64)
        data = {'wire3/feed.json':json.dumps({'visualSelection':{'path':'s'}}).encode(),
                's':json.dumps({'roles':{'rocket':{'descriptor':{'path':'d'}}}}).encode(),
                'd':json.dumps(desc).encode(), 'r':shard}
        with self.assertRaisesRegex(QualificationError, 'truncated token/color'):
            pixels(data,'visualSelection')

    def test_repeat_token_cannot_overrun_literal_row(self):
        # Both streams request the previous transparent pixel. The second asks
        # for 128 pixels in a one-pixel row; slicing must not hide that overflow.
        desc = dict(canvas=[1,1], channels=4, shards=[{'path':'r'}],
                    pixelSha256=hashlib.sha256(bytes(4)).hexdigest())
        data = {'wire3/feed.json':json.dumps({'visualSelection':{'path':'s'}}).encode(),
                's':json.dumps({'roles':{'rocket':{'descriptor':{'path':'d'}}}}).encode(),
                'd':json.dumps(desc).encode(),
                'r':b'SFR1:0:1:' + base64.b64encode(bytes([128]))}
        self.assertEqual(pixels(data,'visualSelection')['rocket']['raw'], bytes(4))
        data['r'] = b'SFR1:0:1:' + base64.b64encode(bytes([255]))
        with self.assertRaisesRegex(QualificationError, 'SFR1 reference row bound'):
            pixels(data,'visualSelection')

    def test_historical_static_source_archive_retains_lock_bytes(self):
        lock = json.loads((ROOT/'.github/native-linux-static-lock.json').read_text())
        archive = ROOT/'tests/fixtures/native-linux-motion/static-archive'
        self.assertEqual({p:pin((archive/p).read_bytes()) for p in lock['sourceFiles']},lock['sourceFiles'])
        self.assertEqual({p:pin((archive/p).read_bytes()) for p in lock['qualificationFiles']},lock['qualificationFiles'])
        for fixture in lock['fixtures'].values():
            checked_tree(ROOT,fixture['inputRoot'],fixture['inputs'])
            checked_tree(ROOT,fixture['referenceRoot'],fixture['referenceFiles'])
        self.assertNotEqual(pin((ROOT/'tools/spacefox/graphics.py').read_bytes()),lock['sourceFiles']['tools/spacefox/graphics.py'])

if __name__ == '__main__': unittest.main()
