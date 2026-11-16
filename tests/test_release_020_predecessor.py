"""Current update guard against an actual retained published receipt and IQ.

The receipt remains a valid historical predecessor after publication metadata
advances. The version rule is exercised using a strictly later candidate and a
same-version refusal; this does not claim that the current candidate is released.
"""
import hashlib
import json
import os
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

from tools import release
from tools.build_watchface import ROOT, NS, BuildBlocked


class Release020PredecessorTest(unittest.TestCase):
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
        recorded = self.policy['latest_release']
        self.assertEqual(recorded['version'], '0.1.22')
        self.assertEqual(recorded['original_receipt_sha256'], hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(self.previous['version'], recorded['version'])
        self.assertEqual(self.previous['package_sha256'], recorded['package_sha256'])
        self.assertEqual(self.previous['source_revision'], recorded['source_revision'])
        self.assertEqual(self.app.get('version'), '0.1.24')
        result = release.validate_previous(self.previous, self.app, self.policy['public_key_spki_sha256'])
        self.assertEqual(result['kind'], 'higher_version_repair')
        self.assertFalse(result['migration_qualified'])

    def test_same_version_and_wrong_signer_refused(self):
        app = ET.fromstring(ET.tostring(self.app))
        app.set('version', self.previous['version'])
        with self.assertRaisesRegex(BuildBlocked, 'strictly increase'):
            release.validate_previous(self.previous, app, self.policy['public_key_spki_sha256'])
        parts = [int(part) for part in self.previous['version'].split('.')]
        parts[-1] += 1
        app.set('version', '.'.join(map(str, parts)))
        with self.assertRaisesRegex(BuildBlocked, 'identity/key changed'):
            release.validate_previous(self.previous, app, '0' * 64)

if __name__ == '__main__':
    unittest.main()
