import Toybox.Application;
import Toybox.Background;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;
import Toybox.Timer;

// Isolated test UUID and public captured feed; no network requests or real
// health values are logged. The first program writes a durable accepted cache;
// the second uses the actual SpaceFoxApp initialization and View lifecycle.
(:background,:typecheck(false)) class D04QuietService extends FeedService {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:typecheck(false)) class D04SeedApp extends Application.AppBase {
 function initialize(){AppBase.initialize();}
 function getServiceDelegate(){return [new D04QuietService()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){
  var started=System.getTimer();var base="https://fixture.invalid/display04-cache";Application.Properties.setValue("FeedBaseUrl",base);
  var store=new NativeStore();var catalog=WatchUi.loadResource(Rez.JsonData.D04Catalog);store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
  var cache=new NativeCache(base,store);var raw=WatchUi.loadResource(Rez.JsonData.D04Feed)["raw"];
  if(!cache.accept(raw,1794551202)){throw new Lang.InvalidValueException("captured feed seed rejected");}
  System.println("D04_SEED accepted=true elapsedMs="+(System.getTimer()-started));return [new WatchUi.WatchFace()];
 }
}
(:typecheck(false)) class D04ControlProxy extends WatchUi.WatchFace {
 var app;var first=true;function initialize(owner){WatchFace.initialize();app=owner;}
 function onLayout(dc){app.view.onLayout(dc);}function onShow(){app.view.onShow();}function onHide(){app.view.onHide();}
 function onEnterSleep(){app.view.onEnterSleep();}function onExitSleep(){app.view.onExitSleep();}
 function onUpdate(dc){app.view.onUpdate(dc);if(first && System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){first=false;var stats=System.getSystemStats();System.println("D04_CONTROL firstFrameMs="+(System.getTimer()-app.started)+" accepted="+(app.feed.packet!=null)+" point="+(app.view.context!=null&&app.view.context.point!=null)+" pin="+(app.view.renderer!=null&&app.view.renderer.pin)+" used="+stats.usedMemory+" total="+stats.totalMemory);app.queueProbe();}}
}
(:background,:typecheck(false)) class D04ControlApp extends SpaceFoxApp {
 var started=0;var probeTimer=null;function initialize(){SpaceFoxApp.initialize();started=System.getTimer();}
 function getServiceDelegate(){return [new D04QuietService()];}
 function queueProbe(){probeTimer=new Timer.Timer();probeTimer.start(method(:runProbe),1000,false);}
 (:typecheck(disableBackgroundCheck)) function runProbe(){
  probeTimer=null;var transfer=new NativeTransfer(feed.base,feed.store);var row=WatchUi.loadResource(Rez.JsonData.D04Moved);var raw=row["raw"];transfer.stage("feed",raw,null);raw=null;row=null;
  System.println("D04_CONTROL movedStaged=true");var start=System.getTimer();reloadFeed();var stats=System.getSystemStats();
  System.println("D04_CONTROL movedAccepted="+(view.context!=null&&view.context.schedule.remainingSeconds(0)==1794611100)+" elapsedMs="+(System.getTimer()-start)+" used="+stats.usedMemory+" total="+stats.totalMemory);
  if(view.context==null||view.context.schedule.remainingSeconds(0)!=1794611100){throw new Lang.InvalidValueException("moved target absent");}
  row=WatchUi.loadResource(Rez.JsonData.D04Moved);raw=row["raw"];transfer.stage("feed",raw,null);raw=null;row=null;reloadFeed();
  if(view.context.schedule.remainingSeconds(0)!=1794611100){throw new Lang.InvalidValueException("duplicate changed target");}
  transfer.stage("feed","{invalid",null);reloadFeed();
  if(!restorePending||view.context.schedule.remainingSeconds(0)!=1794611100){throw new Lang.InvalidValueException("rejection lost accepted target");}
  System.println("D04_CONTROL rejectionRetained=true");
 }
 (:typecheck(disableBackgroundCheck)) function restoreFeed(){SpaceFoxApp.restoreFeed();finishProbe();}
 (:typecheck(disableBackgroundCheck)) function finishProbe(){
  if(restorePending||view.context==null||view.context.schedule.remainingSeconds(0)!=1794611100){throw new Lang.InvalidValueException("accepted restore incomplete");}
  view.onEnterSleep();var renderer=view.renderer;var loads=renderer.resourceLoads;var aod=renderer.aodMap;view.onExitSleep();view.onHide();view.onShow();
  if(view.renderer!=renderer||renderer.resourceLoads!=loads||renderer.aodMap!=aod){throw new Lang.InvalidValueException("warm scene resources reloaded");}
  var stats=System.getSystemStats();System.println("D04_CONTROL restored=true warmScene=true loads="+loads+" used="+stats.usedMemory+" total="+stats.totalMemory);
 }
 (:typecheck(disableBackgroundCheck)) function getInitialView(){
  var result=SpaceFoxApp.getInitialView();System.println("D04_CONTROL initialReturnMs="+(System.getTimer()-started)+" accepted="+(feed.packet!=null)+" targetMoved="+(view.context!=null&&view.context.schedule.remainingSeconds(0)==1794611100));return [new D04ControlProxy(self)];
 }
}
