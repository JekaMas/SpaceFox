import Toybox.Lang;
import Toybox.StringUtil;

(:extendedCode, :typecheck(false))
class NativeCache extends NativeCacheCore {
    function initialize(url,adapter){NativeCacheCore.initialize(url,adapter);backgroundMode=false;}
    function pieces(raw,spans){
        if(!(spans instanceof Array)||spans.size()>16){throw new Lang.InvalidValueException("Missing raw mutable spans");}var result=[];var previous=0;for(var i=0;i<spans.size();i+=1){var span=spans[i];if(!(span instanceof Array)||span.size()!=2||!(span[0] instanceof Number)||!(span[1] instanceof Number)||span[0]<previous||span[1]<=span[0]||span[1]>raw.length()){throw new Lang.InvalidValueException("Invalid raw mutable spans");}result.add(raw.substring(span[0],span[1]));previous=span[1];}return result;
    }
    function hashReplaced(raw,spans,replacements){
        pieces(raw,spans);if(!(replacements instanceof Array)||replacements.size()!=spans.size()){throw new Lang.InvalidValueException("Missing inverse witness");}var hash=new NativeWireHash();var start=0;for(var i=0;i<spans.size();i+=1){if(!(replacements[i] instanceof String)){throw new Lang.InvalidValueException("Invalid inverse witness");}hash.range(raw,start,spans[i][0]);hash.put(replacements[i]);start=spans[i][1];}hash.range(raw,start,raw.length());var digest=hash.digest();if(hash.count>8192){throw new Lang.InvalidValueException("Inverse raw byte bound");}return digest;
    }
    function replaceSpans(raw,spans,replacements){
        pieces(raw,spans);if(!(replacements instanceof Array)||replacements.size()!=spans.size()){throw new Lang.InvalidValueException("Missing raw metadata witness");}var result="";var start=0;for(var i=0;i<spans.size();i+=1){if(!(replacements[i] instanceof String)||replacements[i].length()>8192){throw new Lang.InvalidValueException("Invalid raw metadata witness");}var span=spans[i];result+=raw.substring(start,span[0])+replacements[i];if(result.length()>8192){throw new Lang.InvalidValueException("Raw metadata witness bound");}start=span[1];}result+=raw.substring(start,raw.length());return result;
    }

}

// Foreground durable promotion. Pointer publication is the final phase; every
// input chunk is written and read back in a separate permitted callback.
(:extendedCode, :typecheck(false))
class NativeFeedPromotion {
    var cache;var raw;var candidate;var now;var view;var mustYield=false;var phase=0;var operation="parse";var done=false;var accepted=false;var pub;var mutable;var mutableSpans;var marker;var slot;var same=false;var offset=0;var chunks=0;
    function initialize(owner,text,packet,at,scene){cache=owner;raw=text;candidate=packet;now=at;view=scene;cache.failure="";}
    function step(){
        if(done){return true;}
        try{
            if(phase==0){
                if(!(candidate instanceof NativePreparedBridgeFeed)||candidate.preparePhase!=8||candidate.prepareNow!=now||!candidate.raw.equals(raw)){throw new Lang.InvalidValueException("Incomplete prepared feed");}
                pub=candidate.document["publisher"];if(cache.base.equals("")||pub["selectionValidatedUtc"]==null){cache.failure="update-rejected";done=true;return true;}
                operation="lookup";if(!cache.checkPublisher(pub,candidate.wireHash)){cache.failure="update-rejected";done=true;return true;}
                if(cache.packet!=null){var previous=cache.packet instanceof NativePrior?cache.packet.publisher:cache.packet.document["publisher"];if(!pub["instance"].equals(previous["instance"])||pub["generation"]<previous["generation"]||pub["selectionValidatedUtc"]<previous["selectionValidatedUtc"]){cache.failure="update-rejected";done=true;return true;}
                    if(pub["generation"]==previous["generation"]){if(!candidate.wireHash.equals(cache.packet.wireHash)){cache.failure="update-rejected";done=true;return true;}if(cache.packet instanceof NativePrior){operation="metadata";candidate.metadata(cache.packet,now);candidate.raw="";candidate.spans=null;candidate.ignored=null;raw=null;candidate.presentation=feedScene(candidate,now);candidate.compact();cache.packet=candidate;cache.requestWake=null;}else{cache.packet.advance(now);}accepted=true;done=true;return true;}}
                mutable=candidate.mutableWire();mutableSpans=candidate.ignored;operation="metadata";candidate.metadata(cache.packet,now);candidate.raw="";candidate.spans=null;candidate.ignored=null;operation="persist";same=cache.packet!=null&&candidate.contentHash.equals(cache.packet.contentHash);slot=same?cache.commit["slot"]:cache.freeSlot();var rawDigest=same?cache.commit["rawHash"]:candidate.wireHash;
                marker={"v"=>6,"base"=>cache.base,"slot"=>slot,"generation"=>cache.commit==null?1:cache.commit["generation"]+1,"rawHash"=>rawDigest,"contentHash"=>candidate.contentHash,"validation"=>candidate.validation,"stale"=>candidate.stale,"rescheduled"=>candidate.rescheduled,"publisher"=>pub,"wireHash"=>candidate.wireHash,"mutable"=>mutable};marker["prior"]=cache.priorFrom(candidate);marker["priorHash"]=cache.priorHash(marker["prior"]);marker["seal"]=cache.seal(marker);phase=1;return false;
            }
            if(phase==1){
                if(!same&&offset<raw.length()){var end=offset+512;if(end>raw.length()){end=raw.length();}var part=raw.substring(offset,end);var key="sf.feed."+slot+"."+chunks;cache.store.write(key,part);var observed=cache.store.read(key);if(!(observed instanceof String)||!observed.equals(part)){throw new Lang.InvalidValueException("Chunk readback mismatch");}offset=end;chunks+=1;return false;}
                if(!same){cache.store.write("sf.feed."+slot,{"v"=>2,"base"=>cache.base,"chunks"=>chunks,"rawHash"=>marker["rawHash"],"mutableSpans"=>mutableSpans});}raw=null;phase=2;mustYield=true;return false;
            }
            if(phase==2){candidate.presentation=feedScene(candidate,now);candidate.compact();phase=3;return false;}
            if(phase==3){if(view!=null&&cache.packet!=null){new NativeUpcomingCache(cache.store,cache.base,pub["instance"]).save(view.queueSnapshots());}phase=4;return false;}
            if(phase==4){cache.rememberPublisher(pub,candidate.wireHash);phase=5;return false;}
            if(phase==5){if(cache.commit!=null){cache.store.write("sf.recovery",cache.detached?cache.store.read(cache.commitKey):cache.commit);}phase=6;return false;}
            cache.store.write("sf.commit",marker);var observed=cache.store.read("sf.commit");if(!(observed instanceof Dictionary)||!(observed["seal"] instanceof String)||!observed["seal"].equals(marker["seal"])||!cache.seal(observed).equals(marker["seal"])){throw new Lang.InvalidValueException("Commit readback mismatch");}
            cache.commit=cache.detachedCommit(marker);cache.packet=candidate;cache.commitKey="sf.commit";cache.detached=true;cache.requestWake=null;cache.failure="";accepted=true;done=true;return true;
        }catch(e){var message=e.getErrorMessage();cache.failure=operation.equals("lookup")||operation.equals("persist")||message.equals("Bridge catalog incomplete")?"admission-retry":"update-rejected";done=true;return true;}
    }
}

// Strict restoration is prepared over slices. A marker is not rebound to the
// view until its raw chunks, hashes, full parse and inverse witness all pass.
(:extendedCode, :typecheck(false))
class NativeRestoreJob {
    var cache;var now;var expected;var mustYield=false;var names=["sf.commit","sf.recovery"];var which=0;var phase=0;var marker=null;var value=null;var part=0;var piece=null;var pieceOffset=0;var pieceSize=0;var bytes=[]b;var raw=null;var original=null;var packet=null;var hashJob=null;var current=null;var done=false;var accepted=false;
    function initialize(owner,at,seal){cache=owner;now=at;expected=seal;cache.packet=null;cache.commit=null;cache.lastAttempt=null;cache.requestWake=null;cache.detached=false;try{var attempt=cache.store.read("sf.attempt");if(attempt instanceof Dictionary&&attempt["base"] instanceof String&&attempt["base"].equals(cache.base)&&attempt["utc"] instanceof Long&&attempt["utc"]>= -62135596800l&&attempt["utc"]<=253402300799l){cache.lastAttempt=attempt["utc"];}}catch(e){}}
    function dispose(){if(packet!=null){packet.disposePreparation();packet=null;}}
    function reject(){dispose();marker=null;value=null;bytes=[]b;raw=null;original=null;packet=null;hashJob=null;current=null;part=0;piece=null;pieceOffset=0;pieceSize=0;phase=0;which+=1;if(which>=names.size()){done=true;}}
    function step(){
        if(done){return true;}
        try{
            if(phase==0){
                if(cache.base.equals("")||which>=names.size()){done=true;return true;}marker=cache.store.read(names[which]);if(expected!=null&&(!(marker instanceof Dictionary)||!(marker["seal"] instanceof String)||!marker["seal"].equals(expected))){reject();return done;}
                if(cache.checkedProjection(marker,now)==null){reject();return done;}value=cache.store.read("sf.feed."+marker["slot"]);if(!(value instanceof Dictionary)||!(value["base"] instanceof String)||!value["base"].equals(cache.base)||value["v"]!=2||!(value["chunks"] instanceof Number||value["chunks"] instanceof Long)||value["chunks"]<1||value["chunks"]>16){reject();return done;}phase=1;return false;
            }
            if(phase==1){
                if(part<value["chunks"]){if(piece==null){piece=cache.store.read("sf.feed."+marker["slot"]+"."+part);if(!(piece instanceof String)||piece.length()>512){reject();return done;}pieceOffset=0;pieceSize=0;}
                    if(pieceOffset<piece.length()){var end=pieceOffset+64;if(end>piece.length()){end=piece.length();}var b=piece.substring(pieceOffset,end).toUtf8Array();pieceSize+=b.size();if(pieceSize>2048||bytes.size()+b.size()>8192){reject();return done;}bytes.addAll(b);pieceOffset=end;return false;}piece=null;part+=1;return false;}
                raw=StringUtil.convertEncodedString(bytes,{:fromRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY,:toRepresentation=>StringUtil.REPRESENTATION_STRING_PLAIN_TEXT,:encoding=>StringUtil.CHAR_ENCODING_UTF8});bytes=null;hashJob=new NativeFeedHashJob(raw,[]);phase=2;return false;
            }
            if(phase==2){if(!hashJob.step()){return false;}if(!hashJob.result.equals(marker["rawHash"])){reject();return done;}hashJob=null;current=raw;if(!marker["wireHash"].equals(marker["rawHash"])){var spans=value["mutableSpans"];original=cache.pieces(raw,spans);current=cache.replaceSpans(raw,spans,marker["mutable"]);}value=null;raw=null;packet=new NativePreparedBridgeFeed(current,now,cache.store);phase=3;return false;}
            if(phase==3){if(!packet.prepareStep()){return false;}current=null;var prior=cache.priorFrom(packet);var stored=marker["prior"][0]["launch"];if(stored!=null&&!stored["timing"].hasKey("refresh_utc")&&prior[0]["launch"]!=null){prior[0]["launch"]["timing"].remove("refresh_utc");}if(!packet.wireHash.equals(marker["wireHash"])||!packet.contentHash.equals(marker["contentHash"])||packet.validation!=marker["validation"]||!cache.priorHash(prior).equals(marker["priorHash"])){reject();return done;}
                if(original!=null){cache.pieces(packet.raw,packet.ignored);if(original.size()!=packet.ignored.size()){reject();return done;}var replacements=[];for(var i=0;i<original.size();i+=1){if(!(original[i] instanceof String)){reject();return done;}replacements.add([packet.ignored[i][0],packet.ignored[i][1],original[i]]);}hashJob=new NativeFeedHashJob(packet.raw,replacements);phase=4;return false;}phase=5;return false;
            }
            if(phase==4){if(!hashJob.step()){return false;}if(hashJob.byteCount>8192||!hashJob.result.equals(marker["rawHash"])){reject();return done;}hashJob=null;original=null;phase=5;return false;}
            if(phase==5){var pub=packet.document["publisher"];var bound=marker["publisher"];if(!pub["instance"].equals(bound["instance"])||pub["generation"]!=bound["generation"]||pub["selectionValidatedUtc"]!=bound["selectionValidatedUtc"]||packet.stale&&!marker["stale"]||packet.rescheduled&&!marker["rescheduled"]){reject();return done;}packet.stale=marker["stale"];packet.rescheduled=marker["rescheduled"];packet.advance(now);packet.raw="";packet.spans=null;packet.ignored=null;phase=6;mustYield=true;return false;}
            var latest=cache.store.read(names[which]);if(!(latest instanceof Dictionary)||!(latest["seal"] instanceof String)||!latest["seal"].equals(marker["seal"])){which= -1;reject();return false;}latest=null;
            packet.presentation=feedScene(packet,now);packet.compact();cache.packet=packet;cache.commit=cache.detachedCommit(marker);cache.detached=true;cache.commitKey=names[which];accepted=true;done=true;return true;
        }catch(e){cache.failure="cache-rejected";reject();return done;}
    }
}
