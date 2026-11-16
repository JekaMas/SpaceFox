import Toybox.Lang;
import Toybox.Time;

(:typecheck(false)) class BoundaryFitness {
    // Null means the unfiltered adapter, used by direct API diagnostics.
    var selectedRoles as Array<String> or Null = null;
    var currentBodyBattery as Number or Null = null;
    var selectedFields as SelectedFields or Null = null;
    function initialize() {}
    function requested(role as String) as Boolean {return selectedRoles==null || (selectedRoles as Array<String>).indexOf(role)>=0;}
    // Only finite nonnegative real Garmin data, no fixtures/default health.
    function number(value as Object or Null, maximum as Number or Null) as Number or Null {
        if (!(value instanceof Number || value instanceof Float || value instanceof Double || value instanceof Long)) { return null; }
        if (!(value >= 0) || !(value <= 2147483647) || (maximum != null && !(value <= maximum))) { return null; }
        return value.toNumber();
    }
    function recentValue(value as Object or Null, when as Number or Long or Null, now as Number or Long, maximum as Number or Null, heart as Boolean) as Number or Null {
        if (when == null) { return null; }
        var age = now.toLong() - when.toLong();
        if (age < 0 || age > 300) { return null; }
        var accepted = number(value, maximum);
        if (heart && accepted == 0) { return null; }
        return accepted;
    }
    function recent(sample as MetricSample or Null, now as Number or Long, maximum as Number, heart as Boolean) as Number or Null {
        if(sample==null || sample.when==null){return null;}
        return recentValue(sample.data,sample.when.value(),now,maximum,heart);
    }
    function sample(now as Number or Long) as Dictionary<String, Number or Null> {
        var values = {"steps"=>null,"calories"=>null,"battery"=>null,"heart"=>null,"energy"=>null,"stress"=>null};
        try {
            if ((requested("steps") || requested("calories")) && AvailableFeatures has :ActivityMonitor && MetricSDK.activity has :getInfo) {
                var info = MetricSDK.activity.getInfo();
                if (info != null) {
                    if (info has :steps) { values["steps"] = number(info.steps, null); }
                    if (info has :calories) { values["calories"] = number(info.calories, null); }
                }
            }
        } catch (e) {}
        try { if(requested("battery")){values["battery"] = number(MetricSDK.system.getSystemStats().battery, 100);} } catch (e) {}
        if(requested("energy")){values["energy"]=currentBodyBattery;}
        // One latest sample per selected history source. No entire-history traversal,
        // raw Sensor streaming or health upload. Permission/API failures are null.
        if (AvailableFeatures has :SensorHistory) {
            var options = {:period=>1, :order=>MetricSDK.history.ORDER_NEWEST_FIRST};
            try { if (requested("heart") && MetricSDK.history has :getHeartRateHistory) { values["heart"] = recent(MetricSDK.history.getHeartRateHistory(options).next(), now, 300, true); } } catch (e) {}
            try { if (requested("stress") && MetricSDK.history has :getStressHistory) { values["stress"] = recent(MetricSDK.history.getStressHistory(options).next(), now, 100, false); } } catch (e) {}
        }
        return values;
    }
    (:typecheck(false)) function fieldIcon(role as String) {return selectedFields==null?null:(selectedFields as SelectedFields).icon(role);}
    function fieldLabel(role as String) as String {return selectedFields==null?"":(selectedFields as SelectedFields).label(role);}
    function display(values as Dictionary<String, Number or Null>, role as String) as String {
        if(role.find("custom")==0 && selectedFields!=null){return (selectedFields as SelectedFields).display(role);}
        var value = values[role];
        if (value == null) { return "—"; }
        var text = value.toString();
        return role.equals("battery") ? text + "%" : text;
    }
}
