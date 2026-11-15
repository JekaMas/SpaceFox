"""Negative controls for historical/current applicability receipt reading."""
from pathlib import Path
import unittest
from unittest.mock import patch

from tests import test_current_data_convergence as data
from tests import test_current_format_acceptance as reader_module

ROOT = data.ROOT
EVIDENCE = data.EVIDENCE


class CurrentSourceReaderTest(unittest.TestCase):
    def setUp(self):
        reader_module.CurrentFormatAcceptanceTest._historical_cache.clear()
        reader_module.CurrentFormatAcceptanceTest._route_cache.clear()
        reader_module.CurrentFormatAcceptanceTest._current_ready = False

    def test_current_owner_mutation_refuses(self):
        target = ROOT / 'watchface/source/NativeFeed.mc'
        original = Path.read_bytes
        def mutated(path):
            data = original(path)
            return data + b' ' if path == target else data
        with patch.object(Path, 'read_bytes', mutated):
            with self.assertRaisesRegex(AssertionError, 'source differs: watchface/source/NativeFeed.mc'):
                data.CurrentDataConvergenceTest.setUpClass()

    def test_historical_input_mutation_refuses(self):
        source = 'watchface/source/NativeBridgeFeed.mc'
        build = __import__('json').loads((ROOT / 'openspec/changes/spacefox-watchface/evidence/watch-refresh-cache-whole/linux-runtime/integrity-r5/build.json').read_bytes())
        expected = build['productionSources'][source]
        from tests import public_proof_inputs as snapshots
        item = snapshots.manifest()['inputs'][source+'@'+expected]
        target = ROOT / item['path']
        original = Path.read_bytes
        def mutated(path):
            raw = original(path)
            return b'changed historical source' if path == target else raw
        reader = reader_module.CurrentFormatAcceptanceTest('test_ls05_p5_s01_positive')
        with patch.object(Path, 'read_bytes', mutated):
            with self.assertRaisesRegex(AssertionError, 'historical build input unavailable or changed'):
                reader.source_matches(source, expected, source_head=build['sourceHead'])

    def test_evidence_manifest_mutation_refuses(self):
        target = EVIDENCE / 'MANIFEST.json'
        original = Path.read_bytes
        def mutated(path):
            data = original(path)
            return data + b' ' if path == target else data
        with patch.object(Path, 'read_bytes', mutated):
            with self.assertRaisesRegex(AssertionError, 'retained evidence manifest changed'):
                data.CurrentDataConvergenceTest.setUpClass()

    def test_changed_current_input_invalidates_route_cache(self):
        reader_module.CurrentFormatAcceptanceTest.current_route('moreWidePolicy')
        target = ROOT / 'watchface/source/NativeFeed.mc'
        data.CurrentDataConvergenceTest.input_stamps[str(target)] = (0, 0, 0)
        original = Path.read_bytes
        def mutated(path):
            value = original(path)
            return value + b' ' if path == target else value
        with patch.object(Path, 'read_bytes', mutated):
            with self.assertRaisesRegex(AssertionError, 'source differs: watchface/source/NativeFeed.mc'):
                reader_module.CurrentFormatAcceptanceTest.current_route('moreWidePolicy')


    def test_changed_current_ui_owner_refuses_cached_route(self):
        reader_module.CurrentFormatAcceptanceTest._route_cache.add('current-ui')
        target = ROOT / 'watchface/source/SceneRenderer.mc'
        original = Path.read_bytes
        def mutated(path):
            value = original(path)
            return value + b'changed' if path == target else value
        with patch.object(Path, 'read_bytes', mutated):
            with self.assertRaisesRegex(AssertionError, 'current integration source changed'):
                reader_module.CurrentFormatAcceptanceTest().current_ui()
