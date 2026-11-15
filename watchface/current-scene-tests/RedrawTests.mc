import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;

(:test) class DisplayClock extends WatchClock {
 function initialize(){WatchClock.initialize();}
 function utcSeconds() as Number{return 1794551202;}
 function localTimeText() as String{return "08:08";}
}

(:test) class DisplayResumeCounter {
    var calls as Number = 0;
    function load() as Void {calls += 1;}
}
(:test,:typecheck(false)) function displayDrawDefersResume(logger){
    var clock=new DisplayClock();var view=new SpaceFoxView(clock,new ScheduleState(1794609900,"exact"));
    var counter=new DisplayResumeCounter();view.pendingLoader=counter.method(:load);
    var image=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();view.onLayout(image.getDc());view.onShow();view.onEnterSleep();
    var before=counter.calls;var loads=view.renderer.resourceLoads;
    view.updateForDisplayMode(image.getDc(),System.DISPLAY_MODE_HIGH_POWER);
    Test.assert(counter.calls==before && view.renderer.resourceLoads==loads);
    Test.assertEqual(view.snapshot().countdown,"T- 16:18:18");
    view.syncDisplayMode(System.DISPLAY_MODE_HIGH_POWER);
    Test.assert(counter.calls==before+1);view.onHide();
    logger.debug("DRAW_RESUME deferred=true rendererLoadsStable=true callbackResumesOnce=true");return true;
}
