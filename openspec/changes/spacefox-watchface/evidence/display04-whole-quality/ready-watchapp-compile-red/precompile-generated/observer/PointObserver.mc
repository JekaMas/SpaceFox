import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Timer;
import Toybox.WatchUi;

// Captured content-addressed assets use a test-only in-memory resource store.
// The actual NativeCache/NativeSfrBuild/NativeSfrDecoder and renderer perform
// selection, validation, decompression, color and geometry operations.
(:typecheck(false)) class D04ReadyStore {
 var data={};
 function read(key){if(data.hasKey(key)){return data[key];}if(key.equals("sf.obj.07924fc156dcfcd1725e9dce51567b9d04b13933fe56f89a0255b3ffcc914580")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject0)["raw"];}if(key.equals("sf.obj.0936caabf3d961df403c05a1a35a5436d5842c45de0077cfd7053118a6e7ca29")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject1)["raw"];}if(key.equals("sf.obj.0f6ced072b08fe37b64b1944b2c3e01aead22000bd18ef580f4c60b4728070e4")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject2)["raw"];}if(key.equals("sf.obj.180d4d090c41fddf2fd1d79dd46405bbf9d13569ec151440658ec50208b5eb5b")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject3)["raw"];}if(key.equals("sf.obj.1ffdf397e79433e07fc263e684dec7a38d94a80e99a3bef3922c539ca7d5f3bc")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject4)["raw"];}if(key.equals("sf.obj.2a09c8ea59ca32d5ee8ea4e5520682de56a7539b86e434b804f96ffeca0cecd6")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject5)["raw"];}if(key.equals("sf.obj.4d28962616ea3056f6ce6fde40f6904f9d9dee2e657f67f988b4eaa4d31e8e92")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject6)["raw"];}if(key.equals("sf.obj.584769813730b377510b2c44367330495adf09cc035a4a337512a6d26cb5944a")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject7)["raw"];}if(key.equals("sf.obj.653939e2711ce529f39617eb84040f245960720925e27e70d270247940553e3a")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject8)["raw"];}if(key.equals("sf.obj.671a4b8da3f5c272f41a709b7b72285ee96247eed72d4b3c521bc13884bb6153")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject9)["raw"];}if(key.equals("sf.obj.697b580f41521ace59315e84264ddbfb4dee9d77b50f3d2e256ad10b7a6a56cf")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject10)["raw"];}if(key.equals("sf.obj.6d4ab3dc509e305150b3e44adc2df9d6c70416ec01f09751f1a66c2418cc18e9")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject11)["raw"];}if(key.equals("sf.obj.9107867a46a828266cdc4669352d110734f23c385ef52bc1ca7073709bb415ee")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject12)["raw"];}if(key.equals("sf.obj.a28ecf80077c51aa47efd45080f6c965500ac437d53cc042b34b3a5b8f42c7ce")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject13)["raw"];}if(key.equals("sf.obj.db31d9ab634adaa54e03c7c96a2eee50064466b0565444a8bda1145a520ac301")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject14)["raw"];}if(key.equals("sf.obj.ddef3be6db53150c8c9b4b1712c758cde77d2a2137a981cfcf5a3876aa014d0c")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject15)["raw"];}if(key.equals("sf.obj.eeaefa0a3910f493ba1409eca38c0473fa68b6b99da810696788b8338b01fddd")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject16)["raw"];}if(key.equals("sf.obj.f8a14e2df0245b475990b21c3cb102d219adb7d8b4e8fbf520437c5ec62a7b7f")){return WatchUi.loadResource(Rez.JsonData.D04ReadyObject17)["raw"];}return null;}
 function write(key,value){data[key]=value;}
 function remove(key){data.remove(key);}
}
(:typecheck(false)) class D04ReadyClock extends WatchClock {
 function utcSeconds(){return 1794576343;}
 function localTimeText(){return "08:38";}
 function localCalendar(){return [1,15,11];}
}
(:typecheck(false)) class D04ReadyFitness extends Fitness {
 function sample(now){return {"steps"=>12345,"energy"=>null,"heart"=>null,"stress"=>null,"calories"=>2345,"battery"=>82};}
}
(:typecheck(false)) class D04ReadyBody extends BodyBatterySource {
 function start(callback){return false;}function read(){value=null;observed=true;return null;}function stop(){value=null;observed=false;subscribed=false;}
}
(:typecheck(false)) class D04ReadyView extends SpaceFoxView {
 var adapter;var job=null;var pump=null;var ready=false;var lastMask="";
 function initialize(store){SpaceFoxView.initialize(new D04ReadyClock(),new ScheduleState(null,"empty"));adapter=store;}
 function onShow(){}
 function onLayout(dc){SpaceFoxView.onLayout(dc);pump=new Timer.Timer();pump.start(method(:buildStep),25,true);}
 function buildStep(){
  try{
   if(job==null){System.println("D04_READY_BUILD_START");job=new NativeSfrBuild(adapter,"https://fixture.invalid/display04-ready",packet);}
   if(job.step()){
    downloaded=job.result;renderer.downloaded=downloaded;
    System.println("D04_READY_BUILD_DONE selection="+downloaded.selectionHash+" map="+(downloaded.mapBitmap!=null)+" rocket="+(downloaded.bitmap!=null)+" flag="+(downloaded.siteCountryBitmap!=null)+" position="+(downloaded.scene!=null&&downloaded.scene["position"]!=null));
    job=null;pump.stop();ready=true;pump.start(method(:redraw),1000,true);WatchUi.requestUpdate();
   }
  }catch(e){System.println("D04_READY_BUILD_ERROR "+e);if(pump!=null){pump.stop();pump=null;}throw e;}
 }
 function redraw(){WatchUi.requestUpdate();}
 function onUpdate(dc){
  if(!ready){dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();return;}
  stopAnimation();animationProgress=0;MaskObserver.sample();var selection=MaskObserver.selected()+(MaskObserver.white()?"/white":"/black");
  if(!selection.equals(lastMask)){System.println("D04_READY_MASK "+selection);lastMask=selection;}
  SpaceFoxView.onUpdate(dc);MaskObserver.barcode(dc);
 }
 function onHide(){if(pump!=null){pump.stop();pump=null;}job=null;SpaceFoxView.onHide();}
}
(:background,:typecheck(false)) class Display04PointApp extends Application.AppBase {
 function initialize(){AppBase.initialize();}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){
  var store=new D04ReadyStore();var catalog=WatchUi.loadResource(Rez.JsonData.D04Catalog);store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
  var cache=new NativeCache("https://fixture.invalid/display04-ready",store);var raw=WatchUi.loadResource(Rez.JsonData.D04Feed)["raw"];
  if(!cache.accept(raw,1794576343)){throw new Lang.InvalidValueException("real READY feed rejected");}
  var view=new D04ReadyView(store);view.fitness=new D04ReadyFitness();view.bodyBattery=new D04ReadyBody();view.setSettings(new SceneSettings({"Language"=>0}));view.setPacket(cache.packet);
  // Simulated Storage is external to the application heap on watch. Drop its
  // test-only feed/catalog copies; content-addressed assets stay readable.
  store.data={};
  view.values={"steps"=>12345,"calories"=>2345,"battery"=>82,"energy"=>null,"heart"=>null,"stress"=>null};
  System.println("D04_READY_ACCEPTED realFeed=true");return [view];
 }
}
