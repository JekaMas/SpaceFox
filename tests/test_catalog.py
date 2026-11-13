"""Original VC11/12/15 inputs at actual local catalog/CLI/export boundaries.

Synthetic source facts qualify maintenance mechanics, not world accuracy. These
are the ten original reserved methods; accepted legacy/motion evidence is retained.
"""
import copy
from decimal import Decimal
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.spacefox.catalog import (CatalogError, build_catalog, canonical_bytes,
                                     loads_json, validate_catalog)
from tools.spacefox.global_map import build_site_view, _validate_geography_metadata
from tools.spacefox.graphics import (assemble_visual, build_pack,
                                     write_pack)
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import AcceptedLaunch, ScheduleState
from tools.spacefox.visual_bridge import read_ref

ROOT = Path(__file__).resolve().parents[1]
NOW = 1794484800
SOURCE = 'https://source.example.test/original-maintenance-fixture'
TIMELINE = [2000, [[0, 0, 0, 256], [1000, 64, -128, 384], [2000, 0, 0, 256]]]


class CatalogTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='spacefox-original-catalog-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        seed = loads_json((ROOT / 'tests/fixtures/catalog/core-reference.json').read_bytes())
        self.reference, registry = seed['reference'], seed['registry']
        # Original exact controlled points and unknown identity. No product facts
        # or source history are changed by these test-only, HTTPS-labeled inputs.
        self.reference['sites'][1].update(latitude=Decimal('28.56'), longitude=Decimal('-80.57'), sourceUrl=SOURCE)
        self.reference['models'][2].update(name='NewRocket', fullName='NewRocket')
        for group, size in [('models', [54, 124]), ('companies', [20, 38]), ('countries', [20, 12])]:
            for asset in registry[group]:
                asset['exportSize'] = size
                path = self.root / 'assets/rocket-pack' / asset['file']
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((ROOT / 'assets/rocket-pack' / asset['file']).read_bytes())
        world = dict(schemaVersion=1, license='public-domain', sources=[SOURCE],
                     credit='Original test line', derivation='Synthetic line, no world accuracy claim',
                     lines=[[[-90, 0], [0, 0]]])
        recipe = dict(schemaVersion=1, producerVersion=2, curations=[], catalogVersion='original.fixture.1')
        for key, relative, value in [('reference', 'catalog/reference.json', self.reference),
                                     ('assetSeed', 'assets/rocket-pack/registry.source.json', registry),
                                     ('geography', 'catalog/world.json', world)]:
            recipe[key] = self.pin(relative, value)
        self.source = self.root / 'catalog/source.json'
        self.source.write_bytes(canonical_bytes(recipe))
        self.accepted = self.root / 'accepted-pack'
        write_pack(self.accepted, build_pack(self.root, build_catalog(self.root), roots=['spacefox:asset:generic']))
        self.settings = self.root / 'settings.json'
        self.settings.write_text('{"originMode":"operator","animation":"Off","fitness":["steps","battery"]}')

    def pin(self, relative, value):
        raw = canonical_bytes(value)
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return dict(path=relative, sha256=hashlib.sha256(raw).hexdigest())

    def snapshot(self):
        return {p: p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def unchanged(self, before):
        for path, raw in before.items():
            self.assertEqual(path.read_bytes(), raw, str(path))
        self.assertEqual(list(self.source.parent.glob('.recipe-*')), [])

    def amendment(self, label):
        return dict(schemaVersion=1, id=label, reviewedAt='2026-11-13', sources=[SOURCE],
                    reason='Literal original maintenance contract; not real rocket/site qualification.',
                    assets=[], updates=[], additions=[])

    def image(self, label, *, model=164, color='#ffffff'):
        folder = self.root / 'assets/original'
        folder.mkdir(exist_ok=True)
        path = folder / (label + '.svg')
        path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 32">'
                        '<path fill="' + color + '" d="M6 0 L12 32 L0 32 Z"/></svg>')
        facts = dict(id=label, name='Original MIT fixture', file=path.name,
                     exportSize=[12, 32], creator='Original fixture creator',
                     credit='Original fixture creator — explicit distribution credit',
                     license='MIT', sources=[SOURCE], sourceSha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                     kind='specific', nativeMotion=copy.deepcopy(TIMELINE),
                     coverage=dict(type='specific', configurationIds=['ll2:configuration:' + str(model)],
                                   features=['Literal triangular test body'], limitations='No product geometry claim.'))
        value = self.amendment(label)
        value['assets'] = [dict(collection='models', facts=facts)]
        value['updates'] = [dict(identity='ll2:configuration:' + str(model), sources=[SOURCE],
                                 changes=dict(currentPackAssetId=label, currentPackSpecific=True))]
        return value

    def cli(self, value, *, error=None):
        path = self.root / 'assets/original' / (value['id'] + '.json')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(canonical_bytes(value))
        before = self.snapshot()
        command = [sys.executable, '-B', str(ROOT / 'tools/catalog.py'), '--repo', str(self.root),
                   '--amend', str(path), '--catalog-version', 'original.fixture.' + value['id']]
        result = subprocess.run(command, cwd=tempfile.gettempdir(), capture_output=True, text=True, timeout=30)
        trace = os.environ.get('SPACEFOX_TEST_TRACE')
        if trace:
            with Path(trace).open('a') as stream:
                stream.write(json.dumps(dict(test=self.id(), variant=value['id'], command=command,
                                             exitCode=result.returncode, stdout=result.stdout, stderr=result.stderr)) + '\n')
        if error is None:
            self.assertEqual(result.returncode, 0, result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout)
            self.assertRegex(result.stderr, error)
            self.unchanged(before)
        return build_catalog(self.root)

    def add_provider_model(self):
        # New upstream reference data is authored once, pinned once, then all
        # mapping/image/timeline changes use the one catalog amendment producer.
        self.assertNotIn('ll2:configuration:901', build_catalog(self.root)['dictionaries']['configurations'])
        facts = copy.deepcopy(self.reference['models'][2])
        facts.update(sourceId=901, name='Original901', fullName='Original901', sourceUrl=SOURCE)
        self.reference['models'].append(facts)
        recipe = loads_json(self.source.read_bytes())
        recipe['reference'] = self.pin('catalog/reference-with-901.json', self.reference)
        self.source.write_bytes(canonical_bytes(recipe))
        self.assertEqual(build_catalog(self.root)['dictionaries']['configurations']['ll2:configuration:901']['references']['visual'],
                         'spacefox:asset:generic')


    def test_add_a_rocket_visual_positive(self):
        self.add_provider_model()
        before = self.snapshot()
        c = self.cli(self.image('new-model-901', model=901))
        row = c['dictionaries']['configurations']['ll2:configuration:901']
        self.assertEqual(row['facts']['sourceId'], 901)
        self.assertEqual(row['references']['visual'], 'spacefox:asset:new-model-901')
        pack = build_pack(self.root, c, roots=['ll2:configuration:901'])
        drawing = pack['manifest']['assets']['spacefox:asset:new-model-901']
        self.assertEqual(drawing['catalogRecord']['facts']['nativeMotion'], TIMELINE)
        self.assertEqual(drawing['animation'], [0, []])
        value = assemble_visual([pack['objects'][s['sha256']] for s in drawing['shards']], drawing['animation'])
        self.assertEqual(value[3], [12, 32])
        self.assertEqual(value[7], [0, []])
        self.assertEqual(drawing['rights']['license'], 'MIT')
        from tools.spacefox import native_motion
        row = json.loads((ROOT / 'tests/fixtures/provider/page-normal.json').read_bytes())['results'][0]
        row['rocket']['configuration'].update(id=901, full_name='Original901')
        row['pad'] = None
        selected = normalize_launch(row, NOW)
        files, _ = native_motion.build_artifact(ScheduleState((AcceptedLaunch(selected),), NOW), c, NOW,
            publisher=dict(instance='1' * 64, generation=1, selectionValidatedUtc=NOW), root=self.root)
        motion_feed = loads_json(files[native_motion.FEED_PATH])
        scene = loads_json(read_ref(motion_feed['visualSelection'], files))
        actual = loads_json(read_ref(scene['roles']['rocket']['descriptor'], files))
        self.assertEqual(scene['modelId'], 'll2:configuration:901')
        self.assertEqual(actual['animation'], TIMELINE)
        self.assertEqual(actual['sourceCanvas'], [12, 32])
        for path, raw in before.items():
            if path != self.source:
                self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(set(c['dictionaries']['configurations']),
                         {'ll2:configuration:121', 'll2:configuration:164', 'll2:configuration:999', 'll2:configuration:901'})

    def test_add_a_rocket_visual_negative(self):
        good = self.image('shape-control')
        controlled = self.cli(good)
        write_pack(self.accepted, build_pack(self.root, controlled, roots=['spacefox:asset:shape-control']))
        before = self.snapshot()
        primitive_pack = build_pack(self.root, controlled, roots=['spacefox:asset:shape-control'])
        primitive_pack['manifest']['assets']['spacefox:asset:shape-control']['bounds'][2] = 8193
        with self.assertRaisesRegex(ValueError, 'asset bounds'):
            write_pack(self.accepted, primitive_pack)
        self.unchanged(before)
        missing = self.image('missing-asset')
        missing['updates'][0]['changes']['currentPackAssetId'] = 'not-present'
        self.cli(missing, error='missing|unknown|unresolved')
        ambiguous = self.image('ambiguous-mapping')
        ambiguous['updates'].append(copy.deepcopy(ambiguous['updates'][0]))
        ambiguous['updates'][1]['changes']['currentPackAssetId'] = 'generic'
        self.cli(ambiguous, error='duplicate correction identity')
        primitive = self.image('primitive-bounds')
        primitive['assets'][0]['facts']['exportSize'] = [257, 32]
        self.cli(primitive, error='exportSize')
        duration = self.image('timeline-bounds')
        duration['assets'][0]['facts']['nativeMotion'] = [3001, [[0, 0, 0, 256], [3001, 0, 0, 256]]]
        self.cli(duration, error='animation duration')

    def test_correct_a_launch_site_point_positive(self):
        before = build_catalog(self.root)
        old = build_site_view(self.root, before, 'll2:site:65')['manifest']
        value = self.amendment('site-correction')
        value['updates'] = [dict(identity='ll2:site:65', sources=[SOURCE],
                                 changes=dict(latitude=Decimal('28.57'), longitude=Decimal('-80.58')))]
        c = self.cli(value)
        row = c['dictionaries']['sites']['ll2:site:65']
        self.assertEqual((row['position']['latitude'], row['position']['longitude']), (Decimal('28.57'), Decimal('-80.58')))
        self.assertEqual((row['originalFacts']['latitude'], row['originalFacts']['longitude']), (Decimal('28.56'), Decimal('-80.57')))
        view = build_site_view(self.root, c, 'll2:site:65')['manifest']
        self.assertEqual(view['site']['id'], old['site']['id'])
        self.assertNotEqual(view['site']['definitionSha256'], old['site']['definitionSha256'])
        # Independent literal equirectangular 1/32px point, not project() reuse.
        self.assertEqual(old['marker'], [2277, 2806])
        self.assertEqual(view['marker'], [2277, 2806])
        # A .01-degree correction is below the retained1/32px map grid here;
        # exact manifest facts change, without inventing a visible pixel move.
        self.assertNotEqual(view['site']['sourcePosition'], old['site']['sourcePosition'])
        self.assertNotEqual(c['catalogVersion'], before['catalogVersion'])

    def test_correct_a_launch_site_point_negative(self):
        for label, changes, sources, error in [
                ('unsourced-swap', dict(latitude=Decimal('-80.58'), longitude=Decimal('28.57')), [], 'sources'),
                ('identity-churn', dict(sourceId=66, latitude=Decimal('28.57'), longitude=Decimal('-80.58')), [SOURCE], 'invalid fact correction')]:
            value = self.amendment(label)
            value['updates'] = [dict(identity='ll2:site:65', sources=sources, changes=changes)]
            self.cli(value, error=error)
        c = build_catalog(self.root)
        c['dictionaries']['sites']['ll2:site:65']['position'].update(latitude=Decimal('-80.57'), longitude=Decimal('28.56'))
        with self.assertRaisesRegex(CatalogError, 'position'):
            validate_catalog(c)
        view = build_site_view(self.root, build_catalog(self.root), 'll2:site:65')['manifest']
        view['site']['sourcePosition']['latitude'], view['site']['sourcePosition']['longitude'] = (
            view['site']['sourcePosition']['longitude'], view['site']['sourcePosition']['latitude'])
        with self.assertRaisesRegex(ValueError, 'marker/position'):
            _validate_geography_metadata(view)



    def test_invalid_geographic_entry_positive(self):
        value = self.amendment('sourced-zero')
        value['updates'] = [dict(identity='ll2:site:65', sources=[SOURCE], changes=dict(latitude=0, longitude=0))]
        c = self.cli(value)
        view = build_site_view(self.root, c, 'll2:site:65')['manifest']
        self.assertEqual(c['dictionaries']['sites']['ll2:site:65']['position'],
                         dict(latitude=0, longitude=0, units='degrees', qualification='unverified-reference'))
        self.assertEqual(view['marker'], [4096, 4096])
        self.assertIsNotNone(view['site']['sourcePosition'])
        self.assertEqual(c['dictionaries']['sites']['ll2:site:65']['curation']['sources'], [SOURCE])

    def test_invalid_geographic_entry_negative(self):
        for label, changes, error in [
                ('range-lat', dict(latitude=Decimal('90.001')), 'out of range'),
                ('range-lon', dict(longitude=Decimal('180.001')), 'out of range'),
                ('missing-partner', dict(latitude=None), 'partial coordinate pair')]:
            value = self.amendment(label)
            value['updates'] = [dict(identity='ll2:site:65', sources=[SOURCE], changes=changes)]
            self.cli(value, error=error)
        for token in ('NaN', 'Infinity', '-Infinity'):
            # Write invalid raw JSON explicitly; canonical_bytes rightly refuses
            # nonfinite values before the actual command can see them.
            value = self.amendment('nonfinite-' + token.replace('-', 'minus'))
            value['updates'] = [dict(identity='ll2:site:65', changes=dict(latitude='TOKEN'))]
            raw = canonical_bytes(value).replace(b'"TOKEN"', token.encode())
            path = self.root / 'assets/original' / (value['id'] + '.json')
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            before = self.snapshot()
            result = subprocess.run([sys.executable, '-B', str(ROOT / 'tools/catalog.py'), '--repo', str(self.root),
                                     '--amend', str(path), '--catalog-version', value['id']], capture_output=True, text=True, timeout=30)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('nonfinite JSON value', result.stderr)
            self.unchanged(before)
        c = build_catalog(self.root)
        self.assertIsNone(c['dictionaries']['sites']['ll2:site:101']['position'])
        unknown = build_site_view(self.root, c, 'll2:site:101')['manifest']
        self.assertIsNone(unknown['marker'])
        bad = copy.deepcopy(c)
        bad['dictionaries']['sites']['ll2:site:101']['position'] = dict(latitude=0, longitude=0, units='degrees', qualification='unverified-reference')
        with self.assertRaisesRegex(CatalogError, 'position'):
            validate_catalog(bad)

    def test_replace_a_rocket_image_positive(self):
        value = self.image('rights-replacement', color='#df7936')
        c = self.cli(value)
        asset_id = c['dictionaries']['configurations']['ll2:configuration:164']['references']['visual']
        pack = build_pack(self.root, c, roots=[asset_id])
        asset = pack['manifest']['assets'][asset_id]
        facts = asset['catalogRecord']['facts']
        for field in ('creator', 'sources', 'license', 'credit'):
            self.assertEqual(facts[field], value['assets'][0]['facts'][field])
        self.assertEqual(asset['rights']['credit'], facts['credit'])
        self.assertEqual(asset['rights']['license'], 'MIT')
        write_pack(self.accepted, pack)
        manifest = loads_json((self.accepted / 'manifest.json').read_bytes())
        self.assertEqual(manifest['assets'][asset_id]['rights'], asset['rights'])
        self.assertIn('spacefox:asset:falcon-9', c['dictionaries']['assets'])

    def test_replace_a_rocket_image_negative(self):
        controlled = self.cli(self.image('rights-control'))
        write_pack(self.accepted, build_pack(self.root, controlled, roots=['spacefox:asset:rights-control']))
        # Each is a valid original SVG with exact digest/mapping/shape control;
        # photo/logo intent is attribution metadata, never a format-error proxy.
        for label, changes, error in [
                ('provider-photo-unlicensed', dict(license='unknown'), 'requires MIT rights'),
                ('provider-logo-unlicensed', dict(license='all-rights-reserved'), 'requires MIT rights'),
                ('provider-photo-missing-credit', dict(credit=''), 'missing required credit'),
                ('provider-logo-missing-credit', dict(credit='  '), 'missing required credit')]:
            value = self.image(label)
            value['assets'][0]['facts'].update(changes)
            self.cli(value, error=error)
            c = build_catalog(self.root)
            self.assertEqual(c['dictionaries']['configurations']['ll2:configuration:164']['references']['visual'],
                             'spacefox:asset:rights-control')

    def openworld_fixture(self):
        return loads_json((ROOT / 'tests/fixtures/catalog/original-openworld.json').read_bytes())

    def openworld_reference(self):
        """New fictional upstream identities, authored once in the pinned input."""
        self.reference['countries'].append(dict(sourceId=902, name='Controlled country ZZ',
            alpha2='ZZ', alpha3='ZZZ', currentPackFlagId=None))
        organization = copy.deepcopy(self.reference['organizations'][1])
        organization.update(sourceId=903, name='Controlled ZZ public operator', abbrev='ZZ',
                            sourceUrl=SOURCE, countryIds=[902], currentPackBadgeId=None)
        model = copy.deepcopy(self.reference['models'][2])
        model.update(sourceId=900, name='Controlled ZZ model900', fullName='Controlled ZZ model900',
                     sourceUrl=SOURCE, manufacturerId=903, manufacturerCountryIds=[902])
        site = copy.deepcopy(self.reference['sites'][3])
        site.update(sourceId=901, name='Controlled ZZ site901', sourceUrl=SOURCE,
                    locationName='Controlled ZZ place', countryId=902, agencyIds=[903])
        self.reference['organizations'].append(organization)
        self.reference['models'].append(model)
        self.reference['sites'].append(site)
        recipe = loads_json(self.source.read_bytes())
        recipe['reference'] = self.pin('catalog/reference-openworld.json', self.reference)
        self.source.write_bytes(canonical_bytes(recipe))
        return build_catalog(self.root)

    def openworld_registry(self, catalog):
        # Eligibility is synthetic test data. It deliberately leaves newly seen
        # model900 in review; public schedule admission cannot depend on that review.
        return dict(schemaVersion=1, catalogVersion=catalog['catalogVersion'],
                    dictionaryDigest=hashlib.sha256(canonical_bytes(catalog['dictionaries'])).hexdigest(),
                    records={identity: dict(state='needs-review' if identity.endswith(':900') else 'current-evidence',
                        reason='Controlled lifecycle fixture', sources=[SOURCE], asOf='2026-11-13',
                        uncertainty='Synthetic fixture; no real current status asserted')
                        for identity in catalog['dictionaries']['configurations']})


    def scientific_reference(self):
        # Reuse the two actual source records required by the existing official
        # additions. Only artwork associations are removed for this small fixture;
        # no new LL2 provider records or identities are fabricated.
        source = loads_json((ROOT / 'openspec/changes/spacefox-watchface/evidence/global-catalog/reference-inventory.json').read_bytes())
        for table, identity, mapping in [('countries', 28, 'currentPackFlagId'),
                                         ('organizations', 37, 'currentPackBadgeId')]:
            row = copy.deepcopy(next(r for r in source[table] if r['sourceId'] == identity))
            row[mapping] = None
            self.reference[table].append(row)
        recipe = loads_json(self.source.read_bytes())
        recipe['reference'] = self.pin('catalog/reference-scientific.json', self.reference)
        self.source.write_bytes(canonical_bytes(recipe))
        return build_catalog(self.root)



    def test_a_scientific_rocket_missing_from_the_main_provider_positive(self):
        from tools.spacefox.catalog import dependency_closure
        from tools.spacefox.current_catalog import load_registry, current_view
        catalog = self.scientific_reference()
        self.assertFalse(any(r['facts']['name'] == 'S-520' for r in catalog['dictionaries']['configurations'].values()))
        value = self.openworld_fixture()['scientificSupplement']
        before = self.snapshot()
        revised = self.cli(value)
        rows = revised['dictionaries']
        model = rows['configurations']['spacefox:configuration:s520']
        site = rows['sites']['spacefox:site:uchinoura-sounding-area']
        self.assertEqual(model['facts']['name'], 'S-520')
        self.assertEqual(model['facts']['stages'], 1)
        self.assertEqual(model['facts']['officialLifecycle'], 'operating')
        self.assertEqual(model['facts']['officialLifecycleReviewedAt'], '2026-11-13')
        self.assertEqual(model['facts']['officialLifecycleSource'], 'https://www.isas.jaxa.jp/en/missions/sounding_rockets/')
        for row in (model, site):
            self.assertEqual(row['provenance'], [dict(source='curation', recordId='original-official-s520-review-20261113')])
            self.assertEqual(row['curation']['reviewedAt'], '2026-11-13')
            self.assertEqual(row['facts']['providerCoverage'], 'curator-addition-not-LL2-import')
            self.assertIsNone(row['facts']['providerActive'])
            self.assertEqual(row['curation']['sources'], [row['facts']['sourceUrl']])
        self.assertEqual(site['facts']['sourceUrl'], 'https://www.isas.jaxa.jp/en/missions/sounding_rockets/')
        self.assertIsNone(site['position'])
        self.assertIsNone(site['eventPosition'])
        selected = dependency_closure(revised, ['spacefox:configuration:s520', 'spacefox:site:uchinoura-sounding-area'],
                                      expected_revision=revised['catalogVersion'])
        self.assertEqual(selected['dictionaries']['configurations']['spacefox:configuration:s520']['provenance'], model['provenance'])
        for path, raw in before.items():
            if path != self.source:
                self.assertEqual(path.read_bytes(), raw)
        # Actual maintained source remains separate: its dated current decision
        # and original addition survive; today's isolated review does not rewrite it.
        actual = build_catalog(ROOT)
        registry = load_registry(ROOT, actual)
        current = current_view(actual, registry)
        self.assertIn('spacefox:configuration:s520', current['catalog']['dictionaries']['configurations'])
        self.assertEqual(registry['records']['spacefox:configuration:s520']['asOf'], '2026-11-12')
        recipe = loads_json((ROOT / 'catalog/source.json').read_bytes())
        reference = loads_json((ROOT / recipe['reference']['path']).read_bytes())
        self.assertFalse(any(r['name'] == 'S-520' for r in reference['models']))
        self.assertFalse(any(r['name'] == 'Uchinoura sounding-rocket launch area (pad unresolved)'
                             for r in reference['sites']))
        self.assertEqual(actual['dictionaries']['configurations']['spacefox:configuration:s520']['provenance'],
                         [dict(source='curation', recordId='global-curation-20261112')])
        self.assertEqual(actual['dictionaries']['sites']['spacefox:site:uchinoura-sounding-area']['provenance'],
                         [dict(source='curation', recordId='global-curation-20261112')])

    def test_a_scientific_rocket_missing_from_the_main_provider_negative(self):
        from tools.spacefox.catalog import dependency_closure
        self.scientific_reference()
        good = self.openworld_fixture()['scientificSupplement']
        accepted = self.cli(good)
        # A valid complete counterpart precedes the sole provenance/namespace
        # change. The rejected candidate is a guessed LL2 result with no source,
        # not a malformed model or missing asset standing in for false provenance.
        guessed = copy.deepcopy(good)
        guessed.update(id='unsourced-guess-as-ll2', sources=[])
        guessed['additions'] = [guessed['additions'][0]]
        guessed['additions'][0]['identity'] = 'll2:configuration:900'
        guessed['additions'][0]['facts'].update(sourceId=900, sourceUrl='', providerActive=True,
                                               providerCoverage='LL2-import')
        self.cli(guessed, error='primary HTTPS curation sources')
        # With a valid shared envelope it still cannot launder a curator's guess
        # into the provider namespace. The actual admission owner enforces this.
        guessed.update(id='guessed-provider-namespace', sources=good['sources'])
        self.cli(guessed, error='curated addition requires SpaceFox entity identity')
        forged = copy.deepcopy(accepted)
        model = forged['dictionaries']['configurations']['spacefox:configuration:s520']
        model['provenance'] = [dict(source='reference', recordId=900)]
        with self.assertRaisesRegex(CatalogError, 'curated provenance mismatch'):
            validate_catalog(forged)
        self.assertNotIn('ll2:configuration:900', build_catalog(self.root)['dictionaries']['configurations'])
        with self.assertRaisesRegex(CatalogError, 'unknown root'):
            dependency_closure(accepted, ['ll2:configuration:900'], expected_revision=accepted['catalogVersion'])
        self.assertEqual(build_catalog(self.root)['dictionaries']['configurations']['spacefox:configuration:s520']['provenance'],
                         [dict(source='curation', recordId='original-official-s520-review-20261113')])
