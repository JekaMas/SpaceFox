#!/usr/bin/env python3
"""Ordinary FR165 finite UI observation; no blanket Unicode/device qualification.

UI mode uses only primary-five actual native settings/resources and real accepted
source/bitmap in an owned persisted namespace. It does not require or claim a
complete provider corpus. Common provider text qualification is a separate mode.
"""
import argparse,hashlib,json,sys
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import ROOT,IMPORTS,GROUPS,build_probe,literal
from tools.display_corpus import UI_WORDS

def ui_source(indices,dwell_ms,base="https://current-native.invalid"):
 references='['+','.join('Rez.JsonData.FiniteLocale'+str(i) for i in range(len(indices)))+']'
 return IMPORTS+'import Toybox.Graphics;\nimport Toybox.Timer;\n'+'''
(:background,:typecheck(false)) class FiniteQuiet extends System.ServiceDelegate {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var observer=null;var phase=0;var stage=0;var checks=0;var targets=null;var indices='''+literal(indices)+''';var image=null;var dc=null;var bitmap=null;var epoch=null;var seal=null;var sharedLabel=null;var sharedSmall=null;var expected=null;var loads=0;var high=0;var drawState=0;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=false;}
 function ensure(ok,message){if(!ok){throw new Lang.InvalidValueException("FINITE_UI "+message);}}
 function log(text){System.println("FINITE_UI "+text+" owner="+NativeMetrics.ownerTag);}
 function getServiceDelegate(){return [new FiniteQuiet()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){targets='''+references+''';Application.Properties.setValue("FeedBaseUrl",'''+json.dumps(base)+''');Application.Properties.setValue("Language",0);SpaceFoxApp.getInitialView();view.presentation.qualificationMode=true;view.pendingLoader=method(:begin);return [view];}
 (:typecheck(disableBackgroundCheck)) function begin(){SpaceFoxApp.reloadFeed();if(observer==null){observer=new Timer.Timer();}observer.start(method(:tick),100,false);}
 (:typecheck(disableBackgroundCheck)) function tick(){
  Background.deleteTemporalEvent();checks+=1;var used=System.getSystemStats().usedMemory;if(used>high){high=used;}ensure(System.getSystemStats().totalMemory==126784,"not ordinary memory");
  if(view.downloaded==null||view.sfrBuild!=null||view.sfrRequested){ensure(checks<400,"initial complete scene timeout");observer.start(method(:tick),100,false);return;}
  if(bitmap==null){bitmap=view.downloaded;epoch=feed.packet.validation;seal=feed.store.read("sf.commit")["seal"];sharedLabel=view.presentation.label;sharedSmall=view.presentation.latinSmall;image=Graphics.createBufferedBitmap({:width=>390,:height=>390,:alphaBlending=>Graphics.ALPHA_BLENDING_FULL}).get();dc=image.getDc();}
  ensure(view.downloaded==bitmap&&feed.packet.validation==epoch&&feed.store.read("sf.commit")["seal"].equals(seal),"locale changed source or bitmap");
  if(phase>=targets.size()){observer.stop();observer=null;image=null;dc=null;log("COMPLETE locales="+phase+" ordinaryBytes=126784 sampledHigh="+high+" sameBitmap=true sourceEpoch="+epoch+" physicalDevice=false speakerReview=false");return;}
  if(stage==0){expected=WatchUi.loadResource(targets[phase]);Application.Properties.setValue("Language",indices[phase]);SpaceFoxApp.onSettingsChanged();Background.deleteTemporalEvent();ensure(view.presentation.locale.equals(expected["locale"]),"locale fallback "+expected["locale"]);ensure(view.presentation.label==sharedLabel&&view.presentation.latinSmall==sharedSmall,"shared proper-name fonts changed");var keys='''+literal(list(UI_WORDS))+''';for(var k=0;k<keys.size();k+=1){var raw=view.presentation.word(keys[k]);ensure(raw.equals(expected["words"][keys[k]]),"wrong word "+keys[k]);var font=dc.getTextWidthInPixels(raw,view.presentation.count)>275?view.presentation.small:view.presentation.count;var shown=view.presentation.fit(dc,raw,font,275);ensure(!shown.equals("")&&dc.getTextWidthInPixels(shown,font)<=275,"word overflow "+keys[k]);dc.drawText(195,202,font,shown,Graphics.TEXT_JUSTIFY_CENTER);}loads=view.presentation.loads;drawState=0;stage=1;log("WORDS locale="+expected["locale"]+" keys=0 countFontHeight="+dc.getFontHeight(view.presentation.count)+" smallFontHeight="+dc.getFontHeight(view.presentation.small));observer.start(method(:tick),100,false);return;}
  if(drawState<10){var snapshot=new ClockSnapshot("23:59",drawState<4?"--:--:--":"");if(drawState>=4&&drawState<9){snapshot.remaining=[0,59,3599,3600,93784][drawState-4];}if(drawState==9){snapshot=view.snapshot();ensure(snapshot.remaining!=null,"actual minute target missing");ensure(view.presentation.countdown(snapshot,true).equals(CountdownFormat.format(snapshot.remaining)),"nominal minute countdown mismatch");}view.renderer.active(dc,snapshot,view.settings,view.values,view.fitness,0.0);var raw=view.presentation.countdown(snapshot,true);if(drawState<9){var literals=["--:--:--","--:--:--","--:--:--","--:--:--","00:00:00","00:00:59","00:59:59","01:00:00","26:03:04"];ensure(raw.equals(literals[drawState]),"numeric countdown differs");}var font=dc.getTextWidthInPixels(raw,view.presentation.count)>275?view.presentation.small:view.presentation.count;var shown=view.presentation.fit(dc,raw,font,275);ensure(!shown.equals("")&&dc.getTextWidthInPixels(shown,font)<=275,"countdown overflow");ensure(view.presentation.loads==loads,"dictionary allocation during draw");drawState+=1;observer.start(method(:tick),100,false);return;}
  log("READY locale="+expected["locale"]+" words=0 renderedStates=10 sourceEpoch="+epoch+" sameBitmap=true sampledHigh="+high+" phoneSettingsRendered=false");WatchUi.requestUpdate();phase+=1;stage=0;expected=null;observer.start(method(:tick),'''+str(dwell_ms)+''',false);
 }
}
'''

def build_ui(output,identity,dwell_ms):
 catalog=json.loads((ROOT/'locales/catalog.json').read_text());primary=catalog['supportPolicy']['primaryLocales'];indices=[];resources={};xml=[];inputs={}
 for index,row in enumerate(catalog['locales']):
  if row['id'] not in primary:continue
  name='FiniteLocale'+str(len(indices));path=ROOT/'watchface/resources/json'/('Locale'+str(index)+'.json');native=json.loads(path.read_text());payload={'locale':row['id'],'words':{k:native[k] for k in UI_WORDS}};raw=json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode();resources[name+'.json']=raw;xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>');indices.append(index);inputs[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
 resources['finite.xml']=('<resources>'+''.join(xml)+'</resources>').encode();GROUPS['finite']=(identity['uuid'],identity['basename']);record=build_probe(output,ui_source(indices,dwell_ms,identity.get("url","https://current-native.invalid")),group='finite',probe_resources=resources);record['baseUrl']=identity.get('url','https://current-native.invalid');record['finiteUiInputs']=inputs;record['primaryLocales']=primary;record['proofBoundary']=__doc__;record['generatorSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();(output/'build.json').write_text(json.dumps(record,indent=2)+'\n');return record
def load_complete_corpus(path,root=ROOT):
 from tools import display_corpus
 import shutil,tempfile
 path=path.resolve();data=json.loads(path.read_text());coverage=data['coverage']
 if (coverage['terminalNext'] is not None or coverage['launchCount']!=coverage['sourceCount']
     or coverage['uniqueLaunchIds']!=coverage['sourceCount'] or coverage['sourceCount']<1
     or len(data['launches'])!=coverage['sourceCount']
     or data['neededDisplayIndices']!=list(range(len(data['strings'])))):
  raise ValueError('complete source enumeration and exact needed display dictionary required')
 # Independent replay of the retained raw source chain through the source owner.
 with tempfile.TemporaryDirectory(prefix='spacefox-finite-corpus-replay-') as temp:
  target=Path(temp);shutil.copyfile(path.parent/'collection.json',target/'collection.json');shutil.copytree(path.parent/'raw',target/'raw');display_corpus.build(target,root)
  if (target/'display-corpus.json').read_bytes()!=path.read_bytes():raise ValueError('finite corpus differs from complete raw replay/current semantic UI')
 return data


def common_source(resource_ids,expected_records,base="https://current-native.invalid"):
 refs='['+','.join('Rez.JsonData.'+name for name in resource_ids)+']'
 return IMPORTS+'import Toybox.Graphics;\nimport Toybox.Timer;\n'+'''
(:background,:typecheck(false)) class FiniteQuiet extends System.ServiceDelegate {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var observer=null;var at=0;var rows=null;var rowAt=0;var chunks='''+refs+''';var image=null;var dc=null;var bitmap=null;var epoch=null;var seal=null;var count=0;var compositions=0;var high=0;var checks=0;var trim=0;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=false;}
 function ensure(ok,message){if(!ok){throw new Lang.InvalidValueException("FINITE_CORPUS "+message);}}
 function log(text){System.println("FINITE_CORPUS "+text+" owner="+NativeMetrics.ownerTag);}
 function getServiceDelegate(){return [new FiniteQuiet()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){Application.Properties.setValue("FeedBaseUrl",'''+json.dumps(base)+''');Application.Properties.setValue("Language",0);SpaceFoxApp.getInitialView();view.pendingLoader=method(:begin);return [view];}
 (:typecheck(disableBackgroundCheck)) function begin(){SpaceFoxApp.reloadFeed();observer=new Timer.Timer();observer.start(method(:tick),100,false);}
 function fitted(raw,font,width){var shown=view.presentation.fit(dc,raw,font,width);ensure(!shown.equals("")&&dc.getTextWidthInPixels(shown,font)<=width,"fit empty/overflow");if(!shown.equals(raw)){ensure(shown.substring(shown.length()-1,shown.length()).equals("…"),"missing ellipsis");ensure(raw.find(shown.substring(0,shown.length()-1))==0,"fit changed source prefix");trim+=1;}return shown;}
 function bounds(x,y,font,text){var half=dc.getTextWidthInPixels(text,font)/2.0+1;var bottom=y+dc.getFontHeight(font)+1;var top=y-1;var xs=[x-half,x+half];var ys=[top,bottom];for(var i=0;i<2;i+=1){for(var j=0;j<2;j+=1){var dx=xs[i]-195;var dy=ys[j]-195;ensure(dx*dx+dy*dy<=195*195,"round-display bounds");}}}
 function compose(row){var p=view.presentation;var rocket=row[0]==null?"":row[0];var operator=row[1]==null?"—":row[1];var purpose=row[2]==null?"—":row[2];var site=row[3]==null?"":row[3];var r=fitted(rocket.equals("")?"—":rocket,p.label,122);if(rocket.equals("")){r="";}var o=fitted(operator,p.latinSmall,rocket.equals("")?238:100);var rw=dc.getTextWidthInPixels(r,p.label);var ow=dc.getTextWidthInPixels(o,p.latinSmall);var gap=r.equals("")||o.equals("")?0:16;ensure(rw+ow+gap<=238,"header width");var left=195-(rw+ow+gap)/2.0;dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();dc.setColor(0xD4DFEB,Graphics.COLOR_TRANSPARENT);if(!r.equals("")){bounds(left+rw/2.0,43,p.label,r);dc.drawText(left+rw/2.0,43,p.label,r,Graphics.TEXT_JUSTIFY_CENTER);}bounds(left+rw+gap+ow/2.0,47,p.latinSmall,o);dc.drawText(left+rw+gap+ow/2.0,47,p.latinSmall,o,Graphics.TEXT_JUSTIFY_CENTER);var purposeShown=fitted(purpose,p.latinSmall,282);bounds(195,70,p.latinSmall,purposeShown);dc.drawText(195,70,p.latinSmall,purposeShown,Graphics.TEXT_JUSTIFY_CENTER);if(!site.equals("")){var siteShown=fitted(site,p.label,242);bounds(195,319,p.label,siteShown);dc.drawText(195,319,p.label,siteShown,Graphics.TEXT_JUSTIFY_CENTER);}count+=row[4];compositions+=1;}
 (:typecheck(disableBackgroundCheck)) function tick(){
  Background.deleteTemporalEvent();checks+=1;var used=System.getSystemStats().usedMemory;if(used>high){high=used;}ensure(System.getSystemStats().totalMemory==126784,"not ordinary heap");if(view.downloaded==null||view.sfrBuild!=null||view.sfrRequested){ensure(checks<400,"initial full scene timeout");observer.start(method(:tick),100,false);return;}if(bitmap==null){bitmap=view.downloaded;epoch=feed.packet.validation;seal=feed.store.read("sf.commit")["seal"];image=Graphics.createBufferedBitmap({:width=>390,:height=>390,:alphaBlending=>Graphics.ALPHA_BLENDING_FULL}).get();dc=image.getDc();}
  ensure(view.downloaded==bitmap&&feed.packet.validation==epoch&&feed.store.read("sf.commit")["seal"].equals(seal),"corpus changed accepted source/bitmap");
  if(rows==null){if(at>=chunks.size()){ensure(count=='''+str(expected_records)+''',"record coverage");observer.stop();observer=null;image=null;dc=null;log("COMPLETE records="+count+" compositions="+compositions+" truncatedFields="+trim+" ordinaryBytes=126784 sampledHigh="+high+" sharedFonts=true sameBitmap=true nativeArtworkQualified=false");return;}rows=WatchUi.loadResource(chunks[at]);at+=1;rowAt=0;}
  compose(rows[rowAt]);rowAt+=1;if(rowAt>=rows.size()){rows=null;}observer.start(method(:tick),25,false);
 }
}
'''


def build_common(output,identity,corpus_path):
 corpus_path=corpus_path.resolve();data=load_complete_corpus(corpus_path);strings=data['strings'];groups={}
 for row in data['launches']:
  fields=tuple(None if ref is None else strings[ref] for ref in row[3])
  groups[fields]=groups.get(fields,0)+1
 rows=[[*fields,count] for fields,count in sorted(groups.items(),key=lambda item:json.dumps(item[0],ensure_ascii=False))]
 resources={};names=[];xml=[]
 for offset in range(0,len(rows),4):
  name='FiniteCommon'+str(len(names));names.append(name);resources[name+'.json']=json.dumps(rows[offset:offset+4],ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>')
 resources['finite-common.xml']=('<resources>'+''.join(xml)+'</resources>').encode();GROUPS['finite']=(identity['uuid'],identity['basename']);record=build_probe(output,common_source(names,len(data['launches']),identity.get("url","https://current-native.invalid")),group='finite',probe_resources=resources);record['baseUrl']=identity.get('url','https://current-native.invalid');record['corpusPath']=str(corpus_path.relative_to(ROOT));record['corpusSha256']=hashlib.sha256(corpus_path.read_bytes()).hexdigest();record['records']=len(data['launches']);record['uniqueCompositions']=len(rows);record['proofBoundary']='Ordinary SDK text/fit/round bounds for complete finite real corpus with accepted current scene resident; no historical rocket artwork/device/speaker qualification.';(output/'build.json').write_text(json.dumps(record,indent=2)+'\n');return record

FONT_FILES={'RobotoRegular':'Roboto-Regular.ttf','NotoNaskhArabicRegular':'NotoNaskhArabic-Regular.ttf','NotoSansHebrewRegular':'NotoSansHebrew-Regular.ttf','NotoSansSCMedium':'NotoSansSC-Medium.ttf','KosugiRegular':'Kosugi-Regular.ttf','NanumGothicBold':'NanumGothic-Bold.ttf','PridiRegular':'Pridi-Regular.ttf'}

def font_observation(output,corpus_path,fonts,reuse_ui=None,ui_build=None):
 from fontTools.ttLib import TTFont
 import os,subprocess,unicodedata
 data=load_complete_corpus(corpus_path);catalog=json.loads((ROOT/'locales/catalog.json').read_text());primary=catalog['supportPolicy']['primaryLocales'];loaded={};font_receipts={}
 for face,name in FONT_FILES.items():
  path=fonts/name;loaded[face]=set(TTFont(path).getBestCmap());font_receipts[face]={'fileName':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
 previous=json.loads(reuse_ui.read_text()) if reuse_ui else None
 if previous:
  if previous['fonts']!=font_receipts or previous['primaryLocales']!=primary:raise ValueError('UI font reuse inputs changed')
  prior_inputs=json.loads(ui_build.read_text())['finiteUiInputs']
 base=loaded['RobotoRegular'];proper=set()
 for row in data['launches']:
  for ref in row[3]:
   if ref is not None:proper.update(map(ord,data['strings'][ref]))
 proper.update(map(ord,'—…·'));missing=sorted(proper-base);rows=[]
 for index,row in enumerate(catalog['locales']):
  if row['id'] not in primary:continue
  native_path=ROOT/'watchface/resources/json'/('Locale'+str(index)+'.json');native=json.loads(native_path.read_text())
  face=native['face'];words={key:native[key] for key in UI_WORDS};text=''.join(words.values())+'0123456789:-%,…·—/';absent=sorted({ord(c) for c in text if unicodedata.category(c)!='Cf'}-loaded[face]-base)
  if previous:
   if prior_inputs[str(native_path.relative_to(ROOT))]!=hashlib.sha256(native_path.read_bytes()).hexdigest():raise ValueError('UI words changed; cannot reuse shaping')
   retained=next(item for item in previous['ui'] if item['locale']==row['id'])
   if retained['face']!=native['face'] or retained['missingCodepoints']:raise ValueError('UI face/coverage changed')
   retained=dict(retained);retained['missingCodepoints']=[f'U+{c:04X}' for c in absent];rows.append(retained);continue
  shapes=[]
  for key,value in words.items():
   chosen=face if set(map(ord,value))<=loaded[face] else 'RobotoRegular'
   result=subprocess.run(['hb-shape',str(fonts/FONT_FILES[chosen]),value,'--output-format=json'],capture_output=True,text=True,check=True,env={**os.environ,'LC_ALL':'en_US.UTF-8'});glyphs=json.loads(result.stdout)
   if any(glyph['g'] in (0,'.notdef') for glyph in glyphs):raise ValueError('host shaper missing glyph: '+row['id']+'/'+key)
   shapes.append({'key':key,'face':chosen,'glyphs':glyphs})
  rows.append({'locale':row['id'],'face':face,'missingCodepoints':[f'U+{c:04X}' for c in absent],'shaping':shapes})
 record={'status':'passed' if not missing and all(not row['missingCodepoints'] for row in rows) else 'failed','corpusSha256':hashlib.sha256(corpus_path.read_bytes()).hexdigest(),'primaryLocales':primary,'fonts':font_receipts,'commonRoleMissingCodepoints':[f'U+{c:04X}' for c in missing],'ui':rows,'proofBoundary':'Exact installed SDK font cmap union and host HarfBuzz shaping for finite real provider roles/numeric face tokens. Native ordinary rendering has separate actual SDK observations; no phone/device/speaker claim.'}
 if previous:record['uiReuse']={'priorFontRecordSha256':hashlib.sha256(reuse_ui.read_bytes()).hexdigest(),'nativeUiBuildSha256':hashlib.sha256(ui_build.read_bytes()).hexdigest(),'reason':'Exact primary word resources and installed font bytes unchanged; actual common provider text and numeric display token cmap were rechecked; unchanged nine-word shaping was reused.'}
 output.mkdir(parents=True,exist_ok=True);(output/'fonts.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
 if record['status']!='passed':raise ValueError('finite glyph coverage failed; inspect '+str(output/'fonts.json'))
 return record

def activation_source(catalog,base="https://current-native.invalid"):
 primary=catalog['supportPolicy']['primaryLocales'];rows=[(i,row['id']) for i,row in enumerate(catalog['locales']) if row['id'] in primary]
 return IMPORTS+'import Toybox.Timer;\n'+'''
(:background,:typecheck(false)) class FiniteQuiet extends System.ServiceDelegate {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var timer=null;var checks=0;var at=0;var indices='''+literal([i for i,_ in rows])+''';var locales='''+literal([loc for _,loc in rows])+''';var bitmap=null;var age=null;var seal=null;var signature=null;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=false;}
 function getServiceDelegate(){return [new FiniteQuiet()];}
 function ensure(ok,message){if(!ok){throw new Lang.InvalidValueException("FINITE_ACTIVATION "+message);}}
 function state(){var hash=new NativeCanonical();hash.emit(view.settings.slots);return hash.digest();}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){Application.Properties.setValue("FeedBaseUrl",'''+json.dumps(base)+''');Application.Properties.setValue("Language",0);SpaceFoxApp.getInitialView();view.pendingLoader=method(:begin);return [view];}
 (:typecheck(disableBackgroundCheck)) function begin(){SpaceFoxApp.reloadFeed();timer=new Timer.Timer();timer.start(method(:tick),100,false);}
 (:typecheck(disableBackgroundCheck)) function tick(){checks+=1;Background.deleteTemporalEvent();ensure(!view.presentation.qualificationMode,"diagnostic bypass enabled");ensure(System.getSystemStats().totalMemory==126784,"not ordinary heap");if(view.downloaded==null||view.sfrBuild!=null||view.sfrRequested){ensure(checks<400,"source scene timeout");timer.start(method(:tick),100,false);return;}if(bitmap==null){bitmap=view.downloaded;age=feed.packet.validation;seal=feed.store.read("sf.commit")["seal"];signature=state();}
  if(at>=indices.size()){Application.Properties.setValue("Language",0);SpaceFoxApp.onSettingsChanged();Background.deleteTemporalEvent();timer.stop();timer=null;System.println("FINITE_ACTIVATION COMPLETE locales="+indices.size()+" diagnosticBypass=false settingsPreserved=true sameBitmap=true sourceEpoch="+age+" ordinaryBytes=126784 owner="+NativeMetrics.ownerTag);return;}
  Application.Properties.setValue("Language",indices[at]);SpaceFoxApp.onSettingsChanged();Background.deleteTemporalEvent();ensure(SceneStrings.available(indices[at]),"unavailable generated index");ensure(view.presentation.locale.equals(locales[at]),"production locale fallback "+locales[at]);ensure(signature.equals(state()),"unrelated settings changed");ensure(view.downloaded==bitmap&&feed.packet.validation==age&&feed.store.read("sf.commit")["seal"].equals(seal),"source/bitmap changed");System.println("FINITE_ACTIVATION READY locale="+locales[at]+" diagnosticBypass=false sameBitmap=true settingsPreserved=true owner="+NativeMetrics.ownerTag);at+=1;timer.start(method(:tick),1500,false);
 }
}
'''

def build_activation(output,identity):
 catalog=json.loads((ROOT/'locales/catalog.json').read_text());GROUPS['finite']=(identity['uuid'],identity['basename']);return build_probe(output,activation_source(catalog,identity.get("url","https://current-native.invalid")),group='finite')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['ui','common','fonts','activation'],default='ui');p.add_argument('--corpus',type=Path);p.add_argument('--reuse-ui-fonts',type=Path);p.add_argument('--ui-build',type=Path);p.add_argument('--fonts',type=Path,default=Path.home()/'Library/Application Support/Garmin/ConnectIQ/Fonts');p.add_argument('--output',type=Path,required=True);p.add_argument('--identity',type=Path,default=ROOT/'openspec/changes/spacefox-watchface/evidence/current-only-native/identity.json');p.add_argument('--dwell-ms',type=int,default=1500);a=p.parse_args();identity=json.loads(a.identity.read_text())
 if a.mode in ('common','fonts') and not a.corpus:p.error('--corpus required for complete finite corpus modes')
 if bool(a.reuse_ui_fonts)!=bool(a.ui_build):p.error('--reuse-ui-fonts and --ui-build must be supplied together')
 if a.mode=='fonts':
  r=font_observation(a.output,a.corpus,a.fonts,a.reuse_ui_fonts,a.ui_build);print(json.dumps({'status':r['status'],'primaryModes':len(r['ui']),'commonMissing':r['commonRoleMissingCodepoints']}));sys.exit(0)
 r=build_ui(a.output,identity,a.dwell_ms) if a.mode=='ui' else build_activation(a.output,identity) if a.mode=='activation' else build_common(a.output,identity,a.corpus);print(r['exitCode']);sys.exit(r['exitCode'])
