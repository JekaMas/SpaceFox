#!/usr/bin/env python3
"""Bounded EN/RU final timing/settings SDK observer; no provider/model calls.

The observer substitutes UTC and numeric telemetry only. It reads a captured
accepted schema3/SFR1M cache via actual production parser/cache/model/view. The
separate parser assertions exercise reschedule/withdrawal updates. Full-map UI
frames retain the same actual source text/art; semantic flags/unknown target are
explicit controlled display inputs, not a claim of a new provider fact.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from unittest.mock import patch
from xml.etree import ElementTree as ET
if __package__ in (None, ''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import ROOT, GROUPS, IMPORTS, build_probe
from tools.native_current_runtime import seed

UUID='7af62b7a43d84afcb21e8d935670c107'
BASENAME='SpaceFoxFinalTiming20261113.prg'
URL='https://final-native-timing.invalid'
EVIDENCE=Path('openspec/changes/spacefox-watchface/evidence/final-native-timing-settings')
PROFILE=Path('openspec/changes/spacefox-watchface/evidence/basic-selected-scene-whole/public/artifact')
STATES=('long','seconds59','seconds1','zero','elapsed899','elapsed901','reschedule','unknown','stale','appearance')
NATIVE=('clockExactPositive','clockExactNegative','uncertaintyPositive','uncertaintyNegative','offlineWakePositive','offlineWakeNegative','precisionTransitions','emptyStartup','clockAdapterSmoke','formatLocalSettings','finalTimingPositive','finalTimingNegative','finalParserUpdatePositive','finalParserUpdateNegative','finalSettingsPositive','finalSettingsNegative')
EXPECTED={'long':'T- 49:02:03','seconds59':'T- 00:00:59','seconds1':'T- 00:00:01','zero':'T+ 00:00:00','elapsed899':'T+ 00:14:59','elapsed901':'T+ 00:15:01','reschedule':'T- 01:00:00','unknown':'--:--:--','stale':'T+ 00:05:00','appearance':'T- 49:02:03'}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def observer_source():
 return IMPORTS+'''import Toybox.Graphics;
import Toybox.Timer;
(:typecheck(false)) class FinalClock extends WatchClock {
 var now=0l;function utcSeconds(){return now;}function localTimeText(){return "08:08";}
}
(:typecheck(false)) class FinalDrawing extends SceneRenderer {
 var app;var recording=false;
 function initialize(a,p){SceneRenderer.initialize(p);app=a;}
 function text(dc as Graphics.Dc,x as Numeric,y as Numeric,font as Graphics.FontType,value as String,color as Number,width as Number,contour as Number) as String {
  var shown=SceneRenderer.text(dc,x,y,font,value,color,width,contour);
  if(recording){var kind=font==fonts["time"]?"time":font==fonts["metric"]?"metric":"vector";System.println("FINAL_TEXT|"+app.label()+"|"+kind+"|"+x+"|"+y+"|"+dc.getTextWidthInPixels(shown,font)+"|"+dc.getFontHeight(font)+"|"+color+"|"+shown);}
  return shown;
 }
}
(:typecheck(false)) class FinalProxy extends WatchUi.WatchFace {
 var app;function initialize(a){WatchFace.initialize();app=a;}
 function onLayout(dc){app.view.onLayout(dc);}function onShow(){app.view.onShow();}function onHide(){app.view.onHide();}
 function onUpdate(dc){app.view.onUpdate(dc);app.drawn(dc);}
}
(:background,:typecheck(false)) class FinalQuiet extends System.ServiceDelegate {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:extendedCode,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var observer=null;var clock=null;var rich=null;var sourceContext=null;var sourceTarget=null;var checks=0;var frame=-1;var recorded=false;var cold=false;var fields=null;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=false;}
 function ensure(ok,message){if(!ok){throw new Lang.InvalidValueException("FINAL_NATIVE "+message);}}
 function getServiceDelegate(){return [new FinalQuiet()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){
  Application.Properties.setValue("FeedBaseUrl","https://final-native-timing.invalid");
  cold=Application.Storage.getValue("final.capture.prefix.complete")==true;
  // This held capture reuses the previously observed namespace; fresh English
  // defaults were asserted by the first native startup, not reset here.
  clock=new FinalClock();clock.now=Time.now().value().toLong();view=new SpaceFoxView(clock,new ScheduleState(null,"unknown"));
  view.setSettings(new SceneSettings(null).load());feed=new NativeCache(configuredFeedUrl(),null);feed.load(Time.now().value().toLong());NativeForegroundApp.display(self,feed);view.pendingLoader=method(:begin);view.syncDisplayMode(System.getDisplayMode());return [new FinalProxy(self)];
 }
 (:typecheck(disableBackgroundCheck)) function begin(){SpaceFoxApp.reloadFeed();observer=new Timer.Timer();observer.start(method(:ready),50,false);}
 (:typecheck(disableBackgroundCheck)) function ready(){
  Background.deleteTemporalEvent();checks+=1;ensure(checks<=500,"full captured scene timeout");
  if(view.downloaded==null||view.sfrBuild!=null||view.sfrRequested){observer.start(method(:ready),50,false);return;}
  ensure(System.getSystemStats().totalMemory==126784,"ordinary heap required");rich=view.downloaded;ensure(rich.mapBitmap!=null&&rich.bitmap!=null,"actual full map and rocket required");sourceContext=view.context;sourceTarget=feed.packet.target();
  if(sourceTarget==null){sourceTarget=sourceContext.schedule.remainingSeconds(0);}
  ensure(sourceTarget!=null,"captured nominal-minute target missing");
  if(cold){frame=19;fields=[4,5,0,1];ensure(view.settings.language.equals("ru")&&view.settings.clockColor==0x9ad5ff&&view.settings.countdownColor==0xcdb7ff,"cold persisted language/clock/countdown");ensure(view.settings.slots[0].equals("calories")&&view.settings.slots[1].equals("battery")&&view.settings.slots[2].equals("steps")&&view.settings.slots[3].equals("energy")&&Application.Properties.getValue("FeedBaseUrl").equals("https://final-native-timing.invalid"),"cold four roles and feed URL");ensure(view.settings.fieldColors[0]==0x7fe7c6&&view.settings.fieldColors[1]==0xffd686&&view.settings.fieldColors[2]==0xffafcf&&view.settings.fieldColors[3]==0xf7f9fc,"cold persisted four colors");System.println("FINAL_COLD_REOPEN Properties=true locale=ru colors=6 fields=4 sourceSame=true owner="+NativeMetrics.ownerTag);applyFrame(false);}
  else{frame=0;applyFrame(true);}
 }
 (:typecheck(disableBackgroundCheck)) function onDisplayModeChanged(){var high=System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER;SpaceFoxApp.onDisplayModeChanged();if(high&&rich!=null&&!cold){next();}}
 function label(){return (frame<10?"en":"ru")+"-"+["long","seconds59","seconds1","zero","elapsed899","elapsed901","reschedule","unknown","stale","appearance"][frame%10];}
 (:typecheck(disableBackgroundCheck)) function next(){if(rich==null||frame<0||cold){return;}if(frame<19){frame+=1;applyFrame(true);}else{System.println("FINAL_NATIVE COMPLETE frames=20 callbacks=20 ordinaryBytes=126784 owner="+NativeMetrics.ownerTag);}}
 (:typecheck(disableBackgroundCheck)) function applyFrame(change){
  var state=frame%10;var lang=frame<10?0:1;var colors=state==9?[2,3,0,4,5,1]:[0,0,1,1,1,1];
  if(change){Application.Properties.setValue("Language",lang);var names=["ClockColor","CountdownColor","Field1Color","Field2Color","Field3Color","Field4Color"];for(var i=0;i<names.size();i+=1){Application.Properties.setValue(names[i],colors[i]);}var roleSets=[[0,1,2,3],[4,5,0,1]];fields=roleSets[state%2];for(var j=0;j<4;j+=1){Application.Properties.setValue("Field"+(j+1),fields[j]);}SpaceFoxApp.onSettingsChanged();Background.deleteTemporalEvent();}
  var loaded=new SceneSettings(null).load();ensure(loaded.language.equals(lang==0?"en":"ru")&&view.settings.language.equals(loaded.language),"callback persisted locale");
  ensure(view.presentation.locale.equals(loaded.language)&&!view.presentation.qualificationMode,"actual regular locale selection");
  ensure(view.downloaded==rich,"appearance changed full bitmap");ensure(Application.Properties.getValue("FeedBaseUrl").equals("https://final-native-timing.invalid"),"callback retained feed URL");for(var z=0;z<4;z+=1){ensure(view.settings.slots[z].equals(["steps","energy","heart","stress","calories","battery"][fields[z]]),"callback retained role");}
  var deltas=[176523,59,1,0,-899,-901,3600,0,-300,176523];clock.now=sourceTarget.toLong()-deltas[state];
  // Explicit display seam: no changed launch names or forged provider facts.
  sourceContext.schedule=new ScheduleState(state==7?null:sourceTarget,state==7?"unknown":"minute");sourceContext.rescheduled=state==6||state==7;sourceContext.stale=state==7||state==8;
  view.setContext(sourceContext);view.downloaded=rich;view.packet=null;view.renderer=new FinalDrawing(self,view.presentation);view.renderer.prepare(sourceContext,view.settings);view.renderer.downloaded=rich;
  view.values={"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"calories"=>2345,"battery"=>82};view.animationProgress=0.0;view.stopAnimation();recorded=false;
  var expected=["T- 49:02:03","T- 00:00:59","T- 00:00:01","T+ 00:00:00","T+ 00:14:59","T+ 00:15:01","T- 01:00:00","--:--:--","T+ 00:05:00","T- 49:02:03"];var current=view.snapshot();ensure(current.countdown.equals(expected[state])&&view.presentation.countdown(current,true).equals(expected[state]),"countdown/model/view mismatch");
  if(frame==19){Application.Storage.setValue("final.settings.complete",true);Application.Storage.setValue("final.capture.prefix.complete",true);}
  WatchUi.requestUpdate();
 }
 function drawn(dc){
  if(rich==null||recorded||view.renderer==null){return;}var drawing=view.renderer;drawing.recording=true;var writes=feed.store.writes;var reads=feed.store.reads;view.onUpdate(dc);drawing.recording=false;ensure(writes==feed.store.writes&&reads==feed.store.reads,"redraw storage IO");recorded=true;
  System.println("FINAL_FRAME_READY label="+label()+" ms="+System.getTimer()+" utc="+clock.now+" countdown="+view.snapshot().countdown+" slots="+view.settings.slots+" clockColor="+view.settings.clockColor+" countdownColor="+view.settings.countdownColor+" fieldColors="+view.settings.fieldColors+" source="+feed.packet.wireHash+" bitmap=true map=true callback="+!cold+" ordinaryBytes="+System.getSystemStats().totalMemory+" owner="+NativeMetrics.ownerTag);
 }
}
'''

def english_reopen_source():
 """One bounded second process proves English cold Properties persistence."""
 source=observer_source()
 source=source.replace('cold=Application.Storage.getValue("final.capture.prefix.complete")==true;',
  'cold=Application.Storage.getValue("final.capture.prefix.englishReady")==true;if(!cold){Application.Properties.setValue("Language",0);Application.Storage.setValue("final.capture.prefix.englishReady",true);}')
 source=source.replace('if(cold){frame=19;','if(cold){frame=9;').replace('else{frame=0;applyFrame(true);}','else{frame=9;applyFrame(true);}')
 source=source.replace('view.settings.language.equals("ru")&&view.settings.clockColor','view.settings.language.equals("en")&&view.settings.clockColor').replace('Properties=true locale=ru colors=6','Properties=true locale=en colors=6')
 return source

def build(output, mode, bootstrap=False):
 GROUPS['final-timing']=(UUID,BASENAME)
 source=seed(ROOT/PROFILE,URL) if mode=='seed' else english_reopen_source() if mode=='english' else observer_source()
 resources=None
 if mode=='unit':
  GROUPS['final-timing']=('8af62b7a43d84afcb21e8d935670c108','SpaceFoxFinalUnit20261113.prg')
  source=IMPORTS+'(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}\n'+(ROOT/'watchface/tests/NativeClockTests.mc').read_text()+'\n'+(ROOT/'tests/fixtures/final_native_timing_settings/Assertions.mc').read_text()
  resources={'packets.json':(ROOT/EVIDENCE/'packets.json').read_bytes(),'packets.xml':b'<resources><jsonData id="FinalPackets" filename="packets.json"/></resources>'}
 if bootstrap:
  # Compile-time diagnostic bootstrap only. No runtime qualificationMode or
  # availability override. Final production build repeats strict admission.
  with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
   result=build_probe(output,source,group='final-timing',tests=mode in ('seed','unit'),probe_resources=resources)
 else:result=build_probe(output,source,group='final-timing',tests=mode in ('seed','unit'),probe_resources=resources)
 result['admissionValidation']='pending-delta-diagnostic-build' if bootstrap else 'strict-current-proof'
 result['observerGeneratorSha256']=sha(Path(__file__))
 if mode=='unit':
  result['assertionSha256']=sha(ROOT/'tests/fixtures/final_native_timing_settings/Assertions.mc')
  result['clockAssertionSha256']=sha(ROOT/'watchface/tests/NativeClockTests.mc')
 (output/'build.json').write_text(json.dumps(result,indent=2)+'\n')
 return result

def unknown_pixel_components(path):
 from tools.spacefox.native_profile import png_pixels
 width,height,pixels=png_pixels(Path(path).read_bytes())
 if (width,height)!=(390,390):raise ValueError('unknown-marker frame dimensions')
 mask=set()
 for y in range(202,235):
  for x in range(58,333):
   at=(y*width+x)*4;r,g,b=pixels[at:at+3]
   if r>150 and g>110 and b<170:mask.add((x,y))
 groups=[]
 while mask:
  first=mask.pop();todo=[first];group=[first]
  while todo:
   x,y=todo.pop()
   for nxt in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if nxt in mask:mask.remove(nxt);todo.append(nxt);group.append(nxt)
  groups.append([min(x for x,y in group),min(y for x,y in group),max(x for x,y in group)+1,max(y for x,y in group)+1,len(group)])
 return sorted(groups)

def validate_pixel_readback(directory):
 directory=Path(directory);record=json.loads((directory/'pixel-readback.json').read_text())
 raw=[]
 for name in ('pixel-ocr-first2.jsonl','pixel-ocr-remaining18.jsonl'):
  raw.extend(json.loads(line) for line in (directory/name).read_text().splitlines() if line.strip())
 if len(raw)!=20 or len({Path(r['file']).name for r in raw})!=20:raise ValueError('pixel OCR exact20frame denominator differs')
 if len(record['frames'])!=20:raise ValueError('pixel association denominator differs')
 for lang in ('en','ru'):
  for state in STATES:
   label=lang+'-'+state;name='held-'+label+'.png';path=directory/'frames'/name
   row=next((r for r in raw if Path(r['file']).name==name),None)
   association=next((r for r in record['frames'] if r['label']==label),None)
   if row is None or association is None or association['pngSha256']!=sha(path):raise ValueError('pixel observation association changed: '+label)
   if row['backend']!='macOS Vision on-device' or (row['width'],row['height'])!=(390,390):raise ValueError('pixel OCR backend/size differs')
   observed=row['observations']
   if state=='unknown' and not observed:
    groups=unknown_pixel_components(path)
    dashes=[g for g in groups if g[2]-g[0]==7 and g[3]-g[1]==2]
    dots=[g for g in groups if g[2]-g[0]==3 and g[3]-g[1]==3]
    if len(groups)!=10 or len(dashes)!=6 or len(dots)!=4 or groups!=association.get('unknownComponents'):
     raise ValueError('actual unknown marker is not six dashes/two colons: '+label)
    # Two colons, each two separate dots at the same x; horizontal strokes
    # occur in three pairs. This is a literal pixel marker, no countdown model.
    if [sum(g[0]==x for g in dots) for x in sorted({g[0] for g in dots})]!=[2,2]:raise ValueError('unknown colon geometry differs')
   elif len(observed)!=1 or re.sub(r'\s+','',observed[0]['text'])!=re.sub(r'\s+','',EXPECTED[state]) or observed[0]['confidence']<0.5:
    raise ValueError('actual countdown pixels disagree with label: '+label)
 return record

def validate_evidence(directory, *, root=ROOT, require_clean=False):
 directory=Path(directory);root=Path(root)
 record=json.loads((directory/'native-result.json').read_text());build_record=json.loads((directory/'observer/build.json').read_text())
 if record.get('status')!='passed':raise ValueError('final native evidence incomplete')
 if require_clean and build_record['sourceDirty']:
  binding=json.loads((directory/'clean-source.json').read_text())
  if binding['status']!='passed' or binding['productionSources']!=build_record['productionSources'] or binding['productionResources']!=build_record['productionResources']:
   raise ValueError('final native clean source binding missing')
 for name,digest in {**build_record['productionSources'],**build_record['productionResources']}.items():
  if sha(root/name)!=digest:raise ValueError('final native source changed: '+name)
 if build_record['exitCode']!=0 or build_record['productionSourceScope']!='all-native':raise ValueError('final native compile incomplete')
 compiled=(directory/'observer/Probe.mc.txt').read_text()
 expected=observer_source().replace('frame=19;fields=[4,5,0,1];ensure(', 'frame=19;ensure(').replace('SpaceFoxApp.initialize();','SpaceFoxApp.initialize();NativeMetrics.ownerTag='+json.dumps(build_record['ownerTag'])+';System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);',1)
 if compiled!=expected or hashlib.sha256(compiled.encode()).hexdigest()!=build_record['probeSha256']:
  raise ValueError('final native observer program differs')
 cold_build=json.loads((directory/'cold/build.json').read_text())
 cold_compiled=(directory/'cold/Probe.mc.txt').read_text()
 cold_expected=observer_source().replace('SpaceFoxApp.initialize();','SpaceFoxApp.initialize();NativeMetrics.ownerTag='+json.dumps(cold_build['ownerTag'])+';System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);',1)
 if cold_compiled!=cold_expected or sha(directory/'cold/Probe.mc.txt')!=cold_build['probeSha256'] or cold_build['productionSources']!=build_record['productionSources'] or cold_build['productionResources']!=build_record['productionResources']:raise ValueError('cold observer source binding differs')
 raw=(directory/'observer/run.log').read_text();cold=(directory/'cold/reopen.log').read_text()
 if any(marker in raw+cold for marker in ('Unhandled Exception','Error:','Out Of Memory','Stack Overflow','FINAL_NATIVE FAILED')):raise ValueError('final native VM failed')
 for lang in ('en','ru'):
  for state in STATES:
   label=lang+'-'+state
   if ('FINAL_FRAME_READY label='+label+' ') not in raw:raise ValueError('missing final native state '+label)
 if 'FINAL_COLD_REOPEN Properties=true locale=ru colors=6 fields=4 sourceSame=true' not in cold:raise ValueError('cold reopen not observed')
 if record['observedFrames']!=20 or record['states']!=list(STATES):raise ValueError('final native state denominator differs')
 validate_pixel_readback(directory)
 unit=json.loads((directory/'unit/build.json').read_text())
 from tools.run_native_tests import parse_output
 unit_result=json.loads((directory/'unit/unit-result.json').read_text())
 parsed=parse_output((directory/'unit/native-tests.log').read_text(),unit_result['raw_exit_code'],NATIVE)
 if parsed['status']!='passed' or any(unit_result.get(k)!=v for k,v in parsed.items()):raise ValueError('native unit framework receipt failed')
 if unit['exitCode']!=0 or unit['tests'] is not True or unit['productionSourceScope']!='all-native' or unit['productionSources']!=build_record['productionSources'] or unit['productionResources']!=build_record['productionResources'] or unit['sourceSetSha256']!=build_record['sourceSetSha256']:
  raise ValueError('native unit source/toolchain binding differs')
 unit_probe=(directory/'unit/Probe.mc.txt').read_text()
 unit_expected=IMPORTS+'(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}\n'+(root/'watchface/tests/NativeClockTests.mc').read_text()+'\n'+(root/'tests/fixtures/final_native_timing_settings/Assertions.mc').read_text()
 if unit_probe!=unit_expected or sha(directory/'unit/Probe.mc.txt')!=unit['probeSha256'] or '-d' not in unit['command'] or unit['command'][unit['command'].index('-d')+1]!='fr165':raise ValueError('native unit probe/toolchain differs')
 if unit['assertionSha256']!=sha(root/'tests/fixtures/final_native_timing_settings/Assertions.mc') or unit['clockAssertionSha256']!=sha(root/'watchface/tests/NativeClockTests.mc') or unit['probeResources']['packets.json']!=sha(directory/'packets.json'):
  raise ValueError('native literal assertion/resource inputs changed')
 menus=json.loads((directory/'new-menu-fonts.json').read_text())
 if menus['status']!='passed' or len(menus['rows'])!=60:raise ValueError('new primary appearance menu glyph proof incomplete')
 for row in menus['rows']:
  if sha(root/row['resource'])!=row['resourceSha256'] or row['missing'] or not row['glyphs'] or any(g['g'] in (0,'.notdef') for g in row['glyphs']):raise ValueError('new appearance menu glyph input changed')
 english=json.loads((directory/'english/build.json').read_text())
 english_compiled=(directory/'english/Probe.mc.txt').read_text()
 english_expected=english_reopen_source().replace('SpaceFoxApp.initialize();','SpaceFoxApp.initialize();NativeMetrics.ownerTag='+json.dumps(english['ownerTag'])+';System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);',1)
 if english_compiled!=english_expected or hashlib.sha256(english_compiled.encode()).hexdigest()!=english['probeSha256']:raise ValueError('English reopen assertion program differs')
 english_log=(directory/'english/english-cold-reopen.log').read_text()
 if 'FINAL_COLD_REOPEN Properties=true locale=en colors=6 fields=4 sourceSame=true' not in english_log:raise ValueError('English cold reopen not observed')
 if english['productionSources']!=build_record['productionSources'] or english['productionResources']!=build_record['productionResources']:raise ValueError('English reopen product source differs')
 for name,digest in record['files'].items():
  if sha(directory/name)!=digest:raise ValueError('final native observation changed: '+name)
 if len(record['screenshots'])!=20:raise ValueError('actual20 SDK frames required')
 import struct
 for name in record['screenshots']:
  raw=(directory/name).read_bytes()
  if raw[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',raw[16:24])!=(390,390):raise ValueError('not390x390 actual SDK frame')
 return record

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['seed','observer','english','unit','validate']);p.add_argument('--output',type=Path,required=True);p.add_argument('--bootstrap-build',action='store_true');a=p.parse_args()
 if a.mode=='validate':print(json.dumps(validate_evidence(a.output)));return 0
 result=build(a.output,a.mode,a.bootstrap_build);print(json.dumps({k:result[k] for k in ('exitCode','packageName','sourceSetSha256')}));return result['exitCode']
if __name__=='__main__':raise SystemExit(main())
