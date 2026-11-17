"""Finite producer witnesses using one exact captured LL2 row and local HTTP/Git."""
from copy import deepcopy
from dataclasses import replace
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import gzip
import hashlib
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest

from tests.test_current_motion_publisher import captured_starship, git, NOW, ROOT
from tools.spacefox.catalog import build_catalog
from tools.spacefox.native_motion import build_artifact, validate_artifact
from tools.spacefox.feed import encode_feed, FeedEncodingError, FeedTooLargeError
from tools.spacefox.provider import (LL2Client, ProviderError, Response, Throttled,
    normalize_launch, normalize_detail_launch, validation_epoch)
from tools.spacefox.publisher import GitState, Publisher, LiveRevision, AllowanceUnavailable, StateError
from tools.spacefox.schedule import (AcceptedLaunch, ScheduleState, ScheduleError, RefreshPolicy, TimePrecision,
    Timing, LaunchStatus, StableId, IdKind, cadence_seconds, request_due, merge_schedule, select_next, advance_schedule)
from tools.update_feed import update


class ScheduleProducerWholeTest(unittest.TestCase):
    def test_current_projection_preserves_timing_phase(self):
        row = captured_starship()
        row['net_precision'] = {'id': 0, 'name': 'Second', 'abbrev': 'SEC'}
        record = normalize_launch(row, NOW)
        target = 1794609900
        self.assertEqual(record.timing.exact_utc, target)
        state = merge_schedule(ScheduleState(), (record,), NOW)
        catalog = build_catalog(ROOT)
        publisher = {'instance': 'a' * 64, 'generation': 1, 'selectionValidatedUtc': NOW}
        for at, expected in ((target - 1, 'countdown'), (target, 'awaiting-update')):
            with self.subTest(at=at):
                files, _ = build_artifact(state, catalog, at, publisher=publisher, root=ROOT)
                feed = validate_artifact(files)
                self.assertEqual(feed['timingState'], expected)
                self.assertEqual(feed['launch']['launch_id'], 'll2:launch:' + row['id'])
                self.assertEqual(feed['launch']['timing']['exact_utc'], target)
                self.assertEqual(feed['launch']['source_validated_utc'], NOW)

    def test_cadence_positive(self):
        row = captured_starship(); row['net_precision'] = {'id':0,'name':'Second','abbrev':'SEC'}
        record = normalize_launch(row, NOW); target = record.timing.exact_utc
        self.assertEqual([cadence_seconds(record,target+n) for n in (-7201,-7200,1800,1801)], [3600]*4)
        self.assertFalse(request_due(True,NOW,True,True,NOW+3599))
        self.assertTrue(request_due(True,NOW,True,True,NOW+3600))
        self.assertTrue(request_due(False,NOW,True,True,NOW+1))
        self.assertTrue(request_due(True,NOW,False,True,NOW+1))
        self.assertFalse(request_due(False,NOW,False,False,NOW+299))
        self.assertTrue(request_due(False,NOW,False,False,NOW+300))
        self.assertTrue(request_due(False,NOW,False,True,NOW+1))

    def test_cadence_negative(self):
        for args in ((1,NOW,True,True,NOW+1),(True,NOW,1,True,NOW+1)):
            with self.assertRaises(ScheduleError): request_due(*args)
        self.assertTrue(request_due(True,None,False,True,NOW))
        self.assertTrue(request_due(True,NOW+1,True,True,NOW))

    def test_empty_future_retries_without_duplicate_inflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp); remote=path/'remote.git'; source=path/'source'; source.mkdir()
            subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
            git(source,'init','-q'); git(source,'config','user.name','Local test'); git(source,'config','user.email','local@example.invalid')
            git(source,'commit','--allow-empty','-qm','source'); code=git(source,'rev-parse','HEAD')
            git(source,'push','-q',str(remote),'HEAD:refs/heads/main');store=GitState(str(remote))
            try:
                store.bootstrap(code); pub=Publisher(store,code); pub.reconcile(None)
                token=pub.reserve(pub.head,NOW,trigger='manual')
                with self.assertRaises(StateError): pub.reserve(pub.head,NOW,trigger='manual')
                pub.finish_request(pub.head,token,NOW,'success')
                pub=Publisher(store,code); pub.reconcile(None)
                token=pub.reserve(pub.head,NOW+1,trigger='manual');self.assertIsNotNone(token)
                pub.finish_request(pub.head,token,NOW+1,'failed')
                pub=Publisher(store,code);pub.reconcile(None)
                self.assertIsNotNone(pub.reserve(pub.head,NOW+2,trigger='manual'))
            finally: store.close()

    def test_identity_omission_revalidation_and_atomic_rejection(self):
        row = captured_starship()
        a = normalize_launch(row, NOW)
        row2 = deepcopy(row); row2['id'] = '00000000-0000-4000-8000-000000000001'
        row2['rocket'] = None; row2['pad'] = None; row2['launch_service_provider'] = None
        b = normalize_launch(row2, NOW)
        self.assertIsNone(b.configuration_id); self.assertIsNone(b.site_id); self.assertIsNone(b.operator_id)
        state = merge_schedule(ScheduleState(), (a,b), NOW)
        self.assertEqual(len(state.entries), 2)
        self.assertIn(select_next(state).entry.record.launch_id, (a.launch_id,b.launch_id))
        newer = replace(b, source_validated_utc=NOW+3600)
        updated = merge_schedule(state, (newer,), NOW+3600)
        by_id = {e.record.launch_id: e for e in updated.entries}
        self.assertEqual(by_id[a.launch_id].record.source_validated_utc, NOW)
        self.assertEqual(by_id[b.launch_id].record.source_validated_utc, NOW+3600)
        self.assertEqual(state.entries[0].record.source_validated_utc, NOW)
        for batch in ((a,a), (replace(a, source_validated_utc=NOW-1),),
                      (replace(a, source_validated_utc=NOW+3601),)):
            with self.subTest(batch=batch), self.assertRaises(ScheduleError):
                merge_schedule(updated, batch, NOW+3600)
        cancelled = replace(a, status=LaunchStatus.CANCELLED, source_validated_utc=NOW+3601,
                            source_updated_utc=NOW+3601, source_updated_iso='2026-11-13T07:26:33Z', source_updated_subsecond=0)
        after = merge_schedule(updated, (cancelled,), NOW+3601)
        self.assertEqual(select_next(after).entry.record.launch_id, b.launch_id)
        self.assertEqual(state.entries[0].record.source_validated_utc, NOW)

    def test_current_projection_deterministic(self):
        record=normalize_launch(captured_starship(),NOW)
        state=merge_schedule(ScheduleState(),(record,),NOW)
        catalog=build_catalog(ROOT);pub={'instance':'a'*64,'generation':1,'selectionValidatedUtc':NOW}
        first,digest=build_artifact(state,catalog,NOW,publisher=pub,root=ROOT)
        again,digest2=build_artifact(state,catalog,NOW,publisher=pub,root=ROOT)
        self.assertEqual(first,again);self.assertEqual(digest,digest2)
        feed=validate_artifact(first)
        self.assertEqual((feed['schemaVersion'],feed['rendererProfile']),(3,'SFR1M'))
        self.assertEqual(feed['launch']['launch_id'],'ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b')
        self.assertEqual(feed['launch']['source_validated_utc'],NOW)
        self.assertLessEqual(len(first['feed.json']),8192)
        self.assertEqual(feed['launch']['timing']['source_net'],'2026-11-13T22:45:00Z')
        self.assertEqual(feed['launch']['timing']['nominal_utc'],1794609900)
        self.assertEqual(feed['launch']['site_id'],'ll2:site:235')
        scene=json.loads(first[feed['visualSelection']['path']])
        self.assertEqual(scene['siteId'],'ll2:site:235')
        self.assertEqual((scene['position']['latitude'],scene['position']['longitude']),('25.99677','-97.15799'))
        self.assertEqual(scene['position']['qualification'],'unverified-reference')

    def test_real_utf8_launch_survives_current_projection(self):
        corpus=ROOT/'corpus/real-schedule-basic-five-20261113'
        collection=json.loads((corpus/'collection.json').read_bytes());row=None
        for attempt in collection['attempts']:
            if not attempt.get('raw'):continue
            raw=gzip.decompress((corpus/attempt['raw']).read_bytes())
            self.assertEqual(hashlib.sha256(raw).hexdigest(),attempt['responseSha256'])
            for candidate in json.loads(raw)['results']:
                if candidate['id']=='16d0c02e-0bb1-45d5-a3f5-7c4ff6cf6de1':row=deepcopy(candidate);break
            if row is not None:break
        self.assertIsNotNone(row);self.assertEqual(row['mission']['name'],'Türksat 5B')
        row['status']['id']=1  # Technical eligibility mutation, not a source-status claim.
        at=1794576343;record=normalize_launch(row,at)
        state=merge_schedule(ScheduleState(),(record,),at)
        files,_=build_artifact(state,build_catalog(ROOT),at,
            publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':at},root=ROOT)
        feed=validate_artifact(files)
        self.assertEqual(feed['launch']['launch_id'],'ll2:launch:16d0c02e-0bb1-45d5-a3f5-7c4ff6cf6de1')
        self.assertEqual(feed['launch']['mission_name'],'Türksat 5B')
        self.assertIn('Türksat 5B'.encode(),files['feed.json'])

    def test_missing_optional_context_current_artifact(self):
        row=captured_starship();row['rocket']=None;row['pad']=None;row['launch_service_provider']=None
        row['mission']=None
        record=normalize_launch(row,NOW);state=merge_schedule(ScheduleState(),(record,),NOW)
        files,_=build_artifact(state,build_catalog(ROOT),NOW,
            publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':NOW},root=ROOT)
        feed=validate_artifact(files);launch=feed['launch']
        self.assertEqual(launch['launch_id'],'ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b')
        for name in ('configuration_id','configuration_name','operator_id','operator_name','site_id','country_id','mission_name','mission_purpose'):
            self.assertIsNone(launch[name])
        self.assertNotIn('site_name',launch);self.assertNotIn('country_name',launch)
        scene=json.loads(files[feed['visualSelection']['path']])
        self.assertIsNone(scene['roles']['rocket']);self.assertIsNone(scene['roles']['map'])
        self.assertIsNone(scene['roles']['siteCountry']);self.assertIsNone(scene['position'])

    def test_unknown_identity_current_artifact_positive(self):
        row=captured_starship();row['rocket']['configuration']['id']=999999
        row['pad']['id']=999999;row['launch_service_provider']['id']=999999
        record=normalize_launch(row,NOW)
        state=merge_schedule(ScheduleState(),(record,),NOW)
        files,_=build_artifact(state,build_catalog(ROOT),NOW,
            publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':NOW},root=ROOT)
        feed=validate_artifact(files)
        self.assertEqual(feed['launch']['launch_id'],'ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b')
        for identity in ('ll2:configuration:999999','ll2:site:999999','ll2:organization:999999'):
            self.assertIn(identity,feed['unresolvedCatalogIds'])
        self.assertEqual(feed['launch']['configuration_name'],record.configuration_name)
        self.assertEqual(feed['launch']['operator_name'],record.operator_name)
        self.assertEqual(feed['launch']['site_name'],record.site_name)
        self.assertLessEqual(len(files['feed.json']),8192)
        scene=json.loads(files[feed['visualSelection']['path']])
        self.assertIsNone(scene['roles']['rocket']);self.assertIsNone(scene['roles']['map']);self.assertIsNone(scene['position'])

    def test_missing_art_and_point_do_not_filter_launch_negative(self):
        row=captured_starship();row['rocket']['configuration']['id']=999999;row['pad']['id']=999999
        row['launch_service_provider']['id']=999999
        record=normalize_launch(row,NOW);state=merge_schedule(ScheduleState(),(record,),NOW)
        files,_=build_artifact(state,build_catalog(ROOT),NOW,
            publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':NOW},root=ROOT)
        feed=validate_artifact(files);scene=json.loads(files[feed['visualSelection']['path']])
        self.assertEqual(feed['launch']['launch_id'],'ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b')
        self.assertIsNone(scene['roles']['rocket']);self.assertIsNone(scene['roles']['map'])
        self.assertIsNone(scene['position'])
        for identity in ('ll2:configuration:999999','ll2:site:999999','ll2:organization:999999'):
            self.assertIn(identity,feed['unresolvedCatalogIds'])
        self.assertEqual(feed['launch']['configuration_name'],record.configuration_name)
        self.assertEqual(feed['launch']['operator_name'],record.operator_name)
        self.assertEqual(feed['launch']['site_name'],record.site_name)

    def test_normalized_identity_and_immutable_state_positive(self):
        from dataclasses import FrozenInstanceError
        self.assertEqual(set(IdKind.__members__), {'LAUNCH','CONFIGURATION','ORGANIZATION','SITE','COUNTRY'})
        a=normalize_launch(captured_starship(),NOW)
        a=replace(a,configuration_id=StableId(IdKind.CONFIGURATION,'ll2','121'),
                  operator_id=StableId(IdKind.ORGANIZATION,'ll2','121'))
        state=merge_schedule(ScheduleState(),(a,),NOW)
        with self.assertRaises(FrozenInstanceError): a.source_validated_utc=NOW+1
        with self.assertRaises(FrozenInstanceError): state.entries[0].stale=True
        fresh=merge_schedule(state,(replace(a,source_validated_utc=NOW+1),),NOW+1)
        self.assertEqual(state.entries[0].record.source_validated_utc,NOW)
        self.assertEqual(fresh.entries[0].record.source_validated_utc,NOW+1)
        self.assertEqual(fresh.content_revision,state.content_revision)
        content=a.content()
        self.assertEqual(content['configuration_id'],{'kind':'configuration','namespace':'ll2','value':'121'})
        self.assertEqual(content['operator_id'],{'kind':'organization','namespace':'ll2','value':'121'})
        self.assertIs(type(content['status']),str);self.assertIs(type(content['timing']['precision']),str)
        self.assertEqual(json.loads(encode_feed({'launch':content}))['launch']['launch_id'],
                         {'kind':'launch','namespace':'ll2','value':'0f867f0c-5422-4d44-93b8-d7faaae7019b'})

    def test_normalized_atomic_admission_negative(self):
        a=normalize_launch(captured_starship(),NOW)
        state=merge_schedule(ScheduleState(),(a,),NOW)
        bad=((replace(a,source_validated_utc=NOW-1),),
             (replace(a,status=LaunchStatus.COMPLETED),),(a,a),
             (replace(a,source_validated_utc=NOW+1),),(a,'not-a-record'))
        for batch in bad:
            with self.subTest(batch=batch),self.assertRaises(ScheduleError):merge_schedule(state,batch,NOW)
            self.assertEqual(state.entries,(AcceptedLaunch(a),))
        for change in ({'operator_id':StableId(IdKind.CONFIGURATION,'ll2','121')},
                       {'source_validated_utc':True},{'operator_name':'  '},{'timing':'exact'},{'status':'pending'}):
            with self.subTest(change=change),self.assertRaises(ScheduleError):replace(a,**change)
        for build in (lambda: Timing(TimePrecision.EXACT,exact_utc=True),
                      lambda: Timing(TimePrecision.WINDOW),
                      lambda: Timing(TimePrecision.WINDOW,window_start_utc=2,window_end_utc=1),
                      lambda: ScheduleState(entries=[AcceptedLaunch(a)],evaluated_at_utc=NOW)):
            with self.subTest(build=build),self.assertRaises(ScheduleError):build()

    def test_earlier_target_stale_and_unchanged_validation(self):
        row = captured_starship()
        row['net_precision'] = {'id': 0, 'name': 'Second', 'abbrev': 'SEC'}
        a = normalize_launch(row, NOW)
        initial = merge_schedule(ScheduleState(), (a,), NOW)
        moved = deepcopy(row)
        moved['net'] = '2026-11-13T22:25:00Z'
        moved['window_start'] = None; moved['window_end'] = None
        moved['last_updated'] = '2026-11-13T06:26:33Z'
        earlier = normalize_launch(moved, NOW+1)
        added_row = deepcopy(moved)
        added_row['id'] = '00000000-0000-4000-8000-000000000004'
        added = normalize_launch(added_row, NOW+1)
        expanded = merge_schedule(initial, (added,), NOW+1)
        self.assertEqual(select_next(expanded).entry.record.launch_id, added.launch_id)
        self.assertEqual(len(expanded.entries), 2)
        advanced = merge_schedule(initial, (earlier,), NOW+1)
        self.assertEqual(select_next(advanced).entry.record.timing.exact_utc, 1794608700)
        self.assertTrue(advanced.entries[0].rescheduled)
        replay = merge_schedule(advanced, (earlier,), NOW+10801)
        self.assertTrue(replay.entries[0].stale)
        self.assertEqual(replay.entries[0].record.source_validated_utc, NOW+1)
        fresh = replace(earlier, source_validated_utc=NOW+10802)
        renewed = merge_schedule(replay, (fresh,), NOW+10802)
        self.assertFalse(renewed.entries[0].stale)
        self.assertTrue(renewed.entries[0].rescheduled)
        self.assertEqual(renewed.content_revision, advanced.content_revision)
        corrupt = deepcopy(moved); corrupt['id'] = 'not-a-uuid'
        with self.assertRaises(ProviderError): normalize_launch(corrupt, NOW+10802)
        corrupt = deepcopy(moved); corrupt['last_updated'] = '2099-01-01T00:00:00Z'
        with self.assertRaises(ProviderError): normalize_launch(corrupt, NOW+10802)

    def test_stale_thresholds_and_skipped_near_window(self):
        row = captured_starship()
        a = normalize_launch(row, NOW)
        initial = merge_schedule(ScheduleState(), (a,), NOW)
        self.assertFalse(advance_schedule(initial, NOW+10799).entries[0].stale)
        self.assertTrue(advance_schedule(initial, NOW+10800).entries[0].stale)
        fast = RefreshPolicy(fast_interval_seconds=300)
        self.assertFalse(advance_schedule(initial, NOW+899, fast).entries[0].stale)
        self.assertTrue(advance_schedule(initial, NOW+900, fast).entries[0].stale)
        row['net_precision'] = {'id':0,'name':'Second','abbrev':'SEC'}
        exact = normalize_launch(row, NOW)
        target = exact.timing.exact_utc
        # Validate at near-window entrance, then cross its threshold and exit.
        near = replace(exact, source_validated_utc=target-7200)
        state = merge_schedule(ScheduleState(), (near,), target-7200)
        self.assertFalse(advance_schedule(state, target-4501).entries[0].stale)
        self.assertTrue(advance_schedule(state, target-4500).entries[0].stale)
        jumped = advance_schedule(state, target+1801)
        self.assertEqual(cadence_seconds(near, target+1801),3600)
        self.assertTrue(jumped.entries[0].stale)
        self.assertTrue(merge_schedule(jumped, (near,), target+1801).entries[0].stale)

    def test_stale_latch_after_near_window_with_literal_epoch(self):
        a = normalize_launch(captured_starship(), NOW)
        a = replace(a, timing=Timing(TimePrecision.EXACT, exact_utc=1800007200),
                    source_validated_utc=1800000000)
        initial = merge_schedule(ScheduleState(), (a,), 1800000000)
        crossed = advance_schedule(initial,1800009001)
        self.assertEqual(cadence_seconds(a,1800009001),3600)
        self.assertTrue(crossed.entries[0].stale)
        replay = merge_schedule(crossed,(a,),1800009002)
        self.assertTrue(replay.entries[0].stale)
        self.assertEqual(replay.entries[0].record.source_validated_utc,1800000000)

    def test_record_omission_positive(self):
        a=normalize_launch(captured_starship(),NOW)
        a=replace(a,timing=Timing(TimePrecision.EXACT,exact_utc=1800007200),source_validated_utc=1800000000)
        b=replace(a,launch_id=StableId(IdKind.LAUNCH,'ll2','00000000-0000-4000-8000-000000000005'),
                  timing=Timing(TimePrecision.EXACT,exact_utc=1800010000),source_validated_utc=1800003600)
        initial=merge_schedule(ScheduleState(),(a,),1800000000)
        joined=merge_schedule(initial,(b,),1800003600); by_id={e.record.launch_id:e for e in joined.entries}
        self.assertEqual(by_id[a.launch_id].record.status,LaunchStatus.PENDING)
        self.assertEqual(by_id[a.launch_id].record.source_validated_utc,1800000000)
        self.assertTrue(by_id[a.launch_id].stale)
        self.assertEqual(by_id[b.launch_id].record.source_validated_utc,1800003600)
        self.assertFalse(by_id[b.launch_id].stale)

    def test_record_omission_negative(self):
        a=normalize_launch(captured_starship(),NOW)
        a=replace(a,timing=Timing(TimePrecision.EXACT,exact_utc=1800007200),source_validated_utc=1800000000)
        initial=merge_schedule(ScheduleState(),(a,),1800000000)
        retained=merge_schedule(initial,(),1800003600)
        self.assertEqual(retained.content_revision,initial.content_revision)
        self.assertEqual(len(retained.entries),1);self.assertTrue(retained.entries[0].stale)
        self.assertEqual(retained.entries[0].record.source_validated_utc,1800000000)
        empty=select_next(advance_schedule(ScheduleState(),1800000000))
        self.assertIsNone(empty.entry);self.assertIsNone(empty.remaining_seconds)

    def test_fractional_source_modification_is_exact_and_monotonic(self):
        row=captured_starship();row['last_updated']='2026-11-10T22:06:46.123456Z'
        a=normalize_launch(row,NOW)
        self.assertEqual(a.source_updated_utc,1794348406)
        self.assertEqual(a.source_updated_subsecond,123456)
        self.assertEqual(a.source_updated_iso,'2026-11-10T22:06:46.123456Z')
        state=merge_schedule(ScheduleState(),(a,),NOW)
        newer=deepcopy(row);newer['last_updated']='2026-11-10T22:06:46.123457Z';newer['status']['id']=3
        b=normalize_launch(newer,NOW+1);state2=merge_schedule(state,(b,),NOW+1)
        self.assertEqual(state2.entries[0].record.source_updated_subsecond,123457)
        self.assertEqual(state2.entries[0].record.source_updated_iso,'2026-11-10T22:06:46.123457Z')
        older=normalize_launch(row,NOW+2)
        with self.assertRaises(ScheduleError):merge_schedule(state2,(older,),NOW+2)
        self.assertEqual(state2.entries[0].record,b)

    def test_origin_age_and_future_rejection(self):
        headers = {'Date': formatdate(NOW+120, usegmt=True), 'Age': '120', 'Content-Type': 'application/json'}
        self.assertEqual(validation_epoch(Response(200, headers, b'{}'), NOW+120), NOW)
        future = dict(headers, Date=formatdate(NOW+121, usegmt=True), Age='0')
        with self.assertRaises(ProviderError): validation_epoch(Response(200, future, b'{}'), NOW+120)
        skew=dict(headers,Date=formatdate(NOW+181,usegmt=True),Age='0')
        with self.assertRaises(ProviderError): validation_epoch(Response(200,skew,b'{}'),NOW+120)
        row=captured_starship();row['last_updated']='2026-11-13T06:26:33Z'
        with self.assertRaises(ProviderError):normalize_launch(row,NOW)
        with self.assertRaises(ProviderError): validation_epoch(Response(304, headers, b''), NOW+120)

    def test_detail_mode_positive(self):
        row=captured_starship(); normal=normalize_launch(row,NOW)
        self.assertEqual(normalize_detail_launch(row,NOW),normal)
        row['response_mode']='detailed'; detail=normalize_detail_launch(row,NOW)
        self.assertEqual(detail,normal)
        self.assertEqual(detail.launch_id.value,'0f867f0c-5422-4d44-93b8-d7faaae7019b')
        self.assertEqual(detail.source_validated_utc,NOW)

    def test_detail_mode_negative(self):
        row=captured_starship();row['response_mode']='detailed'
        with self.assertRaises(ProviderError):normalize_launch(row,NOW)

    def test_decoded_boundary_positive(self):
        row=captured_starship()
        self.assertEqual(row['id'],'0f867f0c-5422-4d44-93b8-d7faaae7019b')
        prefix=(b'{"launchId":"0f867f0c-5422-4d44-93b8-d7faaae7019b","metadata":'
                b'{"escape":"\\"\\n","flag":false,"missing":null,"negativeZero":-0.0,'
                b'"precision":"MIN","sourceValidatedUtc":1794551192,"targetUtc":1794609900,"text":"')
        suffix=(b'","typed":{"kind":"launch","namespace":"ll2","value":'
                b'"0f867f0c-5422-4d44-93b8-d7faaae7019b"},"wide":9007199254740993,'
                b'"windowEnd":null,"zero":0}}')
        padding='é'+'a'*(8192-len(prefix)-len(suffix)-2)
        obj={'launchId':row['id'],'metadata':{'escape':'"\n','flag':False,'missing':None,
             'negativeZero':-0.0,'precision':'MIN','sourceValidatedUtc':NOW,'targetUtc':1794609900,'text':padding,
             'typed':{'kind':'launch','namespace':'ll2','value':row['id']},
             'wide':9007199254740993,'windowEnd':None,'zero':0}}
        before=deepcopy(obj);expected=prefix+padding.encode('utf-8')+suffix
        self.assertEqual(len(expected),8192);self.assertEqual(encode_feed(obj),expected)
        self.assertEqual(json.loads(expected),obj);self.assertEqual(obj,before)
        self.assertEqual(obj['metadata']['sourceValidatedUtc'],1794551192)

    def test_decoded_boundary_negative(self):
        import gzip
        # Literal complete wire is 8193 decoded bytes; compression cannot admit it.
        obj={'x':'é'+'a'*8183}; before=deepcopy(obj)
        raw=b'{"x":"'+obj['x'].encode('utf-8')+b'"}'
        self.assertEqual(len(raw),8193);self.assertLess(len(gzip.compress(raw)),8192)
        with self.assertRaises(FeedTooLargeError) as failure:encode_feed(obj)
        self.assertEqual(failure.exception.decoded_bytes,8193);self.assertEqual(obj,before)
        for payload in ({'x':'a'*8184+'"'}, {'metadata':{'x':'a'*8200}},
                        {'dictionary':{'x':'a'*8200}}):
            snapshot=deepcopy(payload)
            with self.subTest(payload=list(payload)),self.assertRaises(FeedTooLargeError):encode_feed(payload)
            self.assertEqual(payload,snapshot)
        cycle=[];cycle.append(cycle)
        for invalid in ({'x':float('nan')},{'x':(1,2)},{1:'x'},{'x':cycle},{'x':'\ud800'}):
            with self.subTest(kind=type(invalid.get('x'))),self.assertRaises(FeedEncodingError):encode_feed(invalid)

    def test_omitted_pending_detail_and_terminal_no_detail(self):
        row = captured_starship()
        pending = normalize_launch(row, NOW)
        terminal_row = deepcopy(row)
        terminal_row['id'] = '00000000-0000-4000-8000-000000000002'
        terminal_row['status']['id'] = 3
        terminal = normalize_launch(terminal_row, NOW)
        cancelled_row = deepcopy(row)
        cancelled_row['id'] = '00000000-0000-4000-8000-000000000003'
        cancelled = replace(normalize_launch(cancelled_row, NOW), status=LaunchStatus.CANCELLED)
        started_row=deepcopy(row);started_row['id']='00000000-0000-4000-8000-000000000015';started_row['status']['id']=6
        unknown_row=deepcopy(row);unknown_row['id']='00000000-0000-4000-8000-000000000016';unknown_row['status']['id']=0
        started=normalize_launch(started_row,NOW);unknown=normalize_launch(unknown_row,NOW)
        details={r['id']:r for r in (row,started_row,unknown_row)}
        calls = []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                data = (json.dumps({'count':0,'next':None,'previous':None,'results':[]}).encode()
                        if '/upcoming/' in self.path else json.dumps(details[self.path.split('/')[-2]]).encode())
                self.send_response_only(200)
                self.send_header('Date', formatdate(NOW+3600, usegmt=True))
                self.send_header('Content-Type','application/json'); self.end_headers(); self.wfile.write(data)
            def log_message(self, *args): pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp); remote=path/'remote.git'; source=path/'source'; source.mkdir()
                subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
                git(source,'init','-q'); git(source,'config','user.name','Local test'); git(source,'config','user.email','local@example.invalid')
                git(source,'commit','--allow-empty','-qm','source'); code=git(source,'rev-parse','HEAD')
                git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
                store=GitState(str(remote))
                try:
                    store.bootstrap(code); pub=Publisher(store,code); pub.reconcile(None)
                    token=pub.reserve(pub.head,NOW,trigger='manual')
                    pub.accept_source(pub.head,token,(pending,terminal,cancelled,started,unknown),NOW,selection_validated_utc=NOW)
                    client=LL2Client(origin=f'http://127.0.0.1:{server.server_port}',local_http=True)
                    result=update(pub,client,NOW+3600,build_catalog(ROOT),detail_limit=4)
                    self.assertEqual(result['requests'],4); self.assertEqual(result['traversal']['detailRequests'],3)
                    self.assertEqual(len(calls),4)
                    for identity in (pending.launch_id.value,started.launch_id.value,unknown.launch_id.value):
                        self.assertTrue(any(identity in call for call in calls[1:]))
                    self.assertNotIn(terminal.launch_id.value, ''.join(calls))
                    self.assertNotIn(cancelled.launch_id.value, ''.join(calls))
                    by_id={e.record.launch_id:e.record for e in pub.schedule.entries}
                    for identity in (pending.launch_id,started.launch_id,unknown.launch_id):
                        self.assertEqual(by_id[identity].source_validated_utc,NOW+3600)
                    self.assertEqual(by_id[started.launch_id].status,LaunchStatus.STARTED)
                    self.assertEqual(by_id[unknown.launch_id].status,LaunchStatus.UNKNOWN)
                    self.assertEqual(by_id[terminal.launch_id].source_validated_utc,NOW)
                    self.assertEqual(by_id[terminal.launch_id].status,LaunchStatus.COMPLETED)
                    self.assertEqual(by_id[cancelled.launch_id].source_validated_utc,NOW)
                    self.assertEqual(by_id[cancelled.launch_id].status,LaunchStatus.CANCELLED)
                finally: store.close()
        finally:
            server.shutdown(); thread.join(); server.server_close()

    def test_local_http_due_origin_304_and_429(self):
        row = captured_starship()
        calls, responses = [], []
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                calls.append(self.path)
                status, epoch, age, body, extra = responses.pop(0)
                self.send_response_only(status)
                self.send_header('Date', formatdate(epoch, usegmt=True))
                self.send_header('Age', str(age)); self.send_header('Content-Type', 'application/json')
                for k,v in extra.items(): self.send_header(k,v)
                self.end_headers(); self.wfile.write(body)
            def log_message(self, *args): pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            with tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp); remote=path/'remote.git'; source=path/'source'; source.mkdir()
                subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
                git(source,'init','-q'); git(source,'config','user.name','Local test'); git(source,'config','user.email','local@example.invalid')
                git(source,'commit','--allow-empty','-qm','source'); code=git(source,'rev-parse','HEAD')
                git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
                store=GitState(str(remote))
                try:
                    store.bootstrap(code); pub=Publisher(store,code); pub.reconcile(None)
                    inflight=pub.reserve(pub.head,NOW-1,trigger='manual')
                    with self.assertRaises(StateError): pub.reserve(pub.head,NOW-1,trigger='manual')
                    pub.finish_request(pub.head,inflight,NOW-1,'failed')
                    client=LL2Client(origin=f'http://127.0.0.1:{server.server_port}',local_http=True)
                    catalog=build_catalog(ROOT)
                    page=json.dumps({'count':1,'next':None,'previous':None,'results':[row]}).encode()
                    responses.append((200,NOW,0,page,{}))
                    result=update(pub,client,NOW,catalog,detail_limit=0)
                    self.assertEqual(result['result'],'pending'); self.assertEqual(result['requests'],1)
                    self.assertEqual(pub.schedule.entries[0].record.source_validated_utc,NOW)
                    self.assertIn('mode=normal',calls[0]); self.assertIn('ordering=net',calls[0])
                    pending=pub.ledger['pending']; live=LiveRevision(pending['generation'],pending['artifact_revision'])
                    self.assertEqual(pub.reconcile(live),'promoted')
                    head=pub.head; self.assertIsNone(pub.reserve(pub.head,NOW+1,trigger='manual')); self.assertEqual(update(pub,client,NOW+1,catalog)['result'],'not_due'); self.assertEqual(update(pub,client,NOW+3599,catalog)['result'],'not_due')
                    self.assertEqual(pub.head,head); self.assertEqual(len(calls),1)
                    responses.append((304,NOW+3600,0,b'',{}))
                    self.assertEqual(update(pub,client,NOW+3600,catalog)['result'],'not_modified_without_record_validation')
                    pub=Publisher(store,code); self.assertEqual(pub.schedule.entries[0].record.source_validated_utc,NOW)
                    self.assertEqual(pub.reconcile(live),'ready')
                    responses.append((429,NOW+7200,0,b'',{'Retry-After':'600'}))
                    with self.assertRaises(Throttled): update(pub,client,NOW+7200,catalog)
                    pub=Publisher(store,code); self.assertIsNone(pub.ledger['backoff_until_utc'])
                    self.assertEqual(pub.reconcile(live),'ready')
                    self.assertEqual(pub.schedule.entries[0].record.source_validated_utc,NOW)
                    responses.append((304,NOW+7201,0,b'',{}))
                    self.assertEqual(update(pub,client,NOW+7201,catalog)['result'],'not_modified_without_record_validation')
                    self.assertEqual(len(calls),4)
                finally: store.close()
        finally:
            server.shutdown(); thread.join(); server.server_close()
