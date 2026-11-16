"""Current release history boundary using the retained actual 0.1.18 receipt.

This does not replace the separate immutable 0.1.12 historical witness and
never reads the private production key or executes a Garmin export.
"""
import hashlib
import json
import os
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools import release
from tools.build_watchface import ROOT, NS, BuildBlocked

class Release018PredecessorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = os.environ.get('SPACEFOX_PUBLISHED_RELEASE_RECEIPT')
        if not path:
            raise RuntimeError('retained SPACEFOX_PUBLISHED_RELEASE_RECEIPT is required')
        cls.path = Path(path).resolve()
        cls.previous = release.previous_release(cls.path)
        cls.policy = json.loads((ROOT / 'release/signing-identity.json').read_text())
        cls.app = ET.parse(ROOT / 'watchface/manifest.xml').getroot().find('iq:application', NS)

    def test_real_receipt_iq_and_higher_version(self):
        latest = self.policy['latest_release']
        self.assertEqual(latest['version'], '0.1.18')
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), latest['original_receipt_sha256'])
        self.assertEqual(self.previous['version'], latest['version'])
        self.assertEqual(self.previous['package_sha256'], latest['package_sha256'])
        self.assertEqual(self.previous['source_revision'], latest['source_revision'])
        self.assertEqual(self.app.get('version'), '0.1.20')
        result = release.validate_previous(self.previous, self.app, self.policy['public_key_spki_sha256'])
        self.assertEqual(result['kind'], 'higher_version_repair')
        self.assertFalse(result['migration_qualified'])

    def test_same_version_and_wrong_signer_refused(self):
        app = ET.fromstring(ET.tostring(self.app))
        app.set('version', '0.1.18')
        with self.assertRaisesRegex(BuildBlocked, 'strictly increase'):
            release.validate_previous(self.previous, app, self.policy['public_key_spki_sha256'])
        with self.assertRaisesRegex(BuildBlocked, 'identity/key changed'):
            release.validate_previous(self.previous, self.app, '0' * 64)

if __name__ == '__main__':
    unittest.main()
