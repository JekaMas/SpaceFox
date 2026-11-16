"""Current integration and update identity admission reject unqualified drift."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

from tools import native_b3_023_qualification as proof
from tools import release

ROOT = Path(__file__).resolve().parents[1]
KEY = '84e95bea4f3052a7c93f297e25605dc374a02f946b8011c65eec950b284146cc'

class IntegrationAdmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'locales/catalog.json').read_text())
        cls.app = ET.parse(ROOT / 'watchface/manifest.xml').getroot().find('{http://www.garmin.com/xml/connectiq}application')
        cls.previous = {'application_uuid': cls.app.get('id'), 'public_key_spki_sha256': KEY,
                        'version': '0.1.22', 'package_sha256': 'a' * 64}

    def test_current_bound_evidence(self):
        self.assertEqual(proof.validate(ROOT, self.catalog), ['en','ru','de','fr','es'])

    def test_native_or_fixture_drift_is_refused(self):
        native = proof.native_inputs(ROOT)
        native['watchface/source/SpaceFoxView.mc'] = '0' * 64
        with patch.object(proof, 'native_inputs', return_value=native):
            with self.assertRaisesRegex(ValueError, 'native input closure'):
                proof.validate(ROOT, self.catalog)
        tests = proof.test_inputs(ROOT)
        tests[next(iter(tests))] = '0' * 64
        with patch.object(proof, 'test_inputs', return_value=tests):
            with self.assertRaisesRegex(ValueError, 'test input closure'):
                proof.validate(ROOT, self.catalog)

    def test_locale_and_evidence_drift_is_refused(self):
        catalog = copy.deepcopy(self.catalog)
        catalog['supportPolicy']['softwareQualifiedLocales'] = ['en']
        with self.assertRaisesRegex(ValueError, 'original 0.1.22 proof failed'):
            proof.validate(ROOT, catalog)
        original = proof.checked
        for target in ('b3QueueAndRollover.log', 'b3AdmissionAndUnknown.log', 'b3OrdinaryReopen.log'):
            def altered(root, ref):
                if ref['path'].endswith(target):
                    raise ValueError('integration input changed')
                return original(root, ref)
            with self.subTest(evidence=target), patch.object(proof, 'checked', side_effect=altered):
                with self.assertRaisesRegex(ValueError, 'integration input changed'):
                    proof.validate(ROOT, self.catalog)

    def test_update_version_uuid_and_key(self):
        self.assertEqual(release.validate_previous(self.previous, self.app, KEY)['previous_version'], '0.1.22')
        for field, value in [('application_uuid','0'*32),('public_key_spki_sha256','0'*64),('version',self.app.get('version'))]:
            previous = dict(self.previous, **{field:value})
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                release.validate_previous(previous, self.app, KEY)

    def test_previous_receipt_rejects_wrong_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'SpaceFox.iq').write_bytes(b'wrong artifact')
            receipt={'status':'signed_candidate_built','source_dirty':False,
                     'packages':{'iq':{'path':'SpaceFox.iq','sha256':'a'*64}},'package_sha256':'a'*64}
            path=folder/'release.json';path.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(RuntimeError, 'package is missing or changed'):
                release.previous_release(path)

if __name__ == '__main__':
    unittest.main()
