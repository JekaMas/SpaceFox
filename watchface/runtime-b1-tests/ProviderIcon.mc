import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

(:test,:typecheck(false)) class B1IconDc {
    var images=0;var markers=0;var color=null;var fail=false;
    function drawBitmap2(x,y,bitmap,options){if(fail){throw new Toybox.Lang.InvalidValueException("icon unavailable");}images+=1;}
    function setColor(foreground,background){color=foreground;}
    function drawCircle(x,y,r){markers+=1;}
}
(:test,:typecheck(false)) function b1ProviderIconBudget(logger){
    var fields=new SelectedFields();
    fields.text["custom1"]="72 bpm";
    var known=WatchUi.loadResource(Rez.Drawables.Metric_steps);
    var safe=fields.safeProviderIcon(known);
    Test.assert(safe instanceof Array&&safe[0]==known);
    var oversized=WatchUi.loadResource(Rez.Drawables.MapView0);
    Test.assert(fields.safeProviderIcon(oversized)==false);
    Test.assert(fields.safeProviderIcon("not a bitmap reference")==false);
    Test.assert(fields.display("custom1").equals("72 bpm"));
    fields.icons["custom1"]=safe;Test.assert(fields.icon("custom1")==safe);
    fields.icons["custom1"]=false;Test.assert(fields.icon("custom1")==false);
    Test.assert(fields.icon("custom2")==null);
    var renderer=new SceneRenderer(new LocalePresentation());var dc=new B1IconDc();
    renderer.drawProviderIcon(dc,safe,55,244,0x123456,"custom1");Test.assert(dc.images==1&&dc.markers==0);
    renderer.drawProviderIcon(dc,false,55,244,0x123456,"custom1");Test.assert(dc.markers==1&&dc.color==0x123456);
    renderer.drawProviderIcon(dc,null,55,244,0x123456,"custom1");Test.assert(dc.markers==2);
    dc.fail=true;renderer.drawProviderIcon(dc,safe,55,244,0x123456,"custom1");Test.assert(dc.markers==3);
    Test.assert(fields.display("custom1").equals("72 bpm"));
    logger.debug("B1_ICON known=true oversized_fallback=true unsupported_fallback=true value_preserved=true");
    return true;
}
