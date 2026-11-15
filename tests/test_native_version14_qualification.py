"""The version-only proof must refuse altered current and prior inputs."""
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.native_language_policy import software_locales

ROOT=Path(__file__).resolve().parents[1]

class Version14QualificationTest(unittest.TestCase):
    def test_changed_manifest_refused(self):
        original=Path.read_bytes; target=(ROOT/'watchface/manifest.xml').resolve()
        def altered(path):
            data=original(path)
            return data+b' ' if path.resolve()==target else data
        with patch.object(Path,'read_bytes',altered),self.assertRaisesRegex(ValueError,'version native closure changed'):
            software_locales(ROOT)

    def test_changed_prior_input_refused(self):
        original=Path.read_bytes;target=(ROOT/'openspec/changes/spacefox-watchface/evidence/version-014/prior/watchface/manifest.xml').resolve()
        def altered(path):
            data=original(path)
            return data+b' ' if path.resolve()==target else data
        with patch.object(Path,'read_bytes',altered),self.assertRaisesRegex(ValueError,'version proof input changed'):
            software_locales(ROOT)

    def test_changed_header_metrics_refused(self):
        original=Path.read_bytes;target=(ROOT/'openspec/changes/spacefox-watchface/evidence/version-014/header-glyph-metrics.json').resolve()
        def altered(path):
            data=original(path)
            return data+b' ' if path.resolve()==target else data
        with patch.object(Path,'read_bytes',altered),self.assertRaisesRegex(ValueError,'version proof input changed'):
            software_locales(ROOT)
