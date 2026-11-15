import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

(:test,:typecheck(false)) function display04ActualFontTrace(logger){
 var bitmap=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();var dc=bitmap.getDc();
 for(var language=0;language<2;language+=1){
  var settings=new SceneSettings({"Language"=>language});var drawing=new SceneRenderer(null);drawing.prepare(null,settings);
  var p=drawing.presentation;var label=drawing.fonts["label"];var small=drawing.fonts["small"];var count=drawing.fonts["count"];
  var time=drawing.fonts["time"];var metric=drawing.fonts["metric"];var aod=drawing.fonts["aod"];
  logger.debug("D04_FONT|"+language+"|locale="+p.locale+"|face="+p.dictionary["face"]+"|labelVector="+(label instanceof Graphics.VectorFont)+"|smallVector="+(small instanceof Graphics.VectorFont)+"|countVector="+(count instanceof Graphics.VectorFont)+"|timeHeight="+dc.getFontHeight(time)+"|metricHeight="+dc.getFontHeight(metric)+"|aodHeight="+dc.getFontHeight(aod));
  Test.assert(p.dictionary["face"].equals("RobotoRegular")&&label instanceof Graphics.VectorFont&&small instanceof Graphics.VectorFont&&count instanceof Graphics.VectorFont);
  Test.assert(time==WatchUi.loadResource(Rez.Fonts.Time80)&&metric==WatchUi.loadResource(Rez.Fonts.Metric32)&&aod==WatchUi.loadResource(Rez.Fonts.Aod40));
 }
 return true;
}
