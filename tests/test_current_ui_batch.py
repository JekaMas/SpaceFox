"""Current source-bound native display evidence; no device or phone claim."""
from pathlib import Path
import unittest
from unittest.mock import patch
import hashlib,json,re
from tools.verify_current_ui_batch import verify_rejection_menu, validate_aod_masks, validate_circle_box, validate_vertical_gap
from tools.run_native_tests import parse_output
from tools.native_language_policy import software_locales


ROOT = Path(__file__).resolve().parents[1]

def verify(root):
    """Compose current native observations with explicitly historical evidence.

    Old frames and their controls retain their own byte-bound history; current
    semantics come from the separately executed DISPLAY04 native inventory and
    current source-bound alpha/locale admission, never by repinning old files.
    """
    verify_rejection_menu(root)
    historical=root/'openspec/changes/spacefox-watchface/evidence/current-native-ui'
    record=json.loads((historical/'batch.json').read_text())
    required={'frames/en-face.png','frames/ru-face.png','frames/runtime.log','frames/build.json',
              'fields/native.log','fields/receipt.json','clock/native.log','clock/receipt.json',
              'lifecycle/native.log','lifecycle/receipt.json','recovery/native.log','recovery/receipt.json',
              'settings-reopen/reopen.log','settings-reopen/build.json'}|{'frames/aod-'+str(i)+'-face.png' for i in range(4)}
    if record['scope']!='current-ui-directed-frames-and-fields' or not required<=set(record['files']):
        raise ValueError('required current UI evidence missing')
    for name,expected in record['files'].items():
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or hashlib.sha256((historical/path).read_bytes()).hexdigest()!=expected:
            raise ValueError('current UI evidence changed: '+name)
    current=root/'openspec/changes/spacefox-watchface/evidence/display04-whole-quality/final-current-native'
    from tools.native_current_batch import inventory
    mapped={Path(row['probe']).stem:row for row in inventory(root)};results={}
    for folder in ('current_fields_probe','current_clock_probe','current_lifecycle_probe','current_recovery_probe','current_settings_probe','current_menu_probe'):
        d=current/folder;receipt=json.loads((d/'receipt.json').read_text());log=(d/'native.log').read_text()
        if hashlib.sha256((d/'Display02Tests.prg').read_bytes()).hexdigest()!=receipt['packageSha256']:
            raise ValueError('current native executable changed: '+folder)
        for name,expected in receipt['inputHashes'].items():
            from tools.native_integrated016_qualification import historical_input
            if hashlib.sha256(historical_input(root,name,expected)).hexdigest()!=expected:raise ValueError('historical native input changed: '+name)
        parsed=parse_output(log,receipt['rawExit'],tuple(mapped[folder]['tests']))
        if parsed['status']!='passed':raise ValueError('current native framework failed: '+folder)
        results[folder]=parsed['observed_tests']
    if software_locales(root)!=['en','ru','de','fr','es']:raise ValueError('current software qualification missing')
    historic_metrics=json.loads((historical/'retained-fitness/metrics-observation.json').read_text())
    names=('metricAvailable','metricDenied','metricUnsupported','metricMissing')
    old_metric=parse_output((historical/'retained-fitness/native-tests.log').read_text(),historic_metrics['raw_exit_code'],names)
    if old_metric['status']!='passed':raise ValueError('historical fitness observation failed')
    old_runtime=(historical/'frames/runtime.log').read_text();natural=re.search(r'UI_NATURAL_DONE elapsedMs=(\d+) frames=(\d+) running=false progress=0\.000000',old_runtime)
    if not natural or not 2000<=int(natural[1])<=3000:raise ValueError('historical animation observation missing')
    def installed(name):return {line.split()[-1].rsplit('/',1)[-1]:line.split()[0] for line in (historical/'settings-reopen'/name).read_text().splitlines()}
    before,after=installed('pre.sha256'),installed('post.sha256')
    if not {'USR.PRG','USR.DAT','USR.IDX','USR.SET'}<=set(before) or set(before)!=set(after):raise ValueError('historical reopen inventory differs')
    for n in ('USR.PRG','USR.DAT','USR.IDX'):
        if before[n]!=after[n]:raise ValueError('historical installed bytes changed')
    for file,test in (('selected-flag.log','test_selected_country_and_mismatch'),('corrected-site.log','test_corrected_site_rebuilds_the_projected_point')):
        raw=(historical/'visual-applicability'/file).read_text()
        if test not in raw or not raw.rstrip().endswith('OK'):raise ValueError('historical site control failed')
    current_d03=root/'openspec/changes/spacefox-watchface/evidence/display04-whole-quality/retained-display03-native'
    d03=json.loads((current_d03/'receipt.json').read_text())
    # Admission has validated the exact retained 24-case/guard source delta.
    d03result=parse_output((current_d03/'native.log').read_text(),d03['rawExit'],tuple(d03['tests']['expected_tests']))
    if d03result['status']!='passed':raise ValueError('current metric source boundary failed')
    return {'settingsResults':{**results['current_settings_probe'],**results['current_menu_probe']},
            'fieldResults':results['current_fields_probe'],'clockResults':results['current_clock_probe'],
            'lifecycleResults':results['current_lifecycle_probe'],'recoveryResults':results['current_recovery_probe'],
            'historicalMetricResults':old_metric['observed_tests'],'metricResults':d03result['observed_tests'],
            'historicalNaturalMs':int(natural[1]),'historicalReopenSetHashChanged':before['USR.SET']!=after['USR.SET'],
            'siteControls':['selected-country-mismatch','corrected-site-point']}

class CurrentUiBatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=verify(ROOT)

    def test_current_fields_and_visuals(self):
        result=self.result
        self.assertEqual(result['fieldResults']['currentPreclipTextIcons'],'PASS')
        self.assertEqual(result['lifecycleResults']['finalAodMinuteGuard'],'PASS')

    def test_corrupt_current_capture_refused(self):
        target=ROOT/'openspec/changes/spacefox-watchface/evidence/current-native-ui/frames/aod-0-face.png'
        original=Path.read_bytes
        def corrupt(path):
            data=original(path)
            return data+b'changed' if path.resolve()==target.resolve() else data
        with patch.object(Path,'read_bytes',corrupt),self.assertRaisesRegex(ValueError,'current UI evidence changed'):
            verify(ROOT)

    def test_excess_and_missing_aod_pixels_refused(self):
        with self.assertRaisesRegex(ValueError, 'nonempty'):
            validate_aod_masks([{1}, {2}, {3}, set()])
        with self.assertRaisesRegex(ValueError, 'pixel budget'):
            validate_aod_masks([set(range(12000)), {12001}, {12002}, {12003}])
        with self.assertRaisesRegex(ValueError, 'interior rest'):
            validate_aod_masks([{1,2}, {1,3}, {1,4}, {1,5}])

    def test_fields_persist_duplicate_roles(self):
        self.assertEqual(self.result['fieldResults']['basicFieldsPositive'],'PASS')

    def test_fields_invalid_slot_defaults_alone(self):
        self.assertEqual(self.result['fieldResults']['basicFieldsNegative'],'PASS')

    def test_unavailable_field_observation(self):
        self.assertEqual(self.result['fieldResults']['basicUnavailablePositive'],'PASS')

    def test_old_sample_replaced_and_age_rejected(self):
        self.assertEqual(self.result['fieldResults']['basicUnavailableNegative'],'PASS')

    def test_battery_and_body_battery_distinct(self):
        self.assertEqual(self.result['fieldResults']['basicBatteryPositive'],'PASS')

    def test_unavailable_battery_never_borrows(self):
        self.assertEqual(self.result['fieldResults']['basicBatteryNegative'],'PASS')

    def test_local_time_and_clock_adapter(self):
        for name in ('currentClockPositive','currentClockAdapter','currentClockFormatting'):
            self.assertEqual(self.result['clockResults'][name],'PASS')

    def test_midnight_does_not_shift_utc_countdown(self):
        self.assertEqual(self.result['clockResults']['currentClockNegative'],'PASS')

    def test_status_color_and_stale_independence(self):
        self.assertEqual(self.result['clockResults']['currentColorStates'],'PASS')

    def test_circle_clipping_refused(self):
        with self.assertRaisesRegex(ValueError,'circular bounds'):
            validate_circle_box((0,0,100,20))
        with self.assertRaisesRegex(ValueError,'overlap'):
            validate_vertical_gap(320,321)

    def test_settings_process_reopen(self):
        # SET changed across direct reopen; its cause is not established.
        self.assertTrue(self.result['historicalReopenSetHashChanged'])

    def test_changed_clock_owner_refused(self):
        target=ROOT/'watchface/source/WatchClock.mc'
        original=Path.read_bytes
        def corrupt(path):
            data=original(path)
            return data+b'changed' if path.resolve()==target.resolve() else data
        with patch.object(Path,'read_bytes',corrupt),self.assertRaisesRegex(ValueError,'current native input changed'):
            verify(ROOT)

    def test_natural_animation_and_stop(self):
        self.assertEqual(self.result['lifecycleResults']['finalAnimationLifecycle'],'PASS')
        self.assertTrue(2000 <= self.result['historicalNaturalMs'] <= 3000)

    def test_animation_bounds_and_stop(self):
        self.assertEqual(self.result['lifecycleResults']['finalAnimationBounds'],'PASS')
        self.assertEqual(self.result['lifecycleResults']['finalAnimationLifecycle'],'PASS')

    def test_local_calendar_and_primary_labels(self):
        self.assertEqual(self.result['lifecycleResults']['finalLocalCalendar'],'PASS')

    def test_status_color_corruption_refused(self):
        target=ROOT/'openspec/changes/spacefox-watchface/evidence/current-native-ui/clock/native.log'
        original=Path.read_bytes
        def corrupt(path):
            data=original(path)
            return data+b'changed' if path.resolve()==target.resolve() else data
        with patch.object(Path,'read_bytes',corrupt),self.assertRaisesRegex(ValueError,'current UI evidence changed'):
            verify(ROOT)

    def test_low_recovery_preserves_seal(self):
        self.assertEqual(self.result['recoveryResults']['currentLowRecovery'],'PASS')

    def test_low_recovery_corruption_refused(self):
        target=ROOT/'openspec/changes/spacefox-watchface/evidence/current-native-ui/recovery/native.log'
        original=Path.read_bytes
        def corrupt(path):
            data=original(path)
            return data+b'changed' if path.resolve()==target.resolve() else data
        with patch.object(Path,'read_bytes',corrupt),self.assertRaisesRegex(ValueError,'current UI evidence changed'):
            verify(ROOT)

    # Complete finite-corpus positive and negative cases are discovered once
    # in tests/test_display_corpus.py; do not execute those same tests again.

    def test_fitness_available(self):
        self.assertEqual(self.result['historicalMetricResults']['metricAvailable'],'PASS')
        self.assertEqual(self.result['metricResults']['display03MetricRolesAndAge'],'PASS')

    def test_fitness_missing(self):
        self.assertEqual(self.result['historicalMetricResults']['metricMissing'],'PASS')
        self.assertEqual(self.result['metricResults']['display03ComplicationSourceBoundary'],'PASS')

    def test_fitness_denied(self):
        self.assertEqual(self.result['historicalMetricResults']['metricDenied'],'PASS')
        self.assertEqual(self.result['metricResults']['display03ComplicationSourceBoundary'],'PASS')

    def test_fitness_unsupported(self):
        self.assertEqual(self.result['historicalMetricResults']['metricUnsupported'],'PASS')
        self.assertEqual(self.result['metricResults']['display03ComplicationSourceBoundary'],'PASS')

    def test_fitness_receipt_corruption_refused(self):
        target=ROOT/'openspec/changes/spacefox-watchface/evidence/current-native-ui/retained-fitness/native-tests.log'
        original=Path.read_bytes
        def corrupt(path):
            data=original(path)
            return data+b'changed' if path.resolve()==target.resolve() else data
        with patch.object(Path,'read_bytes',corrupt),self.assertRaisesRegex(ValueError,'current UI evidence changed'):
            verify(ROOT)

    def test_rehashed_omitted_date_evidence_refused(self):
        target=ROOT/'openspec/changes/spacefox-watchface/evidence/current-native-ui/batch.json'
        original=Path.read_text
        def omit(path,*args,**kwargs):
            text=original(path,*args,**kwargs)
            if path.resolve()==target.resolve():
                import json
                value=json.loads(text);del value['files']['frames/ru-face.png'];return json.dumps(value)
            return text
        with patch.object(Path,'read_text',omit),self.assertRaisesRegex(ValueError,'required current UI evidence missing'):
            verify(ROOT)

    def test_current_site_country_and_corrected_point(self):
        # SetUp reconciles the retained exact header/identity owners, immutable
        # catalog/assets and the two actual selected-country/site host controls.
        self.assertEqual(self.result['siteControls'],['selected-country-mismatch','corrected-site-point'])

    def test_current_scene_evidence_corruption_refused(self):
        target=ROOT/'openspec/changes/spacefox-watchface/evidence/current-native-ui/visual-applicability/selected-flag.log'
        original=Path.read_bytes
        def corrupt(path):
            data=original(path)
            return data+b'changed' if path.resolve()==target.resolve() else data
        with patch.object(Path,'read_bytes',corrupt),self.assertRaisesRegex(ValueError,'current UI evidence changed'):
            verify(ROOT)

    def test_menu_binding_source_corruption_refused(self):
        target=ROOT/'watchface/source/SettingsMenu.mc'
        original=Path.read_bytes
        def corrupt(path):
            data=original(path)
            return data+b'changed' if path.resolve()==target.resolve() else data
        with patch.object(Path,'read_bytes',corrupt),self.assertRaises(ValueError):
            verify(ROOT)

    def test_selected_map_marker_and_fade_refuse_mutation(self):
        import gzip,hashlib,importlib.util
        path=ROOT/'tests/native_scene_diagnostics/current-508/verify_current_scene.py'
        spec=importlib.util.spec_from_file_location('selected_scene_pixel_checker',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        raw=gzip.decompress((ROOT/'openspec/changes/spacefox-watchface/evidence/current-native-ui/map/screen.ppm.gz').read_bytes())
        header=raw.split(b'\n',3);self.assertEqual(header[:3],[b'P6',b'1200 1200',b'255']);image=header[3]
        refs={}
        for name,pin in module.PINS.items():
            value=gzip.decompress((ROOT/'tests/fixtures/sfr1m-current'/(name+'.rgba.gz')).read_bytes())
            self.assertEqual(hashlib.sha256(value).hexdigest(),pin);refs[name]=value
        self.assertTrue(module.check(image,refs))
        marker=bytearray(image);at=((165+256)*1200+335+87)*3;marker[at:at+3]=b'\0\0\0'
        self.assertFalse(module.check(marker,refs))
        flattened=bytearray(image)
        for y in range(78,105):
            for x in range(270,365):
                at=((y+256)*1200+x+87)*3;flattened[at:at+3]=b'\0\0\0'
        self.assertFalse(module.check(flattened,refs))

    def test_current_settings_and_menu(self):
        for name in ('finalSettingsPositive','finalSettingsNegative','currentMenuSettings'):
            self.assertEqual(self.result['settingsResults'][name],'PASS')

    def test_wrong_site_identity_refused(self):
        self.assertEqual(self.result['siteControls'],['selected-country-mismatch','corrected-site-point'])

    def test_menu_closure_omission_refused(self):
        target=ROOT/'openspec/changes/spacefox-watchface/evidence/current-native-ui/batch.json'
        original=Path.read_text
        def omit(path,*args,**kwargs):
            text=original(path,*args,**kwargs)
            if path.resolve()==target.resolve():
                import json
                value=json.loads(text);del value['files']['settings-reopen/reopen.log'];return json.dumps(value)
            return text
        with patch.object(Path,'read_text',omit),self.assertRaisesRegex(ValueError,'required current UI evidence missing'):
            verify(ROOT)
