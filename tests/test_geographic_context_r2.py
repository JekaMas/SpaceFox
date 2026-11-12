"""Independent R2 admission witnesses and analytic projection controls.

These tests create fully rehashed external artifacts.  Expected rights bytes
come from the retained primary-source pins, not the production validator.
"""
import copy
from decimal import Decimal
import hashlib
import math
from pathlib import Path
import tempfile
import unittest

from tools.build_geographic_context import read_artifact, write_artifact
from tools.spacefox.catalog import build_catalog, loads_json
from tools.spacefox.geographic_context import (
    build_artifact, build_view, canonical_bytes, dependencies, load_source, project_profile,
)
from tools.spacefox.global_map import GeographyError

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL_NOTICE_HASHES = {
    'LICENSE.TXT': 'dc53a4833bf9121360a5286917683f041439327353ffe0231206c6b746005b81',
    'README.TXT': '8c83b0d9e861c3cf9390ccfcc28d57dd484b192e1767524e094c988ee9f84ac7',
    'COPYING.LESSERv3': 'ea7d049c7705dc13afc202dd18e1827f3484f8212fd3fa7b82fc4a0c363432c9',
    'COPYINGv3': '3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def replace_common(view, change):
    """Rehash the complete common→proof chain after a semantic mutation."""
    view = copy.deepcopy(view)
    proof_pin = view['manifest']['source']
    proof = loads_json(view['files'][proof_pin['path']])
    common_pin = proof['common']
    common = loads_json(view['files'][common_pin['path']])
    change(common)
    for value, pin in ((common, common_pin), (proof, proof_pin)):
        view['files'].pop(pin['path'])
        raw = canonical_bytes(value)
        pin.update(path='sources/' + sha(raw) + '.json', sha256=sha(raw), decodedBytes=len(raw))
        view['files'][pin['path']] = raw
    return view


def external_artifact(view, *, previous=False, current=None):
    """Package without calling the production admission/builder being tested."""
    files = dict(view['files'])
    raw = canonical_bytes(view['manifest'])
    descriptor = 'manifests/' + sha(raw) + '.json'
    files[descriptor] = raw
    if previous:
        files.update(current['files'])
    manifest = {
        'schemaVersion': 2,
        'qualification': 'offwatch-context-preview-not-native-wire-or-pad-survey',
        'current': current['manifest']['current'] if previous else [descriptor],
        'previous': [descriptor] if previous else [],
        'currentFiles': current['manifest']['currentFiles'] if previous else sorted(files),
        'files': {p: {'sha256': sha(b), 'bytes': len(b)} for p, b in files.items()},
    }
    return {'manifest': manifest, 'files': files}


def raw_write(directory, artifact):
    for path, raw in artifact['files'].items():
        target = directory / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (directory / 'preview-artifact.json').write_bytes(canonical_bytes(artifact['manifest']))


class GeographicContextR2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT, ROOT / 'catalog/geography/context-candidate-20261112.json')
        cls.omelek = build_view(ROOT, cls.catalog, 'll2:site:107')
        cls.accepted = build_artifact([cls.omelek])

    def assert_refused_ports(self, view):
        with self.subTest(port='build'):
            with self.assertRaises(GeographyError):
                build_artifact([view])
        for previous in (False, True):
            forged = external_artifact(view, previous=previous, current=self.accepted if previous else None)
            with self.subTest(port='write', retained=previous), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                write_artifact(directory, self.accepted)
                before = (directory / 'preview-artifact.json').read_bytes()
                with self.assertRaises(GeographyError):
                    write_artifact(directory, forged)
                self.assertEqual((directory / 'preview-artifact.json').read_bytes(), before)
                self.assertEqual(read_artifact(directory)['manifest'], self.accepted['manifest'])
            with self.subTest(port='read', retained=previous), tempfile.TemporaryDirectory() as tmp:
                directory = Path(tmp)
                raw_write(directory, forged)
                with self.assertRaises(GeographyError):
                    read_artifact(directory)

    def test_original_notice_substitution(self):
        proof = loads_json(self.omelek['files'][self.omelek['manifest']['source']['path']])
        common = loads_json(self.omelek['files'][proof['common']['path']])
        for name, digest in ORIGINAL_NOTICE_HASHES.items():
            self.assertEqual(sha(common['notices'][name].encode('utf-8')), digest)
        for name in ORIGINAL_NOTICE_HASHES:
            with self.subTest(notice=name):
                self.assert_refused_ports(replace_common(
                    self.omelek, lambda c: c['notices'].__setitem__(name, 'LGPL-3.0-or-later')))

    def test_supplement_metadata_binding(self):
        # Keep both the original metadata digest and the admission keyword.
        # Outer hashes are all recomputed, so only the metadata-byte binding can
        # distinguish the real primary document from this replacement.
        self.assert_refused_ports(replace_common(
            self.omelek,
            lambda c: c['supplementNotices'][0].__setitem__(
                'originalMetadata', 'The data may be used and redistributed for free.')))

    def test_event_and_source_fact_admission(self):
        point = {'latitude': Decimal('9.047861'), 'longitude': Decimal('167.743'),
                 'sources': ['https://example.org/independent-r2-event']}
        event = build_view(ROOT, self.catalog, 'll2:site:59', event_position=point)
        self.assertEqual(event['manifest']['marker'], [335, 165])
        self.assertEqual(event['manifest']['site']['eventPosition'], point)
        build_artifact([event])
        for defect in ('event-latitude', 'event-provenance', 'event-source-type', 'source-latitude', 'position-mode', 'reference-with-event'):
            with self.subTest(defect=defect):
                bad = copy.deepcopy(event)
                site = bad['manifest']['site']
                if defect == 'event-latitude':
                    site['eventPosition']['latitude'] = 91
                    bad['manifest']['camera']['center'][0] = 91
                elif defect == 'event-provenance':
                    site['eventPosition']['sources'] = []
                elif defect == 'event-source-type':
                    site['eventPosition']['sources'] = {'https://example.org/independent-r2-event': 'wrong-type'}
                elif defect == 'source-latitude':
                    site['sourcePosition']['latitude'] = -91
                elif defect == 'position-mode':
                    site['positionMode'] = 'unreviewed-mode'
                else:
                    site['referenceContextOnly'] = True
                self.assert_refused_ports(bad)
        with self.assertRaises(GeographyError):
            build_view(ROOT, self.catalog, 'll2:site:59', event_position={**point, 'sources': []})
        with self.assertRaises(GeographyError):
            build_view(ROOT, self.catalog, 'll2:site:59', event_position={**point, 'latitude': 91})
        with self.assertRaises(GeographyError):
            build_view(ROOT, self.catalog, 'll2:site:59', event_position={**point, 'sources': {point['sources'][0]: 'wrong-type'}})

    def test_original_source_and_mobile_unknown_roundtrip(self):
        source_pin = self.catalog['source']['geography']
        source = load_source(ROOT, source_pin)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for pin in [source_pin, *dependencies(source)]:
                target = directory / pin['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / pin['path']).read_bytes())
            load_source(directory, source_pin)
            index = loads_json((directory / source_pin['path']).read_bytes())
            notice = next(p for p in index['notices'] if p['path'].endswith('/LICENSE.TXT'))
            fake = b'LGPL-3.0-or-later'
            (directory / notice['path']).write_bytes(fake)
            notice.update(sha256=sha(fake), bytes=len(fake))
            raw = canonical_bytes(index)
            (directory / source_pin['path']).write_bytes(raw)
            with self.assertRaises(GeographyError):
                load_source(directory, {**source_pin, 'sha256': sha(raw)})
        for identity, reference, center in (
            ('ll2:site:59', True, [Decimal('8.716667'), Decimal('167.733333')]),
            ('ll2:site:59', False, [0, 0]),
            ('ll2:site:101', False, [0, 0]),
        ):
            with self.subTest(identity=identity, reference=reference):
                view = build_view(ROOT, self.catalog, identity, reference_context=reference)
                self.assertEqual(view['manifest']['camera']['center'], center)
                self.assertIsNone(view['manifest']['marker'])
                self.assertIsNone(view['manifest']['site']['eventPosition'])
                if identity == 'll2:site:101':
                    self.assertIsNone(view['manifest']['site']['sourcePosition'])
                with tempfile.TemporaryDirectory() as tmp:
                    directory = Path(tmp)
                    artifact = build_artifact([view], self.accepted)
                    write_artifact(directory, artifact)
                    self.assertEqual(read_artifact(directory)['manifest'], artifact['manifest'])

    def test_repaired_profile_and_rights_retained_paths(self):
        globe = build_view(ROOT, self.catalog, 'll2:site:107', kind='globe')
        accepted_map = build_view(ROOT, self.catalog, 'll2:site:107', profile='accepted04-full')
        self.assertEqual(accepted_map['manifest']['camera']['scale'], 145)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            control = build_artifact([accepted_map], build_artifact([globe]))
            write_artifact(directory, control)
            self.assertEqual(read_artifact(directory)['manifest'], control['manifest'])
        globe['manifest']['camera'].update(profile='accepted04-full', scale=145)
        self.assert_refused_ports(globe)
        for mutate in (
            lambda c: c['supplementNotices'][0].__setitem__('license', 'public-domain'),
            lambda c: c.__setitem__('supplementNotices', []),
            lambda c: c['notices'].__setitem__('LICENSE.TXT', ' \n '),
        ):
            self.assert_refused_ports(replace_common(self.omelek, mutate))

    def test_analytic_projection_and_retained_closure_controls(self):
        # Cardinal-angle analytic oracles do not call or reproduce _rotated.
        for kind, expected_y in (('map', 165 - 145 * math.pi / 6), ('globe', 92.5)):
            actual = project_profile(30, 0, kind=kind, center=(0, 0), scale=145)
            self.assertAlmostEqual(actual[0], 335, places=10)
            self.assertAlmostEqual(actual[1], expected_y, places=10)
        date_line = project_profile(0, Decimal('-179.5'), kind='map',
                                    center=(0, Decimal('179.5')), scale=145)
        self.assertAlmostEqual(date_line[0], 335 + 145 * math.pi / 180, places=10)
        self.assertEqual(date_line[1], 165)
        self.assertIsNone(project_profile(0, 180, kind='globe', center=(0, 0), scale=145))
        self.assertAlmostEqual(project_profile(0, 90, kind='globe', center=(0, 0), scale=145)[0], 480)
        current = build_artifact([build_view(ROOT, self.catalog, 'll2:site:104', reference_context=True)], self.accepted)
        self.assertEqual(current['manifest']['previous'], self.accepted['manifest']['current'])
        self.assertLessEqual(current['artifactBytes'], 1048576)
        self.assertEqual(current['artifactBytes'], len(canonical_bytes(current['manifest'])) + sum(map(len, current['files'].values())))
        # A retained source file cannot be dropped even with an honest rebuilt
        # envelope and no orphan pin left in that envelope.
        bad = copy.deepcopy(current)
        retained = loads_json(bad['files'][bad['manifest']['previous'][0]])
        selected = retained['source']['path']
        self.assertNotIn(selected, bad['manifest']['currentFiles'])
        bad['files'].pop(selected)
        bad['manifest']['files'].pop(selected)
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            raw_write(directory, bad)
            with self.assertRaises(GeographyError):
                read_artifact(directory)


if __name__ == '__main__':
    unittest.main()
