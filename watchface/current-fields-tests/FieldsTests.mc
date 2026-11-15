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
    var footerWidth as Number=0;var footerHeight as Number=0;var footerShown as String="";
    var logger as Test.Logger;
    function initialize(log as Test.Logger){SceneRenderer.initialize(null);logger=log;}
    function text(dc as Graphics.Dc,x as Numeric,y as Numeric,font as Graphics.FontType,value as String,color as Number,width as Number,contour as Number) as String {
        var shown=SceneRenderer.text(dc,x,y,font,value,color,width,contour);
        var kind=font==fonts["time"]?"time":font==fonts["metric"]?"metric":"vector";
        if(y==319){footerShown=shown;footerWidth=dc.getTextWidthInPixels(shown,font);footerHeight=dc.getFontHeight(font);}
        logger.debug("BASIC_TEXT|"+kind+"|"+x+"|"+y+"|"+dc.getTextWidthInPixels(shown,font)+"|"+dc.getFontHeight(font)+"|"+shown);
        rows+=1;return shown;
    }
}
(:typecheck(false)) function footerInsideCircle(width,height){
    var half=width/2.0+1;var top=319-1-195;var bottom=319+height+1-195;
    return half*half+top*top<=195*195&&half*half+bottom*bottom<=195*195;
}
(:test,:typecheck(false)) function currentFooterCircleBound(logger){
    // The second literal is the widest composed site in the retained finite
    // real corpus under the SDK's installed Roboto Regular 26px font.
    var sites=["US · Cape Canaveral SFS, FL, USA","KP · Sohae Satellite Launching Station, Cholsan County, North Pyongan Province, Democratic People's Republic of Korea"];
    var image=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();var dc=image.getDc();
    for(var language=0;language<2;language+=1){for(var i=0;i<sites.size();i+=1){
        var d=new BasicDrawing(logger);var settings=new SceneSettings({"Language"=>language});var c=new SceneContext({"id"=>"fixture","site"=>sites[i]});d.prepare(c,settings);
        d.active(dc,new ClockSnapshot("08:38","T- 01:00:00"),settings,{},new Fitness(),0.0);
        Test.assert(!d.footerShown.equals("")&&footerInsideCircle(d.footerWidth,d.footerHeight));
        logger.debug("FOOTER_CIRCLE language="+language+" case="+i+" width="+d.footerWidth+" height="+d.footerHeight+" shown="+d.footerShown);
    }}
    // The independently calculated first 1px overflow must not pass the oracle.
    var w=0;while(footerInsideCircle(w+1,22)){w+=1;}Test.assert(footerInsideCircle(w,22)&&!footerInsideCircle(w+1,22));return true;
}
// Native font/bitmap arguments are captured before each production text/icon
// draw. The conservative box includes the requested outline and one extra
// pixel for native rounding/scaling. Background and rocket/marker draws need
// their separately recorded bounds; this test claims only text and field icons.
(:typecheck(false)) function preclipBoxInside(x0,y0,x1,y1){
    return x0>=0&&y0>=0&&x1<=390&&y1<=390&&x0<x1&&y0<y1;
}
(:test,:typecheck(false)) class BoundsDrawing extends SceneRenderer {
    var ok=true;var textCount=0;var iconCount=0;var logger;
    function initialize(log){SceneRenderer.initialize(null);logger=log;}
    function text(dc,x,y,font,value,color,width,contour){
        var shown=fit(dc,value,font,width);
        if(!shown.equals("")){
            var w=dc.getTextWidthInPixels(shown,font);var h=dc.getFontHeight(font);var pad=contour+1;
            var inside=preclipBoxInside(x-w/2.0-pad,y-pad,x+w/2.0+pad,y+h+pad);
            logger.debug("PRECLIP_TEXT|"+x+"|"+y+"|"+w+"|"+h+"|"+pad+"|"+inside);ok=ok&&inside;textCount+=1;
        }
        return SceneRenderer.text(dc,x,y,font,value,color,width,contour);
    }
    function icon(dc,x,y,role){
        if(icons.hasKey(role)){var bmp=icons[role] as Graphics.BitmapType;var inside=preclipBoxInside(x-1,y-1,x+bmp.getWidth()+1,y+bmp.getHeight()+1);logger.debug("PRECLIP_ICON|"+role+"|"+x+"|"+y+"|"+bmp.getWidth()+"|"+bmp.getHeight()+"|"+inside);ok=ok&&inside;iconCount+=1;}
        SceneRenderer.icon(dc,x,y,role);
    }
}
(:test,:typecheck(false)) function currentPreclipTextIcons(logger){
    var bitmap=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();var dc=bitmap.getDc();
    var sites=["US · Cape Canaveral SFS, FL, USA","KP · Sohae Satellite Launching Station, Cholsan County, North Pyongan Province, Democratic People's Republic of Korea"];
    for(var language=0;language<2;language+=1){for(var k=0;k<sites.size();k+=1){
        var draw=new BoundsDrawing(logger);var settings=new SceneSettings({"Language"=>language});
        var context=new SceneContext({"id"=>"fixture","rocket"=>"Vulcan","operator"=>"United Launch Alliance","purpose"=>"Communications","site"=>sites[k]});
        draw.prepare(context,settings);var now=new ClockSnapshot("08:38","T- 49:02:03");now.localCalendar=[7,14,11];
        draw.active(dc,now,settings,{"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"battery"=>82},new Fitness(),0.0);
        Test.assert(draw.ok&&draw.textCount>=9&&draw.iconCount==4);
    }}
    Test.assert(preclipBoxInside(194,0,196,1)&&!preclipBoxInside(194,-1,196,1));return true;
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
    var f=new Fitness();var actual=f.sample(Time.now().value());var v=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"unknown"));var input=new BasicTelemetry();v.fitness=input;v.onShow();var dc=(Graphics.createBufferedBitmap({:width=>390,:height=>390}).get() as Graphics.BufferedBitmap).getDc();v.onLayout(dc);v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);v.resumeAfterFrame();v.stopAnimation();
    var s=v.snapshot();logger.debug("real Garmin adapter API smoke separately; controlled missing sample exercises actual view/formatter");
    v.onHide();return actual.hasKey("steps")&&actual.hasKey("energy")&&actual.hasKey("heart")&&actual.hasKey("stress")&&actual.hasKey("calories")&&actual.hasKey("battery")&&input.samples==1&&f.display(v.values,"energy").equals("—")&&f.display(v.values,"heart").equals("—")&&f.display(v.values,"stress").equals("—")&&f.display(v.values,"calories").equals("—")&&f.display(v.values,"steps").equals("12345")&&s.localTime.length()==5&&s.countdown.equals("--:--:--");
}
(:test)
function basicUnavailableNegative(logger as Test.Logger) as Boolean {
    var f=new Fitness();var v=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"unknown"));v.values={"heart"=>72,"energy"=>68};v.fitness=new BasicTelemetry();v.onShow();var dc=(Graphics.createBufferedBitmap({:width=>390,:height=>390}).get() as Graphics.BufferedBitmap).getDc();v.onLayout(dc);v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);v.resumeAfterFrame();v.stopAnimation();
    logger.debug("new missing sample replaces former72/68; age300 accepted,301 or future unavailable; real zero allowed only for applicable metrics");
    v.onHide();return f.display(v.values,"heart").equals("—")&&f.display(v.values,"energy").equals("—")&&f.recentValue(68,1800000000,1800000300,100,false)==68&&f.recentValue(68,1800000000,1800000301,100,false)==null&&f.recentValue(68,1800000001,1800000000,100,false)==null&&f.recentValue(0,1800000000,1800000000,300,true)==null&&f.display({"steps"=>0},"steps").equals("0");
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
