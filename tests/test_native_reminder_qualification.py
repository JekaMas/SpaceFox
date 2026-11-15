"""Reconstruct the exact 0.1.14 predecessor and refuse a changed prior helper."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from tools.native_language_policy import software_locales

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'locales/catalog.json').read_text())
SNAPSHOT = ROOT / 'openspec/changes/add-launch-reminders/evidence/locale-015/prior/tools/spacefox/native_profile.py'

class ReminderQualificationTest(unittest.TestCase):
    def test_published_predecessor_reconstruction(self):
        self.assertEqual(software_locales(ROOT, CATALOG), ['en', 'ru', 'de', 'fr', 'es'])

    def test_changed_predecessor_helper_is_refused(self):
        original = Path.read_bytes
        def altered(path):
            raw = original(path)
            return raw + b'\n# changed' if path == SNAPSHOT else raw
        with patch.object(Path, 'read_bytes', altered):
            with self.assertRaisesRegex(ValueError, 'reminder qualification input changed'):
                software_locales(ROOT, CATALOG)
