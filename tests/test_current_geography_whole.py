"""Bounded current SFR1M and retained typed-catalog geography witnesses.

The provider launch is a captured record; the separately sourced scientific
catalog entries are not asserted to be that launch or to have a known target.
"""
import copy
from datetime import datetime, timedelta, timezone
import tempfile
from pathlib import Path
import unittest

from tests.test_current_motion_publisher import NOW, captured_starship
from tests.test_global_catalog import temporary_catalog, supplement, save_revision
from tools.catalog import amend_recipe
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes, loads_json, validate_catalog
from tools.spacefox.graphics import VisualError, _validate_pack, build_pack, write_pack
from tools.spacefox.native_motion import build_artifact, read_ref, validate_artifact
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, merge_schedule

ROOT = Path(__file__).resolve().parents[1]


class CurrentGeographyWholeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        cls.record = normalize_launch(captured_starship(), NOW)
        cls.state = merge_schedule(ScheduleState(), (cls.record,), NOW)
        cls.publisher = dict(instance='a' * 64, generation=1, selectionValidatedUtc=NOW)
        cls.files, _ = build_artifact(cls.state, cls.catalog, NOW, publisher=cls.publisher, root=ROOT)
        cls.feed = validate_artifact(cls.files)
        cls.scene = loads_json(read_ref(cls.feed['visualSelection'], cls.files))

    def test_reviewed_typed_catalog_and_unknown_position(self):
        catalog = self.catalog
        identities = ['spacefox:configuration:s310', 'spacefox:configuration:s520', 'spacefox:configuration:ss520']
        for identity, stages in zip(identities, (1, 1, 2)):
            row = catalog['dictionaries']['configurations'][identity]
            self.assertEqual(row['facts']['stages'], stages)
            self.assertIsNone(row['facts']['providerActive'])
            self.assertTrue(row['curation']['sources'])
            self.assertEqual(row['curation']['reviewedAt'], '2026-11-12')
            pack = build_pack(ROOT, catalog, roots=[identity])
            self.assertEqual(pack['manifest']['selection']['roots'], [identity])
            self.assertEqual(pack['manifest']['selection']['dictionaries']['configurations'][identity], row)
            self.assertLessEqual(len(canonical_bytes(pack['manifest'])) + sum(map(len, pack['objects'].values())), 1048576)
        self.assertEqual(len(set(identities)), 3)
        site = catalog['dictionaries']['sites']['spacefox:site:esrange-sounding-area']
        self.assertIsNone(site['position'])
        self.assertTrue(site['curation']['sources'])

    def test_current_real_selection_and_unrelated_growth(self):
        feed, scene = self.feed, self.scene
        self.assertEqual((feed['schemaVersion'], feed['rendererProfile']), (3, 'SFR1M'))
        self.assertEqual((scene['launchId'], scene['modelId'], scene['operatorId'], scene['siteId']),
                         ('ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b', 'll2:configuration:522',
                          'll2:organization:121', 'll2:site:235'))
        self.assertEqual(scene['sourcePosition']['latitude'], '25.99677')
        self.assertEqual(scene['sourcePosition']['longitude'], '-97.15799')
        self.assertEqual(scene['positionMode'], 'fixed-source')
        self.assertEqual(scene['marker']['anchor'], [335, 165])
        self.assertEqual(feed['launch']['source_validated_utc'], NOW)
        self.assertLessEqual(sum(map(len, self.files.values())), 1048576)
        grown = copy.deepcopy(self.catalog)
        site = copy.deepcopy(grown['dictionaries']['sites']['spacefox:site:esrange-sounding-area'])
        site['facts']['sourceId'] = 'unrelated-context-site'
        grown['dictionaries']['sites']['spacefox:site:unrelated-context-site'] = site
        validate_catalog(grown)
        files, _ = build_artifact(self.state, grown, NOW, publisher=self.publisher, root=ROOT)
        other_feed = validate_artifact(files)
        other = loads_json(read_ref(other_feed['visualSelection'], files))
        for key in ('launchId', 'modelId', 'operatorId', 'siteId', 'countryId', 'sourcePosition', 'position', 'positionMode', 'marker'):
            self.assertEqual(scene[key], other[key], key)
        self.assertLessEqual(sum(map(len, files.values())), 1048576)

    def test_sixteen_actual_asset_roots_and_refusals(self):
        # The fixed real seed roots are bounded at the production selection
        # owner. This is not the retired bundle or a native retention test.
        tokens = ('falcon-9', 'falcon-heavy', 'electron', 'ariane-62', 'ariane-64', 'generic',
                  'vehicle-pslv-standard', 'vehicle-pslv-xl', 'vehicle-pslv-ca', 'vehicle-pslv-dl',
                  'vehicle-pslv-ql', 'vehicle-gslv-mk2', 'vehicle-lvm3', 'vehicle-sslv',
                  'vehicle-h3-30', 'vehicle-h3-22')
        assets = ['spacefox:asset:' + token for token in tokens[:14]]
        model = 'spacefox:configuration:s310'
        visual = 'spacefox:asset:vehicle-s310'
        roots = assets + [model, visual]
        pack = build_pack(ROOT, self.catalog, roots=roots)
        self.assertEqual(pack['manifest']['selection']['roots'], sorted(roots))
        self.assertTrue(set(assets + [visual]) <= set(pack['manifest']['assets']))
        self.assertEqual(pack['manifest']['selection']['dictionaries']['configurations'][model]['references']['visual'], visual)
        referenced = {part['sha256'] for asset in pack['manifest']['assets'].values() for part in asset['shards']}
        self.assertEqual(set(pack['objects']), referenced)
        self.assertLessEqual(len(canonical_bytes(pack['manifest'])), 65536)
        self.assertLessEqual(len(canonical_bytes(pack['manifest'])) + sum(map(len, pack['objects'].values())), 1048576)
        _validate_pack(pack)
        with self.assertRaises(VisualError):
            build_pack(ROOT, self.catalog, roots=roots + ['spacefox:asset:vehicle-h3-24'])
        for defect in ('root', 'asset-envelope', 'provenance'):
            bad = copy.deepcopy(pack)
            if defect == 'root':
                bad['manifest']['selection']['roots'][0] = 'spacefox:asset:missing'
            elif defect == 'asset-envelope':
                bad['manifest']['assets'][assets[0]]['units'] = 1.0
            else:
                bad['manifest']['assets'][assets[0]]['catalogRecord']['provenance'] = []
            with self.subTest(defect=defect), self.assertRaises((VisualError, CatalogError)):
                _validate_pack(bad)

    def test_source_extension_and_reopen_corrections(self):
        identity = 'll2:configuration:164'
        catalog = copy.deepcopy(self.catalog)
        row = catalog['dictionaries']['configurations'][identity]
        extension = {'flag': False, 'missing': None}
        row['facts']['providerExtension'] = copy.deepcopy(extension)
        if 'originalFacts' in row:
            row['originalFacts']['providerExtension'] = copy.deepcopy(extension)
        validate_catalog(catalog)
        pack = build_pack(ROOT, catalog, roots=[identity])
        selected = pack['manifest']['selection']['dictionaries']['configurations'][identity]
        self.assertEqual(selected['facts']['providerExtension'], extension)
        self.assertEqual(selected.get('originalFacts', selected['facts'])['providerExtension'], extension)
        self.assertEqual(selected['references']['origin'], row['references']['origin'])
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            recipe = root / 'catalog/source.json'
            original = build_catalog(root)['dictionaries']['configurations'][identity]
            source = 'https://www.mhi.com/business/products-services/space-defense/launch-service/launch-vehicles'
            history = []
            store = root / 'selected'
            for index in (1, 2):
                value = supplement('technical-retain-' + str(index))
                value['sources'] = [source]
                patch = {'name': original['facts']['name']}
                value['updates'] = [dict(identity=identity, changes=patch, sources=[source])]
                current = amend_recipe(root, recipe, save_revision(root, value, 'step' + str(index) + '.json'), 'technical.retain.' + str(index))
                history.append(dict(id=value['id'], changes=patch, sources=[source]))
                reopened = build_catalog(root)
                current_row = reopened['dictionaries']['configurations'][identity]
                self.assertEqual(current_row['facts'], current['dictionaries']['configurations'][identity]['facts'])
                self.assertEqual(current_row['originalFacts'], original.get('originalFacts', original['facts']))
                self.assertEqual(current_row['curationHistory'][-2 if index == 2 else -1:], history)
                selected_pack = build_pack(root, reopened, roots=[identity])
                write_pack(store, selected_pack)
                self.assertEqual(selected_pack['manifest']['selection']['dictionaries']['configurations'][identity], current_row)
            before = recipe.read_bytes()
            accepted = {p.relative_to(store): p.read_bytes() for p in store.rglob('*') if p.is_file()}
            bad = supplement('technical-identity-refusal')
            bad['updates'] = [dict(identity=identity, changes={'sourceId': current_row['facts']['sourceId']}, sources=[source])]
            with self.assertRaises(CatalogError):
                amend_recipe(root, recipe, save_revision(root, bad, 'bad.json'), 'technical.invalid')
            self.assertEqual(recipe.read_bytes(), before)
            self.assertEqual({p.relative_to(store): p.read_bytes() for p in store.rglob('*') if p.is_file()}, accepted)
            self.assertEqual(build_catalog(root)['dictionaries']['configurations'][identity], current_row)

    def test_selected_source_identity_history_refusals(self):
        identity = 'll2:configuration:164'
        row = self.catalog['dictionaries']['configurations'][identity]
        pack = build_pack(ROOT, self.catalog, roots=[identity])
        for defect in ('source-id', 'history-id'):
            altered = copy.deepcopy(pack)
            selected_row = altered['manifest']['selection']['dictionaries']['configurations'][identity]
            if defect == 'source-id':
                selected_row.setdefault('curation', {}).setdefault('changes', {})['sourceId'] = row['facts']['sourceId']
            else:
                selected_row.setdefault('curationHistory', []).append({'id': 'not an identity token', 'changes': {}, 'sources': ['https://example.invalid/']})
            with self.subTest(defect=defect), self.assertRaises((CatalogError, VisualError)):
                _validate_pack(altered)

    def test_current_sfr_source_extension_preserved(self):
        # Technical raw extension is not a reviewed lifecycle assertion or a
        # new display label. It travels with the captured launch's real model.
        catalog = copy.deepcopy(self.catalog)
        row = catalog['dictionaries']['configurations']['ll2:configuration:522']
        extension = {'flag': False, 'missing': None}
        row['facts']['providerExtension'] = copy.deepcopy(extension)
        row['facts']['officialLifecycle'] = 'raw-provider-extension'
        if 'originalFacts' in row:
            row['originalFacts']['providerExtension'] = copy.deepcopy(extension)
            row['originalFacts']['officialLifecycle'] = 'raw-provider-extension'
        files, _ = build_artifact(self.state, catalog, NOW, publisher=self.publisher, root=ROOT)
        feed = validate_artifact(files)
        scene = loads_json(read_ref(feed['visualSelection'], files))
        source = loads_json(files[scene['origins']['model']['sourceRecord']['path']])
        self.assertEqual(source['ownerId'], 'll2:configuration:522')
        self.assertEqual(source['owner']['facts']['providerExtension'], extension)
        self.assertEqual(source['owner']['facts']['officialLifecycle'], 'raw-provider-extension')
        self.assertEqual(source['owner']['originalFacts']['officialLifecycle'], 'raw-provider-extension')
        self.assertEqual(source['catalogSelection']['dictionaries']['configurations']['ll2:configuration:522'], source['owner'])
        self.assertEqual(source['owner']['references']['origin'], self.catalog['dictionaries']['configurations']['ll2:configuration:522']['references']['origin'])
        self.assertLessEqual(sum(map(len, files.values())), 1048576)

    def test_future_typed_creation_refuses_atomically(self):
        # Use a real row as technical input, with no inherited origin review:
        # the unrelated creation cannot claim that existing source's review.
        row = self.catalog['dictionaries']['configurations']['spacefox:configuration:miura9']
        facts, refs = copy.deepcopy(row['facts']), copy.deepcopy(row['references'])
        for field in list(facts):
            if field.startswith('curatedOrigin'):
                del facts[field]
        refs['origin'] = None
        future = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()
        source = 'https://official.example/independent-review'
        facts.update(sourceId='technical-future-review', officialLifecycle='retired',
                     officialLifecycleSource=source, officialLifecycleReviewedAt=future,
                     officialLifecycleNote='Technical admission test.')
        value = supplement('technical-future-review')
        value['reviewedAt'] = future
        value['sources'] = [source]
        value['additions'] = [dict(identity='spacefox:configuration:technical-future-review', facts=facts, references=refs)]
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            recipe = root / 'catalog/source.json'
            before = recipe.read_bytes()
            with self.assertRaisesRegex(CatalogError, 'official lifecycle review cannot postdate'):
                amend_recipe(root, recipe, save_revision(root, value), 'technical.future.review')
            self.assertEqual(recipe.read_bytes(), before)
            self.assertFalse(list((root / 'catalog').glob('.recipe-*')))

    def test_typed_creation_rejects_actual_guard_failures(self):
        source = 'https://official.example/independent-review'
        model = self.catalog['dictionaries']['configurations']['spacefox:configuration:miura9']
        site = self.catalog['dictionaries']['sites']['ll2:site:65']
        base = dict(officialLifecycle='retired', officialLifecycleSource=source,
                    officialLifecycleReviewedAt='2026-11-12', officialLifecycleNote='Technical admission test.')
        cases = [('state', {'officialLifecycle': True}, 'invalid official lifecycle state'),
                 ('date', {'officialLifecycleReviewedAt': '2026-02-30'}, 'invalid official lifecycle review date'),
                 ('source', {'officialLifecycleSource': source + '/other'}, 'official lifecycle source must belong'),
                 ('collection', {}, 'curated field belongs to another collection')]
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            recipe = root / 'catalog/source.json'
            before = recipe.read_bytes()
            for label, patch, reason in cases:
                source_row = site if label == 'collection' else model
                facts, refs = copy.deepcopy(source_row['facts']), copy.deepcopy(source_row['references'])
                for field in list(facts):
                    if field.startswith('curatedOrigin'):
                        del facts[field]
                if label != 'collection':
                    refs['origin'] = None
                token = 'technical-creation-' + label
                facts.update(sourceId=token, sourceUrl=source, **base)
                facts.update(patch)
                value = supplement(token)
                value['sources'] = [source]
                kind = 'site' if label == 'collection' else 'configuration'
                value['additions'] = [dict(identity='spacefox:' + kind + ':' + token, facts=facts, references=refs)]
                with self.subTest(defect=label), self.assertRaisesRegex(CatalogError, reason):
                    amend_recipe(root, recipe, save_revision(root, value, token + '.json'), 'technical.' + label)
                self.assertEqual(recipe.read_bytes(), before)

    def test_source_integrity_and_typed_refusal(self):
        bad = copy.deepcopy(self.catalog)
        bad['dictionaries']['configurations']['spacefox:configuration:s310']['references']['manufacturer'] = 'll2:organization:121'
        with self.assertRaises(CatalogError):
            validate_catalog(bad)
        altered = dict(self.files)
        path = self.scene['mapSource']['corresponding']['path']
        altered[path] += b' '
        with self.assertRaises(ValueError):
            validate_artifact(altered)
        self.assertEqual(validate_artifact(self.files), self.feed)

    def test_readdressed_selected_source_contract_refusals(self):
        # Re-pin every ancestor and sidecar: digest rejection must not mask
        # the source-selection identity and reachability checks.
        import hashlib
        from tools.spacefox.native_motion import _index, with_text_transport

        target = self.scene['siteCountrySource']['path']
        def rewrite(mutate):
            rebuilt, memo = {}, {}
            def walk(row):
                if isinstance(row, list):
                    return [walk(v) for v in row]
                if not isinstance(row, dict):
                    return row
                if set(row) == {'path', 'sha256', 'decodedBytes'}:
                    return document(row['path'])
                row = {k: walk(v) for k, v in row.items()}
                if 'catalogPath' in row:
                    pin = document(row['catalogPath'])
                    row.update(catalogPath=pin['path'], catalogDigest=pin['sha256'])
                return row
            def document(path):
                if path in memo:
                    return memo[path]
                raw = self.files[path]
                if path.endswith('.json'):
                    row = walk(loads_json(raw))
                    if isinstance(row, dict) and row.get('type') == 'native-transfer':
                        row = _index(rebuilt, row['scene'])
                    if path == target:
                        mutate(row['catalogSelection'])
                    raw = canonical_bytes(row)
                digest = hashlib.sha256(raw).hexdigest()
                name = 'feed.json' if path == 'feed.json' else path.rsplit('/', 1)[0] + '/' + digest + Path(path).suffix
                rebuilt[name] = raw
                memo[path] = dict(path=name, sha256=digest, decodedBytes=len(raw))
                return memo[path]
            document('feed.json')
            return with_text_transport(rebuilt)

        self.assertEqual(rewrite(lambda selection: None), self.files)
        def root(selection):
            selection['roots'] = []
        def provenance(selection):
            selection['dictionaries']['sites']['ll2:site:235']['provenance'][0]['recordId'] = '235'
        def jurisdiction(selection):
            selection['dictionaries']['countries']['ll2:country:2']['jurisdictionKind'] = 'territory'
        def event_position(selection):
            selection['dictionaries']['sites']['ll2:site:235']['eventPosition'] = {'latitude': 0, 'longitude': 0}
        for label, mutation, reason in (
                ('root', root, 'empty/duplicate catalog roots'),
                ('provenance', provenance, 'source provenance mismatch'),
                ('jurisdiction', jurisdiction, 'reference does not qualify a jurisdiction classification'),
                ('event-position', event_position, 'event position not qualified')):
            with self.subTest(defect=label), self.assertRaisesRegex(ValueError, reason):
                validate_artifact(rewrite(mutation))
