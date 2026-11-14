import Toybox.Background;
import Toybox.System;
import Toybox.Time;
(:background, :typecheck(false)) class IncidentObserve extends SpaceFoxApp {
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;NativeMetrics.ownerTag="incident-observer";}
 function getServiceDelegate(){NativeMetrics.enabled=true;NativeMetrics.ownerTag="incident-observer-bg";return [new FeedService()];}
 (:typecheck(disableBackgroundCheck)) function reloadFeed(){SpaceFoxApp.reloadFeed();audit();}
 (:typecheck(disableBackgroundCheck)) function onBackgroundData(d){SpaceFoxApp.onBackgroundData(d);audit();}
 function audit(){var n=Time.now().value();var r=Background.getTemporalEventRegisteredTime();var l=Background.getLastTemporalEventTime();System.println("INCIDENT_SCHEDULE now="+n+" registered="+(r==null?"null":r.value())+" last="+(l==null?"null":l.value()));}
}
