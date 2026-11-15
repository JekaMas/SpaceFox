"""Current selection controls with retained selected-scene observations.

Obsolete native/settings receipt wrappers were retired; their original results
remain historical. Current clock and UI controls own their bounded observations.
"""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import unittest

from tools.native_timing_settings import EVIDENCE, ROOT
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



    def scene(self,*names):
        # Exact old receipt/source inputs plus separately named current seams.
        from tests.retained_scene_reader import observe_scene
        observe_scene(*names)


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





if __name__=='__main__':unittest.main()
