"""Source-preserving island detail and omission control for the native map producer."""
from pathlib import Path
from dataclasses import replace
import unittest
from unittest.mock import patch

from tools.native_all_site_qualification import verify_detail
from tools.spacefox.bridge_map import _requires_regional_detail, build_map, load_source as load_bridge
from tools.spacefox.catalog import build_catalog, loads_json
from tools.spacefox.geographic_context import load_source as load_regional
from tools.spacefox.native_profile import _map_visuals, png_pixels, rasterize
from tools.spacefox.visual_bridge import read_ref

ROOT = Path(__file__).resolve().parents[1]


class NativeMapDetailTest(unittest.TestCase):
    def test_detail_guard_uses_projected_source_not_base_dataset_threshold(self):
        view = {'manifest': {'context': {'nearestHighResolutionCoastDegrees': .1, 'nearestBaseLineDegrees': .5}},
                'segments': [((355, 165), (356, 165))]}
        self.assertTrue(_requires_regional_detail(view))
        view['segments'] = [((334, 165), (336, 165))]
        self.assertFalse(_requires_regional_detail(view))
        view['segments'] = [((355, 165), (356, 165))]
        view['manifest']['context']['nearestHighResolutionCoastDegrees'] = 3
        self.assertFalse(_requires_regional_detail(view))

    def test_sourced_omelek_inset_and_omission(self):
        catalog = build_catalog(ROOT)
        pin = load_bridge(ROOT, catalog['source']['visualBridge'])['index']['regional']
        source = load_regional(ROOT, pin)
        probes = loads_json((ROOT/'tests/fixtures/global_geography/required-regional-details.json').read_bytes())
        def produce():
            files = {}
            ref = build_map(ROOT, catalog, 'll2:site:107', files)
            descriptor = loads_json(read_ref(ref, files))
            _, image, _ = rasterize(_map_visuals(files, descriptor), 390, 390, opaque=True)
            return descriptor, image
        with patch('tools.spacefox.bridge_map._requires_regional_detail', return_value=False):
            _, before = produce()
        descriptor, after = produce()
        checked = verify_detail(descriptor, probes['ll2:site:107'], source['supplements'], after)
        self.assertEqual(checked['sourceVertexPixel'], [348, 139])
        with self.assertRaisesRegex(ValueError, 'sourced regional detail missing'):
            verify_detail(descriptor, probes['ll2:site:107'], source['supplements'], before)
        self.assertEqual(descriptor['center'], ['9.047861', '167.743'])
        self.assertEqual(descriptor['marker']['anchor'], [335, 165])
        _, _, old = png_pixels(before); _, _, new = png_pixels(after)
        for y in range(390):
            for x in range(390):
                if 304 <= x <= 366 and 134 <= y <= 196:
                    continue
                at = (y*390+x)*4
                self.assertEqual(old[at:at+4], new[at:at+4], (x, y))

    def test_current_sfr1m_selected_island_map(self):
        # A technical identity mutation of an existing captured launch exercises
        # the real current producer; it is not a claim that this launch used Omelek.
        from tests.test_current_motion_publisher import NOW, captured_starship
        from tools.spacefox.native_motion import build_artifact, validate_artifact
        from tools.spacefox.provider import normalize_launch
        from tools.spacefox.schedule import IdKind, ScheduleState, StableId, merge_schedule
        catalog = build_catalog(ROOT)
        record = replace(normalize_launch(captured_starship(), NOW),
                         site_id=StableId(IdKind.SITE, 'll2', '107'),
                         country_id=StableId(IdKind.COUNTRY, 'll2', '52'),
                         site_name='Omelek Island', site_location_name='Omelek Island',
                         country_name='Marshall Islands', country_code='MH')
        state = merge_schedule(ScheduleState(), (record,), NOW)
        files, _ = build_artifact(state, catalog, NOW,
            publisher=dict(instance='a'*64, generation=1, selectionValidatedUtc=NOW), root=ROOT)
        feed = validate_artifact(files)
        scene = loads_json(read_ref(feed['visualSelection'], files))
        self.assertEqual(scene['siteId'], 'll2:site:107')
        self.assertEqual(scene['marker']['anchor'], [335, 165])
        raster = loads_json(read_ref(scene['roles']['map']['descriptor'], files))
        self.assertEqual(raster['canvas'], [390, 390])
        self.assertLessEqual(sum(ref['decodedBytes'] for ref in raster['shards']), 98304)
        self.assertLessEqual(sum(map(len, files.values())), 1048576)
