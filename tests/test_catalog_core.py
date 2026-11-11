"""Independent literal vectors for the local publisher; no workflow imports."""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.spacefox.catalog import (
    CatalogError, build_catalog, canonical_bytes, dependency_closure,
    loads_json, normalize_reference, validate_catalog,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/catalog/core-reference.json'
ARCHIVE = ROOT / 'openspec/changes/spacefox-watchface/evidence/global-catalog/reference-inventory.json'
ARCHIVE_SHA = 'a94bdeb202861d2759db348d2b9ded75a15ca9e4acd86f466a4adc6e02669263'


class CatalogCoreTest(unittest.TestCase):
    def setUp(self):
        fixture = loads_json(FIXTURE.read_bytes())
        self.reference, self.registry = fixture['reference'], fixture['registry']

    def catalog(self):
        return normalize_reference(self.reference, self.registry, catalog_version='fixture.1')

    def test_entities_positive(self):
        c = self.catalog()
        d = c['dictionaries']
        self.assertEqual(d['configurations']['ll2:configuration:121']['facts']['fullName'], 'Ariane 62')
        self.assertEqual(d['organizations']['ll2:organization:121']['facts']['name'], 'SpaceX')
        roots = ['ll2:configuration:164', 'll2:site:13', 'll2:configuration:164']
        s = dependency_closure(c, roots, expected_revision='fixture.1')
        self.assertEqual(set(s['dictionaries']['organizations']), {'ll2:organization:121'})
        self.assertEqual(set(s['dictionaries']['countries']), {'ll2:country:2'})
        self.assertEqual(len(s['dictionaries']['assets']), 3)
        self.assertEqual(s['roots'], ['ll2:configuration:164', 'll2:site:13'])
        self.assertNotIn('ll2:configuration:121', s['dictionaries']['configurations'])
        s['dictionaries']['organizations']['ll2:organization:121']['facts']['name'] = 'changed'
        self.assertEqual(d['organizations']['ll2:organization:121']['facts']['name'], 'SpaceX')

    def test_entities_negative(self):
        for collection in ('models', 'organizations', 'countries', 'sites'):
            for conflict in (False, True):
                with self.subTest(collection=collection, conflict=conflict):
                    r = copy.deepcopy(self.reference)
                    item = copy.deepcopy(r[collection][0])
                    if conflict:
                        item['name'] = 'Conflicting source value'
                    r[collection].append(item)
                    with self.assertRaises(CatalogError):
                        normalize_reference(r, self.registry, catalog_version='fixture.1')
        for bad in (True, 0, -1, '00121', '121:other'):
            self.reference['models'][0]['sourceId'] = bad
            with self.subTest(bad=bad), self.assertRaises(CatalogError):
                self.catalog()

    def test_order_positive(self):
        before = self.catalog()
        for source_collection, collection in (('models', 'configurations'), ('organizations', 'organizations'), ('countries', 'countries'), ('sites', 'sites')):
            kind = {'configurations': 'configuration', 'organizations': 'organization', 'countries': 'country', 'sites': 'site'}[collection]
            for expected in self.reference[source_collection]:
                self.assertEqual(before['dictionaries'][collection][f'll2:{kind}:{expected["sourceId"]}']['facts'], expected)
        for collection in ('models', 'organizations', 'countries', 'sites'):
            self.reference[collection].reverse()
        for collection in ('models', 'companies', 'countries'):
            self.registry[collection].reverse()
        self.assertEqual(canonical_bytes(before), canonical_bytes(self.catalog()))
        self.registry['models'][2]['aliases'].append('Renamed full alias')
        self.registry['models'][2]['aliases'].reverse()
        after = self.catalog()
        self.assertEqual(set(before['dictionaries']['configurations']), set(after['dictionaries']['configurations']))
        self.assertIn(b'177.864469000000000001', canonical_bytes(after))
        self.assertIn('未知 / Я'.encode(), canonical_bytes(after))
        self.assertEqual(after['dictionaries']['organizations']['ll2:organization:121']['facts']['providerPendingLaunches'], None)
        self.assertEqual(after['dictionaries']['organizations']['ll2:organization:1044']['facts']['providerPendingLaunches'], 0)
        # Independent literal JSON ensures duplicate keys cannot be silently overwritten.
        self.assertEqual(loads_json(b'{"n":1.2300,"z":0,"u":null}'), {'n': Decimal('1.2300'), 'z': 0, 'u': None})
        self.assertEqual(canonical_bytes(loads_json(b'{"n":1.2300}')), b'{"n":1.2300}')

    def test_order_negative(self):
        for data in (b'{"x":1,"x":2}', b'{"n":NaN}', b'{"n":Infinity}', b'{"n":-Infinity}'):
            with self.subTest(data=data), self.assertRaises(CatalogError):
                loads_json(data)
        for bad in (2, True, '1'):
            r = copy.deepcopy(self.reference); r['schemaVersion'] = bad
            with self.subTest(schema=bad), self.assertRaises(CatalogError):
                normalize_reference(r, self.registry, catalog_version='fixture.1')
        c = self.catalog()
        for revision in ('fixture.0', '', None):
            with self.subTest(revision=revision), self.assertRaises(CatalogError):
                dependency_closure(c, ['ll2:site:13'], expected_revision=revision)
        for schema in (2, True):
            c['schemaVersion'] = schema
            with self.assertRaises(CatalogError):
                validate_catalog(c)
        for field, value in (('license', None), ('sources', []), ('aliases', [121]), ('file', ''), ('creator', ''), ('name', '')):
            c = self.catalog()
            facts = c['dictionaries']['assets']['spacefox:asset:generic']['facts']
            if value is None:
                del facts[field]
            else:
                facts[field] = value
            with self.subTest(asset_field=field), self.assertRaises(CatalogError):
                validate_catalog(c)
        c = self.catalog()
        del c['dictionaries']['assets']['spacefox:asset:flag-europe']['facts']['codes']
        with self.assertRaises(CatalogError):
            validate_catalog(c)

    def test_roles_positive(self):
        c = self.catalog(); d = c['dictionaries']
        cfg = d['configurations']['ll2:configuration:121']
        org = d['organizations']['ll2:organization:121']
        self.assertEqual(cfg['references']['manufacturer'], 'll2:organization:1044')
        self.assertEqual(cfg['references']['origin'], 'spacefox:country:EUROPE')
        self.assertEqual(cfg['unresolvedFamilies'], ['ll2:family:99'])
        self.assertEqual(org['roles'], ['manufacturer-of-required-configuration'])
        self.assertNotIn('operator', org['roles'])
        self.assertEqual(d['organizations']['ll2:organization:1044']['roles'], [])
        self.assertIsNone(d['organizations']['ll2:organization:1044']['references']['origin'])
        self.assertEqual(d['countries']['ll2:country:17']['jurisdictionKind'], 'unknown')
        self.assertEqual(d['countries']['spacefox:country:EUROPE']['jurisdictionKind'], 'region')
        self.assertIsNone(d['configurations']['ll2:configuration:999']['references']['origin'])
        self.assertEqual(org['originSources'], ['fixture:operator-origin'])
        self.assertEqual(cfg['originSources'], ['fixture:regional-origin'])
        self.assertEqual(c['source']['reference']['source']['termsUrl'], 'fixture-data-rights')

    def test_roles_negative(self):
        mutations = [
            ('models', 'manufacturerId', 999999), ('models', 'manufacturerCountryIds', [999999]),
            ('sites', 'countryId', 999999), ('sites', 'agencyIds', [999999]),
            ('organizations', 'countryIds', [999999]), ('models', 'currentPackAssetId', 'missing'),
        ]
        for collection, field, value in mutations:
            r = copy.deepcopy(self.reference); r[collection][0][field] = value
            with self.subTest(field=field), self.assertRaises(CatalogError):
                normalize_reference(r, self.registry, catalog_version='fixture.1')
        c = self.catalog()
        c['dictionaries']['configurations']['ll2:configuration:121']['references']['manufacturer'] = 'll2:configuration:121'
        with self.assertRaises(CatalogError):
            validate_catalog(c)
        r = copy.deepcopy(self.reference); r['countries'][2]['alpha2'] = 'US'
        with self.assertRaises(CatalogError):
            normalize_reference(r, self.registry, catalog_version='fixture.1')
        seed = copy.deepcopy(self.registry)
        seed['countries'][0]['codes'].append('US')
        with self.assertRaises(CatalogError):
            normalize_reference(self.reference, seed, catalog_version='fixture.1')
        c = self.catalog()
        c['dictionaries']['organizations']['ll2:organization:121']['references']['countries'] = [{}]
        with self.assertRaises(CatalogError):
            validate_catalog(c)
        # Every target exists and has the correct kind. These still contradict
        # the independent source IDs/curated origin retained in the same record.
        contradictory = (
            ('configurations', 'll2:configuration:121', 'manufacturer', 'll2:organization:121'),
            ('configurations', 'll2:configuration:121', 'manufacturerCountries', ['ll2:country:2']),
            ('configurations', 'll2:configuration:121', 'visual', 'spacefox:asset:falcon-9'),
            ('configurations', 'll2:configuration:121', 'origin', 'll2:country:1'),
            ('organizations', 'll2:organization:121', 'countries', ['ll2:country:1']),
            ('organizations', 'll2:organization:121', 'badge', None),
            ('organizations', 'll2:organization:121', 'origin', 'll2:country:1'),
            ('sites', 'll2:site:13', 'country', 'll2:country:2'),
            ('sites', 'll2:site:13', 'agencies', ['ll2:organization:1044']),
            ('countries', 'll2:country:2', 'mark', 'spacefox:asset:flag-fr'),
        )
        for collection, identity, field, value in contradictory:
            c = self.catalog()
            c['dictionaries'][collection][identity]['references'][field] = value
            with self.subTest(identity=identity, field=field), self.assertRaises(CatalogError):
                validate_catalog(c)
        c = self.catalog()
        c['dictionaries']['organizations']['ll2:organization:121']['roles'] = ['operator']
        with self.assertRaises(CatalogError):
            validate_catalog(c)
        c = self.catalog()
        c['dictionaries']['configurations']['ll2:configuration:121']['originSources'] = ['fixture:wrong-origin-source']
        with self.assertRaises(CatalogError):
            validate_catalog(c)
        c = self.catalog()
        c['dictionaries']['configurations']['ll2:configuration:121']['facts']['currentPackAssetId'] = 'missing-source-id'
        with self.assertRaises(CatalogError):
            validate_catalog(c)
        for collection, identity, field, value in (
            ('configurations', 'll2:configuration:121', 'recordId', 0),
            ('sites', 'll2:site:13', 'source', 'assetSeed'),
            ('assets', 'spacefox:asset:generic', 'recordId', 'flag-fr'),
            ('assets', 'spacefox:asset:generic', 'source', 'reference'),
            ('countries', 'll2:country:1', 'recordId', True),
        ):
            c = self.catalog()
            c['dictionaries'][collection][identity]['provenance'][0][field] = value
            with self.subTest(identity=identity, provenance_field=field), self.assertRaises(CatalogError):
                validate_catalog(c)
        for identity, classification in (('ll2:country:17', 'country'), ('ll2:country:1', 'territory')):
            c = self.catalog()
            c['dictionaries']['countries'][identity]['jurisdictionKind'] = classification
            with self.subTest(identity=identity, classification=classification), self.assertRaises(CatalogError):
                validate_catalog(c)

    def test_coordinates_positive(self):
        d = self.catalog()['dictionaries']['sites']
        sea = d['ll2:site:13']
        self.assertEqual(sea['position'], {'latitude': 0, 'longitude': Decimal('-154.000000000000000001'), 'units': 'degrees', 'qualification': 'unverified-reference'})
        self.assertIsNone(sea['eventPosition'])
        self.assertIsNone(sea['references']['country'])
        self.assertIsNone(d['ll2:site:101']['position'])
        self.assertEqual(d['ll2:site:65']['position'], d['ll2:site:185']['position'])
        self.assertNotEqual(d['ll2:site:65']['facts']['sourceId'], d['ll2:site:185']['facts']['sourceId'])
        self.assertFalse(d['ll2:site:65']['facts']['providerActive'])
        self.assertEqual(d['ll2:site:65']['facts']['mapRenderQualification'], 'not-performed')
        for lat, lon in ((90, 180), (-90, -180), (0, 0)):
            self.reference['sites'][0].update(latitude=lat, longitude=lon)
            self.assertEqual(self.catalog()['dictionaries']['sites']['ll2:site:13']['position']['latitude'], lat)

    def test_coordinates_negative(self):
        for field, value in (('latitude', Decimal('90.000000000000000001')), ('latitude', -91), ('longitude', 181), ('latitude', Decimal('NaN')), ('longitude', Decimal('Infinity')), ('latitude', None), ('latitude', True), ('longitude', '0'), ('longitude', float('nan'))):
            r = copy.deepcopy(self.reference); r['sites'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(CatalogError):
                normalize_reference(r, self.registry, catalog_version='fixture.1')
        c = self.catalog()
        del c['dictionaries']['sites']['ll2:site:13']['facts']['latitude']
        with self.assertRaises(CatalogError):
            validate_catalog(c)
        for field, value in (('latitude', False), ('latitude', Decimal('0')),
                             ('latitude', Decimal('0.0')),
                             ('longitude', Decimal('-154.0000000000000000010')),
                             ('units', 'radians'), ('qualification', 'verified')):
            c = self.catalog()
            c['dictionaries']['sites']['ll2:site:13']['position'][field] = value
            with self.subTest(derived_field=field, derived_value=value), self.assertRaises(CatalogError):
                validate_catalog(c)
        r = copy.deepcopy(self.reference)
        r['sites'][0]['latitude'] = Decimal('-0.00')
        c = normalize_reference(r, self.registry, catalog_version='fixture.1')
        self.assertEqual(c['dictionaries']['sites']['ll2:site:13']['position']['latitude'].as_tuple(), Decimal('-0.00').as_tuple())
        c['dictionaries']['sites']['ll2:site:13']['position']['latitude'] = Decimal('0.00')
        with self.assertRaises(CatalogError):
            validate_catalog(c)
        for identity, position in (('ll2:site:13', None), ('ll2:site:101', {'latitude': 0, 'longitude': 0, 'units': 'degrees', 'qualification': 'unverified-reference'})):
            c = self.catalog()
            c['dictionaries']['sites'][identity]['position'] = position
            with self.subTest(identity=identity), self.assertRaises(CatalogError):
                validate_catalog(c)
        c = self.catalog()
        del c['dictionaries']['sites']['ll2:site:101']['position']
        with self.assertRaises(CatalogError):
            validate_catalog(c)

    def test_frozen_import_positive(self):
        before = ARCHIVE.read_bytes()
        c = build_catalog(ROOT)
        d = c['dictionaries']
        self.assertEqual({k: len(d[k]) for k in d}, {'countries': 104, 'organizations': 350, 'configurations': 170, 'sites': 216, 'assets': 13})
        expected = {26: 'electron', 116: 'ariane-64', 121: 'ariane-62', 161: 'falcon-heavy', 164: 'falcon-9'}
        for key, asset in expected.items():
            self.assertEqual(d['configurations'][f'll2:configuration:{key}']['references']['visual'], f'spacefox:asset:{asset}')
        self.assertEqual(d['configurations']['ll2:configuration:116']['facts']['providerPendingLaunches'], 16)
        self.assertFalse(d['configurations']['ll2:configuration:116']['facts']['providerActive'])
        self.assertTrue(all(x['facts']['providerPendingLaunches'] is None for x in d['organizations'].values()))
        self.assertEqual(d['countries']['ll2:country:1']['references']['mark'], d['countries']['ll2:country:50']['references']['mark'])
        self.assertEqual(d['sites']['ll2:site:13']['position']['latitude'], 0)
        self.assertIsNone(d['sites']['ll2:site:101']['position'])
        self.assertEqual(hashlib.sha256(before).hexdigest(), ARCHIVE_SHA)
        self.assertEqual(before, ARCHIVE.read_bytes())
        self.assertEqual(canonical_bytes(c), canonical_bytes(build_catalog(ROOT)))
        self.assertEqual(d['assets']['spacefox:asset:falcon-9']['content']['sha256'], hashlib.sha256((ROOT/'assets/rocket-pack/svg/falcon-9.svg').read_bytes()).hexdigest())

    def test_frozen_import_negative(self):
        manifest = loads_json((ROOT/'catalog/source.json').read_bytes())
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/'source.json'
            for key, change in (('reference', {'sha256': '0'*64}), ('assetSeed', {'sha256': '0'*64}), ('reference', {'path': '../outside.json'}), ('reference', {'path': str(ARCHIVE)})):
                bad = copy.deepcopy(manifest); bad[key].update(change)
                p.write_bytes(canonical_bytes(bad))
                with self.subTest(key=key, change=change), self.assertRaises(CatalogError):
                    build_catalog(ROOT, p)

    def test_source_contract_positive(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp)/'catalog.json'
            r = subprocess.run([sys.executable, '-B', 'tools/catalog.py', '--output', str(out)], cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(out.read_bytes(), canonical_bytes(build_catalog(ROOT)))
            summary = json.loads(r.stdout)
            self.assertEqual(summary['schemaVersion'], 1)
            self.assertEqual(summary['sha256'], hashlib.sha256(out.read_bytes()).hexdigest())
            self.assertEqual(summary['qualification'], 'publisher-metadata-only')

    def test_source_contract_negative(self):
        manifest = loads_json((ROOT/'catalog/source.json').read_bytes())
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp)/'source.json'; out = Path(temp)/'accepted.json'
            out.write_bytes(b'previous accepted output')
            for change in ({'schemaVersion': 2}, {'catalogVersion': ''}, {'secondCatalog': []}):
                bad = copy.deepcopy(manifest); bad.update(change); p.write_bytes(canonical_bytes(bad))
                r = subprocess.run([sys.executable, '-B', 'tools/catalog.py', '--source', str(p), '--output', str(out)], cwd=ROOT, capture_output=True, text=True)
                self.assertNotEqual(r.returncode, 0)
                self.assertEqual(out.read_bytes(), b'previous accepted output')
            p.write_bytes(canonical_bytes(manifest))
            original = p.read_bytes()
            r = subprocess.run([sys.executable, '-B', 'tools/catalog.py', '--source', str(p), '--output', str(p)], cwd=ROOT, capture_output=True, text=True)
            self.assertNotEqual(r.returncode, 0)
            self.assertEqual(p.read_bytes(), original)
        c = self.catalog()
        with self.assertRaises(CatalogError):
            dependency_closure(c, ['ll2:configuration:missing'], expected_revision='fixture.1')
        with self.assertRaises(CatalogError):
            dependency_closure(c, ['ll2:configuration:121'], expected_revision='fixture.0')


if __name__ == '__main__':
    unittest.main()
