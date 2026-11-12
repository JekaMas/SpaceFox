"""Independent R3 external-envelope admission and literal repair controls."""
import copy
from decimal import Decimal
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.build_geographic_context import read_artifact, write_artifact
from tools.spacefox.catalog import build_catalog, loads_json
from tools.spacefox.geographic_context import (
    build_artifact, build_view, canonical_bytes, project_profile, validate_artifact,
)
from tools.spacefox.global_map import GeographyError

ROOT = Path(__file__).resolve().parents[1]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def external(view, *, current=None):
    """Construct every envelope/pin without the production artifact builder."""
    raw = canonical_bytes(view['manifest'])
    descriptor = 'manifests/' + sha(raw) + '.json'
    files = {**view['files'], descriptor: raw}
    active = [descriptor]
    active_files = sorted(files)
    previous = []
    if current is not None:
        files.update(current['files'])
        active = current['manifest']['current']
        active_files = current['manifest']['currentFiles']
        previous = [descriptor]
    return {'manifest': {
        'schemaVersion': 2,
        'qualification': 'offwatch-context-preview-not-native-wire-or-pad-survey',
        'current': active, 'previous': previous, 'currentFiles': active_files,
        'files': {p: {'sha256': sha(b), 'bytes': len(b)} for p, b in files.items()},
    }, 'files': files}


def raw_write(directory, artifact):
    for path, raw in artifact['files'].items():
        target = directory / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (directory / 'preview-artifact.json').write_bytes(canonical_bytes(artifact['manifest']))


def alter_common(view, change):
    result = copy.deepcopy(view)
    proof_pin = result['manifest']['source']
    proof = loads_json(result['files'][proof_pin['path']])
    common_pin = proof['common']
    common = loads_json(result['files'][common_pin['path']])
    change(common)
    for value, pin in ((common, common_pin), (proof, proof_pin)):
        result['files'].pop(pin['path'])
        raw = canonical_bytes(value)
        pin.update(path='sources/' + sha(raw) + '.json', sha256=sha(raw), decodedBytes=len(raw))
        result['files'][pin['path']] = raw
    return result


class GeographicContextR3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT, ROOT / 'catalog/geography/context-candidate-20261112.json')
        cls.omelek = build_view(ROOT, cls.catalog, 'll2:site:107')
        cls.accepted = build_artifact([cls.omelek])

    def assert_refused_envelope(self, artifact):
        with self.subTest(port='validate'), self.assertRaises(GeographyError):
            validate_artifact(artifact)
        with self.subTest(port='retain'), self.assertRaises(GeographyError):
            build_artifact([self.omelek], artifact)
        with self.subTest(port='write'), tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            write_artifact(directory, self.accepted)
            before = (directory / 'preview-artifact.json').read_bytes()
            with self.assertRaises(GeographyError):
                write_artifact(directory, artifact)
            self.assertEqual((directory / 'preview-artifact.json').read_bytes(), before)
            self.assertEqual(read_artifact(directory)['manifest'], self.accepted['manifest'])
        with self.subTest(port='read'), tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            raw_write(directory, artifact)
            with self.assertRaises(GeographyError):
                read_artifact(directory)

    def test_external_selection_envelope_admission(self):
        # Every byte, digest, file membership and descriptor remains valid. Only
        # the root selection representation changes, separating selection
        # admission from corruption or missing-source rejection.
        for defect in ('empty-current', 'duplicate-current', 'five-current',
                       'duplicate-previous', 'five-previous', 'current-object',
                       'previous-object', 'current-files-object', 'fractional-version'):
            with self.subTest(defect=defect):
                bad = external(self.omelek)
                manifest = bad['manifest']
                paths = manifest['current']
                if defect == 'empty-current':
                    manifest.update(current=[], previous=paths, currentFiles=[])
                elif defect == 'duplicate-current':
                    manifest['current'] = paths * 2
                elif defect == 'five-current':
                    manifest['current'] = paths * 5
                elif defect == 'duplicate-previous':
                    manifest['previous'] = paths * 2
                elif defect == 'five-previous':
                    manifest['previous'] = paths * 5
                elif defect == 'current-object':
                    manifest['current'] = dict.fromkeys(paths)
                elif defect == 'previous-object':
                    manifest['previous'] = dict.fromkeys(paths)
                elif defect == 'current-files-object':
                    manifest['currentFiles'] = dict.fromkeys(manifest['currentFiles'])
                else:
                    manifest['schemaVersion'] = Decimal('2.0')
                self.assert_refused_envelope(bad)

    def test_repaired_rights_position_and_profile_literals(self):
        changed = [
            alter_common(self.omelek, lambda c: c['notices'].__setitem__(
                'README.TXT', c['notices']['README.TXT'] + '\n')),
            alter_common(self.omelek, lambda c: c['supplementNotices'][0].__setitem__(
                'originalMetadataEncoding', 'utf-8')),
        ]
        event = build_view(ROOT, self.catalog, 'll2:site:59', event_position={
            'latitude': Decimal('9.047861'), 'longitude': Decimal('167.743'),
            'sources': ['https://example.org/r3-literal-event'],
        })
        for key, value in (('longitude', -181), ('latitude', True)):
            bad = copy.deepcopy(event)
            bad['manifest']['site']['eventPosition'][key] = value
            bad['manifest']['camera']['center'][key == 'longitude'] = value
            changed.append(bad)
        bad = copy.deepcopy(self.omelek)
        bad['manifest']['site']['sourcePosition']['units'] = 'radians'
        changed.append(bad)
        bad = copy.deepcopy(self.omelek)
        bad['manifest']['camera'].update(kind='globe', profile='accepted04-full', scale=145)
        changed.append(bad)
        for number, bad in enumerate(changed):
            with self.subTest(literal=number), self.assertRaises(GeographyError):
                build_artifact([bad])
            for retained in (False, True):
                with self.subTest(literal=number, retained=retained):
                    self.assert_refused_envelope(external(bad, current=self.accepted if retained else None))

    def test_five_distinct_descriptors_exceed_selection_count(self):
        views = [self.omelek, build_view(ROOT, self.catalog, 'll2:site:107', kind='globe')]
        views.extend(build_view(ROOT, self.catalog, 'll2:site:59', kind=kind) for kind in ('map', 'globe'))
        views.append(build_view(ROOT, self.catalog, 'll2:site:101'))
        files = {}
        descriptors = []
        for view in views:
            packed = external(view)
            files.update(packed['files'])
            descriptors.extend(packed['manifest']['current'])
        self.assertEqual(len(set(descriptors)), 5)
        for retained in (False, True):
            bad = external(self.omelek)
            bad['files'] = files
            bad['manifest']['files'] = {p: {'sha256': sha(b), 'bytes': len(b)} for p, b in files.items()}
            if retained:
                bad['manifest']['previous'] = descriptors
            else:
                bad['manifest'].update(current=descriptors, currentFiles=sorted(files))
            # The count is the only violated resource boundary: honest file
            # closure and byte accounting are below the separate 1MiB ceiling.
            self.assertLessEqual(len(canonical_bytes(bad['manifest'])) + sum(map(len, files.values())), 1048576)
            with self.subTest(retained=retained):
                self.assert_refused_envelope(bad)

    def test_existing_root_membership_and_shape_rejections(self):
        for field in ('current', 'previous', 'currentFiles', 'schemaVersion', 'qualification'):
            bad = external(self.omelek)
            bad['manifest'].pop(field)
            with self.subTest(missing=field):
                self.assert_refused_envelope(bad)
        for defect in ('current-item', 'previous-item', 'file-item', 'wrong-root-kind',
                       'duplicate-current-file', 'missing-current-file'):
            bad = external(self.omelek)
            manifest = bad['manifest']
            if defect == 'current-item':
                manifest['current'] = [None]
            elif defect == 'previous-item':
                manifest['previous'] = [None]
            elif defect == 'file-item':
                manifest['currentFiles'][0] = None
            elif defect == 'wrong-root-kind':
                manifest['current'] = [self.omelek['manifest']['source']['path']]
            elif defect == 'duplicate-current-file':
                manifest['currentFiles'].append(manifest['currentFiles'][0])
            else:
                manifest['currentFiles'].pop()
            with self.subTest(defect=defect):
                self.assert_refused_envelope(bad)

    def test_selection_rotation_and_supported_limits(self):
        mobile = build_view(ROOT, self.catalog, 'll2:site:59')
        unknown = build_view(ROOT, self.catalog, 'll2:site:101')
        globe = build_view(ROOT, self.catalog, 'll2:site:107', kind='globe')
        views = [self.omelek, mobile, unknown, globe]
        previous = None
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            for count in range(1, 5):
                current = build_artifact(views[:count], previous)
                self.assertEqual(len(current['manifest']['current']), count)
                self.assertEqual(current['manifest']['previous'], previous['manifest']['current'] if previous else [])
                self.assertLessEqual(current['artifactBytes'], 1048576)
                self.assertEqual(current['artifactBytes'], len(canonical_bytes(current['manifest'])) + sum(map(len, current['files'].values())))
                write_artifact(directory, current)
                self.assertEqual(read_artifact(directory)['manifest'], current['manifest'])
                previous = current
            # A prior selection of four remains admitted when current shrinks;
            # current/prior overlap is valid and must not be deduplicated away.
            current = build_artifact([unknown], previous)
            self.assertEqual(len(current['manifest']['previous']), 4)
            write_artifact(directory, current)
            self.assertEqual(read_artifact(directory)['manifest'], current['manifest'])
        self.assertEqual(mobile['manifest']['camera']['center'], [0, 0])
        self.assertIsNone(mobile['manifest']['marker'])
        self.assertIsNone(unknown['manifest']['site']['sourcePosition'])
        self.assertIsNone(unknown['manifest']['marker'])
        # Polar cardinal and exact-center oracles use known spherical geometry,
        # independent of the producer's rotation and clipping implementation.
        self.assertEqual(project_profile(Decimal('9.047861'), Decimal('167.743'),
                                        kind='map', center=(Decimal('9.047861'), Decimal('167.743')), scale=145), (335, 165))
        pole = project_profile(0, 0, kind='globe', center=(90, 0), scale=145)
        self.assertAlmostEqual(pole[0], 335, places=10)
        self.assertAlmostEqual(pole[1], 310, places=10)
        with self.assertRaises(GeographyError):
            build_artifact([])
        with self.assertRaises(GeographyError):
            build_artifact([self.omelek, self.omelek])


if __name__ == '__main__':
    unittest.main()
