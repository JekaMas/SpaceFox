"""Finite captured LL2 point resolution and current snapshot boundary."""
import gzip
from dataclasses import replace
import json
import unittest
from pathlib import Path
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import AcceptedLaunch, ScheduleState, ScheduleError, merge_schedule
from tools.spacefox.publisher import _schedule, schedule_document
from tools.spacefox.watch_snapshot import FIELDS, _row, encode_snapshot

ROOT=Path(__file__).resolve().parents[1]

def captured(pad_id):
    for path in sorted((ROOT/'corpus/real-schedule-basic-five-20261113/raw').glob('*.gz')):
        for launch in json.loads(gzip.decompress(path.read_bytes()))['results']:
            if (launch.get('pad') or {}).get('id') == pad_id:
                return launch
    raise AssertionError('captured pad missing')

def projected(record):
    r=record.content()
    for k in ('launch_id','configuration_id','operator_id','site_id','country_id'):
        identity=getattr(record,k);r[k]=None if identity is None else f'{identity.namespace}:{identity.kind.value}:{identity.value}'
    r.update(source_validated_utc=record.source_validated_utc,rescheduled=False,stale=False)
    return r

class CapturedCoordinates(unittest.TestCase):
    def test_unknown_reference_uses_per_launch_coordinates_after_store_roundtrip(self):
        launch=captured(237); rec=normalize_launch(launch,1800000000)
        self.assertEqual(rec.site_position,{'latitude':'60.8184','longitude':'-0.7692'})
        state=ScheduleState((AcceptedLaunch(rec,False,False),),1800000000)
        restored=_schedule(schedule_document(state))
        self.assertEqual(restored.entries[0].record.site_position,rec.site_position)
        out=dict(zip(FIELDS,_row(projected(restored.entries[0].record),{'entries':{'ll2:site:237':{'positionMode':'fixed-source','position':None}}},{},True)))
        self.assertEqual(out['point'],['-0.7692','60.8184'])

    def test_finite_2026_2036_catalog_coverage(self):
        recipe=json.loads((ROOT/'catalog/source.json').read_text())
        sites={s['sourceId']:s for s in json.loads((ROOT/recipe['reference']['path']).read_text())['sites']}
        seen=set();count=0
        for path in (ROOT/'corpus/real-schedule-basic-five-20261113/raw').glob('*.gz'):
            for launch in json.loads(gzip.decompress(path.read_bytes()))['results']:
                net=launch.get('net'); pad=launch.get('pad') or {}
                if net and '2026'<=net[:4]<='2036' and pad.get('id'):
                    seen.add(pad['id']);count+=1
        self.assertEqual((count,len(seen)),(743,78));self.assertFalse(seen-set(sites))
        good=[i for i in seen if sites[i]['latitude'] is not None and sites[i]['longitude'] is not None and not (sites[i]['latitude']==0 and sites[i]['longitude']==0)]
        self.assertEqual(len(good),77);self.assertIsNone(sites[237]['latitude']);self.assertEqual(sites[25]['name'],'Launch Complex 9')

    def test_captured_response_reaches_whole_publisher_snapshot(self):
        rec=normalize_launch(captured(237),1794812998)
        rec=_schedule(schedule_document(ScheduleState((AcceptedLaunch(rec,False,False),),1794812998))).entries[0].record
        folder=ROOT/'tests/fixtures/fr165-runtime-20261116';feed=json.loads((folder/'feed.txt').read_text());catalog=json.loads((folder/'objects'/feed['catalogPath']).read_text())
        feed['launch']=projected(rec)
        decoded=json.loads(encode_snapshot(feed,catalog))['data']
        self.assertEqual(decoded[3][0],f'll2:launch:{rec.launch_id.value}')
        self.assertEqual(decoded[3][9],['-0.7692','60.8184'])

    def test_shared_placeholder_points_survive_complete_artifact_admission(self):
        # One unchanged captured launch plus an explicitly synthetic second
        # launch at the same placeholder ID. Expected points are input literals,
        # never read from the catalog, encoder or accepted output.
        from tools.spacefox.catalog import build_catalog
        from tools.spacefox.native_motion import build_artifact
        from tools.spacefox.schedule import StableId, IdKind
        now=1800000000
        first=normalize_launch(captured(237),now)
        second=replace(first,launch_id=StableId(IdKind.LAUNCH,'ll2','ffffffff-ffff-4fff-8fff-ffffffffffff'),
                       site_position={'latitude':'60.9001','longitude':'-0.7402'})
        stored=schedule_document(ScheduleState((AcceptedLaunch(first,False,False),AcceptedLaunch(second,False,False)),now))
        state=_schedule(json.loads(json.dumps(stored)))
        files,_=build_artifact(state,build_catalog(ROOT),now,
                              publisher={'instance':'1'*64,'generation':1,'selectionValidatedUtc':now},root=ROOT)
        payload=json.loads(files['watch.json'])['data']
        self.assertEqual(payload[3][0],'ll2:launch:9536659f-bacc-4396-8bd4-04f8050cc92d')
        self.assertEqual(payload[3][8],'ll2:site:237')
        self.assertEqual(payload[3][9],['-0.7692','60.8184'])
        self.assertEqual(len(payload[4]),1)
        self.assertEqual(payload[4][0][0],'ll2:launch:ffffffff-ffff-4fff-8fff-ffffffffffff')
        self.assertEqual(payload[4][0][8],'ll2:site:237')
        self.assertEqual(payload[4][0][9],['-0.7402','60.9001'])
        # Match the existing native store/decoder fixture's captured identity
        # and point, without claiming its injected envelope is this artifact.
        native=json.loads((ROOT/'watchface/trusted-tests/resources/unknown-pad.json').read_text())['payload']
        self.assertEqual((native[3][0],native[3][9]),(payload[3][0],payload[3][9]))

    def test_known_pad_and_missing_position(self):
        rec=normalize_launch(captured(25),1800000000); launch=projected(rec)
        entry={'positionMode':'fixed-source','position':{'longitude':'111.589567','latitude':'38.863128'}}
        out=dict(zip(FIELDS,_row(launch,{'entries':{'ll2:site:25':entry}},{},True)))
        self.assertEqual(out['point'],['111.589567','38.863128'])
        launch.pop('site_position',None);out=dict(zip(FIELDS,_row(launch,{'entries':{}},{},True)))
        self.assertIsNone(out['point'])

    def test_response_point_wins_for_mobile_and_bad_point_is_absent(self):
        rec=normalize_launch(captured(237),1800000000); launch=projected(rec)
        mobile={'positionMode':'mobile-reference-no-event','position':{'latitude':'1','longitude':'2'}}
        value=dict(zip(FIELDS,_row(launch,{'entries':{'ll2:site:237':mobile}},{},True)))
        self.assertEqual(value['point'],['-0.7692','60.8184'])
        launch['site_position']={'latitude':'0','longitude':'0'}
        value=dict(zip(FIELDS,_row(launch,{'entries':{'ll2:site:237':mobile}},{},True)))
        self.assertIsNone(value['point'])

    def test_newer_validation_can_correct_per_launch_position_without_time_or_identity_change(self):
        original=normalize_launch(captured(237),1794812998)
        corrected=replace(original,source_validated_utc=1794812999,site_position={'latitude':'60.8185','longitude':'-0.7693'})
        state=ScheduleState((AcceptedLaunch(original,False,False),),1794812998)
        state=merge_schedule(state,(corrected,),1794812999)
        self.assertEqual(state.entries[0].record.site_position,corrected.site_position)
        self.assertEqual(state.entries[0].record.launch_id,original.launch_id)
        with self.assertRaises(ScheduleError):merge_schedule(state,(replace(corrected,site_position=original.site_position),),1794812999)

    def test_map_paths_do_not_paint_question_badges(self):
        for name in ('SceneRenderer.mc','SpaceFoxView.mc'):
            text=(ROOT/'watchface/source'/name).read_text()
            self.assertNotIn('FallbackMap.uncertain',text)
            self.assertNotIn('FallbackMap.unknown',text)
            self.assertNotIn('"?"',text)
        text=(ROOT/'watchface/source/SceneRenderer.mc').read_text()
        self.assertNotIn('function uncertain(',text);self.assertNotIn('function unknown(',text)
