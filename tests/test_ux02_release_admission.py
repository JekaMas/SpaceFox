"""Historical source inputs remain distinct from current release inputs."""
import unittest
from unittest.mock import patch
from tools import release
from tools.build_watchface import ROOT

class HistoricalReleaseInputs(unittest.TestCase):
    def test_deleted_font_uses_hash_checked_snapshot(self):
        inputs = release.source_state(ROOT)['inputs']
        original = 'watchface/resources/fonts/Battery13.fnt'
        snapshot = 'openspec/changes/spacefox-watchface/evidence/ux02/prior/watchface__resources__fonts__Battery13.fnt'
        self.assertNotIn(original, inputs)
        self.assertIn(snapshot, inputs)
        real_digest = release.digest
        def altered(path):
            return '0' * 64 if str(path).endswith(snapshot) else real_digest(path)
        with patch.object(release, 'digest', side_effect=altered):
            with self.assertRaisesRegex(release.ReleaseBlocked, 'historical admission source snapshot'):
                release.source_state(ROOT)
