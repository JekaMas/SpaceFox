"""The historical-version mapping must not hide altered current owners."""
from pathlib import Path
import unittest
from unittest.mock import patch
from tests import test_current_data_convergence as data_reader
from tests import test_current_timing_convergence as timing_reader

class CurrentVersionBindingTest(unittest.TestCase):
    def test_changed_current_build_id_is_rejected_by_native_readers(self):
        original = Path.read_bytes
        for replacement in (b'ID = "deadbeef"', b'ID = "de5011f4"'):
            def altered(path):
                data = original(path)
                if path.as_posix().endswith('watchface/source/generated/NativeVersion.mc'):
                    return data.replace(b'ID = "ea38c443"', replacement)
                return data
            with self.subTest(replacement=replacement), patch.object(Path, 'read_bytes', altered):
                with self.assertRaisesRegex(AssertionError, 'NativeVersion.mc'):
                    data_reader.CurrentDataConvergenceTest.setUpClass()
                with self.assertRaisesRegex(AssertionError, 'NativeVersion.mc'):
                    timing_reader.CurrentTimingConvergenceTest('test_retained_native_countdown_pair_positive').test_retained_native_countdown_pair_positive()


if __name__ == '__main__': unittest.main()
