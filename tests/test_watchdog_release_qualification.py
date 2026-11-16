"""The additive watchdog release admission rejects unreviewed source drift."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools import native_watchdog_release_qualification as proof

ROOT = Path(__file__).resolve().parents[1]

class WatchdogReleaseQualificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'locales/catalog.json').read_text())
        cls.inputs = proof.native_inputs(ROOT)

    def test_bound_delta_and_existing_evidence_with_prior_result(self):
        with patch.object(proof, 'run_prior', return_value=['en','ru','de','fr','es']) as prior:
            self.assertEqual(proof.validate(ROOT, self.catalog), ['en','ru','de','fr','es'])
            prior.assert_called_once()

    def test_extra_unreviewed_native_file_is_rejected(self):
        changed = dict(self.inputs, **{'watchface/source/Unreviewed.mc': '0' * 64})
        with patch.object(proof, 'native_inputs', return_value=changed), \
             patch.object(proof, 'run_prior') as prior:
            with self.assertRaisesRegex(ValueError, 'native source closure changed'):
                proof.validate(ROOT, self.catalog)
            prior.assert_not_called()

    def test_changed_reviewed_native_file_is_rejected(self):
        changed = dict(self.inputs)
        changed['watchface/source/NativeFeed.mc'] = '0' * 64
        with patch.object(proof, 'native_inputs', return_value=changed), \
             patch.object(proof, 'run_prior') as prior:
            with self.assertRaisesRegex(ValueError, 'native source closure changed'):
                proof.validate(ROOT, self.catalog)
            prior.assert_not_called()

    def test_version_normalization_cannot_hide_nonlabel_module_content(self):
        catalog_proof = self.catalog['supportPolicy']['softwareQualificationProof']
        record = json.loads((ROOT / catalog_proof['watchdogReleaseProof']['path']).read_text())
        manifest = (ROOT / record['priorSnapshots']['watchface/manifest.xml']['path']).read_bytes()
        author_version = (ROOT / record['authorVersion']['path']).read_bytes()
        candidate = json.loads((ROOT / record['evidence']['candidate']['path']).read_text())
        proof.require_peer_source_binding(ROOT, manifest, author_version, candidate)
        with tempfile.TemporaryDirectory(prefix='watchdog-version-normalization-') as folder:
            root = Path(folder)
            shutil.copytree(ROOT / 'watchface', root / 'watchface', copy_function=os.link)
            generated = root / 'watchface/source/generated/NativeVersion.mc'
            changed = generated.read_bytes() + b'// unreviewed module content\n'
            generated.unlink()
            generated.write_bytes(changed)
            # Even if a changed generator accepts this output, normalization
            # must independently reject every change beyond the two labels.
            with self.assertRaisesRegex(ValueError, 'exceeds release BUILD/ID labels'):
                proof.require_peer_source_binding(root, manifest, author_version, candidate)

    def test_repinning_current_hashes_cannot_replace_peer_source(self):
        # Model a modified native owner plus a freshly repinned delta record.
        # Historical proof and peer candidate remain untouched. The independent
        # diagnostic-source digest must still refuse the modified bytes.
        with tempfile.TemporaryDirectory(prefix='watchdog-repin-test-') as folder:
            root = Path(folder)
            shutil.copytree(ROOT / 'watchface', root / 'watchface', copy_function=os.link)
            for name in ('tools', 'tests', 'openspec'):
                (root / name).symlink_to(ROOT / name, target_is_directory=True)
            changed = root / 'watchface/source/NativeFeed.mc'
            data = changed.read_bytes() + b'\n// unreviewed source mutation\n'
            changed.unlink()
            changed.write_bytes(data)
            # A repinner can also regenerate the normal NativeVersion file;
            # that must not evade the independent diagnostic-source binding.
            from tools.generate_native_version import render
            generated = root / 'watchface/source/generated/NativeVersion.mc'
            regenerated = render(root)
            generated.unlink()
            generated.write_text(regenerated)
            catalog = json.loads(json.dumps(self.catalog))
            ref = catalog['supportPolicy']['softwareQualificationProof']['watchdogReleaseProof']
            record = json.loads((ROOT / ref['path']).read_text())
            record['nativeInputs'] = proof.native_inputs(root)
            record['watchfaceInputs'] = {p.relative_to(root).as_posix(): proof.sha(p)
                                         for p in sorted((root / 'watchface').rglob('*')) if p.is_file()}
            fake = root / 'repinned-proof.json'
            fake.write_text(json.dumps(record, indent=2) + '\n')
            ref['sha256'] = hashlib.sha256(fake.read_bytes()).hexdigest()
            original = proof.checked
            def checked(candidate_root, name, expected):
                if name == ref['path']:
                    self.assertEqual(expected, hashlib.sha256(fake.read_bytes()).hexdigest())
                    return fake
                return original(candidate_root, name, expected)
            with patch.object(proof, 'checked', side_effect=checked), patch.object(proof, 'run_prior') as prior:
                with self.assertRaisesRegex(ValueError, 'differ from peer-verified diagnostic source'):
                    proof.validate(root, catalog)
                prior.assert_not_called()

if __name__ == '__main__':
    unittest.main()
