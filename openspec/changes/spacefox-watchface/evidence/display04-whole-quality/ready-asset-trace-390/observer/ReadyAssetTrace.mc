import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;

// The generated store exposes only the original content-addressed inputs.
(:test,:typecheck(false)) class D04ReadyAssetStore {
 var data={};
 function read(key){if(data.hasKey(key)){return data[key];}if(key.equals("sf.obj.07924fc156dcfcd1725e9dce51567b9d04b13933fe56f89a0255b3ffcc914580")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject0)["raw"];}if(key.equals("sf.obj.0936caabf3d961df403c05a1a35a5436d5842c45de0077cfd7053118a6e7ca29")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject1)["raw"];}if(key.equals("sf.obj.0f6ced072b08fe37b64b1944b2c3e01aead22000bd18ef580f4c60b4728070e4")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject2)["raw"];}if(key.equals("sf.obj.180d4d090c41fddf2fd1d79dd46405bbf9d13569ec151440658ec50208b5eb5b")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject3)["raw"];}if(key.equals("sf.obj.1ffdf397e79433e07fc263e684dec7a38d94a80e99a3bef3922c539ca7d5f3bc")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject4)["raw"];}if(key.equals("sf.obj.2a09c8ea59ca32d5ee8ea4e5520682de56a7539b86e434b804f96ffeca0cecd6")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject5)["raw"];}if(key.equals("sf.obj.4d28962616ea3056f6ce6fde40f6904f9d9dee2e657f67f988b4eaa4d31e8e92")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject6)["raw"];}if(key.equals("sf.obj.584769813730b377510b2c44367330495adf09cc035a4a337512a6d26cb5944a")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject7)["raw"];}if(key.equals("sf.obj.653939e2711ce529f39617eb84040f245960720925e27e70d270247940553e3a")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject8)["raw"];}if(key.equals("sf.obj.671a4b8da3f5c272f41a709b7b72285ee96247eed72d4b3c521bc13884bb6153")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject9)["raw"];}if(key.equals("sf.obj.697b580f41521ace59315e84264ddbfb4dee9d77b50f3d2e256ad10b7a6a56cf")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject10)["raw"];}if(key.equals("sf.obj.6d4ab3dc509e305150b3e44adc2df9d6c70416ec01f09751f1a66c2418cc18e9")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject11)["raw"];}if(key.equals("sf.obj.9107867a46a828266cdc4669352d110734f23c385ef52bc1ca7073709bb415ee")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject12)["raw"];}if(key.equals("sf.obj.a28ecf80077c51aa47efd45080f6c965500ac437d53cc042b34b3a5b8f42c7ce")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject13)["raw"];}if(key.equals("sf.obj.db31d9ab634adaa54e03c7c96a2eee50064466b0565444a8bda1145a520ac301")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject14)["raw"];}if(key.equals("sf.obj.ddef3be6db53150c8c9b4b1712c758cde77d2a2137a981cfcf5a3876aa014d0c")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject15)["raw"];}if(key.equals("sf.obj.eeaefa0a3910f493ba1409eca38c0473fa68b6b99da810696788b8338b01fddd")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject16)["raw"];}if(key.equals("sf.obj.f8a14e2df0245b475990b21c3cb102d219adb7d8b4e8fbf520437c5ec62a7b7f")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject17)["raw"];}return null;}
 function write(key,value){data[key]=value;}
 function remove(key){data.remove(key);}
}
(:test,:typecheck(false)) class D04ReadyAssetDrawing extends SceneRenderer {
 var logger;var lang;
 function initialize(log,language){logger=log;lang=language;SceneRenderer.initialize(null);}
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
(:test,:typecheck(false)) function display04RealReadyAssetTrace(logger){
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
  var canvas=Graphics.createBufferedBitmap({:width=>390,:height=>390,:colorDepth=>16}).get();draw.active(canvas.getDc(),current,settings,{"steps"=>12345,"calories"=>2345,"battery"=>82,"energy"=>null,"heart"=>null,"stress"=>null},new Fitness(),0.0);
 }
 return true;
}
