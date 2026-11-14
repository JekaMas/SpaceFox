import Toybox.WatchUi;
import Toybox.Lang;
import Toybox.Test;

(:test, :typecheck(false)) function composedBatteryDistinct(logger) {
    var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
    view.values={"steps"=>123,"energy"=>68,"heart"=>67,"stress"=>8,"battery"=>82,"calories"=>456};
    var renderer=new SceneRenderer(view.presentation);renderer.prepare(null,view.settings);
    Test.assert(renderer.metricText(view.fitness,view.values,"battery",view.settings).equals("82%"));
    Test.assert(renderer.metricText(view.fitness,view.values,"energy",view.settings).equals("68"));
    Test.assert(view.snapshot().battery.equals("82%"));
    logger.debug("selected watch charge 82% and body energy 68 are independent");return true;
}
(:test, :typecheck(false)) function composedBatteryUnavailable(logger) {
    var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
    view.values={"steps"=>123,"energy"=>68,"heart"=>67,"stress"=>8,"battery"=>null,"calories"=>456};
    var renderer=new SceneRenderer(view.presentation);renderer.prepare(null,view.settings);
    Test.assert(renderer.metricText(view.fitness,view.values,"battery",view.settings).equals("—"));
    Test.assert(renderer.metricText(view.fitness,view.values,"energy",view.settings).equals("68"));
    Test.assert(view.snapshot().battery.equals("—"));
    logger.debug("missing watch charge stays unavailable while body energy remains 68");return true;
}

(:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 function initialize(){SpaceFoxApp.initialize();}
 function getInitialView() as [Views] or [Views,InputDelegates] {return SpaceFoxApp.getInitialView();}
}
