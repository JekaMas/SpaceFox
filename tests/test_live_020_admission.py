"""The current release proof cannot repin an unreviewed native change."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools import native_live_020_qualification as owner

ROOT = Path(__file__).resolve().parents[1]


class LiveAdmissionBinding(unittest.TestCase):
    def test_repinned_changed_native_is_rejected(self):
        catalog = json.loads((ROOT / 'locales/catalog.json').read_text())
        proof = catalog['supportPolicy']['softwareQualificationProof']['liveRuntime020Proof']
        record = json.loads((ROOT / proof['path']).read_text())
        altered = dict(record['nativeInputs'])
        altered['watchface/source/FeedScene.mc'] = '0' * 64
        record['nativeInputs'] = altered
        with tempfile.TemporaryDirectory() as directory:
            replacement = Path(directory) / 'repinned.json'
            replacement.write_text(json.dumps(record))
            original = owner.checked
            def checked(root, ref):
                return replacement if ref['path'] == proof['path'] else original(root, ref)
            with patch.object(owner, 'native_inputs', return_value=altered), patch.object(owner, 'checked', side_effect=checked):
                with self.assertRaisesRegex(ValueError, 'differs from reviewed source'):
                    owner.validate(ROOT, catalog)


if __name__ == '__main__':
    unittest.main()
