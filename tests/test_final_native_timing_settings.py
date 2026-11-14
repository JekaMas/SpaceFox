"""Whole final timer/selection/settings unit with actual source-bound SDK evidence.

No native countdown implementation is duplicated on the host. Exact literal
values, forbidden identities/states, actual Properties callbacks and cold reopen
are the oracle. Retained finite fonts/corpus keep their original observation.
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from xml.etree import ElementTree as ET

from tools.native_timing_settings import EVIDENCE, ROOT, NATIVE, validate_evidence
from tools.run_native_tests import parse_output
from tools.spacefox.schedule import (LaunchStatus, ScheduleState, Timing, TimePrecision,
    advance_schedule, merge_schedule, select_next, ScheduleError)
from tools.spacefox.wire import project_schedule, validate_current_feed
from tools.spacefox.catalog import canonical_bytes
from tests import test_basic_launch_logic as basic_launch
from tests.test_basic_launch_logic import NOW, VULCAN, STARSHIP, SECOND, state



class FinalNativeTimingSettingsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        basic_launch.BasicLaunchLogicTest.setUpClass()
        cls.rows=basic_launch.BasicLaunchLogicTest.rows
        cls.records=basic_launch.BasicLaunchLogicTest.records
        cls.catalog=basic_launch.BasicLaunchLogicTest.catalog
        cls.template=basic_launch.BasicLaunchLogicTest.template
        cls.evidence=ROOT/EVIDENCE

    feed=basic_launch.BasicLaunchLogicTest.feed

    def clock(self,*names):
        # Explicit current native16 assertion receipt replaces only the former
        # clock receipt reader; the host assertions below execute unchanged.
        return self.native(*names)

    def exact_feed_native(self):
        return self.native('finalTimingPositive','finalParserUpdatePositive')

    def scene(self,*names):
        # Retain only the two unmodified typed SFR identity assertions. They do
        # not draw text, settings, timer, colors or marks. The whole old scene
        # suite is historical, never claimed current.
        allowed={'selectedIdentityPositive','selectedIdentityNegative'}
        self.assertTrue(set(names)<=allowed)
        folder=ROOT/'openspec/changes/spacefox-watchface/evidence/basic-selected-scene-whole/native'
        result=json.loads((folder/'scene-observation.json').read_text())
        hashes=result['build']['source_sha256']
        dependencies=['NativeSfr.mc','NativeImmutable.mc','NativeBridgeFeed.mc','NativeJson.mc','NativeSourceTimes.mc','NativeAssetTypes.mc','NativeRenderSource.mc','NativeAnimation.mc','NativeVisualRenderer.mc']
        for name in ['watchface/source/'+x for x in dependencies]+[x for x in hashes if x.startswith('tests/fixtures/basic_selected_scene/')]:
            source = self.evidence/'observer/production-snapshot'/Path(name+'.txt') if name=='watchface/source/NativeJson.mc' else ROOT/name
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),hashes[name],name)
        old=(self.evidence/'baseline/watchface/source/NativeFeed.mc').read_text()
        current=(self.evidence/'observer/production-snapshot/watchface/source/NativeFeed.mc.txt').read_text()
        self.assertEqual(current.replace('["pending","unknown","started"].indexOf(l["status"])','["pending","unknown"].indexOf(l["status"])'),old)
        self.assertEqual(hashlib.sha256(old.encode()).hexdigest(),hashes['watchface/source/NativeFeed.mc'])
        from tests.test_basic_selected_scene import NAMES
        observed=parse_output((folder/'native-tests.log').read_text(),result['raw_exit_code'],NAMES)
        self.assertEqual(observed['status'],'passed')
        for name in names:self.assertEqual(observed['observed_tests'][name],'PASS')

    def native(self,*names):
        result=json.loads((self.evidence/'unit/unit-result.json').read_text())
        build=json.loads((self.evidence/'unit/build.json').read_text())
        self.assertEqual(build['exitCode'],0)
        binding=json.loads((self.evidence/'clean-source.json').read_text())
        self.assertEqual(binding['status'],'passed')
        self.assertEqual(binding['productionSources'],build['productionSources'])
        self.assertEqual(binding['productionResources'],build['productionResources'])
        for name,digest in {**build['productionSources'],**build['productionResources']}.items():
            # NativeFeed gained a bounded ascent field. The retained run binds
            # its old byte snapshot; strict admission independently validates
            # that snapshot and the current parser's targeted SDK assertions.
            source = self.evidence/'observer/production-snapshot'/Path(name+'.txt') if name in ('watchface/source/NativeFeed.mc','watchface/source/NativeJson.mc') else ROOT/name
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),digest,name)
        from tools.native_language_policy import software_locales
        self.assertEqual(software_locales(ROOT),['en','ru','de','fr','es'])
        self.assertEqual(build['assertionSha256'],hashlib.sha256((ROOT/'tests/fixtures/final_native_timing_settings/Assertions.mc').read_bytes()).hexdigest())
        self.assertEqual(build['clockAssertionSha256'],hashlib.sha256((ROOT/'watchface/tests/NativeClockTests.mc').read_bytes()).hexdigest())
        raw=(self.evidence/'unit/native-tests.log').read_text()
        observed=parse_output(raw,result['raw_exit_code'],NATIVE)
        self.assertEqual(observed['status'],'passed')
        for name in names:self.assertEqual(observed['observed_tests'][name],'PASS')
        return raw,result

    def test_selection_positive(self):
        from tests.test_sourced_ascent_end import SourcedAscentEndTest
        SourcedAscentEndTest.setUpClass()
        SourcedAscentEndTest('test_selection_replay_and_updated_source').test_selection_replay_and_updated_source()
        SourcedAscentEndTest('test_deterministic_event_sequences').test_deterministic_event_sequences()
        SourcedAscentEndTest('test_current_wire_projection_and_bounds').test_current_wire_projection_and_bounds()
        SourcedAscentEndTest('test_real_publisher_reopen_preserves_supplement').test_real_publisher_reopen_preserves_supplement()
        SourcedAscentEndTest('test_actual_update_pipeline').test_actual_update_pipeline()
        basic_launch.BasicLaunchLogicTest.test_earlier_positive(self)
        basic_launch.BasicLaunchLogicTest.test_ordering_positive(self)
        first=replace(self.records[VULCAN],timing=Timing(TimePrecision.EXACT,exact_utc=NOW))
        second=replace(self.records[STARSHIP],timing=Timing(TimePrecision.EXACT,exact_utc=NOW+1800))
        accepted=state(first,second)
        for offset in (0,1,59,899,900):
            selected=select_next(advance_schedule(accepted,NOW+offset))
            self.assertEqual(selected.entry.record.launch_id.value,VULCAN)
            self.assertEqual(selected.entry.record.status,LaunchStatus.PENDING)
        after=select_next(advance_schedule(accepted,NOW+901))
        self.assertEqual(after.entry.record.launch_id.value,STARSHIP)
        self.assertEqual(after.remaining_seconds,899)
        # Earlier newly supplied future target wins before the current launch's
        # phase; fixed IDs keep rocket/site/time in one source record.
        later=replace(first,timing=Timing(TimePrecision.EXACT,exact_utc=NOW+7200))
        self.assertEqual(select_next(state(later,second)).entry.record,second)
        # LL2 nominal minute uses exactly the same retention without upgrading
        # its wire/source precision to exact-second knowledge.
        minute=self.records[VULCAN];target=minute.timing.nominal_utc
        self.assertEqual(minute.timing.source_precision_id,1)
        future=replace(second,timing=Timing(TimePrecision.EXACT,exact_utc=target+1800))
        for offset,wanted in ((0,VULCAN),(899,VULCAN),(900,VULCAN),(901,STARSHIP)):
            self.assertEqual(select_next(advance_schedule(state(minute,future),target+offset)).entry.record.launch_id.value,wanted)
        packet=json.loads((ROOT/'tests/fixtures/map-only/feed.json').read_text())
        for offset in (0,899,900,901):
            advanced=advance_schedule(accepted,NOW+offset)
            projected=project_schedule(advanced,self.catalog,NOW+offset,publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':NOW})
            parsed=validate_current_feed(canonical_bytes(dict(packet,**projected)),now=NOW+offset)
            self.assertEqual(parsed['launch']['launch_id'],'ll2:launch:'+(VULCAN if offset<=900 else STARSHIP))
        self.assertEqual(json.loads((self.evidence/'captured-provider-fields.json').read_text())['ascentFieldCandidates'],{})

    def test_selection_negative(self):
        from tests.test_sourced_ascent_end import SourcedAscentEndTest
        SourcedAscentEndTest.setUpClass()
        SourcedAscentEndTest('test_malformed_refusal_and_binding').test_malformed_refusal_and_binding()
        SourcedAscentEndTest('test_default_cli_and_update_load_tracked_supplement').test_default_cli_and_update_load_tracked_supplement()
        basic_launch.BasicLaunchLogicTest.test_earlier_negative(self)
        basic_launch.BasicLaunchLogicTest.test_ordering_negative(self)
        first=replace(self.records[VULCAN],timing=Timing(TimePrecision.EXACT,exact_utc=NOW))
        second=replace(self.records[STARSHIP],timing=Timing(TimePrecision.EXACT,exact_utc=NOW+1800))
        accepted=state(first,second)
        for status in (LaunchStatus.CANCELLED,LaunchStatus.COMPLETED):
            terminal=replace(first,status=status)
            self.assertEqual(select_next(state(terminal,second)).entry.record,second)
        # Technical status6/9 mutations of the real captured record exercise
        # the literal expected in-flight reducer state (no captured6/9rows).
        # Keep that same timed identity during ascent, then permit
        # the next launch; never newly select an ancient in-flight record.
        from tools.spacefox.provider import normalize_launch
        for source_id in (6,9):
            raw=deepcopy(self.rows[VULCAN]);raw['status']['id']=source_id
            started=replace(normalize_launch(raw,NOW),timing=first.timing)
            self.assertEqual(started.status,LaunchStatus.STARTED)
            untimed=replace(started,timing=Timing(TimePrecision.UNKNOWN))
            self.assertEqual(select_next(state(untimed,second)).entry.record,second)
            self.assertIsNone(select_next(state(untimed)).entry)
            for offset in (0,899,900):
                self.assertEqual(select_next(advance_schedule(state(started,second),NOW+offset)).entry.record.launch_id.value,VULCAN)
            self.assertEqual(select_next(advance_schedule(state(started,second),NOW+901)).entry.record.launch_id.value,STARSHIP)
            self.assertIsNone(select_next(advance_schedule(state(started),NOW+901)).entry)
        # New source facts override retention even one second after nominalzero.
        postponed=replace(first,timing=Timing(TimePrecision.EXACT,exact_utc=NOW+3600),source_validated_utc=NOW+1,source_updated_utc=NOW+1,source_updated_iso=None)
        updated=merge_schedule(accepted,(postponed,),NOW+1)
        self.assertTrue(next(e for e in updated.entries if e.record.launch_id.value==VULCAN).rescheduled)
        self.assertEqual(select_next(updated).entry.record,second)
        withdrawn=replace(postponed,timing=Timing(TimePrecision.UNKNOWN),source_validated_utc=NOW+2,source_updated_utc=NOW+2)
        self.assertEqual(select_next(merge_schedule(updated,(withdrawn,),NOW+2)).entry.record,second)
        cancelled=replace(postponed,status=LaunchStatus.CANCELLED)
        self.assertEqual(select_next(merge_schedule(accepted,(cancelled,),NOW+1)).entry.record,second)
        # A missing next record never promotes elapsed time to sourcecompletion.
        lone=select_next(advance_schedule(state(first),NOW+7200))
        self.assertEqual(lone.entry.record.status,LaunchStatus.PENDING)
        self.assertEqual(lone.entry.record.launch_id.value,VULCAN)
        with self.assertRaises(ScheduleError):Timing(TimePrecision.EXACT,exact_utc=True)

    def test_native_positive(self):
        basic_launch.BasicLaunchLogicTest.test_exact_positive(self)
        basic_launch.BasicLaunchLogicTest.test_uncertain_positive(self)
        basic_launch.BasicLaunchLogicTest.test_provider_precision_positive(self)
        self.native('clockExactPositive','offlineWakePositive','precisionTransitions','clockAdapterSmoke','formatLocalSettings','finalTimingPositive','finalParserUpdatePositive')
        from tools.native_language_policy import software_locales
        self.assertEqual(software_locales(ROOT),['en','ru','de','fr','es'])
        result=json.loads((self.evidence/'native-result.json').read_text())
        self.assertEqual(result['observedFrames'],20)
        self.assertEqual(set(result['locales']),{'en','ru'})
        self.assertEqual(result['geometryStatus'],'passed')

    def test_native_negative(self):
        basic_launch.BasicLaunchLogicTest.test_uncertain_negative(self)
        basic_launch.BasicLaunchLogicTest.test_provider_precision_negative(self)
        basic_launch.BasicLaunchLogicTest.test_minute_negative(self)
        raw,result=self.native('clockExactNegative','uncertaintyPositive','uncertaintyNegative','offlineWakeNegative','emptyStartup','finalTimingNegative','finalParserUpdateNegative')
        self.assertEqual(parse_output(raw.replace('finalTimingNegative','wrongTiming'),result['raw_exit_code'],NATIVE)['status'],'failed')
        # Reproduce the root counterexample as a technical permutation of
        # actual observed pixels/OCR: elapsed899 placed under a zero label.
        # Hashes are updated consistently so only the semantic pixel oracle can
        # reject it; no invented display text or digit corrections.
        import shutil
        from tools.native_timing_settings import validate_pixel_readback
        with tempfile.TemporaryDirectory() as t:
            folder=Path(t);shutil.copytree(self.evidence/'frames',folder/'frames')
            for name in ('pixel-readback.json','pixel-ocr-first2.jsonl','pixel-ocr-remaining18.jsonl'):
                shutil.copyfile(self.evidence/name,folder/name)
            target=folder/'frames/held-en-zero.png';target.write_bytes((folder/'frames/held-en-elapsed899.png').read_bytes())
            association=json.loads((folder/'pixel-readback.json').read_text())
            next(row for row in association['frames'] if row['label']=='en-zero')['pngSha256']=hashlib.sha256(target.read_bytes()).hexdigest()
            (folder/'pixel-readback.json').write_text(json.dumps(association))
            rows=[json.loads(line) for line in (folder/'pixel-ocr-remaining18.jsonl').read_text().splitlines()]
            elapsed=next(row for row in rows if Path(row['file']).name=='held-en-elapsed899.png')
            next(row for row in rows if Path(row['file']).name=='held-en-zero.png')['observations']=deepcopy(elapsed['observations'])
            (folder/'pixel-ocr-remaining18.jsonl').write_text('\n'.join(json.dumps(row) for row in rows)+'\n')
            with self.assertRaisesRegex(ValueError,'actual countdown pixels disagree with label: en-zero'):
                validate_pixel_readback(folder)
        # Source-bound evidence itself must reject missing native state coverage.
        with tempfile.TemporaryDirectory() as t:
            p=Path(t);(p/'native-result.json').write_text(json.dumps({'status':'failed'}))
            with self.assertRaises((ValueError,FileNotFoundError)):validate_evidence(p)

    def test_settings_positive(self):
        self.native('finalSettingsPositive')
        from tools.native_language_policy import software_locales
        self.assertEqual(software_locales(ROOT),['en','ru','de','fr','es'])
        result=json.loads((self.evidence/'native-result.json').read_text())
        self.assertTrue(result['coldReopenObserved'])
        props=ET.parse(ROOT/'watchface/resources/settings/properties.xml').getroot()
        self.assertEqual(next(x.text for x in props if x.get('id')=='Language'),'0')
        self.assertEqual({x.get('id') for x in props},{'Field1','Field2','Field3','Field4','Language','ClockColor','CountdownColor','Field1Color','Field2Color','Field3Color','Field4Color','FeedBaseUrl'})
        menus=ET.parse(ROOT/'watchface/resources/settings/settings.xml').getroot()
        language=next(x for x in menus if x.get('propertyKey')=='@Properties.Language')
        self.assertEqual({int(x.get('value')) for x in language.find('settingConfig')},{0,1,2,3,4,36})
        from tools.native_language_policy import software_locales
        self.assertEqual(software_locales(ROOT),['en','ru','de','fr','es'])
        from tests.test_native_localization import NativeLocalizationResourcesTest
        resource_test=NativeLocalizationResourcesTest()
        resource_test.test_all36_and_settings_preserved()
        resource_test.test_generation_is_complete_and_repeatable()
        from tests.test_native_finite_evidence import NativeFiniteEvidenceTest
        NativeFiniteEvidenceTest().test_actual_finite_primary_software_receipt_admits_without_human_flags()

    def test_settings_negative(self):
        self.native('finalSettingsNegative')
        for color in (0x7FE7C6,0xF7F9FC,0x9AD5FF,0xCDB7FF,0xFFD686,0xFFAFCF):
            def linear(c):return c/12.92 if c<=0.04045 else ((c+0.055)/1.055)**2.4
            rgb=[linear(((color>>shift)&255)/255) for shift in (16,8,0)]
            contrast=(sum(a*b for a,b in zip(rgb,(0.2126,0.7152,0.0722)))+0.05)/0.05
            self.assertGreaterEqual(contrast,4.5)  # black contour heuristic only
        from tests.test_native_finite_evidence import NativeFiniteEvidenceTest
        NativeFiniteEvidenceTest('test_rehashed_native_log_probe_sdk_and_corpus_corruptions_refuse').test_rehashed_native_log_probe_sdk_and_corpus_corruptions_refuse()
        resource=ET.parse(ROOT/'watchface/resources/settings/settings.xml').getroot()
        self.assertEqual(len(resource),12)
        self.assertFalse(any(any(word in x.get('propertyKey','').lower() for word in ('layout','globe','projection','hide','format')) for x in resource))

if __name__=='__main__':unittest.main()
