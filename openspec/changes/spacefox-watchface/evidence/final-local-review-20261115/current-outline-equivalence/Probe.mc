import Toybox.Application;import Toybox.Background;import Toybox.Graphics;import Toybox.Lang;import Toybox.System;import Toybox.Timer;import Toybox.WatchUi;
(:typecheck(false)) class PhaseClock extends WatchClock {var now=1794551280;function initialize(){WatchClock.initialize();}function utcSeconds(){return now;}function localTimeText(){return "08:08";}function localCalendar(){return [1,15,11];}}
(:typecheck(false)) class PhaseView extends SpaceFoxView {
 var phaseClock;var phase=0;var started=0;var taskTimer;var rich;
 function initialize(c){SpaceFoxView.initialize(c,new ScheduleState(null,"empty"));phaseClock=c;}
 function onShow(){SpaceFoxView.onShow();onEnterSleep();rich=new NativeSfrRenderer();rich.scene={"position"=>true};rich.mapOutline=WatchUi.loadResource(Rez.Drawables.AodRestMask);renderer.downloaded=rich;started=System.getTimer();WatchUi.requestUpdate();taskTimer=new Timer.Timer();taskTimer.start(method(:next),12000,true);}
 function onUpdate(dc){updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);var ms=System.getTimer()-started;var r=renderer as SceneRenderer;System.println("PHASE frame="+phase+" lang="+(phase<4?"en":"ru")+" ms="+ms+" map="+(r.aodMap!=null)+" point="+r.aodPin+" minute="+aodMinute);}
 function next(){phase+=1;if(phase>=2){taskTimer.stop();System.println("EQUIVALENCE_COMPLETE");return;}rich.mapOutline=null;rich.bundledOutline=true;aodMinute=null;started=System.getTimer();WatchUi.requestUpdate();}

}
(:background,:typecheck(false)) class PhaseApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}function getInitialView(){Application.Properties.setValue("FeedBaseUrl","");var c=new PhaseClock();var v=new PhaseView(c);v.setContext(new SceneContext({"id"=>"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a","rocket"=>"Vulcan VC6L","operator"=>"United Launch Alliance","operatorShort"=>"ULA","purpose"=>"Communications","site"=>"US · Cape Canaveral SFS","point"=>[-80.58303644,28.58341025],"target"=>1794592440,"precision"=>"minute"}));return [v];}}
