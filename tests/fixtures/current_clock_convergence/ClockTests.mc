import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.Time;

// Explicit input adapter: replaces only watch clock/time-zone input, never the
// countdown/view domain owner. It does not model FR165 physical sleep or DST.
(:test)
class ControlledClock extends WatchClock {
    var utc as Number;
    var local as String;
    var reads as Number = 0;
    function initialize(value as Number, text as String) {
        WatchClock.initialize();
        utc = value;
        local = text;
    }
    function utcSeconds() as Number { reads += 1; return utc; }
    function localTimeText() as String { return local; }
}

(:test)
function uncertaintyPositive(logger as Test.Logger) as Boolean {
    var date = new ScheduleState(1800007200, "date");
    var window = new ScheduleState(1800007200, "window");
    var unknown = new ScheduleState(null, "unknown");
    logger.debug("date/window ignore nominal midpoint; exact countdown remains null");
    return date.remainingSeconds(1800000000) == null && date.display(1800000000).equals("--:--:--") &&
        window.remainingSeconds(1800000000) == null && window.display(1800000000).equals("--:--:--") &&
        unknown.remainingSeconds(1800000000) == null && unknown.display(1800000000).equals("--:--:--");
}


(:test)
function uncertaintyNegative(logger as Test.Logger) as Boolean {
    var invalid = [null, 1800007200.5, "2027-01-15", "1800007200", true];
    for (var index = 0; index < invalid.size(); index += 1) {
        var value = invalid[index];
        var schedule = new ScheduleState(value, "exact");
        if (schedule.remainingSeconds(1800000000) != null ||
            !schedule.display(1800000000).equals("--:--:--")) { return false; }
    }
    logger.debug("null/fraction/date/string/boolean cannot create precision; signed integer UTC is present");
    var valid = [0, 0l, -1, -1000000000, -62135596800l];
    for (var index = 0; index < valid.size(); index += 1) {
        var schedule = new ScheduleState(valid[index], "exact");
        if (schedule.remainingSeconds(1800000000) == null ||
            (schedule.remainingSeconds(1800000000) as Number or Long) >= 0 ||
            schedule.display(1800000000).find("T+ ") != 0) { return false; }
    }
    return true;
}


(:test)
function offlineWakePositive(logger as Test.Logger) as Boolean {
    var input = new ControlledClock(1800000000, "08:00");
    var schedule = new ScheduleState(1800010800, "exact");
    var view = new SpaceFoxView(input, schedule);
    view.onExitSleep();
    var before = view.snapshot();
    var remainingBefore = schedule.remainingSeconds(input.utc);
    view.onEnterSleep();
    input.utc = 1800007200; // two hours with no redraw/tick/network call
    input.local = "10:00";
    view.onExitSleep();
    var after = view.snapshot();
    logger.debug("offline before="+before.countdown+" after="+after.countdown+" reads="+input.reads);
    return remainingBefore == 10800 && before.countdown.equals("T- 03:00:00") &&
        schedule.remainingSeconds(input.utc) == 3600 && after.countdown.equals("T- 01:00:00") && input.reads == 4;
}


(:test)
function offlineWakeNegative(logger as Test.Logger) as Boolean {
    var input = new ControlledClock(1800000000, "08:00");
    var view = new SpaceFoxView(input, new ScheduleState(1800007200, "exact"));
    view.onExitSleep();
    input.utc = 1800007300; // jump past target: elapsed time, no liftoff claim
    var elapsed = view.snapshot();
    input.utc = 1800007200; // exactly zero is still awaiting
    var zero = view.snapshot();
    input.utc = 1800003600; // backward clock correction: recompute, no latched zero
    var backwards = view.snapshot();
    logger.debug("forward/zero/backward: T+00:01:40,T+00:00:00,T- 01:00:00");
    return elapsed.countdown.equals("T+ 00:01:40") && zero.countdown.equals("T+ 00:00:00") &&
        backwards.countdown.equals("T- 01:00:00");
}


(:test)
function emptyStartup(logger as Test.Logger) as Boolean {
    var app = new SpaceFoxApp();
    var initial = app.getInitialView();
    var view = initial[0] as SpaceFoxView;
    logger.debug("real App initial view has no invented launch");
    return view.snapshot().countdown.equals("--:--:--");
}


(:test)
function clockAdapterSmoke(logger as Test.Logger) as Boolean {
    var before = Time.now().value();
    var clock = new WatchClock();
    var current = clock.utcSeconds();
    var after = Time.now().value();
    var nativeLocal = System.getClockTime();
    var expected = clock.formatLocal(nativeLocal.hour, nativeLocal.min);
    logger.debug("live SDK Time.now adapter observed=" + current);
    return current >= before && current <= after && clock.localTimeText().equals(expected);
}

