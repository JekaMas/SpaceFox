"""A repinned record cannot silently admit a changed native closure."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from tools import native_audit_025_qualification as owner

ROOT=Path(__file__).resolve().parents[1]
class Current022Binding(unittest.TestCase):
    def test_repinned_native_delta_is_refused(self):
        catalog=json.loads((ROOT/'locales/catalog.json').read_text());ref=catalog['supportPolicy']['softwareQualificationProof']['auditRuntime025Proof']
        record=json.loads((ROOT/ref['path']).read_text());record['nativeInputs']['watchface/source/FeedScene.mc']='0'*64
        with tempfile.TemporaryDirectory() as directory:
            replacement=Path(directory)/'record.json';replacement.write_text(json.dumps(record));original=owner.checked
            def read(root,item):return replacement if item['path']==ref['path'] else original(root,item)
            with patch.object(owner,'checked',side_effect=read),patch.object(owner,'native_inputs',return_value=record['nativeInputs']):
                with self.assertRaisesRegex(ValueError,'audit proof differs from reviewed closure'):owner.validate(ROOT,catalog)

    def test_unreviewed_native_delta_is_refused(self):
        catalog=json.loads((ROOT/'locales/catalog.json').read_text())
        native=owner.native_inputs(ROOT);native['watchface/source/WatchClock.mc']='0'*64
        with patch.object(owner,'native_inputs',return_value=native):
            with self.assertRaisesRegex(ValueError,'audit native input closure changed'):owner.validate(ROOT,catalog)

    def test_release_requires_matching_independent_peer(self):
        import re, subprocess
        from tools import release
        native=(ROOT/'watchface/source/generated/NativeVersion.mc').read_text()
        native_id=re.search(r'const ID = "([0-9a-f]{8})"',native).group(1)
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        good={'data': {'kind':'known-site-coordinates-independent-peer','status':'GREEN','version':'0.2.8','native_id':native_id,'source_revision':revision}}
        with patch.object(owner,'validate',return_value=[]):
            with self.assertRaises(Exception): release.require_combined_peer(ROOT,[])
            bad={'data':dict(good['data'],native_id='00000000')}
            with self.assertRaises(Exception): release.require_combined_peer(ROOT,[bad])
            release.require_combined_peer(ROOT,[good])
            with patch.object(release,'git',return_value='watchface/source/SpaceFoxView.mc'):
                with self.assertRaises(Exception):release.require_combined_peer(ROOT,[good])

    def test_current_peer_binds_workflow_and_sparse_seed(self):
        import re, subprocess
        from tools import release
        native=(ROOT/'watchface/source/generated/NativeVersion.mc').read_text()
        native_id=re.search(r'const ID = "([0-9a-f]{8})"',native).group(1)
        revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
        good={'data':{'kind':'known-site-coordinates-independent-peer','status':'GREEN','version':'0.2.8','native_id':native_id,'source_revision':revision}}
        original=release.git
        # Report a post-review change only if the real gate asks Git to inspect
        # that semantic input. This tests its selected closure, not a blanket
        # mocked dirty result unrelated to the passed pathspec.
        with patch.object(owner,'validate',return_value=[]):
            for changed_path in ('.github/workflows/update-feed.yml','.github/spacefox-inputs.txt','release/signing-identity.json','tests/test_current_motion_publisher.py','tests/test_known_site_coordinates.py','tests/test_watch_snapshot.py'):
                def changed(root,*args):
                    if args[0]=='diff':return changed_path+'\n' if changed_path in args else ''
                    return original(root,*args)
                with self.subTest(path=changed_path),patch.object(release,'git',side_effect=changed):
                    with self.assertRaisesRegex(Exception,'reviewed runtime audit source changed'):
                        release.require_combined_peer(ROOT,[good])
