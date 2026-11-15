#!/usr/bin/env python3
"""Source-bound ordinary SDK probes for native origins and catalog motion.

Seed mode replaces only transport with producer-validated immutable bytes.
Ordinary modes contain no pixel/raw fixture constants, use production owners,
and preserve exact preparation/timing boundaries. Never runs the Simulator while
building. Caller owns the exclusive Simulator lease and external test key.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
if __package__ in (None, ''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import native_full_visual_runtime as runtime
from tools.native_full_visual_quota import source as quota_source
from tools.native_full_visual_lifecycle import source as lifecycle_source
from tools.native_full_visual_faults import source as fault_source
ROOT=Path(__file__).resolve().parents[1]
PACKET=ROOT/'openspec/changes/spacefox-watchface/evidence/current-only-native'


def anchors():
    return runtime.IMPORTS+'''import Toybox.Graphics;
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=false;}
 function near(actual,expected){if(actual<expected-0.0001||actual>expected+0.0001){throw new Lang.InvalidValueException("anchor actual="+actual+" expected="+expected);}}
 function anchor(r,progress,ascent,x,y,mx,my){r.prepareFrame(progress,ascent);var p=r.transform.transformPoint([27.0,62.0]);near(r.frameX+p[0],x);near(r.frameY+p[1],y);p=r.transform.transformPoint([0.0,0.0]);near(r.frameX+17*r.frameScale+p[0],mx);near(r.frameY+52*r.frameScale+p[1],my);}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){
 Application.Properties.setValue("FeedBaseUrl","");Background.deleteTemporalEvent();var r=new NativeVisualRenderer();var matrix=r.transform;var options=r.drawOptions;r.animations=[2000,[[0,0,0,256],[2000,128,-256,512]]];
 r.prepareCanvas([32,256]);near(r.fitScale,0.484375);anchor(r,0.0,0,49.0,180.0,39.0,170.0);anchor(r,0.5,0,49.96875,178.0625,34.96875,163.0625);anchor(r,1.0,0,50.9375,176.125,30.9375,156.125);
 r.prepareCanvas([256,32]);near(r.fitScale,0.2109375);anchor(r,0.0,0,49.0,180.0,39.0,170.0);anchor(r,0.5,0,49.421875,179.15625,34.421875,164.15625);anchor(r,1.0,9,49.84375,169.3125,29.84375,149.3125);
 if(matrix!=r.transform||options!=r.drawOptions){throw new Lang.InvalidValueException("transform reallocated");}
 System.println("MOTION_ANCHORS_COMPLETE tall=3 wide=3 sourceScale=uniform SDKtransformPoint=true pivot=27,62 rocketOnlyTransform=true identityPreserved=true memory="+System.getSystemStats().usedMemory);return [new WatchUi.WatchFace()];}
}
'''


def selected_files(profile):
    files={str(p.relative_to(profile)):p.read_bytes() for p in profile.rglob('*') if p.is_file()}
    route='feed.json'
    feed=json.loads(files[route]);index=feed['nativeTransfer']
    paths={feed['catalogPath'],index['path']}
    for kind,digest,size in json.loads(files[index['path']])['objects']:
        path=('rasters/' if kind else 'descriptors/')+digest+('.sfr' if kind else '.json')
        raw=files[path]
        if len(raw)!=size or hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('fixture immutable mismatch')
        paths.add(path)
    return files,feed,route,sorted(paths)


def seed(profile,url,frame=0.0,objects_only=False):
    files,feed,route,paths=selected_files(profile)
    body=[]
    for path in paths:
        raw=files[path];digest=hashlib.sha256(raw).hexdigest()
        ref=dict(path=path,sha256=digest,decodedBytes=len(raw))
        body.append('if(!objects.put('+runtime.literal(ref)+','+json.dumps(raw.decode(),ensure_ascii=False)+')){throw new Lang.InvalidValueException("seed immutable refused");}')
    if objects_only:
        body.append('if(!before.equals(store.read("sf.commit")["seal"])){throw new Lang.InvalidValueException("object setup changed accepted seal");}')
    else:
        body.append('var t=new NativeTransfer('+json.dumps(url)+',store);if(!t.stage("feed",'+json.dumps(files[route].decode(),ensure_ascii=False)+',null)){throw new Lang.InvalidValueException("seed feed refused");}')
    return runtime.IMPORTS+'(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}\n(:test,:typecheck(false)) function motionSeed(logger){var store=new NativeStore();var before='+('store.read("sf.commit")["seal"]' if objects_only else 'null')+';var objects=new NativeImmutable(store);'+''.join(body)+'Application.Properties.setValue("FeedBaseUrl",'+json.dumps(url)+');Application.Storage.setValue("sf.control.frame",'+str(float(frame))+');Background.deleteTemporalEvent();logger.debug("MOTION_SEEDED generation='+str(feed['publisher']['generation'])+' objects='+str(len(paths))+' objectsOnly='+str(objects_only).lower()+' sourceAdmission=false");return true;}\n'


def observe(url, frame=0.0, trace=False, defer_pending=False, refusal=False):
    # Controlled-frame capture is distinct from natural wrist animation.
    source=runtime.IMPORTS+'''import Toybox.Timer;
(:background,:typecheck(false)) class MotionQuiet extends System.ServiceDelegate {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}
(:typecheck(false)) class MotionProxy extends WatchUi.WatchFace {
 var app;function initialize(a){WatchFace.initialize();app=a;}
 function onLayout(dc){app.view.onLayout(dc);}function onShow(){app.view.onShow();}function onHide(){app.view.onHide();}
 function onUpdate(dc){var v=app.view;var reads=app.feed.store.reads;var writes=app.feed.store.writes;var loads=v.presentation.loads;var resources=v.renderer==null?0:v.renderer.resourceLoads;var r=v.downloaded;var bitmap=r==null?null:r.bitmap;var matrix=r==null?null:r.transform;v.onUpdate(dc);if(reads!=app.feed.store.reads||writes!=app.feed.store.writes||loads!=v.presentation.loads||v.renderer!=null&&resources!=v.renderer.resourceLoads||r!=null&&(r.bitmap!=bitmap||r.transform!=matrix)){throw new Lang.InvalidValueException("motion redraw I/O/resources");}app.draws+=1;}
}
(:background,:extendedCode,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var observer=null;var requested=0;var checks=0;var sampledHigh=0;var beforeWrites=0;var draws=0;var phase=0;var rich=null;var age=null;var seal=null;var point=null;var frameValue=0.0;var deferredAdmitted=false;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled='''+runtime.literal(trace)+''';NativeMetrics.traceStores=false;}
 function getServiceDelegate(){return [new MotionQuiet()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){
 Application.Properties.setValue("FeedBaseUrl",'''+runtime.literal(url)+''');Application.Properties.setValue("Language",0);Application.Properties.setValue("Field1",0);Application.Properties.setValue("Field2",4);Application.Properties.setValue("Field3",5);Application.Properties.setValue("Field4",3);
 var chosenFrame='''+(str(float(frame)) if frame>=0 else 'Application.Storage.getValue("sf.control.frame")')+''';frameValue=(chosenFrame instanceof Number||chosenFrame instanceof Float)?chosenFrame.toFloat():0.0;if(frameValue<0||frameValue>1){frameValue=0.0;}SpaceFoxApp.getInitialView();view.pendingLoader=method(:begin);Background.deleteTemporalEvent();return [new MotionProxy(self)];}
 (:typecheck(disableBackgroundCheck)) function begin(){requested=System.getTimer();beforeWrites=feed.store.writes;''' + ('view.prepareVisual();' if defer_pending else 'SpaceFoxApp.reloadFeed();') + '''observer=new Timer.Timer();observer.start(method(:ready),50,false);}
 function ensure(ok,message){if(!ok){throw new Lang.InvalidValueException(message);}}
 (:typecheck(disableBackgroundCheck)) function ready(){
 Background.deleteTemporalEvent();checks+=1;var used=System.getSystemStats().usedMemory;if(used>sampledHigh){sampledHigh=used;}
 if(view.downloaded==null||view.sfrBuild!=null||view.sfrRequested){if(checks>250){System.println("MOTION_FAILED fullSceneMissing checks="+checks+" generation="+(feed.packet==null?-1:feed.packet.document["publisher"]["generation"]));observer.stop();observer=null;return;}observer.start(method(:ready),50,false);return;}
 rich=view.downloaded;ensure(rich instanceof NativeSfrRenderer,"wrong renderer");ensure(rich.selectionHash.equals(feed.packet.bridge["selection"]["sha256"]),"selection mismatch");age=feed.packet.validation;seal=feed.store.read("sf.commit")["seal"];point=view.context.point;
 ''' + ('''if(!deferredAdmitted){deferredAdmitted=true;var priorBitmap=rich;var priorGeneration=feed.packet.document["publisher"]["generation"];var priorAge=feed.packet.validation;SpaceFoxApp.reloadFeed();ensure(view.downloaded==priorBitmap,"source-only admission lost accepted bitmap");System.println("CURRENT_SAME_SESSION oldGeneration="+priorGeneration+" newGeneration="+feed.packet.document["publisher"]["generation"]+" oldAge="+priorAge+" newAge="+feed.packet.validation+" sameBitmap=true");age=feed.packet.validation;seal=feed.store.read("sf.commit")["seal"];}''' if defer_pending else '') + '''var elapsed=System.getTimer()-requested;ensure(elapsed<8000,"strict preparation phase exceeded8s");ensure(System.getSystemStats().totalMemory==126784,"not ordinary foreground");
 view.animationProgress=frameValue;WatchUi.requestUpdate();System.println("MOTION_READY profile="+"SFR1M"+" phase="+phase+" generation="+feed.packet.document["publisher"]["generation"]+" validation="+age+" elapsedMs="+elapsed+" sampledHigh="+sampledHigh+" total="+System.getSystemStats().totalMemory+" writes="+(feed.store.writes-beforeWrites)+" siteCountryFlag="+(rich.siteCountryBitmap!=null)+" frame="+view.animationProgress+" canvas="+rich.manifest["canvas"]+" duration="+rich.duration()+" draws="+draws+" noDrawIo=true");
 observer.stop();observer=null;
 }

}
'''

    if refusal:
        source=source.replace('var deferredAdmitted=false;', 'var deferredAdmitted=false;var expectedAge=null;var expectedSeal=null;var expectedGeneration=null;var expectedFloor=null;')
        original='SpaceFoxApp.reloadFeed();ensure(view.downloaded==priorBitmap,"source-only admission lost accepted bitmap");'
        injected='expectedAge=priorAge;expectedSeal=feed.store.read("sf.commit")["seal"];expectedGeneration=priorGeneration;expectedFloor=feed.store.read(feed.pinKey)["generation"];requested=System.getTimer();beforeWrites=feed.store.writes;SpaceFoxApp.reloadFeed();rich=null;return;'
        source=source.replace(original,injected)
        source=source.replace('var elapsed=System.getTimer()-requested;', 'ensure(feed.packet.validation==expectedAge&&feed.store.read("sf.commit")["seal"].equals(expectedSeal)&&feed.packet.document["publisher"]["generation"]==expectedGeneration&&feed.store.read(feed.pinKey)["generation"]==expectedFloor,"refusal changed accepted source/seal/floor");System.println("CURRENT_REFUSAL exactAgeSealFloor=true generation="+expectedGeneration+" sourceEpoch="+expectedAge+" bitmapReconstructed=true");var elapsed=System.getTimer()-requested;')
    return source


def cleanup_source(url):
    source=runtime.observer_source(url,cleanup=True)
    controls='''if(Application.Storage.getValue("sf.control.corrupt")!=null||Application.Storage.getValue("sf.control.fill.max")!=null){throw new Lang.InvalidValueException("unrecovered diagnostic state");}Application.Storage.deleteValue("sf.control.frame");Application.Storage.deleteValue("sf.control.bg.feed");System.println("MOTION_CONTROLS_CLEANED frame=true backgroundRaw=true noFillerOrCorruptBackup=true");'''
    return source.replace('function sfrQuiesce(){','function sfrQuiesce(){'+controls)


def restage(profile,url):
    path=profile if profile.is_file() else profile/"feed.json"
    raw_bytes=path.read_bytes();feed=json.loads(raw_bytes)
    raw=runtime.literal(raw_bytes.decode())
    return runtime.IMPORTS+'''(:background,:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 function initialize(){AppBase.initialize();NativeMetrics.enabled=true;}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){Background.deleteTemporalEvent();var store=new NativeStore();var before=store.read("sf.commit")["seal"];var t=new NativeTransfer('''+runtime.literal(url)+''',store);var raw='''+raw+''';if(!t.stage("feed",raw,null)){throw new Lang.InvalidValueException("restage");}if(!before.equals(store.read("sf.commit")["seal"])){throw new Lang.InvalidValueException("restage changed accepted seal");}System.println("MOTION_RESTAGED generation='''+str(feed['publisher']['generation'])+''' exactRaw=true currentProfile=SFR1M acceptedSeal="+before+" sourceAdmission=false");return [new WatchUi.WatchFace()];}
}
'''


def late_provenance_setup(profile,url):
    files,feed,route,_=selected_files(profile)
    feed['providerTraversal']={'query':'qualification-only','complete':True,'reportedCount':1,'receivedUpcoming':1,'detailRequests':0,'worldwideCompleteness':True}
    raw=json.dumps(feed,sort_keys=True,ensure_ascii=False,separators=(',',':'))
    return runtime.IMPORTS+'''(:background,:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 function initialize(){AppBase.initialize();}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){Background.deleteTemporalEvent();var store=new NativeStore();var before=store.read("sf.commit")["seal"];var t=new NativeTransfer('''+runtime.literal(url)+''',store);if(!t.stage("feed",'''+runtime.literal(raw)+''',null)){throw new Lang.InvalidValueException("late provenance staging");}var after=store.read("sf.commit")["seal"];if(!before.equals(after)){throw new Lang.InvalidValueException("setup changed accepted seal");}System.println("MOTION_LATE_PROVENANCE_STAGED invalidWorldwideClaim=true validationPhase=traversal acceptedSeal="+before+" sourceAdmission=false");return [new WatchUi.WatchFace()];}
}
'''


def optional_fault_setup(mode):
    """Mutate only the owned optional raw object without renderer residency.

    This setup is deliberately separate from the subsequent production reopen.
    Keeping a complete scene while allocating the diagnostic backup can exhaust
    the ordinary heap; that failed probe is retained rather than hidden.
    """
    return runtime.IMPORTS+'''(:background,:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 function initialize(){AppBase.initialize();}
 function sealed(){var h=new NativeCanonical();var keys=["sf.commit","sf.recovery","sf.pins"];for(var i=0;i<keys.size();i+=1){var key=keys[i];h.quoted(key);h.emit(Application.Storage.getValue(key));}return h.digest();}
 function digest(raw){var h=new NativeWireHash();h.put(raw);return h.digest();}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){Background.deleteTemporalEvent();var before=sealed();var backup=Application.Storage.getValue("sf.control.corrupt");
 '''+('''
 if(backup==null){var active=Application.Storage.getValue("sf.raster.active");var chosen=null;for(var j=0;j<active["refs"].size();j+=1){var r=active["refs"][j];if(r[0]==1){chosen=r;break;}}if(chosen==null){throw new Lang.InvalidValueException("no optional raster");}var key="sf.obj."+chosen[1];var raw=Application.Storage.getValue(key);if(!digest(raw).equals(chosen[1])){throw new Lang.InvalidValueException("original optional raw invalid");}backup={"key"=>key,"sha256"=>chosen[1],"raw"=>raw};Application.Storage.setValue("sf.control.corrupt",backup);}
 if(!digest(backup["raw"]).equals(backup["sha256"])||!backup["key"].equals("sf.obj."+backup["sha256"])){throw new Lang.InvalidValueException("backup binding");}
 var altered=backup["raw"].substring(0,backup["raw"].length()-1)+"!";Application.Storage.setValue(backup["key"],altered);System.println("MOTION_OPTIONAL_CORRUPTED key="+backup["key"]+" original="+backup["sha256"]+" altered="+digest(altered)+" bytes="+altered.length()+" setupBlank=true");
 ''' if mode=='corrupt-setup' else '''
 if(!(backup instanceof Dictionary)||!digest(backup["raw"]).equals(backup["sha256"])||!backup["key"].equals("sf.obj."+backup["sha256"])){throw new Lang.InvalidValueException("backup binding");}Application.Storage.setValue(backup["key"],backup["raw"]);Application.Storage.deleteValue("sf.control.corrupt");System.println("MOTION_OPTIONAL_RESTORED key="+backup["key"]+" sha256="+backup["sha256"]+" setupBlank=true");
 ''')+'''var after=sealed();if(!before.equals(after)){throw new Lang.InvalidValueException("accepted metadata changed");}System.println("MOTION_OPTIONAL_SETUP_COMPLETE before="+before+" after="+after+" preserved=true memory="+System.getSystemStats().usedMemory+" total="+System.getSystemStats().totalMemory);return [new WatchUi.WatchFace()];}
}
'''


def draw_observer(source):
    """Observe after the real draw without consuming a fourth SDK timer.

    The normal timer observer can contend with fitness + executing restore +
    decoder timers during rejected-source recovery. Only the diagnostic owns
    this change; production onUpdate is checked before the observer runs.
    """
    source=source.replace('app.draws+=1;', 'app.draws+=1;if(app.requested>0&&app.rich==null){app.ready();}')
    source=source.replace('observer=new Timer.Timer();observer.start(method(:ready),50,false);', '')
    source=source.replace('observer.stop();observer=null;return;', 'return;')
    source=source.replace('observer.start(method(:ready),50,false);return;', 'return;')
    source=source.replace('observer.start(method(:change),1500,false);', 'if(observer==null){observer=new Timer.Timer();}observer.start(method(:change),1500,false);')
    source=source.replace('observer.stop();observer=null;', '')
    return source


def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['anchors','seed','cleanup','fill','clean','observe','lifecycle','corrupt','inspect-corrupt','restore','retry','corrupt-setup','restore-setup','late-provenance','restage']);p.add_argument('--identity',type=Path,default=PACKET/'identity.json');p.add_argument('--profile',type=Path);p.add_argument('--frame',type=float,default=0.0);p.add_argument('--trace',action='store_true');p.add_argument('--defer-pending',action='store_true');p.add_argument('--refusal',action='store_true');p.add_argument('--draw-observer',action='store_true');p.add_argument('--hold-initial',action='store_true');p.add_argument('--objects-only',action='store_true');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    identity=json.loads(a.identity.read_text());runtime.GROUPS['motion']=(identity['uuid'],identity['basename'])
    source=observe(identity['url'],a.frame,a.trace,a.defer_pending or a.refusal,a.refusal) if a.mode=='observe' else anchors() if a.mode=='anchors' else seed(a.profile,identity['url'],a.frame,a.objects_only) if a.mode=='seed' else quota_source(a.mode) if a.mode in ('fill','clean') else lifecycle_source(identity['url'],a.hold_initial) if a.mode=='lifecycle' else fault_source(identity['url'],a.mode) if a.mode in ('corrupt','inspect-corrupt','restore','retry') else runtime.observer_source(identity['url'],cleanup=True)
    if a.mode=='cleanup':source=cleanup_source(identity['url'])
    if a.mode=='restage':source=restage(a.profile,identity['url'])
    if a.mode=='late-provenance':source=late_provenance_setup(a.profile,identity['url'])
    if a.mode in ('corrupt-setup','restore-setup'):source=optional_fault_setup(a.mode)
    if a.draw_observer or a.refusal:
        if a.mode!='observe':p.error('--draw-observer requires observe')
        source=draw_observer(source)
    result=runtime.build_probe(a.output,source,group='motion',tests=a.mode=='seed',source_files=['watchface/source/NativeMetrics.mc'] if a.mode in ('fill','clean') else None)
    result['expectedTests']=['motionSeed'] if a.mode=='seed' else []
    result['generatorSha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (a.output/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('exitCode','sourceSetSha256','packageName')}));return result['exitCode']
if __name__=='__main__':sys.exit(main())
