"""Current published predecessor policy and actual receipt admission boundaries."""
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from xml.etree import ElementTree as ET

from tools import release
from tools.build_watchface import NS, BuildBlocked

ROOT = Path(__file__).resolve().parents[1]


class PublishedPredecessorTest(unittest.TestCase):
    def test_published_identity_and_next_version_policy(self):
        policy = json.loads((ROOT / 'release/signing-identity.json').read_text())
        latest = policy['latest_release']
        self.assertEqual((latest['version'], latest['tag'], latest['kind']),
                         ('0.1.16', 'v0.1.16', 'github_regular_release_and_garmin_submission'))
        self.assertEqual(latest['package_sha256'], '09ef11c1fbc38af7e3e55327ecd213b361d8f66bbf271f6739763056dbca33e7')
        self.assertEqual(latest['original_receipt_sha256'], '09e3ed20e5c7964b8d0907fe94a49c4c3ee8627bd82ab47fddfd07c2dbdd7ca7')
        self.assertEqual(latest['source_revision'], 'b1e0c56df8ef04b4a73637c80f176b6c0ff9cfed')
        self.assertEqual(latest['tag_revision'], 'b1e0c56df8ef04b4a73637c80f176b6c0ff9cfed')
        self.assertEqual(policy['historical_release_015']['version'], '0.1.15')
        self.assertEqual(policy['historical_release_015']['original_receipt_sha256'], '357b36af8e5e1d8c876705e0fa9cf52e1936216dcec0730bf1ddb57ed04bce44')
        self.assertEqual(policy['historical_release_014']['version'], '0.1.14')
        self.assertEqual(policy['historical_release_014']['package_sha256'], '6c80caef8ec6527ae3a3cdc3129e8be1fb581c5a2e1d85634b963f1b92a26a27')
        self.assertEqual(policy['previous_release']['version'], '0.1.13')
        self.assertEqual(policy['previous_release']['kind'], 'garmin_ordinary_store_submission')
        self.assertEqual(policy['historical_release_012']['version'], '0.1.12')
        self.assertEqual(policy['historical_release_011']['version'], '0.1.11')
        app = ET.Element('application', id=policy['application_uuid'], version='0.1.17')
        prior = {'version': latest['version'], 'package_sha256': latest['package_sha256'],
                 'application_uuid': policy['application_uuid'], 'public_key_spki_sha256': policy['public_key_spki_sha256']}
        update = release.validate_previous(prior, app, policy['public_key_spki_sha256'])
        self.assertEqual((update['previous_version'], update['previous_package_sha256']),
                         ('0.1.16', latest['package_sha256']))
        self.assertFalse(update['migration_qualified'])
        for version in ('0.1.16', '0.1.15'):
            app.set('version', version)
            with self.subTest(version=version), self.assertRaisesRegex(BuildBlocked, 'strictly increase'):
                release.validate_previous(prior, app, policy['public_key_spki_sha256'])
        app.set('version', '0.1.17')
        with self.assertRaisesRegex(BuildBlocked, 'identity/key changed'):
            release.validate_previous(dict(prior, application_uuid='0' * 32), app, policy['public_key_spki_sha256'])
        with self.assertRaisesRegex(BuildBlocked, 'identity/key changed'):
            release.validate_previous(prior, app, '0' * 64)


class ExportBoundaryReached(Exception):
    """Stop after production history admission, before custody/export."""


@unittest.skipUnless(os.environ.get('SPACEFOX_PUBLISHED_RELEASE_RECEIPT'), 'actual published receipt not supplied')
class ActualPublishedPredecessorTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path = Path(os.environ['SPACEFOX_PUBLISHED_RELEASE_RECEIPT']).resolve()
        cls.prior = release.previous_release(cls.path)
        cls.policy = json.loads((ROOT / 'release/signing-identity.json').read_text())
        cls.public = (cls.path.parent / 'developer-public.spki').read_bytes()
        cls.lock = json.loads((ROOT / 'watchface/toolchain-lock.json').read_text())

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='spacefox-published-016-')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def admit(self, version, previous):
        tree = ET.parse(ROOT / 'watchface/manifest.xml')
        tree.getroot().find('iq:application', NS).set('version', version)
        output = self.base / 'not-exported'
        with ExitStack() as stack:
            for name, value in (('source_state', {'inputs': {}}),
                                ('discover_toolchain', {'lock': self.lock}),
                                ('validate_api_policy', None), ('validate_manifest', tree),
                                ('public_key', self.public)):
                stack.enter_context(patch.object(release, name, return_value=value))
            stack.enter_context(patch.object(release, 'backup_status', side_effect=ExportBoundaryReached))
            try:
                release.build_release(output, key=self.base / 'unused-no-private-key', root=ROOT, previous=previous)
            finally:
                self.assertFalse(output.exists())

    def test_actual_16_receipt_and_iq_reach_next_version_boundary(self):
        latest = self.policy['latest_release']
        self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(), latest['original_receipt_sha256'])
        self.assertEqual(hashlib.sha256(self.public).hexdigest(), self.policy['public_key_spki_sha256'])
        self.assertEqual(self.prior['version'], latest['version'])
        self.assertEqual(self.prior['package_sha256'], latest['package_sha256'])
        self.assertEqual(self.prior['source_revision'], latest['source_revision'])
        self.assertEqual(self.prior['application_uuid'], self.policy['application_uuid'])
        self.assertEqual(self.prior['update']['previous_version'], '0.1.15')
        with self.assertRaises(ExportBoundaryReached):
            self.admit('0.1.17', self.path)
        for version in ('0.1.16', '0.1.15'):
            with self.subTest(version=version), self.assertRaisesRegex(BuildBlocked, 'strictly increase'):
                self.admit(version, self.path)
        with self.assertRaisesRegex(BuildBlocked, 'committed latest release receipt/package'):
            self.admit('0.1.17', None)
        app = ET.Element('application', id=self.policy['application_uuid'], version='0.1.17')
        for prior, key in ((dict(self.prior, application_uuid='0' * 32), self.policy['public_key_spki_sha256']),
                           (self.prior, '0' * 64)):
            with self.assertRaisesRegex(BuildBlocked, 'identity/key changed'):
                release.validate_previous(prior, app, key)

    def test_different_retained_history_is_refused(self):
        shutil.copyfile(self.path.parent / self.prior['packages']['iq']['path'], self.base / 'SpaceFox.iq')
        changed = dict(self.prior, version='0.0.9')
        path = self.base / 'release.json'
        path.write_text(json.dumps(changed))
        with self.assertRaisesRegex(BuildBlocked, 'committed latest release receipt/package'):
            self.admit('0.1.17', path)

    def test_same_package_with_altered_receipt_is_refused(self):
        shutil.copyfile(self.path.parent / self.prior['packages']['iq']['path'], self.base / 'SpaceFox.iq')
        path = self.base / 'release.json'
        for altered in (dict(self.prior, source_revision='0' * 40),
                        dict(self.prior, extra_unpublished_metadata=True)):
            path.write_text(json.dumps(altered))
            with self.subTest(altered=altered), self.assertRaisesRegex(
                    BuildBlocked, 'committed latest release receipt/package'):
                self.admit('0.1.17', path)

    def test_actual_receipt_must_match_committed_source(self):
        wrong = dict(self.policy, latest_release=dict(self.policy['latest_release'], source_revision='0' * 40))
        with patch.object(release, 'identity_policy', return_value=wrong):
            with self.assertRaisesRegex(BuildBlocked, 'committed latest release receipt/package'):
                self.admit('0.1.17', self.path)
