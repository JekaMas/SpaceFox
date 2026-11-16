import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;

// Technical fixture only: the accepted launch and source point remain the
// captured refresh-cache fixture. No watch health or provider call is used.
(:test,:typecheck(false)) class D04TraceStore {
 var data={};
 function read(k){return data.hasKey(k)?data[k]:null;}
 function write(k,v){data[k]=v;}
 function remove(k){data.remove(k);}
}
(:test,:typecheck(false)) class D04TraceDrawing extends SceneRenderer {
 var log;var currentLanguage;
 function initialize(logger,language){SceneRenderer.initialize(null);log=logger;currentLanguage=language;}
 function text(dc,x,y,font,value,color,width,contour){
  var shown=fit(dc,value,font,width);var tag="other";
  if(font==fonts["time"]){tag="time";}else if(font==fonts["metric"]){tag="metric";}
  else if(font==fonts["label"]){tag="label";}else if(font==fonts["nameSmall"]){tag="nameSmall";}
  else if(font==fonts["small"]){tag="small";}else if(font==fonts["count"]){tag="count";}
  else if(font==presentation.calendarFont){tag="calendar";}
  log.debug("D04_TRACE_TEXT|"+currentLanguage+"|"+x+"|"+y+"|"+tag+"|"+dc.getTextWidthInPixels(shown,font)+"|"+dc.getFontHeight(font)+"|"+color+"|"+width+"|"+contour+"|"+shown);
  return SceneRenderer.text(dc,x,y,font,value,color,width,contour);
 }
 function icon(dc,x,y,role){
  if(icons.hasKey(role)){var bmp=icons[role];log.debug("D04_TRACE_ICON|"+currentLanguage+"|"+role+"|"+x+"|"+y+"|"+bmp.getWidth()+"|"+bmp.getHeight());}
  SceneRenderer.icon(dc,x,y,role);
 }
}
(:test,:typecheck(false)) function display04PendingOperationTextTrace(logger){
 var store=new D04TraceStore();var catalog=WatchUi.loadResource(Rez.JsonData.D04Catalog);store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
 var cache=new NativeCache("https://fixture.invalid/display04-point",store);var raw=WatchUi.loadResource(Rez.JsonData.D04Feed)["raw"];
 Test.assert(cache.accept(raw,1794551202));var context=feedScene(cache.packet,1794551202);Test.assert(context!=null&&context.point!=null);
 var image=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();var dc=image.getDc();
 for(var language=0;language<2;language+=1){
  var settings=new SceneSettings({"Language"=>language});var draw=new D04TraceDrawing(logger,language);draw.prepare(context,settings);
  var current=new ClockSnapshot("08:38",CountdownFormat.format(context.schedule.remainingSeconds(1794551202)));current.lowCountdown=CountdownFormat.minutes(context.schedule.remainingSeconds(1794551202));current.localCalendar=[1,15,11];current.battery="82%";
  current.rescheduled=context.rescheduled;current.sourceHold=context.sourceHold;current.stale=context.stale;
  draw.active(dc,current,settings,{"steps"=>12345,"calories"=>2345,"battery"=>82,"energy"=>null,"heart"=>null,"stress"=>null},new Fitness(),0.0);
 }
 return true;
}
