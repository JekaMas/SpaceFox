import Toybox.Lang;
import Toybox.Test;

(:test, :typecheck(false))
class RescheduleCatalog {
    function read(key){
        return key.equals("sf.obj.5a2e753c268be3a02728a78733c8d3d22f44058c6b9076d1e43acb86c8ca23ad")?ReschedulePackets.catalog():null;
    }
}
(:test)
class RescheduleClock extends WatchClock {
    function initialize(){WatchClock.initialize();}
    function utcSeconds() as Number {return 1794551202;}
    function localTimeText() as String {return "10:26";}
}
(:typecheck(false))
function rescheduleView(packet){
    var v=new SpaceFoxView(new RescheduleClock(),new ScheduleState(null,"unknown"));
    v.setPacket(packet);return v;
}
(:test, :typecheck(false))
function rescheduleMove(logger as Test.Logger) as Boolean {
    var first=new NativeBridgeFeed(ReschedulePackets.initial(),1794551202,new RescheduleCatalog());
    var before=rescheduleView(first).snapshot();
    var moved=new NativeBridgeFeed(ReschedulePackets.moved(),1794551202,new RescheduleCatalog());
    moved.metadata(first,1794551202);
    var v=rescheduleView(moved);var after=v.snapshot();
    logger.debug("actual producer MIN/null-exact envelope: 16:18:18 -> 16:38:18; reschedule latched");
    return before.remaining==58698&&after.remaining==59898&&after.remaining-before.remaining==1200&&
        before.countdown.equals("16:18:18")&&after.countdown.equals("16:38:18")&&
        moved.rescheduled&&v.context.rescheduled&&moved.document["launch"]["timing"]["exact_utc"]==null;
}
(:test, :typecheck(false))
function rescheduleRefresh(logger as Test.Logger) as Boolean {
    var first=new NativeBridgeFeed(ReschedulePackets.initial(),1794551202,new RescheduleCatalog());
    var unchanged=new NativeBridgeFeed(ReschedulePackets.unchanged(),1794551202,new RescheduleCatalog());unchanged.metadata(first,1794551202);
    var moved=new NativeBridgeFeed(ReschedulePackets.moved(),1794551202,new RescheduleCatalog());moved.metadata(first,1794551202);
    var refreshed=new NativeBridgeFeed(ReschedulePackets.refresh(),1794551202,new RescheduleCatalog());refreshed.metadata(moved,1794551202);
    var v=rescheduleView(refreshed);
    logger.debug("successful unchanged validations neither create nor clear current launch latch");
    return !unchanged.rescheduled&&moved.rescheduled&&refreshed.rescheduled&&v.context.rescheduled&&
        v.snapshot().remaining==59898&&v.snapshot().countdown.equals("16:38:18");
}
(:test, :typecheck(false))
function rescheduleWithdraw(logger as Test.Logger) as Boolean {
    var moved=new NativeBridgeFeed(ReschedulePackets.moved(),1794551202,new RescheduleCatalog());
    var withdrawn=new NativeBridgeFeed(ReschedulePackets.withdrawn(),1794551202,new RescheduleCatalog());withdrawn.metadata(moved,1794551202);
    var v=rescheduleView(withdrawn);var s=v.snapshot();
    logger.debug("withdrawn current target: --:--:--, no prior nominal target, reschedule still set");
    return withdrawn.rescheduled&&v.context.rescheduled&&s.remaining==null&&s.countdown.equals("--:--:--")&&
        withdrawn.document["launch"]["timing"]["nominal_utc"]==null;
}
(:test, :typecheck(false))
function rescheduleDifferent(logger as Test.Logger) as Boolean {
    var withdrawn=new NativeBridgeFeed(ReschedulePackets.withdrawn(),1794551202,new RescheduleCatalog());
    var refresh=new NativeBridgeFeed(ReschedulePackets.withdrawn_refresh(),1794551202,new RescheduleCatalog());refresh.metadata(withdrawn,1794551202);
    var oldView=rescheduleView(refresh);var old=oldView.snapshot();
    var different=new NativeBridgeFeed(ReschedulePackets.different(),1794551202,new RescheduleCatalog());different.metadata(refresh,1794551202);
    var v=rescheduleView(different);
    logger.debug("withdrawn unchanged refresh stays unknown/latched; next identity never inherits old flag");
    return refresh.rescheduled&&old.countdown.equals("--:--:--")&&old.remaining==null&&
        !different.launchId().equals(refresh.launchId())&&!different.rescheduled&&!v.context.rescheduled&&
        v.snapshot().remaining==58698&&v.snapshot().countdown.equals("16:18:18");
}
