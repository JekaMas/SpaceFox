"""Portable current catalog reference and explicit-review amendment controls."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_global_catalog import temporary_catalog, supplement
from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json
from tools.spacefox.current_catalog import load_registry

ROOT = Path(__file__).resolve().parents[1]


class CatalogMaintenanceCurrentTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = temporary_catalog(self.temp.name)
        self.source = self.root / 'catalog/source.json'
        self.recipe = loads_json(self.source.read_bytes())
        self.reference = loads_json((self.root / self.recipe['reference']['path']).read_bytes())
        self.catalog = build_catalog(self.root)
        self.registry = load_registry(self.root, self.catalog)
        self.revision = self.root / 'assets/global/test-maintenance.json'
        self.revision.write_bytes(canonical_bytes(supplement('test-maintenance-current')))
        self.ref = self.root / 'catalog/test-reference.json'
        self.review = self.root / 'catalog/test-review.json'

    def run_cli(self):
        return subprocess.run([sys.executable, '-B', str(ROOT / 'tools/catalog.py'), '--repo', str(self.root),
            '--amend', str(self.revision), '--catalog-version', 'test.maintenance.current',
            '--reference', str(self.ref), '--eligibility-review', str(self.review)],
            capture_output=True, text=True, timeout=180)

    def test_reference_and_review_round_trip(self):
        self.ref.write_bytes(canonical_bytes(self.reference))
        identity = next(iter(sorted(self.registry['records'])))
        self.review.write_bytes(canonical_bytes({identity: self.registry['records'][identity]}))
        result = self.run_cli()
        self.assertEqual(result.returncode, 0, result.stderr)
        after = build_catalog(self.root)
        self.assertEqual(load_registry(self.root, after)['records'], self.registry['records'])
        self.assertEqual(after['dictionaries'], self.catalog['dictionaries'])
        self.assertEqual(loads_json(self.source.read_bytes())['reference']['path'], 'catalog/test-reference.json')

    def test_mutated_reference_and_unknown_review_refuse_atomically(self):
        self.ref.write_bytes(canonical_bytes(self.reference))
        self.review.write_bytes(canonical_bytes({'ll2:configuration:999999999': {'state': 'current-evidence'}}))
        original = self.source.read_bytes()
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('unknown configuration', result.stderr)
        self.assertEqual(self.source.read_bytes(), original)
        identity = next(iter(sorted(self.registry['records'])))
        self.review.write_bytes(canonical_bytes({identity: self.registry['records'][identity]}))
        changed = copy.deepcopy(self.reference)
        changed['models'][0]['name'] = next(row['name'] for row in changed['models'][1:]
                                                   if row['name'] != changed['models'][0]['name'])
        self.ref.write_bytes(canonical_bytes(changed))
        result = self.run_cli()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('preserve every prior model fact', result.stderr)
        self.assertEqual(self.source.read_bytes(), original)
