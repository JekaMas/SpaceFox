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
 function read(key){if(data.hasKey(key)){return data[key];}/* ASSET_BRANCHES */return null;}
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
// A watch-app must return a View. Forward its test-only callbacks to the
// exact production SpaceFoxView drawing/layout owner; lifecycle and power are
// deliberately outside this geometry observer's claim.
(:typecheck(false)) class D04ReadyWrapper extends WatchUi.View {
 var inner;
 function initialize(view){View.initialize();inner=view;}
 function onLayout(dc){inner.onLayout(dc);}
 function onUpdate(dc){inner.onUpdate(dc);}
 function onHide(){inner.onHide();}
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
  System.println("D04_READY_ACCEPTED realFeed=true");return [new D04ReadyWrapper(view)];
 }
}
