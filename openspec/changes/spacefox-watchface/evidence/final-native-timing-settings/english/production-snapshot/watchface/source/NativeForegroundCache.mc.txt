import Toybox.Lang;
import Toybox.StringUtil;

(:extendedCode, :typecheck(false))
class NativeCache extends NativeCacheCore {
    function initialize(url,adapter){NativeCacheCore.initialize(url,adapter);backgroundMode=false;}
    function parseFeed(raw,now){return new NativeBridgeFeed(raw,now,store);}
    function readCommit(marker,now){
        if(backgroundMode){return NativeCacheCore.readCommit(marker,now);}
        if(checkedProjection(marker,now)==null){return null;}
        var value=store.read("sf.feed."+marker["slot"]);if(!(value instanceof Dictionary)||!(value["base"] instanceof String)||!value["base"].equals(base)){return null;}var raw=readRaw(value,marker["slot"]);NativeMetrics.sample("load-raw-assembled");if(!(raw instanceof String)){return null;}
        if(!rawHash(raw).equals(marker["rawHash"])){return null;}var original=null;var current=raw;
        if(!marker["wireHash"].equals(marker["rawHash"])){var spans=value["mutableSpans"];original=pieces(raw,spans);current=replaceSpans(raw,spans,marker["mutable"]);}
        value=null;raw=null;var p=parseFeed(current,now);current=null;
        if(!p.wireHash.equals(marker["wireHash"])||!p.contentHash.equals(marker["contentHash"])||p.validation!=marker["validation"]||!priorHash(priorFrom(p)).equals(marker["priorHash"])){return null;}
        // The inverse uses spans discovered by the FULL current-feed parser,
        // not cached positions. It must reproduce the unchanged durable raw.
        if(original!=null&&!hashReplaced(p.raw,p.ignored,original).equals(marker["rawHash"])){return null;}
        var pub=p.document["publisher"];var bound=marker["publisher"];if(!pub["instance"].equals(bound["instance"])||pub["generation"]!=bound["generation"]||pub["selectionValidatedUtc"]!=bound["selectionValidatedUtc"]||p.stale&&!marker["stale"]||p.rescheduled&&!marker["rescheduled"]){return null;}
        p.stale=marker["stale"];p.rescheduled=marker["rescheduled"];p.advance(now);p.presentation=feedScene(p,now);p.compact();return p;
    }
    function pieces(raw,spans){
        if(!(spans instanceof Array)||spans.size()>16){throw new Lang.InvalidValueException("Missing raw mutable spans");}var result=[];var previous=0;for(var i=0;i<spans.size();i+=1){var span=spans[i];if(!(span instanceof Array)||span.size()!=2||!(span[0] instanceof Number)||!(span[1] instanceof Number)||span[0]<previous||span[1]<=span[0]||span[1]>raw.length()){throw new Lang.InvalidValueException("Invalid raw mutable spans");}result.add(raw.substring(span[0],span[1]));previous=span[1];}return result;
    }
    function hashReplaced(raw,spans,replacements){
        pieces(raw,spans);if(!(replacements instanceof Array)||replacements.size()!=spans.size()){throw new Lang.InvalidValueException("Missing inverse witness");}var hash=new NativeWireHash();var start=0;for(var i=0;i<spans.size();i+=1){if(!(replacements[i] instanceof String)){throw new Lang.InvalidValueException("Invalid inverse witness");}hash.range(raw,start,spans[i][0]);hash.put(replacements[i]);start=spans[i][1];}hash.range(raw,start,raw.length());var digest=hash.digest();if(hash.count>8192){throw new Lang.InvalidValueException("Inverse raw byte bound");}return digest;
    }
    function replaceSpans(raw,spans,replacements){
        pieces(raw,spans);if(!(replacements instanceof Array)||replacements.size()!=spans.size()){throw new Lang.InvalidValueException("Missing raw metadata witness");}var result="";var start=0;for(var i=0;i<spans.size();i+=1){if(!(replacements[i] instanceof String)||replacements[i].length()>8192){throw new Lang.InvalidValueException("Invalid raw metadata witness");}var span=spans[i];result+=raw.substring(start,span[0])+replacements[i];if(result.length()>8192){throw new Lang.InvalidValueException("Raw metadata witness bound");}start=span[1];}result+=raw.substring(start,raw.length());return result;
    }

    function readRaw(value,slot){
        if(value["v"]!=2||!(value["chunks"] instanceof Number||value["chunks"] instanceof Long)||value["chunks"]<1||value["chunks"]>16){return null;}
        // ByteArray growth avoids concatenation retaining two almost-complete
        // strings under the ordinary61KiB background heap. Convert once.
        var bytes=[]b;
        for(var part=0;part<value["chunks"];part+=1){
            var piece=store.read("sf.feed."+slot+"."+part);if(!(piece instanceof String)||piece.length()>512){return null;}
            var size=0;for(var offset=0;offset<piece.length();offset+=64){var end=offset+64;if(end>piece.length()){end=piece.length();}var chunk=piece.substring(offset,end).toUtf8Array();size+=chunk.size();if(size>2048||bytes.size()+chunk.size()>8192){return null;}bytes.addAll(chunk);}
        }
        NativeMetrics.sample("load-bytes-assembled");
        return StringUtil.convertEncodedString(bytes,{:fromRepresentation=>StringUtil.REPRESENTATION_BYTE_ARRAY,:toRepresentation=>StringUtil.REPRESENTATION_STRING_PLAIN_TEXT,:encoding=>StringUtil.CHAR_ENCODING_UTF8});
    }
}
