import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;

(:test,:typecheck(false)) class Display03Clock extends WatchClock {
    var now=1794762690;
    function initialize(){WatchClock.initialize();}
    function utcSeconds(){return now;}
    function localTimeText(){return "08:08";}
}
(:test,:typecheck(false)) class Display03Renderer extends SceneRenderer {
    var lowText=null;var lowCalls=0;
    function initialize(){SceneRenderer.initialize(null);}
    function aod(dc,current,minute,settings){lowText=current.countdown;lowCalls+=1;}
}
(:test,:typecheck(false)) function display03RepeatedLowCallbacks(logger){
    var target=1794762690;var clock=new Display03Clock();clock.now=1794762540;
    var v=new SpaceFoxView(clock,new ScheduleState(target,"exact"));var d=new Display03Renderer();v.renderer=d;v.onEnterSleep();
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    for(var i=0;i<60;i+=1){clock.now=1794762540+i;v.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);Test.assert(d.lowCalls==1);Test.assertEqual(d.lowText,"T- 00:03");}
    clock.now=1794762600;v.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);Test.assert(d.lowCalls==2);Test.assertEqual(d.lowText,"T- 00:02");
    logger.debug("LOW_CALLBACKS 60 same-minute callbacks one paint; next minute second paint");return true;
}
(:test,:typecheck(false)) function display03MinuteRounding(logger){
    // Captured Vulcan target, independent expected literals. Each case uses a
    // fresh view to avoid the legitimate same-minute redraw suppression.
    var target=1794762690;var offsets=[-61,-60,-59,-1,0,1,59,60,61];
    var expected=["T- 00:02","T- 00:01","T- 00:01","T- 00:01","T+ 00:00","T+ 00:00","T+ 00:00","T+ 00:01","T+ 00:01"];
    var bmp=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();
    for(var i=0;i<offsets.size();i+=1){
        var clock=new Display03Clock();clock.now=target+offsets[i];
        var view=new SpaceFoxView(clock,new ScheduleState(target,"exact"));var d=new Display03Renderer();view.renderer=d;
        view.updateForDisplayMode(bmp.getDc(),System.DISPLAY_MODE_LOW_POWER);
        logger.debug("MINUTE offset="+offsets[i]+" observed="+d.lowText+" expected="+expected[i]);
        Test.assertEqual(d.lowText,expected[i]);
    }
    return true;
}
(:test,:typecheck(false)) class Display03ModeRenderer extends SceneRenderer {
    var activeCalls=0;var lowCalls=0;
    function initialize(){SceneRenderer.initialize(null);}
    function active(dc,current,settings,values,fitness,progress){activeCalls+=1;}
    function aod(dc,current,minute,settings){lowCalls+=1;}
}
(:test,:typecheck(false)) function display03SleepThenHighObservation(logger){
    var c=new Display03Clock();var v=new SpaceFoxView(c,new ScheduleState(1794762690,"exact"));var d=new Display03ModeRenderer();v.renderer=d;
    v.onEnterSleep();var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    logger.debug("SLEEP_QUERY_HIGH active="+d.activeCalls+" low="+d.lowCalls+" mode="+v.displayMode());
    Test.assert(d.activeCalls==0 && d.lowCalls==1);return true;
}
(:test,:typecheck(false)) function display03WakeThenLowObservation(logger){
    var c=new Display03Clock();var v=new SpaceFoxView(c,new ScheduleState(1794762690,"exact"));var d=new Display03ModeRenderer();v.renderer=d;
    v.onEnterSleep();v.onExitSleep();var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    v.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);
    logger.debug("WAKE_QUERY_LOW active="+d.activeCalls+" low="+d.lowCalls+" mode="+v.displayMode());
    // A real LOW display remains protected even after the CPU wake callback.
    Test.assert(d.activeCalls==0 && d.lowCalls==1);
    v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    Test.assert(d.activeCalls==1 && d.lowCalls==1);return true;
}
(:test,:typecheck(false)) function display03PrimaryLanguages(logger){
 var expected=["Sun 15.11","Вс 15.11","So 15.11","dim 15.11","dom 15.11"];
 var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
 for(var i=0;i<5;i+=1){var settings=new SceneSettings({"Language"=>i});var presentation=new LocalePresentation();presentation.prepare(settings.language);var date=presentation.calendar([1,15,11]);Test.assertEqual(date,expected[i]);var width=dc.getTextWidthInPixels(date,presentation.aodContextFont);Test.assert(width>0&&width<=300);logger.debug("PRIMARY_DATE locale="+settings.language+" text="+date+" width="+width);}
 return true;
}
(:test,:typecheck(false)) class D03LocaleView extends SpaceFoxView {
 var refreshes=0;function initialize(c,s){SpaceFoxView.initialize(c,s);}
 function refreshLocale(){refreshes+=1;SpaceFoxView.refreshLocale();}
}
(:test,:typecheck(false)) function display03LocaleResume(logger){
 var c=new Display03Clock();var v=new D03LocaleView(c,new ScheduleState(1794762690,"exact"));v.renderer=new Display03ModeRenderer();v.onShow();var before=v.refreshes;v.onEnterSleep();v.onExitSleep();
 var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assert(v.refreshes==before);v.resumeAfterFrame();Test.assert(v.refreshes==before+1);v.onHide();logger.debug("LOCALE_WAKE refreshed_after_first_frame=true");return true;
}
