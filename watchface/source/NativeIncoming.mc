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
        var row=null;try{row=read("feed",cache.packet==null);if(row!=null&&row[0]["kind"] instanceof String&&row[0]["kind"].equals("feed")){accepted=cache.accept(takeRaw(row),now);if(!accepted&&!cache.failure.equals("")){try{store.write("sf.sync.admission",{"base"=>base,"reason"=>cache.failureReason});}catch(e){}}else if(accepted){try{store.remove("sf.sync.admission");}catch(e){}}if(accepted||!cache.failure.equals("admission-retry")){processed("feed",row[0]);}}}catch(e){NativeMetrics.failure(e.getErrorMessage());}
        row=null;pending=null;done=null;
        // A failed promotion restores the FULL durable feed under loaded UI
        // residency. Release reconstructible view state before strict old8KiB
        // raw reassembly; compact display context does not retain mission_name.
        // Rebind the strict durable result and rebuild its own optional scene
        // outside redraw. Durable raw, age, floor and accepted seal stay intact.
        // Successful source-only admission keeps its completed bitmap.
        if(!accepted){if(view!=null){view.clearForRestore();}cache.packet=null;cache.commit=null;cache.commitKey=commitKey;if(view==null){cache.restoreAccepted(now,restoreSeal);}else{needsRestore=true;}}
        NativeMetrics.sample("foreground-feed-admission");return accepted;
    }
}
