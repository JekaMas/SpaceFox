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

    def test_release_requires_matching_independent_peer(self):
        from tools import release
        catalog=json.loads((ROOT/'locales/catalog.json').read_text())
        digest='9838392688273e99b88e3808b4a4a24e7f549e4a97d418386ba461aa2243592c'
        good={'data': {'kind':'current022-independent-native-peer', 'status':'GREEN', 'integration_proof_sha256':digest}}
        with patch.object(owner,'validate',return_value=[]):
            with self.assertRaises(Exception): release.require_combined_peer(ROOT,[])
            bad={'data':dict(good['data'],integration_proof_sha256='0'*64)}
            with self.assertRaises(Exception): release.require_combined_peer(ROOT,[bad])
            release.require_combined_peer(ROOT,[good])
