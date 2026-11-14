import shutil
import tempfile
import unittest
from pathlib import Path
from tools.generate_native_version import GENERATED, ROOT, render, validate

class NativeBuildIdentity(unittest.TestCase):
    def test_current_identity_matches_native_inputs(self):
        validate(ROOT)
    def test_changed_native_input_requires_regeneration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            shutil.copytree(ROOT/'watchface',root/'watchface')
            validate(root)
            path=root/'watchface/source/NativeForegroundApp.mc'
            path.write_bytes(path.read_bytes()+b'\n// changed source input\n')
            with self.assertRaisesRegex(ValueError,'identity is stale'):
                validate(root)
            (root/GENERATED).write_text(render(root))
            validate(root)
            path=root/'watchface/resources/strings/strings.xml'
            if not path.exists():
                path=next(p for p in (root/'watchface/resources').rglob('*') if p.is_file())
            path.write_bytes(path.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'identity is stale'):
                validate(root)

if __name__ == '__main__': unittest.main()
