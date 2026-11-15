import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Background;
import Toybox.Time;
import Toybox.Timer;

(:background,:typecheck(false)) class SfrLifeQuiet extends FeedService {function onTemporalEvent() as Void {System.println("SFR_LIFE_QUIET calls=0 owner="+NativeMetrics.ownerTag);Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var observer=null;var last="";var checks=0;var completed=null;var holdInitial=false;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.ownerTag="bc2f73c361fd435abef2e5841220cdf9|ru-draw-io|7c6edd591566";System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);NativeMetrics.enabled=true;NativeMetrics.traceStores=false;}
 function getServiceDelegate() as [System.ServiceDelegate]{return [new SfrLifeQuiet()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView() as [Views] or [Views,InputDelegates]{Application.Properties.setValue("FeedBaseUrl","https://lifecycle.invalid");Application.Properties.setValue("Language",1);var result=SpaceFoxApp.getInitialView();view.pendingLoader=method(:beginLife);return [new DrawProxy(self)];}
 (:typecheck(disableBackgroundCheck)) function beginLife() as Void {if(!holdInitial){SpaceFoxApp.reloadFeed();}else{Background.deleteTemporalEvent();System.println("SFR_LIFECYCLE diagnosticInitialHold=true owner="+NativeMetrics.ownerTag);}startPulse();}
 (:typecheck(disableBackgroundCheck)) function startPulse() as Void {if(System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}checks=0;last="";if(observer==null){observer=new Timer.Timer();}observer.start(method(:pulse),50,true);}
 (:typecheck(disableBackgroundCheck)) function report(label) as Void {if(view==null){return;}if(completed==null&&view.downloaded!=null){completed=view.downloaded;}System.println("SFR_LIFECYCLE event="+label+" mode="+System.getDisplayMode()+" buildTimer="+(view.sfrTimer!=null)+" build="+(view.sfrBuild!=null)+" requested="+view.sceneLifecycle.pending()+" bitmap="+(view.downloaded!=null)+" sameBitmap="+(completed!=null&&completed==view.downloaded)+" animation="+view.animationRunning+" progress="+view.animationProgress+" fitnessTimer="+(view.fitnessTimer!=null)+" reads="+feed.store.reads+" writes="+feed.store.writes+" ms="+System.getTimer()+" owner="+NativeMetrics.ownerTag);}
 (:typecheck(disableBackgroundCheck)) function pulse() as Void {checks+=1;var key="state|"+(view.sfrTimer!=null)+"|"+(view.sfrBuild!=null)+"|"+view.sceneLifecycle.pending()+"|"+(view.downloaded!=null)+"|"+view.animationRunning+"|"+(view.fitnessTimer!=null);if(!key.equals(last)){last=key;report("state");}if(checks>=600){observer.stop();observer=null;report("observer-finite-end");}}
 (:typecheck(disableBackgroundCheck)) function onDisplayModeChanged() as Void {if(System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){holdInitial=false;}SpaceFoxApp.onDisplayModeChanged();report("display");if(System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){startPulse();}else if(observer!=null){observer.stop();observer=null;}}
 (:typecheck(disableBackgroundCheck)) function onBackgroundData(data as Application.PersistableType) as Void {if(holdInitial){Background.deleteTemporalEvent();return;}SpaceFoxApp.onBackgroundData(data);if(view!=null){report("background");}}
}

(:typecheck(false)) class DrawProxy extends WatchUi.WatchFace {var app;var draws=0;function initialize(a){WatchFace.initialize();app=a;}function onLayout(dc){app.view.onLayout(dc);}function onShow(){app.view.onShow();}function onHide(){app.view.onHide();}function onUpdate(dc){var v=app.view;var reads=app.feed.store.reads;var writes=app.feed.store.writes;var loads=v.presentation.loads;var resources=v.renderer==null?0:v.renderer.resourceLoads;var r=v.downloaded;var bitmap=r==null?null:r.bitmap;var matrix=r==null?null:r.transform;System.println("DRAW_BEGIN n="+(draws+1));v.onUpdate(dc);System.println("DRAW_END n="+(draws+1));if(reads!=app.feed.store.reads||writes!=app.feed.store.writes||loads!=v.presentation.loads||v.renderer!=null&&resources!=v.renderer.resourceLoads||r!=null&&(r.bitmap!=bitmap||r.transform!=matrix)){throw new Lang.InvalidValueException("draw I/O or resource reconstruction");}draws+=1;System.println("RU_DRAW_OK count="+draws+" bitmap="+(r!=null)+" locale="+v.settings.language);}}
