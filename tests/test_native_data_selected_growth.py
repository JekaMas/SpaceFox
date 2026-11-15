"""Current scheduled eligibility projection retains bounded selected dependencies."""
import copy
import hashlib
from pathlib import Path
import unittest

from tests.test_current_motion_publisher import NOW, captured_starship
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes, loads_json, validate_catalog
from tools.spacefox.current_catalog import load_registry
from tools.spacefox.native_motion import build_artifact, validate_artifact
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, merge_schedule

ROOT = Path(__file__).resolve().parents[1]

class SelectedGrowthTest(unittest.TestCase):
    def test_real_unrelated_asset_does_not_enlarge_current_selection(self):
        catalog = build_catalog(ROOT)
        registry = load_registry(ROOT, catalog)
        smaller = copy.deepcopy(catalog)
        removed = smaller['dictionaries']['assets'].pop('spacefox:asset:vehicle-spaceshiptwo')
        self.assertEqual(removed, catalog['dictionaries']['assets']['spacefox:asset:vehicle-spaceshiptwo'])
        validate_catalog(smaller)
        small_registry = copy.deepcopy(registry)
        small_registry['dictionaryDigest'] = hashlib.sha256(canonical_bytes(smaller['dictionaries'])).hexdigest()
        record = normalize_launch(captured_starship(), NOW)
        state = merge_schedule(ScheduleState(), (record,), NOW)
        publisher = dict(instance='a' * 64, generation=1, selectionValidatedUtc=NOW)
        with self.assertRaisesRegex(CatalogError, 'eligibility catalog digest mismatch'):
            build_artifact(state, smaller, NOW, publisher=publisher, root=ROOT, eligibility=registry)
        outputs = [build_artifact(state, c, NOW, publisher=publisher, root=ROOT,
                                  eligibility=reg)[0] for c, reg in ((smaller, small_registry), (catalog, registry))]
        feeds = [validate_artifact(files) for files in outputs]
        self.assertNotEqual(feeds[0]['catalogSourceDigest'], feeds[1]['catalogSourceDigest'])
        self.assertEqual(feeds[0]['visualSelection']['decodedBytes'], feeds[1]['visualSelection']['decodedBytes'])
        self.assertEqual(feeds[0]['nativeTransfer']['decodedBytes'], feeds[1]['nativeTransfer']['decodedBytes'])
        scenes = [loads_json(files[feed['visualSelection']['path']]) for files, feed in zip(outputs, feeds)]
        for key in ('launchId', 'modelId', 'siteId', 'countryId', 'position', 'rendererProfile', 'layoutRevision'):
            self.assertEqual(scenes[0][key], scenes[1][key], key)
        rows = [loads_json(files[feed['nativeTransfer']['path']])['objects'] for files, feed in zip(outputs, feeds)]
        self.assertEqual([(kind, size) for kind, _, size in rows[0]], [(kind, size) for kind, _, size in rows[1]])
        self.assertLessEqual(len(rows[1]), 40)
        self.assertTrue(all(0 < size <= 4096 for _, _, size in rows[1]))

if __name__ == '__main__':
    unittest.main()
