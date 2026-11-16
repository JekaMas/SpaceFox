import Toybox.Lang;

(:extendedCode,:typecheck(false))
function feedScene(packet,now){
    if(packet==null||packet.document["launch"]==null){return null;}
    packet.advance(now);
    if(packet.presentation!=null){packet.presentation.stale=packet.stale;packet.presentation.rescheduled=packet.rescheduled;return packet.presentation;}
    var row=packet.document["launch"];var siteData=packet.bridge==null?null:packet.bridge["site"];
    var current=feedSceneRow(packet,row,siteData,true);
    packet.upcomingScenes=[];
    var rows=packet.document["upcoming"];
    if(rows instanceof Array){for(var i=0;i<rows.size();i+=1){var item=rows[i];if(item instanceof SceneContext){packet.upcomingScenes.add(item);continue;}if(item.hasKey("terminal")){continue;}var pos=item["sitePosition"];var site=pos==null?null:{"positionMode"=>"fixed-source","position"=>pos};packet.upcomingScenes.add(feedSceneRow(packet,item,site,false));}}
    return current;
}

(:extendedCode,:typecheck(false))
function feedSceneRow(packet,row,siteData,selected){
    var dictionaries=packet.document["dictionaries"];
    var rocket=row["configuration_name"];var operator=row["operator_name"];var site=row["site_location_name"]==null?row["site_name"]:row["site_location_name"];
    if(selected&&rocket==null&&row["configuration_id"]!=null&&dictionaries.hasKey(row["configuration_id"])){rocket=packet.catalogName(row["configuration_id"]);}
    if(selected&&operator==null&&row["operator_id"]!=null&&dictionaries.hasKey(row["operator_id"])){operator=packet.catalogName(row["operator_id"]);}
    if(selected&&site==null&&row["site_id"]!=null&&dictionaries.hasKey(row["site_id"])){site=packet.catalogName(row["site_id"]);}
    var operatorShort=row["operator_abbrev"];if(selected&&operatorShort==null){operatorShort=packet.catalogOperatorShort;}
    // Keep full source text in the accepted feed; derive only a compact place
    // label by removing an exact operator prefix and comma-delimited region.
    if(site!=null){var comma=site.find(",");if(comma!=null&&comma>0){site=site.substring(0,comma);}var prefix=row["operator_name"];if(prefix!=null&&!prefix.equals("")&&site.find(prefix+" ")==0){site=site.substring(prefix.length()+1,site.length());}}
    var country=row["country_code"]==null?row["country_name"]:row["country_code"];if(country!=null&&!country.equals("")){site=site==null||site.equals("")?country:country+" · "+site;}
    // A schema-3 fixed site has already been validated against the catalog.
    // Keep its source qualification: the renderer uses it only with a matching
    // bundled projection or a validated downloaded scene, never a generic map.
    var point=null;var pointText=null;
    if(siteData!=null&&siteData["positionMode"].equals("fixed-source")&&siteData["position"]!=null){var position=siteData["position"];pointText=[position["longitude"],position["latitude"]];point=[position["longitude"].toFloat(),position["latitude"].toFloat()];}
    var timing=row["timing"];var precision=timing["precision"];var target=timing["exact_utc"];
    // LL2 MIN is a usable nominal minute, not an exact second. Keep its
    // approximate display precision separate from the accepted feed identity.
    if(precision.equals("source-coarse")&&timing["source_precision_id"]==1&&timing["nominal_utc"]!=null){precision="minute";target=timing["nominal_utc"];}
    else if(precision.equals("source-coarse")&&(timing["window_start_utc"]!=null||timing["window_end_utc"]!=null)){precision="window";}
    var ordering=timing["exact_utc"];if(ordering==null){ordering=timing["window_start_utc"];if(timing["date_utc"]!=null){var day=nativeUtcDay(timing["date_utc"])*86400l;if(ordering==null||day>ordering){ordering=day;}}if(ordering==null){ordering=timing["window_end_utc"]==null?timing["nominal_utc"]:timing["window_end_utc"];}}
    var deadline=null;
    if((precision.equals("exact")||precision.equals("minute")) && (target instanceof Number||target instanceof Long)){
        deadline=target.toLong()+900l;var ascent=row["ascent_end"];
        if(ascent!=null && ascent["end_utc"]>deadline){deadline=ascent["end_utc"].toLong();}
    }
    var reminderEligible=row["status"] instanceof String&&row["status"].equals("pending")&&deadline!=null&&
        (timing["window_start_utc"]==null||target>=timing["window_start_utc"])&&
        (timing["window_end_utc"]==null||target<=timing["window_end_utc"]);
    return new SceneContext({"pointText"=>pointText,"orderingUtc"=>ordering,"sourceValidated"=>row["source_validated_utc"],"freshnessPolicy"=>packet.document["refreshPolicy"],"retentionDeadline"=>deadline,"reminderEligible"=>reminderEligible,"id"=>row["launch_id"],"rocket"=>rocket,"operator"=>operator,"operatorShort"=>operatorShort,"purpose"=>row["mission_purpose"],"site"=>site,"modelId"=>row["configuration_id"],"operatorId"=>row["operator_id"],"siteId"=>row["site_id"],"point"=>point,"target"=>target,"precision"=>precision,"date"=>timing["date_utc"],"rescheduled"=>selected?packet.rescheduled:row["rescheduled"],"stale"=>selected?packet.stale:row["stale"],"sourceHold"=>row["source_status_id"]==5});
}
