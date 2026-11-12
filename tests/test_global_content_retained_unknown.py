"""Retained global Unknown identities survive successive ordinary curations."""
import copy
from pathlib import Path
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes
from tools.spacefox.graphics import build_pack
from tests.test_global_catalog import temporary_catalog, supplement, save_revision

ROOT = Path(__file__).resolve().parents[1]


class GlobalContentRetainedUnknownTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)

    def test_ordinary_unknown_recode_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            before = source.read_bytes()
            value = supplement('r2-ordinary-unknown-recode')
            value['updates'] = [{'identity': 'll2:country:17', 'changes': {
                'name': 'Literal renamed country', 'alpha2': 'ZX', 'alpha3': 'ZXX'},
                'sources': value['sources']}]
            with self.assertRaisesRegex(CatalogError, 'unknown source jurisdiction must retain unknown kind'):
                amend_recipe(root, source, save_revision(root, value), 'r2.ordinary.recode')
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_recoded_unknown_model_operator_origins_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            first = supplement('r2-retained-unknown-recode')
            first['updates'] = [{'identity': 'll2:country:17', 'changes': {
                'name': 'Literal renamed country', 'alpha2': 'ZX', 'alpha3': 'ZXX',
                'jurisdictionKind': 'unknown'}, 'sources': first['sources']}]
            current = amend_recipe(root, source, save_revision(root, first, 'first.json'), 'r2.recode.unknown')
            self.assertEqual(current['dictionaries']['countries']['ll2:country:17']['jurisdictionKind'], 'unknown')
            before = source.read_bytes()
            value = supplement('r2-retained-unknown-origins')
            value['updates'] = [{'identity': 'll2:country:17',
                                 'changes': {'jurisdictionKind': 'country'}, 'sources': value['sources']}]
            for collection, owner, asset_id, field in [
                    ('companies', 'll2:organization:37', 'content-r1-operator-37', 'currentPackBadgeId'),
                    ('models', 'll2:configuration:52', 'content-r1-vehicle-minotaur-iv', 'currentPackAssetId')]:
                original = self.catalog['dictionaries']['assets']['spacefox:asset:'+asset_id]
                facts = copy.deepcopy(original['facts'])
                facts.update(id='r2-retained-unknown-'+collection, file=original['content']['path'],
                             originCode='ZX', originSources=value['sources'])
                value['assets'].append({'collection': collection, 'facts': facts})
                value['updates'].append({'identity': owner, 'changes': {field: facts['id']},
                                         'sources': value['sources']})
            with self.assertRaisesRegex(CatalogError, 'unknown source jurisdiction must retain unknown kind'):
                amend_recipe(root, source, save_revision(root, value, 'second.json'), 'r2.recode.origins')
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_renamed_unknown_model_origin_specific_art_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            before = source.read_bytes()
            value = supplement('r2-retained-unknown-model')
            original = self.catalog['dictionaries']['assets']['spacefox:asset:content-r1-vehicle-minotaur-iv']
            facts = copy.deepcopy(original['facts'])
            facts.update(id='r2-renamed-unknown-model', file=original['content']['path'])
            facts['coverage']['configurationIds'] = ['ll2:configuration:511']
            value['assets'] = [{'collection': 'models', 'facts': facts}]
            value['updates'] = [{'identity': 'll2:configuration:511', 'changes': {
                'name': 'Literal resolved model', 'fullName': 'Literal resolved model',
                'placeholder': False, 'currentPackAssetId': facts['id'], 'currentPackSpecific': True},
                'sources': value['sources']}]
            with self.assertRaisesRegex(CatalogError, 'unknown configuration must retain generic fallback and omit origin'):
                amend_recipe(root, source, save_revision(root, value), 'r2.renamed.model')
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_generic_unknown_and_known_identity_corrections_positive(self):
        pack = build_pack(ROOT, self.catalog, roots=['ll2:configuration:511'])
        unknown = pack['manifest']['selection']['dictionaries']['configurations']['ll2:configuration:511']
        self.assertEqual(unknown['references']['visual'], 'spacefox:asset:generic')
        self.assertIsNone(unknown['references']['origin'])
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            value = supplement('r2-known-identity-corrections')
            value['updates'] = [
                {'identity': 'll2:country:28', 'changes': {'name': 'Japan literal sourced correction'}, 'sources': value['sources']},
                {'identity': 'll2:organization:37', 'changes': {'name': 'JAXA literal sourced correction'}, 'sources': value['sources']},
                {'identity': 'll2:configuration:182', 'changes': {
                    'name': 'Atlas V literal sourced correction', 'placeholder': False}, 'sources': value['sources']}]
            current = amend_recipe(root, source, save_revision(root, value), 'r2.known.corrections')
            for collection, identity in [('countries', 'll2:country:28'), ('organizations', 'll2:organization:37'),
                                         ('configurations', 'll2:configuration:182')]:
                before = self.catalog['dictionaries'][collection][identity]
                row = current['dictionaries'][collection][identity]
                self.assertEqual(row['references'], before['references'])
                self.assertEqual(canonical_bytes(row['originalFacts']), canonical_bytes(before.get('originalFacts', before['facts'])))
                self.assertEqual(row['curationHistory'][-1]['sources'], value['sources'])
            self.assertFalse(current['dictionaries']['configurations']['ll2:configuration:182']['facts']['placeholder'])


if __name__ == '__main__':
    unittest.main()
