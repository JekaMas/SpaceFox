"""Whole eligibility/view boundary over the maintained catalog and registry."""
import copy
from pathlib import Path
import unittest

from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes, loads_json
from tools.spacefox.current_catalog import current_coverage, current_view, future_reference, validate_registry

ROOT = Path(__file__).resolve().parents[1]
TRIAGE = ROOT / 'catalog/current-2026.json'


class CurrentCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        cls.registry = loads_json(TRIAGE.read_bytes())

    def test_dated_inventory_produces_closed_current_view_and_preserves_archive(self):
        before = canonical_bytes(self.catalog)
        result = current_view(self.catalog, self.registry)
        records = self.registry['records']
        expected = {k for k, v in records.items() if v['state'] == 'current-evidence'}
        self.assertEqual(set(result['catalog']['dictionaries']['configurations']), expected)
        self.assertEqual(set(result['reviewIds']), {k for k, v in records.items() if v['state'] == 'needs-review'})
        self.assertTrue(result['provisional'])
        report = current_coverage(self.catalog, self.registry,
                                  referenced_ids=['ll2:site:13', 'll2:configuration:511',
                                                  'll2:configuration:999999'])
        self.assertEqual(report['currentConfigurations'], len(expected))
        self.assertEqual(report['qualification'], 'provisional-review-incomplete')
        self.assertEqual(report['connectedCounts']['sites'], 1)
        self.assertEqual(set(report['eventReviewIds']), {'ll2:configuration:511', 'll2:configuration:999999'})
        self.assertEqual(canonical_bytes(self.catalog), before)
        with self.assertRaisesRegex(CatalogError, 'review is incomplete'):
            current_view(self.catalog, self.registry, require_complete_eligibility=True)
        # A published scheduled reference survives for downstream identity/fallback,
        # including an unseen provider ID; neither is quietly declared retired.
        for identity in ('ll2:configuration:511', 'll2:configuration:999999'):
            event = future_reference(self.catalog, self.registry, identity)
            self.assertEqual(event['identity'], identity)
            self.assertTrue(event['reviewRequired'])
            self.assertIsNone(event['configuration'])
        excluded = copy.deepcopy(self.registry)
        excluded['records']['ll2:configuration:39']['state'] = 'excluded'
        projection = current_view(self.catalog, excluded, referenced_ids=['ll2:configuration:39'])
        self.assertNotIn('ll2:configuration:39', projection['catalog']['dictionaries']['configurations'])
        self.assertIn('ll2:configuration:39', projection['eventReviewIds'])
        self.assertTrue(future_reference(self.catalog, excluded, 'll2:configuration:39')['reviewRequired'])
        event = future_reference(self.catalog, self.registry, 'll2:configuration:116')
        self.assertFalse(event['reviewRequired'])
        self.assertEqual(event['configuration']['facts']['providerActive'], False)

    def test_real_dual_feed_keeps_review_reference_without_old_art(self):
        from tests.test_visual_bridge import NOW, envelope, record, sid, state
        from tools.spacefox.schedule import IdKind
        from tools.spacefox.visual_bridge import build_artifact, read_ref, validate_feed, FEED_PATH
        from tools.spacefox.wire import validate_feed as validate_v1
        for model, current in [('164', True), ('39', False), ('999999', False)]:
            launch = record(configuration_id=sid(IdKind.CONFIGURATION, model))
            files, _ = build_artifact(state(launch), self.catalog, NOW, publisher=envelope(),
                                      root=ROOT, eligibility=self.registry)
            old = validate_v1(files['feed.json'])
            new_feed = validate_feed(files[FEED_PATH])
            identity = 'll2:configuration:' + model
            self.assertEqual(old['launch']['configuration_id'], identity)
            self.assertEqual(old['launch'], new_feed['launch'])
            self.assertEqual(old['launch']['source_validated_utc'], NOW - 3600)
            self.assertEqual(identity in old['unresolvedCatalogIds'], not current)
            selection = loads_json(read_ref(new_feed['visualSelection'], files))
            self.assertEqual(selection['roles']['rocket'] is not None, current)
        import subprocess
        import tempfile
        import sys
        with tempfile.TemporaryDirectory() as temp:
            for model, expected_exit in [('164', 0), ('39', 1)]:
                result = subprocess.run([sys.executable, '-B', 'tools/export_visuals.py',
                                         '--root', 'll2:configuration:' + model,
                                         '--output', str(Path(temp) / model)],
                                        cwd=ROOT, capture_output=True, text=True, check=False)
                self.assertEqual(result.returncode, expected_exit, result.stderr)

    def test_data_only_revision_keeps_evidence_and_reopens_changed_identity(self):
        import tempfile
        from tests.test_global_catalog import temporary_catalog, supplement, save_revision
        from tools.catalog import amend_recipe
        from tools.spacefox.current_catalog import load_registry
        with tempfile.TemporaryDirectory() as temp:
            root = temporary_catalog(temp)
            change = supplement('current-scope-revision')
            change['updates'] = [{'identity': 'll2:configuration:116',
                                  'changes': {'fullName': 'Ariane 64 revised name'}}]
            source = save_revision(root, change)
            revised = amend_recipe(root, root / 'catalog/source.json', source,
                                   '2026-11-12.scope-revision-test')
            registry = load_registry(root, revised)
            self.assertEqual(registry['records']['ll2:configuration:116']['state'], 'needs-review')
            self.assertEqual(registry['records']['ll2:configuration:164']['state'], 'current-evidence')
            self.assertEqual(registry['catalogVersion'], revised['catalogVersion'])
            self.assertTrue((root / 'catalog/source.json').exists())

    def test_invalid_or_stale_registry_cannot_activate(self):
        for edit in ('missing', 'extra', 'stale', 'date', 'source', 'placeholder'):
            registry = copy.deepcopy(self.registry)
            if edit == 'missing':
                registry['records'].pop('ll2:configuration:116')
            elif edit == 'extra':
                registry['records']['ll2:configuration:999999'] = registry['records']['ll2:configuration:116']
            elif edit == 'stale':
                registry['catalogVersion'] = 'other'
            elif edit == 'date':
                registry['records']['ll2:configuration:116']['asOf'] = 'not-a-date'
            elif edit == 'source':
                registry['records']['ll2:configuration:116']['sources'] = []
            else:
                registry['records']['ll2:configuration:511']['state'] = 'current-evidence'
            with self.subTest(edit=edit), self.assertRaises(CatalogError):
                validate_registry(self.catalog, registry)


if __name__ == '__main__':
    unittest.main()
