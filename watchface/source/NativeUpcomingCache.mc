import Toybox.Lang;

// Small derived queue from already admitted packets. It never owns the feed's
// active/recovery slots. Writes happen only during feed admission, not redraw.
(:extendedCode,:typecheck(false))
class NativeUpcomingCache {
    var store;var base;var instance;var key;
    function initialize(adapter,url,owner){store=adapter;base=url;instance=owner;var h=new NativeWireHash();h.put(url);key="sf.upcoming."+h.digest();}
    function seal(value){var h=new NativeCanonical();h.emit(value);return h.digest();}
    function validNumber(v){return (v instanceof Number||v instanceof Long)&&v>= -62135596800l&&v<=253402301699l;}
    function validIdentity(value,kind,optional){
        if(!(value instanceof String)){return false;}if(value.length()==0){return optional;}var a=value.find(":");if(a==null||a==0){return false;}var rest=value.substring(a+1,value.length());var b=rest.find(":");return b!=null&&rest.substring(0,b).equals(kind)&&b<rest.length()-1&&nativeNormalizedEdges(value.substring(0,a))&&nativeNormalizedEdges(rest.substring(b+1,rest.length()));
    }
    function validRow(row){
        if(!(row instanceof Dictionary)){return false;}
        var keys=["id","rocket","operator","operatorShort","purpose","site","modelId","operatorId","siteId","pointText","target","precision","date","retentionDeadline","orderingUtc","sourceValidated","freshnessPolicy","rescheduled","stale","sourceHold"];
        if(row.size()!=keys.size()&&!(row.size()==keys.size()+1&&row.hasKey("displayTarget"))){return false;}if(row.hasKey("displayTarget")&&(!validNumber(row["displayTarget"])||!(row["precision"] instanceof String)||row["precision"].equals("exact"))){return false;}for(var i=0;i<keys.size();i+=1){if(!row.hasKey(keys[i])){return false;}}
        var texts=["id","rocket","operator","operatorShort","purpose","site","modelId","operatorId","siteId","precision"];
        for(var j=0;j<texts.size();j+=1){var value=row[texts[j]];if(!(value instanceof String)){return false;}}
        if(!validIdentity(row["id"],"launch",false)||!validIdentity(row["modelId"],"configuration",true)||!validIdentity(row["operatorId"],"organization",true)||!validIdentity(row["siteId"],"site",true)||["exact","minute","date","window","unknown","source-coarse"].indexOf(row["precision"])<0){return false;}
        if(!(row["stale"] instanceof Boolean)||!(row["rescheduled"] instanceof Boolean)||!(row["sourceHold"] instanceof Boolean)||!validNumber(row["sourceValidated"])){return false;}
        if(row["date"]!=null){if(!(row["date"] instanceof String)){return false;}try{nativeUtcDay(row["date"]);}catch(e){return false;}}
        var target=row["target"];var deadline=row["retentionDeadline"];var order=row["orderingUtc"];
        if(target!=null&&!validNumber(target)||deadline!=null&&!validNumber(deadline)||order!=null&&!validNumber(order)||target==null&&deadline!=null||target!=null&&(deadline==null||deadline<target+900)){return false;}
        var p=row["freshnessPolicy"];if(!(p instanceof Dictionary)||p.size()!=4){return false;}var n=p["normal_interval_seconds"];var near=p["near_interval_seconds"];var fast=p["fast_interval_seconds"];var cycles=p["stale_cycles"];
        if(!(n instanceof Number||n instanceof Long)||!(near instanceof Number||near instanceof Long)||!(cycles instanceof Number||cycles instanceof Long)||n<300||near<300||near>n||cycles<1||fast!=null&&(!(fast instanceof Number||fast instanceof Long)||fast<300||fast>near)){return false;}
        var point=row["pointText"];if(point!=null){if(!(point instanceof Array)||point.size()!=2||!(point[0] instanceof String)||!(point[1] instanceof String)||point[0].length()>64||point[1].length()>64){return false;}try{var lon=point[0].toFloat();var lat=point[1].toFloat();if(lon< -180||lon>180||lat< -90||lat>90){return false;}}catch(e){return false;}}
        return true;
    }
    function save(scenes){
        var rows=[];for(var i=0;i<scenes.size()&&rows.size()<3;i+=1){var scene=scenes[i];if(scene!=null&&scene.sourceValidated!=null){var row=scene.cacheRow();if(!validRow(row)){throw new Lang.InvalidValueException("Invalid future queue row");}rows.add(row);}}
        var value={"v"=>1,"base"=>base,"instance"=>instance,"rows"=>rows};var digest=seal(value);var old=store.read(key);
        if(old instanceof Dictionary&&old["seal"] instanceof String&&old["seal"].equals(digest)&&old["value"] instanceof Dictionary&&nativeSame(old["value"],value)&&seal(old["value"]).equals(digest)){return;}
        store.write(key,{"value"=>value,"seal"=>digest});var readback=store.read(key);if(!(readback instanceof Dictionary)||!(readback["seal"] instanceof String)||!readback["seal"].equals(digest)||!(readback["value"] instanceof Dictionary)||!nativeSame(readback["value"],value)||!seal(readback["value"]).equals(digest)){throw new Lang.InvalidValueException("Future queue readback failed");}
    }
    function load(){
        var marker=store.read(key);if(!(marker instanceof Dictionary)||marker.size()!=2||!(marker["seal"] instanceof String)||!nativeHex(marker["seal"])||!(marker["value"] instanceof Dictionary)){return [];}
        var value=marker["value"];if(value.size()!=4||value["v"]!=1||!(value["base"] instanceof String)||!value["base"].equals(base)||!(value["instance"] instanceof String)||!value["instance"].equals(instance)||!(value["rows"] instanceof Array)||value["rows"].size()>3||!seal(value).equals(marker["seal"])){return [];}
        var result=[];for(var i=0;i<value["rows"].size();i+=1){var row=value["rows"][i];if(!validRow(row)){return [];}var data={};var keys=row.keys();for(var j=0;j<keys.size();j+=1){data[keys[j]]=row[keys[j]];}var point=row["pointText"];data["point"]=point==null?null:[point[0].toFloat(),point[1].toFloat()];result.add(new SceneContext(data));}return result;
    }
}
