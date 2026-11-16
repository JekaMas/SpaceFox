"""Literal content-addressed current/retained metadata admission controls."""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json
from tools.spacefox.graphics import build_pack
from tools.spacefox.global_map import GeographyError, build_bundle, write_bundle
from tests.test_global_content import lifecycle, URL

ROOT = Path(__file__).resolve().parents[1]


def patch_row(row, changes):
    """Keep visible correction history consistent so it cannot mask the defect."""
    if 'originalFacts' not in row:
        row['originalFacts'] = copy.deepcopy(row['facts'])
        row['curation'] = {'id': 'r3-literal-selection-correction', 'reviewedAt': '2026-11-12',
                           'sources': [URL], 'reason': 'Literal metadata discriminator.', 'changes': {}}
        row['curationHistory'] = [{'id': row['curation']['id'], 'changes': {}, 'sources': [URL]}]
    row['facts'].update(changes)
    row['curation']['changes'].update(changes)
    row['curationHistory'][-1]['changes'].update(changes)


def rehash(bundle, change):
    bad = copy.deepcopy(bundle)
    old = bad['manifest']['current']['visual']
    record = loads_json(bad['files'].pop(old))
    change(record)
    data = canonical_bytes(record)
    new = 'manifests/'+hashlib.sha256(data).hexdigest()+'.json'
    bad['files'][new] = data
    bad['manifest']['files'].pop(old)
    bad['manifest']['files'][new] = {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}
    bad['manifest']['current']['visual'] = new
    bad['manifest']['currentFiles'].remove(old)
    bad['manifest']['currentFiles'].append(new)
    bad['artifactBytes'] = len(canonical_bytes(bad['manifest']))+sum(map(len, bad['files'].values()))
    return bad


class GlobalContentSelectionR3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        cls.pack = build_pack(ROOT, cls.catalog, roots=[
            'll2:configuration:175', 'spacefox:configuration:miura9', 'll2:configuration:511',
            'll2:organization:183', 'll2:country:17', 'll2:organization:37', 'll2:configuration:52'])
        cls.bundle = build_bundle(cls.pack, [])

    def test_rehashed_current_retained_metadata_negative(self):
        def mutation(name):
            def change(record):
                d = record['selection']['dictionaries']
                if name in ('future-date', 'bad-state', 'incomplete'):
                    facts = d['configurations']['spacefox:configuration:miura9']['facts']
                    if name == 'future-date': facts['officialLifecycleReviewedAt'] = '9999-12-31'
                    elif name == 'bad-state': facts['officialLifecycle'] = True
                    else: facts.pop('officialLifecycleNote')
                elif name == 'wrong-collection':
                    patch_row(d['organizations']['ll2:organization:37'], lifecycle())
                elif name == 'unknown-badge':
                    row = d['organizations']['ll2:organization:183']
                    badge = d['organizations']['ll2:organization:37']['references']['badge']
                    patch_row(row, {'name': 'Literal renamed unresolved operator',
                                    'currentPackBadgeId': badge.removeprefix('spacefox:asset:')})
                    row['references']['badge'] = badge
                elif name == 'unknown-country-recode':
                    row = d['countries']['ll2:country:17']
                    patch_row(row, {'alpha2': 'ZX', 'alpha3': 'ZXX', 'jurisdictionKind': 'country'})
                    row['jurisdictionKind'] = 'country'
                elif name == 'unknown-model':
                    patch_row(d['configurations']['ll2:configuration:511'],
                              {'name': 'Literal resolved vehicle', 'placeholder': False})
                elif name in ('unknown-model-origin', 'unknown-operator-origin'):
                    table, identity, field = (('configurations', 'll2:configuration:52', 'visual') if
                                              name == 'unknown-model-origin' else
                                              ('organizations', 'll2:organization:37', 'badge'))
                    row = d[table][identity]
                    facts = record['assets'][row['references'][field]]['catalogRecord']['facts']
                    facts.update(originCode='??', originSources=[URL])
                    row['references']['origin'] = 'll2:country:17'; row['originSources'] = [URL]
                elif name == 'wrong-exact-art':
                    row = d['configurations']['ll2:configuration:52']
                    art = d['configurations']['ll2:configuration:175']['references']['visual']
                    patch_row(row, {'currentPackAssetId': art.removeprefix('spacefox:asset:')})
                    row['references']['visual'] = art
                elif name == 'wrong-typed-role':
                    row = d['configurations']['ll2:configuration:52']
                    badge = d['organizations']['ll2:organization:37']['references']['badge']
                    patch_row(row, {'currentPackAssetId': badge.removeprefix('spacefox:asset:'),
                                    'currentPackSpecific': False})
                    row['references']['visual'] = badge
            return change
        names = ('future-date', 'bad-state', 'incomplete', 'wrong-collection', 'unknown-badge',
                 'unknown-country-recode', 'unknown-model', 'unknown-model-origin',
                 'unknown-operator-origin', 'wrong-exact-art', 'wrong-typed-role')
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            write_bundle(output, self.bundle)
            accepted = (output/'manifest.json').read_bytes()
            for name in names:
                bad = rehash(self.bundle, mutation(name))
                with self.subTest(name=name, boundary='current'), self.assertRaises(GeographyError):
                    write_bundle(output, bad)
                self.assertEqual((output/'manifest.json').read_bytes(), accepted)
                # Reproduce a self-consistent retained artifact on disk; both
                # its file hash and top index agree with the invalid metadata.
                for path, data in bad['files'].items():
                    target = output/path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
                (output/'manifest.json').write_bytes(canonical_bytes(bad['manifest']))
                with self.subTest(name=name, boundary='retained'), self.assertRaises(GeographyError):
                    build_bundle(self.pack, [], previous_directory=output)
                (output/'manifest.json').write_bytes(accepted)

    def test_known_unknown_legacy_current_retained_positive(self):
        historical = build_catalog(ROOT, ROOT/'tests/fixtures/catalog/global-before-content-source.json')
        legacy = build_pack(ROOT, historical, roots=['spacefox:configuration:s310', 'll2:configuration:164'])
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)
            first = build_bundle(legacy, [])
            write_bundle(output, first)
            second = build_bundle(self.pack, [], previous_directory=output)
            receipt = write_bundle(output, second)
            self.assertTrue(receipt['retainedSelection'])
            self.assertLessEqual(receipt['artifactBytes'], 1048576)
            d = self.pack['manifest']['selection']['dictionaries']
            self.assertIsNone(d['organizations']['ll2:organization:183']['references']['badge'])
            self.assertEqual(d['configurations']['ll2:configuration:511']['references']['visual'], 'spacefox:asset:generic')
            self.assertEqual(d['configurations']['ll2:configuration:175']['references']['visual'],
                             'spacefox:asset:content-r1-vehicle-minotaur-i')
            self.assertEqual(d['configurations']['ll2:configuration:52']['references']['visual'],
                             'spacefox:asset:content-r1-vehicle-minotaur-iv')
            self.assertEqual(d['organizations']['ll2:organization:37']['references']['origin'], 'll2:country:28')
            old = legacy['manifest']['selection']['dictionaries']['configurations']['spacefox:configuration:s310']
            self.assertEqual(old['facts']['officialLifecycle'], 'operating-listed')
            self.assertNotIn('officialLifecycleReviewedAt', old['facts'])


if __name__ == '__main__':
    unittest.main()
