import Toybox.Lang;

(:extendedCode, :typecheck(false))
function nativeSame(a,b){
    if(a==null||b==null){return a==null&&b==null;}
    if(a instanceof String){return b instanceof String&&a.equals(b);}
    if(a instanceof Number||a instanceof Long){return (b instanceof Number||b instanceof Long)&&a==b;}
    if(a instanceof Boolean){return b instanceof Boolean&&a==b;}
    if(a instanceof Array){if(!(b instanceof Array)||a.size()!=b.size()){return false;}for(var i=0;i<a.size();i+=1){if(!nativeSame(a[i],b[i])){return false;}}return true;}
    if(a instanceof Dictionary){if(!(b instanceof Dictionary)||a.size()!=b.size()){return false;}var keys=a.keys();for(var j=0;j<keys.size();j+=1){if(!b.hasKey(keys[j])||!nativeSame(a[keys[j]],b[keys[j]])){return false;}}return true;}return false;
}

// The current schema3 SFR1M feed keeps exact raw/hash/order semantics. A bounded
// immutable catalog is admitted before the common launch/clock validator runs.
(:extendedCode, :typecheck(false))
class NativeBridgeFeed extends NativeFeed {
    var catalogStore;var catalogData=null;var catalogOperatorId=null;var catalogOperatorShort=null;var catalogSiteId=null;var catalogSite=null;var catalogPin="";
    function ref(r,prefix){shape(r,["path","sha256","decodedBytes"],[]);if(!hex(r["sha256"])||!integer(r["decodedBytes"])||r["decodedBytes"]<1||r["decodedBytes"]>4096||!same(r["path"],prefix+"/"+r["sha256"]+(prefix.equals("rasters")?".sfr":".json"))){fail();}return r;}
    function equal(a,b){return nativeSame(a,b);}
    function dictionaryRow(key,row){
        var isSite=row instanceof Dictionary&&same(row["kind"],"site");shape(row,isSite?["kind","name","visual","sourcePosition","position","positionMode"]:["kind","name","visual"],["abbrev"]);if(row.hasKey("abbrev")){if(!same(row["kind"],"organization")||!same(key,catalogOperatorId)||!(row["abbrev"] instanceof String)||row["abbrev"].length()==0||!nativeNormalizedEdges(row["abbrev"])){fail();}catalogOperatorShort=row["abbrev"];row.remove("abbrev");}if(row["visual"]!=null){ref(row["visual"],"descriptors");}
        if(isSite){if(["fixed-source","mobile-reference-no-event"].indexOf(row["positionMode"])<0||!equal(row["position"],same(row["positionMode"],"fixed-source")?row["sourcePosition"]:null)){fail();}if(catalogSiteId!=null&&same(key,catalogSiteId)){catalogSite={"sourcePosition"=>row["sourcePosition"],"position"=>row["position"],"positionMode"=>row["positionMode"]};}row.remove("positionMode");row["position"]=null;}row["visual"]=null;return NativeFeed.dictionaryRow(key,row);
    }
    function header(d){

        var version=d["schemaVersion"];if(!integer(version)||version!=3){fail();}
        var required=["schemaVersion","catalogRevision","catalogDigest","catalogPath","unresolvedCatalogIds","launch","timingState","refreshPolicy","pollIntervalSeconds","sourceContentRevision","selection","providerTraversal","publisher","visualSelection","catalogSourceDigest","dictionaryMode"];
        required.add("rendererProfile");required.add("nativeTransfer");shape(d,required,["upcoming"]);
        if(!text(d["catalogRevision"],false)||d["catalogRevision"].length()==0||!hex(d["catalogDigest"])||!hex(d["sourceContentRevision"])||!hex(d["catalogSourceDigest"])||!same(d["dictionaryMode"],"immutable-catalog")||!same(d["catalogPath"],"wire3/catalogs/"+d["catalogDigest"]+".json")){fail();}
        if(d["visualSelection"]!=null){ref(d["visualSelection"],"descriptors");}if(!same(d["rendererProfile"],"SFR1M")){fail();}ref(d["nativeTransfer"],"descriptors");
        var catalog=catalogData;shape(catalog,["schemaVersion","catalogVersion","projection","entries","unresolved","visualSelection"],[]);
        if(!same(catalogPin,d["catalogDigest"])||!integer(catalog["schemaVersion"])||catalog["schemaVersion"]!=version||!same(catalog["catalogVersion"],d["catalogRevision"])||!same(catalog["projection"],"selected-display-motion-v3")||!equal(catalog["unresolved"],d["unresolvedCatalogIds"])||!equal(catalog["visualSelection"],d["visualSelection"])||!(catalog["entries"] instanceof Dictionary)){fail();}
        d["dictionaries"]=catalog["entries"];var l=d["launch"];if(l!=null&&(!equal(catalogSiteId,l["site_id"])||!equal(catalogOperatorId,l["operator_id"])||catalogOperatorShort!=null&&l["operator_abbrev"]!=null)){fail();}if(l==null&&catalogOperatorShort!=null){fail();}
        bridge={"version"=>version,"catalogDigest"=>d["catalogDigest"],"selection"=>d["visualSelection"],"transfer"=>d["nativeTransfer"],"site"=>catalogSite,"ids"=>l==null?null:[l["launch_id"],l["configuration_id"],l["operator_id"],l["site_id"],l["country_id"]]};catalogData=null;

    }
    function catalogHash(d){}
}


// Foreground preparation exposes validation phases as separate units. The
// packet remains provisional until every phase and durable promotion succeed.
(:extendedCode, :typecheck(false))
class NativePreparedBridgeFeed extends NativeBridgeFeed {
    var prepareNow;var preparePhase=0;var parser=null;var catalogRaw=null;var hashJob=null;var recordMask=0;var recordHashes=[null,null,null,null];var validationPhase=0;var validationIndex=0;var validationLast=null;var validationIds=null;var validationFuture=0;var deferredLaunch=false;var launchStage=0;var mustYield=false;
    function initialize(text,now,adapter){catalogStore=adapter;raw=text;prepareNow=now;}
    function prepareStep(){
        if(preparePhase==0){
            catalogPin=nativeHeaderText(raw,"catalogDigest");catalogOperatorId=nativeHeaderText(raw,"operator_id");catalogSiteId=nativeHeaderText(raw,"site_id");if(!hex(catalogPin)){fail();}
            // Parse the feed before loading the catalog. This keeps the
            // catalog's parsed objects out of the peak feed-parser live set.
            parser=new NativeIncrementalJson();parser.feedMode=true;parser.keepCatalogNames=!backgroundNames;parser.rowOwner=self;parser.nodeOwner=self;parser.rootOwner=self;parser.begin(raw,8192);preparePhase=1;return false;
        }
        if(preparePhase==1){if(!parser.step()){return false;}document=parser.result;spans=parser.spans;ignored=parser.ignored;parser=null;preparePhase=2;mustYield=true;return false;}
        if(preparePhase==2){
            // The selected row was syntax-checked during the first pass, then
            // released before parsing successors. Rebuild it from its original
            // span after the successor parser frames have been released.
            if(deferredLaunch&&launchStage==0){var span=spans["/launch"];parser=new NativeIncrementalJson();parser.feedMode=true;parser.begin(raw.substring(span[0],span[1]),8192);parser.path="/launch";launchStage=1;return false;}
            if(deferredLaunch&&launchStage==1){if(!parser.step()){return false;}document["launch"]=parser.result;parser=null;
                skipCatalogRefs=true;validateLaunch(document["launch"],prepareNow,false);skipCatalogRefs=false;
                // These fields have been checked above and are not used by
                // rendering, admission identity or persisted projection.
                var l=document["launch"];var discard=["mission_name","source_updated_utc","source_updated_subsecond","source_updated_iso","source_status_name"];for(var di=0;di<discard.size();di+=1){l.remove(discard[di]);}
                var timing=l["timing"];var drop=["source_net","source_precision_name","source_precision_abbrev","source_precision_description"];for(var ti=0;ti<drop.size();ti+=1){timing.remove(drop[ti]);}
                launchStage=2;mustYield=true;return false;}
            if(catalogRaw==null){catalogRaw=catalogStore.read("sf.obj."+catalogPin);if(!(catalogRaw instanceof String)||catalogRaw.length()>4096){throw new Lang.InvalidValueException("Bridge catalog incomplete");}hashJob=new NativeFeedHashJob(catalogRaw,[]);return false;}if(!hashJob.step()){return false;}if(!hashJob.result.equals(catalogPin)||hashJob.byteCount>4096){throw new Lang.InvalidValueException("Bridge catalog incomplete");}hashJob=null;parser=new NativeIncrementalJson();parser.feedMode=true;parser.catalogMode=true;parser.rowOwner=self;parser.begin(catalogRaw,4096);preparePhase=3;return false;}
        if(preparePhase==3){if(!parser.step()){return false;}catalogData=parser.result;catalogRaw=null;parser=null;preparePhase=4;mustYield=true;return false;}
        if(preparePhase==4){if(!validateStep()){return false;}validation=document["launch"]==null?null:document["launch"]["source_validated_utc"];stale=document["launch"]!=null&&document["launch"]["stale"];rescheduled=document["launch"]!=null&&document["launch"]["rescheduled"];}
        else if(preparePhase==5){if(hashJob==null){hashJob=new NativeFeedHashJob(raw,ignored);}if(!hashJob.step()){return false;}contentHash=hashJob.result;hashJob=null;}
        else if(preparePhase==6){if(hashJob==null){hashJob=new NativeFeedHashJob(raw,[]);}if(!hashJob.step()){return false;}wireHash=hashJob.result;hashJob=null;}
        else if(preparePhase==7){
            var launch=document["launch"];var allowed=launch==null?0:(launch["country_code"]==null?0:1)+(launch["site_location_name"]==null?0:2);
            if(recordMask>0&&(recordMask & allowed)!=recordMask){recordMask+=1;if(recordMask>=4){recordHash=recordHashes[0];preparePhase+=1;return true;}return false;}
            if(hashJob==null){if(recordMask==0){timingKey=timingIdentity();reminderData=reminderProjection();}var launchSpan=spans["/launch"];var changes=[];var ascent=spans["/launch/ascent_end"];if(ascent!=null){changes.add([launchSpan[0]+1,ascent[1]+1,""]);}
                var extra=spans["/launch/operator_abbrev"];if(extra!=null){changes.add([extra[0],extra[1],""]);}
                if((recordMask & 1)!=0){var country=spans["/launch/country_code"];if(country!=null){changes.add([country[0],country[1],"null"]);}}
                if((recordMask & 2)!=0){var site=spans["/launch/site_location_name"];if(site!=null){changes.add([site[0],site[1],"null"]);}}
                for(var i=0;i<ignored.size();i+=1){var item=ignored[i];if(item[0]>=launchSpan[0]&&item[1]<=launchSpan[1]){changes.add([item[0],item[1],"null"]);}}
                // The parser itself bounds ignored fields and launch metadata.
                for(var j=1;j<changes.size();j+=1){var value=changes[j];var k=j;while(k>0&&changes[k-1][0]>value[0]){changes[k]=changes[k-1];k-=1;}changes[k]=value;}
                var previous=launchSpan[0];for(var n=0;n<changes.size();n+=1){if(changes[n][0]<previous||changes[n][1]>launchSpan[1]){fail();}previous=changes[n][1];}
                hashJob=new NativeFeedHashJob(raw,changes);hashJob.setRange(launchSpan[0],launchSpan[1]);
            }
            if(!hashJob.step()){return false;}recordHashes[recordMask]=hashJob.result;hashJob=null;recordMask+=1;
            if(recordMask<4){return false;}recordHash=recordHashes[0];
        }
        else{return true;}
        preparePhase+=1;return preparePhase>=8;
    }

    // Canonical root order places publisher and refresh policy before upcoming.
    // Validate each successor as it closes, then retain its compact scene while
    // later rows parse. Duplicate and overall-count checks still run in the
    // validation phase before the candidate can be published.
    function sceneField(key,value){if(key.equals("launch")&&value!=null){deferredLaunch=true;return null;}return value;}
    function knownField(path,key){}
    function objectField(path,key,value){return value;}
    function arrayElement(path,index,value,depth){
        if(!path.equals("/upcoming")||!(value instanceof Dictionary)||value.hasKey("terminal")){return value;}
        document=parser.stack[0].result;
        if(!value.hasKey("sitePosition")||!value.hasKey("siteSource")){fail();}
        validateLaunch(value,prepareNow,true);var point=value["sitePosition"];var source=value["siteSource"];
        if(source!=null){shape(source,["path","sha256","decodedBytes"],[]);if(!hex(source["sha256"])||!same(source["path"],"sources/"+source["sha256"]+".json")||!integer(source["decodedBytes"])||source["decodedBytes"]<1||source["decodedBytes"]>1048576){fail();}}
        if(point!=null){if(source==null){fail();}shape(point,["encoding","latitude","longitude","units","qualification"],[]);if(!same(point["encoding"],"decimal-text-v1")||!same(point["units"],"degrees")||!same(point["qualification"],"unverified-reference")){fail();}decimal(point["latitude"],90);decimal(point["longitude"],180);}
        var site=point==null?null:{"positionMode"=>"fixed-source","position"=>point};return feedSceneRow(self,value,site,false);
    }
    function validateStep(){
        var now=prepareNow;
        if(validationPhase==0){
        var d=document;header(d);
        phase="publisher";var publisher=d["publisher"];shape(publisher,["instance","generation","selectionValidatedUtc"],[]);
        if(!hex(publisher["instance"])||!integer(publisher["generation"])||publisher["generation"]<1||publisher["generation"]>253402300799l||publisher["selectionValidatedUtc"]!=null&&(!utc(publisher["selectionValidatedUtc"])||publisher["selectionValidatedUtc"]>now)){fail();}
        phase="policy";var policy=d["refreshPolicy"];shape(policy,["normal_interval_seconds","near_interval_seconds","fast_interval_seconds","stale_cycles"],[]);
        var normal=policy["normal_interval_seconds"];var near=policy["near_interval_seconds"];var fast=policy["fast_interval_seconds"];
        var poll=d["pollIntervalSeconds"];if(!policyInteger(normal,300)||!policyInteger(near,300)||policyCompare(near,normal)>0||fast!=null&&(!policyInteger(fast,300)||policyCompare(fast,near)>0)||!policyInteger(policy["stale_cycles"],1)||!policyInteger(poll,300)||policyCompare(poll,normal)!=0&&policyCompare(poll,near)!=0&&(fast==null||policyCompare(poll,fast)!=0)){fail();}
        // Retain native-width policies byte-for-byte in v6 projections so old
        // accepted Long policies remain reopenable. They already calculate
        // safely (division, and bounded wake addition). An overflow policy was
        // never admitted by the old format; normalize its entire policy so
        // mixed Long/lexeme ordering still holds after calculation projection.
        if(normal instanceof NativeIntegerLexeme||near instanceof NativeIntegerLexeme||fast instanceof NativeIntegerLexeme||policy["stale_cycles"] instanceof NativeIntegerLexeme){var policyKeys=["normal_interval_seconds","near_interval_seconds","fast_interval_seconds","stale_cycles"];for(var pi=0;pi<policyKeys.size();pi+=1){policy[policyKeys[pi]]=policyValue(policy[policyKeys[pi]]);}d["pollIntervalSeconds"]=policyValue(poll);}
            phase="dictionaries";if(!(document["dictionaries"] instanceof Dictionary)||!(document["unresolvedCatalogIds"] instanceof Array)){fail();}validationPhase=1;return false;
        }
        if(validationPhase==1){var unresolved=document["unresolvedCatalogIds"];if(validationIndex<unresolved.size()){var gap=unresolved[validationIndex];if(!(gap instanceof String)||document["dictionaries"].hasKey(gap)||validationLast!=null&&validationLast.compareTo(gap)>=0){fail();}if(!id(gap,"configuration",false)&&!id(gap,"organization",false)&&!id(gap,"site",false)&&!id(gap,"country",false)){fail();}validationLast=gap;validationIndex+=1;return false;}validationPhase=2;return false;}
        if(validationPhase==2){var d=document;
        phase="catalog-hash";catalogHash(d);
        phase="selection";var selection=d["selection"];shape(selection,["acceptedRecords","includedRecords","scope","worldwideCompleteness"],[]);var launch=d["launch"];
        if(!integer(selection["acceptedRecords"])||selection["acceptedRecords"]<0||selection["acceptedRecords"]>128||!integer(selection["includedRecords"])||selection["includedRecords"]!=(launch==null?0:1)||selection["includedRecords"]>selection["acceptedRecords"]||!same(selection["scope"],"selected-launch")||!(selection["worldwideCompleteness"] instanceof Boolean)||selection["worldwideCompleteness"]){fail();}
        if(launch==null){if(!same(d["timingState"],"no-schedule")){fail();}}else{phase="launch";var refs=["configuration_id","operator_id","site_id","country_id"];for(var ri=0;ri<refs.size();ri+=1){var idValue=launch[refs[ri]];if(idValue!=null&&!d["dictionaries"].hasKey(idValue)&&d["unresolvedCatalogIds"].indexOf(idValue)<0){fail();}}}
            hasUpcomingMetadata=d.hasKey("upcoming");validationIds={};if(launch!=null){validationIds[launch["launch_id"]]=true;}
            if(hasUpcomingMetadata){phase="upcoming";var upcomingRows=d["upcoming"];if(!(upcomingRows instanceof Array)||upcomingRows.size()>128||upcomingRows.size()+(launch==null?0:1)>selection["acceptedRecords"]){fail();}terminalUpdates=[];}
            validationIndex=0;validationPhase=3;return false;
        }
        if(validationPhase==3){
            var d=document;if(hasUpcomingMetadata&&validationIndex<d["upcoming"].size()){
                var item=d["upcoming"][validationIndex];validationIndex+=1;
                if(item instanceof Dictionary&&item.hasKey("terminal")){shape(item,["terminal"],[]);var terminal=item["terminal"];shape(terminal,["launch_id","status","source_validated_utc","source_updated_utc","source_updated_subsecond"],[]);var tid=terminal["launch_id"];var checked=terminal["source_validated_utc"];var updated=terminal["source_updated_utc"];var sub=terminal["source_updated_subsecond"];if(!id(tid,"launch",false)||validationIds.hasKey(tid)||["cancelled","completed"].indexOf(terminal["status"])<0||!utc(checked)||checked>now||d["publisher"]["selectionValidatedUtc"]==null||updated!=null&&(!utc(updated)||updated>checked)||!integer(sub)||sub<0||sub>999999||updated==null&&sub!=0){fail();}validationIds[tid]=true;terminalUpdates.add(terminal);return false;}
                validationFuture+=1;if(validationFuture>2||!(item instanceof SceneContext)||validationIds.hasKey(item.launchId)){fail();}validationIds[item.launchId]=true;return false;
            }
            validationIds=null;validationPhase=4;return false;
        }
        var d=document;var launch=d["launch"];
        phase="traversal";var traversal=d["providerTraversal"];if(traversal!=null){shape(traversal,["query","complete","reportedCount","receivedUpcoming","detailRequests","worldwideCompleteness"],[]);if(!text(traversal["query"],false)||!(traversal["complete"] instanceof Boolean)||!(traversal["worldwideCompleteness"] instanceof Boolean)||traversal["worldwideCompleteness"]||!integer(traversal["reportedCount"])||traversal["reportedCount"]<0||traversal["reportedCount"]>1000000||!integer(traversal["receivedUpcoming"])||traversal["receivedUpcoming"]<0||traversal["receivedUpcoming"]>80||traversal["receivedUpcoming"]>traversal["reportedCount"]||traversal["complete"]&&traversal["receivedUpcoming"]!=traversal["reportedCount"]||!integer(traversal["detailRequests"])||traversal["detailRequests"]<0||traversal["detailRequests"]>4){fail();}}
        validationPhase=5;return true;
    }
    function metadata(previous,now){
        if(previous!=null&&launchId()!=null&&launchId().equals(previous.launchId())){if(validation<previous.validation){fail();}if(validation==previous.validation&&!sameRecordOrEnrichment(previous)){fail();}rescheduled=rescheduled||previous.rescheduled;if(!timingKey.equals(previous.timingKey)){var before=previous.refreshTarget();var after=refreshTarget();if(before==null||after==null||before!=after){rescheduled=true;}}if(validation==previous.validation){stale=stale||previous.stale;}}
        advance(now);
    }
    function sameRecordOrEnrichment(previous){
        if(recordHash.equals(previous.recordHash)){return true;}for(var mask=1;mask<=3;mask+=1){if(recordHashes[mask]!=null&&recordHashes[mask].equals(previous.recordHash)){return true;}}return false;
    }
    function disposePreparation(){if(parser!=null){parser.dispose();parser=null;}catalogRaw=null;hashJob=null;catalogData=null;catalogStore=null;raw="";document=null;spans=null;ignored=null;}
    function compact(){NativeFeed.compact();recordHashes=null;parser=null;catalogRaw=null;hashJob=null;catalogData=null;catalogStore=null;catalogOperatorId=null;catalogOperatorShort=null;catalogSiteId=null;catalogSite=null;catalogPin="";validationIds=null;validationLast=null;}
}

// SHA256 receives bounded raw slices without materializing a substituted feed.
// The caller supplies parser-discovered, ordered ignored spans for semantic
// identity; an empty list hashes the original wire unchanged.
(:extendedCode, :typecheck(false))
class NativeFeedHashJob {
    var text;var spans;var wire;var cursor=0;var limit;var spanIndex=0;var result=null;var byteCount=0;
    function initialize(value,ignored){text=value;spans=ignored;limit=value.length();wire=new NativeWireHash();}
    function setRange(start,end){cursor=start;limit=end;}
    function step(){
        var work=0;
        while(work<4){work+=1;var target=spanIndex<spans.size()?spans[spanIndex][0]:limit;
            if(cursor<target){var end=cursor+128;if(end>target){end=target;}wire.put(text.substring(cursor,end));cursor=end;continue;}
            if(spanIndex<spans.size()){wire.put(spans[spanIndex].size()>2?spans[spanIndex][2]:"null");cursor=spans[spanIndex][1];spanIndex+=1;continue;}
            result=wire.digest();byteCount=wire.count;text=null;wire=null;return true;
        }return false;
    }
}
