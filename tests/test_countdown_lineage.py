"""Captured coarse NET must expire without promoting source precision."""
import json
import unittest
from pathlib import Path
from tools.spacefox.schedule import AcceptedLaunch, IdKind, LaunchRecord, LaunchStatus, ScheduleState, StableId, Timing, TimePrecision, select_next
from tools.spacefox.watch_snapshot import FIELDS, snapshot
from tools.spacefox.wire import terminal_updates
from dataclasses import replace

ROOT = Path(__file__).resolve().parents[1]
NET = 1795042200

def launch(identity, timing):
    return LaunchRecord(StableId(IdKind.LAUNCH, 'll2', identity), timing, LaunchStatus.PENDING, 1794970678)

class CountdownLineage(unittest.TestCase):
    def test_captured_coarse_net_has_display_retention_without_reminder(self):
        p=ROOT/'tests/fixtures/fr165-runtime-20261116/feed.txt'
        feed=json.loads(p.read_text());catalog=json.loads((p.parent/'objects'/feed['catalogPath']).read_text())
        result=dict(zip(FIELDS,snapshot(feed,catalog)[3]))
        self.assertEqual(result['displayTarget'],NET)
        self.assertIsNone(result['target'])
        self.assertEqual(result['precision'],'window')
        self.assertEqual(result['retentionDeadline'],NET+900)
        self.assertFalse(result['reminderEligible'])

    def test_captured_coarse_selection_expires_at_boundary(self):
        coarse=launch('e0a11eb1-0bda-4872-b36b-140247fd5c60', Timing(TimePrecision.SOURCE_COARSE,window_start_utc=1795041780,window_end_utc=1795043100,nominal_utc=NET,source_net='2026-11-18T22:50:00Z',source_precision_id=2,source_precision_name='Hour',source_precision_abbrev='HR',source_precision_description='The T-0 is accurate to the hour.'))
        later=launch('76617033-4dc0-4448-b50c-e5b0d5a18539',Timing(TimePrecision.EXACT,exact_utc=1795148935))
        a,b=AcceptedLaunch(coarse,False,False),AcceptedLaunch(later,False,False)
        self.assertEqual(select_next(ScheduleState((a,b),NET+899)).entry.record.launch_id,coarse.launch_id)
        self.assertEqual(select_next(ScheduleState((a,b),NET+900)).entry.record.launch_id,later.launch_id)
        self.assertIsNone(select_next(ScheduleState((a,),NET+900)).entry)

    def test_recent_cancellation_supersedes_cached_later_target_after_old_net(self):
        old=launch('e0a11eb1-0bda-4872-b36b-140247fd5c60', Timing(TimePrecision.SOURCE_COARSE,window_start_utc=1795041780,window_end_utc=1795043100,nominal_utc=NET,source_net='2026-11-18T22:50:00Z',source_precision_id=2,source_precision_name='Hour',source_precision_abbrev='HR',source_precision_description='The T-0 is accurate to the hour.'))
        cancelled=replace(old,status=LaunchStatus.CANCELLED,source_validated_utc=NET+3600)
        state=ScheduleState((AcceptedLaunch(cancelled,False,False),),NET+3600)
        self.assertEqual(terminal_updates(state,NET+3600)[0]['terminal']['launch_id'],'ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60')

    def test_exact_cancellation_later_cached_target_is_not_omitted(self):
        old=launch('e0a11eb1-0bda-4872-b36b-140247fd5c60',Timing(TimePrecision.EXACT,exact_utc=NET))
        cancelled=replace(old,status=LaunchStatus.CANCELLED,source_validated_utc=NET+3600)
        state=ScheduleState((AcceptedLaunch(cancelled,False,False),),NET+3600)
        self.assertEqual(terminal_updates(state,NET+3600)[0]['terminal']['launch_id'],'ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60')

    def test_window_without_announced_net_is_not_given_a_clock_deadline(self):
        unknown=launch('e0a11eb1-0bda-4872-b36b-140247fd5c60',Timing(TimePrecision.WINDOW,window_start_utc=NET))
        state=ScheduleState((AcceptedLaunch(unknown,False,False),),NET+90000)
        self.assertEqual(select_next(state).entry.record.launch_id,unknown.launch_id)

    def test_sourced_ascent_end_extends_exact_retention(self):
        old=launch('e0a11eb1-0bda-4872-b36b-140247fd5c60',Timing(TimePrecision.EXACT,exact_utc=NET))
        ascent={'launch_id':'ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60','target_utc':NET,'end_utc':NET+1800,'source_url':'https://example.invalid/ascent','reviewed_utc':1794970678}
        record=replace(old,ascent_end=ascent)
        entry=AcceptedLaunch(record,False,False)
        self.assertIsNotNone(select_next(ScheduleState((entry,),NET+1799)).entry)
        self.assertIsNone(select_next(ScheduleState((entry,),NET+1800)).entry)
