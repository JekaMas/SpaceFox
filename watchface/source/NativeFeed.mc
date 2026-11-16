import Toybox.Lang;

(:extendedCode, :typecheck(false))
class NativeFeed {
    var bridge=null;var presentation=null;var upcomingScenes=null;var terminalUpdates=[];var hasUpcomingMetadata=false;var reminderData=null;var backgroundNames=false;var skipCatalogRefs=false;var document;var raw;var contentHash;var wireHash;var spans;var ignored;var timingKey="";var recordHash="";var phase="header";var validation;var stale=false;var rescheduled=false;
    (:extendedCode) function reminderProjection(){
        var l=document["launch"];if(l==null||!same(l["status"],"pending")){return null;}var t=l["timing"];
        var target=refreshTarget();if(target==null||!(same(t["precision"],"exact")||same(t["precision"],"source-coarse")&&t["source_precision_id"]==1)){return null;}
        // Bounds accompanying a nominal target must actually contain it.
        if(t["window_start_utc"]!=null&&target<t["window_start_utc"]||t["window_end_utc"]!=null&&target>t["window_end_utc"]){return null;}
        var rocket=l["configuration_name"];var mission=l["mission_purpose"];var title=rocket instanceof String?rocket:"";
        if(mission instanceof String&&mission.length()>0){title+=(title.length()>0?" · ":"")+mission;}if(title.length()==0){title="Launch";}
        return {"id"=>l["launch_id"],"target"=>target,"precision"=>t["precision"],"title"=>title};
    }
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
    function dictionaryRow(key,row){
        if(!(row instanceof Dictionary)){fail();}var kind=row["kind"];if(!(kind instanceof String)||["configuration","organization","site","country"].indexOf(kind)<0||!id(key,kind,false)){fail();}shape(row,kind.equals("site")?["kind","name","visual","position","sourcePosition"]:["kind","name","visual"],[]);if(!text(row["name"],true)||row["visual"]!=null){fail();}if(kind.equals("site")){if(row["position"]!=null){fail();}var point=row["sourcePosition"];if(point!=null){shape(point,["encoding","latitude","longitude","units","qualification"],[]);if(!same(point["encoding"],"decimal-text-v1")||!same(point["units"],"degrees")||!same(point["qualification"],"unverified-reference")){fail();}decimal(point["latitude"],90);decimal(point["longitude"],180);}}return backgroundNames?true:row["name"];
    }
    function catalogName(id){var names=document["dictionaries"];if(!names.hasKey(id)){return null;}var name=names[id];return name instanceof String&&name.length()>64?name.substring(0,63)+"…":name;}
    (:extendedCode)
    function validateLaunch(l,now,successor){
        var optional=["source_updated_utc","source_updated_subsecond","source_updated_iso","source_status_id","source_status_name","site_name","country_name","operator_abbrev","ascent_end"];if(successor){optional.add("sitePosition");optional.add("siteSource");}
        shape(l,["launch_id","configuration_id","operator_id","site_id","country_id","configuration_name","operator_name","mission_name","mission_purpose","timing","status","source_validated_utc","rescheduled","stale","country_code","site_location_name"],optional);
        var fields=["launch_id","configuration_id","operator_id","site_id","country_id"];var kinds=["launch","configuration","organization","site","country"];
        for(var i=0;i<fields.size();i+=1){var value=l[fields[i]];if(!id(value,kinds[i],i>0)){fail();}if(!successor && !skipCatalogRefs && i>0 && value!=null && !document["dictionaries"].hasKey(value) && document["unresolvedCatalogIds"].indexOf(value)<0){fail();}}
        var texts=["configuration_name","operator_name","mission_name","mission_purpose","source_updated_iso","source_status_name","site_name","country_name","country_code","site_location_name","operator_abbrev"];for(var j=0;j<texts.size();j+=1){if(!text(l[texts[j]],true)){fail();}}
        var code=l["country_code"];if(code!=null){if(!(code instanceof String)||code.length()<2||code.length()>3){fail();}for(var ci=0;ci<code.length();ci+=1){if("ABCDEFGHIJKLMNOPQRSTUVWXYZ".find(code.substring(ci,ci+1))==null){fail();}}}
        if(document["publisher"]["selectionValidatedUtc"]==null||!successor&&document["publisher"]["selectionValidatedUtc"]<l["source_validated_utc"]){fail();}
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
        if(!successor && (["countdown","awaiting-update","uncertain"].indexOf(document["timingState"])<0||exact==same(document["timingState"],"uncertain"))){fail();}
    }
    // Preserve the original record hash and persisted v6 projections. During
    // same-validation admission compare the candidate against the hashes it
    // would have had with an enriched field null. The prior hash itself proves
    // that the earlier value was null; known values cannot change or disappear.
    function timingIdentity(){var l=document["launch"];if(l==null){return "empty";}var t=l["timing"];if(t["exact_utc"]!=null){return "exact:"+t["exact_utc"];}var h=new NativeWireHash();h.put("[\""+t["precision"]+"\",\""+(t["date_utc"]==null?"":t["date_utc"])+"\"");var fields=["window_start_utc","window_end_utc","nominal_utc"];for(var i=0;i<fields.size();i+=1){var v=t[fields[i]];h.put(","+(v==null?"null":v.toString()));}h.put("]");return h.digest();}
    function priorDocument(){
        var l=document["launch"];var row=l==null?null:{"launch_id"=>l["launch_id"],"configuration_id"=>l["configuration_id"],"timing"=>{"exact_utc"=>l["timing"]["exact_utc"]}};
        if(row!=null){var refresh=refreshTarget();if(row["timing"]["exact_utc"]==null&&refresh!=null){row["timing"]["refresh_utc"]=refresh;}}
        return {"catalogDigest"=>document["catalogDigest"],"refreshPolicy"=>document["refreshPolicy"],"launch"=>row};
    }
    function mutableWire(){var pieces=[];for(var i=0;i<ignored.size();i+=1){var span=ignored[i];pieces.add(raw.substring(span[0],span[1]));}return pieces;}
    function compact(){var pub=document["publisher"];document=priorDocument();document["publisher"]=pub;raw="";spans=null;ignored=null;}
    function target(){return document["launch"]==null?null:document["launch"]["timing"]["exact_utc"];}
    // Source precision MIN is an actionable nominal-minute target, just as in FeedScene.
    // Cached projections retain it separately so exact_utc remains source truthful.
    function refreshTarget(){var l=document["launch"];if(l==null){return null;}var t=l["timing"];if(t["exact_utc"]!=null){return t["exact_utc"];}if(t.hasKey("refresh_utc")){return t["refresh_utc"];}return t["precision"] instanceof String&&t["precision"].equals("source-coarse")&&t["source_precision_id"]==1?t["nominal_utc"]:null;}
    function launchId(){return document["launch"]==null?null:document["launch"]["launch_id"];}
    function interval(now){var p=document["refreshPolicy"];if(p["fast_interval_seconds"]!=null){return p["fast_interval_seconds"];}var t=refreshTarget();return t!=null && now>=t-7200 && now<=t+1800?p["near_interval_seconds"]:p["normal_interval_seconds"];}
    function advance(now){
        var checked=validation==null?document["publisher"]["selectionValidatedUtc"]:validation;if(checked==null){return;}var p=document["refreshPolicy"];var age=now-checked;if(age<0){age=0;}var cycles=p["stale_cycles"];
        if(p["fast_interval_seconds"]!=null){stale=stale||age/p["fast_interval_seconds"]>=cycles;return;}
        stale=stale||age/p["normal_interval_seconds"]>=cycles;var t=refreshTarget();if(t!=null){var end=now<t+1800?now:t+1800;stale=stale||end>=t-7200&&end>=checked&&(end-checked)/p["near_interval_seconds"]>=cycles;}
    }
}

// A v6 sealed projection is only used after the durable raw SHA is verified.
// The foreground independently reparses all raw bytes before UI activation.
(:extendedCode, :typecheck(false))
class NativeCachedPacket extends NativeFeed {
    function initialize(marker){
        var prior=marker["prior"];var d=prior[0];document={"publisher"=>marker["publisher"],"catalogDigest"=>d["catalogDigest"],"refreshPolicy"=>d["refreshPolicy"],"launch"=>d["launch"]};
        raw="";spans=null;ignored=null;contentHash=marker["contentHash"];wireHash=marker["wireHash"];timingKey=prior[1];recordHash=prior[2];validation=marker["validation"];stale=marker["stale"];rescheduled=marker["rescheduled"];phase="cached";
    }
}
