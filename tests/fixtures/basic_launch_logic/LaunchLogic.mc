import Toybox.Lang;
import Toybox.Test;

(:test, :typecheck(false))
class LaunchLogicCatalog {
    function read(key) {
        return key.equals("sf.obj.09d14343e538fc1e6abcbdd1add8f5a2883e77a9d99169218f91f53a569d891b") ? LaunchLogicPackets.catalog() : null;
    }
}

(:test)
class LaunchLogicClock extends WatchClock {
    var now as Number;
    function initialize(utc as Number) { WatchClock.initialize(); now = utc; }
    function utcSeconds() as Number { return now; }
    function localTimeText() as String { return "13:25"; }
}

(:typecheck(false))
function launchLogicReading(raw, utc) {
    var packet = new NativeBridgeFeed(raw, utc, new LaunchLogicCatalog());
    var timing = packet.document["launch"]["timing"];
    // Preserve the admitted source facts before View compacts its working packet.
    var facts = [timing["precision"], timing["exact_utc"], timing["nominal_utc"],
                 timing["source_precision_id"], packet.wireHash];
    var view = new SpaceFoxView(new LaunchLogicClock(utc), new ScheduleState(null, "unknown"));
    view.setPacket(packet);
    return [view.snapshot(), facts, view.context.rocket, view.context.operator];
}

(:test, :typecheck(false))
function basicLaunchFeedTiming(logger as Test.Logger) as Boolean {
    var exact = launchLogicReading(LaunchLogicPackets.exact(), 1794576343);
    var zero = launchLogicReading(LaunchLogicPackets.exact(), 1794583543);
    var minute = launchLogicReading(LaunchLogicPackets.minute(), 1794576343);
    var absent = launchLogicReading(LaunchLogicPackets.unknown(), 1794576343);
    logger.debug("current schema3 NativeBridgeFeed->FeedScene->View: SEC=" + exact[0].countdown +
                 "; MIN=" + minute[0].countdown + "; zero=" + zero[0].countdown + "; unknown=" + absent[0].countdown);
    logger.debug("source facts p=" + exact[1][0] + " id=" + exact[1][3] + " rawSHA=" + exact[1][4] + " rocket=" + exact[2]);
    Test.assert(exact[0].remaining == 7200);
    Test.assert(exact[0].countdown.equals("02:00:00"));
    Test.assert(exact[1][0].equals("exact"));
    Test.assert(exact[1][1] == 1794583543);
    Test.assert(exact[1][2] == 1794583543);
    Test.assert(exact[1][3] == 0);
    Test.assert(exact[1][4].equals(LaunchLogicPackets.exactSha()));
    Test.assert(exact[2].equals("Vulcan VC6L"));
    Test.assert(exact[3].equals("United Launch Alliance"));
    Test.assert(zero[0].remaining == 0);
    Test.assert(zero[0].countdown.equals("00:00:00"));
    Test.assert(minute[0].remaining == 16097);
    Test.assert(minute[0].countdown.equals("04:28:17"));
    Test.assert(minute[1][0].equals("source-coarse"));
    Test.assert(minute[1][1] == null);
    Test.assert(minute[1][2] == 1794592440);
    Test.assert(minute[1][3] == 1);
    Test.assert(minute[1][4].equals(LaunchLogicPackets.minuteSha()));
    Test.assert(absent[0].remaining == null);
    Test.assert(absent[0].countdown.equals("--:--:--"));
    Test.assert(absent[1][0].equals("unknown"));
    Test.assert(absent[1][1] == null);
    Test.assert(absent[1][2] == null);
    Test.assert(absent[1][4].equals(LaunchLogicPackets.unknownSha()));
    return true;
}
