import json
import gzip
from pathlib import Path
import re
import unittest

from tools.spacefox.catalog import build_catalog
from tools.spacefox.native_profile import decode_raster, png_pixels

ROOT = Path(__file__).resolve().parents[1]


class OfflineModelBindings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        source = (ROOT / 'watchface/source/generated/NativeModels.mc').read_text()
        cls.mapping = dict(re.findall(r'id\.equals\("([^"]+)"\)\)\{return Rez\.Drawables\.(BundledModel\d+);\}', source))

    def test_current_carriers_have_a_real_bound_model(self):
        registry = json.loads((ROOT / self.catalog['source']['eligibility']['path']).read_text())['records']
        configurations = self.catalog['dictionaries']['configurations']
        assets = self.catalog['dictionaries']['assets']
        identities = [identity for identity, record in registry.items() if record['state'] == 'current-evidence']
        self.assertEqual(len(identities), 175)
        for identity in identities:
            asset = configurations[identity]['references']['visual']
            self.assertIsNotNone(asset, identity)
            self.assertNotEqual(assets[asset]['facts']['kind'], 'generic', identity)
            self.assertIn(identity, self.mapping)
            self.assertTrue((ROOT / 'watchface/resources/drawables' / (self.mapping[identity] + '.png')).is_file())

    def test_lm2d_is_the_captured_sourced_raster(self):
        name = self.mapping['ll2:configuration:17']
        png = ROOT / 'watchface/resources/drawables' / (name + '.png')
        width, height, pixels = png_pixels(png.read_bytes())
        capture = ROOT / 'tests/fixtures/fr165-runtime-20261116/objects/rasters/81d5861906e66d2305e390eb4cc6983fa07064ae9c466759ccddca7480d68e16.sfr'
        self.assertEqual((width, height), (54, 124))
        self.assertEqual(pixels, decode_raster([capture.read_bytes()], 54, 124, 4))

    def test_unidentified_id_is_not_assigned_a_known_vehicle(self):
        self.assertNotIn('ll2:configuration:999999999', self.mapping)

    def test_every_binding_preserves_its_catalog_asset_identity(self):
        configurations = self.catalog['dictionaries']['configurations']
        expected = {identity: row['references']['visual'] for identity, row in configurations.items()
                    if row['references']['visual'] is not None}
        asset_names = {identity: 'BundledModel%03d' % index
                       for index, identity in enumerate(sorted(set(expected.values())))}
        self.assertEqual(self.mapping, {identity: asset_names[asset] for identity, asset in expected.items()})

    def test_captured_2026_2036_carrier_identities_are_bound(self):
        ids = set()
        count = 0
        configs = self.catalog['dictionaries']['configurations']
        assets = self.catalog['dictionaries']['assets']
        for path in (ROOT / 'corpus/real-schedule-basic-five-20261113/raw').glob('*.gz'):
            for row in json.loads(gzip.decompress(path.read_bytes()))['results']:
                net = row.get('net') or ''
                if not ('2026' <= net[:4] <= '2036'):
                    continue
                source_id = ((row.get('rocket') or {}).get('configuration') or {}).get('id')
                self.assertIsNotNone(source_id)
                identity = 'll2:configuration:' + str(source_id)
                count += 1
                ids.add(identity)
                self.assertIn(identity, self.mapping)
                asset = configs[identity]['references']['visual']
                if net >= '2026-11-18' and identity != 'll2:configuration:511':
                    self.assertNotEqual(assets[asset]['facts']['kind'], 'generic', identity)
        self.assertEqual((count, len(ids)), (743, 110))
