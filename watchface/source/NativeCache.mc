import Toybox.Application;
import Toybox.Lang;
import Toybox.StringUtil;
import Toybox.System;

(:background, :typecheck(false))
class NativeStore {
    var reads=0;var writes=0;var dataWrites=0;
    function initialize(){}
    function read(key){reads+=1;return Application.Storage.getValue(key);}
    function write(key,value){writes+=1;if(key.find("sf.feed.")==0){dataWrites+=1;}Application.Storage.setValue(key,value);if(NativeMetrics.traceStores){System.println("NATIVE_STORE op=write key="+key+" owner="+NativeMetrics.ownerTag);}}
    function remove(key){writes+=1;Application.Storage.deleteValue(key);if(NativeMetrics.traceStores){System.println("NATIVE_STORE op=delete key="+key+" owner="+NativeMetrics.ownerTag);}}
}

(:typecheck(false))
class NativePrior {
    var identity;var publisher;var validation;var stale;var rescheduled;var contentHash;var wireHash;var timingKey;var recordHash;
    function initialize(p){identity=p.launchId();publisher=p.document["publisher"];validation=p.validation;stale=p.stale;rescheduled=p.rescheduled;contentHash=p.contentHash;wireHash=p.wireHash;timingKey=p.timingKey;recordHash=p.recordHash;}
    function launchId(){return identity;}
}

// Foreground-only admission/storage owner. FeedService uses NativeTransfer,
// not this class; clock/renderer arithmetic remains resident.
(:extendedCode, :typecheck(false))
class NativeCacheCore {
    var store;var base;var pinKey;var packet=null;var commit=null;var lastAttempt=null;var failure="";var backgroundMode=true;var requestWake=null;var commitKey="sf.commit";var detached=false;
    function initialize(url,adapter){base=normalize(url);pinKey="sf.pin."+rawHash(base);store=adapter==null?new NativeStore():adapter;}
    function normalize(value){
        if(!(value instanceof String)||value.length()<9||value.length()>240||!value.substring(0,8).equals("https://")){return "";}
        if(value.find("@")!=null||value.find("?")!=null||value.find("#")!=null||value.find("..")!=null||value.find("\\")!=null){return "";}
        var allowed="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._/:";
        for(var i=8;i<value.length();i+=1){if(allowed.find(value.substring(i,i+1))==null){return "";}}
        while(value.length()>8&&value.substring(value.length()-1,value.length()).equals("/")){value=value.substring(0,value.length()-1);}return value.length()>8?value:"";
    }
    function parseFeed(raw,now){return new NativeBridgeFeed(raw,now,store);}
    function rawHash(raw){var h=new NativeWireHash();h.put(raw);return h.digest();}
    function seal(marker){
        // Internal v6 fixed-field canonical preimage. Every string is restricted
        // to normalized URL or lowercase hex before calling this on storage.
        var h=new NativeWireHash();h.put("[6,\""+marker["base"]+"\"");var numbers=["slot","generation","validation"];for(var i=0;i<numbers.size();i+=1){var v=marker[numbers[i]];h.put(","+(v==null?"null":v.toString()));}
        var texts=["rawHash","contentHash","wireHash"];for(var j=0;j<texts.size();j+=1){h.put(",\""+marker[texts[j]]+"\"");}h.put(marker["stale"]?",true":",false");h.put(marker["rescheduled"]?",true":",false");var pub=marker["publisher"];h.put(",\""+pub["instance"]+"\","+pub["generation"]+","+pub["selectionValidatedUtc"]+",\""+marker["priorHash"]+"\"]");return h.digest();
    }
    function hex(value){return nativeHex(value);}
    function load(now){
        packet=null;commit=null;lastAttempt=null;requestWake=null;detached=false;if(base.equals("")){return null;}
        try{var attempt=store.read("sf.attempt");if(attempt instanceof Dictionary&&attempt["base"] instanceof String&&attempt["base"].equals(base)&&attempt["utc"] instanceof Long&&attempt["utc"]>= -62135596800l&&attempt["utc"]<=253402300799l){lastAttempt=attempt["utc"];}}catch(e){}
        var names=["sf.commit","sf.recovery"];
        for(var i=0;i<names.size();i+=1){try{var marker=store.read(names[i]);var loaded=readCommit(marker,now);if(loaded!=null){if(backgroundMode){loaded.compact();}packet=loaded;commit=backgroundMode?marker:detachedCommit(marker);detached=!backgroundMode;commitKey=names[i];return packet;}}catch(e){failure="cache-rejected";NativeMetrics.failure(e.getErrorMessage());if(NativeMetrics.enabled){e.printStackTrace();}}}
        return null;
    }
    // Strict readCommit has already authenticated the complete durable marker.
    // Rendering only needs this summary; detached promotion reloads commitKey
    // before preserving the full recovery record, never writes this summary.
    function detachedCommit(marker){return {"slot"=>marker["slot"],"generation"=>marker["generation"],"rawHash"=>marker["rawHash"],"seal"=>marker["seal"]};}
    function restoreAccepted(now,expectedSeal){
        // Same-session refusal restores the previously accepted marker, even
        // when a new commit write succeeded but its mandatory readback failed.
        // Keep only its seal while parsing; never retain a second full packet.
        packet=null;commit=null;lastAttempt=null;requestWake=null;detached=false;
        if(base.equals("")||!hex(expectedSeal)){return null;}
        try{var attempt=store.read("sf.attempt");if(attempt instanceof Dictionary&&attempt["base"] instanceof String&&attempt["base"].equals(base)&&attempt["utc"] instanceof Long&&attempt["utc"]>= -62135596800l&&attempt["utc"]<=253402300799l){lastAttempt=attempt["utc"];}}catch(e){}
        var names=["sf.commit","sf.recovery"];
        for(var i=0;i<names.size();i+=1){try{var marker=store.read(names[i]);if(!(marker instanceof Dictionary)||!(marker["seal"] instanceof String)||!marker["seal"].equals(expectedSeal)){continue;}var loaded=readCommit(marker,now);if(loaded!=null){if(backgroundMode){loaded.compact();}packet=loaded;commit=backgroundMode?marker:detachedCommit(marker);detached=!backgroundMode;commitKey=names[i];return packet;}}catch(e){failure="cache-rejected";NativeMetrics.failure(e.getErrorMessage());}}
        return null;
    }
    function priorFrom(packet){return [packet.priorDocument(),packet.timingKey,packet.recordHash];}
    function priorHash(prior){
        var h=new NativeWireHash();var d=prior[0];var l=d["launch"];h.put("[\""+d["catalogDigest"]+"\",\""+prior[1]+"\",\""+prior[2]+"\",");h.scalar(l==null?null:l["launch_id"]);h.put(",");h.scalar(l==null?null:l["configuration_id"]);h.put(",");h.scalar(l==null?null:l["timing"]["exact_utc"]);var policy=d["refreshPolicy"];var keys=["normal_interval_seconds","near_interval_seconds","fast_interval_seconds","stale_cycles"];for(var i=0;i<keys.size();i+=1){h.put(",");h.scalar(policy[keys[i]]);}h.put("]");return h.digest();
    }
    function checkedProjection(marker,now){
        if(!(marker instanceof Dictionary)||marker["v"]!=6||!(marker["base"] instanceof String)||!marker["base"].equals(base)||!(marker["prior"] instanceof Array)||marker["prior"].size()!=3||!(marker["prior"][0] instanceof Dictionary)){return null;}
        var p=new NativeCachedPacket(marker);var d=marker["prior"][0];p.shape(d,["catalogDigest","refreshPolicy","launch"],[]);var l=d["launch"];var policy=d["refreshPolicy"];p.shape(policy,["normal_interval_seconds","near_interval_seconds","fast_interval_seconds","stale_cycles"],[]);
        if(!p.integer(marker["slot"])||marker["slot"]<0||marker["slot"]>2||!p.integer(marker["generation"])||marker["generation"]<1||!(marker["stale"] instanceof Boolean)||!(marker["rescheduled"] instanceof Boolean)||!hex(marker["seal"])||!hex(marker["rawHash"])||!hex(marker["wireHash"])||!hex(marker["contentHash"])||!hex(marker["priorHash"])||!hex(d["catalogDigest"])||!hex(p.recordHash)||!(p.timingKey instanceof String)||p.timingKey.length()>80){return null;}
        var pub=marker["publisher"];p.shape(pub,["instance","generation","selectionValidatedUtc"],[]);if(!hex(pub["instance"])||!p.integer(pub["generation"])||pub["generation"]<1||pub["generation"]>253402300799l||!p.utc(pub["selectionValidatedUtc"])||pub["selectionValidatedUtc"]>now){return null;}
        if(l==null){if(marker["validation"]!=null){return null;}}else{p.shape(l,["launch_id","configuration_id","timing"],[]);p.shape(l["timing"],["exact_utc"],[]);if(!p.id(l["launch_id"],"launch",false)||!p.id(l["configuration_id"],"configuration",true)||l["timing"]["exact_utc"]!=null&&!p.utc(l["timing"]["exact_utc"])||!p.utc(marker["validation"])||marker["validation"]>pub["selectionValidatedUtc"]){return null;}}
        if(l==null?!p.timingKey.equals("empty"):p.target()!=null?!p.timingKey.equals("exact:"+p.target()):!hex(p.timingKey)){return null;}
        var normal=policy["normal_interval_seconds"];var near=policy["near_interval_seconds"];var fast=policy["fast_interval_seconds"];if(!p.integer(normal)||normal<300||!p.integer(near)||near<300||near>normal||fast!=null&&(!p.integer(fast)||fast<300||fast>near)||!p.integer(policy["stale_cycles"])||policy["stale_cycles"]<1||!priorHash(marker["prior"]).equals(marker["priorHash"])||!seal(marker).equals(marker["seal"])){return null;}return p;
    }
    function verifyRaw(marker){
        var value=store.read("sf.feed."+marker["slot"]);if(!(value instanceof Dictionary)||!(value["base"] instanceof String)||!value["base"].equals(base)){return false;}var hash=new NativeWireHash();var total=0;
        if(value["v"]==2&&(value["chunks"] instanceof Number||value["chunks"] instanceof Long)&&value["chunks"]>=1&&value["chunks"]<=16){for(var i=0;i<value["chunks"];i+=1){var piece=store.read("sf.feed."+marker["slot"]+"."+i);if(!(piece instanceof String)||piece.length()>512){return false;}var bytes=StringUtil.convertEncodedString(piece,{:fromRepresentation=>StringUtil.REPRESENTATION_STRING_PLAIN_TEXT,:toRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY,:encoding=>StringUtil.CHAR_ENCODING_UTF8});total+=bytes.size();if(bytes.size()>2048||total>8192){return false;}hash.update(bytes);}}
        else{return false;}return hash.digest().equals(marker["rawHash"]);
    }
    function readCommit(marker,now){var p=checkedProjection(marker,now);if(p==null||!verifyRaw(marker)){return null;}p.advance(now);NativeMetrics.sample("cached-raw-and-projection-verified");return p;}
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
        requestWake=nextWake(now);detached=true;if(packet!=null){packet=new NativePrior(packet);}if(commit!=null){commit={"slot"=>commit["slot"],"generation"=>commit["generation"],"rawHash"=>commit["rawHash"],"seal"=>commit["seal"]};}NativeMetrics.sample("pre-request-released");
    }
    function accept(raw,now){
        var operation="parse";failure="";try{
            var promotionWrites=store.writes;var candidate=parseFeed(raw,now);var pub=candidate.document["publisher"];
            if(base.equals("")||pub["selectionValidatedUtc"]==null){return false;}
            operation="lookup";if(!checkPublisher(pub,candidate.wireHash)){return false;}
            if(packet!=null){var previous=packet instanceof NativePrior?packet.publisher:packet.document["publisher"];if(!pub["instance"].equals(previous["instance"])||pub["generation"]<previous["generation"]||pub["selectionValidatedUtc"]<previous["selectionValidatedUtc"]){return false;}if(pub["generation"]==previous["generation"]){if(!candidate.wireHash.equals(packet.wireHash)){return false;}if(packet instanceof NativePrior){operation="metadata";candidate.metadata(packet,now);if(!backgroundMode){candidate.presentation=feedScene(candidate,now);}candidate.compact();packet=candidate;requestWake=null;}else{packet.advance(now);}return true;}}
            var mutable=candidate.mutableWire();var mutableSpans=candidate.ignored;operation="metadata";candidate.metadata(packet,now);NativeMetrics.sample("candidate-and-prior");if(!backgroundMode){candidate.presentation=feedScene(candidate,now);}candidate.compact();NativeMetrics.sample("candidate-compacted");operation="persist";var same=packet!=null&&candidate.contentHash.equals(packet.contentHash);var slot=same?commit["slot"]:freeSlot();var rawDigest=same?commit["rawHash"]:candidate.wireHash;
            var marker={"v"=>6,"base"=>base,"slot"=>slot,"generation"=>commit==null?1:commit["generation"]+1,"rawHash"=>rawDigest,"contentHash"=>candidate.contentHash,"validation"=>candidate.validation,"stale"=>candidate.stale,"rescheduled"=>candidate.rescheduled,"publisher"=>pub,"wireHash"=>candidate.wireHash,"mutable"=>mutable};marker["prior"]=priorFrom(candidate);marker["priorHash"]=priorHash(marker["prior"]);marker["seal"]=seal(marker);
            if(!same){var chunks=0;for(var offset=0;offset<raw.length();offset+=512){var end=offset+512;if(end>raw.length()){end=raw.length();}var part=raw.substring(offset,end);var key="sf.feed."+slot+"."+chunks;store.write(key,part);var verify=store.read(key);if(!(verify instanceof String)||!verify.equals(part)){throw new Lang.InvalidValueException("Chunk readback mismatch");}verify=null;part=null;chunks+=1;}store.write("sf.feed."+slot,{"v"=>2,"base"=>base,"chunks"=>chunks,"rawHash"=>rawDigest,"mutableSpans"=>mutableSpans});}
            // Every chunk has completed write/readback; commit verification needs
            // only the compact candidate and immutable raw hash from this point.
            raw=null;
            rememberPublisher(pub,candidate.wireHash);if(commit!=null){store.write("sf.recovery",detached?store.read(commitKey):commit);}store.write("sf.commit",marker);var observed=store.read("sf.commit");if(!(observed instanceof Dictionary)||!(observed["seal"] instanceof String)||!observed["seal"].equals(marker["seal"])||!seal(observed).equals(marker["seal"])){throw new Lang.InvalidValueException("Commit readback mismatch");}
            commit=backgroundMode?marker:detachedCommit(marker);packet=candidate;commitKey="sf.commit";detached=!backgroundMode;requestWake=null;failure="";NativeMetrics.writes("promotion",store.writes-promotionWrites);NativeMetrics.sample("cache-committed");return true;
        }catch(e){failure=operation.equals("lookup")||operation.equals("persist")||e.getErrorMessage().equals("Bridge catalog incomplete")?"admission-retry":"update-rejected";NativeMetrics.failure(e.getErrorMessage());return false;}
    }
    function attempted(now){lastAttempt=now.toLong();try{store.write("sf.attempt",{"base"=>base,"utc"=>lastAttempt});return true;}catch(e){failure="storage-full";return false;}}
    function due(now){if(base.equals("")){return false;}var cadence=packet==null?3600:packet.interval(now);return lastAttempt==null||now<lastAttempt||now-lastAttempt>=cadence;}
    function nextWake(now){
        if(requestWake!=null){return requestWake;}var interval=packet==null?3600:packet.interval(now);var remaining=lastAttempt==null||now<lastAttempt?0:interval-(now-lastAttempt);var next=remaining<=0?now:now+(remaining>86400?86400:remaining);var target=packet==null?null:packet.target();
        if(target!=null){if(now<target-7200&&next>target-7200){next=target-7200;}else if(now<target+1801&&next>target+1801){next=target+1801;}}if(next<now){next=now;}if(next>now+86400){next=now+86400;}return next;
    }
}
