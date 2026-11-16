import Toybox.Application;
import Toybox.Lang;
import Toybox.StringUtil;
import Toybox.System;

(:background, :typecheck(false))
class NativeStore {
    var reads=0;var writes=0;var dataWrites=0;
    function initialize(){}
    function read(key){reads+=1;return Application.Storage.getValue(key);}
    function write(key,value){writes+=1;if(key.find("sf.feed.")==0){dataWrites+=1;}Application.Storage.setValue(key,value);}
    function remove(key){writes+=1;Application.Storage.deleteValue(key);}
}

(:typecheck(false))
class NativePrior {
    var identity;var refresh;var publisher;var validation;var stale;var rescheduled;var contentHash;var wireHash;var timingKey;var recordHash;
    function initialize(p){identity=p.launchId();refresh=p.refreshTarget();publisher=p.document["publisher"];validation=p.validation;stale=p.stale;rescheduled=p.rescheduled;contentHash=p.contentHash;wireHash=p.wireHash;timingKey=p.timingKey;recordHash=p.recordHash;}
    function launchId(){return identity;}
    function refreshTarget(){return refresh;}
}

// Foreground-only admission/storage owner. FeedService uses NativeTransfer,
// not this class; clock/renderer arithmetic remains resident.
(:extendedCode, :typecheck(false))
class NativeCacheCore {
    var store;var base;var pinKey;var queueView=null;var packet=null;var commit=null;var lastAttempt=null;var failure="";var backgroundMode=true;var requestWake=null;var commitKey="sf.commit";var detached=false;
    function initialize(url,adapter){base=normalize(url);pinKey="sf.pin."+rawHash(base);store=adapter==null?new NativeStore():adapter;}
    function normalize(value){
        if(!(value instanceof String)||value.length()<9||value.length()>240||!value.substring(0,8).equals("https://")){return "";}
        if(value.find("@")!=null||value.find("?")!=null||value.find("#")!=null||value.find("..")!=null||value.find("\\")!=null){return "";}
        var allowed="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._/:";
        for(var i=8;i<value.length();i+=1){if(allowed.find(value.substring(i,i+1))==null){return "";}}
        while(value.length()>8&&value.substring(value.length()-1,value.length()).equals("/")){value=value.substring(0,value.length()-1);}return value.length()>8?value:"";
    }
    function rawHash(raw){var h=new NativeWireHash();h.put(raw);return h.digest();}
    function seal(marker){
        // Internal v6 fixed-field canonical preimage. Every string is restricted
        // to normalized URL or lowercase hex before calling this on storage.
        var h=new NativeWireHash();h.put("[6,\""+marker["base"]+"\"");var numbers=["slot","generation","validation"];for(var i=0;i<numbers.size();i+=1){var v=marker[numbers[i]];h.put(","+(v==null?"null":v.toString()));}
        var texts=["rawHash","contentHash","wireHash"];for(var j=0;j<texts.size();j+=1){h.put(",\""+marker[texts[j]]+"\"");}h.put(marker["stale"]?",true":",false");h.put(marker["rescheduled"]?",true":",false");var pub=marker["publisher"];h.put(",\""+pub["instance"]+"\","+pub["generation"]+","+pub["selectionValidatedUtc"]+",\""+marker["priorHash"]+"\"]");return h.digest();
    }
    function hex(value){return nativeHex(value);}
    // Strict readCommit has already authenticated the complete durable marker.
    // Rendering only needs this summary; detached promotion reloads commitKey
    // before preserving the full recovery record, never writes this summary.
    function detachedCommit(marker){return {"slot"=>marker["slot"],"generation"=>marker["generation"],"rawHash"=>marker["rawHash"],"seal"=>marker["seal"]};}
    function priorFrom(packet){return [packet.priorDocument(),packet.timingKey,packet.recordHash];}
    function priorHash(prior){
        var h=new NativeWireHash();var d=prior[0];var l=d["launch"];h.put("[\""+d["catalogDigest"]+"\",\""+prior[1]+"\",\""+prior[2]+"\",");h.scalar(l==null?null:l["launch_id"]);h.put(",");h.scalar(l==null?null:l["configuration_id"]);h.put(",");h.scalar(l==null?null:l["timing"]["exact_utc"]);if(l!=null&&l["timing"].hasKey("refresh_utc")){h.put(",");h.scalar(l["timing"]["refresh_utc"]);}var policy=d["refreshPolicy"];var keys=["normal_interval_seconds","near_interval_seconds","fast_interval_seconds","stale_cycles"];for(var i=0;i<keys.size();i+=1){h.put(",");h.scalar(policy[keys[i]]);}h.put("]");return h.digest();
    }
    function checkedProjection(marker,now){
        if(!(marker instanceof Dictionary)||marker["v"]!=6||!(marker["base"] instanceof String)||!marker["base"].equals(base)||!(marker["prior"] instanceof Array)||marker["prior"].size()!=3||!(marker["prior"][0] instanceof Dictionary)){return null;}
        var p=new NativeCachedPacket(marker);var d=marker["prior"][0];p.shape(d,["catalogDigest","refreshPolicy","launch"],[]);var l=d["launch"];var policy=d["refreshPolicy"];p.shape(policy,["normal_interval_seconds","near_interval_seconds","fast_interval_seconds","stale_cycles"],[]);
        if(!p.integer(marker["slot"])||marker["slot"]<0||marker["slot"]>2||!p.integer(marker["generation"])||marker["generation"]<1||!(marker["stale"] instanceof Boolean)||!(marker["rescheduled"] instanceof Boolean)||!hex(marker["seal"])||!hex(marker["rawHash"])||!hex(marker["wireHash"])||!hex(marker["contentHash"])||!hex(marker["priorHash"])||!hex(d["catalogDigest"])||!hex(p.recordHash)||!(p.timingKey instanceof String)||p.timingKey.length()>80){return null;}
        var pub=marker["publisher"];p.shape(pub,["instance","generation","selectionValidatedUtc"],[]);if(!hex(pub["instance"])||!p.integer(pub["generation"])||pub["generation"]<1||pub["generation"]>253402300799l||!p.utc(pub["selectionValidatedUtc"])||pub["selectionValidatedUtc"]>now){return null;}
        if(l==null){if(marker["validation"]!=null){return null;}}else{p.shape(l,["launch_id","configuration_id","timing"],[]);p.shape(l["timing"],["exact_utc"],["refresh_utc"]);if(!p.id(l["launch_id"],"launch",false)||!p.id(l["configuration_id"],"configuration",true)||l["timing"]["exact_utc"]!=null&&!p.utc(l["timing"]["exact_utc"])||l["timing"].hasKey("refresh_utc")&&(l["timing"]["exact_utc"]!=null||!p.utc(l["timing"]["refresh_utc"]))||!p.utc(marker["validation"])||marker["validation"]>pub["selectionValidatedUtc"]){return null;}}
        if(l==null?!p.timingKey.equals("empty"):p.target()!=null?!p.timingKey.equals("exact:"+p.target()):!hex(p.timingKey)){return null;}
        var normal=policy["normal_interval_seconds"];var near=policy["near_interval_seconds"];var fast=policy["fast_interval_seconds"];if(!p.integer(normal)||normal<300||!p.integer(near)||near<300||near>normal||fast!=null&&(!p.integer(fast)||fast<300||fast>near)||!p.integer(policy["stale_cycles"])||policy["stale_cycles"]<1||!priorHash(marker["prior"]).equals(marker["priorHash"])||!seal(marker).equals(marker["seal"])){return null;}return p;
    }
    function freeSlot(){
        var active=commit==null?-1:commit["slot"];var recovery=-1;var old=store.read("sf.recovery");if(old instanceof Dictionary&&old["base"] instanceof String&&old["base"].equals(base)&&(old["slot"] instanceof Number||old["slot"] instanceof Long)){recovery=old["slot"];}
        for(var slot=0;slot<3;slot+=1){if(slot!=active&&slot!=recovery){return slot;}}throw new Lang.InvalidValueException("No inactive feed slot");
    }
    function checkPublisher(pub,wire){
        var pin=store.read(pinKey);if(pin==null){return true;}
        return pin instanceof Dictionary&&pin["instance"] instanceof String&&pin["instance"].equals(pub["instance"])&&(pin["generation"] instanceof Number||pin["generation"] instanceof Long)&&pub["generation"]>=pin["generation"]&&pub["selectionValidatedUtc"]>=pin["selectionValidatedUtc"]&&(pub["generation"]!=pin["generation"]||wire.equals(pin["wireHash"]));
    }
    function rememberPublisher(pub,wire){
        var key=pinKey;var pin=store.read(key);if(pin!=null&&pin["generation"]==pub["generation"]&&wire.equals(pin["wireHash"])){return;}
        if(pin==null){var index=store.read("sf.pins");if(index==null){index=[];}if(!(index instanceof Array)||index.size()>=8){throw new Lang.InvalidValueException("Publisher namespace capacity");}var next=[];for(var i=0;i<index.size();i+=1){if(!(index[i] instanceof String)){throw new Lang.InvalidValueException("Publisher namespace index");}next.add(index[i]);}if(next.indexOf(key)<0){next.add(key);store.write("sf.pins",next);}}
        // Monotonic admission floor precedes commit. Interruption may retain the
        // prior display, but switching URLs cannot erase a seen publisher head.
        store.write(key,{"instance"=>pub["instance"],"generation"=>pub["generation"],"selectionValidatedUtc"=>pub["selectionValidatedUtc"],"wireHash"=>wire});
    }
    function releaseForTransfer(now){
        // An identical publisher generation can succeed without writing a new
        // commit. Keep its accepted seal for a later same-session refusal.
        requestWake=nextWake(now);detached=true;if(packet!=null){packet=new NativePrior(packet);}if(commit!=null){commit={"slot"=>commit["slot"],"generation"=>commit["generation"],"rawHash"=>commit["rawHash"],"seal"=>commit["seal"]};}
    }
    function attempted(now){lastAttempt=now.toLong();try{store.write("sf.attempt",{"base"=>base,"utc"=>lastAttempt});return true;}catch(e){failure="storage-full";return false;}}
    function due(now){if(base.equals("")){return false;}var cadence=packet==null?3600:packet.interval(now);return lastAttempt==null||now<lastAttempt||now-lastAttempt>=cadence;}
    function nextWake(now){
        if(requestWake!=null){return requestWake;}var interval=packet==null?3600:packet.interval(now);var remaining=lastAttempt==null||now<lastAttempt?0:interval-(now-lastAttempt);var next=remaining<=0?now:now+(remaining>86400?86400:remaining);var target=packet==null?null:packet.refreshTarget();
        if(target!=null){if(now<target-7200&&next>target-7200){next=target-7200;}else if(now<target+1801&&next>target+1801){next=target+1801;}}if(next<now){next=now;}if(next>now+86400){next=now+86400;}return next;
    }
}
