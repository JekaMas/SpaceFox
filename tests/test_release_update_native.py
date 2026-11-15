"""Source-bound reading of the actual SDK schema/renderer/host control.

The runtime observations live in the retained SDK log and probe, not in this
reader. This does not re-run the simulator or prove physical/Store behavior.
"""
import hashlib
import json
from pathlib import Path
import unittest

from tools.run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'openspec/changes/spacefox-watchface/evidence/release-update-native'
PINS = {
    'build.json': '24b32d8bbf0b03095da2e80eaacc2cc12d5d8922787297c3a8fe9df81027b2c0',
    'Probe.mc.txt': '01a45b14fdfdee8d26436cac970c4f87e958caab8266a1c13915718a8490e2ea',
    'run.log': 'd3ebbb9f466db3961d5aa39c839d007cf5d426dc4b9208995f39019c3f0d4afb',
    'exit.txt': '4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_payload(name, data):
    if digest(data) != PINS[name]:
        raise ValueError('native observation changed: ' + name)


def check_sources(build, read):
    from tools.generate_native_version import render
    current_version = (ROOT / 'watchface/source/generated/NativeVersion.mc').read_text()
    if current_version != render(ROOT) or 'BUILD = "0.1.12"' not in current_version:
        raise ValueError('current NativeVersion identity differs')
    for name, expected in {**build['productionSources'], **build['productionResources']}.items():
        data = read(ROOT / name)
        if digest(data) != expected:
            raise ValueError('native owner changed: ' + name)


class ReleaseUpdateNativeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = {name: (EVIDENCE / name).read_bytes() for name in PINS}
        for name, data in raw.items():
            check_payload(name, data)
        cls.build = json.loads(raw['build.json'])
        if cls.build['exitCode'] != 0 or cls.build['probeSha256'] != digest(raw['Probe.mc.txt']):
            raise AssertionError('SDK build/probe binding incomplete')
        check_sources(cls.build, Path.read_bytes)
        cls.probe = raw['Probe.mc.txt'].decode()
        cls.log = raw['run.log'].decode()
        result = parse_output(cls.log, int(raw['exit.txt']), ('releaseCurrentHostSchema',))
        if result['status'] != 'passed' or result['observed_tests'].get('releaseCurrentHostSchema') != 'PASS':
            raise AssertionError('SDK named result incomplete')

    def test_supported_current_cache_reopens(self):
        self.assertIn('Test.assert(reopened.load(now)!=null);Test.assertEqual(reopened.packet.wireHash,wire);', self.probe)
        self.assertIn('oldWireRetained=1', self.log)

    def test_unsupported_schema_refused_without_replacement(self):
        self.assertIn('incomingPath=1 deferredRestoreSameCache=1 schemaRefused=1 rendererRefused=1 actionableMenu=1 fiveLocales=1 clearsOnSuccess=1 oldWireRetained=1', self.log)
        self.assertIn('Check URL or update SpaceFox', self.probe)
        self.assertIn('"schemaVersion\\":4', self.probe)
        with self.assertRaisesRegex(ValueError, 'native observation changed'):
            check_payload('run.log', (EVIDENCE / 'run.log').read_bytes() + b'changed')

    def test_feed_hosts_keep_independent_age_and_reschedule(self):
        self.assertIn('separateHostAge=1 separateReschedule=1', self.log)
        self.assertIn('Test.assert(b.load(now)==null)', self.probe)
        self.assertIn('Test.assert(!b.packet.rescheduled);Test.assert(b.packet.validation==1794551192l)', self.probe)

    def test_host_publisher_floor_and_owner_mutation_refusal(self):
        self.assertIn('hostFloor=1', self.log)
        self.assertIn('Test.assert(!original.accept(', self.probe)
        target = ROOT / 'watchface/source/NativeCache.mc'
        def altered(path):
            data = path.read_bytes()
            return data + b'changed' if path == target else data
        with self.assertRaisesRegex(ValueError, 'native owner changed'):
            check_sources(self.build, altered)

    def test_unsupported_renderer_refused(self):
        self.assertIn('rendererRefused=1', self.log)
        self.assertIn('SFR-unsupported', self.probe)
        with self.assertRaisesRegex(ValueError, 'native observation changed'):
            check_payload('Probe.mc.txt', (EVIDENCE / 'Probe.mc.txt').read_bytes() + b'changed')

class ReleaseUpdateAdmissionTest(unittest.TestCase):
    def test_language_admission_refuses_changed_menu_owner(self):
        from unittest.mock import patch
        from tools.native_language_policy import software_locales
        original = Path.read_bytes
        target = ROOT / 'watchface/source/SettingsMenu.mc'
        def altered(path):
            data = original(path)
            return data + b'changed' if path.resolve() == target else data
        with patch.object(Path, 'read_bytes', altered), self.assertRaisesRegex(ValueError, 'rejection menu current owner changed'):
            software_locales(ROOT)

    def test_language_admission_refuses_changed_sdk_observation(self):
        from unittest.mock import patch
        from tools.native_language_policy import software_locales
        original = Path.read_bytes
        target = EVIDENCE / 'run.log'
        def altered(path):
            data = original(path)
            return data + b'changed' if path.resolve() == target else data
        with patch.object(Path, 'read_bytes', altered), self.assertRaisesRegex(ValueError, 'rejection menu observation changed'):
            software_locales(ROOT)
