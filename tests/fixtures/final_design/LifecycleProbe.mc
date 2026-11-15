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
(:typecheck(false))
class FinalGuardView extends SpaceFoxView {
    var draws=0;
    function initialize(clock as WatchClock){SpaceFoxView.initialize(clock,new ScheduleState(null,"empty"));}
    function maintenance(dc as Graphics.Dc) as Void {draws+=1;}
}
function finalContext() as SceneContext {
    return new SceneContext({"id"=>"fixture-a","rocket"=>"Vulcan VC6L","operator"=>"ULA","purpose"=>"Communications","site"=>"US · Cape Canaveral SFS","target"=>1800007200,"precision"=>"exact"});
}
function finalBuffer() as Graphics.BufferedBitmap {
    return Graphics.createBufferedBitmap({:width=>390,:height=>390}).get() as Graphics.BufferedBitmap;
}
(:test, :typecheck(false))
function finalAnimationLifecycle(logger as Test.Logger) as Boolean {
    var v=new SpaceFoxView(new FinalClock(),new ScheduleState(null,"empty"));
    v.setContext(finalContext());v.onShow();v.onExitSleep();
    var started=v.animationRunning;v.setSettings(new SceneSettings(null));var settingsStopped=!v.animationRunning && v.animationProgress==0.0;v.onExitSleep();v.onEnterSleep();var stopped=!v.animationRunning && v.animationProgress==0.0;
    v.onExitSleep();var restarted=v.animationRunning;v.onHide();
    logger.debug("wake starts; sleep and hide stop/reset; static fallback duration 2.5s");
    return started && settingsStopped && stopped && restarted && !v.animationRunning && v.animationProgress==0.0 && new NativeVisualRenderer().duration()==2.5;
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
    var c=new FinalClock();var v=new FinalGuardView(c);v.setContext(finalContext());v.onShow();v.onExitSleep();
    var im=finalBuffer();v.onLayout(im.getDc());v.onEnterSleep();v.visualMaintenance=true;v.onUpdate(im.getDc());var first=v.aodMinute;var firstDraws=v.draws;c.now+=1;v.onUpdate(im.getDc());var same=v.aodMinute;var sameDraws=v.draws;c.now+=60;v.onUpdate(im.getDc());var next=v.aodMinute;var nextDraws=v.draws;
    logger.debug("actual low-power guard calls substituted maintenance once per minute and animation remains stopped");v.onHide();return first==same && next!=same && firstDraws==1 && sameDraws==1 && nextDraws==2 && !v.animationRunning;
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
