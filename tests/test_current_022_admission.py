"""A repinned record cannot silently admit a changed native closure."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import native_current_022_qualification as owner

ROOT=Path(__file__).resolve().parents[1]
class Current022Binding(unittest.TestCase):
    def test_repinned_native_delta_is_refused(self):
        catalog=json.loads((ROOT/'locales/catalog.json').read_text());ref=catalog['supportPolicy']['softwareQualificationProof']['currentIntegration022Proof']
        record=json.loads((ROOT/ref['path']).read_text());record['nativeInputs']['watchface/source/FeedScene.mc']='0'*64
        with tempfile.TemporaryDirectory() as directory:
            replacement=Path(directory)/'record.json';replacement.write_text(json.dumps(record));original=owner.checked
            def read(root,item):return replacement if item['path']==ref['path'] else original(root,item)
            with patch.object(owner,'checked',side_effect=read),patch.object(owner,'native_inputs',return_value=record['nativeInputs']):
                with self.assertRaisesRegex(ValueError,'differs from reviewed closure'):owner.validate(ROOT,catalog)

    def test_unreviewed_native_delta_is_refused(self):
        catalog=json.loads((ROOT/'locales/catalog.json').read_text())
        native=owner.native_inputs(ROOT);native['watchface/source/WatchClock.mc']='0'*64
        with patch.object(owner,'native_inputs',return_value=native):
            with self.assertRaisesRegex(ValueError,'trusted snapshot native delta differs'):owner.validate(ROOT,catalog)

    def test_release_requires_matching_independent_peer(self):
        import re, subprocess
        from tools import release
        native=(ROOT/'watchface/source/generated/NativeVersion.mc').read_text()
        native_id=re.search(r'const ID = "([0-9a-f]{8})"',native).group(1)
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        good={'data': {'kind':'state-machine-independent-peer','status':'GREEN','version':'0.2.5','native_id':native_id,'source_revision':revision}}
        with patch.object(owner,'validate',return_value=[]):
            with self.assertRaises(Exception): release.require_combined_peer(ROOT,[])
            bad={'data':dict(good['data'],native_id='00000000')}
            with self.assertRaises(Exception): release.require_combined_peer(ROOT,[bad])
            release.require_combined_peer(ROOT,[good])
            with patch.object(release,'git',return_value='watchface/source/SpaceFoxView.mc'):
                with self.assertRaises(Exception):release.require_combined_peer(ROOT,[good])
