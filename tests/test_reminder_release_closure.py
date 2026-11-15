"""The reminder evidence allowlist does not admit unrelated paths."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from tools import release

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'release/native-admission-inputs.json'

class ReminderReleaseClosureTest(unittest.TestCase):
    def test_unrelated_evidence_is_refused(self):
        real_read = Path.read_text
        real_git = release.git
        def read(path, *args, **kwargs):
            text = real_read(path, *args, **kwargs)
            if path == MANIFEST:
                return json.dumps(['openspec/changes/unrelated/evidence/not-allowed.json'] + json.loads(text))
            return text
        def git(root, *args):
            if args[:1] == ('status',):
                return ''
            return real_git(root, *args)
        with patch.object(Path, 'read_text', read), patch.object(release, 'git', git):
            with self.assertRaisesRegex(release.ReleaseBlocked, 'unsafe or untracked native admission input'):
                release.source_state(ROOT)
