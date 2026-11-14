"""Current proof rejects tampering while replaying the retained UX02 root."""
import json,shutil,tempfile,unittest
from pathlib import Path
from tools.native_language_policy import software_locales
ROOT=Path(__file__).resolve().parents[1]
class Ux03Admission(unittest.TestCase):
 def test_primary_qualification_and_changed_renderer_refusal(self):
  catalog=json.loads((ROOT/'locales/catalog.json').read_text())
  self.assertEqual(software_locales(ROOT),catalog['supportPolicy']['primaryLocales'])
  with tempfile.TemporaryDirectory(prefix='spacefox-ux03-tamper-') as d:
   root=Path(d)
   for folder in ('watchface','locales','tools','tests'):shutil.copytree(ROOT/folder,root/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
   for folder in ('openspec','corpus','assets','catalog','schemas'):(root/folder).symlink_to(ROOT/folder,target_is_directory=True)
   p=root/'watchface/source/SceneRenderer.mc';p.write_text(p.read_text()+'\n// tamper\n')
   with self.assertRaisesRegex(ValueError,'UX03 proof input changed'):software_locales(root)
