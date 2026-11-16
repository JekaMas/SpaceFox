import Toybox.Lang;

(:extendedCode,:typecheck(false))
function feedScene(packet,now){return feedSceneWork(packet,now,false);}
(:extendedCode,:typecheck(false))
function feedSceneCompacting(packet,now){return feedSceneWork(packet,now,true);}
(:extendedCode,:typecheck(false))
function feedSceneWork(packet,now,releaseParsed){
    if(packet==null||packet.document["launch"]==null){return null;}
    packet.advance(now);
    if(packet.presentation!=null){packet.presentation.stale=packet.stale;packet.presentation.rescheduled=packet.rescheduled;return packet.presentation;}
    var row=packet.document["launch"];var siteData=packet.bridge==null?null:packet.bridge["site"];
    var current=feedSceneRow(packet,row,siteData,true);
    // During a transaction only, later work needs the compact launch identity,
    // not the parsed launch/catalog object graph. Release it before allocating
    // successor scenes; each validated successor can then be released in turn.
    if(releaseParsed){packet.reducePresentationLaunch();row=null;siteData=null;}
    packet.upcomingScenes=[];
    var rows=packet.document["upcoming"];
    if(rows instanceof Array){for(var i=0;i<rows.size();i+=1){var item=rows[i];if(item.hasKey("terminal")){if(releaseParsed){rows[i]=null;}continue;}var pos=item["sitePosition"];var site=pos==null?null:{"positionMode"=>"fixed-source","position"=>pos};packet.upcomingScenes.add(feedSceneRow(packet,item,site,false));if(releaseParsed){rows[i]=null;item=null;pos=null;site=null;}}}
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
    // Avoid a second 22-entry dictionary while the validated feed and its raw
    // durable bytes are still live. Values have passed the same feed/catalog
    // validation as before; assign the exact SceneContext projection directly.
    var scene=new SceneContext({});scene.pointText=pointText;scene.orderingUtc=ordering==null?null:ordering.toLong();
    var checked=row["source_validated_utc"];scene.sourceValidated=checked==null?null:checked.toLong();scene.freshnessPolicy=packet.document["refreshPolicy"];scene.retentionDeadline=deadline;
    scene.launchId=row["launch_id"];scene.rocket=rocket instanceof String?rocket:"";scene.operator=operator instanceof String?operator:"";
    scene.operatorShort=operatorShort instanceof String?operatorShort:"";scene.purpose=row["mission_purpose"] instanceof String?row["mission_purpose"]:"";
    scene.site=site instanceof String?site:"";scene.modelId=row["configuration_id"] instanceof String?row["configuration_id"]:"";
    scene.operatorId=row["operator_id"] instanceof String?row["operator_id"]:"";scene.siteId=row["site_id"] instanceof String?row["site_id"]:"";
    scene.point=point!=null&&scene.validPoint(point)?point:null;scene.schedule=new ScheduleState(target,precision);scene.sourcePrecision=precision;scene.date=timing["date_utc"] instanceof String?timing["date_utc"]:null;
    if((precision.equals("exact")||precision.equals("minute"))&&(target instanceof Number||target instanceof Long)){scene.freshnessTarget=target.toLong();scene.retentionTarget=target.toLong();}
    scene.rescheduled=selected?packet.rescheduled:row["rescheduled"];scene.stale=selected?packet.stale:row["stale"];scene.sourceHold=row["source_status_id"]==5;
    return scene;
}
