import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;
(:test,:typecheck(false)) class RecoveryClock extends WatchClock {
    var now=1794551202;
    function initialize(){WatchClock.initialize();}
    function utcSeconds(){return now;}
    function localTimeText(){return "08:08";}
}
(:test,:typecheck(false)) function currentLowRecovery(logger){
    var clock=new RecoveryClock();var store=new NativeStore();var cat=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);store.write("sf.obj."+cat["catalogDigest"],cat["catalog"]);
    var cache=new TestNativeCache("https://recovery.invalid",store);var initial=WatchUi.loadResource(Rez.JsonData.DisplayInitial)["raw"];var moved=WatchUi.loadResource(Rez.JsonData.DisplayMoved)["raw"];var stale=WatchUi.loadResource(Rez.JsonData.DisplayStale)["raw"];
    Test.assert(cache.accept(initial,clock.now));Test.assert(cache.accept(moved,clock.now));var prior=store.read("sf.commit");var seal=prior["seal"];var writes=store.writes;
    var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.setPacket(cache.packet);var frame=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();view.onLayout(frame.getDc());view.updateForDisplayMode(frame.getDc(),System.DISPLAY_MODE_LOW_POWER);var minute=view.lastLowFrameMinute();
    Test.assert(!cache.accept(initial.substring(0,100),clock.now));Test.assert(!cache.accept(stale,clock.now));Test.assertEqual(store.writes,writes);Test.assertEqual(store.read("sf.commit")["seal"],seal);
    clock.now+=1;view.updateForDisplayMode(frame.getDc(),System.DISPLAY_MODE_LOW_POWER);Test.assertEqual(view.lastLowFrameMinute(),minute);Test.assert(!view.animationRunning);
    var reopened=new TestNativeCache("https://recovery.invalid",store);Test.assert(reopened.load(clock.now)!=null);Test.assertEqual(store.read("sf.commit")["seal"],seal);view.setPacket(reopened.packet);view.onShow();view.updateForDisplayMode(frame.getDc(),System.DISPLAY_MODE_HIGH_POWER);
    Test.assertEqual(view.snapshot().countdown,"T- 16:38:17");view.onHide();logger.debug("LOW_RECOVERY actualStore=true malformedRejected=true laterGenerationOlderSourceRejected=true sealStable=true minuteGuard=true highReopen=true countdown=T- 16:38:17");return true;
}
