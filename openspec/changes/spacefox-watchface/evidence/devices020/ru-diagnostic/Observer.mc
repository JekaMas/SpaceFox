import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
import Toybox.WatchUi;
(:typecheck(false)) class Devices020Proxy extends WatchUi.WatchFace {
    var actual;
    function initialize(v){WatchFace.initialize();actual=v;}
    function onLayout(dc){actual.onLayout(dc);}
    function onShow(){actual.onShow();}
    function onHide(){actual.onHide();}
    function onEnterSleep(){actual.onEnterSleep();}
    function onExitSleep(){actual.onExitSleep();}
    function onUpdate(dc){System.println("DEVICE020_BEGIN "+System.getTimer());actual.onUpdate(dc);System.println("DEVICE020_END "+System.getTimer()+" utc="+Time.now().value()+" locale="+actual.presentation.locale+" visual="+(actual.downloaded!=null));}
}
(:background,:typecheck(false)) class Devices020App extends SpaceFoxApp {
    function initialize(){SpaceFoxApp.initialize();}
    function getInitialView(){var result=SpaceFoxApp.getInitialView();return [new Devices020Proxy(result[0])];}
}
