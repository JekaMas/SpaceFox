// Runtime-lifecycle observer. No synthetic onExitSleep call at startup.
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
class RuntimeObservedView extends AnimationObservedView {
    function initialize(clock as WatchClock,schedule as ScheduleState){AnimationObservedView.initialize(clock,schedule);}
    function onExitSleep() as Void{AnimationObservedView.onExitSleep();System.println("RUNTIME_WAKE running="+animationRunning);}
    function onEnterSleep() as Void{System.println("RUNTIME_SLEEP before="+animationRunning+" progress="+animationProgress);SpaceFoxView.onEnterSleep();System.println("RUNTIME_SLEEP after="+animationRunning+" progress="+animationProgress);}
}

class LifecyclePreviewApp extends SpaceFoxApp {
    function initialize(){SpaceFoxApp.initialize();}
    function getInitialView() as [Views] or [Views,InputDelegates] {
        var selected=new RuntimeObservedView(new PreviewClock(),new ScheduleState(null,"empty"));
        selected.setSettings(new SceneSettings(PreviewInput.settings));
        if(PreviewInput.context!=null){selected.setContext(new SceneContext(PreviewInput.context as Dictionary<String,Object or Null>));}
        selected.fitness=new PreviewTelemetry();
        return [selected];
    }
}
