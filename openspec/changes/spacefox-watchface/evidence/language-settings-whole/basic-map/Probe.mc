import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Background;
import Toybox.Time;
import Toybox.Timer;
(:background,:typecheck(false)) class MotionQuiet extends System.ServiceDelegate {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}
(:typecheck(false)) class MotionProxy extends WatchUi.WatchFace {
 var app;function initialize(a){WatchFace.initialize();app=a;}
 function onLayout(dc){app.view.onLayout(dc);}function onShow(){app.view.onShow();}function onHide(){app.view.onHide();}
 function onUpdate(dc){var v=app.view;var reads=app.feed.store.reads;var writes=app.feed.store.writes;var loads=v.presentation.loads;var resources=v.renderer==null?0:v.renderer.resourceLoads;var r=v.downloaded;var bitmap=r==null?null:r.bitmap;var matrix=r==null?null:r.transform;v.onUpdate(dc);if(reads!=app.feed.store.reads||writes!=app.feed.store.writes||loads!=v.presentation.loads||v.renderer!=null&&resources!=v.renderer.resourceLoads||r!=null&&(r.bitmap!=bitmap||r.transform!=matrix)){throw new Lang.InvalidValueException("motion redraw I/O/resources");}app.draws+=1;}
}
(:background,:extendedCode,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var observer=null;var requested=0;var checks=0;var sampledHigh=0;var beforeWrites=0;var draws=0;var phase=0;var rich=null;var age=null;var seal=null;var point=null;var frameValue=0.0;var deferredAdmitted=false;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.ownerTag="7af62b7a43d84afcb21e8d935670c105|map-proof|e3fbb187da1d";System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);NativeMetrics.enabled=false;NativeMetrics.traceStores=false;}
 function getServiceDelegate(){return [new MotionQuiet()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){
 Application.Properties.setValue("FeedBaseUrl","https://map-only-native.invalid");Application.Properties.setValue("Language",0);Application.Properties.setValue("Field1",0);Application.Properties.setValue("Field2",4);Application.Properties.setValue("Field3",5);Application.Properties.setValue("Field4",3);
 var chosenFrame=0.0;frameValue=(chosenFrame instanceof Number||chosenFrame instanceof Float)?chosenFrame.toFloat():0.0;if(frameValue<0||frameValue>1){frameValue=0.0;}SpaceFoxApp.getInitialView();view.pendingLoader=method(:begin);Background.deleteTemporalEvent();return [new MotionProxy(self)];}
 (:typecheck(disableBackgroundCheck)) function begin(){requested=System.getTimer();beforeWrites=feed.store.writes;SpaceFoxApp.reloadFeed();observer=new Timer.Timer();observer.start(method(:ready),50,false);}
 function ensure(ok,message){if(!ok){throw new Lang.InvalidValueException(message);}}
 (:typecheck(disableBackgroundCheck)) function ready(){
 Background.deleteTemporalEvent();checks+=1;var used=System.getSystemStats().usedMemory;if(used>sampledHigh){sampledHigh=used;}
 if(view.downloaded==null||view.sfrBuild!=null||view.sfrRequested){if(checks>250){System.println("MOTION_FAILED fullSceneMissing checks="+checks+" generation="+(feed.packet==null?-1:feed.packet.document["publisher"]["generation"]));observer.stop();observer=null;return;}observer.start(method(:ready),50,false);return;}
 rich=view.downloaded;ensure(rich instanceof NativeSfrRenderer,"wrong renderer");ensure(rich.selectionHash.equals(feed.packet.bridge["selection"]["sha256"]),"selection mismatch");age=feed.packet.validation;seal=feed.store.read("sf.commit")["seal"];point=view.context.point;
 System.println("BASIC_MAP_CONTEXT site="+view.context.site+" rocket="+view.context.rocket);ensure(view.context.site.equals("US · SpaceX Starbase, TX, USA")&&view.context.rocket.equals("Starship V3"),"captured context mismatch");ensure(rich.scene["position"]!=null&&rich.mapBitmap!=null&&rich.bitmap!=null,"captured map/rocket mismatch");System.println("BASIC_MAP site="+view.context.site+" rocket="+view.context.rocket+" siteId="+feed.packet.document["launch"]["site_id"]+" modelId="+feed.packet.document["launch"]["configuration_id"]+" position="+rich.scene["position"]+" mapBitmap=true rocketBitmap=true markerAnchor=335,165 sourceSelection="+rich.selectionHash);var elapsed=System.getTimer()-requested;ensure(elapsed<8000,"strict preparation phase exceeded8s");ensure(System.getSystemStats().totalMemory==126784,"not ordinary foreground");
 view.animationProgress=frameValue;WatchUi.requestUpdate();System.println("MOTION_READY profile="+"SFR1M"+" phase="+phase+" generation="+feed.packet.document["publisher"]["generation"]+" validation="+age+" elapsedMs="+elapsed+" sampledHigh="+sampledHigh+" total="+System.getSystemStats().totalMemory+" writes="+(feed.store.writes-beforeWrites)+" modelFlag="+(rich.modelOriginBitmap!=null)+" frame="+view.animationProgress+" canvas="+rich.manifest["canvas"]+" duration="+rich.duration()+" draws="+draws+" noDrawIo=true");
 observer.stop();observer=null;
 }

}
