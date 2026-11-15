"""Mutation refusals for the source-bound current clock observation."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from tests import current_clock_reader as reader

class CurrentClockReaderTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name); self.base=self.root/reader.BASE.relative_to(reader.ROOT)
        shutil.copytree(reader.BASE,self.base)
        meta=json.loads((self.base/'binding.json').read_bytes())
        for name in list(meta['inputs'])+['tests/fixtures/current_clock_convergence/linux_runner.py','tests/fixtures/current_clock_convergence/probe.py']:
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(reader.ROOT/name,dest)
        self.root_patch=patch.object(reader,'ROOT',self.root);self.root_patch.start();self.addCleanup(self.root_patch.stop)
        self.base_patch=patch.object(reader,'BASE',self.base);self.base_patch.start();self.addCleanup(self.base_patch.stop)
        reader._cache=None;self.addCleanup(setattr,reader,'_cache',None)

    def test_source_mutation_refuses_cached_observation(self):
        reader.observe_clock('offlineWakePositive')
        source=self.root/'watchface/source/ScheduleState.mc'
        source.write_bytes(source.read_bytes()+b'\n// mutation\n')
        with self.assertRaisesRegex(ValueError,'clock input changed'): reader.observe_clock('offlineWakePositive')

    def test_raw_mutation_refuses(self):
        raw=self.base/'native.log';raw.write_bytes(raw.read_bytes()+b'mutation\n')
        with self.assertRaisesRegex(ValueError,'clock observation changed'): reader.observe_clock('uncertaintyPositive')

    def test_binding_mutation_refuses(self):
        binding=self.base/'binding.json';binding.write_bytes(binding.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'clock binding changed'): reader.observe_clock('uncertaintyPositive')

    def test_exact_packet_input_mutation_refuses(self):
        original=Path(__file__).resolve().parents[1]
        relative=Path('openspec/changes/spacefox-watchface/evidence/canonical-current-convergence/current-exact-packet-probe')
        shutil.copytree(original/relative,self.root/relative)
        meta=json.loads((self.root/relative/'binding.json').read_bytes())
        for name in list(meta['inputs'])+['tests/fixtures/current_clock_convergence/linux_runner_exact.py','tests/fixtures/current_clock_convergence/probe_exact.py']:
            dest=self.root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(original/name,dest)
        packet=self.root/'openspec/changes/spacefox-watchface/evidence/final-native-timing-settings/packets.json'
        packet.write_bytes(packet.read_bytes()+b' ')
        with self.assertRaisesRegex(ValueError,'exact probe input changed'): reader.observe_exact_packet()
