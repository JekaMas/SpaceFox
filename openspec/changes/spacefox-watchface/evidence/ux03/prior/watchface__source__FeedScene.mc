import Toybox.Lang;

(:typecheck(false))
function feedScene(packet,now){
    if(packet==null||packet.document["launch"]==null){return null;}packet.advance(now);if(packet.presentation!=null){packet.presentation.stale=packet.stale;packet.presentation.rescheduled=packet.rescheduled;return packet.presentation;}var row=packet.document["launch"];var dictionaries=packet.document["dictionaries"];
    var rocket=row["configuration_name"];var operator=row["operator_name"];var site=row["site_location_name"]==null?row["site_name"]:row["site_location_name"];
    if(rocket==null&&row["configuration_id"]!=null&&dictionaries.hasKey(row["configuration_id"])){rocket=packet.catalogName(row["configuration_id"]);}
    if(operator==null&&row["operator_id"]!=null&&dictionaries.hasKey(row["operator_id"])){operator=packet.catalogName(row["operator_id"]);}
    if(site==null&&row["site_id"]!=null&&dictionaries.hasKey(row["site_id"])){site=packet.catalogName(row["site_id"]);}
    var operatorShort=row["operator_abbrev"];
    // Keep full source text in the accepted feed; derive only a compact place
    // label by removing an exact operator prefix and comma-delimited region.
    if(site!=null){var comma=site.find(",");if(comma!=null&&comma>0){site=site.substring(0,comma);}var prefix=row["operator_name"];if(prefix!=null&&!prefix.equals("")&&site.find(prefix+" ")==0){site=site.substring(prefix.length()+1,site.length());}}
    var country=row["country_code"]==null?row["country_name"]:row["country_code"];if(country!=null&&!country.equals("")){site=site==null||site.equals("")?country:country+" · "+site;}
    // Source positions are explicitly unverified. Generic/no-point is coherent
    // for every model until an exact qualified visual envelope is available.
    var timing=row["timing"];var precision=timing["precision"];var target=timing["exact_utc"];
    // LL2 MIN is a usable nominal minute, not an exact second. Keep its
    // approximate display precision separate from the accepted feed identity.
    if(precision.equals("source-coarse")&&timing["source_precision_id"]==1&&timing["nominal_utc"]!=null){precision="minute";target=timing["nominal_utc"];}
    else if(precision.equals("source-coarse")&&(timing["window_start_utc"]!=null||timing["window_end_utc"]!=null)){precision="window";}
    return new SceneContext({"id"=>row["launch_id"],"rocket"=>rocket,"operator"=>operator,"operatorShort"=>operatorShort,"purpose"=>row["mission_purpose"],"site"=>site,"modelId"=>row["configuration_id"],"operatorId"=>row["operator_id"],"point"=>null,"target"=>target,"precision"=>precision,"date"=>timing["date_utc"],"rescheduled"=>packet.rescheduled,"stale"=>packet.stale});
}
