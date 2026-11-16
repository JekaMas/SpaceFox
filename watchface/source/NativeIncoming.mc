import Toybox.Lang;
import Toybox.StringUtil;
// Foreground only: the provisional pointer is not an admission receipt.
(:extendedCode, :typecheck(false))
class NativeIncoming {
    var store;var base;
    function initialize(adapter,url){store=adapter;base=url;}
    function token(marker){return marker["sha256"]+":"+marker["sequence"];}
    function validFeedMarker(m){if(!(m instanceof Dictionary)||m["v"]!=2||!(m["base"] instanceof String)||!m["base"].equals(base)||!nativeHex(m["sha256"])||!(m["parts"] instanceof Array)||m["parts"].size()<1||m["parts"].size()>16||!(m["sequence"] instanceof Number||m["sequence"] instanceof Long)||m["sequence"]<1||m["sequence"]>253402300799l||!(m["bytes"] instanceof Number)||m["bytes"]<1||m["bytes"]>8192||!(m["kind"] instanceof String)||!m["kind"].equals("feed")){return false;}for(var i=0;i<m["parts"].size();i+=1){var slot=m["parts"][i];if(!(slot instanceof Number)||slot<0||slot>1){return false;}}return true;}
    // Transfer the raw value without retaining a second caller reference while
    // the cache verifies its durable commit after all raw chunks are written.
    function takeRaw(row){var raw=row[1];row[1]=null;return raw;}
    function processed(name,marker){store.write("sf.incoming."+name+".processed",token(marker));}
    // A complete but rejected candidate is cooled down instead of reparsed on
    // every wake. A later retry is allowed: future-dated source timestamps can
    // become valid without a new wire generation. Missing catalogs never mark
    // this rejection and remain immediately retryable.
    function rejected(marker,now){store.write("sf.incoming.feed.rejected",{"token"=>token(marker),"until"=>now+300});}
    function clearRejected(marker){var old=store.read("sf.incoming.feed.rejected");if(old instanceof Dictionary&&old["token"] instanceof String&&old["token"].equals(token(marker))){store.remove("sf.incoming.feed.rejected");}}
    function defer(marker,now){store.write("sf.incoming.feed.deferred",{"token"=>token(marker),"until"=>now+300});}
    function clearDeferred(){var old=store.read("sf.incoming.feed.deferred");if(old!=null){store.remove("sf.incoming.feed.deferred");}}
}

// One stored provisional part per foreground callback. The marker and final
// digest are rechecked before exposing the assembled input to the parser.
(:typecheck(false))
class NativeIncomingReadJob {
    var owner;var key;var marker;var hash;var assembled=[]b;var total=0;var part=0;var result=null;var done=false;
    function initialize(incoming){
        owner=incoming;key="sf.incoming.feed";marker=owner.store.read(key);
        if(!owner.validFeedMarker(marker)){done=true;return;}
        hash=new NativeWireHash();
    }
    function step(){
        if(done){return true;}
        if(part<marker["parts"].size()){
            var slot=marker["parts"][part];if(!(slot instanceof Number)||slot<0||slot>1){done=true;return true;}var s=owner.store.read(key+"."+slot+"."+part);if(!(s instanceof String)||s.length()>512){done=true;return true;}
            var b=StringUtil.convertEncodedString(s,{:fromRepresentation=>StringUtil.REPRESENTATION_STRING_PLAIN_TEXT,:toRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY,:encoding=>StringUtil.CHAR_ENCODING_UTF8});if(b.size()>2048||total+b.size()>8192){done=true;return true;}hash.update(b);total+=b.size();assembled.addAll(b);part+=1;return false;
        }
        var latest=owner.store.read(key);if(total==marker["bytes"]&&hash.digest().equals(marker["sha256"])&&latest instanceof Dictionary&&latest["sequence"]==marker["sequence"]&&latest["sha256"] instanceof String&&latest["sha256"].equals(marker["sha256"])){
            var raw=StringUtil.convertEncodedString(assembled,{:fromRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY,:toRepresentation=>StringUtil.REPRESENTATION_STRING_PLAIN_TEXT,:encoding=>StringUtil.CHAR_ENCODING_UTF8});result=[marker,raw];
        }
        assembled=null;hash=null;done=true;return true;
    }
}
