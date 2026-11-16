"""Current B1 admission retains old evidence and rejects changed inputs."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

from tools import native_b1_019_qualification as b1
from tools.release import ReleaseBlocked, previous_release, validate_previous

ROOT = Path(__file__).resolve().parents[1]

class B1ReleaseAdmissionTest(unittest.TestCase):
    def setUp(self):
        self.catalog = json.loads((ROOT/'locales/catalog.json').read_text())

    def test_current_scope_passes(self):
        self.assertEqual(b1.validate(ROOT, self.catalog), ['en','ru','de','fr','es'])

    def test_changed_native_and_evidence_are_rejected(self):
        original = b1.sha
        for suffix in ('watchface/source/SpaceFoxView.mc',
                       'openspec/changes/restore-fr165-runtime-guarantees/evidence/peer-deferred-fitness-green.log'):
            def changed(path):
                return '0'*64 if Path(path).as_posix().endswith(suffix) else original(path)
            with self.subTest(path=suffix), patch.object(b1, 'sha', side_effect=changed):
                with self.assertRaises(ValueError):
                    b1.validate(ROOT, self.catalog)

    def test_locale_policy_cannot_change_under_delta(self):
        changed = copy.deepcopy(self.catalog)
        changed['supportPolicy']['softwareQualifiedLocales'] = ['en']
        with self.assertRaisesRegex(ValueError, 'locale policy'):
            b1.validate(ROOT, changed)

    def test_predecessor_uuid_key_version_and_package_rejected(self):
        app = ET.Element('application', {'id':'official','version':'0.1.19'})
        old = {'application_uuid':'official','public_key_spki_sha256':'a'*64,
               'version':'0.1.18','package_sha256':'b'*64}
        self.assertEqual(validate_previous(old, app, 'a'*64)['previous_version'], '0.1.18')
        for key, value in [('application_uuid','other'),('public_key_spki_sha256','c'*64),
                           ('version','0.1.19'),('package_sha256','bad')]:
            with self.subTest(key=key):
                bad = dict(old, **{key:value})
                with self.assertRaises(ReleaseBlocked):
                    validate_previous(bad, app, 'a'*64)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root/'SpaceFox.iq').write_bytes(b'wrong package')
            receipt = {'status':'signed_candidate_built','source_dirty':False,
                       'package_sha256':'b'*64,'packages':{'iq':{'path':'SpaceFox.iq','sha256':'b'*64}}}
            (root/'release.json').write_text(json.dumps(receipt))
            with self.assertRaises(ReleaseBlocked):
                previous_release(root/'release.json')

if __name__ == '__main__':
    unittest.main()
