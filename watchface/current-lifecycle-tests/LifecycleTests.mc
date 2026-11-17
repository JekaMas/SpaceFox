import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.Time;
import Toybox.Time.Gregorian;
import Toybox.WatchUi;

(:typecheck(false))
class SfrRuntimeApp extends SpaceFoxApp {
    function initialize(){SpaceFoxApp.initialize();}
    function getInitialView() as [Views] or [Views,InputDelegates] {return SpaceFoxApp.getInitialView();}
}
(:typecheck(false))
class FinalClock extends WatchClock {
    var now=1800000000;
    function initialize(){WatchClock.initialize();}
    function utcSeconds() as Number{return now;}
    function localTimeText() as String{return "08:08";}
}
(:typecheck(false)) class FinalAodRenderer extends SceneRenderer {
    var draws=0;
    function initialize(){SceneRenderer.initialize(null);}
    function aod(dc,current,minute,settings){draws+=1;SceneRenderer.aod(dc,current,minute,settings);}
}
function finalContext() as SceneContext {
    return new SceneContext({"id"=>"ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b","rocket"=>"Starship V3","operator"=>"SpaceX","purpose"=>"Communications","site"=>"US · Starbase","target"=>1800007200,"precision"=>"exact"});
}
function finalBuffer() as Graphics.BufferedBitmap {
    return Graphics.createBufferedBitmap({:width=>390,:height=>390}).get() as Graphics.BufferedBitmap;
}
(:test, :typecheck(false))
function finalStaticLifecycle(logger as Test.Logger) as Boolean {
    var v=new SpaceFoxView(new FinalClock(),new ScheduleState(null,"empty"));
    v.setContext(finalContext());var dc=finalBuffer().getDc();v.onLayout(dc);v.onShow();
    v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);v.resumeAfterFrame();v.setSettings(new SceneSettings(null));v.onEnterSleep();
    var low=v.displayMode()==0;v.onExitSleep();v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);var active=v.displayMode()==1;v.onHide();
    logger.debug("static face preserves LOW and ACTIVE lifecycle");return low && active && !v.visible();
}
(:test, :typecheck(false))
function finalAnimationBounds(logger as Test.Logger) as Boolean {
    var validator=new NativeAnimation();var rejected=0;
    validator.validate([2000,[[0,0,0,256],[2000,0,-32,256]]]);
    validator.validate([3000,[[0,0,0,256],[3000,0,-32,256]]]);
    try{validator.validate([1999,[[0,0,0,256],[1999,0,-32,256]]]);}catch(e){rejected+=1;}
    try{validator.validate([3001,[[0,0,0,256],[3001,0,-32,256]]]);}catch(e){rejected+=1;}
    logger.debug("actual animation admission inclusive 2000 and 3000ms rejects outside");return rejected==2;
}
(:test, :typecheck(false))
function finalAodMinuteGuard(logger as Test.Logger) as Boolean {
    var c=new FinalClock();var v=new SpaceFoxView(c,new ScheduleState(null,"empty"));v.setContext(finalContext());v.onShow();
    var im=finalBuffer();v.onLayout(im.getDc());var renderer=new FinalAodRenderer();renderer.prepare(v.context,v.settings);v.renderer=renderer;v.onEnterSleep();v.updateForDisplayMode(im.getDc(),System.DISPLAY_MODE_LOW_POWER);var first=v.lastLowFrameMinute();var firstDraws=renderer.draws;c.now+=1;v.updateForDisplayMode(im.getDc(),System.DISPLAY_MODE_LOW_POWER);var same=v.lastLowFrameMinute();var sameDraws=renderer.draws;c.now+=1;v.updateForDisplayMode(im.getDc(),System.DISPLAY_MODE_LOW_POWER);var held=v.lastLowFrameMinute();var heldDraws=renderer.draws;c.now+=60;v.updateForDisplayMode(im.getDc(),System.DISPLAY_MODE_LOW_POWER);var next=v.lastLowFrameMinute();var nextDraws=renderer.draws;
    logger.debug("actual sparse renderer minute guard first="+first+" same="+same+" held="+held+" next="+next+" draws="+firstDraws+","+sameDraws+","+heldDraws+","+nextDraws);v.onHide();return first==null&&same==held&&next!=held&&firstDraws==1&&sameDraws==2&&heldDraws==2&&nextDraws==3;
}

(:typecheck(false)) class FinalDateClock extends FinalClock {
    var dateParts=[7,14,11];
    function localCalendar(){return dateParts;}
}
(:test, :typecheck(false))
function finalLocalCalendar(logger as Test.Logger) as Boolean {
    var p=new LocalePresentation();p.qualificationMode=true;p.prepare("en");
    var en=p.calendar([7,14,11]);p.prepare("ru");var ru=p.calendar([7,14,11]);
    p.prepare("de");var de=p.calendar([7,14,11]);p.prepare("fr");var fr=p.calendar([7,14,11]);p.prepare("es");var es=p.calendar([7,14,11]);
    var clock=new FinalDateClock();var v=new SpaceFoxView(clock,new ScheduleState(null,"empty"));v.setContext(finalContext());v.onShow();v.onExitSleep();
    var first=v.snapshot();clock.dateParts=[1,15,11];var second=v.snapshot();v.onEnterSleep();var aod=v.snapshot();v.onHide();
    var nativeClock=new WatchClock();var actual=nativeClock.localCalendar();var info=Gregorian.info(Time.now(),Time.FORMAT_SHORT);
    logger.debug("five primary weekday labels; local midnight changes 14 Sat to 15 Sun, separate from launch date; actual Garmin local Gregorian smoke");
    return en.equals("Sat 14.11") && ru.equals("Сб 14.11") && de.equals("Sa 14.11") && fr.equals("sam 14.11") && es.equals("sáb 14.11") && first.localCalendar[0]==7 && first.localCalendar[1]==14 && second.localCalendar[0]==1 && second.localCalendar[1]==15 && aod.localCalendar[0]==1 && aod.localCalendar[1]==15 && actual[0]==info.day_of_week && actual[1]==info.day && actual[2]==info.month;
}
