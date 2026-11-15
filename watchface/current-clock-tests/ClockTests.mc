import Toybox.Lang;
import Toybox.Graphics;
import Toybox.System;
import Toybox.Test;
import Toybox.Time;
(:test,:typecheck(false)) class CurrentClockInput extends WatchClock {
    var utc=1800000000;var local="08:00";
    function initialize(){WatchClock.initialize();}
    function utcSeconds(){return utc;}
    function localTimeText(){return local;}
}
(:test,:typecheck(false)) function currentClockPositive(logger){
    var c=new CurrentClockInput();var s=new ScheduleState(1800007200,"exact");var v=new SpaceFoxView(c,s);var a=v.snapshot();c.local="12:00";var b=v.snapshot();
    Test.assertEqual(a.localTime,"08:00");Test.assertEqual(b.localTime,"12:00");Test.assertEqual(a.countdown,"T- 02:00:00");Test.assertEqual(b.countdown,"T- 02:00:00");
    logger.debug("CLOCK_LOCAL 08:00->12:00 UTC=7200 unchanged");return true;
}
(:test,:typecheck(false)) function currentClockNegative(logger){
    var c=new CurrentClockInput();c.local="23:59";var v=new SpaceFoxView(c,new ScheduleState(1800007200,"exact"));var a=v.snapshot();c.local="00:01";var b=v.snapshot();
    Test.assertEqual(a.countdown,"T- 02:00:00");Test.assertEqual(b.countdown,"T- 02:00:00");logger.debug("CLOCK_MIDNIGHT no offset applied UTC=7200");return true;
}
(:test,:typecheck(false)) function currentClockAdapter(logger){
    var before=Time.now().value();var c=new WatchClock();var current=c.utcSeconds();var after=Time.now().value();var clockInfo=System.getClockTime();
    Test.assert(current>=before&&current<=after);Test.assertEqual(c.localTimeText(),c.formatLocal(clockInfo.hour,clockInfo.min));logger.debug("CLOCK_API actual Garmin local and UTC adapters");return true;
}
(:test,:typecheck(false)) function currentClockFormatting(logger){
    var c=new WatchClock();Test.assertEqual(c.formatLocal(0,5),"00:05");Test.assertEqual(c.formatLocal(12,5),"12:05");Test.assertEqual(c.formatLocal(23,5),"23:05");logger.debug("CLOCK_FORMAT fixed 24h midnight noon 23h");return true;
}

(:test,:typecheck(false)) class CurrentColorRenderer extends SceneRenderer {
    var timeColor=null;var countColor=null;var underlines=0;
    function initialize(){SceneRenderer.initialize(null);}
    function text(dc,x,y,font,value,color,width,contour){if(y==109){timeColor=color;}if(y==202){countColor=color;}return SceneRenderer.text(dc,x,y,font,value,color,width,contour);}
    function underline(dc,x,y,width,color){underlines+=1;SceneRenderer.underline(dc,x,y,width,color);}
}
(:test,:typecheck(false)) function currentColorStates(logger){
    var r=new CurrentColorRenderer();var settings=new SceneSettings({"ClockColor"=>2,"CountdownColor"=>3});var context=new SceneContext({"id"=>"ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b","rocket"=>"Starship V3","operator"=>"SpaceX","purpose"=>"Communications","site"=>"US · SpaceX Starbase, TX, USA"});r.prepare(context,settings);
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();var clock=new ClockSnapshot("08:08","T- 01:00:00");
    r.active(dc,clock,settings,{},new Fitness(),0.0);Test.assertEqual(r.timeColor,0x9ad5ff);Test.assertEqual(r.countColor,0xcdb7ff);Test.assertEqual(r.underlines,0);
    clock.rescheduled=true;r.active(dc,clock,settings,{},new Fitness(),0.0);Test.assertEqual(r.timeColor,0x9ad5ff);Test.assertEqual(r.countColor,0xff6b6b);Test.assertEqual(r.underlines,0);
    clock.rescheduled=false;clock.stale=true;r.active(dc,clock,settings,{},new Fitness(),0.0);Test.assertEqual(r.timeColor,0x9ad5ff);Test.assertEqual(r.countColor,0xcdb7ff);Test.assertEqual(r.underlines,1);
    clock.rescheduled=true;clock.countdown="--:--:--";r.active(dc,clock,settings,{},new Fitness(),0.0);Test.assertEqual(r.timeColor,0x9ad5ff);Test.assertEqual(r.countColor,0xff6b6b);Test.assertEqual(r.underlines,2);
    clock.rescheduled=false;clock.sourceHold=true;r.active(dc,clock,settings,{},new Fitness(),0.0);Test.assertEqual(r.countColor,0xff6b6b);Test.assertEqual(r.underlines,3);
    logger.debug("COLORS selected clock and countdown; coral reschedule or sourced hold; stale dots; coexisting unknown preserves clock");return true;
}
