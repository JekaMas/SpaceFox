"""Current catalog additions against the explicitly pinned off-watch source.

This supplements, rather than changes, the original 213 numeric reference cohort.
It is not a survey, an operating-site inventory, or a native raster observation.
"""
from pathlib import Path
import unittest

from tools.spacefox.catalog import build_catalog, canonical_bytes as exact_bytes
from tools.spacefox.geographic_context import build_artifact, build_view, canonical_bytes

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / 'catalog/geography/context-candidate-20261112.json'


class CurrentGeographyAdditionsTest(unittest.TestCase):
    def test_current_extra_rows_against_pinned_source(self):
        current = build_catalog(ROOT)
        cohort = build_catalog(ROOT, CANDIDATE)
        sites = current['dictionaries']['sites']
        extra = set(sites) - set(cohort['dictionaries']['sites'])
        numeric = {'ll2:site:125', 'll2:site:203', 'll2:site:77', 'll2:site:81'}
        unknown = {'ll2:site:237', 'spacefox:site:spaceport-nova-scotia'}
        self.assertEqual(extra, numeric | unknown)
        for identity in sorted(extra):
            with self.subTest(site=identity):
                site = sites[identity]
                view = build_view(ROOT, current, identity, source_pin=cohort['source']['geography'])
                manifest = view['manifest']
                self.assertEqual(exact_bytes(manifest['site']['sourcePosition']), exact_bytes(site['position']))
                self.assertIsNone(manifest['site']['eventPosition'])
                self.assertEqual(manifest['marker'], [335, 165] if identity in numeric else None)
                self.assertEqual(site['position'] is None, identity in unknown)
                self.assertTrue(view['segments'])
                self.assertTrue(all(0 <= p[0] <= 390 and 0 <= p[1] <= 390 for segment in view['segments'] for p in segment))
                self.assertLessEqual(len(canonical_bytes(manifest)), 8192)
                artifact = build_artifact([view])
                self.assertLessEqual(artifact['artifactBytes'], 1048576)
                self.assertEqual(artifact['artifactBytes'], len(canonical_bytes(artifact['manifest'])) + sum(map(len, artifact['files'].values())))
