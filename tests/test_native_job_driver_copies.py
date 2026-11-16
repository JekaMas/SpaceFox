"""Release input safety for the shared native job test driver."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CANONICAL = ROOT / 'tests/native-runtime/CurrentJobs.mc'

class NativeJobDriverCopiesTest(unittest.TestCase):
    def test_test_driver_copies_are_regular_and_identical(self):
        source = CANONICAL.read_bytes()
        copies = [p for base in ('tests', 'watchface')
                  for p in (ROOT / base).rglob('CurrentJobs.mc') if p != CANONICAL]
        self.assertEqual(len(copies), 36)
        for path in copies:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertFalse(path.is_symlink())
                self.assertTrue(path.is_file())
                self.assertEqual(path.read_bytes(), source)

if __name__ == '__main__':
    unittest.main()
