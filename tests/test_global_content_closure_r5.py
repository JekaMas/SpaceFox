"""Actual producer/delivered root contract, with independently readdressed bytes."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from tools.spacefox.catalog import build_catalog, validate_catalog, CatalogError
from tools.spacefox.graphics import build_pack, _validate_pack, VisualError
from tools.spacefox.global_map import build_bundle, write_bundle, GeographyError

ROOT = Path(__file__).resolve().parents[1]
ROOTS = ['ll2:configuration:175', 'll2:country:76', 'll2:configuration:52',
         'll2:configuration:164', 'll2:organization:121', 'll2:organization:151',
         'll2:configuration:40', 'spacefox:configuration:s310', 'll2:site:65']


def encode(value):
    # These selected fixtures contain only ordinary JSON numbers. This serializer
    # does not use production canonical_bytes or an admission/checksum helper.
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def addressed(bundle, change):
    candidate = copy.deepcopy(bundle)
    old = candidate['manifest']['current']['visual']
    record = json.loads(candidate['files'].pop(old))
    change(record)
    raw = encode(record)
    digest = hashlib.sha256(raw).hexdigest()
    new = 'manifests/' + digest + '.json'
    candidate['files'][new] = raw
    envelope = candidate['manifest']
    envelope['current']['visual'] = new
    envelope['currentFiles'] = sorted(new if p == old else p for p in envelope['currentFiles'])
    envelope['files'].pop(old)
    envelope['files'][new] = {'sha256': digest, 'bytes': len(raw)}
    candidate['artifactBytes'] = len(encode(envelope)) + sum(map(len, candidate['files'].values()))
    return candidate


def raw_store(directory, bundle):
    # Deliberately place self-consistent bytes on disk to test retained admission
    # even when the current writer correctly refuses this candidate.
    directory = Path(directory)
    for name, raw in bundle['files'].items():
        target = directory / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    (directory / 'manifest.json').write_bytes(encode(bundle['manifest']))


def reachable(record):
    # An independent graph oracle. Exact reachability is the existing builder
    # contract; its answer is not obtained from dependency_closure/validators.
    selected = record['selection']
    rows = {identity: row for table in selected['dictionaries'].values()
            for identity, row in table.items()}
    rows.update({identity: group['catalogRecord'] for identity, group in record['assets'].items()})
    seen, todo = set(), list(selected['roots'])
    while todo:
        identity = todo.pop()
        if identity in seen:
            continue
        seen.add(identity)
        for value in rows[identity]['references'].values():
            todo.extend(value if isinstance(value, list) else [] if value is None else [value])
    return seen, set(rows)


class GlobalContentClosureR5Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packs = {}
        for name, source in [('current', None), ('frozen', ROOT / 'tests/fixtures/catalog/global-before-content-source.json')]:
            catalog = build_catalog(ROOT, source)
            cls.packs[name] = build_pack(ROOT, catalog, roots=ROOTS)

    def test_readdressed_root_and_exact_closure_negative(self):
        for source, pack in self.packs.items():
            record = pack['manifest']
            # Seventeen existing IDs includes all original roots: every supplied
            # row is still reachable, so this isolates the root-count boundary.
            all_ids = sorted(reachable(record)[1])
            seventeen = list(ROOTS)
            seventeen.extend(x for x in all_ids if x not in seventeen)
            seventeen = seventeen[:17]
            self.assertEqual(len(seventeen), 17)
            cases = {
                'unreachable-country-and-mark': [x for x in ROOTS if x != 'll2:country:76'],
                'unreachable-metadata-from-asset-root': ['spacefox:asset:content-r1-vehicle-minotaur-i']
                if source == 'current' else ['spacefox:asset:generic'],
                'seventeen-roots-with-exact-closure': seventeen,
                'duplicate-root': ROOTS + [ROOTS[0]],
                'unknown-root': ROOTS + ['ll2:configuration:999999999'],
                'scalar-roots': ROOTS[0],
                'empty-roots': [],
            }
            for label, roots in cases.items():
                candidate_pack = copy.deepcopy(pack)
                candidate_pack['manifest']['selection']['roots'] = roots
                with self.subTest(source=source, case=label, port='producer'):
                    # The producer API already enforces each declared boundary.
                    if label != 'duplicate-root':
                        with self.assertRaises((VisualError, ValueError, TypeError)):
                            _validate_pack(candidate_pack)
                bad = addressed(build_bundle(pack, []),
                                lambda value: value['selection'].update(roots=roots))
                if label == 'seventeen-roots-with-exact-closure':
                    self.assertEqual(*reachable(candidate_pack['manifest']))
                elif label.startswith('unreachable-'):
                    self.assertNotEqual(*reachable(candidate_pack['manifest']))
                with tempfile.TemporaryDirectory() as tmp:
                    output = Path(tmp)
                    good = build_bundle(pack, [])
                    write_bundle(output, good)
                    before = {p.relative_to(output).as_posix(): p.read_bytes()
                              for p in output.rglob('*') if p.is_file()}
                    with self.subTest(source=source, case=label, port='current'):
                        with self.assertRaises(GeographyError):
                            write_bundle(output, bad)
                        after = {p.relative_to(output).as_posix(): p.read_bytes()
                                 for p in output.rglob('*') if p.is_file()}
                        self.assertEqual(after, before)
                    raw_store(output, bad)
                    stored = (output / 'manifest.json').read_bytes()
                    with self.subTest(source=source, case=label, port='retained'):
                        with self.assertRaises(GeographyError):
                            build_bundle(pack, [], previous_directory=output)
                        self.assertEqual((output / 'manifest.json').read_bytes(), stored)

    def test_readdressed_envelope_and_visible_row_contract_negative(self):
        def change(label, record):
            d = record['selection']['dictionaries']
            asset = sorted(record['assets'])[0]
            if label == 'missing-catalog-pin':
                record.pop('catalogSha256')
            elif label == 'invalid-catalog-pin':
                record['catalogSha256'] = True
            elif label == 'missing-selection':
                record.pop('selection')
            elif label == 'extra-envelope-field':
                record['arbitrary'] = 'not a builder field'
            elif label in ('nontext-version', 'blank-version'):
                value = False if label == 'nontext-version' else '  '
                record['catalogVersion'] = value
                record['selection']['catalogVersion'] = value
            elif label == 'reference-provenance':
                d['organizations']['ll2:organization:121']['provenance'] = [{'source': 'curation', 'recordId': 'imagined'}]
            elif label == 'reference-source-id-type':
                d['organizations']['ll2:organization:121']['provenance'][0]['recordId'] = '121'
            elif label == 'creation-provenance':
                d['configurations']['spacefox:configuration:s310']['provenance'] = []
            elif label == 'missing-creation-evidence':
                d['configurations']['spacefox:configuration:s310'].pop('creationCuration')
            elif label == 'asset-provenance':
                record['assets'][asset]['catalogRecord']['provenance'] = []
            elif label == 'asset-qualification':
                record['assets'][asset]['catalogRecord']['qualification'] = 'device-qualified'
            elif label == 'organization-role-type':
                row = d['organizations']['ll2:organization:121']
                row['roles'] = row['facts']['referenceRoles'] = True
            elif label == 'site-position':
                d['sites']['ll2:site:65']['position'] = None
            elif label == 'site-event-position':
                d['sites']['ll2:site:65']['eventPosition'] = {'latitude': 0, 'longitude': 0}

        labels = ('missing-catalog-pin', 'invalid-catalog-pin', 'missing-selection',
                  'extra-envelope-field', 'nontext-version', 'blank-version',
                  'reference-provenance', 'reference-source-id-type', 'creation-provenance',
                  'missing-creation-evidence', 'asset-provenance', 'asset-qualification',
                  'organization-role-type', 'site-position', 'site-event-position')
        for source, pack in self.packs.items():
            good = build_bundle(pack, [])
            for label in labels:
                candidate_pack = copy.deepcopy(pack)
                change(label, candidate_pack['manifest'])
                with self.subTest(source=source, case=label, port='producer'):
                    with self.assertRaises(VisualError):
                        _validate_pack(candidate_pack)
                if label in labels[6:]:
                    candidate_catalog = copy.deepcopy(pack['catalog'])
                    for table, rows in candidate_pack['manifest']['selection']['dictionaries'].items():
                        candidate_catalog['dictionaries'][table].update(rows)
                    for identity, group in candidate_pack['manifest']['assets'].items():
                        candidate_catalog['dictionaries']['assets'][identity] = group['catalogRecord']
                    with self.subTest(source=source, case=label, port='full-catalog'):
                        with self.assertRaises(CatalogError):
                            validate_catalog(candidate_catalog)
                bad = addressed(good, lambda record: change(label, record))
                with tempfile.TemporaryDirectory() as tmp:
                    output = Path(tmp)
                    write_bundle(output, good)
                    before = {p.relative_to(output).as_posix(): p.read_bytes()
                              for p in output.rglob('*') if p.is_file()}
                    with self.subTest(source=source, case=label, port='current'):
                        with self.assertRaises(GeographyError):
                            write_bundle(output, bad)
                        self.assertEqual({p.relative_to(output).as_posix(): p.read_bytes()
                                          for p in output.rglob('*') if p.is_file()}, before)
                    raw_store(output, bad)
                    stored = (output / 'manifest.json').read_bytes()
                    with self.subTest(source=source, case=label, port='retained'):
                        with self.assertRaises(GeographyError):
                            build_bundle(pack, [], previous_directory=output)
                        self.assertEqual((output / 'manifest.json').read_bytes(), stored)

    def test_current_frozen_asset_roots_and_shared_dependencies_positive(self):
        for source, pack in self.packs.items():
            bundle = build_bundle(pack, [])
            self.assertEqual(addressed(bundle, lambda value: None), bundle)
            self.assertEqual(*reachable(pack['manifest']))
            asset = sorted(pack['manifest']['assets'])[0]
            roots = [*ROOTS, asset]
            all_ids = sorted(reachable(pack['manifest'])[1])
            roots.extend(x for x in all_ids if x not in roots)
            roots = roots[:16]
            # Every dependency may also be an explicit root; valid overlap does
            # not duplicate rows/assets or become an "unreferenced" rejection.
            overlap = build_pack(ROOT, pack['catalog'], roots=roots)
            self.assertEqual(*reachable(overlap['manifest']))
            self.assertEqual(overlap['manifest']['selection']['dictionaries'],
                             pack['manifest']['selection']['dictionaries'])
            self.assertEqual(overlap['objects'], pack['objects'])
            standalone = build_pack(ROOT, pack['catalog'], roots=[asset])
            self.assertEqual(*reachable(standalone['manifest']))
            with self.subTest(source=source), tempfile.TemporaryDirectory() as tmp:
                first = build_bundle(overlap, [])
                write_bundle(tmp, first)
                second = build_bundle(standalone, [], previous_directory=tmp)
                receipt = write_bundle(tmp, second)
                self.assertTrue(receipt['retainedSelection'])
                self.assertLessEqual(receipt['artifactBytes'], 1048576)
                self.assertLessEqual(receipt['files'], 256)
                self.assertEqual(second['manifest']['previous'], first['manifest']['current'])

    def test_readdressed_asset_envelope_and_standalone_role_negative(self):
        for source, original in self.packs.items():
            for label in ('extra-asset-field', 'boolean-bound', 'standalone-asset-role',
                          'decimal-canvas', 'decimal-bound', 'decimal-units'):
                asset = sorted(original['manifest']['assets'])[0]
                pack = (build_pack(ROOT, original['catalog'], roots=[asset])
                        if label == 'standalone-asset-role' else original)
                def change(record):
                    group = record['assets'][asset]
                    if label == 'extra-asset-field':
                        group['arbitrary'] = 'not a builder asset field'
                    elif label == 'boolean-bound':
                        group['bounds'][0] = False
                    elif label == 'decimal-canvas':
                        group['canvas'][0] = float(group['canvas'][0])
                    elif label == 'decimal-bound':
                        group['bounds'][0] = 0.0
                    elif label == 'decimal-units':
                        group['units'] = float(group['units'])
                    else:
                        group['catalogRecord']['seedCollection'] = 'untyped-role'
                candidate_pack = copy.deepcopy(pack)
                change(candidate_pack['manifest'])
                with self.subTest(source=source, case=label, port='producer'):
                    with self.assertRaises(VisualError):
                        _validate_pack(candidate_pack)
                good = build_bundle(pack, [])
                self.assertEqual(addressed(good, lambda value: None), good)
                bad = addressed(good, change)
                with tempfile.TemporaryDirectory() as tmp:
                    write_bundle(tmp, good)
                    before = (Path(tmp) / 'manifest.json').read_bytes()
                    with self.subTest(source=source, case=label, port='current'):
                        with self.assertRaises(GeographyError):
                            write_bundle(tmp, bad)
                        self.assertEqual((Path(tmp) / 'manifest.json').read_bytes(), before)
                    raw_store(tmp, bad)
                    before = (Path(tmp) / 'manifest.json').read_bytes()
                    with self.subTest(source=source, case=label, port='retained'):
                        with self.assertRaises(GeographyError):
                            build_bundle(pack, [], previous_directory=tmp)
                        self.assertEqual((Path(tmp) / 'manifest.json').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
