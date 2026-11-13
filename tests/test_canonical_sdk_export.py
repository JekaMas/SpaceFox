"""Typed entry point for the retained real SDK export qualification owner.

Execution requires the pinned SDK, Java and explicit SDK execution authority.
This adapter does not itself constitute an export observation.
"""
import importlib.util
from pathlib import Path
import unittest


class CanonicalSdkExport(unittest.TestCase):
    def test_actual_joined_export_and_signature_qualification(self):
        owner = (Path(__file__).resolve().parents[1] / 'openspec/changes/spacefox-watchface/'
                 'evidence/core-release-integration/round1/run_joined_export.py')
        spec = importlib.util.spec_from_file_location('spacefox_joined_sdk_export', owner)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # The real owner performs the export, cryptographic inspection,
        # provenance assertions and protected disposable-key cleanup.
        self.assertIsNone(module.main())
