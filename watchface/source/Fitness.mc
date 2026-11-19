import Toybox.ActivityMonitor;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;

// One bounded, source-independent policy for Garmin history samples.
module HealthSample {
    function recentValue(value as Object or Null, when as Number or Long or Null, now as Number or Long, maximum as Number, heart as Boolean) as Number or Null {
        if(when==null||!(value instanceof Number||value instanceof Float||value instanceof Double||value instanceof Long)){return null;}
        var age=now.toLong()-when.toLong();
        if(age<0||age>300||!(value>=0)||!(value<=maximum)||(heart&&value==0)){return null;}
        return value.toNumber();
    }
}

class Fitness {
    // Null means the unfiltered adapter, used by direct API diagnostics.
    var selectedRoles as Array<String> or Null = null;
    var selectedFields as SelectedFields or Null = null;
    var status as Dictionary = {};var reason as Dictionary = {};
    function initialize() {}
    function activityAvailable() as Boolean {return Toybox has :ActivityMonitor && ActivityMonitor has :getInfo;}
    (:typecheck(false)) function activityInfo(){return ActivityMonitor.getInfo();}
    (:typecheck(false)) function batteryValue(){return System.getSystemStats().battery;}
    function requested(role as String) as Boolean {return selectedRoles==null || (selectedRoles as Array<String>).indexOf(role)>=0;}
    // Only finite nonnegative real Garmin data, no fixtures/default health.
    function number(value as Object or Null, maximum as Number or Null) as Number or Null {
        if (!(value instanceof Number || value instanceof Float || value instanceof Double || value instanceof Long)) { return null; }
        if (!(value >= 0) || !(value <= 2147483647) || (maximum != null && !(value <= maximum))) { return null; }
        return value.toNumber();
    }
    // READY means a real Garmin value, WAITING means the provider returned
    // no usable current sample, and UNAVAILABLE records a missing API/error.
    (:typecheck(false)) function sample(now as Number or Long) as Dictionary<String, Number or Null> {
        var values={"steps"=>null,"calories"=>null,"battery"=>null,"heart"=>null,"energy"=>null,"stress"=>null};
        status={};reason={};var roles=["steps","calories","battery","heart","energy","stress"];
        for(var i=0;i<roles.size();i+=1){if(requested(roles[i])){status[roles[i]]="WAITING";reason[roles[i]]="no-sample";}}
        if(requested("steps")||requested("calories")){
            try{if(activityAvailable()){var info=activityInfo();if(info!=null){if(info has :steps){values["steps"]=number(info.steps,null);}if(info has :calories){values["calories"]=number(info.calories,null);}}}
                else{status["steps"]="UNAVAILABLE";status["calories"]="UNAVAILABLE";reason["steps"]="unsupported";reason["calories"]="unsupported";}}
            catch(e){status["steps"]="UNAVAILABLE";status["calories"]="UNAVAILABLE";reason["steps"]="provider-error";reason["calories"]="provider-error";}
        }
        if(requested("battery")){try{values["battery"]=number(batteryValue(),100);}catch(e){status["battery"]="UNAVAILABLE";reason["battery"]="provider-error";}}
        if(selectedFields!=null){var source=selectedFields as SelectedFields;var health=["energy","heart","stress"];
            for(var i=0;i<health.size();i+=1){var role=health[i];if(requested(role)){values[role]=source.healthValue(role);status[role]=source.healthState(role);reason[role]=source.healthReason(role);}}}
        for(var i=0;i<roles.size();i+=1){var role=roles[i];if(requested(role)&&values[role]!=null){status[role]="READY";reason[role]=selectedFields!=null&&(role.equals("energy")||role.equals("heart")||role.equals("stress"))?(selectedFields as SelectedFields).healthReason(role):"available";}}
        return values;
    }
    function fieldReason(role as String) as String {if(role.find("custom")==0&&selectedFields!=null){return (selectedFields as SelectedFields).reason(role) as String;}return reason.hasKey(role)?reason[role] as String:"no-sample";}
    function fieldState(role as String) as String {if(role.find("custom")==0&&selectedFields!=null){return (selectedFields as SelectedFields).state(role) as String;}return status.hasKey(role)?status[role] as String:"WAITING";}
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
