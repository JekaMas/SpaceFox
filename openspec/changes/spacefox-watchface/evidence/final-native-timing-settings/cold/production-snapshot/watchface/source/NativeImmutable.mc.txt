import Toybox.Lang;

(:background, :typecheck(false))
function nativeHeaderText(raw,key){var prefix="\""+key+"\":\"";var at=raw.find(prefix);if(at==null){return null;}var rest=raw.substring(at+prefix.length(),raw.length());var end=rest.find("\"");return end==null?null:rest.substring(0,end);}

// Raw <=4KiB immutable strings only. No parsed scene, native object or bitmap is
// written by background. Active/recovery/feed pins protect referenced content.
(:background, :typecheck(false))
class NativeImmutable {
    var store;
    function initialize(adapter){store=adapter;}
    function raw(ref){
        var value=store.read("sf.obj."+ref["sha256"]);if(!(value instanceof String)||value.length()>4096){return null;}var h=new NativeWireHash();h.put(value);var digest=h.digest();if(h.count>4096||ref["decodedBytes"]!=null&&h.count!=ref["decodedBytes"]||!digest.equals(ref["sha256"])){return null;}return value;
    }
    function protectedHash(digest){
        // Called only when a candidate eviction is actually needed. Scan one
        // durable record at a time; do not retain a second whole active +
        // recovery + pending graph during a raw response allocation.
        var keys=["sf.commit","sf.recovery","sf.raster.active","sf.raster.recovery","sf.batch.head","sf.batch.refs"];
        for(var i=0;i<keys.size();i+=1){var m=store.read(keys[i]);if(m instanceof Dictionary){if(m["prior"] instanceof Array&&m["prior"].size()==3&&m["prior"][0] instanceof Dictionary&&m["prior"][0]["catalogDigest"] instanceof String&&m["prior"][0]["catalogDigest"].equals(digest)){return true;}if(m["catalogDigest"] instanceof String&&m["catalogDigest"].equals(digest)){return true;}if(m["transfer"] instanceof Dictionary&&m["transfer"]["sha256"] instanceof String&&m["transfer"]["sha256"].equals(digest)){return true;}if(m["refs"] instanceof Array){for(var j=0;j<m["refs"].size();j+=1){var r=m["refs"][j];if(r instanceof Dictionary&&r["sha256"] instanceof String&&r["sha256"].equals(digest)){return true;}if(r instanceof Array&&r.size()==3&&r[1] instanceof String&&r[1].equals(digest)){return true;}}}}}
        return false;
    }
    function put(ref,value){
        if(!(value instanceof String)||value.length()>4096||!nativeHex(ref["sha256"])){return false;}var h=new NativeWireHash();h.put(value);var digest=h.digest();if(h.count<1||h.count>4096||ref["decodedBytes"]!=null&&h.count!=ref["decodedBytes"]||!digest.equals(ref["sha256"])){return false;}if(raw(ref)!=null){return true;}
        var index=store.read("sf.objects");if(index==null){index=[];}if(!(index instanceof Array)||index.size()>96){return false;}var total=h.count;var next=[];
        for(var i=0;i<index.size();i+=1){var r=index[i];if(!(r instanceof Array)||r.size()!=2||!nativeHex(r[0])||!(r[1] instanceof Number||r[1] instanceof Long)||r[1]<1||r[1]>4096){return false;}if(!r[0].equals(ref["sha256"])){total+=r[1];next.add(r);}}
        var retained=[];for(var j=0;j<next.size();j+=1){var r=next[j];if((total>393216||next.size()-j+retained.size()>=96)&&!protectedHash(r[0])){store.remove("sf.obj."+r[0]);total-=r[1];}else{retained.add(r);}}
        if(total>393216||retained.size()>=96){return false;}retained.add([ref["sha256"],h.count]);store.write("sf.objects",retained);store.write("sf.obj."+ref["sha256"],value);if(raw(ref)==null){return false;}return true;
    }
}

// This scanner schedules only finite, same-host, digest-addressed provisional
// downloads. Full closed JSON/schema/selection validation remains foreground.
(:background, :typecheck(false))
class NativeBatch {
    var store;var base;var immutable;var head=null;var refs=null;
    function initialize(adapter,url){store=adapter;base=url;immutable=new NativeImmutable(store);var value=store.read("sf.batch.head");if(value instanceof Dictionary&&value["base"] instanceof String&&value["base"].equals(base)){head=value;}}
    function text(raw,key){return nativeHeaderText(raw,key);}
    function pinned(raw,key){var prefix="\""+key+"\":{";var at=raw.find(prefix);if(at==null){return null;}var tail=raw.substring(at+prefix.length(),raw.length());var end=tail.find("}");if(end==null||end>240){return null;}var part=tail.substring(0,end);var hash=text(part,"sha256");if(!nativeHex(hash)||!text(part,"path").equals("descriptors/"+hash+".json")){return null;}return {"path"=>"descriptors/"+hash+".json","sha256"=>hash,"decodedBytes"=>null};}
    function begin(raw){
        var hash=text(raw,"catalogDigest");if(!nativeHex(hash)){return false;}var transfer=pinned(raw,"nativeTransfer");if(transfer==null){return false;}head={"base"=>base,"catalogDigest"=>hash,"transfer"=>transfer,"pending"=>true};store.write("sf.batch.head",head);store.write("sf.batch.pending",{"base"=>base,"pending"=>true});refs=null;return true;
    }
    // Settings switch schedules only this source-bound selected closure. The
    // existing immutable active/recovery pins survive an incomplete new view.
    // A quota failure between the two provisional writes is retryable: a matching
    // head is not evidence that its pending marker was persisted.
    function select(bridge){
        var transfer=bridge["transfer"];if(transfer==null){return;}
        if(head!=null&&head["catalogDigest"] instanceof String&&head["catalogDigest"].equals(bridge["catalogDigest"])&&head["transfer"] instanceof Dictionary&&head["transfer"]["sha256"] instanceof String&&head["transfer"]["sha256"].equals(transfer["sha256"])){if(head["pending"]==true){var pending=store.read("sf.batch.pending");if(!(pending instanceof Dictionary)||!(pending["base"] instanceof String)||!pending["base"].equals(base)||pending["pending"]!=true){store.write("sf.batch.pending",{"base"=>base,"pending"=>true});}}return;}
        head={"base"=>base,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>transfer,"pending"=>true};refs=null;store.write("sf.batch.head",head);store.write("sf.batch.pending",{"base"=>base,"pending"=>true});
    }
    function parseIndex(raw){
        var prefix="\"objects\":[";var at=raw.find(prefix);if(at==null){throw new Lang.InvalidValueException("Batch objects absent");}at+=prefix.length();var rows=[];var total=0;var seen={};
        while(at<raw.length()&&!raw.substring(at,at+1).equals("]")){
            if(rows.size()>0){if(!raw.substring(at,at+1).equals(",")){throw new Lang.InvalidValueException("Batch comma");}at+=1;}
            if(at+70>=raw.length()||!raw.substring(at,at+1).equals("[")){throw new Lang.InvalidValueException("Batch row");}var kind=raw.substring(at+1,at+2);if(!kind.equals("0")&&!kind.equals("1")||!raw.substring(at+2,at+4).equals(",\"")){throw new Lang.InvalidValueException("Batch kind");}var digest=raw.substring(at+4,at+68);if(!nativeHex(digest)||!raw.substring(at+68,at+70).equals("\",")){throw new Lang.InvalidValueException("Batch digest");}at+=70;var start=at;while(at<raw.length()&&"0123456789".find(raw.substring(at,at+1))!=null){at+=1;}var number=raw.substring(start,at);if(number.length()==0||number.length()>4||number.substring(0,1).equals("0")||!raw.substring(at,at+1).equals("]")){throw new Lang.InvalidValueException("Batch size");}at+=1;var size=number.toNumber();if(size<1||size>4096||seen.hasKey(digest)){throw new Lang.InvalidValueException("Batch bound");}seen[digest]=true;total+=size;var path=kind.equals("1")?"rasters/"+digest+".sfr":"descriptors/"+digest+".json";rows.add({"path"=>path,"sha256"=>digest,"decodedBytes"=>size});if(rows.size()>40||total>114688){throw new Lang.InvalidValueException("Batch complete bound");}
        }
        if(at>=raw.length()||!raw.substring(at,at+1).equals("]")){throw new Lang.InvalidValueException("Batch end");}return rows;
    }
    function sameRefs(rows){var saved=store.read("sf.batch.refs");if(!(saved instanceof Dictionary)||saved.size()!=2||!(saved["base"] instanceof String)||!saved["base"].equals(base)||!(saved["refs"] instanceof Array)||saved["refs"].size()!=rows.size()){return false;}for(var i=0;i<rows.size();i+=1){var a=saved["refs"][i];var b=rows[i];if(!(a instanceof Dictionary)||a.size()!=3||!(a["path"] instanceof String)||!a["path"].equals(b["path"])||!(a["sha256"] instanceof String)||!a["sha256"].equals(b["sha256"])||!(a["decodedBytes"] instanceof Number||a["decodedBytes"] instanceof Long)||a["decodedBytes"]!=b["decodedBytes"]){return false;}}return true;}
    function next(){
        if(head==null){return null;}var catalog={"path"=>"wire3/catalogs/"+head["catalogDigest"]+".json","sha256"=>head["catalogDigest"],"decodedBytes"=>null};if(immutable.raw(catalog)==null){return catalog;}if(head["transfer"]!=null){var raw=immutable.raw(head["transfer"]);if(raw==null){return head["transfer"];}if(refs==null){refs=parseIndex(raw);if(!sameRefs(refs)){store.write("sf.batch.refs",{"base"=>base,"refs"=>refs});}}for(var i=0;i<refs.size();i+=1){if(immutable.raw(refs[i])==null){return refs[i];}}}if(head["pending"]!=false){head["pending"]=false;head.remove("refs");store.write("sf.batch.head",head);store.write("sf.batch.pending",{"base"=>base,"pending"=>false});}return null;
    }
}
