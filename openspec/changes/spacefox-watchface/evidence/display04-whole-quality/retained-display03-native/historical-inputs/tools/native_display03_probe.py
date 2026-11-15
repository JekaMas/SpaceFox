#!/usr/bin/env python3
"""Focused test-key SDK execution; caller owns simulator lease and restoration.

This diagnostic bypasses release admission only to produce its input evidence.
It never signs a release or claims device/Store qualification.
"""
import hashlib, json, os, subprocess, sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.build_watchface import discover
from tools.run_native_tests import parse_output
NAMES=('display03MinuteRounding','display03RepeatedLowCallbacks','display03SleepThenHighObservation','display03WakeThenLowObservation','display03CausalSequence','display03ReadyAndErrorOnWake','display03BackgroundBeforeFrame','display03RealMapDecode','display03PrimaryLanguages','display03LocaleResume','display03PackedCenters','display03SameBatchJob','display03FailedSameDigestRetry','display03SourcedHoldCache','display03WarmAodResources','display03MetricRolesAndAge','display03LowDoesNotSample','display03OffStopsWork','display03SameSceneRefreshKeepsJob','display03ForegroundReloadDuringBuild','display03StreamWireValidation','display03CurrentBodyBatteryLifecycle','display03ComplicationSourceBoundary','display03ActualComplicationApi')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs(root=ROOT):
 root=Path(root).resolve()
 paths=[p for p in (root/'watchface/source').rglob('*.mc') if p.is_file()]
 paths += [p for p in (root/'watchface/resources').rglob('*') if p.is_file()]
 paths += [p for d in root.glob('watchface/resources-*') for p in d.rglob('*') if p.is_file()]
 paths += list((root/'watchface/display03-tests').glob('*.mc'))
 paths += [p for p in (root/'openspec/changes/spacefox-watchface/evidence/site-flag-visual-batch/native-artifact').rglob('*') if p.is_file()]
 paths += [root/'tests/native_scene_diagnostics/profile-a/descriptors/426804295ad5943e1d73e755ba0b38e105f4fec8de8479bf470671e7f62dba70.json',root/'watchface/manifest.xml',root/'watchface/toolchain-lock.json',root/'tests/fixtures/watch_refresh_cache/packets.json',root/'tests/fixtures/basic_platform_metrics/MetricBoundary.mc',root/'tests/test_basic_platform_metrics.py',root/'tools/native_display03_probe.py']
 return {str(p.relative_to(root)):sha(p) for p in sorted(paths)}
def run(out):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True);ctx=discover();before=inputs()
 ET.register_namespace('iq','http://www.garmin.com/xml/connectiq');tree=ET.parse(ROOT/'watchface/manifest.xml');tree.getroot().find('{http://www.garmin.com/xml/connectiq}application').set('id','5bb6fca4fe174f9da6bfdc2ac6d70b59');tree.write(out/'manifest.xml',encoding='utf-8',xml_declaration=True)
 fixture=json.loads((ROOT/'tests/fixtures/watch_refresh_cache/packets.json').read_text());rows={'DisplayCatalog':fixture['catalogs']['initial'],'DisplayInitial':{'raw':fixture['packets']['initial']},'DisplayMoved':{'raw':fixture['packets']['moved']}}
 rows['D03RetrySelection']={'raw':(ROOT/'tests/native_scene_diagnostics/profile-a/descriptors/426804295ad5943e1d73e755ba0b38e105f4fec8de8479bf470671e7f62dba70.json').read_text()}
 artifact=ROOT/'openspec/changes/spacefox-watchface/evidence/site-flag-visual-batch/native-artifact'
 feed=json.loads((artifact/'feed.json').read_text());scene=json.loads((artifact/feed['visualSelection']['path']).read_text());descriptor=json.loads((artifact/scene['roles']['map']['descriptor']['path']).read_text())
 refs=[];branches=[]
 for i,ref in enumerate(descriptor['shards']):
  raw=(artifact/ref['path']).read_text();name='D03MapShard'+str(i);rows[name]={'raw':raw};refs.append([ref['sha256'],ref['decodedBytes']]);branches.append('if(key.equals("sf.obj.'+ref['sha256']+'")){return WatchUi.loadResource(Rez.JsonData.'+name+')["raw"];}')
 rows['D03MapDescriptor']={'canvas':descriptor['canvas'],'channels':3,'pixelSha256':descriptor['pixelSha256'],'shards':refs}
 probe='''import Toybox.Lang;import Toybox.System;import Toybox.Test;import Toybox.WatchUi;\n(:test,:typecheck(false)) class D03MapStore {function read(key){'''+''.join(branches)+'''return null;}}\n(:test,:typecheck(false)) function display03RealMapDecode(logger){var d=WatchUi.loadResource(Rez.JsonData.D03MapDescriptor);var start=System.getTimer();var decoder=new NativeSfrDecoder(new D03MapStore(),d);var steps=0;while(!decoder.step()){steps+=1;Test.assert(steps<2000);}Test.assert(decoder.done&&decoder.bitmap!=null&&decoder.outlineBitmap!=null);logger.debug("REAL_MAP_DECODE launch=ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a sourceSite=ll2:site:29 checksum=verified outline=true steps="+steps+" elapsedMs="+(System.getTimer()-start));return true;}\n'''
 (out/'GeneratedMapTest.mc').write_text(probe)
 from tests.test_basic_platform_metrics import mapped_fitness
 (out/'BoundaryFitness.mc').write_text(mapped_fitness())
 body=(ROOT/'watchface/source/BodyBatterySource.mc').read_text().replace('import Toybox.Complications;','').replace('Complications.Id','D03Id').replace('Complications.COMPLICATION_TYPE_BODY_BATTERY','D03Complications.BODY').replace('Complications.registerComplicationChangeCallback','D03Complications.registerComplicationChangeCallback').replace('Complications.subscribeToUpdates','D03Complications.subscribeToUpdates').replace('Complications.unsubscribeFromUpdates','D03Complications.unsubscribeFromUpdates').replace('Complications.getComplication','D03Complications.getComplication').replace('class BodyBatterySource','class MappedBodyBatterySource')
 (out/'MappedBodyBatterySource.mc').write_text(body)
 boundary=(ROOT/'tests/fixtures/basic_platform_metrics/MetricBoundary.mc').read_text().split('(:test)\nfunction metricAvailable',1)[0]
 (out/'MetricBoundary.mc').write_text(boundary)
 res=out/'resources';res.mkdir(exist_ok=True)
 for name,value in rows.items():(res/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')))
 (res/'data.xml').write_text('<resources>'+''.join('<jsonData id="'+name+'" filename="'+name+'.json"/>' for name in rows)+'</resources>')
 catalog=json.loads((ROOT/'locales/catalog.json').read_text());j='project.manifest = '+str(out/'manifest.xml')+'\nbase.sourcePath = '+str(ROOT/'watchface/source')+';'+str(ROOT/'watchface/display03-tests')+';'+str(out)+'\nbase.resourcePath = '+str(ROOT/'watchface/resources')+';'+str(res)+'\n'
 for row in catalog['locales']:
  if row['id']=='en':continue
  code={'chs':'zhs','cht':'zht'}.get(row['garmin'],row['garmin']);j+='base.lang.'+code+' = '+str(ROOT/'watchface'/('resources-'+code))+'\n'
 (out/'probe.jungle').write_text(j);package=out/'Display02Tests.prg';cmd=[str(ctx['java']),'-Dfile.encoding=UTF-8','-jar',str(ctx['compiler']),'-f',str(out/'probe.jungle'),'-d','fr165m','-o',str(package),'-y',str(ctx['key']),'-l','3','-O','2','-w','--unit-test'];build=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'compile.log').write_text(build.stdout)
 if build.returncode:raise RuntimeError('SDK compile failed')
 launch=[str(ctx['java']),'-Dfile.encoding=UTF-8','-classpath',str(ctx['compiler']),'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux','-f',str(package),'-d','fr165m','-s',str(ctx['sdk']/'bin/shell'),'-t'];selected=os.environ.get('SPACEFOX_DISPLAY03_TEST');
 if selected:
  if selected not in NAMES:raise ValueError('unknown DISPLAY03 test filter')
  launch.append(selected)
 # Stream output to disk so a hung test retains its first failure/stage output.
 with (out/'native.log').open('w') as log:
  try:test=subprocess.run(launch,text=True,stdout=log,stderr=subprocess.STDOUT,timeout=240)
  except subprocess.TimeoutExpired:
   (out/'timeout.json').write_text(json.dumps({'timeoutSeconds':240,'launchCommand':launch,'inputHashes':before,'packageSha256':sha(package)},indent=2)+'\n')
   raise
 result=parse_output((out/'native.log').read_text(),test.returncode,(selected,) if selected else NAMES)
 if inputs()!=before:raise RuntimeError('native source changed during test')
 receipt={'status':result['status'],'buildCommand':cmd,'launchCommand':launch,'rawExit':test.returncode,'tests':result,'inputHashes':before,'packageSha256':sha(package),'testKeyBoundary':'disposable SDK test key','admission':'diagnostic bypass; current proof checked separately'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 if result['status']!='passed':raise RuntimeError('SDK tests incomplete or failed')
 print('PASS '+str(result['observed_count'])+' source-bound tests; raw launcher exit '+str(test.returncode))
if __name__=='__main__':run(sys.argv[1])
