"""Compare decoded watch artwork to published launch-configuration envelope ratios."""
from pathlib import Path
import json
import re
import unittest
import xml.etree.ElementTree as ET

from tools.spacefox.native_profile import png_pixels

ROOT = Path(__file__).resolve().parents[1]


class PublishedRocketProportions(unittest.TestCase):
    def test_themis_uses_sourced_height_with_illustrative_diameter(self):
        # ArianeGroup reports 28 m; the 3.5 m plotted width and first-hop
        # landing-leg position remain illustrative, not measured facts.
        document = json.loads((ROOT / 'assets/global/curation-20261112-content-r1.json').read_text())
        facts = next(x['facts'] for x in document['assets'] if x['facts']['id'] == 'content-r1-vehicle-themis-t1h')
        self.assertEqual(facts['geometryReference']['lengthMetres'], '28.0')
        svg = ET.fromstring((ROOT / 'assets/global' / facts['file']).read_bytes())
        core = next(x for x in svg if x.attrib.get('data-part') == 'core')
        coords = [float(x) for x in re.findall(r'-?\d+(?:\.\d+)?', core.attrib['d'])]
        xs, ys = coords[0::2], coords[1::2]
        self.assertAlmostEqual((max(xs)-min(xs))/(max(ys)-min(ys)+6.48), 3.5/28, delta=0.003)

    def test_radial_boosters_form_one_attached_stack(self):
        # The observed launch references show strap-ons mounted against the
        # main stage, rather than spaced apart in a flattened row.
        selected = ('ll2:configuration:15', 'll2:configuration:168',
                    'll2:configuration:38', 'll2:configuration:19',
                    'll2:configuration:202', 'll2:configuration:204')
        source = (ROOT / 'watchface/source/generated/NativeModels.mc').read_text()
        mapping = dict(re.findall(r'id\.equals\("([^\"]+)"\)\)\{return Rez\.Drawables\.(BundledModel\d+);\}', source))
        for identity in selected:
            with self.subTest(identity=identity):
                w, h, pixels = png_pixels((ROOT / 'watchface/resources/drawables' / (mapping[identity] + '.png')).read_bytes())
                visible = [(i % w, i // w) for i in range(w*h) if pixels[4*i+3] > 127]
                top, bottom = min(y for _, y in visible), max(y for _, y in visible)
                y = round(top + 0.78 * (bottom - top))
                xs = [x for x in range(w) if pixels[4*(y*w+x)+3] > 127]
                self.assertGreater(len(xs), 0)
                self.assertLessEqual(max((b-a-1 for a,b in zip(xs,xs[1:])), default=0), 1,
                                     f'disconnected strap-on stack at row {y}: {xs}')

    def test_primary_launch_envelopes(self):
        # SpaceX Falcon guide 2025 figures 2-1/2-2 and table 2-1;
        # Rocket Lab Electron payload guide v7 pp. 11–12;
        # ArianeGroup Ariane 6 launch kit VA268 (equipped boosters, long fairing).
        # Small raster stroke/rounding allowance is separate from dimensions.
        limits = {
            'll2:configuration:164': ('Falcon 9', 5.2 / 70, 0.025),
            'll2:configuration:161': ('Falcon Heavy', 12.2 / 70, 0.035),
            'll2:configuration:26': ('Electron', 1.2 / 18, 0.025),
            'll2:configuration:121': ('Ariane 62', 12.2 / 62, 0.035),
            'll2:configuration:116': ('Ariane 64', 12.2 / 62, 0.035),
            # ILS Proton Mission Planner's Guide rev. 7, section A.1:
            # maximum first-stage width 7.4 m, representative height 60 m.
            'll2:configuration:22': ('Proton-M Breeze-M', 7.4 / 60, 0.035),
            # Northrop Pegasus User Guide, figure 2-3: top-view wingspan
            # 6.706 m and overall vehicle length 16.939 m.
            'll2:configuration:173': ('Pegasus XL', 6.706 / 16.939, 0.035),
            # FAA 2017 fact sheets: 26.4 x 1.4 m and 19.4 x 1.4 m.
            'll2:configuration:110': ('Shavit 2', 1.4 / 26.4, 0.025),
            'll2:configuration:135': ('Kuaizhou 1A', 1.4 / 19.4, 0.025),
            # NASA core 8.4 m, two 12 ft boosters, Block 1 height 322 ft.
            'll2:configuration:143': ('SLS Block 1', (8.4 + 2 * 3.6576) / 98.1456, 0.035),
        }
        source = (ROOT / 'watchface/source/generated/NativeModels.mc').read_text()
        mapping = dict(re.findall(r'id\.equals\("([^\"]+)"\)\)\{return Rez\.Drawables\.(BundledModel\d+);\}', source))
        for identity, (name, expected, margin) in limits.items():
            with self.subTest(name=name, identity=identity):
                w, h, pixels = png_pixels((ROOT / 'watchface/resources/drawables' / (mapping[identity] + '.png')).read_bytes())
                points = [(i % w, i // w) for i in range(w*h) if pixels[4*i+3] > 127]
                self.assertTrue(points)
                width = max(x for x, _ in points) - min(x for x, _ in points) + 1
                height = max(y for _, y in points) - min(y for _, y in points) + 1
                self.assertLessEqual(abs(width / height - expected), margin,
                                     f'{name}: decoded bbox {width}x{height}, expected ratio {expected:.3f}')


if __name__ == '__main__':
    unittest.main()
