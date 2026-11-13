"""Actual remaining primary menu text/glyph binding and missing-glyph refusal."""
import copy
import json
from pathlib import Path
import unittest
from tools.basic_menu_evidence import validate

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / 'openspec/changes/spacefox-watchface/evidence/basic-main-review/primary-menu-fonts.json'


class BasicMenuEvidenceTest(unittest.TestCase):
    def test_actual_primary_menu_font_binding(self):
        result = validate(json.loads(RECEIPT.read_text()))
        self.assertEqual(result['primaryModes'], 5)
        self.assertEqual(result['menuStringsPerMode'], 19)

    def test_actual_menu_missing_glyph_or_changed_label_refuses(self):
        observed = json.loads(RECEIPT.read_text())
        missing = copy.deepcopy(observed)
        missing['glyphs'][str(ord('Я'))] = '.notdef'
        with self.assertRaises(ValueError):
            validate(missing)
        changed = copy.deepcopy(observed)
        changed['menus']['ru'].pop('Language')
        with self.assertRaises(ValueError):
            validate(changed)
