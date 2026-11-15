import Toybox.Lang;
import Toybox.System;
import Toybox.Time;

// UTC arithmetic and local watch presentation have separate sources. Do not apply
// a time-zone offset to Time.now(), which is already an absolute UTC moment.
class WatchClock {
    function initialize() {}

    function utcSeconds() as Number {
        return Time.now().value();
    }

    function localTimeText() as String {
        var clock = System.getClockTime();
        return formatLocal(clock.hour, clock.min);
    }

    function formatLocal(hour as Number, minute as Number) as String {
        return hour.format("%02d") + ":" + minute.format("%02d");
    }
}
