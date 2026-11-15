"""A current owner mutation must not inherit historical SDK evidence."""
import unittest
from pathlib import Path
from unittest.mock import patch
from tests.retained_native_binding import ROOT, verify_current

class CurrentOwnerBindingTest(unittest.TestCase):
    def test_current_owner_and_tamper_refusal(self):
        verify_current()
        original = Path.read_bytes
        target = (ROOT/'watchface/source/NativeSfr.mc').resolve()
        def altered(path):
            data = original(path)
            return data+b'changed' if path.resolve()==target else data
        with patch.object(Path, 'read_bytes', altered):
            with self.assertRaisesRegex(AssertionError, 'current integration source changed'):
                verify_current()
