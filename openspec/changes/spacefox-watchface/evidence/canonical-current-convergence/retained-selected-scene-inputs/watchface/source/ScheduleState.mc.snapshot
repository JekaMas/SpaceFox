import Toybox.Lang;

// Consumes validated exact-second or nominal-minute UTC from the accepted feed.
// Minute targets retain their source precision; their nominal UTC is used for arithmetic.
class ScheduleState {
    private var _exactUtc as Long or Null;
    private var _precision as String;

    function initialize(exactUtc as Object or Null, precision as String) {
        _precision = precision;
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
        return remaining > 0 ? remaining : 0;
    }

    function display(nowUtc as Number or Long, active as Boolean) as String {
        return CountdownFormat.format(remainingSeconds(nowUtc));
    }
}

module CountdownFormat {
    function format(seconds as Number or Long or Null) as String {
        if (seconds == null) { return "--:--:--"; }
        var n = seconds.toLong();
        if (n < 0) { n = 0; }
        var hours = (n / 3600).toNumber();
        var minutes = ((n % 3600) / 60).toNumber();
        var remaining = (n % 60).toNumber();
        return hours.format("%02d") + ":" + minutes.format("%02d") + ":" + remaining.format("%02d");
    }
}
