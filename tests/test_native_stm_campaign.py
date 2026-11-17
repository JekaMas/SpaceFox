"""Controls for the native campaign's output fence, not a model of STM behavior."""
import unittest
from tools.run_native_stm_campaign import coverage_counts


class NativeCampaignOutputControl(unittest.TestCase):
    def test_required_coverage_cannot_be_empty_zero_malformed_or_duplicated(self):
        self.assertEqual(coverage_counts('{start_applied=>2, callback_no=>3}'),
                         {'start_applied': 2, 'callback_no': 3})
        for text in ('{}', '{start=>0}', '{start=>1, start=>2}', '{start=1}', 'start=>2'):
            with self.subTest(text=text):
                self.assertIsNone(coverage_counts(text))


if __name__ == '__main__':
    unittest.main()
