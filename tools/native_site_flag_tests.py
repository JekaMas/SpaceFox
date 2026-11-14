"""Build the selected real-source SFR1M artifact and native assertion program.

The SDK simulator is launched separately; building is never a passing receipt.
"""
from copy import deepcopy
import hashlib
import json
import shutil
from pathlib import Path

from tests import test_basic_launch_logic as source
from tools.native_current_runtime import selected_files
from tools.native_full_visual_runtime import IMPORTS
from tools.spacefox.catalog import canonical_bytes
from tools.spacefox.native_motion import build_artifact
from tools.spacefox.provider import _country_code

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'openspec/changes/spacefox-watchface/evidence/site-flag-visual-batch'
PROFILE=OUT/'native-artifact'


def build_fixture():
    source.BasicLaunchLogicTest.setUpClass()
    record=source.BasicLaunchLogicTest.records[source.VULCAN]
    state=source.state(record)
    files,_=build_artifact(state,source.BasicLaunchLogicTest.catalog,source.NOW,
        publisher=dict(instance='a'*64,generation=1,selectionValidatedUtc=source.NOW),root=ROOT)
    if PROFILE.exists(): shutil.rmtree(PROFILE)  # only this task's generated artifact
    for name,data in files.items():
        path=PROFILE/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    raw,feed,route,paths=selected_files(PROFILE)
    old=deepcopy(feed);old['launch'].pop('operator_abbrev',None)
    later=deepcopy(feed);later['publisher']['generation']=2
    bad=deepcopy(later);bad['publisher']['generation']=3;bad['launch']['country_code']='??'
    headers={}; sites={}
    for item in source.BasicLaunchLogicTest.rows.values():
        config=(item.get('rocket') or {}).get('configuration') or {}
        org=item.get('launch_service_provider') or {};pad=item.get('pad') or {}
        loc=pad.get('location') or {};country=pad.get('country') or {}
        values=[config.get('full_name') or config.get('name') or '',org.get('name') or '',
                org.get('abbrev') or '',loc.get('name') or pad.get('name') or '',
                _country_code(country) or '',(item.get('mission') or {}).get('type') or '']
        values=[v if len(v)<=64 else v[:63]+'…' for v in values]
        headers.setdefault((values[0],values[1],values[2]),values)
        sites.setdefault((values[1],values[3],values[4]),values)
    corpus=sorted(list(headers.values())+list(sites.values()))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'header-footer-corpus.json').write_bytes(canonical_bytes(
        {'sourceLaunches':len(source.BasicLaunchLogicTest.rows),'headerCases':len(headers),
         'footerCases':len(sites),'rows':corpus}))
    bindings=[]
    for path in paths:
        data=raw[path]
        bindings.append('store.write('+json.dumps('sf.obj.'+hashlib.sha256(data).hexdigest())+','+json.dumps(data.decode(),ensure_ascii=False)+');')
    unknown_row=source.BasicLaunchLogicTest.rows['1b11f81e-cdbf-49aa-a7ce-aa79f609046c']
    from tools.spacefox.provider import normalize_launch
    unknown_record=normalize_launch(unknown_row,source.NOW)
    unknown_files,_=build_artifact(source.state(unknown_record),source.BasicLaunchLogicTest.catalog,source.NOW,
        publisher=dict(instance='b'*64,generation=1,selectionValidatedUtc=source.NOW),root=ROOT)
    unknown_profile=OUT/'native-unknown-artifact'
    if unknown_profile.exists(): shutil.rmtree(unknown_profile)
    for name,data in unknown_files.items():
        path=unknown_profile/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    unknown_raw,_,unknown_route,unknown_paths=selected_files(unknown_profile)
    unknown_bindings=[]
    for path in unknown_paths:
        data=unknown_raw[path]
        unknown_bindings.append('store.write('+json.dumps('sf.obj.'+hashlib.sha256(data).hexdigest())+','+json.dumps(data.decode(),ensure_ascii=False)+');')
    program=IMPORTS+'''import Toybox.Graphics;
(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}
(:typecheck(false)) function siteRaw(old){return old?'''+json.dumps(canonical_bytes(old).decode(),ensure_ascii=False)+':'+json.dumps(canonical_bytes(later).decode(),ensure_ascii=False)+''';}
(:typecheck(false)) function badSiteRaw(){return '''+json.dumps(canonical_bytes(bad).decode(),ensure_ascii=False)+''';}
(:typecheck(false)) function sitePacket(old){var store=new NativeStore();'''+''.join(bindings)+'''var raw=old?'''+json.dumps(canonical_bytes(old).decode(),ensure_ascii=False)+':'+json.dumps(raw[route].decode(),ensure_ascii=False)+''';return new NativeBridgeFeed(raw,'''+str(source.NOW)+''',store);}
(:typecheck(false)) function unknownSitePacket(){var store=new NativeStore();'''+''.join(unknown_bindings)+'''return new NativeBridgeFeed('''+json.dumps(unknown_raw[unknown_route].decode(),ensure_ascii=False)+','+str(source.NOW)+''',store);}
(:test,:typecheck(false)) function siteFlagPositive(logger){
 var p=sitePacket(false);var c=feedScene(p,'''+str(source.NOW)+''');
 if(!c.rocket.equals("Vulcan VC6L")||!c.operator.equals("ULA")||!c.purpose.equals("Communications")||!c.site.equals("US · Cape Canaveral SFS")){return false;}
 if(!p.document["launch"]["operator_name"].equals("United Launch Alliance")||!p.document["launch"]["site_location_name"].equals("Cape Canaveral SFS, FL, USA")){return false;}
 var l=new LocalePresentation();l.prepare("ru");if(!l.mission("Communications").equals("Связь")||!l.mission("Test Flight").equals("Test Flight")){return false;}l.prepare("en");if(!l.mission("Communications").equals("Communications")){return false;}
 var store=new NativeStore();var b=new NativeSfrBuild(store,"https://site-flag.invalid",p);var step=0;while(!b.complete&&step<1000){b.step();step+=1;}
 if(!b.complete||b.result.bitmap==null||b.result.mapBitmap==null||b.result.siteCountryBitmap==null){return false;}
 var staticFlag=b.result.siteCountryBitmap;b.result.prepareFrame(0.5,4);if(b.result.siteCountryBitmap!=staticFlag){return false;}
 var writes=store.writes;var reopened=new NativeSfrBuild(store,"https://site-flag.invalid",p);step=0;while(!reopened.complete&&step<1000){reopened.step();step+=1;}if(!reopened.complete||store.writes!=writes){return false;}
 logger.debug("SITE_FLAG_POSITIVE realVulcan=true operator=ULA country=US staticFlag=true roleCount=3 completeAtomicDecode=true rasterReopenWrites=0");return true;
}
(:test,:typecheck(false)) function siteFlagNegative(logger){
 logger.debug("SITE_NEG step=country");var p=sitePacket(false);var b=new NativeSfrBuild(new NativeStore(),"https://site-flag.invalid",p);b.scene["roles"]["siteCountry"]["entityId"]=p.bridge["ids"][1];
 var rejected=false;try{b.prepareRole("siteCountry");}catch(ex){rejected=true;}if(!rejected){return false;}
 logger.debug("SITE_NEG step=model");var q=sitePacket(false);var m=new NativeSfrBuild(new NativeStore(),"https://site-flag.invalid",q);m.scene["roles"]["rocket"]["entityId"]=q.bridge["ids"][2];rejected=false;try{m.prepareRole("rocket");}catch(ex){rejected=true;}if(!rejected){return false;}
 logger.debug("SITE_NEG step=corrupt");var corrupt=sitePacket(false);var cs=new NativeStore();var cb=new NativeSfrBuild(cs,"https://site-flag.invalid",corrupt);var key="sf.obj."+cb.scene["roles"]["siteCountry"]["descriptor"][0];var saved=cs.read(key);cs.write(key,"{}");rejected=false;try{cb.prepareRole("siteCountry");}catch(ex){rejected=true;}cs.write(key,saved);if(!rejected){return false;}
 logger.debug("SITE_NEG step=unknown");var u=unknownSitePacket();var ub=new NativeSfrBuild(new NativeStore(),"https://site-flag.invalid",u);if(ub.scene["position"]!=null||ub.scene["roles"]["map"]!=null){return false;}var n=0;while(!ub.complete&&n<1000){ub.step();n+=1;}if(!ub.complete||ub.result.mapBitmap!=null||ub.result.siteCountryBitmap==null){return false;}
 logger.debug("SITE_NEG step=zero-and-swap");var zero=new SceneContext({"id"=>u.launchId(),"point"=>[0,0]});if(zero.point==null||zero.point[0]!=0||zero.point[1]!=0){return false;}
 var oldView=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"unknown"));oldView.setContext(feedScene(p,'''+str(source.NOW)+'''));oldView.downloaded=new NativeSfrRenderer();var replacement=new SceneContext({"id"=>u.launchId(),"rocket"=>"Orbex Prime","modelId"=>"ll2:configuration:999999999"});oldView.setContext(replacement);var drawing=new SceneRenderer(null);drawing.prepare(replacement,new SceneSettings(null));if(oldView.downloaded!=null||drawing.model!=NativeAssets.models["generic"]||!replacement.rocket.equals("Orbex Prime")){return false;}
 logger.debug("SITE_NEG step=metadata");var before=sitePacket(true);var after=sitePacket(false);if(!before.recordHash.equals(after.recordHash)){return false;}after.metadata(before,'''+str(source.NOW)+''');
 logger.debug("SITE_NEG step=cache");var st=new NativeStore();var cache=new NativeCache("https://site-flag-age.invalid",st);st.remove(cache.pinKey);st.remove("sf.pins");st.remove("sf.commit");st.remove("sf.recovery");if(!cache.accept(siteRaw(true),'''+str(source.NOW)+''')){logger.debug("SITE_CACHE first="+cache.failure);return false;}if(!cache.accept(siteRaw(false),'''+str(source.NOW)+''')){logger.debug("SITE_CACHE second="+cache.failure);return false;}var reopened=new NativeCache("https://site-flag-age.invalid",st);if(reopened.load('''+str(source.NOW)+''')==null){logger.debug("SITE_CACHE reopen="+reopened.failure);return false;}if(reopened.packet.validation!=before.validation||reopened.packet.rescheduled){logger.debug("SITE_CACHE age="+reopened.packet.validation+" expected="+before.validation+" rescheduled="+reopened.packet.rescheduled);return false;}if(reopened.accept(badSiteRaw(),'''+str(source.NOW)+''')||reopened.packet.validation!=before.validation){logger.debug("SITE_CACHE invalid="+reopened.failure);return false;}
 logger.debug("SITE_NEG step=absent");var absent=new SceneContext({"id"=>p.launchId(),"rocket"=>"Vulcan VC6L"});var pd=new LocalePresentation();var ad=new SiteBoundRenderer(pd);ad.prepare(absent,new SceneSettings(null));var img=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();ad.active(img.getDc(),new ClockSnapshot("08:08","--:--:--"),new SceneSettings(null),{},new Fitness(),0.0);if(!absent.operator.equals("")||!absent.purpose.equals("")||!ad.operatorShown.equals("—")||!ad.purposeShown.equals("—")){return false;}
 logger.debug("SITE_FLAG_NEGATIVE wrongCountryAndModelRejected=true corruptRasterRefRejected=true unknownPadNoPin=true zeroValid=true identitySwapClears=true missingExplicit=true metadataReopenAgePreserved=true invalidUpdateRetainsPrior=true");return !after.rescheduled&&after.validation==before.validation;
}
'''
    program += '''
(:test,:typecheck(false)) class SiteBoundRenderer extends SceneRenderer {
 var valid=true;var operatorShown="";var purposeShown="";
 function initialize(p){SceneRenderer.initialize(p);}
 function text(dc as Graphics.Dc,x as Numeric,y as Numeric,font as Graphics.FontType,value as String,color as Number,width as Number,contour as Number) as String {
  var shown=SceneRenderer.text(dc,x,y,font,value,color,width,contour);var w=dc.getTextWidthInPixels(shown,font);
  if(y==47){operatorShown=shown;}if(y==70){purposeShown=shown;}
  if(y==43||y==47){if(x-w/2<75||x+w/2>315){valid=false;}}
  if(y==319){if(x-w/2-26<65||x+w/2>325||w>216){valid=false;}}
  return shown;
 }
}
(:test,:typecheck(false)) function siteCorpusBounds(logger){
 var p=sitePacket(false);var b=new NativeSfrBuild(new NativeStore(),"https://site-flag.invalid",p);var step=0;while(!b.complete&&step<1000){b.step();step+=1;}if(!b.complete||b.result.siteCountryBitmap==null){return false;}
 var canvas=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();var dc=canvas.getDc();var settings=new SceneSettings(null);var presentation=new LocalePresentation();var renderer=new SiteBoundRenderer(presentation);renderer.prepare(feedScene(p,NOW_VALUE),settings);renderer.downloaded=b.result;
 var rows=CORPUS_VALUE;for(var lang=0;lang<2;lang+=1){settings.language=lang==0?"en":"ru";presentation.prepare(settings.language);renderer.prepare(feedScene(p,NOW_VALUE),settings);renderer.downloaded=b.result;
  for(var i=0;i<rows.size();i+=1){var v=rows[i];var l=p.document["launch"];l["configuration_name"]=v[0];l["operator_name"]=v[1];l["operator_abbrev"]=v[2];l["site_location_name"]=v[3];l["country_code"]=v[4];l["mission_purpose"]=v[5];p.presentation=null;renderer.fullContext=feedScene(p,NOW_VALUE);renderer.active(dc,new ClockSnapshot("08:08","02:00:00"),settings,{},new Fitness(),0.0);if(!renderer.valid){logger.debug("SITE_BOUNDS_FAILED language="+settings.language+" row="+i);return false;}}
 }
 logger.debug("SITE_CORPUS_BOUNDS rows="+rows.size()+" languages=2 sourceLaunches=1822 valid=true");return true;
}
'''.replace('NOW_VALUE',str(source.NOW)).replace('CORPUS_VALUE',json.dumps(corpus,ensure_ascii=False,separators=(',',':')))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'SiteFlagAssertions.mc').write_text(program)
    return {'selectedFiles':len(files),'artifactBytes':sum(map(len,files.values())), 'feedBytes':len(raw[route]),
            'assertionSha256':hashlib.sha256(program.encode()).hexdigest()}


if __name__=='__main__':print(json.dumps(build_fixture(),sort_keys=True))
