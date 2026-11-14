import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Background;
import Toybox.Time;
import Toybox.Timer;
(:typecheck(false)) class UxClock extends WatchClock {var now=1794540000l;function utcSeconds(){return now;}function localTimeText(){return "08:08";}}
(:typecheck(false)) class UxFitness extends Fitness {
 function sample(now as Number or Long) as Dictionary<String, Number or Null> {return {"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"calories"=>2345,"battery"=>82};}
}
(:background,:typecheck(false)) class UxQuiet extends FeedService {function onTemporalEvent() as Void {Background.deleteTemporalEvent();Background.exit(null);}}
(:typecheck(false)) class UxMaintView extends SpaceFoxView {
 function initialize(c,s){SpaceFoxView.initialize(c,s);}
 function onLayout(dc){SpaceFoxView.onLayout(dc);maintenanceTimeFont=renderer.fonts["time"];maintenanceCountFont=renderer.fonts["count"];maintenanceMetricFont=renderer.fonts["metric"];visualMaintenance=true;releaseRenderer();System.println("UX03_MAINT ready="+visualMaintenance+" rendererNull="+(renderer==null));}
}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.ownerTag="db397c8a8ea54ee9ac91ee6e7a674d19|maintenance|1fa76a529e69";System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);NativeMetrics.enabled=true;}
 function getServiceDelegate(){return [new UxQuiet()];}
 function getInitialView(){
  var clock=new UxClock();view=new UxMaintView(clock,new ScheduleState(clock.now+176523l,"minute"));view.setContext(new SceneContext({"id"=>"d74afbc7-0de5-491c-be05-4e9c31f736ac","rocket"=>"Falcon 9 Block 5","site"=>"US · Cape Canaveral SFS","target"=>clock.now+176523l,"precision"=>"exact","stale"=>true}));view.fitness=new UxFitness();view.setSettings(new SceneSettings({"ClockColor"=>3,"CountdownColor"=>2,"Field4"=>5,"Field4Color"=>3}));
  view.values={"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"calories"=>2345,"battery"=>82};
  view.syncDisplayMode(System.getDisplayMode());Background.deleteTemporalEvent();
  System.println("UX_VISUAL initial mode="+System.getDisplayMode());return [view];
 }
 function onDisplayModeChanged(){SpaceFoxApp.onDisplayModeChanged();System.println("UX_VISUAL mode="+System.getDisplayMode());}
}
