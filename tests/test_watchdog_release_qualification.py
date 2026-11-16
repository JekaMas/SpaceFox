"""The additive watchdog release admission rejects unreviewed source drift."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tools import native_watchdog_release_qualification as proof

ROOT = Path(__file__).resolve().parents[1]

class WatchdogReleaseQualificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'locales/catalog.json').read_text())
        cls.inputs = proof.native_inputs(ROOT)

    def test_bound_delta_and_existing_evidence_with_prior_result(self):
        with patch.object(proof, 'run_prior', return_value=['en','ru','de','fr','es']) as prior:
            self.assertEqual(proof.validate(ROOT, self.catalog), ['en','ru','de','fr','es'])
            prior.assert_called_once()

    def test_extra_unreviewed_native_file_is_rejected(self):
        changed = dict(self.inputs, **{'watchface/source/Unreviewed.mc': '0' * 64})
        with patch.object(proof, 'native_inputs', return_value=changed), \
             patch.object(proof, 'run_prior') as prior:
            with self.assertRaisesRegex(ValueError, 'native source closure changed'):
                proof.validate(ROOT, self.catalog)
            prior.assert_not_called()

    def test_changed_reviewed_native_file_is_rejected(self):
        changed = dict(self.inputs)
        changed['watchface/source/NativeFeed.mc'] = '0' * 64
        with patch.object(proof, 'native_inputs', return_value=changed), \
             patch.object(proof, 'run_prior') as prior:
            with self.assertRaisesRegex(ValueError, 'native source closure changed'):
                proof.validate(ROOT, self.catalog)
            prior.assert_not_called()

if __name__ == '__main__':
    unittest.main()
