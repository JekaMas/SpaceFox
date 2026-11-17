import Toybox.Lang;
import Toybox.WatchUi;
class PeerFrameView extends SpaceFoxView {
 function initialize(){SpaceFoxView.initialize(new WatchClock(),new ScheduleState(null,"empty"));}
 function prepareRenderer() as Void {throw new Lang.InvalidValueException("injected optional renderer failure");}
}
(:background) class PeerFrameApp extends SpaceFoxApp {
 (:typecheck(false)) function getInitialView(){
  var base="https://jekamas.github.io/SpaceFox";var owner=new NativeTrustedStore(null,base);owner.save(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]);
  view=new PeerFrameView();view.bootstrapPending=true;view.pendingLoader=method(:reloadFeed);
  Toybox.System.println("PEER_ACTIVE_FALLBACK id="+NativeVersion.ID+" fixture=Coarse renderer=injected_failure");return [view];
 }
}
