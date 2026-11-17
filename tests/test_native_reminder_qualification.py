"""Current reminder owner is covered by active source admission; old receipts stay historical."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from tools.native_language_policy import software_locales

ROOT = Path(__file__).resolve().parents[1]
CATALOG = json.loads((ROOT / 'locales/catalog.json').read_text())
SNAPSHOT = ROOT / 'watchface/source/LaunchReminder.mc'

class ReminderQualificationTest(unittest.TestCase):
    def test_published_predecessor_reconstruction(self):
        self.assertEqual(software_locales(ROOT, CATALOG), ['en', 'ru', 'de', 'fr', 'es'])

    def test_changed_predecessor_helper_is_refused(self):
        original = Path.read_bytes
        def altered(path):
            raw = original(path)
            return raw + b'\n# changed' if path == SNAPSHOT else raw
        with patch.object(Path, 'read_bytes', altered):
            with self.assertRaisesRegex(ValueError, 'audit native input closure changed'):
                software_locales(ROOT, CATALOG)
