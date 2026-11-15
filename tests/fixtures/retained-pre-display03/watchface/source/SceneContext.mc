import Toybox.Lang;

// One accepted selected-launch object is replaced atomically. Real startup has
// none. This is an injection/cache seam, not a claimed live feed implementation.
(:extendedCode)
class SceneContext {
    var date as String or Null=null;
    var launchId as String;
    var rocket as String;
    var operator as String;
    var operatorShort as String;
    var purpose as String;
    var site as String;
    var modelId as String;
    var operatorId as String;
    var point as Array<Numeric> or Null;
    var rescheduled as Boolean = false;
    var stale as Boolean = false;
    var schedule as ScheduleState;
    function initialize(data as Dictionary<String, Object or Null>) {
        launchId = text(data, "id");
        if(data.hasKey("date")&&data["date"] instanceof String){date=data["date"] as String;}
        rocket = text(data, "rocket"); operator = text(data, "operator"); operatorShort = text(data, "operatorShort");
        purpose = text(data, "purpose"); site = text(data, "site");
        modelId = text(data, "modelId"); operatorId = text(data, "operatorId");
        point = null;
        if (data.hasKey("point") && validPoint(data["point"]) &&
            (!flag(data,"moving") || flag(data,"eventPosition"))) {
            var supplied = data["point"] as Array<Numeric>;
            point = [supplied[0],supplied[1]];
        }
        rescheduled = flag(data,"rescheduled");
        stale = flag(data,"stale");
        var target = data.hasKey("target") ? data["target"] as Object or Null : null;
        var precision = text(data, "precision");
        schedule = new ScheduleState(target, precision);
    }
    function flag(data as Dictionary<String, Object or Null>, key as String) as Boolean {
        var value=data[key]; return value instanceof Boolean && value;
    }
    function text(data as Dictionary<String, Object or Null>, key as String) as String {
        if (data.hasKey(key) && data[key] instanceof String) { return data[key] as String; }
        return "";
    }
    function validPoint(p as Object or Null) as Boolean {
        if (!(p instanceof Array) || p.size() != 2) { return false; }
        for (var i = 0; i < 2; i += 1) {
            if (!(p[i] instanceof Number || p[i] instanceof Float || p[i] instanceof Double || p[i] instanceof Long)) { return false; }
        }
        var coordinates = p as Array<Numeric>;
        return coordinates[0] >= -180 && coordinates[0] <= 180 && coordinates[1] >= -90 && coordinates[1] <= 90;
    }
}
