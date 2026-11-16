import Toybox.Application;
import Toybox.Graphics;
import Toybox.System;
import Toybox.Time;
import Toybox.Timer;
import Toybox.WatchUi;
(:typecheck(false)) class B1TimerClock extends WatchClock {
 var origin;
 function initialize(){origin=Time.now().value().toLong();}
 function utcSeconds(){return 1794551202l+Time.now().value().toLong()-origin;}
 function localTimeText(){return "08:38";}
}
(:typecheck(false)) class B1TimerView extends SpaceFoxView {
 var c;var app;var last=null;
 function initialize(clock,owner){c=clock;app=owner;SpaceFoxView.initialize(clock,new ScheduleState(null,"empty"));}
 function onShow(){SpaceFoxView.onShow();app.begin();}
 function onUpdate(dc){SpaceFoxView.onUpdate(dc);if(sfrBuild!=null){var value=snapshotAt(c.utcSeconds()).countdown;if(last==null||!last.equals(value)){System.println("B1_TIMER frame="+value+" actual_sfr_pending=true simulated_now="+c.utcSeconds());last=value;}}}
}
(:typecheck(false)) class B1TimerApp extends Application.AppBase {
 var view;var cache;var job;var timer;
 function initialize(){AppBase.initialize();}
 function getInitialView(){var clock=new B1TimerClock();view=new B1TimerView(clock,self);cache=new NativeCache("https://fixture.invalid/profile-a",new NativeStore());job=new NativeRestoreJob(cache,clock.utcSeconds(),null);return [view];}
 function begin(){view.beginAdmission();timer=new Timer.Timer();timer.start(method(:step),100,true);}
 function step(){if(!job.finished){job.step();return;}timer.stop();timer=null;if(!job.restored){System.println("B1_TIMER no_stored_profile");view.endAdmission();return;}System.println("B1_TIMER profile_restored");view.setPacket(cache.packet);view.setAssetCache(new NativeRenderSource(cache.store,cache.base,cache.packet.bridge));view.endAdmission();}
}
