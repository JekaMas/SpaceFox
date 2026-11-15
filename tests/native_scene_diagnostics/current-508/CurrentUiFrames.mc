import Toybox.Application;
import Toybox.Background;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Timer;
import Toybox.WatchUi;

(:typecheck(false)) class UiFrameClock extends WatchClock {
    var now=1800000000;
    function initialize(){WatchClock.initialize();}
    function utcSeconds(){return now;}
    function localTimeText(){return "08:08";}
    function localCalendar(){return [7,14,11];}
}
(:typecheck(false)) class UiFrameView extends SpaceFoxView {
    var clock;var phase=-2;var started=0;var frames=0;var timer;
    function initialize(c){SpaceFoxView.initialize(c,new ScheduleState(null,"empty"));clock=c;}
    function onShow(){started=System.getTimer();SpaceFoxView.onShow();if(!animationRunning){onExitSleep();}System.println("UI_NATURAL_START running="+animationRunning);}
    function onUpdate(dc){
        if(phase<0){if(animationRunning){frames+=1;}SpaceFoxView.onUpdate(dc);System.println(phase==-2?"UI_ACTIVE_EN":"UI_ACTIVE_RU");}
        else {updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);System.println("UI_AOD phase="+phase+" minute="+aodMinute+" countdown="+snapshot().countdown+" running="+animationRunning);}
    }
    function animationDone(){
        var elapsed=System.getTimer()-started;SpaceFoxView.animationDone();System.println("UI_NATURAL_DONE elapsedMs="+elapsed+" frames="+frames+" running="+animationRunning+" progress="+animationProgress);
        phase=-1;setSettings(new SceneSettings({"Language"=>1,"Field1"=>4,"Field2"=>5,"Field3"=>0,"Field4"=>1,"ClockColor"=>2,"CountdownColor"=>3,"Field1Color"=>0,"Field2Color"=>4,"Field3Color"=>5,"Field4Color"=>1}));
        setContext(new SceneContext({"id"=>"ll2:launch:fcd23739-8135-43bb-9524-a5dba87d40ac","rocket"=>"Long March 4B","operator"=>"China Aerospace Science and Technology Corporation","purpose"=>"Earth Science","site"=>"CN · Taiyuan Satellite Launch Center, People's Republic of China","target"=>1800176523,"precision"=>"exact"}));
        values={"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"calories"=>2345,"battery"=>82};WatchUi.requestUpdate();timer=new Timer.Timer();timer.start(method(:next),3000,false);
    }
    function next(){
        if(phase==-1){phase=0;onEnterSleep();clock.now=1800000000;timer=new Timer.Timer();timer.start(method(:next),4000,true);}
        else {phase+=1;clock.now=1800000000+phase*60;if(phase>3){timer.stop();System.println("UI_AOD_COMPLETE phases=4");return;}}
        WatchUi.requestUpdate();
    }
}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
    function initialize(){SpaceFoxApp.initialize();}
    (:typecheck(disableBackgroundCheck)) function getInitialView(){
        Application.Properties.setValue("FeedBaseUrl","");Background.deleteTemporalEvent();var c=new UiFrameClock();var v=new UiFrameView(c);
        v.setContext(new SceneContext({"id"=>"ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b","rocket"=>"Starship V3","operator"=>"SpaceX","purpose"=>"Communications","site"=>"US · SpaceX Starbase, TX, USA","target"=>1800176523,"precision"=>"exact"}));
        v.values={"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"calories"=>2345,"battery"=>82};return [v];
    }
}
