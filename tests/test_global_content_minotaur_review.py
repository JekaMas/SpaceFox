"""Literal source-fact correction and selected producer binding for Minotaur I."""
import hashlib
from pathlib import Path
import unittest

from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.graphics import build_pack

ROOT = Path(__file__).resolve().parents[1]


class GlobalContentMinotaurReviewTest(unittest.TestCase):
    def test_optional_fairing_metadata_and_selection_positive(self):
        catalog = build_catalog(ROOT)
        identity = 'spacefox:asset:content-r1-vehicle-minotaur-i'
        asset = catalog['dictionaries']['assets'][identity]
        feature = asset['facts']['coverage']['features'][0]
        self.assertIn('baseline50-inch', feature)
        self.assertIn('optional61-inch representative', feature)
        self.assertIn('no73-inch, event-specific or default-fairing claim', feature)
        self.assertEqual(asset['facts']['coverage']['configurationIds'], ['ll2:configuration:175'])
        self.assertEqual(asset['content']['sha256'],
                         '38dafdfdfa44acaf8a645fe73e43662841b7283141fd436963c8f6390c9908a2')
        self.assertEqual(hashlib.sha256((ROOT/asset['content']['path']).read_bytes()).hexdigest(),
                         asset['content']['sha256'])
        pack = build_pack(ROOT, catalog, roots=['ll2:configuration:175'])
        selection = pack['manifest']['selection']['dictionaries']['configurations']['ll2:configuration:175']
        self.assertEqual(selection['references']['visual'], identity)
        self.assertIn(identity, pack['manifest']['assets'])
        self.assertLessEqual(len(canonical_bytes(pack['manifest']))+sum(map(len, pack['objects'].values())), 1048576)
        self.assertTrue(all(s['maxShardDecodedBytes'] <= 4096 for s in pack['statistics'].values()))


if __name__ == '__main__':
    unittest.main()
