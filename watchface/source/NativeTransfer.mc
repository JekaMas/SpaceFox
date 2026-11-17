import Toybox.Lang;
import Toybox.StringUtil;
// Raw provisional transfer only. This class never creates an accepted feed,
// publisher floor, source epoch, or active visual pointer.
(:background, :extendedCode, :typecheck(false))
class NativeTransfer {
    var store;var base;var lastAttempt=null;
    function initialize(url,adapter){base=normalize(url);store=adapter==null?new NativeStore():adapter;}
    function normalize(value){
        if(!(value instanceof String)||value.length()<9||value.length()>240||!value.substring(0,8).equals("https://")){return "";}if(value.find("@")!=null||value.find("?")!=null||value.find("#")!=null||value.find("..")!=null||value.find("\\")!=null){return "";}var allowed="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._/:";for(var i=8;i<value.length();i+=1){if(allowed.find(value.substring(i,i+1))==null){return "";}}while(value.length()>8&&value.substring(value.length()-1,value.length()).equals("/")){value=value.substring(0,value.length()-1);}return value.length()>8?value:"";
    }
    function utc(v){return (v instanceof Number||v instanceof Long)&&v>= -62135596800l&&v<=253402300799l;}
    // One decision for callback admission and OS wake scheduling. Garmin
    // temporal callbacks are at least five minutes apart; a connected retry
    // becomes due immediately and armFeed applies that platform floor.
    var lastSucceeded=false;
    function load(){
        if(base.equals("")){return;}var state=store.read("sf.attempt:"+base);
        if(state instanceof Dictionary&&state["base"] instanceof String&&state["base"].equals(base)&&utc(state["utc"])){
            lastAttempt=state["utc"].toLong();lastSucceeded=state["success"]==true;
        }
    }
    function futureUntil(now){
        var marker=new NativeTrustedStore(store,base).marker();var plan=store.read("sf.transfer.plan:"+base);
        if(!(marker instanceof Dictionary)||!(plan instanceof Dictionary)||!(plan["base"] instanceof String)||!plan["base"].equals(base)||plan["sequence"]!=marker["sequence"] ){return null;}
        var targets=plan["targets"];if(!(targets instanceof Array)){return null;}
        var latest=null;for(var i=0;i<targets.size();i+=1){if(utc(targets[i])&&targets[i]>now&&(latest==null||targets[i]>latest)){latest=targets[i];}}return latest;
    }
    function nextWake(now,connected){
        if(lastAttempt==null||now<lastAttempt){return now;}
        var latest=futureUntil(now);if(lastSucceeded&&latest!=null){var hourly=lastAttempt+3600;return latest<hourly?latest:hourly;}
        return connected||now>=lastAttempt+300?now:lastAttempt+300;
    }
    function due(now,connected){return !base.equals("")&&now>=nextWake(now,connected);}
    function attempted(now){lastAttempt=now.toLong();lastSucceeded=false;store.write("sf.attempt:"+base,{"base"=>base,"utc"=>lastAttempt,"success"=>false});}
    function completed(success){lastSucceeded=success;store.write("sf.attempt:"+base,{"base"=>base,"utc"=>lastAttempt,"success"=>success});}
}
