import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.Time;

// Only technical clock/telemetry are controlled. Display strings are verbatim
// from tests/fixtures/map-only/feed.json, the already captured real launch.
(:test)
class BasicDrawing extends SceneRenderer {
    var rows as Number=0;
    var logger as Test.Logger;
    function initialize(log as Test.Logger){SceneRenderer.initialize(null);logger=log;}
    function text(dc as Graphics.Dc,x as Numeric,y as Numeric,font as Graphics.FontType,value as String,color as Number,width as Number,contour as Number) as String {
        var shown=SceneRenderer.text(dc,x,y,font,value,color,width,contour);
        var kind=font==fonts["time"]?"time":font==fonts["metric"]?"metric":"vector";
        logger.debug("BASIC_TEXT|"+kind+"|"+x+"|"+y+"|"+dc.getTextWidthInPixels(shown,font)+"|"+dc.getFontHeight(font)+"|"+shown);
        rows+=1;return shown;
    }
}
(:test) function currentLayoutEnglish(logger as Test.Logger) as Boolean {
    var d=new BasicDrawing(logger);var s=new SceneSettings(null);
    var c=new SceneContext({"id"=>"ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b","rocket"=>"Starship V3","operator"=>"SpaceX","purpose"=>"Communications","site"=>"US · SpaceX Starbase, TX, USA"});
    d.prepare(c,s);var image=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get() as Graphics.BufferedBitmap;
    var current=new ClockSnapshot("08:08","T- 49:02:03");current.localCalendar=[7,14,11];
    d.active(image.getDc(),current,s,{"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"battery"=>82},new Fitness(),0.0);
    logger.debug("LAYOUT_EN actual captured launch, date, default fields and colors");return d.rows>8;
}
(:test) function currentLayoutRussianLong(logger as Test.Logger) as Boolean {
    var d=new BasicDrawing(logger);var s=new SceneSettings({"Language"=>1,"Field1"=>4,"Field2"=>5,"Field3"=>0,"Field4"=>1,"ClockColor"=>2,"CountdownColor"=>3,"Field1Color"=>0,"Field2Color"=>4,"Field3Color"=>5,"Field4Color"=>1});
    var c=new SceneContext({"id"=>"ll2:launch:fcd23739-8135-43bb-9524-a5dba87d40ac","rocket"=>"Long March 4B","operator"=>"China Aerospace Science and Technology Corporation","purpose"=>"Earth Science","site"=>"CN · Taiyuan Satellite Launch Center, People's Republic of China"});
    d.prepare(c,s);var image=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get() as Graphics.BufferedBitmap;
    var current=new ClockSnapshot("08:08","T+ 00:15:01");current.localCalendar=[7,14,11];
    d.active(image.getDc(),current,s,{"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"calories"=>2345,"battery"=>82},new Fitness(),0.0);
    logger.debug("LAYOUT_RU real long captured launch, date, custom four fields and independent colors");return d.rows>8;
}
(:test)
function basicFieldsPositive(logger as Test.Logger) as Boolean {
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
(:test)
function basicFieldsNegative(logger as Test.Logger) as Boolean {
    var wanted=[4,99,5,4];for(var i=0;i<4;i+=1){Application.Properties.setValue("Field"+(i+1),wanted[i]);}
    var s=new SceneSettings(null).load();var reopened=new SceneSettings(null).load();
    var pass=s.slots[0].equals("calories")&&s.slots[1].equals("energy")&&s.slots[2].equals("battery")&&s.slots[3].equals("calories")&&reopened.slots[0].equals("calories")&&reopened.slots[1].equals("energy")&&reopened.slots[2].equals("battery")&&reopened.slots[3].equals("calories");
    for(var i=0;i<4;i+=1){Application.Properties.setValue("Field"+(i+1),i);}
    logger.debug("only invalid second persisted field defaults; other three including duplicates unchanged");return pass;
}
(:test)
class BasicTelemetry extends Fitness {
    var samples as Number=0;
    function initialize(){Fitness.initialize();}
    function sample(now as Number or Long) as Dictionary<String,Number or Null>{samples+=1;return {"steps"=>12345,"energy"=>null,"heart"=>null,"stress"=>null,"calories"=>null,"battery"=>82};}
}
(:test)
function basicUnavailablePositive(logger as Test.Logger) as Boolean {
    var f=new Fitness();var actual=f.sample(Time.now().value());var v=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"unknown"));var input=new BasicTelemetry();v.fitness=input;v.onExitSleep();v.stopAnimation();
    var s=v.snapshot();logger.debug("real Garmin adapter API smoke separately; controlled missing sample exercises actual view/formatter");
    return actual.hasKey("steps")&&actual.hasKey("energy")&&actual.hasKey("heart")&&actual.hasKey("stress")&&actual.hasKey("calories")&&actual.hasKey("battery")&&input.samples==1&&f.display(v.values,"energy").equals("—")&&f.display(v.values,"heart").equals("—")&&f.display(v.values,"stress").equals("—")&&f.display(v.values,"calories").equals("—")&&f.display(v.values,"steps").equals("12345")&&s.localTime.length()==5&&s.countdown.equals("--:--:--");
}
(:test)
function basicUnavailableNegative(logger as Test.Logger) as Boolean {
    var f=new Fitness();var v=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"unknown"));v.values={"heart"=>72,"energy"=>68};v.fitness=new BasicTelemetry();v.onExitSleep();v.stopAnimation();
    logger.debug("new missing sample replaces former72/68; age300 accepted,301 or future unavailable; real zero allowed only for applicable metrics");
    return f.display(v.values,"heart").equals("—")&&f.display(v.values,"energy").equals("—")&&f.recentValue(68,1800000000,1800000300,100,false)==68&&f.recentValue(68,1800000000,1800000301,100,false)==null&&f.recentValue(68,1800000001,1800000000,100,false)==null&&f.recentValue(0,1800000000,1800000000,300,true)==null&&f.display({"steps"=>0},"steps").equals("0");
}
(:test)
function basicBatteryPositive(logger as Test.Logger) as Boolean {
    var f=new Fitness();var s=new SceneSettings({"Field1"=>1,"Field2"=>1,"Field3"=>5,"Field4"=>4});var values={"battery"=>82,"energy"=>68};
    logger.debug("top battery reads watch82%; BodyBattery68 remains different; four slots including duplicate energy survive");
    return f.display(values,"battery").equals("82%")&&f.display(values,"energy").equals("68")&&s.slots.size()==4&&s.slots[0].equals("energy")&&s.slots[1].equals("energy")&&s.slots[2].equals("battery")&&s.slots[3].equals("calories");
}
(:test)
function basicBatteryNegative(logger as Test.Logger) as Boolean {
    var f=new Fitness();var values={"battery"=>null,"energy"=>68};var s=new SceneSettings({"Field1"=>1,"Field2"=>1,"Field3"=>5,"Field4"=>4});
    logger.debug("missing watch charge cannot borrowBodyBattery68; dedicated battery not a fifth configurable field");
    return f.display(values,"battery").equals("—")&&f.display(values,"energy").equals("68")&&s.slots.size()==4&&s.slots[2].equals("battery");
}
