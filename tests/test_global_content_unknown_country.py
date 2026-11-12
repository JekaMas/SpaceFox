"""R2 literal Unknown-country admission witnesses at the real publisher API."""
import copy
from pathlib import Path
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes
from tests.test_global_catalog import temporary_catalog, save_revision
from tests.test_global_content import mark_revision

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://official.example/r2-literal-evidence'


class GlobalContentUnknownCountryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)

    def test_imported_unknown_informational_mark_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            before = source.read_bytes()
            value = mark_revision(root, 'r2-unknown-code-label', '??',
                                  'll2:country:17', 'original-informational-country-code')
            with self.assertRaisesRegex(CatalogError, 'unknown jurisdiction must omit its mark'):
                amend_recipe(root, source, save_revision(root, value), 'r2.unknown.code')
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_curated_unknown_informational_mark_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            before = source.read_bytes()
            identity = 'spacefox:country:r2-unresolved'
            value = mark_revision(root, 'r2-unknown-new-label', 'ZX', identity,
                                  'original-informational-country-code')
            value['updates'] = []
            value['additions'] = [{'identity': identity, 'facts': {
                'sourceId': 'r2-unresolved', 'name': 'Literal unresolved jurisdiction',
                'alpha2': 'ZX', 'alpha3': 'ZXX', 'sourceUrl': URL,
                'currentPackFlagId': 'r2-unknown-new-label', 'jurisdictionKind': 'unknown'},
                'references': {'mark': 'spacefox:asset:r2-unknown-new-label'}}]
            with self.assertRaisesRegex(CatalogError, 'unknown jurisdiction must omit its mark'):
                amend_recipe(root, source, save_revision(root, value), 'r2.unknown.new')
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_region_mark_origin_and_unmarked_unknown_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            identity = 'spacefox:country:r2-region'
            value = mark_revision(root, 'r2-region-label', 'ZX', identity,
                                  'original-informational-country-code')
            value['updates'] = []
            value['additions'] = [{'identity': identity, 'facts': {
                'sourceId': 'r2-region', 'name': 'Literal reviewed region',
                'alpha2': 'ZX', 'alpha3': 'ZXX', 'sourceUrl': URL,
                'currentPackFlagId': 'r2-region-label', 'jurisdictionKind': 'region'},
                'references': {'mark': 'spacefox:asset:r2-region-label'}},
                {'identity': 'spacefox:country:r2-unmarked-unknown', 'facts': {
                    'sourceId': 'r2-unmarked-unknown', 'name': 'Literal unresolved jurisdiction',
                    'alpha2': 'ZY', 'alpha3': 'ZYY', 'sourceUrl': URL,
                    'currentPackFlagId': None, 'jurisdictionKind': 'unknown'},
                 'references': {'mark': None}}]
            original = self.catalog['dictionaries']['assets']['spacefox:asset:content-r1-operator-37']
            facts = copy.deepcopy(original['facts'])
            facts.update(id='r2-region-operator-label', file=original['content']['path'],
                         originCode='ZX', originSources=[URL], sources=[URL])
            value['assets'].append({'collection': 'companies', 'facts': facts})
            value['updates'] = [{'identity': 'll2:organization:37',
                                 'changes': {'currentPackBadgeId': facts['id']}, 'sources': [URL]}]
            catalog = amend_recipe(root, source, save_revision(root, value), 'r2.region')
            rows = catalog['dictionaries']
            self.assertEqual(rows['countries'][identity]['jurisdictionKind'], 'region')
            self.assertEqual(rows['countries'][identity]['references']['mark'],
                             'spacefox:asset:r2-region-label')
            self.assertIsNone(rows['countries']['spacefox:country:r2-unmarked-unknown']['references']['mark'])
            operator = rows['organizations']['ll2:organization:37']
            self.assertEqual(operator['references']['origin'], identity)
            self.assertEqual(operator['references']['countries'],
                             self.catalog['dictionaries']['organizations']['ll2:organization:37']['references']['countries'])
            self.assertEqual(operator['curationHistory'][-1]['sources'], [URL])
            self.assertEqual(rows['assets']['spacefox:asset:content-r1-operator-37'], original)
            self.assertEqual(canonical_bytes(operator['originalFacts']), canonical_bytes(
                self.catalog['dictionaries']['organizations']['ll2:organization:37']['originalFacts']))


if __name__ == '__main__':
    unittest.main()
