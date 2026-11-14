(:extendedCode, :typecheck(false))
class NativeRenderSource {
    var store;var base;var ready;var serial;
    function initialize(adapter,url,bridge){
        store=adapter;base=url;ready=false;serial=0;
        if(bridge==null||!(bridge["transfer"] instanceof Dictionary)){return;}
        try {
            var head=store.read("sf.batch.head");var marker=store.read("sf.batch.pending");var transfer=bridge["transfer"];
            ready=head instanceof Dictionary && head["base"] instanceof String && head["base"].equals(base) &&
                head["pending"]==false && marker instanceof Dictionary && marker["base"] instanceof String &&
                marker["base"].equals(base) && marker["pending"]==false && head["catalogDigest"] instanceof String &&
                head["catalogDigest"].equals(bridge["catalogDigest"]) && head["transfer"] instanceof Dictionary &&
                head["transfer"]["sha256"] instanceof String && head["transfer"]["sha256"].equals(transfer["sha256"]);
            if(ready && (head["serial"] instanceof Number || head["serial"] instanceof Long) && head["serial"]>=0){serial=head["serial"];}
        } catch(e) { ready=false; }
    }
}
