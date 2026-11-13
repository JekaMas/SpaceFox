"""Published production history admission, stopping before SDK export.

Use the retained real candidate receipt and IQ via
SPACEFOX_PUBLISHED_RELEASE_RECEIPT. Toolchain discovery/API/manifest validation,
source cleanliness and key access are explicitly substituted to isolate history
admission. Public SPKI bytes come from the real IQ; no private custody is read.
These checks prove neither signed higher-version output nor native acceptance.
"""
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from tools import release
from tools.build_watchface import ROOT, NS, BuildBlocked


class ExportBoundaryReached(Exception):
    """History was accepted; deliberately stop before any export/custody work."""


class PublishedReleaseHistoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        configured = os.environ.get('SPACEFOX_PUBLISHED_RELEASE_RECEIPT')
        if not configured:
            raise RuntimeError('retained SPACEFOX_PUBLISHED_RELEASE_RECEIPT is required')
        cls.previous_path = Path(configured).resolve()
        cls.previous = release.previous_release(cls.previous_path)
        cls.policy = json.loads((ROOT / 'release/signing-identity.json').read_text())
        cls.latest = cls.policy['latest_release']
        cls.iq = cls.previous_path.parent / cls.previous['packages']['iq']['path']
        cls.public = subprocess.run(
            ['/usr/bin/tar', '-xOf', str(cls.iq), 'dev_key.pub'],
            capture_output=True, check=True).stdout
        cls.lock = json.loads((ROOT / 'watchface/toolchain-lock.json').read_text())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='spacefox-public-history-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def admit(self, version, previous):
        # These owners already have retained native greens. Only history admission
        # is under test; no result here is a fresh toolchain/source/key verdict.
        tree = ET.parse(ROOT / 'watchface/manifest.xml')
        tree.getroot().find('iq:application', NS).set('version', version)
        output = self.base / 'not-exported'
        with ExitStack() as stack:
            for name, value in (
                ('source_state', {'inputs': {}}),
                ('discover_toolchain', {'lock': self.lock}),
                ('validate_api_policy', None),
                ('validate_manifest', tree),
                ('public_key', self.public),
            ):
                stack.enter_context(patch.object(release, name, return_value=value))
            boundary = stack.enter_context(patch.object(
                release, 'backup_status', side_effect=ExportBoundaryReached))
            try:
                release.build_release(output, key=self.base / 'unused-no-private-key',
                                      root=ROOT, previous=previous)
            finally:
                self.assertFalse(output.exists(), 'history controls must not create SDK output')
            return boundary

    def test_actual_public_identity_artifact_and_acceptance_boundary(self):
        self.assertEqual(self.latest['version'], '0.1.0')
        self.assertEqual(self.latest['package_sha256'],
                         'b0126d9ed13cf186f2fc15be984231da06a562070f3aa2d3d5395c7bdefc037a')
        self.assertEqual(self.previous['version'], self.latest['version'])
        self.assertEqual(self.previous['package_sha256'], self.latest['package_sha256'])
        self.assertEqual(self.previous['application_uuid'],
                         'ec8b7c8a8ea54ee9ac91ee6e7a674d15')
        self.assertEqual(self.previous['public_key_spki_sha256'], self.policy['public_key_spki_sha256'])
        self.assertEqual(hashlib.sha256(self.public).hexdigest(), self.policy['public_key_spki_sha256'])
        self.assertEqual(hashlib.sha256(self.previous_path.read_bytes()).hexdigest(),
                         self.latest['original_receipt_sha256'])
        prg = self.previous_path.parent / self.previous['packages']['prg']['path']
        self.assertEqual(hashlib.sha256(prg.read_bytes()).hexdigest(),
                         'aa0376f64da4b7a6d9ddcf253c034360c23b1157e2aee9a20953632356a3f788')
        self.assertFalse(self.previous['official_release'])
        self.assertFalse(self.previous['publication_ready'])
        self.assertEqual(self.latest['kind'], 'github_prerelease_for_physical_testing')
        self.assertEqual(self.latest['tag'], 'v0.1.0-test.1')
        readback = json.loads((ROOT / self.latest['evidence']).read_text())
        self.assertEqual(readback['release_url'], self.latest['url'])
        self.assertEqual(len(readback['anonymous_https_downloads']), 8)
        for asset in readback['anonymous_https_downloads']:
            self.assertEqual(asset['http_status'], 200)
            self.assertTrue(asset['matches_uploaded'])
        iq = next(row for row in readback['anonymous_https_downloads'] if row['name'] == 'SpaceFox.iq')
        self.assertEqual(iq['sha256'], self.latest['package_sha256'])

    def test_missing_prior_receipt_refused(self):
        with self.assertRaisesRegex(BuildBlocked, 'committed latest release receipt/package'):
            self.admit('0.1.1', None)

    def test_different_prior_version_refused(self):
        # Retain the real IQ bytes so this reaches committed history comparison.
        directory = self.base / 'different-history'
        directory.mkdir()
        shutil.copyfile(self.iq, directory / self.iq.name)
        previous = dict(self.previous, version='0.0.9')
        path = directory / 'release.json'
        path.write_text(json.dumps(previous))
        with self.assertRaisesRegex(BuildBlocked, 'committed latest release receipt/package'):
            self.admit('0.1.1', path)

    def test_same_or_lower_native_version_refused(self):
        for version in ('0.1.0', '0.0.9'):
            with self.subTest(version=version):
                with self.assertRaisesRegex(BuildBlocked, 'strictly increase'):
                    self.admit(version, self.previous_path)

    def test_higher_version_passes_history_admission_only(self):
        with self.assertRaises(ExportBoundaryReached):
            self.admit('0.1.1', self.previous_path)
