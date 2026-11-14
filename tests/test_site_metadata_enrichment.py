"""Source-epoch enrichment and contradictions through the real schedule owner."""
from dataclasses import replace
import unittest
from tests import test_site_flag_protocol_working as captured
from tools.spacefox.schedule import ScheduleError, ScheduleState, merge_schedule

class SiteMetadataEnrichmentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        captured.SiteFlagWorkingTest.setUpClass()
        cls.record = captured.SiteFlagWorkingTest.record

    def test_additions_preserve_validation_and_stale_latch(self):
        old = replace(self.record, country_code=None, site_location_name=None)
        now = captured.captured.NOW
        initial = merge_schedule(ScheduleState(), (old,), now)
        later = now + 20000
        updated = merge_schedule(initial, (self.record,), later)
        entry = updated.entries[0]
        self.assertEqual(entry.record.source_validated_utc, old.source_validated_utc)
        self.assertTrue(entry.stale)
        self.assertFalse(entry.rescheduled)
        self.assertEqual(entry.record.country_code, self.record.country_code)
        self.assertEqual(entry.record.site_location_name, self.record.site_location_name)

    def test_known_values_cannot_change_or_disappear(self):
        import json
        from pathlib import Path
        corpus = json.loads((Path(__file__).resolve().parents[1]/'openspec/changes/spacefox-watchface/evidence/site-flag-visual-batch/header-footer-corpus.json').read_text())
        self.assertIn(['Atlas V 401', 'United Launch Alliance', 'ULA', 'Vandenberg SFB, CA, USA', 'US', 'Earth Science'], corpus['rows'])
        now = captured.captured.NOW
        state = merge_schedule(ScheduleState(), (self.record,), now)
        for candidate in (replace(self.record, country_code='JP'), replace(self.record, country_code=None),
                          replace(self.record, site_location_name='Vandenberg SFB, CA, USA'), replace(self.record, site_location_name=None)):
            with self.subTest(candidate=candidate), self.assertRaises(ScheduleError):
                merge_schedule(state, (candidate,), now)

class MetadataProofCorruptionTest(unittest.TestCase):
    def test_rehashed_failed_native_result_refuses_admission(self):
        import copy, hashlib, json, tempfile, shutil
        from pathlib import Path
        from tools.native_language_policy import software_locales
        root = Path(__file__).resolve().parents[1]
        catalog = json.loads((root/'openspec/changes/spacefox-watchface/evidence/test-release-20261114/prior-locale-catalog.json').read_text())
        reference = catalog['supportPolicy']['softwareQualificationProof']['visualDeltaProof']
        proof_path = Path(reference['path'])
        proof = json.loads((root/proof_path).read_text())
        log_path = Path(proof['metadataDelta']['evidence']['native.log']['path'])
        with tempfile.TemporaryDirectory(prefix='spacefox-metadata-proof-') as temporary:
            destination = Path(temporary)
            # Link immutable siblings and copy only the two attacked leaves.
            def overlay(source, target, paths):
                target.mkdir(exist_ok=True)
                for child in source.iterdir():
                    matching = [p for p in paths if p.parts[0] == child.name]
                    out = target/child.name
                    if not matching and source == root and child.name in ("watchface", "locales", "tools"):
                        shutil.copytree(child, out, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                    elif not matching:
                        out.symlink_to(child, target_is_directory=child.is_dir())
                    elif any(len(p.parts)==1 for p in matching):
                        out.write_bytes(child.read_bytes())
                    else:
                        overlay(child, out, [Path(*p.parts[1:]) for p in matching])
            overlay(root, destination, [proof_path, log_path])
            # Exercise the original corruption witness on its exact historical
            # resource and policy, independently of the new bootstrap wrapper.
            base = root/'openspec/changes/spacefox-watchface/evidence/test-release-20261114'
            shutil.copyfile(base/'prior-properties.xml', destination/'watchface/resources/settings/properties.xml')
            shutil.copyfile(base/'prior-native-language-policy.py.txt', destination/'tools/native_language_policy.py')
            shutil.copyfile(base/'prior-native-profile.py.txt', destination/'tools/spacefox/native_profile.py')
            log = destination/log_path
            raw = log.read_bytes()
            changed = raw.replace(b'enrichmentAdmission                 PASS', b'enrichmentAdmission                 FAIL')
            self.assertNotEqual(raw, changed)
            log.write_bytes(changed)
            proof['metadataDelta']['evidence']['native.log']['sha256'] = hashlib.sha256(changed).hexdigest()
            edited = json.dumps(proof, indent=2, ensure_ascii=False).encode()+b'\n'
            (destination/proof_path).write_bytes(edited)
            updated = copy.deepcopy(catalog)
            updated['supportPolicy']['softwareQualificationProof']['visualDeltaProof']['sha256'] = hashlib.sha256(edited).hexdigest()
            with self.assertRaisesRegex(ValueError, 'metadata native assertion failed'):
                software_locales(destination, updated)

    def test_rehashed_failed_header_result_refuses_admission(self):
        import copy, hashlib, json, tempfile, shutil
        from pathlib import Path
        from tools.native_language_policy import software_locales
        root = Path(__file__).resolve().parents[1]
        catalog = json.loads((root/'openspec/changes/spacefox-watchface/evidence/test-release-20261114/prior-locale-catalog.json').read_text())
        reference = catalog['supportPolicy']['softwareQualificationProof']['visualDeltaProof']
        proof_path = Path(reference['path'])
        proof = json.loads((root/proof_path).read_text())
        log_path = Path(proof['headerDelta']['evidence']['native.log']['path'])
        with tempfile.TemporaryDirectory(prefix='spacefox-metadata-proof-') as temporary:
            destination = Path(temporary)
            # Link immutable siblings and copy only the two attacked leaves.
            def overlay(source, target, paths):
                target.mkdir(exist_ok=True)
                for child in source.iterdir():
                    matching = [p for p in paths if p.parts[0] == child.name]
                    out = target/child.name
                    if not matching and source == root and child.name in ("watchface", "locales", "tools"):
                        shutil.copytree(child, out, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                    elif not matching:
                        out.symlink_to(child, target_is_directory=child.is_dir())
                    elif any(len(p.parts)==1 for p in matching):
                        out.write_bytes(child.read_bytes())
                    else:
                        overlay(child, out, [Path(*p.parts[1:]) for p in matching])
            overlay(root, destination, [proof_path, log_path])
            # Exercise the original corruption witness on its exact historical
            # resource and policy, independently of the new bootstrap wrapper.
            base = root/'openspec/changes/spacefox-watchface/evidence/test-release-20261114'
            shutil.copyfile(base/'prior-properties.xml', destination/'watchface/resources/settings/properties.xml')
            shutil.copyfile(base/'prior-native-language-policy.py.txt', destination/'tools/native_language_policy.py')
            shutil.copyfile(base/'prior-native-profile.py.txt', destination/'tools/spacefox/native_profile.py')
            log = destination/log_path
            raw = log.read_bytes()
            changed = raw.replace(b'capturedHeaderChoice                PASS', b'capturedHeaderChoice                FAIL')
            self.assertNotEqual(raw, changed)
            log.write_bytes(changed)
            proof['headerDelta']['evidence']['native.log']['sha256'] = hashlib.sha256(changed).hexdigest()
            edited = json.dumps(proof, indent=2, ensure_ascii=False).encode()+b'\n'
            (destination/proof_path).write_bytes(edited)
            updated = copy.deepcopy(catalog)
            updated['supportPolicy']['softwareQualificationProof']['visualDeltaProof']['sha256'] = hashlib.sha256(edited).hexdigest()
            with self.assertRaisesRegex(ValueError, 'header native assertion failed'):
                software_locales(destination, updated)
