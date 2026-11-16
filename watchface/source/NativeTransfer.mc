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
    function load(){
        if(base.equals("")){return;}var attempt=store.read("sf.attempt");if(attempt instanceof Dictionary&&attempt["base"] instanceof String&&attempt["base"].equals(base)&&attempt["build"] instanceof String&&attempt["build"].equals(NativeVersion.BUILD)&&utc(attempt["utc"])){lastAttempt=attempt["utc"].toLong();}
    }
    function interval(now){
        // A first-install failure must not defer the next attempt for an hour.
        // Accepted content retains its existing feed-driven cadence.
        var ready=store.read("sf.transfer.ready");if(!(ready instanceof Dictionary)||!(ready["base"] instanceof String)||!ready["base"].equals(base)||ready["accepted"]!=true){return 300;}
        var plan=store.read("sf.transfer.plan");if(!(plan instanceof Dictionary)||!(plan["base"] instanceof String)||!plan["base"].equals(base)){return 3600;}var p=plan["policy"];if(!(p instanceof Array)||p.size()!=3){return 3600;}for(var i=0;i<3;i+=1){if(p[i]!=null&&(!(p[i] instanceof Number||p[i] instanceof Long)||p[i]<300)){return 3600;}}if(p[0]==null||p[1]==null||p[1]>p[0]||p[2]!=null&&p[2]>p[1]){return 3600;}if(p[2]!=null){return p[2];}var targets=planTargets(plan);if(targets==null){return p[1];}for(var t=0;t<targets.size();t+=1){var target=targets[t];if(now>=target-7200&&now<=target+1800){return p[1];}}return p[0];
    }
    // The current plan owns all validated selected/preloaded targets. Missing
    // derived plans use near cadence until the foreground rebuilds from raw.
    function planTargets(plan){var targets=plan["targets"];if(targets instanceof Array&&targets.size()<=3){for(var i=0;i<targets.size();i+=1){if(!utc(targets[i])){return null;}}return targets;}return null;}
    function due(now){return !base.equals("")&&(lastAttempt==null||now<lastAttempt||now-lastAttempt>=interval(now));}
    function attempted(now){lastAttempt=now.toLong();store.write("sf.attempt",{"base"=>base,"utc"=>lastAttempt,"build"=>NativeVersion.BUILD});}
    function nextWake(now){
        var cadence=interval(now);var remaining=lastAttempt==null||now<lastAttempt?0:cadence-(now-lastAttempt);var next=remaining<=0?now:now+(remaining>86400?86400:remaining);var p=store.read("sf.transfer.plan");if(p instanceof Dictionary&&p["base"] instanceof String&&p["base"].equals(base)){var targets=planTargets(p);if(targets!=null){for(var i=0;i<targets.size();i+=1){var start=targets[i]-7200;var end=targets[i]+1801;if(now<start&&next>start){next=start;}if(now<end&&next>end){next=end;}}}}return next;
    }
    // Publish the new marker first. Only then remove fragments not referenced
    // by it; an interrupted cleanup can leave garbage but cannot damage the
    // current marker. An older concurrent reader rechecks the marker on reopen.
    function cleanupFragments(key,parts){
        try{for(var i=0;i<16;i+=1){for(var bank=0;bank<2;bank+=1){if(i<parts.size()&&parts[i]==bank){continue;}var fragment=key+"."+bank+"."+i;if(store.read(fragment)!=null){store.remove(fragment);}}}}catch(e){}
    }
    function sameMarker(a,b){
        if(!(a instanceof Dictionary)||a.size()!=b.size()||a["v"]!=b["v"]||!(a["base"] instanceof String)||!a["base"].equals(b["base"])||a["sequence"]!=b["sequence"]||!(a["sha256"] instanceof String)||!a["sha256"].equals(b["sha256"])||a["bytes"]!=b["bytes"]||!(a["kind"] instanceof String)||!a["kind"].equals(b["kind"])||!(a["parts"] instanceof Array)||a["parts"].size()!=b["parts"].size()){return false;}
        for(var i=0;i<a["parts"].size();i+=1){if(a["parts"][i]!=b["parts"][i]){return false;}}
        var x=a["request"];var y=b["request"];if(x==null||y==null){return x==null&&y==null;}
        return x instanceof Dictionary&&y instanceof Dictionary&&x["sha256"] instanceof String&&y["sha256"] instanceof String&&x["sha256"].equals(y["sha256"])&&x["decodedBytes"]==y["decodedBytes"];
    }
    function stage(kind,raw,request){
        var limit=kind.equals("feed")?8192:4096;if(!(raw instanceof String)||raw.length()>limit){return false;}var hash=new NativeWireHash();hash.put(raw);var sha=hash.digest();if(hash.count>limit){return false;}if(kind.equals("object")&&(!nativeHex(request["sha256"])||!sha.equals(request["sha256"])||hash.count!=request["decodedBytes"])){return false;}
        var name=kind.equals("feed")?"feed":"asset";var key="sf.incoming."+name;var prior=store.read(key);var valid=prior instanceof Dictionary&&prior["v"]==2&&prior["base"] instanceof String&&prior["base"].equals(base)&&prior["parts"] instanceof Array&&prior["parts"].size()<=16;var parts=[];var count=0;var changed=false;
        for(var offset=0;offset<raw.length();offset+=512){var end=offset+512;if(end>raw.length()){end=raw.length();}var piece=raw.substring(offset,end);var old=valid&&count<prior["parts"].size()?prior["parts"][count]:null;var oldSlot=old instanceof Number&&(old==0||old==1)?old:null;var retained=oldSlot==null?null:store.read(key+"."+oldSlot+"."+count);var slot=oldSlot;
            if(!(retained instanceof String)||!retained.equals(piece)){slot=oldSlot==0?1:0;var partKey=key+"."+slot+"."+count;store.write(partKey,piece);var observed=store.read(partKey);if(!(observed instanceof String)||!observed.equals(piece)){throw new Lang.InvalidValueException("Provisional readback");}changed=true;}parts.add(slot);count+=1;
        }
        if(kind.equals("feed")&&valid&&!changed&&prior["sha256"] instanceof String&&prior["sha256"].equals(sha)&&prior["parts"].size()==parts.size()){cleanupFragments(key,parts);return true;}
        var sequence=valid&&(prior["sequence"] instanceof Number||prior["sequence"] instanceof Long)&&prior["sequence"]>=1&&prior["sequence"]<253402300799l?prior["sequence"]+1:1;
        var marker={"v"=>2,"base"=>base,"parts"=>parts,"sequence"=>sequence,"sha256"=>sha,"bytes"=>hash.count,"kind"=>kind,"request"=>request};store.write(key,marker);
        var observed=store.read(key);if(!sameMarker(observed,marker)){throw new Lang.InvalidValueException("Provisional marker readback");}cleanupFragments(key,parts);return true;
    }

}
