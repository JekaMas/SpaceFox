"""Current source-bound native display evidence; no device or phone claim."""
from pathlib import Path
import unittest
from unittest.mock import patch
from tools.verify_current_ui_batch import validate_aod_masks, validate_circle_box, validate_vertical_gap
from tests.public_ui_binding import verify

ROOT = Path(__file__).resolve().parents[1]

class CurrentUiBatchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=verify(ROOT)

    def test_current_fields_and_visuals(self):
        result=self.result
        self.assertEqual(result['naturalMs'],2557)
        self.assertEqual(result['aodLit'],[7365,7334,7404,7396])
        self.assertEqual(result['aodIntersection'],0)

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
        self.test_changed_clock_owner_refused()

    def test_status_color_and_stale_independence(self):
        self.assertEqual(self.result['clockResults']['currentColorStates'],'PASS')

    def test_circle_clipping_refused(self):
        with self.assertRaisesRegex(ValueError,'circular bounds'):
            validate_circle_box((0,0,100,20))
        with self.assertRaisesRegex(ValueError,'overlap'):
            validate_vertical_gap(320,321)

    def test_settings_process_reopen(self):
        # SET changed across direct reopen; its cause is not established.
        self.assertTrue(self.result['reopenSetHashChanged'])

    def test_changed_clock_owner_refused(self):
        target=ROOT/'watchface/source/WatchClock.mc'
        original=Path.read_bytes
        def corrupt(path):
            data=original(path)
            return data+b'changed' if path.resolve()==target.resolve() else data
        with patch.object(Path,'read_bytes',corrupt),self.assertRaisesRegex(ValueError,'semantic owner changed'):
            verify(ROOT)

    def test_natural_animation_and_stop(self):
        self.assertEqual(self.result['lifecycleResults']['finalAnimationLifecycle'],'PASS')
        self.assertTrue(2000 <= self.result['naturalMs'] <= 3000)

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

    def test_current_finite_corpus_positive(self):
        from tests.test_display_corpus import RealDisplayCorpusTest
        RealDisplayCorpusTest.setUpClass()
        RealDisplayCorpusTest('test_whole_real_collection_raws_dictionary_and_locales').test_whole_real_collection_raws_dictionary_and_locales()
        RealDisplayCorpusTest('test_all_actual_display_fields_match_production_provider_projection').test_all_actual_display_fields_match_production_provider_projection()

    def test_current_finite_corpus_negative(self):
        from tests.test_display_corpus import RealDisplayCorpusTest
        RealDisplayCorpusTest.setUpClass()
        RealDisplayCorpusTest('test_incomplete_actual_collection_never_builds').test_incomplete_actual_collection_never_builds()
        RealDisplayCorpusTest('test_whole_actual_hash_mutation_refuses_without_publishing').test_whole_actual_hash_mutation_refuses_without_publishing()

    def test_fitness_available(self):
        self.assertEqual(self.result['metricResults']['metricAvailable'],'PASS')

    def test_fitness_missing(self):
        self.assertEqual(self.result['metricResults']['metricMissing'],'PASS')

    def test_fitness_denied(self):
        self.assertEqual(self.result['metricResults']['metricDenied'],'PASS')

    def test_fitness_unsupported(self):
        self.assertEqual(self.result['metricResults']['metricUnsupported'],'PASS')

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
        self.test_current_scene_evidence_corruption_refused()

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
