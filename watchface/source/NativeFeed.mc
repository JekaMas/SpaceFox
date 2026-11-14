import Toybox.Lang;

(:typecheck(false))
class NativeFeed {
    var bridge=null;var presentation=null;var backgroundNames=false;var document;var raw;var contentHash;var wireHash;var spans;var ignored;var timingKey="";var recordHash="";var phase="header";var validation;var stale=false;var rescheduled=false;
    function initialize(text,now){raw=text;parse(text);validate(now);validation=document["launch"]==null?null:document["launch"]["source_validated_utc"];stale=document["launch"]!=null && document["launch"]["stale"];rescheduled=document["launch"]!=null && document["launch"]["rescheduled"];contentHash=semanticHash();wireHash=hashRaw(raw);timingKey=timingIdentity();recordHash=recordIdentity(0);NativeMetrics.sample("feed-validated");}
    function hashRaw(text){var wire=new NativeWireHash();wire.put(text);return wire.digest();}
    function parse(text){var parser=new NativeJson();parser.feedMode=true;parser.keepCatalogNames=!backgroundNames;parser.rowOwner=self;document=parser.parse(text,8192);spans=parser.spans;ignored=parser.ignored;}
    function fail(){throw new Lang.InvalidValueException("Invalid current feed:"+phase);}
    function shape(value,required,optional){if(!(value instanceof Dictionary)){fail();}var keys=value.keys();for(var i=0;i<required.size();i+=1){if(!value.hasKey(required[i])){fail();}}for(var j=0;j<keys.size();j+=1){if(required.indexOf(keys[j])<0 && optional.indexOf(keys[j])<0){fail();}}}
    function integer(value){return value instanceof Number || value instanceof Long;}
    function metadataInteger(value){return integer(value)?value>=0:value instanceof NativeIntegerLexeme&&value.nonnegative();}
    function policyText(value){return value instanceof NativeIntegerLexeme?value.text:value.toString();}
    function policyCompare(a,b){var x=policyText(a);var y=policyText(b);return x.length()==y.length()?x.compareTo(y):x.length()-y.length();}
    function policyInteger(value,minimum){return metadataInteger(value)&&policyCompare(value,minimum)>=0;}
    // Calculation-only projection. D=MAX_UTC-MIN_UTC=315537897599.
    // All elapsed ages are <=D; replacing a positive divisor or cycles >D by
    // D+1 preserves both due and floor(age/interval)>=cycles exactly. Validate
    // original ordering/equality first, before saturation can erase distinctions.
    // Original numeric lexemes remain in raw/content/record hashes and Storage
    // chunks, never a custom lexeme instance in persisted projection metadata.
    function policyValue(value){return value==null?null:policyCompare(value,315537897600l)>=0?315537897600l:value;}
    function utc(value){return integer(value) && value>= -62135596800l && value<=253402300799l;}
    function text(value,optional){return value==null?optional:(value instanceof String);}
    function same(value,expected){return value instanceof String && value.equals(expected);}
    function hex(value){return nativeHex(value);}
    function id(value,kind,optional){
        if(value==null){return optional;}if(!(value instanceof String)){return false;}var a=value.find(":");if(a==null||a==0){return false;}var rest=value.substring(a+1,value.length());var b=rest.find(":");return b!=null && rest.substring(0,b).equals(kind) && b<rest.length()-1&&nativeNormalizedEdges(value.substring(0,a))&&nativeNormalizedEdges(rest.substring(b+1,rest.length()));
    }
    (:extendedCode)
    function decimal(value,limit){
        if(!(value instanceof String)||value.length()==0||value.length()>64){fail();}var negative=value.substring(0,1).equals("-");var text=negative?value.substring(1,value.length()):value;var mark=text.find("E");if(mark==null){mark=text.find("e");}var mantissa=mark==null?text:text.substring(0,mark);var exponent=0l;
        if(mark!=null){var exp=text.substring(mark+1,text.length());var signed=exp.length()>0&&["+","-"].indexOf(exp.substring(0,1))>=0;var digits=signed?exp.substring(1,exp.length()):exp;if(digits.length()==0||digits.length()>19||digits.length()==19&&digits.compareTo("9223372036854775807")>0){fail();}for(var e=0;e<digits.length();e+=1){if("0123456789".find(digits.substring(e,e+1))==null){fail();}}exponent=exp.toLong();if(exponent< -1999999999999999997l||exponent>999999999999999999l){fail();}}
        var dot=mantissa.find(".");var integer=dot==null?mantissa:mantissa.substring(0,dot);var fraction=dot==null?"":mantissa.substring(dot+1,mantissa.length());if(integer.length()==0||integer.length()>1&&integer.substring(0,1).equals("0")||dot!=null&&fraction.length()==0){fail();}var coefficient=integer+fraction;for(var c=0;c<coefficient.length();c+=1){if("0123456789".find(coefficient.substring(c,c+1))==null){fail();}}while(coefficient.length()>1&&coefficient.substring(0,1).equals("0")){coefficient=coefficient.substring(1,coefficient.length());}exponent-=fraction.length();if(exponent< -1999999999999999997l||exponent>999999999999999999l){fail();}var adjusted=exponent+coefficient.length()-1;
        var canonical="";if(exponent<=0&&adjusted>= -6){var point=coefficient.length()+exponent;if(point<=0){canonical="0.";while(point<0){canonical+="0";point+=1;}canonical+=coefficient;}else if(exponent<0){canonical=coefficient.substring(0,point.toNumber())+"."+coefficient.substring(point.toNumber(),coefficient.length());}else{canonical=coefficient;}}
        else{canonical=coefficient.substring(0,1)+(coefficient.length()>1?"."+coefficient.substring(1,coefficient.length()):"")+"E"+(adjusted>=0?"+":"")+adjusted;}
        if(!(negative?"-"+canonical:canonical).equals(value)){fail();}if(coefficient.equals("0")){return;}var bound=limit.toString();if(adjusted>bound.length()-1){fail();}if(adjusted==bound.length()-1){var whole=coefficient;while(whole.length()<bound.length()){whole+="0";}var prefix=whole.substring(0,bound.length());if(prefix.compareTo(bound)>0){fail();}if(prefix.equals(bound)){for(var tail=bound.length();tail<whole.length();tail+=1){if(!whole.substring(tail,tail+1).equals("0")){fail();}}}}
    }
    function date(value){try{nativeUtcDay(value);return true;}catch(e){return false;}}
    function header(d){fail();}
    function catalogHash(d){}
    (:extendedCode)
    function validate(now){
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
        phase="dictionaries";var rows=d["dictionaries"];var unresolved=d["unresolvedCatalogIds"];if(!(rows instanceof Dictionary)||!(unresolved instanceof Array)){fail();}
        // Each row was fully schema-checked by dictionaryRow while parsing.
        var last=null;for(var k=0;k<unresolved.size();k+=1){var gap=unresolved[k];if(!(gap instanceof String)||rows.hasKey(gap)||last!=null && last.compareTo(gap)>=0){fail();}if(!id(gap,"configuration",false)&&!id(gap,"organization",false)&&!id(gap,"site",false)&&!id(gap,"country",false)){fail();}last=gap;}
        phase="catalog-hash";catalogHash(d);
        phase="selection";var selection=d["selection"];shape(selection,["acceptedRecords","includedRecords","scope","worldwideCompleteness"],[]);var launch=d["launch"];
        if(!integer(selection["acceptedRecords"])||selection["acceptedRecords"]<0||selection["acceptedRecords"]>128||!integer(selection["includedRecords"])||selection["includedRecords"]!=(launch==null?0:1)||selection["includedRecords"]>selection["acceptedRecords"]||!same(selection["scope"],"selected-launch")||!(selection["worldwideCompleteness"] instanceof Boolean)||selection["worldwideCompleteness"]){fail();}
        if(launch==null){if(!same(d["timingState"],"no-schedule")){fail();}}else{phase="launch";validateLaunch(launch,now);}
        if(launch!=null){launch["source_updated_iso"]=null;launch["timing"]["source_net"]=null;}phase="traversal";var traversal=d["providerTraversal"];if(traversal!=null){shape(traversal,["query","complete","reportedCount","receivedUpcoming","detailRequests","worldwideCompleteness"],[]);if(!text(traversal["query"],false)||!(traversal["complete"] instanceof Boolean)||!(traversal["worldwideCompleteness"] instanceof Boolean)||traversal["worldwideCompleteness"]||!integer(traversal["reportedCount"])||traversal["reportedCount"]<0||traversal["reportedCount"]>1000000||!integer(traversal["receivedUpcoming"])||traversal["receivedUpcoming"]<0||traversal["receivedUpcoming"]>80||traversal["receivedUpcoming"]>traversal["reportedCount"]||traversal["complete"]&&traversal["receivedUpcoming"]!=traversal["reportedCount"]||!integer(traversal["detailRequests"])||traversal["detailRequests"]<0||traversal["detailRequests"]>4){fail();}}
    }
    function dictionaryRow(key,row){
        if(!(row instanceof Dictionary)){fail();}var kind=row["kind"];if(!(kind instanceof String)||["configuration","organization","site","country"].indexOf(kind)<0||!id(key,kind,false)){fail();}shape(row,kind.equals("site")?["kind","name","visual","position","sourcePosition"]:["kind","name","visual"],[]);if(!text(row["name"],true)||row["visual"]!=null){fail();}if(kind.equals("site")){if(row["position"]!=null){fail();}var point=row["sourcePosition"];if(point!=null){shape(point,["encoding","latitude","longitude","units","qualification"],[]);if(!same(point["encoding"],"decimal-text-v1")||!same(point["units"],"degrees")||!same(point["qualification"],"unverified-reference")){fail();}decimal(point["latitude"],90);decimal(point["longitude"],180);}}return backgroundNames?true:row["name"];
    }
    function catalogName(id){var names=document["dictionaries"];if(!names.hasKey(id)){return null;}var name=names[id];return name instanceof String&&name.length()>64?name.substring(0,63)+"…":name;}
    (:extendedCode)
    function validateLaunch(l,now){
        shape(l,["launch_id","configuration_id","operator_id","site_id","country_id","configuration_name","operator_name","mission_name","mission_purpose","timing","status","source_validated_utc","rescheduled","stale","country_code","site_location_name"],["source_updated_utc","source_updated_subsecond","source_updated_iso","source_status_id","source_status_name","site_name","country_name","operator_abbrev","ascent_end"]);
        var fields=["launch_id","configuration_id","operator_id","site_id","country_id"];var kinds=["launch","configuration","organization","site","country"];
        for(var i=0;i<fields.size();i+=1){var value=l[fields[i]];if(!id(value,kinds[i],i>0)){fail();}if(i>0 && value!=null && !document["dictionaries"].hasKey(value) && document["unresolvedCatalogIds"].indexOf(value)<0){fail();}}
        var texts=["configuration_name","operator_name","mission_name","mission_purpose","source_updated_iso","source_status_name","site_name","country_name","country_code","site_location_name","operator_abbrev"];for(var j=0;j<texts.size();j+=1){if(!text(l[texts[j]],true)){fail();}}
        var code=l["country_code"];if(code!=null){if(!(code instanceof String)||code.length()<2||code.length()>3){fail();}for(var ci=0;ci<code.length();ci+=1){if("ABCDEFGHIJKLMNOPQRSTUVWXYZ".find(code.substring(ci,ci+1))==null){fail();}}}
        if(document["publisher"]["selectionValidatedUtc"]==null||document["publisher"]["selectionValidatedUtc"]<l["source_validated_utc"]){fail();}
        if(!utc(l["source_validated_utc"])||l["source_validated_utc"]>now||["pending","unknown","started"].indexOf(l["status"])<0||!(l["rescheduled"] instanceof Boolean)||!(l["stale"] instanceof Boolean)){fail();}
        if(l["source_updated_utc"]!=null&&(!utc(l["source_updated_utc"])||l["source_updated_utc"]>l["source_validated_utc"])){fail();}if(l.hasKey("source_updated_subsecond")&&(!integer(l["source_updated_subsecond"])||l["source_updated_subsecond"]<0||l["source_updated_subsecond"]>999999)){fail();}if(l["source_status_id"]!=null&&!metadataInteger(l["source_status_id"])){fail();}
        if(l["source_updated_subsecond"]!=null&&l["source_updated_subsecond"]>0&&l["source_updated_utc"]==null||!nativeSourceIso(l["source_updated_iso"],l["source_updated_utc"],l["source_updated_subsecond"]==null?0:l["source_updated_subsecond"])){fail();}
        var t=l["timing"];shape(t,["precision","exact_utc","date_utc","window_start_utc","window_end_utc"],["nominal_utc","source_net","source_precision_id","source_precision_name","source_precision_abbrev","source_precision_description"]);
        if(["exact","date","window","unknown","source-coarse"].indexOf(t["precision"])<0){fail();}var utcFields=["exact_utc","window_start_utc","window_end_utc","nominal_utc"];for(var k=0;k<utcFields.size();k+=1){if(t[utcFields[k]]!=null&&!utc(t[utcFields[k]])){fail();}}
        if(t["date_utc"]!=null&&!date(t["date_utc"])){fail();}var exact=t["precision"].equals("exact");if(exact!=(t["exact_utc"]!=null)||t["precision"].equals("date")&&t["date_utc"]==null||t["precision"].equals("window")&&t["window_start_utc"]==null&&t["window_end_utc"]==null||t["window_start_utc"]!=null&&t["window_end_utc"]!=null&&t["window_start_utc"]>t["window_end_utc"]||t["precision"].equals("unknown")&&(t["date_utc"]!=null||t["window_start_utc"]!=null||t["window_end_utc"]!=null)){fail();}
        if(t["source_precision_id"]!=null&&!metadataInteger(t["source_precision_id"])){fail();}var optionalText=["source_net","source_precision_name","source_precision_abbrev","source_precision_description"];for(var n=0;n<optionalText.size();n+=1){if(!text(t[optionalText[n]],true)){fail();}}
        if(!nativeSourceIso(t["source_net"],t["nominal_utc"],null)||t["precision"].equals("source-coarse")&&(t["source_net"]==null||t["nominal_utc"]==null)){fail();}
        if(exact&&(t["nominal_utc"]!=null&&t["nominal_utc"]!=t["exact_utc"]||t["window_start_utc"]!=null&&t["exact_utc"]<t["window_start_utc"]||t["window_end_utc"]!=null&&t["exact_utc"]>t["window_end_utc"])){fail();}
        if(t["date_utc"]!=null){var start=nativeUtcDay(t["date_utc"])*86400;if(t["window_start_utc"]!=null&&t["window_start_utc"]>start+86399||t["window_end_utc"]!=null&&t["window_end_utc"]<start||exact&&(t["exact_utc"]<start||t["exact_utc"]>=start+86400)){fail();}}
        var a=l["ascent_end"];if(a!=null){shape(a,["launch_id","target_utc","end_utc","source_url","reviewed_utc"],[]);var target=exact?t["exact_utc"]:(t["precision"].equals("source-coarse")&&t["source_precision_id"]==1?t["nominal_utc"]:null);var url=a["source_url"];if(!same(a["launch_id"],l["launch_id"])||target==null||!utc(a["target_utc"])||a["target_utc"]!=target||!utc(a["end_utc"])||a["end_utc"]<target||!utc(a["reviewed_utc"])||a["reviewed_utc"]>now||!(url instanceof String)||url.length()<9||url.length()>512||!url.substring(0,8).equals("https://")||url.find("#")!=null||url.find("@")!=null){fail();}var slash=url.substring(8,url.length()).find("/");var hostEnd=slash==null?url.length():slash+8;if(hostEnd==8){fail();}var authority=url.substring(8,hostEnd);var colon=authority.find(":");var host=colon==null?authority:authority.substring(0,colon);if(host.length()==0){fail();}var hostChars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-";for(var ui=0;ui<host.length();ui+=1){if(hostChars.find(host.substring(ui,ui+1))==null){fail();}}if(colon!=null){var port=authority.substring(colon+1,authority.length());if(port.length()<1||port.length()>5){fail();}for(var pi=0;pi<port.length();pi+=1){if("0123456789".find(port.substring(pi,pi+1))==null){fail();}}}var pathChars="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._~/%?=&+-";for(var xi=hostEnd;xi<url.length();xi+=1){if(pathChars.find(url.substring(xi,xi+1))==null){fail();}}}
        if(["countdown","awaiting-update","uncertain"].indexOf(document["timingState"])<0||exact==same(document["timingState"],"uncertain")){fail();}
    }
    function rawSpan(hash,key){var span=spans[key];hash.range(raw,span[0],span[1]);}
    function semanticHash(){var hash=new NativeWireHash();var start=0;for(var i=0;i<ignored.size();i+=1){var span=ignored[i];hash.range(raw,start,span[0]);hash.put("null");start=span[1];}hash.range(raw,start,raw.length());return hash.digest();}
    // Preserve the original record hash and persisted v6 projections. During
    // same-validation admission compare the candidate against the hashes it
    // would have had with an enriched field null. The prior hash itself proves
    // that the earlier value was null; known values cannot change or disappear.
    function recordRange(hash,start,end,extra,mask){
        var fields=[spans["/launch/country_code"],extra,spans["/launch/site_location_name"]];
        for(var i=0;i<fields.size();i+=1){var item=fields[i];if(item==null||item[1]<=start||item[0]>=end){continue;}if(item[0]<start||item[1]>end){fail();}hash.range(raw,start,item[0]);if(i!=1){hash.put((mask & (i==0?1:2))!=0?"null":raw.substring(item[0],item[1]));}start=item[1];}hash.range(raw,start,end);
    }
    function recordIdentity(mask){var span=spans["/launch"];var hash=new NativeWireHash();var start=span[0];var ascent=spans["/launch/ascent_end"];var extra=spans["/launch/operator_abbrev"];if(ascent!=null){hash.range(raw,start,start+1);start=ascent[1]+1;}for(var i=0;i<ignored.size();i+=1){var item=ignored[i];if(item[0]<start||item[1]>span[1]){continue;}recordRange(hash,start,item[0],extra,mask);hash.put("null");start=item[1];}recordRange(hash,start,span[1],extra,mask);return hash.digest();}
    function sameRecordOrEnrichment(previous){if(recordHash.equals(previous.recordHash)){return true;}var row=document["launch"];var allowed=(row["country_code"]==null?0:1)+(row["site_location_name"]==null?0:2);for(var mask=1;mask<=3;mask+=1){if((mask & allowed)==mask&&recordIdentity(mask).equals(previous.recordHash)){return true;}}return false;}
    function timingIdentity(){var l=document["launch"];if(l==null){return "empty";}var t=l["timing"];if(t["exact_utc"]!=null){return "exact:"+t["exact_utc"];}var h=new NativeWireHash();h.put("[\""+t["precision"]+"\",\""+(t["date_utc"]==null?"":t["date_utc"])+"\"");var fields=["window_start_utc","window_end_utc","nominal_utc"];for(var i=0;i<fields.size();i+=1){var v=t[fields[i]];h.put(","+(v==null?"null":v.toString()));}h.put("]");return h.digest();}
    function priorDocument(){
        var l=document["launch"];var row=l==null?null:{"launch_id"=>l["launch_id"],"configuration_id"=>l["configuration_id"],"timing"=>{"exact_utc"=>l["timing"]["exact_utc"]}};
        return {"catalogDigest"=>document["catalogDigest"],"refreshPolicy"=>document["refreshPolicy"],"launch"=>row};
    }
    function mutableWire(){var pieces=[];for(var i=0;i<ignored.size();i+=1){var span=ignored[i];pieces.add(raw.substring(span[0],span[1]));}return pieces;}
    function compact(){var pub=document["publisher"];document=priorDocument();document["publisher"]=pub;raw="";spans=null;ignored=null;}
    function target(){return document["launch"]==null?null:document["launch"]["timing"]["exact_utc"];}
    function launchId(){return document["launch"]==null?null:document["launch"]["launch_id"];}
    function interval(now){var p=document["refreshPolicy"];if(p["fast_interval_seconds"]!=null){return p["fast_interval_seconds"];}var t=target();return t!=null && now>=t-7200 && now<=t+1800?p["near_interval_seconds"]:p["normal_interval_seconds"];}
    function advance(now){
        var checked=validation==null?document["publisher"]["selectionValidatedUtc"]:validation;if(checked==null){return;}var p=document["refreshPolicy"];var age=now-checked;if(age<0){age=0;}var cycles=p["stale_cycles"];
        if(p["fast_interval_seconds"]!=null){stale=stale||age/p["fast_interval_seconds"]>=cycles;return;}
        stale=stale||age/p["normal_interval_seconds"]>=cycles;var t=target();if(t!=null){var end=now<t+1800?now:t+1800;stale=stale||end>=t-7200&&end>=checked&&(end-checked)/p["near_interval_seconds"]>=cycles;}
    }
    function metadata(previous,now){
        if(previous!=null&&launchId()!=null&&launchId().equals(previous.launchId())){if(validation<previous.validation){fail();}if(validation==previous.validation&&!sameRecordOrEnrichment(previous)){fail();}rescheduled=rescheduled||previous.rescheduled;if(!timingKey.equals(previous.timingKey)){rescheduled=true;}if(validation==previous.validation){stale=stale||previous.stale;}}
        advance(now);
    }
}

// A v6 sealed projection is only used after the durable raw SHA is verified.
// The foreground independently reparses all raw bytes before UI activation.
(:typecheck(false))
class NativeCachedPacket extends NativeFeed {
    function initialize(marker){
        var prior=marker["prior"];var d=prior[0];document={"publisher"=>marker["publisher"],"catalogDigest"=>d["catalogDigest"],"refreshPolicy"=>d["refreshPolicy"],"launch"=>d["launch"]};
        raw="";spans=null;ignored=null;contentHash=marker["contentHash"];wireHash=marker["wireHash"];timingKey=prior[1];recordHash=prior[2];validation=marker["validation"];stale=marker["stale"];rescheduled=marker["rescheduled"];phase="cached";
    }
}
