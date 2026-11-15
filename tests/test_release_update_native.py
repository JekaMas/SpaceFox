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
    'build.json': '4b9de8393ae22dbb02bd13f3a093906a206d272b38c372065d266925b7b9e1ca',
    'Probe.mc.txt': '0713ca67b40d0ce7e22db9d85383591f9e4d859d0497b4b576a9df4fa9f7ead1',
    'run.log': '10be30feb2c55fabe58fffc5d6f87f6bda27bffa7e0f363315e5851ae160a2f0',
    'exit.txt': '4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_payload(name, data):
    if digest(data) != PINS[name]:
        raise ValueError('native observation changed: ' + name)


def check_sources(build, read):
    from tools.generate_native_version import render
    current_version = read(ROOT / 'watchface/source/generated/NativeVersion.mc').decode()
    if current_version != render(ROOT) or 'BUILD = "0.1.13"' not in current_version:
        raise ValueError('current NativeVersion identity differs')
    # The receipt predates DISPLAY03. Bind the live input to the new admission
    # and compare its preserved predecessor bytes to the historical receipt.
    proof = json.loads((ROOT / 'openspec/changes/spacefox-watchface/evidence/display03-active-tick-wake/integration13/proof.json').read_text())
    for name, expected in {**build['productionSources'], **build['productionResources']}.items():
        data = read(ROOT / name)
        if digest(data) != proof['nativeInputs'][name]:
            raise ValueError('native owner changed: ' + name)
        if digest(data) != expected:
            data = (EVIDENCE.parent / 'display03-active-tick-wake/integration13/historical/settings' / name).read_bytes()
        if digest(data) != expected:
            raise ValueError('historical native owner changed: ' + name)


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
        self.assertIn('incomingPath=1 deferredRestoreSameCache=1 schemaRefused=1 rendererRefused=1 actionableMenu=1 fiveLocales=1 languageRefresh=1 clearsOnSuccess=1 oldWireRetained=1', self.log)
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

    def test_open_warning_tracks_language_selection(self):
        self.assertIn('languageRefresh=1', self.log)
        self.assertIn('choice.onSelect(new WatchUi.MenuItem("Русский",null,:i1,null))', self.probe)
        self.assertIn('Test.assertEqual(item.getSubLabel(),"Проверьте URL или обновите SpaceFox")', self.probe)
        self.assertIn('Test.assertEqual(item.getSubLabel(),"Check URL or update SpaceFox")', self.probe)

class ReleaseUpdateAdmissionTest(unittest.TestCase):
    def test_language_admission_refuses_changed_warning_glyph_observation(self):
        from unittest.mock import patch
        from tools.native_language_policy import software_locales
        original = Path.read_bytes
        target = EVIDENCE / 'menu-warning-glyphs.json'
        def altered(path):
            data = original(path)
            return data + b'changed' if path.resolve() == target else data
        with patch.object(Path, 'read_bytes', altered), self.assertRaisesRegex(ValueError, 'glyph observation changed'):
            software_locales(ROOT)

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
