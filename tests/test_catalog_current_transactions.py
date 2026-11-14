"""Current catalog CLI transactions on captured data, local files only."""
from copy import deepcopy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_global_catalog import temporary_catalog
from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json
from tools.spacefox.global_map import project
from tools.spacefox.graphics import build_pack, write_pack, VisualError

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'spacefox:configuration:exos-blk3'
SITE = 'll2:site:29'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def snapshot(root):
    return {str(p.relative_to(root)): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def candidate(root, defect=None):
    # Existing researched identity, attribution and source date; color is a
    # technical test mutation, not a new factual artwork claim.
    c = loads_json((ROOT / 'assets/global/curation-20261113-blk3-r1.json').read_bytes())
    c['id'] = 'technical-current-replacement'
    c['reason'] = 'Technical color mutation of retained real source, not a factual update.'
    fact = c['assets'][0]['facts']
    fact['id'] = 'technical-current-blk3-replacement'
    old = root / 'assets/global' / fact['file']
    raw = old.read_bytes()
    # Change one real source fill; geometry and all source dates remain unchanged.
    new = raw.replace(b'fill="#e2e9ec"', b'fill="#123456"', 1)
    assert new != raw
    path = root / 'assets/global/technical-current-blk3.svg'
    path.write_bytes(new)
    fact['file'] = path.relative_to(root / 'assets/global').as_posix()
    fact['sourceSha256'] = digest(new)
    c['updates'][0]['changes']['currentPackAssetId'] = fact['id']
    if defect == 'wrong-model':
        fact['coverage']['configurationIds'] = ['ll2:configuration:164']
    elif defect == 'rights':
        fact['license'] = 'unknown'
    elif defect == 'source':
        fact['sources'] = []
    elif defect == 'geometry':
        new = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><image href="https://example.org/a.png"/></svg>'
        path.write_bytes(new); fact['sourceSha256'] = digest(new)
    if defect:
        # A valid first update must not commit when a later asset is invalid.
        c['updates'].insert(0, {'identity': SITE, 'sources': ['https://ll.thespacedevs.com/2.3.0/pads/29/?format=json'],
                                'changes': {'latitude': Decimal('28.123400')}})
    f = root / 'assets/global/technical-current-replacement.json'
    f.write_bytes(canonical_bytes(c))
    return f, old, path


def cli(root, path, version, output):
    return subprocess.run([sys.executable, '-B', str(ROOT / 'tools/catalog.py'), '--repo', str(root),
        '--amend', str(path), '--catalog-version', version, '--output', str(output)],
        capture_output=True, text=True, timeout=180)


class CurrentCatalogTransactions(unittest.TestCase):
    def test_replace_reopen_select_and_preserve(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp); before = build_catalog(root)
            self.assertEqual(before['catalogVersion'], '2026-11-14.global.40.best-effort-r1')
            original = before['dictionaries']['configurations'][MODEL]
            old_pack = build_pack(root, before, roots=[MODEL]); store = root / 'selected'
            write_pack(store, old_pack); old_objects = snapshot(store / 'objects')
            recipe_bytes = (root / 'catalog/source.json').read_bytes()
            inputs = {p: (root / p).read_bytes() for p in before['inputDigests']}
            path, old_art, new_art = candidate(root)
            result = cli(root, path, 'technical.blk3.v2', root / 'build/catalog.json')
            self.assertEqual(result.returncode, 0, result.stderr)
            after = build_catalog(root); row = after['dictionaries']['configurations'][MODEL]
            self.assertEqual(row.get('originalFacts', row['facts']), original.get('originalFacts', original['facts']))
            self.assertEqual(row['references']['visual'], 'spacefox:asset:technical-current-blk3-replacement')
            fact = after['dictionaries']['assets'][row['references']['visual']]['facts']
            self.assertEqual(fact['geometryReference']['reviewedAt'], '2026-11-12')
            self.assertEqual(fact['geometryReference']['representativeDate'], '2026-07')
            self.assertEqual(fact['coverage']['configurationIds'], [MODEL])
            self.assertEqual(loads_json((root / 'catalog/source.json').read_bytes())['catalogVersion'], 'technical.blk3.v2')
            self.assertNotEqual((root / 'catalog/source.json').read_bytes(), recipe_bytes)
            for p, data in inputs.items(): self.assertEqual((root / p).read_bytes(), data, p)
            self.assertNotEqual(old_art.read_bytes(), new_art.read_bytes())
            pack = build_pack(root, after, roots=[MODEL]); write_pack(store, pack)
            self.assertEqual(snapshot(store / 'objects') | old_objects, snapshot(store / 'objects'))
            for p, data in old_objects.items(): self.assertEqual((store / 'objects' / p).read_bytes(), data)
            self.assertEqual(json.loads((store / 'manifest.json').read_bytes())['catalogVersion'], 'technical.blk3.v2')
            self.assertTrue(pack['objects'])
            self.assertNotEqual(set(pack['objects']), set(old_pack['objects']))
            self.assertEqual(write_pack(store, pack)['objectsReused'], len(pack['objects']))

    def test_invalid_amendments_preserve_all_files(self):
        for defect in ('wrong-model', 'rights', 'source', 'geometry'):
            with self.subTest(defect=defect), tempfile.TemporaryDirectory() as tmp:
                root = temporary_catalog(tmp); catalog = build_catalog(root)
                store = root / 'selected'; write_pack(store, build_pack(root, catalog, roots=[MODEL]))
                out = root / 'build/catalog.json'; out.parent.mkdir(); out.write_bytes(b'accepted catalog bytes')
                path, _, _ = candidate(root, defect); before = snapshot(root)
                result = cli(root, path, 'technical.invalid.' + defect, out)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertIn({'wrong-model': 'art not reviewed for this exact configuration',
                               'rights': 'MIT rights', 'source': 'asset sources required',
                               'geometry': 'unsupported source element image'}[defect], result.stderr)
                self.assertEqual(snapshot(root), before, result.stderr)
                self.assertEqual(build_catalog(root)['catalogVersion'], catalog['catalogVersion'])
                write_pack(store, build_pack(root, build_catalog(root), roots=[MODEL]))
                self.assertEqual(snapshot(root), before)

    def test_correction_and_independent_map_vectors(self):
        # Independent literal screen vectors for axes, antimeridian and poles.
        for lat, lon, expected in [(0, 0, (128, 128)), (90, -180, (1, 1)),
                                   (-90, 180, (1, 255)), (0, 180, (1, 128)),
                                   (0, -180, (1, 128))]:
            self.assertEqual(project(lat, lon), expected)
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp); before = build_catalog(root)
            original = before['dictionaries']['sites'][SITE]
            self.assertEqual(original['position']['latitude'].as_tuple(), Decimal('28.58341025').as_tuple())
            self.assertEqual(original['position']['longitude'].as_tuple(), Decimal('-80.58303644').as_tuple())
            self.assertEqual(original['facts']['sourceUrl'], 'https://ll.thespacedevs.com/2.3.0/pads/29/?format=json')
            sources = [original['facts']['sourceUrl']]
            c = {'schemaVersion': 1, 'id': 'technical-point-correction', 'reviewedAt': '2026-11-14',
                 'sources': sources, 'reason': 'Technical point mutation, not a surveyed location.',
                 'assets': [], 'additions': [], 'updates': [{'identity': SITE, 'sources': sources,
                    'changes': {'latitude': Decimal('28.123400'), 'longitude': Decimal('-80.567890')}}]}
            path = root / 'assets/global/technical-point.json'; path.write_bytes(canonical_bytes(c))
            result = cli(root, path, 'technical.point.v2', root / 'build/catalog.json')
            self.assertEqual(result.returncode, 0, result.stderr)
            row = build_catalog(root)['dictionaries']['sites'][SITE]
            self.assertEqual(row.get('originalFacts', row['facts']), original.get('originalFacts', original['facts']))
            self.assertEqual(row['facts']['sourceId'], 29)
            self.assertEqual(row['position']['latitude'].as_tuple(), Decimal('28.123400').as_tuple())
            self.assertEqual(row['position']['longitude'].as_tuple(), Decimal('-80.567890').as_tuple())

    def test_readd_real_model_in_current_recipe(self):
        # Remove only this actual identity and its two subsequent updates from a
        # temporary global.40 recipe. Every other current source remains intact.
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp); source = root / 'catalog/source.json'
            recipe = loads_json(source.read_bytes()); registry_pin = recipe.pop('eligibility')
            addition = None
            for name in ('curation-20261112-current-closure-r1.json',
                         'curation-20261113-current-next-r1.json', 'curation-20261113-blk3-r1.json'):
                path = root / 'assets/global' / name; revision = loads_json(path.read_bytes())
                if name.startswith('curation-20261112'):
                    addition = next(x for x in revision['additions'] if x['identity'] == MODEL)
                    revision['additions'].remove(addition)
                revision['updates'] = [x for x in revision['updates'] if x['identity'] != MODEL]
                path.write_bytes(canonical_bytes(revision))
                entry = next(x for x in recipe['curations'] if x['path'] == path.relative_to(root).as_posix())
                entry['sha256'] = digest(path.read_bytes())
            source.write_bytes(canonical_bytes(recipe)); before = build_catalog(root)
            self.assertNotIn(MODEL, before['dictionaries']['configurations'])
            registry = loads_json((root / registry_pin['path']).read_bytes()); del registry['records'][MODEL]
            registry['dictionaryDigest'] = digest(canonical_bytes(before['dictionaries']))
            reg = root / 'catalog/technical-eligibility.json'; reg.write_bytes(canonical_bytes(registry))
            recipe['eligibility'] = {'path': reg.relative_to(root).as_posix(), 'sha256': digest(reg.read_bytes())}
            source.write_bytes(canonical_bytes(recipe))
            c = {'schemaVersion': 1, 'id': 'readd-real-blk3', 'reviewedAt': '2026-11-12',
                 'sources': [addition['facts']['sourceUrl']], 'reason': 'Replay actual retained model addition.',
                 'assets': [], 'updates': [], 'additions': [addition]}
            path = root / 'assets/global/readd-real-blk3.json'; path.write_bytes(canonical_bytes(c))
            result = cli(root, path, 'technical.readd.blk3', root / 'build/catalog.json')
            self.assertEqual(result.returncode, 0, result.stderr)
            after = build_catalog(root); row = after['dictionaries']['configurations'][MODEL]
            self.assertEqual(row['facts'], addition['facts'])
            self.assertEqual(row['references'], addition['references'])
            self.assertEqual(row['facts']['name'], 'EXOS BLK3')
            self.assertEqual(set(after['dictionaries']['configurations']), set(before['dictionaries']['configurations']) | {MODEL})
            for identity, prior in before['dictionaries']['configurations'].items():
                self.assertEqual(after['dictionaries']['configurations'][identity], prior, identity)

    def test_invalid_point_refuses_atomically(self):
        source = 'https://ll.thespacedevs.com/2.3.0/pads/29/?format=json'
        for label, changes, sources in [('range', {'latitude': 91}, [source]),
                                         ('identity', {'sourceId': 30}, [source]),
                                         ('unsourced', {'latitude': Decimal('28.1234')}, [])]:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as tmp:
                root = temporary_catalog(tmp)
                out = root / 'build/catalog.json'; out.parent.mkdir(); out.write_bytes(b'accepted')
                c = {'schemaVersion': 1, 'id': 'technical-invalid-point', 'reviewedAt': '2026-11-14',
                     'sources': [source], 'reason': 'Technical refusal control.', 'assets': [], 'additions': [],
                     'updates': [{'identity': SITE, 'sources': sources, 'changes': changes}]}
                path = root / 'assets/global/invalid-point.json'; path.write_bytes(canonical_bytes(c))
                before = snapshot(root); result = cli(root, path, 'technical.invalid.point.' + label, out)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertRegex(result.stderr, {'range': 'latitude|coordinate', 'identity': 'invalid fact correction',
                                                 'unsourced': 'sources'}[label])
                self.assertEqual(snapshot(root), before)

    def test_malformed_selection_keeps_store(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp); catalog = build_catalog(root); store = root / 'selected'
            write_pack(store, build_pack(root, catalog, roots=[MODEL])); before = snapshot(store)
            for roots in ([MODEL, 'll2:configuration:does-not-exist'], ['bad'], []):
                with self.assertRaises(VisualError): build_pack(root, catalog, roots=roots)
                self.assertEqual(snapshot(store), before)

if __name__ == '__main__': unittest.main()
