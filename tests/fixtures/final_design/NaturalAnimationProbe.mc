import Toybox.Application;
import Toybox.Background;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;
(:typecheck(false)) class FinalNaturalView extends SpaceFoxView {
    var started=0;var frames=0;var began=false;
    function initialize(){SpaceFoxView.initialize(new WatchClock(),new ScheduleState(null,"empty"));}
    function onShow(){SpaceFoxView.onShow();if(!began){began=true;started=System.getTimer();onExitSleep();System.println("NATURAL_START running="+animationRunning+" owner="+NativeMetrics.ownerTag);}}
    function onUpdate(dc){if(animationRunning){frames+=1;}SpaceFoxView.onUpdate(dc);}
    function animationDone(){var elapsed=System.getTimer()-started;SpaceFoxView.animationDone();System.println("NATURAL_DONE elapsedMs="+elapsed+" frames="+frames+" running="+animationRunning+" progress="+animationProgress+" owner="+NativeMetrics.ownerTag);}
}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
    function initialize(){SpaceFoxApp.initialize();}
    (:typecheck(disableBackgroundCheck)) function getInitialView(){
        Application.Properties.setValue("FeedBaseUrl","");Background.deleteTemporalEvent();
        var v=new FinalNaturalView();v.setContext(new SceneContext({"id"=>"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a","rocket"=>"Vulcan VC6L","operator"=>"United Launch Alliance","operatorShort"=>"ULA","purpose"=>"Communications","site"=>"US · Cape Canaveral SFS","precision"=>"unknown"}));return [v];
    }
}
