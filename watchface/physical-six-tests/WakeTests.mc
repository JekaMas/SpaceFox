import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.Timer;

(:test,:typecheck(false)) class PhysicalWakeTimer extends Timer.Timer {
 function initialize(){}
 function start(callback as Method,delay as Number,repeating as Boolean) as Void {}
 function stop() as Void {}
}
(:test,:typecheck(false)) class PhysicalWakeClock extends WatchClock {
 function utcSeconds() as Number {return 1800000000;}
 function localTimeText() as String {return "08:25";}
}
(:test,:typecheck(false)) class PhysicalWakeDc extends Graphics.Dc {function initialize(){}}
(:test,:typecheck(false)) class PhysicalWakeView extends SpaceFoxView {
 var mode=System.DISPLAY_MODE_LOW_POWER;var requests=0;var paints=0;
 function initialize(){SpaceFoxView.initialize(new PhysicalWakeClock(),new ScheduleState(null,"empty"));}
 function deviceMode() as System.DisplayMode{return mode;}
 function requestFrame() as Void {requests+=1;}
 function logMode() as Void {}
 function newViewTimer() as Timer.Timer {return new PhysicalWakeTimer();}
 function onLayout(dc as Graphics.Dc) as Void {renderer=new PbtFrameRenderer();layoutReady=true;}
 function drawScene(dc as Graphics.Dc) as Boolean {paints+=1;return true;}
}
(:test,:typecheck(false)) function physicalFirstWakeFromColdLow(logger){
 var view=new PhysicalWakeView();view.onShow();Test.assert(view.displayMode()==0);
 var before=view.requests;view.mode=System.DISPLAY_MODE_HIGH_POWER;view.onExitSleep();
 Test.assertMessage(view.displayMode()==1&&view.requests>before,"first OS wake after cold LOW must request ACTIVE without another wake");
 view.updateForDisplayMode(new PhysicalWakeDc(),System.DISPLAY_MODE_HIGH_POWER);Test.assert(view.paints==1);
 before=view.requests;view.onExitSleep();Test.assert(view.requests==before);view.onHide();
 logger.debug("cold LOW -> first OS wake -> active paint; duplicate wake is idempotent");return true;
}
