"""The published GitHub predecessor must remain distinct from Garmin status."""
import json
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from tools.release import validate_previous, BuildBlocked

ROOT=Path(__file__).resolve().parents[1]

class PublishedPredecessorTest(unittest.TestCase):
    def test_published_identity_and_next_version_policy(self):
        policy=json.loads((ROOT/'release/signing-identity.json').read_text())
        latest=policy['latest_release']
        self.assertEqual((latest['version'],latest['tag'],latest['kind']),('0.1.14','v0.1.14-test.1','github_test_prerelease'))
        self.assertEqual(latest['package_sha256'],'6c80caef8ec6527ae3a3cdc3129e8be1fb581c5a2e1d85634b963f1b92a26a27')
        self.assertEqual(latest['original_receipt_sha256'],'491362b67469489d6d833668f2e509a38fd98b611df44586a178417cb281b480')
        self.assertEqual(latest['source_revision'],'1bebd706649176b562681685d33b3cfcc7c9d4dd')
        self.assertEqual(latest['tag_revision'],'918c64f9a447cb8f3d61204bb7e37a8e2f255710')
        self.assertEqual(policy['previous_release']['version'],'0.1.13')
        self.assertEqual(policy['previous_release']['kind'],'garmin_ordinary_store_submission')
        self.assertEqual(policy['historical_release_012']['version'],'0.1.12')
        self.assertEqual(policy['historical_release_011']['version'],'0.1.11')
        app=ET.Element('application',id=policy['application_uuid'],version='0.1.15')
        prior={'version':latest['version'],'package_sha256':latest['package_sha256'],
               'application_uuid':policy['application_uuid'],'public_key_spki_sha256':policy['public_key_spki_sha256']}
        update=validate_previous(prior,app,policy['public_key_spki_sha256'])
        self.assertEqual(update['previous_version'],'0.1.14')
        self.assertEqual(update['previous_package_sha256'],latest['package_sha256'])
        self.assertFalse(update['migration_qualified'])
        for version in ('0.1.14','0.1.13'):
            app.set('version',version)
            with self.subTest(version=version),self.assertRaisesRegex(BuildBlocked,'strictly increase'):
                validate_previous(prior,app,policy['public_key_spki_sha256'])
        app.set('version','0.1.15')
        with self.assertRaisesRegex(BuildBlocked,'identity/key changed'):
            validate_previous(dict(prior,application_uuid='0'*32),app,policy['public_key_spki_sha256'])
