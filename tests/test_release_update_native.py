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
    'build.json': '6bd698889d1bdfcd1e4f6e6618afa313fe21d3606af483bd91957ebc55c3b3c6',
    'Probe.mc.txt': '1e21951157d63680d73eafc6cf129afb36a157fd4aa30f8c56eee642a2005ed9',
    'run.log': 'cdac9c1c8f8aaba14340f59538d3f7922706ef929f0bfea5ec3d875b055bd092',
    'exit.txt': '4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check_payload(name, data):
    if digest(data) != PINS[name]:
        raise ValueError('native observation changed: ' + name)


def check_sources(build, read):
    for name, expected in {**build['productionSources'], **build['productionResources']}.items():
        if digest(read(ROOT / name)) != expected:
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
        self.assertIn('schemaRefused=1 rendererRefused=1 actionableMenu=1 fiveLocales=1 clearsOnSuccess=1 oldWireRetained=1', self.log)
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
