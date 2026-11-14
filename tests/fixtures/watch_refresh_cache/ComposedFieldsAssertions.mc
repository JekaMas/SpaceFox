import Toybox.WatchUi;
import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.Time;

(:typecheck(false)) class BasicTelemetry extends Fitness {
    var samples as Number=0;
    function initialize(){Fitness.initialize();}
    function sample(now as Number or Long) as Dictionary<String,Number or Null>{samples+=1;return {"steps"=>12345,"energy"=>null,"heart"=>null,"stress"=>null,"calories"=>null,"battery"=>82};}
}
(:test, :typecheck(false)) function basicFieldsPositive(logger as Test.Logger) as Boolean {
    var wanted=[4,3,4,5];var roles=["calories","stress","calories","battery"];
    for(var i=0;i<4;i+=1){Application.Properties.setValue("Field"+(i+1),wanted[i]);}
    var app=new SpaceFoxApp();var v=app.getInitialView()[0] as SpaceFoxView;
    var first=true;for(var i=0;i<4;i+=1){first=first&&v.settings.slots[i].equals(roles[i]);}
    Application.Properties.setValue("Field2",1);app.onSettingsChanged();
    var reopened=new SceneSettings(null).load();
    var pass=first&&v.settings.slots[0].equals("calories")&&v.settings.slots[1].equals("energy")&&v.settings.slots[2].equals("calories")&&v.settings.slots[3].equals("battery")&&reopened.slots[2].equals("calories")&&reopened.slots[1].equals("energy");
    for(var i=0;i<4;i+=1){Application.Properties.setValue("Field"+(i+1),i);}
    logger.debug("actual Properties and app callback: duplicate selections persist; only second field changes");return pass;
}
(:test, :typecheck(false)) function basicFieldsNegative(logger as Test.Logger) as Boolean {
    var wanted=[4,99,5,4];for(var i=0;i<4;i+=1){Application.Properties.setValue("Field"+(i+1),wanted[i]);}
    var s=new SceneSettings(null).load();var reopened=new SceneSettings(null).load();
    var pass=s.slots[0].equals("calories")&&s.slots[1].equals("energy")&&s.slots[2].equals("battery")&&s.slots[3].equals("calories")&&reopened.slots[0].equals("calories")&&reopened.slots[1].equals("energy")&&reopened.slots[2].equals("battery")&&reopened.slots[3].equals("calories");
    for(var i=0;i<4;i+=1){Application.Properties.setValue("Field"+(i+1),i);}
    logger.debug("only invalid second persisted field defaults; other three including duplicates unchanged");return pass;
}
(:test, :typecheck(false)) function basicUnavailablePositive(logger as Test.Logger) as Boolean {
    var f=new Fitness();var actual=f.sample(Time.now().value());var v=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"unknown"));var input=new BasicTelemetry();v.fitness=input;v.onExitSleep();v.stopAnimation();
    var s=v.snapshot();logger.debug("real Garmin adapter API smoke separately; controlled missing sample exercises actual view/formatter");
    return actual.hasKey("steps")&&actual.hasKey("energy")&&actual.hasKey("heart")&&actual.hasKey("stress")&&actual.hasKey("calories")&&actual.hasKey("battery")&&input.samples==1&&f.display(v.values,"energy").equals("—")&&f.display(v.values,"heart").equals("—")&&f.display(v.values,"stress").equals("—")&&f.display(v.values,"calories").equals("—")&&f.display(v.values,"steps").equals("12345")&&s.localTime.length()==5&&s.countdown.equals("--:--:--");
}
(:test, :typecheck(false)) function basicUnavailableNegative(logger as Test.Logger) as Boolean {
    var f=new Fitness();var v=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"unknown"));v.values={"heart"=>72,"energy"=>68};v.fitness=new BasicTelemetry();v.onExitSleep();v.stopAnimation();
    logger.debug("new missing sample replaces former72/68; age300 accepted,301 or future unavailable; real zero allowed only for applicable metrics");
    return f.display(v.values,"heart").equals("—")&&f.display(v.values,"energy").equals("—")&&f.recentValue(68,1800000000,1800000300,100,false)==68&&f.recentValue(68,1800000000,1800000301,100,false)==null&&f.recentValue(68,1800000001,1800000000,100,false)==null&&f.recentValue(0,1800000000,1800000000,300,true)==null&&f.display({"steps"=>0},"steps").equals("0");
}

(:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 function initialize(){SpaceFoxApp.initialize();}
 function getInitialView() as [Views] or [Views,InputDelegates] {return SpaceFoxApp.getInitialView();}
}
