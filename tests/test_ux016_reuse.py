"""Validate UX01 historical source snapshots within their original receipt scope.

These archived observations do not prove today's changed renderer or lifecycle;
current-source behavior requires fresh executable/native evidence.
"""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / 'openspec/changes/spacefox-watchface/evidence/ux01-016'


class RetainedNativeProof(unittest.TestCase):
    def assert_snapshot(self, snapshot, build, source):
        data = (E / snapshot).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), build['productionSources'][source])

    def test_aod_paint_and_cadence_inputs(self):
        old = json.loads((E / 'lifecycle-build.json').read_text())
        new = json.loads((E / 'settings-build.json').read_text())
        for name in ('watchface/source/LocalePresentation.mc', 'watchface/source/WatchClock.mc', 'watchface/source/Fitness.mc'):
            self.assertEqual(old['productionSources'][name], new['productionSources'][name], name)
        for name in ('watchface/resources/fonts/Aod40.fnt', 'watchface/resources/fonts/Aod40.png'):
            self.assertEqual(old['productionResources'][name], new['productionResources'][name], name)
        self.assert_snapshot('lifecycle-renderer.mc.txt', old, 'watchface/source/SceneRenderer.mc')
        self.assert_snapshot('lifecycle-view.mc.txt', old, 'watchface/source/SpaceFoxView.mc')

    def test_network_restore_historical_source(self):
        old = json.loads((E / 'network-final-build.json').read_text())
        self.assert_snapshot('network-view.mc.txt', old, 'watchface/source/SpaceFoxView.mc')
