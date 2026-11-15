"""Directed current SFR1M producer timeline, using a captured real selection."""
import json
import unittest
from copy import deepcopy
from tests.test_sfr1m_offline_current import build, documents, literal_decode, digest
from tests.test_current_motion_publisher import ROOT, captured_starship
from tools.spacefox.catalog import build_catalog
from tools.spacefox.native_motion import validate_artifact


class CurrentAnimationTest(unittest.TestCase):
    def test_captured_artwork_timeline_and_pixels(self):
        catalog = build_catalog(ROOT)
        asset = catalog['dictionaries']['assets']['spacefox:asset:further-r2-starship-v3-2026']
        timeline = [2000, [[0, 0, 0, 256], [1000, 0, -64, 288], [2000, 0, -128, 256]]]
        asset['facts']['nativeMotion'] = deepcopy(timeline)
        files = build(captured_starship(), catalog)
        feed, scene, _ = documents(files)
        descriptor = json.loads(files[scene['roles']['rocket']['descriptor']['path']])
        self.assertEqual(descriptor['animation'], timeline)
        pixels = literal_decode([files[p['path']] for p in descriptor['shards']],
                                *descriptor['canvas'], descriptor['channels'])
        self.assertEqual(digest(pixels), '15395365f81866ada8f35c360baa648fb7621b9a0e15052c2dfe5562ae8eacba')
        self.assertEqual(descriptor['pixelSha256'], digest(pixels))
        self.assertEqual(validate_artifact(files), feed)


if __name__ == '__main__':
    unittest.main()
