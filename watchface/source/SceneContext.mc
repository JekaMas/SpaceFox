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
    var operatorId as String;var siteId as String;
    var point as Array<Numeric> or Null;
    var rescheduled as Boolean = false;
    var stale as Boolean = false;
    var sourceHold as Boolean = false;
    var schedule as ScheduleState;
    var retentionDeadline as Long or Null = null;
    var retentionTarget as Long or Null = null;
    var sourceValidated as Long or Null = null;
    var freshnessTarget as Long or Null = null;
    var freshnessPolicy as Dictionary or Null = null;
    var displayTarget as Long or Null=null;
    var sourcePrecision as String = "";var pointText as Array or Null=null;var orderingUtc as Long or Null=null;
    function initialize(data as Dictionary<String, Object or Null>) {
        launchId = text(data, "id");
        if(data.hasKey("date")&&data["date"] instanceof String){date=data["date"] as String;}
        rocket = text(data, "rocket"); operator = text(data, "operator"); operatorShort = text(data, "operatorShort");
        purpose = text(data, "purpose"); site = text(data, "site");
        modelId = text(data, "modelId"); operatorId = text(data, "operatorId");siteId=text(data,"siteId");
        point = null;
        if (data.hasKey("point") && validPoint(data["point"]) &&
            (!flag(data,"moving") || flag(data,"eventPosition"))) {
            var supplied = data["point"] as Array<Numeric>;
            point = [supplied[0],supplied[1]];
        }
        rescheduled = flag(data,"rescheduled");
        stale = flag(data,"stale");
        sourceHold = flag(data,"sourceHold");
        var target = data.hasKey("target") ? data["target"] as Object or Null : null;
        var precision = text(data, "precision");
        schedule = new ScheduleState(target, precision);sourcePrecision=precision;
        var announced=data["displayTarget"];if(announced instanceof Number||announced instanceof Long){displayTarget=announced.toLong();}else if(precision.equals("minute")&&(target instanceof Number||target instanceof Long)){displayTarget=target.toLong();}
        if(data["pointText"] instanceof Array){pointText=data["pointText"] as Array;}
        var ordering=data["orderingUtc"];if(ordering instanceof Number||ordering instanceof Long){orderingUtc=ordering.toLong();}
        var deadline=data["retentionDeadline"];
        if(deadline instanceof Number || deadline instanceof Long){retentionDeadline=deadline.toLong();}
        var checked=data["sourceValidated"];if(checked instanceof Number || checked instanceof Long){sourceValidated=checked.toLong();}
        if((precision.equals("exact")||precision.equals("minute")) && (target instanceof Number||target instanceof Long)){freshnessTarget=target.toLong();retentionTarget=target.toLong();}
        if(data["freshnessPolicy"] instanceof Dictionary){freshnessPolicy=data["freshnessPolicy"] as Dictionary;}
    }
    (:typecheck(false)) function cacheRow(){
        var row={"id"=>launchId,"rocket"=>rocket,"operator"=>operator,"operatorShort"=>operatorShort,"purpose"=>purpose,"site"=>site,"modelId"=>modelId,"operatorId"=>operatorId,"siteId"=>siteId,"pointText"=>pointText,"target"=>retentionTarget,"precision"=>sourcePrecision,"date"=>date,"retentionDeadline"=>retentionDeadline,"orderingUtc"=>orderingUtc,"sourceValidated"=>sourceValidated,"freshnessPolicy"=>freshnessPolicy,"rescheduled"=>rescheduled,"stale"=>stale,"sourceHold"=>sourceHold};if(displayTarget!=null){row["displayTarget"]=displayTarget;}return row;
    }
    // Same source-age rule as accepted feed, applied to whichever launch is
    // displayed after local selection. It performs arithmetic only.
    (:typecheck(false)) function advanceFreshness(now) as Void {
        if(sourceValidated==null||freshnessPolicy==null){return;}var age=now.toLong()-sourceValidated;if(age<0){age=0;}
        var p=freshnessPolicy;var cycles=p["stale_cycles"];var fast=p["fast_interval_seconds"];
        if(fast!=null){stale=stale||age/fast>=cycles;return;}
        stale=stale||age/p["normal_interval_seconds"]>=cycles;var t=freshnessTarget;
        if(t!=null){var end=now<t+1800?now:t+1800;stale=stale||end>=t-7200&&end>=sourceValidated&&(end-sourceValidated)/p["near_interval_seconds"]>=cycles;}
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
