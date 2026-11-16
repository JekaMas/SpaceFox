import Toybox.Test;
import Toybox.WatchUi;
import Toybox.Lang;

// Independent review discriminator: mutate only technical identity/count/
// terminal fields of the captured real response. Compare admission with the
// retained pre-continuation validator as well as explicit expected outcomes.
(:typecheck(false)) function peerReplaceOnce(raw,before,after){
    var at=raw.find(before);Test.assertMessage(at!=null,"peer mutation must reach its captured input");
    return raw.substring(0,at)+after+raw.substring(at+before.length(),raw.length());
}
(:typecheck(false)) function peerUpcoming(raw,rows){
    var start=raw.find("\"upcoming\":[");var end=raw.find(",\"visualSelection\":");
    Test.assert(start!=null&&end!=null&&end>start);
    return raw.substring(0,start)+"\"upcoming\":["+rows+"]"+raw.substring(end,raw.length());
}
(:typecheck(false)) function peerTerminal(id,status,checked){
    return "{\"terminal\":{\"launch_id\":\""+id+"\",\"source_updated_subsecond\":0,\"source_updated_utc\":null,\"source_validated_utc\":"+checked+",\"status\":\""+status+"\"}}";
}
(:typecheck(false)) function peerAdmissionCase(raw,store,expected,label,logger){
    var now=1794818604l;var oldAccepted=false;var accepted=false;var packet=null;
    try{var oracle=new B1MeasuredFeed(store);oracle.raw=raw;oracle.parse(raw);oracle.validate(now);oldAccepted=true;}catch(e){if(!(e instanceof Lang.InvalidValueException)){throw e;}}
    try{packet=new NativePreparedBridgeFeed(raw,now,store);var steps=0;while(!packet.prepareStep()){steps+=1;Test.assert(steps<2000);}accepted=true;}catch(e){if(!(e instanceof Lang.InvalidValueException)){throw e;}}
    if(packet!=null){packet.disposePreparation();}
    Test.assertMessage(oldAccepted==expected&&accepted==expected,"peer admission mismatch: "+label);
    logger.debug("PEER_ADMISSION "+label+" expected="+expected+" original="+oldAccepted+" staged="+accepted);
}
(:test,:typecheck(false)) function peerCrossRecordAdmission(logger){
    var store=new B1MemoryStore();var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];
    var batch=new NativeBatch(store,"https://jekamas.github.io/SpaceFox");Test.assert(batch.begin(raw));var catalog=batch.next();Test.assert(catalog!=null&&batch.immutable.put(catalog,b1Response(catalog["path"])));
    var selected="ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60";
    var first="ll2:launch:76617033-4dc0-4448-b50c-e5b0d5a18539";
    var second="ll2:launch:a2975167-7c6f-4403-99e1-b40df17c8140";
    peerAdmissionCase(raw,store,true,"captured-positive",logger);
    peerAdmissionCase(peerReplaceOnce(raw,first,selected),store,false,"selected-future-duplicate",logger);
    peerAdmissionCase(peerReplaceOnce(raw,second,first),store,false,"future-future-duplicate",logger);
    peerAdmissionCase(peerReplaceOnce(raw,"\"acceptedRecords\":20","\"acceptedRecords\":2"),store,false,"overall-count",logger);
    var terminal=peerTerminal(first,"completed","1794818604");
    peerAdmissionCase(peerUpcoming(raw,terminal),store,true,"terminal-positive",logger);
    peerAdmissionCase(peerUpcoming(raw,peerTerminal(selected,"completed","1794818604")),store,false,"selected-terminal-duplicate",logger);
    peerAdmissionCase(peerUpcoming(raw,terminal+","+terminal),store,false,"terminal-terminal-duplicate",logger);
    peerAdmissionCase(peerUpcoming(raw,peerTerminal(first,"pending","1794818604")),store,false,"terminal-status",logger);
    peerAdmissionCase(peerUpcoming(raw,peerTerminal(first,"completed","1794818605")),store,false,"terminal-future-validation",logger);
    logger.debug("PEER_CROSS_RECORD cases=9 original_staged_parity=true");return true;
}
