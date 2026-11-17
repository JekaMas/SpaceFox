"""Current qualified model geometry and atomic refusal at the catalog CLI."""
from pathlib import Path
import tempfile
import unittest

from tests import test_catalog_current_transactions as current
from tools.spacefox.catalog import build_catalog
from tools.spacefox.graphics import build_pack, write_pack


class CanonicalGeometry(unittest.TestCase):
    def test_qualified_selection_reopens_and_reuses_objects(self):
        current.CurrentCatalogTransactions.test_replace_reopen_select_and_preserve(self)

    def test_unsupported_geometry_refuses_without_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = current.temporary_catalog(tmp)
            catalog = build_catalog(root)
            store = root / 'selected'
            write_pack(store, build_pack(root, catalog, roots=[current.MODEL]))
            output = root / 'build/catalog.json'
            output.parent.mkdir(); output.write_bytes(b'accepted catalog bytes')
            path, _, _ = current.candidate(root, 'geometry')
            before = current.snapshot(root)
            result = current.cli(root, path, 'technical.invalid.geometry', output)
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertIn('unsupported source element image', result.stderr)
            self.assertEqual(current.snapshot(root), before)
            self.assertEqual(output.read_bytes(), b'accepted catalog bytes')
