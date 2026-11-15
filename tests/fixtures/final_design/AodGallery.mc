import Toybox.Application;
import Toybox.Background;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;
(:typecheck(false)) class FinalAodClock extends WatchClock {
    var now=1800000000;
    function initialize(){WatchClock.initialize();}
    function utcSeconds(){return now;}
    function localTimeText(){return "08:08";}
}
(:typecheck(false)) class FinalAodView extends SpaceFoxView {
    function initialize(clock){SpaceFoxView.initialize(clock,new ScheduleState(1800003661,"exact"));}
    function onShow(){SpaceFoxView.onShow();onEnterSleep();}
    function onExitSleep(){onEnterSleep();}
    function onUpdate(dc){SpaceFoxView.onUpdate(dc);System.println("FINAL_AOD_DRAW minute="+aodMinute+" total="+System.getSystemStats().totalMemory+" owner="+NativeMetrics.ownerTag);}
}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
    function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=false;}
    (:typecheck(disableBackgroundCheck)) function getInitialView(){
        Application.Properties.setValue("FeedBaseUrl","");Background.deleteTemporalEvent();
        var clock=new FinalAodClock();clock.now=1800000000+__PHASE__*60;
        view=new FinalAodView(clock);view.setSettings(new SceneSettings(null));
        view.restoreStatus=true;view.restoreStale=true;view.restoreRescheduled=true;
        return [view];
    }
}
