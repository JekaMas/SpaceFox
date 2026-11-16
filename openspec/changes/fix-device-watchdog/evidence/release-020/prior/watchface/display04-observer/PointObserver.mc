import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;

// A captured real feed/catalog is admitted through the actual cache parser.
// Memory storage and fixed metrics are test-only. No network, user health or
// source coordinate is fabricated; the observer never writes app storage.
(:typecheck(false)) class PointStore {
 var data={};var reads=0;var writes=0;
 function read(k){reads+=1;return data.hasKey(k)?data[k]:null;}
 function write(k,v){writes+=1;data[k]=v;}
 function remove(k){writes+=1;data.remove(k);}
}
(:typecheck(false)) class PointClock extends WatchClock {
 function utcSeconds(){return 1794551202+(System.getTimer()/1000);}
 function localTimeText(){return "08:38";}
 function localCalendar(){return [1,15,11];}
}
(:typecheck(false)) class PointFitness extends Fitness {
 function sample(now){return {"steps"=>12345,"energy"=>null,"heart"=>null,"stress"=>null,"calories"=>2345,"battery"=>82};}
}
(:typecheck(false)) class PointBody extends BodyBatterySource {
 function start(callback){return false;}function read(){value=null;observed=true;return null;}function stop(){value=null;observed=false;subscribed=false;}
}
(:typecheck(false)) class PointView extends SpaceFoxView {
 var announced=false;
 function initialize(c,s){SpaceFoxView.initialize(c,s);}
 function onUpdate(dc){
  SpaceFoxView.onUpdate(dc);
  if(!announced && System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER && renderer!=null){
   System.println("DISPLAY04_POINT pending=true capturedFeed=true point="+(context!=null&&context.point!=null)+" bundledPin="+renderer.pin+" clock=08:38");announced=true;
  }
 }
}
(:background,:typecheck(false)) class Display04PointApp extends Application.AppBase {
 function initialize(){AppBase.initialize();}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){
  System.println("DISPLAY04_STAGE initial");var store=new PointStore();var catalog=WatchUi.loadResource(Rez.JsonData.D04Catalog);store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
  var cache=new NativeCache("https://fixture.invalid/display04-point",store);var raw=WatchUi.loadResource(Rez.JsonData.D04Feed)["raw"];
  System.println("DISPLAY04_STAGE before_accept");if(!cache.accept(raw,1794551202)){throw new Lang.InvalidValueException("captured feed rejected");}
  System.println("DISPLAY04_STAGE accepted");var v=new PointView(new PointClock(),new ScheduleState(null,"empty"));v.fitness=new PointFitness();v.bodyBattery=new PointBody();
  v.setSettings(new SceneSettings({"Language"=>0}));v.setPacket(cache.packet);v.values={"steps"=>12345,"calories"=>2345,"battery"=>82,"energy"=>null,"heart"=>null,"stress"=>null};
  System.println("DISPLAY04_STAGE ready_view");return [v];
 }
}
