"""Unclassified imported jurisdiction metadata requires explicit reviewed facts."""
import copy
from pathlib import Path
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.graphics import build_pack
from tools.spacefox.global_map import GeographyError, build_bundle, write_bundle
from tests.test_global_catalog import temporary_catalog, supplement, save_revision
from tests.test_global_content_selection_r3 import rehash

ROOT = Path(__file__).resolve().parents[1]
URL = 'https://r4.example/explicit-classification'


class GlobalContentJurisdictionR4Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        current = build_catalog(ROOT)
        legacy = build_catalog(ROOT, ROOT/'tests/fixtures/catalog/global-before-content-source.json')
        cls.packs = {
            'current': (build_pack(ROOT, current, roots=['ll2:country:76']), 'll2:country:76'),
            'legacy': (build_pack(ROOT, legacy, roots=['ll2:country:28']), 'll2:country:28'),
        }

    def test_unreviewed_kind_rehashed_current_retained_negative(self):
        # All three are valid enum strings, but no explicit jurisdictionKind
        # fact/correction authorizes them. Source hashes/index/bytes all agree.
        for source, (pack, identity) in self.packs.items():
            bundle = build_bundle(pack, [])
            for kind in ('country', 'territory', 'historical'):
                def change(record):
                    record['selection']['dictionaries']['countries'][identity]['jurisdictionKind'] = kind
                bad = rehash(bundle, change)
                with tempfile.TemporaryDirectory() as tmp:
                    output = Path(tmp); write_bundle(output, bundle)
                    accepted = (output/'manifest.json').read_bytes()
                    with self.subTest(source=source, kind=kind, port='current'):
                        with self.assertRaises(GeographyError):
                            write_bundle(output, bad)
                        self.assertEqual((output/'manifest.json').read_bytes(), accepted)
                    # Write actual rehashed producer bytes to exercise retained
                    # admission independently of the current writer's rejection.
                    for path, data in bad['files'].items():
                        target = output/path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
                    (output/'manifest.json').write_bytes(canonical_bytes(bad['manifest']))
                    with self.subTest(source=source, kind=kind, port='retained'):
                        with self.assertRaises(GeographyError):
                            build_bundle(pack, [], previous_directory=output)

    def test_unclassified_and_explicit_review_current_retained_positive(self):
        for source, (pack, identity) in self.packs.items():
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp)
                row = pack['manifest']['selection']['dictionaries']['countries'][identity]
                self.assertEqual(row['jurisdictionKind'], 'unclassified')
                self.assertNotIn('jurisdictionKind', row['facts'])
                first = build_bundle(pack, []); write_bundle(output, first)
                receipt = write_bundle(output, build_bundle(pack, [], previous_directory=output))
                self.assertTrue(receipt['retainedSelection'])
                self.assertLessEqual(receipt['artifactBytes'], 1048576)
        # A literal explicit sourced review remains legal; this temporary fixture
        # tests structural admission, not the factual status of the jurisdiction.
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp); source = root/'catalog/source.json'
            original = copy.deepcopy(build_catalog(root)['dictionaries']['countries']['ll2:country:76'])
            value = supplement('r4-explicit-jurisdiction-review')
            value['updates'] = [{'identity': 'll2:country:76', 'changes': {'jurisdictionKind': 'country'}, 'sources': [URL]}]
            catalog = amend_recipe(root, source, save_revision(root, value), 'r4.explicit.review')
            row = catalog['dictionaries']['countries']['ll2:country:76']
            self.assertEqual(row['jurisdictionKind'], 'country')
            self.assertEqual(row['facts']['jurisdictionKind'], 'country')
            self.assertEqual(row['originalFacts'], original.get('originalFacts', original['facts']))
            self.assertEqual(row['curationHistory'][-1]['sources'], [URL])
            pack = build_pack(root, catalog, roots=['ll2:country:76'])
            output = root/'build/bundle'
            write_bundle(output, build_bundle(pack, []))
            receipt = write_bundle(output, build_bundle(pack, [], previous_directory=output))
            self.assertTrue(receipt['retainedSelection'])


if __name__ == '__main__':
    unittest.main()
