import Toybox.Lang;

// Consumes validated exact-second or nominal-minute UTC from the accepted feed.
// Minute targets retain their source precision; their nominal UTC is used for arithmetic.
class ScheduleState {
    private var _exactUtc as Long or Null;

    function initialize(exactUtc as Object or Null, precision as String) {
        _exactUtc = null;
        // Validated Unix UTC includes epoch zero and pre-1970 timestamps. Null
        // denotes absence; sign does not. Promote before arithmetic so accepted
        // integer UTC differences cannot wrap at the signed Number boundary.
        if ((precision.equals("exact") || precision.equals("minute")) &&
            (exactUtc instanceof Number || exactUtc instanceof Long)) {
            _exactUtc = exactUtc.toLong();
        }
    }

    function remainingSeconds(nowUtc as Number or Long) as Number or Long or Null {
        if (_exactUtc == null) { return null; }
        var remaining = _exactUtc - nowUtc.toLong();
        return remaining;
    }

    function display(nowUtc as Number or Long) as String {
        return CountdownFormat.format(remainingSeconds(nowUtc));
    }
}

module CountdownFormat {
    // LOW is a minute snapshot of the same signed UTC delta. Round a future
    // target up so zero is never shown before the target; elapsed time rounds
    // down. Zero itself belongs to T+.
    function minutes(seconds as Number or Long or Null) as String {
        if (seconds == null) { return "--:--"; }
        var n=seconds.toLong();var future=n>0;
        var total=future?(n+59)/60:(-n)/60;
        return (future?"T- ":"T+ ")+(total/60).toNumber().format("%02d")+":"+(total%60).toNumber().format("%02d");
    }
    function format(seconds as Number or Long or Null) as String {
        if (seconds == null) { return "--:--:--"; }
        var n = seconds.toLong();
        var elapsed = n <= 0;
        if (n < 0) { n = -n; }
        var hours = (n / 3600).toNumber();
        var minutes = ((n % 3600) / 60).toNumber();
        var remaining = (n % 60).toNumber();
        return (elapsed ? "T+ " : "T- ") + hours.format("%02d") + ":" + minutes.format("%02d") + ":" + remaining.format("%02d");
    }
}
