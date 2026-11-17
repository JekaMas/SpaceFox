import Toybox.Lang;
import Toybox.Application;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Timer;
(:typecheck(false)) class PeerFrameClock extends WatchClock {
 function utcSeconds(){return 1795041600;}
 function localTimeText(){return "09:10";}
 function localCalendar(){return [3,17,11];}
}
(:typecheck(false)) class PeerFrameStore extends NativeStore {
 var data={};function read(key){return data[key];}function write(key,value){data[key]=value;}function remove(key){data.remove(key);}
}
(:typecheck(false)) class PeerMapApp extends SpaceFoxApp {
 var consumed=0;
 function getInitialView(){
  feed=new NativeCache("https://jekamas.github.io/SpaceFox",new PeerFrameStore());
  view=new PeerMapView(self);view.pendingLoader=method(:consume);view.pendingVolatileCheck=method(:hasPendingVolatile);
  view.setContext(new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]).presentation);
  return [view];
 }
 function consume(){if(!hasPendingVolatile()){return;}consumed+=1;NativeForegroundApp.flushVolatile(self,feed);System.println("PEER_CONSUMED count="+consumed+" pending="+(feed.pendingVolatile!=null));}
}
(:typecheck(false)) class PeerMapView extends SpaceFoxView {
 var owner;var phase=0;var painted=-1;var timer;var lowPaints=0;
 function initialize(app){SpaceFoxView.initialize(new PeerFrameClock(),new ScheduleState(null,"empty"));owner=app;}
 function onShow(){SpaceFoxView.onShow();if(timer==null){timer=new Timer.Timer();timer.start(method(:step),1500,true);}}
 function step(){
  phase+=1;
  if(phase==1){var second=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];second[3][0]="ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a";var before=renderer.resourceLoads;setContext(new NativeTrustedPacket(second).presentation);System.println("PEER_SAME_SITE identity="+mapDecision.identity+" loads_before="+before+" loads_after="+renderer.resourceLoads);}
  else if(phase==2){onEnterSleep();}
  else if(phase==3){var before=lastLowFrameMinute();onHide();var next=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];next[1]["generation"]=57;next[1]["selectionValidatedUtc"]=1794812998l;next[3][0]="ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a";next[3][20]=1795042260l;owner.onBackgroundData({"base"=>"https://jekamas.github.io/SpaceFox","volatileSnapshot"=>next});onShow();System.println("PEER_RESHOW prior_minute="+before+" invalidated="+(lastLowFrameMinute()==null)+" pending="+owner.hasPendingVolatile());}
  else if(phase==4){timer.stop();System.println("PEER_REPEAT consumed="+owner.consumed+" low_paints="+lowPaints+" minute="+lastLowFrameMinute());}
  WatchUi.requestUpdate();
 }
 function drawPendingLow(dc){lowPaints+=1;SpaceFoxView.drawPendingLow(dc);}
 function onUpdate(dc){
  updateForDisplayMode(dc,phase<2?System.DISPLAY_MODE_HIGH_POWER:System.DISPLAY_MODE_LOW_POWER);
  if(painted!=phase){painted=phase;System.println("PEER_FRAME phase="+phase+" native="+NativeVersion.ID+" identity="+mapDecision.identity+" point="+mapDecision.point+" xy="+mapDecision.x+","+mapDecision.y+" target="+context.displayTarget+" low_minute="+lastLowFrameMinute()+" consumed="+owner.consumed+" low_paints="+lowPaints);}
 }
}
