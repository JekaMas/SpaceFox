"""Technical mutations only: no actual upstream ascent facts are claimed."""
from dataclasses import replace
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import subprocess
from datetime import datetime, timezone
from email.utils import format_datetime
import unittest
from unittest.mock import patch
from tools.spacefox.ascent_supplement import attach, load_supplement
from tools.spacefox.schedule import (AcceptedLaunch, LaunchStatus, ScheduleError, ScheduleState, TimePrecision, Timing,
                                     advance_schedule, merge_schedule, select_next)
from tools.spacefox.publisher import _schedule, schedule_document
from tools.spacefox.provider import normalize_launch
from tests import test_basic_launch_logic as basic
from tests.test_basic_launch_logic import NOW, VULCAN, STARSHIP, state


class SourcedAscentEndTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        basic.BasicLaunchLogicTest.setUpClass()
        cls.first = replace(basic.BasicLaunchLogicTest.records[VULCAN], timing=Timing(TimePrecision.EXACT, exact_utc=NOW))
        cls.second = replace(basic.BasicLaunchLogicTest.records[STARSHIP], timing=Timing(TimePrecision.EXACT, exact_utc=NOW+3600))
        cls.fact = {'launch_id':'ll2:launch:'+VULCAN, 'target_utc':NOW, 'end_utc':NOW+1800,
                    'source_url':'https://example.invalid/mission/?missionId=technical', 'reviewed_utc':cls.first.source_validated_utc}

    def test_selection_replay_and_updated_source(self):
        original=attach(self.first,(self.fact,)); initial=state(original,self.second)
        self.assertEqual(original.source_validated_utc,self.first.source_validated_utc)
        with self.assertRaises(TypeError):original.ascent_end['end_utc']=NOW+9999
        for offset, expected in ((0,VULCAN),(900,VULCAN),(901,VULCAN),(1800,VULCAN),(1801,STARSHIP)):
            self.assertEqual(select_next(advance_schedule(initial,NOW+offset)).entry.record.launch_id.value,expected)
        fallback=state(self.first,self.second)
        self.assertEqual(select_next(advance_schedule(fallback,NOW+901)).entry.record.launch_id.value,STARSHIP)
        window=replace(self.first,timing=Timing(TimePrecision.EXACT,exact_utc=NOW,window_end_utc=NOW+3000))
        self.assertEqual(select_next(advance_schedule(state(window,self.second),NOW+901)).entry.record.launch_id.value,STARSHIP)
        self.assertEqual(_schedule(schedule_document(initial)),initial)
        self.assertEqual(merge_schedule(initial,(original,),NOW), initial)
        # A later independent review may attach at the same provider epoch;
        # it does not renew that epoch. A future review is refused.
        later=attach(self.first,(dict(self.fact,reviewed_utc=NOW+1),))
        with self.assertRaises(ScheduleError):merge_schedule(state(self.first,self.second),(later,),NOW)
        attached=merge_schedule(state(self.first,self.second),(later,),NOW+1)
        selected=next(e.record for e in attached.entries if e.record.launch_id.value==VULCAN)
        self.assertEqual(selected.source_validated_utc,self.first.source_validated_utc)
        self.assertEqual(selected.ascent_end['reviewed_utc'],NOW+1)
        stale=ScheduleState((AcceptedLaunch(self.first,False,True),AcceptedLaunch(self.second)),NOW)
        changed=merge_schedule(stale,(later,),NOW+1)
        self.assertTrue(next(e for e in changed.entries if e.record.launch_id.value==VULCAN).stale)
        older=attach(self.first,(dict(self.fact,end_utc=NOW+1900),))
        with self.assertRaises(ScheduleError):merge_schedule(attached,(older,),NOW+2)
        moved=replace(self.first,timing=Timing(TimePrecision.EXACT,exact_utc=NOW+4000),source_validated_utc=NOW+1,source_updated_utc=NOW+1,source_updated_iso=None)
        updated=merge_schedule(initial,(attach(moved,(self.fact,)),),NOW+1)
        self.assertEqual(select_next(updated).entry.record.launch_id.value,STARSHIP)
        self.assertIsNone(next(e.record for e in updated.entries if e.record.launch_id.value==VULCAN).ascent_end)
        withdrawn=replace(moved,timing=Timing(TimePrecision.UNKNOWN))
        self.assertIsNone(attach(withdrawn,(self.fact,)).ascent_end)
        self.assertEqual(select_next(merge_schedule(initial,(attach(withdrawn,(self.fact,)),),NOW+1)).entry.record.launch_id.value,STARSHIP)
        cancelled=replace(moved,status=LaunchStatus.CANCELLED)
        self.assertEqual(select_next(merge_schedule(initial,(attach(cancelled,(self.fact,)),),NOW+1)).entry.record.launch_id.value,STARSHIP)
        for source_id in (6,9):
            raw=deepcopy(basic.BasicLaunchLogicTest.rows[VULCAN]);raw['status']['id']=source_id
            started=replace(normalize_launch(raw,NOW),timing=self.first.timing)
            self.assertEqual(select_next(advance_schedule(state(attach(started,(self.fact,)),self.second),NOW+1800)).entry.record.launch_id.value,VULCAN)

    def test_current_wire_projection_and_bounds(self):
        from tools.spacefox.wire import project_schedule, validate_current_feed
        from tools.spacefox.catalog import canonical_bytes
        record=attach(self.first,(self.fact,))
        packet=json.loads(Path('tests/fixtures/map-only/feed.json').read_text())
        projected=project_schedule(state(record,self.second),basic.BasicLaunchLogicTest.catalog,NOW+901,
                                   publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':NOW})
        raw=canonical_bytes(dict(packet,**projected))
        self.assertLessEqual(len(raw),8192)
        checked=validate_current_feed(raw,now=NOW+901)
        self.assertEqual(checked['launch']['launch_id'],'ll2:launch:'+VULCAN)
        self.assertEqual(checked['launch']['ascent_end'],self.fact)
        tampered=json.loads(raw);tampered['launch']['ascent_end']['target_utc']+=1
        with self.assertRaises(ScheduleError):validate_current_feed(canonical_bytes(tampered),now=NOW+901)

    def test_deterministic_event_sequences(self):
        # Independent literals describe the expected selected identity after
        # each event. All requested dispositions must occur in this run.
        coverage=set()
        for final in ('reschedule','withdrawal','cancellation'):
            schedule=state(self.first,self.second)
            fresh=attach(replace(self.first,source_validated_utc=NOW+1),(self.fact,))
            schedule=merge_schedule(schedule,(fresh,),NOW+1);coverage.add(('source_refresh','applied'))
            self.assertEqual(select_next(schedule).entry.record.launch_id.value,VULCAN)
            replay=merge_schedule(schedule,(fresh,),NOW+2);coverage.add(('replay','observed_no_mutation'))
            self.assertEqual(replay.entries,schedule.entries)
            schedule=advance_schedule(replay,NOW+901);coverage.add(('clock_advance','applied'))
            self.assertEqual(select_next(schedule).entry.record.launch_id.value,VULCAN)
            if final=='reschedule':
                update=replace(self.first,timing=Timing(TimePrecision.EXACT,exact_utc=NOW+4000),source_validated_utc=NOW+902,source_updated_utc=NOW+902,source_updated_iso=None)
            elif final=='withdrawal':
                update=replace(self.first,timing=Timing(TimePrecision.UNKNOWN),source_validated_utc=NOW+902,source_updated_utc=NOW+902,source_updated_iso=None)
            else:
                update=replace(self.first,status=LaunchStatus.CANCELLED,source_validated_utc=NOW+902,source_updated_utc=NOW+902,source_updated_iso=None)
            schedule=merge_schedule(schedule,(attach(update,(self.fact,)),),NOW+902);coverage.add((final,'applied'))
            self.assertEqual(select_next(schedule).entry.record.launch_id.value,STARSHIP)
            self.assertIsNone(next(e.record.ascent_end for e in schedule.entries if e.record.launch_id.value==VULCAN))
        self.assertEqual(coverage,{('source_refresh','applied'),('replay','observed_no_mutation'),('clock_advance','applied'),('reschedule','applied'),('withdrawal','applied'),('cancellation','applied')})

    def test_real_publisher_reopen_preserves_supplement(self):
        from tools.spacefox.publisher import GitState, Publisher
        def git(path,*args):
            return subprocess.check_output(['git','-C',str(path),*args],stderr=subprocess.DEVNULL,text=True).strip()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);remote=root/'remote.git';source=root/'source';source.mkdir()
            subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
            git(source,'init','-q');git(source,'config','user.name','Local test');git(source,'config','user.email','test@example.invalid')
            git(source,'commit','--allow-empty','-qm','source');code=git(source,'rev-parse','HEAD');git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
            store=GitState(str(remote))
            try:
                store.bootstrap(code);pub=Publisher(store,code);pub.reconcile(None)
                token=pub.reserve(pub.head,NOW,trigger='manual');record=attach(self.first,(self.fact,))
                pub.accept_source(pub.head,token,(record,self.second),NOW,selection_validated_utc=NOW)
                reopened=Publisher(store,code)
                restored=next(e.record for e in reopened.schedule.entries if e.record.launch_id.value==VULCAN)
                self.assertEqual(dict(restored.ascent_end),self.fact)
                self.assertEqual(restored.source_validated_utc,self.first.source_validated_utc)
                self.assertEqual(select_next(advance_schedule(reopened.schedule,NOW+901)).entry.record.launch_id.value,VULCAN)
            finally:store.close()

    def test_actual_update_pipeline(self):
        from tools.spacefox.publisher import GitState, Publisher
        from tools.update_feed import update
        from tools.spacefox.native_motion import validate_feed
        def git(path,*args):
            return subprocess.check_output(['git','-C',str(path),*args],stderr=subprocess.DEVNULL,text=True).strip()
        class Response:
            status=200
            headers={'Content-Type':'application/json','Date':format_datetime(datetime.fromtimestamp(NOW,timezone.utc),usegmt=True)}
        class Client:
            first_url='https://example.invalid/technical-provider'
            def request(self,pub,when,**kwargs):return pub.reserve(pub.head,when,trigger='manual'),Response()
            def page(self,response,when):return {'count':2,'next':None},(self_first,self_second)
        self_first=self.first;self_second=self.second
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);remote=root/'remote.git';source=root/'source';source.mkdir()
            subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
            git(source,'init','-q');git(source,'config','user.name','Local test');git(source,'config','user.email','test@example.invalid')
            git(source,'commit','--allow-empty','-qm','source');code=git(source,'rev-parse','HEAD');git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
            store=GitState(str(remote))
            try:
                store.bootstrap(code);pub=Publisher(store,code);pub.reconcile(None)
                later=dict(self.fact,reviewed_utc=NOW+1)
                result=update(pub,Client(),NOW+1,basic.BasicLaunchLogicTest.catalog,trigger='manual',ascent_supplement=(later,))
                self.assertEqual(result['result'],'pending')
                reopened=Publisher(store,code);record=next(e.record for e in reopened.schedule.entries if e.record.launch_id.value==VULCAN)
                self.assertEqual(dict(record.ascent_end),later)
                feed=validate_feed(reopened.pending_files()['feed.json'])
                self.assertEqual(feed['launch']['ascent_end'],later)
                self.assertEqual(feed['launch']['source_validated_utc'],self.first.source_validated_utc)
                self.assertLessEqual(len(reopened.pending_files()['feed.json']),8192)
            finally:store.close()

    def test_default_cli_and_update_load_tracked_supplement(self):
        from types import SimpleNamespace
        from tools import update_feed
        from tools.spacefox import ascent_supplement
        class Store:
            def __init__(self,*a,**k):pass
            def close(self):pass
        class Pub:
            def __init__(self,*a,**k):self.head='head';self.ledger={'code_revision':'code'}
            def reconcile(self,*a):return 'ready'
        seen=[]
        def fake_update(*args,**kwargs):seen.append(kwargs['ascent_supplement']);return {'result':'not_due'}
        with patch.object(update_feed,'executing_revision',return_value='code'),patch.object(update_feed,'GitState',Store),patch.object(update_feed,'Publisher',Pub),patch.object(update_feed,'LL2Client'),patch.object(update_feed,'build_catalog',return_value={}),patch('tools.spacefox.current_catalog.load_registry',return_value={}),patch.object(update_feed,'update',side_effect=fake_update):
            self.assertEqual(update_feed.main(['--remote','unused','--expected-base','head','run','--output','unused']),0)
        self.assertEqual(seen,[None])
        observed=[]
        def load(path):observed.append(path);return ()
        class NoRequest:
            def request(self,*args,**kwargs):return None
        with patch.object(ascent_supplement,'load_supplement',side_effect=load):
            self.assertEqual(update_feed.update(SimpleNamespace(head='head'),NoRequest(),NOW,{})['result'],'not_due')
        self.assertEqual(observed,[Path(update_feed.__file__).resolve().parents[1]/'catalog/ascent-end-supplement.json'])

    def test_malformed_refusal_and_binding(self):
        for edit in ({'launch_id':'ll2:launch:wrong'}, {'target_utc':NOW+1}, {'end_utc':NOW-1},
                     {'source_url':'http://example.invalid/'}):
            with self.subTest(edit=edit),self.assertRaises(ScheduleError):replace(self.first,ascent_end=dict(self.fact,**edit))
        self.assertIsNone(attach(self.first,(dict(self.fact,launch_id='ll2:launch:wrong'),)).ascent_end)
        self.assertIsNone(attach(self.first,(dict(self.fact,target_utc=NOW+1),)).ascent_end)
        self.assertEqual(load_supplement(Path('catalog/ascent-end-supplement.json')),())
        self.assertEqual(attach(self.first,load_supplement(Path('catalog/ascent-end-supplement.json'))),self.first)
        self.assertIsNone(attach(self.first,()).ascent_end)
        self.assertNotIn('ascent_end',self.first.content())
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'source.json';path.write_text(json.dumps({'version':1,'entries':[self.fact]}))
            self.assertEqual(attach(self.first,load_supplement(path)).ascent_end['end_utc'],NOW+1800)
            path.write_text(json.dumps({'version':1,'entries':[self.fact,self.fact]}))
            with self.assertRaises(ScheduleError):load_supplement(path)

if __name__=='__main__':unittest.main()
