import Toybox.Lang;
import Toybox.StringUtil;
// Foreground only: the provisional pointer is not an admission receipt.
(:extendedCode, :typecheck(false))
class NativeIncoming {
    var store;var base;var needsRestore=false;var restoreSeal=null;
    function initialize(adapter,url){store=adapter;base=url;}
    function token(marker){return marker["sha256"]+":"+marker["sequence"];}
    function read(name,force){
        var key="sf.incoming."+name;var m=store.read(key);if(!(m instanceof Dictionary)||m["v"]!=2||!(m["base"] instanceof String)||!m["base"].equals(base)||!nativeHex(m["sha256"])||!(m["parts"] instanceof Array)||m["parts"].size()<1||m["parts"].size()>16||!(m["sequence"] instanceof Number||m["sequence"] instanceof Long)||m["sequence"]<1||m["sequence"]>253402300799l||!(m["bytes"] instanceof Number)||m["bytes"]<1||m["bytes"]>8192){return null;}
        var done=store.read(key+".processed");if(!force&&done instanceof String&&done.equals(token(m))){return null;}var assembled=[]b;var total=0;var h=new NativeWireHash();for(var i=0;i<m["parts"].size();i+=1){var slot=m["parts"][i];if(!(slot instanceof Number)||slot<0||slot>1){return null;}var s=store.read(key+"."+slot+"."+i);if(!(s instanceof String)||s.length()>512){return null;}var b=StringUtil.convertEncodedString(s,{:fromRepresentation=>StringUtil.REPRESENTATION_STRING_PLAIN_TEXT,:toRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY,:encoding=>StringUtil.CHAR_ENCODING_UTF8});if(b.size()>2048||total+b.size()>8192){return null;}h.update(b);total+=b.size();assembled.addAll(b);}
        var latest=store.read(key);if(total!=m["bytes"]||!h.digest().equals(m["sha256"])||!(latest instanceof Dictionary)||latest["sequence"]!=m["sequence"]||!(latest["sha256"] instanceof String)||!latest["sha256"].equals(m["sha256"])){return null;}
        latest=null;h=null;var raw=StringUtil.convertEncodedString(assembled,{:fromRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY,:toRepresentation=>StringUtil.REPRESENTATION_STRING_PLAIN_TEXT,:encoding=>StringUtil.CHAR_ENCODING_UTF8});return [m,raw];
    }
    // Transfer the raw value without retaining a second caller reference while
    // the cache verifies its durable commit after all raw chunks are written.
    function takeRaw(row){var raw=row[1];row[1]=null;return raw;}
    function processed(name,marker){store.write("sf.incoming."+name+".processed",token(marker));}
    function admitFeed(cache,now){return admitFeedForView(cache,now,null);}
    function admitFeedForView(cache,now,view){
        needsRestore=false;restoreSeal=cache.commit instanceof Dictionary?cache.commit["seal"]:null;
        var pending=store.read("sf.incoming.feed");var done=store.read("sf.incoming.feed.processed");if(!(pending instanceof Dictionary)||cache.packet!=null&&pending["sha256"] instanceof String&&done instanceof String&&token(pending).equals(done)){return false;}
        var commitKey=cache.commitKey;cache.releaseForTransfer(now);var accepted=false;
        var row=null;try{row=read("feed",cache.packet==null);if(row!=null&&row[0]["kind"] instanceof String&&row[0]["kind"].equals("feed")){cache.queueView=view;try{accepted=cache.accept(takeRaw(row),now);}finally{cache.queueView=null;}if(accepted||!cache.failure.equals("admission-retry")){processed("feed",row[0]);}}}catch(e){}
        row=null;pending=null;done=null;
        // A failed promotion restores the FULL durable feed under loaded UI
        // residency. Release reconstructible view state before strict old8KiB
        // raw reassembly; compact display context does not retain mission_name.
        // Rebind the strict durable result and rebuild its own optional scene
        // outside redraw. Durable raw, age, floor and accepted seal stay intact.
        // Successful source-only admission keeps its completed bitmap.
        if(!accepted){if(view!=null){view.clearForRestore();}cache.packet=null;cache.commit=null;cache.commitKey=commitKey;if(view==null){cache.restoreAccepted(now,restoreSeal);}else{needsRestore=true;}}
        return accepted;
    }
}

// One foreground admission owns one exact provisional token. Expensive strict
// parser/hash phases run on separate permitted event turns; atomic promotion is
// still delegated to NativeCacheCore.acceptPrepared.
(:extendedCode,:typecheck(false))
class NativeAdmissionJob {
    var cache;var view;var incoming;var now;var phase=0;var marker=null;var raw=null;var candidate=null;
    var restoreSeal=null;var commitKey=null;var prepared=null;var started=false;var accepted=false;var retry=false;var finished=false;
    function initialize(owner,target,instant){cache=owner;view=target;now=instant;incoming=new NativeIncoming(cache.store,cache.base);}
    function takeRaw(){var value=raw;raw=null;return value;}
    function current(){var latest=cache.store.read("sf.incoming.feed");return latest instanceof Dictionary&&marker instanceof Dictionary&&latest["sequence"]==marker["sequence"]&&latest["sha256"] instanceof String&&latest["sha256"].equals(marker["sha256"]);}
    function begin(){
        restoreSeal=cache.commit instanceof Dictionary?cache.commit["seal"]:null;commitKey=cache.commitKey;
        cache.releaseForTransfer(now);started=true;var row=incoming.read("feed",cache.packet==null);
        if(row==null||!(row[0]["kind"] instanceof String)||!row[0]["kind"].equals("feed")){retry=true;return false;}
        marker=row[0];raw=incoming.takeRaw(row);row=null;candidate=new NativeStagedBridgeFeed(raw,cache.store);return true;
    }
    function step(){
        if(finished){return true;}
        try{
            if(phase==0){if(!begin()){finish(false);return true;}}
            else if(phase==1){candidate.parseStage();}
            else if(phase==2){candidate.validationStage(now);}
            else if(phase==3){candidate.semanticStage();}
            else if(phase==4){candidate.wireStage();}
            else if(phase==5){candidate.identityStage();}
            else if(phase==6){
                if(!current()){retry=true;finish(false);return true;}
                prepared=cache.prepareCandidate(candidate,takeRaw(),now);
                if(prepared==null){retry=cache.failure.equals("admission-retry");if(!retry){try{incoming.processed("feed",marker);}catch(e){}}finish(false);return true;}
                // Return through the VM event boundary before allocating the
                // display contexts; no raw-feed argument remains on the stack.
            }
            else{
                if(!current()){retry=true;finish(false);return true;}
                cache.queueView=view;try{accepted=cache.finishCandidate(prepared,now);}finally{cache.queueView=null;}
                retry=!accepted&&cache.failure.equals("admission-retry");
                if(accepted||!retry){try{incoming.processed("feed",marker);}catch(e){}}
                finish(accepted);return true;
            }
            phase+=1;return false;
        }catch(e){var message=e.getErrorMessage();retry=message.equals("Bridge catalog incomplete");cache.failure=retry?"admission-retry":"update-rejected";if(marker!=null&&!retry){try{incoming.processed("feed",marker);}catch(ignored){}}finish(false);return true;}
    }
    function finish(ok){
        finished=true;candidate=null;raw=null;marker=null;prepared=null;
        if(!ok&&started){if(view!=null){view.clearForRestore();}cache.packet=null;cache.commit=null;cache.commitKey=commitKey;}
    }
    function abort(){if(finished&&accepted){return;}retry=true;finish(false);}
}
