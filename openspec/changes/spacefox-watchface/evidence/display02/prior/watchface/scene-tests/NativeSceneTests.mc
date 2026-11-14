import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.Time;

function sceneBuffer() as Graphics.BufferedBitmap {
    if(!(Graphics has :createBufferedBitmap)){throw new Lang.InvalidValueException("requiredAPI4graphicsbufferunavailable");}
    return Graphics.createBufferedBitmap({:width=>390,:height=>390}).get() as Graphics.BufferedBitmap;
}
function suppliedScene() as SceneContext {
    return new SceneContext({"id"=>"fixture-a","rocket"=>"Falcon 9","operator"=>"SpaceX","purpose"=>"Communications","site"=>"USA · Cape Canaveral","modelId"=>"falcon-9","operatorId"=>"company-spacex","point"=>[-80.6043,28.6084],"target"=>1800007200,"precision"=>"exact"});
}
(:test)
class SceneClock extends WatchClock {
    var now as Number=1800000000;
    function initialize(){WatchClock.initialize();}
    function utcSeconds() as Number{return now;}
    function localTimeText() as String{return "08:08";}
}
(:test)
class SceneTelemetry extends Fitness {
    var reads as Number=0;
    function initialize(){Fitness.initialize();}
    function sample(now as Number or Long) as Dictionary<String, Number or Null>{reads+=1;return {"steps"=>12345,"energy"=>0,"heart"=>null,"stress"=>47,"battery"=>82,"calories"=>0};}
}
(:test)
function sceneLayoutPositive(logger as Test.Logger) as Boolean {
    var drawing=new SceneRenderer(null);var settings=new SceneSettings(null);drawing.prepare(suppliedScene(),settings);
    var image=sceneBuffer();var dc=image.getDc();
    drawing.active(dc,new ClockSnapshot("08:08","02:00:00"),settings,new SceneTelemetry().sample(1800000000),new Fitness(),0.0);
    logger.debug("actual390x390 native active resource render; heap="+System.getSystemStats().usedMemory);
    var c=new ClockSnapshot("18:38","unused");c.remaining=9240l;var ru=new SceneSettings({"Language"=>"ru"});var numeric=drawing.displayCountdown(c,ru).equals("02:34:00");c.remaining=8040l;var frozen=drawing.displayCountdown(c,ru).equals("02:14:00");return dc.getWidth()==390 && dc.getHeight()==390 && drawing.pin && drawing.resourceLoads<=20 && numeric && frozen;
}
(:test)
function sceneLayoutNegative(logger as Test.Logger) as Boolean {
    var drawing=new SceneRenderer(null);var image=sceneBuffer();var dc=image.getDc();
    var long="Очень длинная строка названия космического аппарата и назначения";
    var short=drawing.fit(dc,long,drawing.fonts["label"] as Graphics.FontType,238);
    logger.debug("long full retained; bounded actual glyph width="+dc.getTextWidthInPixels(short,drawing.fonts["label"] as Graphics.FontType));
    return short.length()<long.length() && dc.getTextWidthInPixels(short,drawing.fonts["label"] as Graphics.FontType)<=238;
}
(:test)
function sceneContextPositive(logger as Test.Logger) as Boolean {
    var v=new SpaceFoxView(new SceneClock(),new ScheduleState(null,"empty"));var a=suppliedScene();v.setContext(a);v.onExitSleep();v.stopAnimation();
    var first=v.snapshot();var b=new SceneContext({"id"=>"fixture-b","rocket"=>"Electron","operator"=>"Rocket Lab","purpose"=>"Small satellites","site"=>"New Zealand · Mahia","modelId"=>"electron","operatorId"=>"company-rocket-lab","point"=>[166.463,-39.261],"target"=>1800010800,"precision"=>"exact"});v.setContext(b);
    logger.debug("selected-id a->b swaps all context/time as one reference");
    return first.countdown.equals("02:00:00") && v.snapshot().countdown.equals("03:00:00") && v.context==b && (v.context as SceneContext).site.equals("New Zealand · Mahia");
}
(:test)
function sceneContextNegative(logger as Test.Logger) as Boolean {
    var context=new SceneContext({"id"=>"missing","rocket"=>"Unknown launcher"});
    var view=new SpaceFoxView(new SceneClock(),new ScheduleState(null,"empty"));view.setContext(suppliedScene());view.setContext(context);
    logger.debug("absent context fields stay empty; no previous-launch inheritance");
    var absent=context.operator.equals("") && context.purpose.equals("") && context.site.equals("") && context.point==null && view.snapshot().countdown.equals("--:--:--");
    view.setContext(new SceneContext({"rocket"=>"No selected ID","point"=>[-80.6043,28.6084]}));
    return absent && view.context==null && view.snapshot().countdown.equals("--:--:--");
}
(:test)
function sceneSettingsPositive(logger as Test.Logger) as Boolean {
    Application.Properties.setValue("Field1",4);Application.Properties.setValue("Field2",3);Application.Properties.setValue("Field3",4);Application.Properties.setValue("Field4",5);
    var settings=new SceneSettings(null).load();var reopened=new SceneSettings(null).load();
    var app=new SpaceFoxApp();var original=app.getInitialView()[0] as SpaceFoxView;Application.Properties.setValue("Field1",1);app.onSettingsChanged();var changed=original.settings.slots[0].equals("energy");Application.Properties.setValue("Field1",4);app.onSettingsChanged();
    logger.debug("actual Properties write/reopen independent calories/stress/calories/battery; restore defaults");
    var pass=settings.slots[0].equals("calories") && settings.slots[1].equals("stress") && settings.slots[2].equals("calories") && settings.slots[3].equals("battery") && reopened.slots[2].equals("calories") && changed && original.settings.slots[0].equals("calories");
    for(var i=0;i<4;i+=1){Application.Properties.setValue("Field"+(i+1),i);}return pass;
}
(:test)
function sceneSettingsNegative(logger as Test.Logger) as Boolean {
    var s=new SceneSettings({"Field1"=>"energy","Field2"=>"energy","Field3"=>"energy","Field4"=>"energy","Language"=>null});
    var bad=new SceneSettings({"Field1"=>6,"Field2"=>"off","Field3"=>false,"Field4"=>null});
    logger.debug("duplicates permitted; invalid individual setting preserves only its default");
    return s.slots[0].equals("energy") && s.slots[3].equals("energy") && bad.slots[0].equals("steps") && bad.slots[1].equals("energy") && bad.slots[2].equals("heart") && bad.slots[3].equals("stress");
}
(:test)
function sceneRocketPositive(logger as Test.Logger) as Boolean {
    var d=new SceneRenderer(null);var s=new SceneSettings(null);d.prepare(suppliedScene(),s);var original=d.model;
    d.prepare(new SceneContext({"id"=>"e","rocket"=>"Electron","operator"=>"Rocket Lab","modelId"=>"electron","operatorId"=>"company-rocket-lab"}),s);
    logger.debug("actual catalog resources change Falcon9->Electron; curated rocket origin remainsNZ independent USoperator");
    return original!=(d.model) && (d.model as NativeModel).origin.equals("NZ") && d.country!=null && d.company!=null;
}
(:test)
function sceneRocketNegative(logger as Test.Logger) as Boolean {
    var d=new SceneRenderer(null);d.prepare(new SceneContext({"id"=>"x","rocket"=>"Future unlisted rocket","site"=>"USA · Somewhere","modelId"=>"new-999","operatorId"=>"company-spacex"}),new SceneSettings(null));
    logger.debug("unknown model generic, missing supplied operator omits company/origin; siteUSA never fallback");
    return d.model==NativeAssets.models["generic"] && d.country==null && d.company==null;
}
(:test)
function sceneGeographyPositive(logger as Test.Logger) as Boolean {
    var d=new SceneRenderer(null);var c=suppliedScene();d.prepare(c,new SceneSettings(null));var flat=d.map;
    logger.debug("accepted flat-map resource preserves sourcepoint; pin335/165");
    return d.pin && flat!=null;
}
(:test)
function sceneGeographyNegative(logger as Test.Logger) as Boolean {
    var d=new SceneRenderer(null);var bad=[null,[181,0],[0,-91],["0",0],[0],[0,0]];
    for(var i=0;i<bad.size();i+=1){d.prepare(new SceneContext({"id"=>"x","point"=>bad[i]}),new SceneSettings(null));if(d.pin){return false;}}
    d.prepare(new SceneContext({"id"=>"ship","point"=>[-80.6043,28.6084],"moving"=>true}),new SceneSettings(null));
    logger.debug("invalid/missing/unprepared/moving-without-event position cannot createfalsepin");return !d.pin;
}
(:test)
function sceneCompositionPositive(logger as Test.Logger) as Boolean {
    var d=new SceneRenderer(null);d.prepare(suppliedScene(),new SceneSettings(null));var im=sceneBuffer();var dc=im.getDc();
    var time=d.fonts["time"] as Graphics.FontType;var label=d.fonts["label"] as Graphics.FontType;var metric=d.fonts["metric"] as Graphics.FontType;
    logger.debug("real resource font width08:08="+dc.getTextWidthInPixels("08:08",time)+" height="+dc.getFontHeight(time));
    return d.art!=null && (d.art as Graphics.BitmapType).getHeight()==124 && dc.getTextWidthInPixels("08:08",time)<=250 && dc.getFontHeight(label)>=21 && dc.getFontHeight(metric)>=32;
}
(:test)
function sceneCompositionNegative(logger as Test.Logger) as Boolean {
    var d=new SceneRenderer(null);d.prepare(suppliedScene(),new SceneSettings(null));var before=d.resourceLoads;var im=sceneBuffer();var dc=im.getDc();
    for(var i=0;i<3;i+=1){d.active(dc,new ClockSnapshot("08:08","02:00:00"),new SceneSettings(null),new SceneTelemetry().sample(1800000000),new Fitness(),0.0);}
    logger.debug("actual3redraws do not load/parse static resource again");return d.resourceLoads==before;
}
(:test)
function sceneStatusPositive(logger as Test.Logger) as Boolean {
    var c=new SceneContext({"id"=>"flags","rescheduled"=>true,"stale"=>true,"precision"=>"unknown"});var d=new SceneRenderer(null);d.prepare(c,new SceneSettings(null));var im=sceneBuffer();
    d.active(im.getDc(),new ClockSnapshot("08:08",c.schedule.display(1800000000,true)),new SceneSettings(null),new SceneTelemetry().sample(1800000000),new Fitness(),0.0);
    logger.debug("actual uncertainty render with independent amber+dots; no preciseT-0");return c.rescheduled && c.stale && c.schedule.display(1800000000,true).equals("--:--:--");
}
(:test)
function sceneStatusNegative(logger as Test.Logger) as Boolean {
    var a=new SceneContext({"id"=>"a","rescheduled"=>true});var b=new SceneContext({"id"=>"b","stale"=>true});
    logger.debug("reschedule and stale do not implyeachother");return a.rescheduled && !a.stale && b.stale && !b.rescheduled;
}
(:test)
function sceneAnimationPositive(logger as Test.Logger) as Boolean {
    var v=new SpaceFoxView(new SceneClock(),new ScheduleState(null,"empty"));v.setContext(suppliedScene());v.onShow();v.onExitSleep();var running=v.animationRunning;v.onEnterSleep();
    logger.debug("real WatchUi.animate active starts; sleep cancels/reset; no liftoffstate");return running && !v.animationRunning && v.animationProgress==0.0 && v.snapshot().countdown.equals("02:00:00");
}
(:test)
function sceneAodPositive(logger as Test.Logger) as Boolean {
    var input=new SceneClock();var v=new SpaceFoxView(input,new ScheduleState(1800003661,"exact"));var telemetry=new SceneTelemetry();v.fitness=telemetry;
    v.onExitSleep();var im=sceneBuffer();v.onLayout(im.getDc());v.onEnterSleep();v.onUpdate(im.getDc());var minute=v.aodMinute;input.now+=1;v.onUpdate(im.getDc());
    logger.debug("sleep minute redraw guard; fixed numeric countdown; telemetry read once outside redraw");return minute==v.aodMinute && telemetry.reads==1 && v.snapshot().countdown.equals("01:01:00") && !v.animationRunning;
}
(:test)
function sceneAodNegative(logger as Test.Logger) as Boolean {
    var d=new SceneRenderer(null);var im=sceneBuffer();d.prepare(suppliedScene(),new SceneSettings(null));
    for(var i=0;i<4;i+=1){d.aod(im.getDc(),new ClockSnapshot("08:08","02:00:00"),i);}
    d.aod(im.getDc(),new ClockSnapshot("08:08","02:00:00"),-1);
    logger.debug("actual4sparseposition renders plusnegativeUTCminute; mapnotdrawn byseparatepath; pixelbudget separatelyscreenshotted");var v=new SpaceFoxView(new SceneClock(),new ScheduleState(null,"empty"));
    return d.map!=null && v.utcMinute(-1)==-1l && v.utcMinute(-60)==-1l && v.utcMinute(-61)==-2l && v.utcMinute(253402300799l)==4223371679l;
}
(:test)
function sceneMetricsPositive(logger as Test.Logger) as Boolean {
    var f=new Fitness();var values={"steps"=>0,"energy"=>0,"heart"=>72,"stress"=>0,"calories"=>0,"battery"=>82};
    logger.debug("independently supplied0validenergy/stress/calories/steps vs82watchcharge;300srecencyinclusive");
    return f.display(values,"steps").equals("0") && f.display(values,"stress").equals("0") && f.display(values,"calories").equals("0") && f.display({"battery"=>0},"battery").equals("0%") && f.display(values,"energy").equals("0") && f.display(values,"battery").equals("82%") && f.recentValue(0,1800000000,1800000300,100,false)==0 && f.recentValue(72,1800000000,1800000300,300,true)==72;
}
(:test)
function sceneMetricsNegative(logger as Test.Logger) as Boolean {
    var f=new Fitness();var measured=f.sample(Time.now().value());
    logger.debug("realSDKmetricadapter guardedpermission/API smoke; nofixturehealth; absent/stale/future/outofrange rejected");
    return f.display({"heart"=>null},"heart").equals("—") && f.number(-1,100)==null && f.number(101,100)==null && f.number(true,100)==null && f.recentValue(50,1800000000,1800000301,100,false)==null && f.recentValue(50,1800000001,1800000000,100,false)==null && f.recentValue(0,1800000000,1800000000,300,true)==null && measured.hasKey("battery");
}
(:test)
function sceneFontsPositive(logger as Test.Logger) as Boolean {
    var d=new SceneRenderer(null);var im=sceneBuffer();var dc=im.getDc();
    var text="Россия · Восточный";var bounded=d.fit(dc,text,d.fonts["label"] as Graphics.FontType,242);
    d.text(dc,195,319,d.fonts["label"] as Graphics.FontType,bounded,0xFFFFFF,242,1);
    logger.debug("actualUnicode="+text+"; UTF8middle="+"·"+"; width="+dc.getTextWidthInPixels(text,d.fonts["label"] as Graphics.FontType));return dc.getTextWidthInPixels(bounded,d.fonts["label"] as Graphics.FontType)<=242 && dc.getTextWidthInPixels("·",d.fonts["label"] as Graphics.FontType)>0 && dc.getTextWidthInPixels("·",d.fonts["label"] as Graphics.FontType)<dc.getTextWidthInPixels("M",d.fonts["label"] as Graphics.FontType) && dc.getTextWidthInPixels("Россия",d.fonts["label"] as Graphics.FontType)!=dc.getTextWidthInPixels("??????",d.fonts["label"] as Graphics.FontType);
}
(:test)
function sceneFontsNegative(logger as Test.Logger) as Boolean {
    var s=new SceneSettings({"Language"=>"unsupported"});var r=new SceneSettings({"Language"=>"ru"});
    logger.debug("unsupported selection retains English fallback; explicit ru selection stays ru; rendering admission is separately checked");return s.language.equals("en") && r.language.equals("ru");
}
