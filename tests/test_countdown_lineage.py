"""Captured coarse NET must expire without promoting source precision."""
import json
import unittest
import zipfile
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
    def test_public_generation102_reopens(self):
        from tools.spacefox.cloud import snapshot_files
        from tools.spacefox.publisher import decode_ledger, _schedule, schedule_document, validate_snapshot_artifact, StateError
        from tools.spacefox.native_motion import _RepositoryCatalogOperation, with_text_transport
        from tools.spacefox.schedule import advance_schedule, RefreshPolicy
        from tools.spacefox.feed import encode_feed
        with zipfile.ZipFile(ROOT/'tests/fixtures/publisher-generation102-public.zip') as archive:
            captured={name:archive.read(name) for name in archive.namelist()}
        class PublicStore:
            def _ledger_at(self, revision):
                return decode_ledger(captured['ledger.json'],captured.__getitem__)
            def _blob(self, revision, path, limit):
                return captured[path]
        snapshot,files=snapshot_files(PublicStore(),'captured-public-state',102)
        self.assertEqual(snapshot['generation'],102)
        self.assertEqual(files['watch.json'],captured['artifacts/102/watch.json'])
        doc=PublicStore()._ledger_at('captured-public-state')
        policy=RefreshPolicy(**doc['refresh_policy'])
        now=snapshot['schedule']['evaluated_at_utc']+1
        state=advance_schedule(_schedule(snapshot['schedule']),now,policy)
        publisher={'instance':doc['instance_id'],'generation':103,
                   'selectionValidatedUtc':doc['selection_validated_utc']}
        owner=_RepositoryCatalogOperation(ROOT)
        candidate_files,revision=owner.build(state,None,now,publisher=publisher,policy=policy,traversal=None)
        candidate=dict(snapshot,generation=103,catalog_revision=revision,schedule=schedule_document(state))
        feed=validate_snapshot_artifact(candidate,candidate_files,refresh_policy=doc['refresh_policy'],
            instance=doc['instance_id'],selection_validated_utc=doc['selection_validated_utc'],
            require_selection_epoch=True,require_current_projection=True)
        self.assertEqual(sum('terminal' in r for r in feed['upcoming']),1)
        for mutation in ('omitted','changed'):
            altered=json.loads(candidate_files['feed.json'])
            if mutation=='omitted':
                altered['upcoming']=[row for row in altered['upcoming'] if 'terminal' not in row]
            else:
                row=next(row for row in altered['upcoming'] if 'terminal' in row)
                row['terminal']['status']='cancelled' if row['terminal']['status']=='completed' else 'completed'
            changed=dict(candidate_files,**{'feed.json':encode_feed(altered)})
            changed=with_text_transport(changed)
            with self.subTest(mutation=mutation),self.assertRaisesRegex(StateError,'upcoming facts disagree'):
                validate_snapshot_artifact(candidate,changed,refresh_policy=doc['refresh_policy'],
                    require_current_projection=True)

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
