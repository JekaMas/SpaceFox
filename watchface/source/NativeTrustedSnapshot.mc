import Toybox.Lang;

// One ordering rule for accepted RAM and persisted publisher snapshots.
// A later source-validation epoch wins; within one epoch the same publisher
// instance must advance its generation. Cross-instance ties are not ordered.
(:background, :extendedCode, :typecheck(false))
function nativePublisherNewer(a,b,allowEqual) {
    if(!(a instanceof Dictionary)||!(b instanceof Dictionary)){return false;}
    var at=a["selectionValidatedUtc"];var bt=b["selectionValidatedUtc"];
    var ag=a["generation"];var bg=b["generation"];
    if((at!=null&&!(at instanceof Number||at instanceof Long))||
       (bt!=null&&!(bt instanceof Number||bt instanceof Long))||
       !(ag instanceof Number||ag instanceof Long)||!(bg instanceof Number||bg instanceof Long)||
       !(a["instance"] instanceof String)||!(b["instance"] instanceof String)){return false;}
    // A source epoch may legitimately be absent before the first validated
    // traversal. A real epoch advances that state; null never replaces one.
    if(at==null&&bt!=null){return false;}if(at!=null&&bt==null){return true;}
    if(at!=null&&bt!=null&&at!=bt){return at>bt;}
    if(!a["instance"].equals(b["instance"])){return false;}
    return allowEqual?ag>=bg:ag>bg;
}

// The publisher supplies this bounded positional schema over HTTPS. Two slots
// keep the previously selected snapshot intact until the new pointer is saved.
(:background, :extendedCode, :typecheck(false))
class NativeTrustedStore {
    // Save progresses candidate -> slot -> published pointer. A failed write
    // never moves the durable active pointer to a partially written slot.
    const IDLE=0;const CANDIDATE=1;const SLOT_WRITTEN=2;const COMMITTED=3;
    var phase=0;var store;var base;var token=null;
    function initialize(adapter,url){store=adapter==null?new NativeStore():adapter;base=url;}
    function activeKey(){return "sf.snapshot.active:"+base;}
    function slotKey(slot){return "sf.snapshot."+slot+":"+base;}
    function marker(){return store.read(activeKey());}
    function load(){return loadMarker(marker());}
    function loadMarker(marker){
        if(!(marker instanceof Dictionary)||!(marker["base"] instanceof String)||!marker["base"].equals(base)||!(marker["slot"] instanceof Number)||marker["slot"]<0||marker["slot"]>1){return null;}
        token=marker["sequence"];var value=store.read(slotKey(marker["slot"]));
        if(!(value instanceof Array)||value.size()!=7||value[0]!=1){return null;}return value;
    }
    function integer(value){return value==null?null:value.toLong();}
    function normalize(value){
        var publisher=value[1];publisher["generation"]=integer(publisher["generation"]);publisher["selectionValidatedUtc"]=integer(publisher["selectionValidatedUtc"]);
        var policy=value[2];var names=["normal_interval_seconds","near_interval_seconds","fast_interval_seconds","stale_cycles"];for(var n=0;n<names.size();n+=1){var k=names[n];policy[k]=integer(policy[k]);}
        var rows=[];if(value[3]!=null){rows.add(value[3]);}rows.addAll(value[4]);
        for(var i=0;i<rows.size();i+=1){var row=rows[i];var nums=[10,13,14,15,20];for(var j=0;j<nums.size();j+=1){var k=nums[j];row[k]=integer(row[k]);}row[16]=policy;}
        for(var t=0;t<value[5].size();t+=1){var wrapper=value[5][t];wrapper["source_validated_utc"]=integer(wrapper["source_validated_utc"]);var terminal=wrapper["terminal"];if(terminal instanceof Dictionary){var tn=["source_validated_utc","source_updated_utc","source_updated_subsecond"];for(var z=0;z<tn.size();z+=1){terminal[tn[z]]=integer(terminal[tn[z]]);}}}
        var bridge=value[6];if(bridge!=null){bridge["version"]=bridge["version"].toNumber();var revision=bridge["artRevision"];if(revision instanceof Number || revision instanceof Long || revision instanceof Float || revision instanceof Double){bridge["artRevision"]=revision.toNumber();}var refs=[bridge["selection"],bridge["transfer"]];for(var r=0;r<refs.size();r+=1){if(refs[r]!=null){refs[r]["decodedBytes"]=refs[r]["decodedBytes"].toNumber();}}}
    }
    function writeCandidate(slot,value){
        if(phase!=CANDIDATE){throw new Lang.InvalidValueException("No snapshot candidate");}
        store.write(slotKey(slot),value);phase=SLOT_WRITTEN;
    }
    function publishCandidate(slot,sequence,publisher){
        if(phase!=SLOT_WRITTEN){throw new Lang.InvalidValueException("Snapshot slot is incomplete");}
        var stamp={"generation"=>publisher["generation"],"instance"=>publisher["instance"],"selectionValidatedUtc"=>publisher["selectionValidatedUtc"]};
        store.write(activeKey(),{"base"=>base,"slot"=>slot,"sequence"=>sequence,"publisher"=>stamp});token=sequence;phase=COMMITTED;
    }
    function save(value){
        if(!(value instanceof Array)||value.size()!=7||value[0]!=1){return false;}
        normalize(value);return saveNormalized(value);
    }
    function saveNormalized(value){
        var prior=marker();
        // A delayed response or stale CDN object must not publish an older
        // generation over the last complete slot, including after restart.
        var current=null;var stamp=prior instanceof Dictionary?prior["publisher"]:null;
        // Old schema-1 pointers did not store a small publisher stamp. Read
        // their complete slot until the first newer commit publishes the stamp
        // atomically with the pointer. Newer ordinary responses compare
        // the stamp without holding two complete snapshots in memory.
        if(stamp==null&&prior!=null){current=loadMarker(prior);if(current!=null){stamp=current[1];}}
        if(stamp!=null&&!nativePublisherNewer(value[1],stamp,false)){
            if(!nativePublisherNewer(value[1],stamp,true)){return false;}
            // A tied immutable revision is successful only when all normalized
            // facts match. It never moves the pointer or restamps source age.
            if(current==null){current=loadMarker(prior);}
            if(current==null){return false;}normalize(current);return nativeSame(value,current);
        }
        current=null;
        phase=CANDIDATE;
        var slot=0;var sequence=1;
        if(prior instanceof Dictionary&&prior["base"] instanceof String&&prior["base"].equals(base)&&(prior["sequence"] instanceof Number||prior["sequence"] instanceof Long)){sequence=prior["sequence"]+1;}
        if(prior instanceof Dictionary&&prior["base"] instanceof String&&prior["base"].equals(base)&&prior["slot"]==0){slot=1;}
        writeCandidate(slot,value);publishCandidate(slot,sequence,value[1]);
        // Keep only future-ordering facts needed by the request policy.
        var targets=[];var rows=[];if(value[3]!=null){rows.add(value[3]);}rows.addAll(value[4]);
        for(var i=0;i<rows.size();i+=1){var target=rows[i][14];if(target!=null&&targets.indexOf(target)<0){targets.add(target);}}
        try{store.write("sf.transfer.plan:"+base,{"base"=>base,"sequence"=>sequence,"targets"=>targets});}catch(ignore){}return true;
    }
}

// SceneContext and the existing renderer remain the presentation owners.
(:extendedCode, :typecheck(false))
class NativeTrustedPacket extends NativeFeed {
    function ref(r,prefix){shape(r,["path","sha256","decodedBytes"],[]);if(!hex(r["sha256"])||!integer(r["decodedBytes"])||r["decodedBytes"]<1||r["decodedBytes"]>4096||!same(r["path"],prefix+"/"+r["sha256"]+(prefix.equals("rasters")?".sfr":".json"))){fail();}return r;}
    function scene(row,policy){
        if(row==null){return null;}if(!(row instanceof Array)||row.size()!=22){throw new Lang.InvalidValueException("Invalid snapshot row");}
        var keys=["id","rocket","operator","operatorShort","purpose","site","modelId","operatorId","siteId","point","target","precision","date","retentionDeadline","orderingUtc","sourceValidated","freshnessPolicy","rescheduled","stale","sourceHold","displayTarget","reminderEligible"];
        var d={};for(var i=0;i<keys.size();i+=1){d[keys[i]]=row[i];}
        var point=row[9];if(point instanceof Array&&point.size()==2){d["pointText"]=point;d["point"]=[point[0].toFloat(),point[1].toFloat()];}
        d["freshnessPolicy"]=policy;return new SceneContext(d);
    }
    function initialize(value){
        if(!(value instanceof Array)||value.size()!=7||value[0]!=1||!(value[1] instanceof Dictionary)||!(value[2] instanceof Dictionary)||!(value[4] instanceof Array)||!(value[5] instanceof Array)){throw new Lang.InvalidValueException("Invalid snapshot");}
        var policy=value[2];presentation=scene(value[3],policy);upcomingScenes=[];
        for(var i=0;i<value[4].size();i+=1){upcomingScenes.add(scene(value[4][i],policy));}
        terminalUpdates=value[5];bridge=value[6];document={"publisher"=>value[1],"refreshPolicy"=>policy,"launch"=>presentation==null?null:{"launch_id"=>presentation.launchId}};
        validation=presentation==null?null:presentation.sourceValidated;stale=presentation==null?false:presentation.stale;rescheduled=presentation==null?false:presentation.rescheduled;
    }
    function refreshTarget(){return presentation==null?null:presentation.retentionTarget;}
    function advance(now){if(presentation!=null){presentation.advanceFreshness(now);stale=presentation.stale;}}
    function compact(){}
}
