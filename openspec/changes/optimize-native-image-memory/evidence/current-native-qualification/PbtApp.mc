import Toybox.Application;
import Toybox.WatchUi;
// Test-only entrypoint: construction and startup do not create SpaceFoxApp,
// timers, storage, network, background registrations or sensor providers.
(:typecheck(false)) class PbtApp extends Application.AppBase {
 function initialize(){Application.AppBase.initialize();}
 function getInitialView(){return [new PbtEmptyView()];}
}
(:typecheck(false)) class PbtEmptyView extends WatchUi.WatchFace {
 function initialize(){WatchUi.WatchFace.initialize();}
}
