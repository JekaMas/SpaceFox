// Explicit visual-only input adapters. Not in production/default/test sourcePath.
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;
class PreviewClock extends WatchClock {
    function initialize(){WatchClock.initialize();}
    function utcSeconds() as Number{return PreviewInput.utc;}
    function localTimeText() as String{return PreviewInput.clock;}
}
class PreviewTelemetry extends Fitness {
    function initialize(){Fitness.initialize();}
    function sample(now as Number or Long) as Dictionary<String, Number or Null>{return PreviewInput.metrics;}
}
class AnimationObservedView extends SpaceFoxView {
    var started as Number=0;var frames as Number=0;var peak as Float=0.0;
    function initialize(clock as WatchClock,schedule as ScheduleState){SpaceFoxView.initialize(clock,schedule);}
    function onExitSleep() as Void {started=System.getTimer();System.println("ANIMATION_START "+started);SpaceFoxView.onExitSleep();}
    function onUpdate(dc as Graphics.Dc) as Void {SpaceFoxView.onUpdate(dc);if(animationRunning){frames+=1;if(animationProgress>peak){peak=animationProgress;}}}
    function animationDone() as Void {System.println("ANIMATION_DONE elapsedMs="+(System.getTimer()-started)+" frames="+frames+" peak="+peak);SpaceFoxView.animationDone();}
}
class ScenePreviewApp extends SpaceFoxApp {
    function initialize(){SpaceFoxApp.initialize();}
    function getInitialView() as [Views] or [Views, InputDelegates] {
        var selected=PreviewInput.animate?new AnimationObservedView(new PreviewClock(),new ScheduleState(null,"empty")):new SpaceFoxView(new PreviewClock(),new ScheduleState(null,"empty"));
        selected.setSettings(new SceneSettings(PreviewInput.settings));
        if(PreviewInput.context!=null){selected.setContext(new SceneContext(PreviewInput.context as Dictionary<String,Object or Null>));}
        selected.fitness=new PreviewTelemetry();
        if(!PreviewInput.asleep){selected.onExitSleep();}else{selected.onEnterSleep();}
        if(PreviewInput.frame!=null){selected.animationProgress=PreviewInput.frame as Float;}
        return [selected];
    }
}
