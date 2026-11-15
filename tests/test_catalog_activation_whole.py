"""Current catalogue identity and coordinate controls using captured source facts."""
import copy
from decimal import Decimal
from pathlib import Path
import unittest
from tests.public_proof_inputs import recorded_input
from tests.public_proof_inputs import verify_current_closure as verify_current

from tests.test_current_motion_publisher import NOW, captured_starship
from tools.spacefox.catalog import CatalogError, build_catalog, validate_catalog
from tools.spacefox.native_motion import build_artifact, validate_artifact
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, merge_schedule

ROOT = Path(__file__).resolve().parents[1]

class CatalogActivationWholeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)

    def unknown(self):
        row = captured_starship()
        row['rocket']['configuration']['id'] = 999999
        record = normalize_launch(row, NOW)
        state = merge_schedule(ScheduleState(), (record,), NOW)
        files, _ = build_artifact(state, self.catalog, NOW, publisher={
            'instance': 'a' * 64, 'generation': 1, 'selectionValidatedUtc': NOW}, root=ROOT)
        feed = validate_artifact(files)
        import json
        scene = json.loads(files[feed['visualSelection']['path']])
        return row, feed, scene

    def test_catalog_identity_attribution_and_asset_version(self):
        self.assertEqual(self.catalog['schemaVersion'], 1)
        self.assertTrue(self.catalog['catalogVersion'])
        validate_catalog(self.catalog)
        for table, rows in self.catalog['dictionaries'].items():
            for identity, row in rows.items():
                self.assertTrue(identity.startswith(('ll2:', 'spacefox:')), identity)
                self.assertTrue(row['provenance'], identity)
                self.assertTrue(row['kind'] and isinstance(row['facts'], dict), identity)
        model = self.catalog['dictionaries']['configurations']['ll2:configuration:479']
        self.assertEqual((model['kind'], model['facts']['sourceId'], model['facts']['fullName']),
                         ('configuration', 479, 'Vulcan VC6L'))
        self.assertEqual(model['provenance'][0], {'source': 'reference', 'recordId': 479})
        self.assertEqual(model['references']['visual'], 'spacefox:asset:vehicle-vulcan-6l')
        asset = self.catalog['dictionaries']['assets'][model['references']['visual']]
        self.assertEqual(asset['facts']['coverage']['configurationIds'], ['ll2:configuration:479'])
        self.assertEqual(asset['facts']['license'], 'MIT')
        self.assertTrue(asset['facts']['creator'] and asset['facts']['sources'])
        self.assertEqual(len(asset['content']['sha256']), 64)
        site = self.catalog['dictionaries']['sites']['ll2:site:29']
        self.assertEqual((site['facts']['name'], site['facts']['locationName']),
                         ('Space Launch Complex 41', 'Cape Canaveral SFS, FL, USA'))
        self.assertEqual(site['references']['country'], 'll2:country:2')
        self.assertEqual(site['position']['qualification'], 'unverified-reference')

    def test_unknown_typed_configuration_positive(self):
        row, feed, scene = self.unknown()
        self.assertEqual(feed['launch']['configuration_id'], 'll2:configuration:999999')
        self.assertEqual(feed['launch']['configuration_name'], row['rocket']['configuration']['full_name'])
        self.assertIn('ll2:configuration:999999', feed['unresolvedCatalogIds'])
        self.assertIsNone(scene['roles']['rocket'])

    def test_unknown_typed_configuration_negative(self):
        row, feed, scene = self.unknown()
        self.assertTrue(row['rocket']['configuration'].get('families'))
        self.assertIsNone(scene['roles']['rocket'])
        self.assertEqual(feed['launch']['configuration_name'], row['rocket']['configuration']['full_name'])

    def coordinate_catalog(self, lat, lon):
        c = copy.deepcopy(self.catalog)
        site = c['dictionaries']['sites']['ll2:site:29']
        site['facts']['latitude'], site['facts']['longitude'] = lat, lon
        site['position']['latitude'], site['position']['longitude'] = lat, lon
        return c

    def test_real_site_zero_coordinates_positive(self):
        c = self.coordinate_catalog(Decimal('0'), Decimal('0'))
        validate_catalog(c)
        position = c['dictionaries']['sites']['ll2:site:29']['position']
        self.assertEqual((position['latitude'], position['longitude']), (0, 0))
        self.assertEqual(position['qualification'], 'unverified-reference')
        self.assertEqual(c['dictionaries']['sites']['ll2:site:29']['references']['country'], 'll2:country:2')

    def test_real_site_invalid_coordinates_negative(self):
        for lat, lon in ((Decimal('NaN'), 0), (0, Decimal('Infinity')),
                         (Decimal('90.001'), 0), (0, Decimal('180.001')), (None, 0)):
            with self.subTest(lat=lat, lon=lon), self.assertRaises(CatalogError):
                validate_catalog(self.coordinate_catalog(lat, lon))
        c = copy.deepcopy(self.catalog)
        unknown = next(row for row in c['dictionaries']['sites'].values() if row['position'] is None)
        self.assertIsNone(unknown['position'])
        validate_catalog(c)

    def test_selected_manifest_ignores_real_unrelated_growth(self):
        import json
        small = copy.deepcopy(self.catalog)
        removed = small['dictionaries']['assets'].pop('spacefox:asset:vehicle-spaceshiptwo')
        self.assertEqual(removed, self.catalog['dictionaries']['assets']['spacefox:asset:vehicle-spaceshiptwo'])
        validate_catalog(small)
        record = normalize_launch(captured_starship(), NOW)
        state = merge_schedule(ScheduleState(), (record,), NOW)
        envelope = {'instance': 'a' * 64, 'generation': 1, 'selectionValidatedUtc': NOW}
        before, _ = build_artifact(state, small, NOW, publisher=envelope, root=ROOT)
        after, _ = build_artifact(state, self.catalog, NOW, publisher=envelope, root=ROOT)
        a, b = json.loads(before['feed.json']), json.loads(after['feed.json'])
        # Full catalog provenance is intentionally pinned; its changed digest
        # repins ancestors, but the selected manifest must not grow.
        self.assertNotEqual(a['catalogSourceDigest'], b['catalogSourceDigest'])
        self.assertEqual(a['visualSelection']['decodedBytes'], b['visualSelection']['decodedBytes'])
        self.assertEqual(a['nativeTransfer']['decodedBytes'], b['nativeTransfer']['decodedBytes'])
        selected_a = json.loads(before[a['visualSelection']['path']])
        selected_b = json.loads(after[b['visualSelection']['path']])
        for key in ('launchId', 'modelId', 'siteId', 'countryId', 'position', 'rendererProfile', 'layoutRevision'):
            self.assertEqual(selected_a[key], selected_b[key], key)
        rows_a = json.loads(before[a['nativeTransfer']['path']])['objects']
        rows_b = json.loads(after[b['nativeTransfer']['path']])['objects']
        self.assertEqual([(k, size) for k, _, size in rows_a], [(k, size) for k, _, size in rows_b])
        index = json.loads(after[b['nativeTransfer']['path']])
        self.assertLessEqual(len(index['objects']), 40)
        self.assertTrue(all(0 < size <= 4096 for _, _, size in index['objects']))
        validate_artifact(before)
        validate_artifact(after)

    def test_current_artifact_integrity_and_missing_files(self):
        import json
        from tools.spacefox.catalog import canonical_bytes
        record = normalize_launch(captured_starship(), NOW)
        state = merge_schedule(ScheduleState(), (record,), NOW)
        files, _ = build_artifact(state, self.catalog, NOW, publisher={
            'instance': 'a' * 64, 'generation': 1, 'selectionValidatedUtc': NOW}, root=ROOT)
        accepted = validate_artifact(files)
        self.assertEqual((accepted['schemaVersion'], accepted['rendererProfile']), (3, 'SFR1M'))
        old = dict(files)
        raster = next(path for path in files if path.startswith('rasters/'))
        for mode in ('missing', 'corrupt', 'unsupported'):
            candidate = dict(files)
            if mode == 'missing':
                del candidate[raster]
                del candidate[raster + '.txt']
            elif mode == 'corrupt':
                candidate[raster] += b'x'
                candidate[raster + '.txt'] = candidate[raster]
            else:
                feed = json.loads(candidate['feed.json'])
                feed['schemaVersion'] = 4
                candidate['feed.json'] = canonical_bytes(feed)
                candidate['feed.json.txt'] = candidate['feed.json']
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                validate_artifact(candidate)
            self.assertEqual(files, old)
            self.assertEqual(validate_artifact(files)['catalogDigest'], accepted['catalogDigest'])

class CurrentSdkSceneReceiptTest(unittest.TestCase):
    def test_same_package_replacement_and_restart(self):
        import hashlib
        import json
        verify_current()
        path = ROOT / 'openspec/changes/spacefox-watchface/evidence/catalog-activation-whole/sdk-r2'
        build = json.loads((path / 'build.json').read_text())
        sha = lambda raw: hashlib.sha256(raw).hexdigest()
        self.assertEqual(sha((path / 'Probe.mc').read_bytes()), build['probeSha256'])
        for name, expected in {**build['productionSources'], **build['productionResources']}.items():
            self.assertEqual(sha(recorded_input(name, expected)), expected, name)
        for name, expected in build['probeResources'].items():
            self.assertEqual(sha((path / 'probe-resources' / name).read_bytes()), expected, name)
        feeds = {label: json.loads(json.loads((path / 'probe-resources' / ('Feed'+label+'.json')).read_bytes())['raw']) for label in ('A', 'B')}
        self.assertEqual([feeds[x]['publisher']['generation'] for x in ('A', 'B')], [1, 2])
        self.assertEqual([feeds[x]['publisher']['selectionValidatedUtc'] for x in ('A', 'B')], [NOW, NOW])
        objects = {}
        for file in (path / 'probe-resources').glob('Obj*.json'):
            item = json.loads(file.read_bytes()); raw = item['raw'].encode()
            self.assertEqual(sha(raw), item['ref']['sha256'])
            self.assertEqual(len(raw), item['ref']['decodedBytes'])
            objects[item['ref']['path']] = raw
        pixels = []
        for label, latitude in (('A', '25.99677'), ('B', '26.99677')):
            feed = feeds[label]
            scene = json.loads(objects[feed['visualSelection']['path']])
            self.assertEqual(scene['position']['latitude'], latitude)
            self.assertEqual(scene['launchId'], 'll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b')
            rocket = json.loads(objects[scene['roles']['rocket']['descriptor']['path']])
            pixels.append(rocket['pixelSha256'])
        self.assertEqual(pixels, ['15395365f81866ada8f35c360baa648fb7621b9a0e15052c2dfe5562ae8eacba',
                                  '7226fcead839ac92bd84dd92dc2b0c0991a60719e49cab00b0426d91f1ff7790'])
        for phase, stage, label, no_write in ((1, 1, 'A', 'false'), (2, 11, 'A', 'true'),
                                              (3, 21, 'B', 'false'), (4, 31, 'B', 'true')):
            log = (path / ('phase%d.log' % phase)).read_text()
            self.assertIn('CAT_PHASE stage=%d generation=%d selected=%s' %
                          (stage, feeds[label]['publisher']['generation'], feeds[label]['visualSelection']['sha256']), log)
            self.assertIn('fullScene=true reopenNoWrites='+no_write, log)
            self.assertNotIn('CAT_FAIL', log)
            if phase > 1:
                self.assertIn('push=false', log)
                self.assertEqual((path / ('phase%d.exit' % phase)).read_text().strip(), '0')
        for prefix in ('', 'b-'):
            before = (path / (prefix+'before-restart.sha256')).read_text()
            self.assertEqual(before, (path / (prefix+'after-restart.sha256')).read_text())
            self.assertEqual(before, (path / (prefix+'after-read.sha256')).read_text())
            self.assertEqual(len(before.splitlines()), 3)

    def test_incomplete_corrupt_scene_and_retry(self):
        import hashlib
        import json
        verify_current()
        path = ROOT / 'openspec/changes/spacefox-watchface/evidence/catalog-activation-whole/sdk-negative'
        build = json.loads((path / 'build.json').read_text())
        sha = lambda raw: hashlib.sha256(raw).hexdigest()
        self.assertEqual(sha((path / 'Probe.mc').read_bytes()), build['probeSha256'])
        for name, expected in {**build['productionSources'], **build['productionResources']}.items():
            self.assertEqual(sha(recorded_input(name, expected)), expected, name)
        for name, expected in build['probeResources'].items():
            self.assertEqual(sha((path / 'probe-resources' / name).read_bytes()), expected, name)
        rows = [json.loads(p.read_bytes()) for p in (path / 'probe-resources').glob('ObjB*.json')]
        selected = [x for x in rows if x['ref']['path'] == build['missing']]
        self.assertEqual(len(selected), 1)
        self.assertEqual(sha(selected[0]['raw'].encode()), selected[0]['ref']['sha256'])
        log = (path / 'run.log').read_text()
        self.assertIn('NEG_EXPECTED missingObject=Invalid SFR1 raster', log)
        self.assertIn('NEG_COMPLETE corruptRejected=true missingRefused=true priorPointerPreserved=true '
                      'freshBContext=true noOldBitmap=true retryB=true recoveryA=true', log)
        self.assertNotIn('NEG_FAIL', log)
        # The ordinary launcher timed out after the explicit completion marker.
        self.assertEqual((path / 'run.exit').read_text().strip(), '124')

    def test_bounded_native_batch_receipt(self):
        import hashlib
        import json
        verify_current()
        path = ROOT / 'openspec/changes/spacefox-watchface/evidence/catalog-activation-whole/sdk-batch'
        build = json.loads((path / 'build.json').read_text())
        sha = lambda raw: hashlib.sha256(raw).hexdigest()
        self.assertEqual(sha((path / 'Probe.mc').read_bytes()), build['probeSha256'])
        for name, expected in {**build['productionSources'], **build['productionResources']}.items():
            self.assertEqual(sha(recorded_input(name, expected)), expected, name)
        for name, expected in build['probeResources'].items():
            self.assertEqual(sha((path / 'probe-resources' / name).read_bytes()), expected, name)
        objects = {}
        for file in (path / 'probe-resources').glob('Obj*.json'):
            item = json.loads(file.read_bytes()); raw = item['raw'].encode()
            self.assertEqual(sha(raw), item['sha256'])
            self.assertLessEqual(len(raw), 4096)
            objects[item['path']] = raw
        feed = json.loads(json.loads((path / 'probe-resources/Feed.json').read_bytes())['raw'])
        index = json.loads(objects[feed['nativeTransfer']['path']])
        expected_paths = {feed['catalogPath'], feed['nativeTransfer']['path']}
        for kind, digest, size in index['objects']:
            name = ('rasters/' + digest + '.sfr') if kind == 1 else ('descriptors/' + digest + '.json')
            self.assertEqual(len(objects[name]), size)
            self.assertEqual(sha(objects[name]), digest)
            expected_paths.add(name)
        self.assertLessEqual(len(index['objects']), 40)
        self.assertEqual(set(objects), expected_paths)
        self.assertEqual(sorted(objects), build['selectedPaths'])
        self.assertEqual(len(objects), 18)
        log = (path / 'run.log').read_text()
        self.assertIn('BATCH_COMPLETE fetched=18 expected=18 exactSelectedOnly=true noGlobalManifest=true unboundedIndexRefused=true', log)
        self.assertNotIn('BATCH_FAIL', log)
        self.assertEqual((path / 'run.exit').read_text().strip(), '124')

    def test_current_native_scene_and_motion_grammar_receipt(self):
        import hashlib
        import json
        import tempfile
        from tools import generate_native_current_tests as gen
        from tools.run_native_tests import parse_output
        verify_current()
        path = ROOT / 'openspec/changes/spacefox-watchface/evidence/catalog-activation-whole/sdk-grammar'
        source = ROOT / 'openspec/changes/spacefox-watchface/evidence/catalog-activation-whole/sdk-r2/probe-resources'
        build = json.loads((path / 'build.json').read_text())
        sha = lambda raw: hashlib.sha256(raw).hexdigest()
        for name, expected in {**build['productionSources'], **build['productionResources']}.items():
            self.assertEqual(sha(recorded_input(name, expected)), expected, name)
        with tempfile.TemporaryDirectory() as tmp:
            profile = Path(tmp)
            feed = json.loads((source / 'FeedA.json').read_bytes())['raw'].encode()
            (profile / 'feed.json').write_bytes(feed)
            for file in source.glob('ObjA*.json'):
                row = json.loads(file.read_bytes()); raw = row['raw'].encode()
                self.assertEqual(sha(raw), row['ref']['sha256'])
                target = profile / row['ref']['path']; target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(raw)
            generated = gen.source(profile)
            for name in gen.EXPECTED:
                if name not in ('currentSceneGrammar', 'currentMotionGrammar'):
                    generated = generated.replace('(:test,:typecheck(false)) function '+name,
                                                  '(:typecheck(false)) function '+name)
            self.assertEqual((path / 'Probe.mc').read_text(), generated)
        self.assertEqual(sha((path / 'Probe.mc').read_bytes()), build['probeSha256'])
        log = (path / 'run.log').read_text()
        result = parse_output(log, int((path / 'run.exit').read_text()),
                              ('currentSceneGrammar', 'currentMotionGrammar'))
        self.assertEqual(result['status'], 'passed')
        self.assertIn('rehashedSchemaProfileOriginNegatives=6 noActivation=true', log)
        self.assertIn('rehashedCanvasProvenanceTimelineNegatives=5 noActivation=true', log)

    def test_interrupted_scene_survives_no_push_restart(self):
        import hashlib
        import json
        verify_current()
        path = ROOT / 'openspec/changes/spacefox-watchface/evidence/catalog-activation-whole/sdk-interrupted'
        build = json.loads((path / 'build.json').read_text())
        sha = lambda raw: hashlib.sha256(raw).hexdigest()
        self.assertEqual(sha((path / 'Probe.mc').read_bytes()), build['probeSha256'])
        for name, expected in {**build['productionSources'], **build['productionResources']}.items():
            self.assertEqual(sha(recorded_input(name, expected)), expected, name)
        for name, expected in build['probeResources'].items():
            self.assertEqual(sha((path / 'probe-resources' / name).read_bytes()), expected, name)
        first = (path / 'phase1.log').read_text(); second = (path / 'phase2.log').read_text()
        self.assertIn('NEG_INTERRUPT preparedB=true activeA=true missing=true', first)
        self.assertIn('push=false', second)
        self.assertIn('NEG_EXPECTED missingObject=Invalid SFR1 raster', second)
        self.assertIn('NEG_COMPLETE corruptRejected=true missingRefused=true priorPointerPreserved=true '
                      'freshBContext=true noOldBitmap=true retryB=true recoveryA=true', second)
        self.assertNotIn('NEG_FAIL', first + second)
        self.assertEqual((path / 'before-restart.sha256').read_text(),
                         (path / 'after-restart.sha256').read_text())
        self.assertEqual(len((path / 'before-restart.sha256').read_text().splitlines()), 3)
        self.assertEqual((path / 'phase2.exit').read_text().strip(), '0')

    def test_native_settings_and_host_selection(self):
        import hashlib
        import json
        verify_current()
        path = ROOT / 'openspec/changes/spacefox-watchface/evidence/catalog-activation-whole/sdk-settings'
        build = json.loads((path / 'build.json').read_text())
        sha = lambda raw: hashlib.sha256(raw).hexdigest()
        self.assertEqual(sha((path / 'Probe.mc').read_bytes()), build['probeSha256'])
        for name, expected in {**build['productionSources'], **build['productionResources']}.items():
            self.assertEqual(sha(recorded_input(name, expected)), expected, name)
        for name, expected in build['probeResources'].items():
            self.assertEqual(sha((path / 'probe-resources' / name).read_bytes()), expected, name)
        probe = (path / 'Probe.mc').read_text()
        self.assertIn('"battery","calories","heart","steps"', probe)
        self.assertIn('https://first.invalid/site/feed.json.txt', probe)
        self.assertIn('https://second.invalid/site/feed.json.txt', probe)
        log = (path / 'run.log').read_text()
        self.assertIn('fourSettingsPreserved=true twoHosts=true', log)
        self.assertIn('retryB=true recoveryA=true', log)
        self.assertNotIn('NEG_FAIL', log)
        self.assertEqual((path / 'run.exit').read_text().strip(), '124')

    def test_stale_immutable_bytes_are_refused(self):
        import hashlib
        import json
        import re
        verify_current()
        path = ROOT / 'openspec/changes/spacefox-watchface/evidence/catalog-activation-whole/sdk-skew'
        build = json.loads((path / 'build.json').read_text())
        sha = lambda raw: hashlib.sha256(raw).hexdigest()
        probe = (path / 'Probe.mc').read_text()
        self.assertEqual(sha(probe.encode()), build['probeSha256'])
        for name, expected in {**build['productionSources'], **build['productionResources']}.items():
            self.assertEqual(sha(recorded_input(name, expected)), expected, name)
        for name, expected in build['probeResources'].items():
            self.assertEqual(sha((path / 'probe-resources' / name).read_bytes()), expected, name)
        match = re.search(r'WatchUi\.loadResource\(Rez\.JsonData\.(ObjA\d+)\)\["raw"\]', probe)
        self.assertIsNotNone(match)
        old = json.loads((path / 'probe-resources' / (match.group(1)+'.json')).read_bytes())
        new = next(json.loads(p.read_bytes()) for p in (path / 'probe-resources').glob('ObjB*.json')
                   if json.loads(p.read_bytes())['ref']['path'] == build['missing'])
        self.assertEqual(sha(old['raw'].encode()), old['ref']['sha256'])
        self.assertNotEqual(sha(old['raw'].encode()), new['ref']['sha256'])
        self.assertIn('reject old CDN bytes for new digest', probe)
        log = (path / 'run.log').read_text()
        self.assertIn('oldBytesRefused=true', log)
        self.assertIn('priorPointerPreserved=true', log)
        self.assertNotIn('NEG_FAIL', log)
        self.assertEqual((path / 'run.exit').read_text().strip(), '124')

    def test_raster_pointer_write_faults(self):
        import hashlib
        import json
        verify_current()
        path = ROOT / 'openspec/changes/spacefox-watchface/evidence/catalog-activation-whole/sdk-raster-fault'
        build = json.loads((path / 'build.json').read_text())
        sha = lambda raw: hashlib.sha256(raw).hexdigest()
        probe = (path / 'Probe.mc').read_text()
        self.assertEqual(sha(probe.encode()), build['probeSha256'])
        for name, expected in {**build['productionSources'], **build['productionResources']}.items():
            self.assertEqual(sha(recorded_input(name, expected)), expected, name)
        for name, expected in build['probeResources'].items():
            self.assertEqual(sha((path / 'probe-resources' / name).read_bytes()), expected, name)
        self.assertIn('store.failKey="sf.raster.recovery"', probe)
        self.assertIn('"sf.raster.active":null', probe)
        self.assertIn('ensure(store.fired,"fault reached")', probe)
        log = (path / 'run.log').read_text()
        self.assertIn('RASTER_FAULT_COMPLETE recoveryWriteAndActiveWriteInjected=true '
                      'oldPointerPreserved=true retryB=true recoveryA=true', log)
        self.assertNotIn('NEG_FAIL', log)
        self.assertEqual((path / 'run.exit').read_text().strip(), '124')

    def test_http_200_stale_callback_refused(self):
        import hashlib
        import json
        import re
        verify_current()
        path = ROOT / 'openspec/changes/spacefox-watchface/evidence/catalog-activation-whole/sdk-callback'
        build = json.loads((path / 'build.json').read_text())
        sha = lambda raw: hashlib.sha256(raw).hexdigest()
        probe = (path / 'Probe.mc').read_text()
        self.assertEqual(sha(probe.encode()), build['probeSha256'])
        for name, expected in {**build['productionSources'], **build['productionResources']}.items():
            self.assertEqual(sha(recorded_input(name, expected)), expected, name)
        for name, expected in build['probeResources'].items():
            self.assertEqual(sha((path / 'probe-resources' / name).read_bytes()), expected, name)
        match = re.search(r'callback\.receiveBatch\(200,WatchUi\.loadResource\(Rez\.JsonData\.(ObjA\d+)\)', probe)
        self.assertIsNotNone(match)
        old = json.loads((path / 'probe-resources' / (match.group(1)+'.json')).read_bytes())
        new = next(json.loads(p.read_bytes()) for p in (path / 'probe-resources').glob('ObjB*.json')
                   if json.loads(p.read_bytes())['ref']['path'] == build['missing'])
        self.assertEqual(sha(old['raw'].encode()), old['ref']['sha256'])
        self.assertNotEqual(sha(old['raw'].encode()), new['ref']['sha256'])
        self.assertIn('callback.status.equals("assetFailed")', probe)
        log = (path / 'run.log').read_text()
        self.assertIn('http200CallbackRefused=true', log)
        self.assertIn('priorPointerPreserved=true', log)
        self.assertNotIn('NEG_FAIL', log)
        self.assertEqual((path / 'run.exit').read_text().strip(), '124')

    def test_decoded_prior_bitmap_is_cleared(self):
        import hashlib
        import json
        verify_current()
        path = ROOT / 'openspec/changes/spacefox-watchface/evidence/catalog-activation-whole/sdk-realview'
        build = json.loads((path / 'build.json').read_text())
        sha = lambda raw: hashlib.sha256(raw).hexdigest()
        probe = (path / 'Probe.mc').read_text()
        self.assertEqual(sha(probe.encode()), build['probeSha256'])
        for name, expected in {**build['productionSources'], **build['productionResources']}.items():
            self.assertEqual(sha(recorded_input(name, expected)), expected, name)
        for name, expected in build['probeResources'].items():
            self.assertEqual(sha((path / 'probe-resources' / name).read_bytes()), expected, name)
        self.assertIn('priorRenderer=build.result', probe)
        self.assertIn('old.bitmap!=null', probe)
        self.assertIn('view.setPacket(cache.packet);priorRenderer=null;old=null', probe)
        log = (path / 'run.log').read_text()
        self.assertIn('actualOldBitmapCleared=true', log)
        self.assertIn('missingRefused=true priorPointerPreserved=true', log)
        self.assertNotIn('NEG_FAIL', log)
        self.assertEqual((path / 'run.exit').read_text().strip(), '124')

class WholePropertyTest(unittest.TestCase):
    """Join actual current native receipts to direct producer assertions."""
    def test_vc12_whole(self):
        CatalogActivationWholeTest.setUpClass()
        case = CatalogActivationWholeTest()
        case.test_catalog_identity_attribution_and_asset_version()
        case.test_unknown_typed_configuration_positive()
        case.test_unknown_typed_configuration_negative()
        case.test_real_site_zero_coordinates_positive()
        case.test_real_site_invalid_coordinates_negative()

    def test_vc13_whole(self):
        from tests.test_display03_receipt_binding import CurrentCoreCompositionTest
        from tests.test_current_format_acceptance import CurrentFormatAcceptanceTest
        receipt = CurrentSdkSceneReceiptTest()
        receipt.test_same_package_replacement_and_restart()
        receipt.test_native_settings_and_host_selection()
        receipt.test_stale_immutable_bytes_are_refused()
        receipt.test_http_200_stale_callback_refused()
        receipt.test_incomplete_corrupt_scene_and_retry()
        receipt.test_current_native_scene_and_motion_grammar_receipt()
        CurrentCoreCompositionTest('test_identity_negative').test_identity_negative()
        CurrentFormatAcceptanceTest().test_ls05_p6_s01_positive_current()
        CurrentFormatAcceptanceTest().test_ls05_p6_s01_negative_current()

    def test_vc14_whole(self):
        from tests.test_display03_receipt_binding import CurrentCoreCompositionTest, CurrentGeographyCompositionTest
        from tests.test_current_format_acceptance import CurrentFormatAcceptanceTest
        receipt = CurrentSdkSceneReceiptTest()
        receipt.test_same_package_replacement_and_restart()
        receipt.test_interrupted_scene_survives_no_push_restart()
        receipt.test_raster_pointer_write_faults()
        receipt.test_incomplete_corrupt_scene_and_retry()
        receipt.test_current_native_scene_and_motion_grammar_receipt()
        CurrentCoreCompositionTest('test_identity_negative').test_identity_negative()
        CurrentGeographyCompositionTest('test_geography_negative').test_geography_negative()
        CurrentFormatAcceptanceTest().test_ls11_p4_s01_positive_current()
        CurrentFormatAcceptanceTest().test_ls11_p4_s01_negative_current()
        CurrentFormatAcceptanceTest().test_ls05_p7_s01_positive_current()
        CurrentFormatAcceptanceTest().test_ls05_p7_s01_negative_current()

    def test_vc17_whole(self):
        CatalogActivationWholeTest.setUpClass()
        CatalogActivationWholeTest().test_selected_manifest_ignores_real_unrelated_growth()
        receipt = CurrentSdkSceneReceiptTest()
        receipt.test_bounded_native_batch_receipt()
        receipt.test_current_native_scene_and_motion_grammar_receipt()

class ScenarioCases(unittest.TestCase):
    """Each scenario has a distinct positive and negative execution identity."""
    @classmethod
    def setUpClass(cls):
        CatalogActivationWholeTest.setUpClass()

    def receipt(self): return CurrentSdkSceneReceiptTest()
    def catalog(self): return CatalogActivationWholeTest()
    def current(self):
        from tests.test_current_format_acceptance import CurrentFormatAcceptanceTest
        return CurrentFormatAcceptanceTest()
    def composition(self):
        from types import SimpleNamespace
        from tests.test_display03_receipt_binding import CurrentCoreCompositionTest, CurrentGeographyCompositionTest
        return SimpleNamespace(
            test_current_native_identity_refusal=CurrentCoreCompositionTest('test_identity_negative').test_identity_negative,
            test_current_native_geography_refusal=CurrentGeographyCompositionTest('test_geography_negative').test_geography_negative)

    def test_vc12_s01_positive(self):
        self.catalog().test_catalog_identity_attribution_and_asset_version()
        self.catalog().test_unknown_typed_configuration_positive()
    def test_vc12_s01_negative(self): self.catalog().test_unknown_typed_configuration_negative()
    def test_vc12_s02_positive(self): self.catalog().test_real_site_zero_coordinates_positive()
    def test_vc12_s02_negative(self): self.catalog().test_real_site_invalid_coordinates_negative()

    def test_vc13_s01_positive(self):
        self.receipt().test_same_package_replacement_and_restart()
        self.receipt().test_native_settings_and_host_selection()
        self.current().test_ls05_p6_s01_positive_current()
    def test_vc13_s01_negative(self):
        self.receipt().test_stale_immutable_bytes_are_refused()
        self.receipt().test_http_200_stale_callback_refused()
        self.receipt().test_current_native_scene_and_motion_grammar_receipt()
    def test_vc13_s02_positive(self): self.receipt().test_incomplete_corrupt_scene_and_retry()
    def test_vc13_s02_negative(self): self.receipt().test_current_native_scene_and_motion_grammar_receipt()
    def test_vc13_s03_positive(self):
        self.receipt().test_interrupted_scene_survives_no_push_restart()
        self.current().test_ls05_p6_s01_negative_current()
    def test_vc13_s03_negative(self):
        self.receipt().test_http_200_stale_callback_refused()
        self.composition().test_current_native_identity_refusal()
        self.current().test_ls05_p6_s01_negative_current()

    def test_vc14_s01_positive(self): self.receipt().test_same_package_replacement_and_restart()
    def test_vc14_s01_negative(self):
        self.receipt().test_incomplete_corrupt_scene_and_retry()
        self.receipt().test_current_native_scene_and_motion_grammar_receipt()
        self.composition().test_current_native_geography_refusal()
    def test_vc14_s02_positive(self): self.receipt().test_interrupted_scene_survives_no_push_restart()
    def test_vc14_s02_negative(self):
        self.receipt().test_raster_pointer_write_faults()
        self.current().test_ls11_p4_s01_positive_current()
        self.current().test_ls11_p4_s01_negative_current()
    def test_vc14_s03_positive(self):
        self.receipt().test_interrupted_scene_survives_no_push_restart()
        self.current().test_ls05_p7_s01_positive_current()
    def test_vc14_s03_negative(self):
        self.receipt().test_decoded_prior_bitmap_is_cleared()
        self.composition().test_current_native_identity_refusal()
        self.current().test_ls05_p7_s01_negative_current()

    def test_vc17_s01_positive(self):
        self.receipt().test_bounded_native_batch_receipt()
        self.catalog().test_selected_manifest_ignores_real_unrelated_growth()
    def test_vc17_s01_negative(self):
        self.receipt().test_bounded_native_batch_receipt()
        self.receipt().test_current_native_scene_and_motion_grammar_receipt()
        self.catalog().test_selected_manifest_ignores_real_unrelated_growth()
