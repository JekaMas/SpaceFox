import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;
(:test,:typecheck(false)) class ControlledExactClock extends WatchClock { var utc; function initialize(v){WatchClock.initialize();utc=v;} function utcSeconds(){return utc;} function localTimeText(){return "08:08";} }
(:typecheck(false)) class ExactPacketStore {var data;function initialize(d){data=d;}function read(key){return key.equals("sf.obj."+data["catalogDigest"])?data["catalog"]:null;}}
(:test,:typecheck(false)) function currentExactPacketView(logger){
 var d=WatchUi.loadResource(Rez.JsonData.TimingCatalog);var exact=WatchUi.loadResource(Rez.JsonData.TimingExact)["raw"];var minute=WatchUi.loadResource(Rez.JsonData.TimingMinute)["raw"];var unknown=WatchUi.loadResource(Rez.JsonData.TimingUnknown)["raw"];
 var clock=new ControlledExactClock(1794576343);var view=new SpaceFoxView(clock,new ScheduleState(null,"unknown"));
 logger.debug("EXACT before constructor");
 var p=new NativeBridgeFeed(exact,1794576343,new ExactPacketStore(d));
 var precision=p.document["launch"]["timing"]["precision"];
 logger.debug("EXACT before setPacket");
 view.setPacket(p);
 logger.debug("EXACT before snapshot");
 Test.assertEqual(view.snapshot().countdown,"T- 02:00:00");
 Test.assertEqual(precision,"exact");
 p=new NativeBridgeFeed(minute,1794576343,new ExactPacketStore(d));precision=p.document["launch"]["timing"]["precision"];var absent=p.document["launch"]["timing"]["exact_utc"]==null;view.setPacket(p);Test.assertEqual(view.snapshot().countdown,"T- 04:28:17");Test.assertEqual(precision,"source-coarse");Test.assert(absent);
 p=new NativeBridgeFeed(unknown,1794576343,new ExactPacketStore(d));view.setPacket(p);Test.assertEqual(view.snapshot().countdown,"--:--:--");
 logger.debug("EXACT_PACKET_VIEW SEC=02:00:00 MIN=04:28:17 unknown=--:--:--");return true;}
