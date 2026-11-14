"""The prior language qualification survives only a source-bound delivery delta."""
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.native_language_policy import software_locales

ROOT = Path(__file__).resolve().parents[1]

class DeliveryAdmission(unittest.TestCase):
    def test_current_delta_and_prior_language_proof(self):
        self.assertEqual(software_locales(ROOT), ['en','ru','de','fr','es'])

    def test_changed_runtime_or_native_receipt_is_rejected(self):
        real = Path.read_bytes
        for target in (ROOT/'watchface/source/SpaceFoxView.mc',
                       ROOT/'openspec/changes/spacefox-watchface/evidence/delivery01/native-retained-final.log'):
            def changed(path):
                raw=real(path)
                return raw+b'\nchanged' if path == target else raw
            with self.subTest(target=target), patch.object(Path,'read_bytes',changed):
                with self.assertRaises(ValueError): software_locales(ROOT)

if __name__ == '__main__': unittest.main()
