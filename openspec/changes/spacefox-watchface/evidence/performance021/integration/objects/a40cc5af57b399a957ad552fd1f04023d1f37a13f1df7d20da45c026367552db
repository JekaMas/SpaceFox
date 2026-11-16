import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;

// The generated store exposes only the original content-addressed inputs.
(:test,:typecheck(false)) class D04ReadyAssetStore {
 var data={};
 function read(key){if(data.hasKey(key)){return data[key];}/* ASSET_BRANCHES */return null;}
 function write(key,value){data[key]=value;}
 function remove(key){data.remove(key);}
}
(:test,:typecheck(false)) class D04ReadyAssetDrawing extends SceneRenderer {
 var logger;var lang;var ids;var refs;
 function initialize(log,language){logger=log;lang=language;ids=[];refs=[];SceneRenderer.initialize(null);}
 function load(id){var value=SceneRenderer.load(id);ids.add(id);refs.add(value);return value;}
 function identity(value){for(var i=0;i<refs.size();i+=1){if(refs[i]==value){return ids[i];}}return null;}
 function text(dc,x,y,font,value,color,width,contour){
  var shown=fit(dc,value,font,width);var tag="other";
  if(font==fonts["time"]){tag="time";}else if(font==fonts["metric"]){tag="metric";}
  else if(font==fonts["label"]){tag="label";}else if(font==fonts["nameSmall"]){tag="nameSmall";}
  else if(font==fonts["small"]){tag="small";}else if(font==fonts["count"]){tag="count";}
  else if(font==presentation.calendarFont){tag="calendar";}
  logger.debug("D04_READY_TRACE_TEXT|"+lang+"|"+x+"|"+y+"|"+tag+"|"+dc.getTextWidthInPixels(shown,font)+"|"+dc.getFontHeight(font)+"|"+color+"|"+width+"|"+contour+"|"+shown);
  return SceneRenderer.text(dc,x,y,font,value,color,width,contour);
 }
 function icon(dc,x,y,role){if(icons.hasKey(role)){var bmp=icons[role];logger.debug("D04_READY_TRACE_ICON|"+lang+"|"+role+"|"+x+"|"+y+"|"+bmp.getWidth()+"|"+bmp.getHeight());}SceneRenderer.icon(dc,x,y,role);}
}
(:typecheck(false)) function dcFont(dc,font){return dc.getFontHeight(font);}
(:test,:typecheck(false)) function display04RealReadyLowTrace(logger){
 var priorResource=null;var priorX=null;var priorY=null;var priorCount=null;
 for(var language=0;language<2;language+=1){
  var store=new D04ReadyAssetStore();var catalog=WatchUi.loadResource(Rez.JsonData.D04Catalog);store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
  var cache=new NativeCache("https://fixture.invalid/display04-ready",store);var raw=WatchUi.loadResource(Rez.JsonData.D04Feed)["raw"];
  Test.assert(cache.accept(raw,1794576343));var context=feedScene(cache.packet,1794576343);Test.assert(context!=null&&context.point!=null);
  store.data={};var build=new NativeSfrBuild(store,"https://fixture.invalid/display04-ready",cache.packet);var steps=0;
  while(!build.step()){steps+=1;Test.assert(steps<5000);}
  var visual=build.result;Test.assert(visual!=null&&visual.bitmap!=null&&visual.mapBitmap!=null&&visual.siteCountryBitmap!=null&&visual.scene["position"]!=null);
  logger.debug("D04_READY_ASSETS|"+language+"|selection="+visual.selectionHash+"|map="+visual.mapBitmap.getWidth()+"x"+visual.mapBitmap.getHeight()+"|rocket="+visual.bitmap.getWidth()+"x"+visual.bitmap.getHeight()+"|flag="+visual.siteCountryBitmap.getWidth()+"x"+visual.siteCountryBitmap.getHeight()+"|phase=0|position=true");
  var settings=new SceneSettings({"Language"=>language});var draw=new D04ReadyAssetDrawing(logger,language);draw.prepare(context,settings);draw.downloaded=visual;
  var current=new ClockSnapshot("08:38",CountdownFormat.format(context.schedule.remainingSeconds(1794576343)));current.lowCountdown=CountdownFormat.minutes(context.schedule.remainingSeconds(1794576343));current.localCalendar=[1,15,11];current.battery="82%";current.rescheduled=context.rescheduled;current.sourceHold=context.sourceHold;current.stale=context.stale;
  var canvas=Graphics.createBufferedBitmap({:width=>390,:height=>390,:colorDepth=>16}).get();draw.prepareAod();
  var bundled=draw.aodMap!=null&&draw.aodPin;Test.assert(bundled&&draw.identity(draw.aodMap)!=null);
  var chosen=draw.identity(draw.aodMap);var minute=1794576343/60;current.countdown=current.lowCountdown;
  if(priorResource!=null){Test.assert(chosen==priorResource&&draw.aodPinX==priorX&&draw.aodPinY==priorY&&current.countdown.equals(priorCount));}
  priorResource=chosen;priorX=draw.aodPinX;priorY=draw.aodPinY;priorCount=current.countdown;
  logger.debug("D04_READY_LOW|"+language+"|selection="+visual.selectionHash+"|bundled="+bundled+"|mapResource="+chosen+"|mapSize="+draw.aodMap.getWidth()+"x"+draw.aodMap.getHeight()+"|point="+draw.aodPinX+","+draw.aodPinY+"|minutePhase="+(minute%4)+"|clock="+current.localTime+"|count="+current.countdown+"|date="+draw.presentation.calendar(current.localCalendar)+"|aodFont="+dcFont(canvas.getDc(),draw.fonts["aod"])+"|contextFont="+dcFont(canvas.getDc(),draw.presentation.aodContextFont));
  // Record actual native font metrics at the exact LOW primitive arguments.
  // The source-bound host oracle checks clip ownership and 454 scaling.
  var dc=canvas.getDc();var date=draw.presentation.calendar(current.localCalendar);var count=draw.presentation.fit(dc,current.countdown,draw.presentation.aodContextFont,300);
  var dateWidth=dc.getTextWidthInPixels(date,draw.presentation.aodContextFont);var countWidth=dc.getTextWidthInPixels(count,draw.presentation.aodContextFont);var clockWidth=dc.getTextWidthInPixels(current.localTime,draw.fonts["aod"]);var batteryWidth=dc.getTextWidthInPixels(current.battery,draw.presentation.aodBatteryFont);
  var contextHeight=dc.getFontHeight(draw.presentation.aodContextFont);var clockHeight=dc.getFontHeight(draw.fonts["aod"]);var batteryHeight=dc.getFontHeight(draw.presentation.aodBatteryFont);
  var p=(minute%4)==0?[-1,-1]:(minute%4)==1?[1,-1]:(minute%4)==2?[-1,1]:[1,1];
  Test.assert(dateWidth>0&&dateWidth<350&&countWidth>0&&countWidth<=300&&clockWidth>0&&clockWidth<350&&batteryWidth>0&&batteryWidth<350);
  Test.assert(89+p[1]>=0&&89+p[1]+contextHeight<=390&&121+clockHeight<=390&&246+p[1]+contextHeight<=390&&295+p[1]+batteryHeight<=390);
  logger.debug("D04_LOW_BOUNDS|"+language+"|viewport="+dc.getWidth()+"x"+dc.getHeight()+"|phase="+(minute%4)+"|date="+dateWidth+","+contextHeight+"|clock="+clockWidth+","+clockHeight+"|count="+countWidth+","+contextHeight+"|battery="+batteryWidth+","+batteryHeight+"|point="+draw.aodPinX+","+draw.aodPinY);
  draw.aod(canvas.getDc(),current,minute,settings);
 }
 return true;
}
