"""Compare the reviewed per-identity art choices to actual shipped resources."""
import json
from pathlib import Path
import re
import unittest
from tests.model_pixel_support import restore
from tools.spacefox.catalog import build_catalog
from tools.spacefox.graphics import export_svg, fit_model_visual
from tools.spacefox.native_profile import png_pixels, rasterize

ROOT=Path(__file__).resolve().parents[1]
MATRIX=ROOT/'openspec/changes/qualify-current-rocket-art/evidence/model-matrix.json'


def assert_bindings(rows, catalog, mapping, pixels):
    configurations=catalog['dictionaries']['configurations']
    assets=catalog['dictionaries']['assets']
    for row in rows:
        identity=row['configuration_id'];expected=row['asset_id']
        if configurations[identity]['references']['visual'] != expected:
            raise AssertionError('wrong catalog asset for '+identity)
        if assets[expected]['facts']['kind'] == 'generic':
            raise AssertionError('generic asset for '+identity)
        if identity not in mapping or pixels(mapping[identity]) != pixels(expected):
            raise AssertionError('wrong rendered artwork for '+identity)


class ReviewedModelBindings(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows=json.loads(MATRIX.read_text())['rows']
        cls.catalog=build_catalog(ROOT)
        source=(ROOT/'watchface/source/generated/NativeModels.mc').read_text()
        cls.mapping=dict(re.findall(r'id\.equals\("([^\"]+)"\)\)\{return Rez\.Drawables\.(BundledModel\d+);\}',source))
        cls.cache={}

    @classmethod
    def pixels(cls,key):
        if key not in cls.cache:
            if key.startswith('BundledModel'):
                raw=(ROOT/'watchface/resources/drawables'/f'{key}.png').read_bytes()
            else:
                row=cls.catalog['dictionaries']['assets'][key]
                source=(ROOT/row['content']['path']).read_bytes()
                visual=fit_model_visual(export_svg(source,row['facts']['exportSize']))
                _,raw,_=rasterize([visual],54,124)
            if key.startswith('BundledModel'):
                width,height,rgba=54,124,restore(key)
            else:
                width,height,rgba=png_pixels(raw)
            if (width,height)!=(54,124):raise AssertionError('wrong model canvas '+key)
            cls.cache[key]=bytes(rgba)
        return cls.cache[key]

    def test_reviewed_175_identity_and_real_bundled_pixels(self):
        self.assertEqual(len(self.rows),175)
        self.assertEqual(len({x['configuration_id'] for x in self.rows}),175)
        assert_bindings(self.rows,self.catalog,self.mapping,self.pixels)

    def test_decoded_sharing_follows_explicit_reviewed_groups(self):
        groups, owners = {}, {}
        for row in self.rows:
            identity = row['configuration_id']
            group = row['share_group']
            self.assertTrue(row['share_reason'], identity)
            actual = self.pixels(self.mapping[identity])
            if group in groups:
                self.assertEqual(actual, groups[group], identity)
            else:
                groups[group] = actual
            if actual in owners:
                self.assertEqual(group, owners[actual], identity)
            else:
                owners[actual] = group

    def test_updated_themis_binding_and_unique_pixels(self):
        row = next(x for x in self.rows if x['name'] == 'Themis Demonstrator')
        assert_bindings([row], self.catalog, self.mapping, self.pixels)
        pixels = self.pixels(self.mapping[row['configuration_id']])
        for other in self.rows:
            if other['configuration_id'] != row['configuration_id']:
                self.assertNotEqual(pixels, self.pixels(self.mapping[other['configuration_id']]), other['name'])

    def test_auxiliary_family_and_unknown_decisions(self):
        configurations = self.catalog['dictionaries']['configurations']
        expected = {
            'll2:configuration:96': 'spacefox:asset:current-family-art-20261118-96',
            'll2:configuration:120': 'spacefox:asset:current-family-art-20261118-120',
            'll2:configuration:182': 'spacefox:asset:current-family-art-20261118-182',
            'll2:configuration:505': 'spacefox:asset:current-family-art-20261118-505',
            'll2:configuration:511': 'spacefox:asset:generic',
        }
        for identity, asset in expected.items():
            with self.subTest(identity=identity):
                self.assertEqual(configurations[identity]['references']['visual'], asset)
                self.assertEqual(self.pixels(self.mapping[identity]), self.pixels(asset))
        # PrimeNEO's configuration is unfinalized; it must not acquire an
        # invented alias to the retired Orbex Prime art.
        self.assertIsNone(configurations['spacefox:configuration:primeneo']['references']['visual'])
        self.assertNotIn('spacefox:configuration:primeneo', self.mapping)

    def test_generic_and_wrong_specific_art_are_both_refused(self):
        row=next(r for r in self.rows if r['configuration_id']=='ll2:configuration:17')
        identity=row['configuration_id']; generic=self.catalog['dictionaries']['configurations']['ll2:configuration:511']['references']['visual']
        other=self.catalog['dictionaries']['configurations']['ll2:configuration:164']['references']['visual']
        self.assertNotEqual(other,row['asset_id'])
        for wrong in (generic,other):
            altered=dict(self.catalog['dictionaries']['configurations'][identity])
            altered['references']=dict(altered['references'],visual=wrong)
            configurations=dict(self.catalog['dictionaries']['configurations'],**{identity:altered})
            dictionaries=dict(self.catalog['dictionaries'],configurations=configurations)
            bad=dict(self.catalog,dictionaries=dictionaries)
            with self.subTest(wrong=wrong), self.assertRaisesRegex(AssertionError,'wrong catalog asset'):
                assert_bindings([row],bad,self.mapping,self.pixels)
        wrong_mapping=dict(self.mapping);wrong_mapping[identity]=self.mapping['ll2:configuration:164']
        with self.assertRaisesRegex(AssertionError,'wrong rendered artwork'):
            assert_bindings([row],self.catalog,wrong_mapping,self.pixels)
