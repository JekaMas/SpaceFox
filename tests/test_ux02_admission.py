"""Retained UX02 snapshot stays historical; current tampering fails."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from tools.native_language_policy import software_locales

ROOT=Path(__file__).resolve().parents[1]
class HistoricalAdmission(unittest.TestCase):
    def test_historical_root_replays_and_changed_current_owner_is_rejected(self):
        catalog=json.loads((ROOT/'locales/catalog.json').read_text())
        record=json.loads((ROOT/catalog['supportPolicy']['softwareQualificationProof']['ux02DeltaProof']['path']).read_text())
        old=ROOT/record['priorSnapshots']['watchface/source/SceneRenderer.mc']['path']
        self.assertNotEqual(old.read_bytes(), (ROOT/'watchface/source/SceneRenderer.mc').read_bytes())
        self.assertEqual(software_locales(ROOT),catalog['supportPolicy']['primaryLocales'])
        with tempfile.TemporaryDirectory(prefix='spacefox-ux02-tamper-') as d:
            root=Path(d)
            for folder in ('watchface','locales','tools'): shutil.copytree(ROOT/folder,root/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            for folder in ('corpus','tests','assets','catalog','schemas'): (root/folder).symlink_to(ROOT/folder,target_is_directory=True)
            audit=root/'openspec/changes/close-static-runtime-audit/evidence/native-admission.json';audit.parent.mkdir(parents=True);shutil.copyfile(ROOT/audit.relative_to(root),audit)
            owner=root/'watchface/source/SceneRenderer.mc';owner.write_text(owner.read_text()+'\n// tampered current owner\n')
            with self.assertRaisesRegex(ValueError,'audit native input closure changed'): software_locales(root)
if __name__=='__main__': unittest.main()
