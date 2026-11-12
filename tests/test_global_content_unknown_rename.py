"""A curation rename cannot turn the retained Unknown placeholder into a mark."""
import copy
from pathlib import Path
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.spacefox.catalog import CatalogError, build_catalog
from tests.test_global_catalog import temporary_catalog, supplement, save_revision

ROOT = Path(__file__).resolve().parents[1]


class GlobalContentUnknownRenameTest(unittest.TestCase):
    def test_renamed_unknown_operator_badge_negative(self):
        catalog = build_catalog(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            before = source.read_bytes()
            value = supplement('r2-unknown-rename')
            original = catalog['dictionaries']['assets']['spacefox:asset:content-r1-operator-37']
            facts = copy.deepcopy(original['facts'])
            facts.update(id='r2-unknown-renamed-badge', file=original['content']['path'],
                         organizationId='ll2:organization:183')
            for field in ('originCode', 'originSources', 'originAssertion'):
                facts.pop(field, None)
            value['assets'] = [{'collection': 'companies', 'facts': facts}]
            value['updates'] = [{'identity': 'll2:organization:183', 'changes': {
                'name': 'Literal renamed unresolved operator', 'currentPackBadgeId': facts['id']},
                'sources': value['sources']}]
            with self.assertRaisesRegex(CatalogError, 'unknown organization must omit its badge'):
                amend_recipe(root, source, save_revision(root, value), 'r2.unknown.renamed')
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))


if __name__ == '__main__':
    unittest.main()
