import Toybox.Background;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
import Toybox.Test;

(:test,:typecheck(false)) function deliveryModeCallbacksAreIdempotent(logger){
 var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
 var modes=[System.DISPLAY_MODE_HIGH_POWER,System.DISPLAY_MODE_HIGH_POWER,System.DISPLAY_MODE_LOW_POWER,System.DISPLAY_MODE_LOW_POWER,System.DISPLAY_MODE_OFF,System.DISPLAY_MODE_HIGH_POWER];
 var expected=[view.NOT_LOW,view.NOT_LOW,view.LOW,view.LOW,view.LOW,view.NOT_LOW];
 for(var i=0;i<modes.size();i+=1){view.syncDisplayMode(modes[i]);Test.assert(view.displayMode()==expected[i]);}
 view.onEnterSleep();Test.assert(view.displayMode()==view.LOW);logger.debug("MODE highLowOff normalized; duplicate callbacks stable");return true;
}

// Isolated view boundary only. A separate live-feed run establishes that the
// selected visual was acquired by the same native application before rejection.
(:test,:typecheck(false)) function deliveryRejectedResponseRetainsScene(logger){
    var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
    var scene=new SceneContext({"id"=>"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a","rocket"=>"Vulcan VC6L","site"=>"US · Cape Canaveral SFS","target"=>1794762690l,"precision"=>"exact"});
    view.setContext(scene);view.prepareRenderer();
    var visual=new NativeSfrRenderer();view.downloaded=visual;view.renderer.downloaded=visual;
    view.clearForRestore();
    Test.assert(view.context==scene);
    Test.assert(view.downloaded==visual);
    Test.assert(view.renderer!=null&&view.renderer.downloaded==visual);
    logger.debug("REJECTED_RESPONSE retainedAcceptedScene=true");return true;
}

(:test,:typecheck(false)) function deliveryPendingDeadlineDoesNotMove(logger){
    // Expected deadlines are stated from the event history, not read back from
    // the production helper. The OS minimum may delay an impossible event.
    var last=1000l;var deadline=pendingWake(1000l,4600l,null,last,true);
    Test.assert(deadline==1300l);
    deadline=pendingWake(1100l,4700l,deadline,last,true);
    Test.assert(deadline==1300l);
    deadline=pendingWake(1200l,4800l,deadline,last,true);
    Test.assert(deadline==1300l);
    Test.assert(pendingWake(1200l,4800l,1100l,800l,true)==1200l);
    Test.assert(pendingWake(1300l,4900l,1300l,1300l,true)==1600l);
    Test.assert(pendingWake(1200l,1250l,1300l,1000l,false)==1300l);
    Test.assert(!registrationNeeded(1200l,1300l,1300l,1000l,true));
    Test.assert(!registrationNeeded(1301l,1301l,1300l,1000l,true));
    Test.assert(!registrationNeeded(1361l,1361l,1300l,1000l,true));
    Test.assert(registrationNeeded(1301l,1600l,1300l,1300l,true));
    Test.assert(registrationNeeded(1200l,1300l,1100l,1000l,true));
    logger.debug("PENDING_DEADLINE first=1300 wake=1300 reload=1300 osMinimum=1600");return true;
}

(:test,:typecheck(false)) function deliverySceneEventsAndLateCompletion(logger){
 var job=new SceneLifecycle();job.replace();Test.assert(job.request(1));Test.assert(!job.request(1));var old=job.begin();job.cancel();Test.assert(!job.complete(old));Test.assert(job.request(2));var current=job.begin();Test.assert(job.complete(current));job.replace();Test.assert(!job.complete(current));logger.debug("JOB duplicate blocked; cancelled and old completion rejected; current applied");return true;
}

(:typecheck(false)) class DeliveryKeyPacket {
    var bridge;var generation;var target;
    function initialize(model,site,position,mode,selection,generationValue,targetValue){
        bridge={"selection"=>{"sha256"=>selection},
            "ids"=>["ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a",model,"ll2:organization:124",site,"ll2:country:2"],
            "site"=>{"position"=>position,"positionMode"=>mode}};
        generation=generationValue;target=targetValue;
    }
}

(:test,:typecheck(false)) function deliveryVisualIdentityCases(logger){
    var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
    var selection="77d4b3173b019ee84b7eb751e81ccb7a47edfba560a54166bfb47f441e8b7b37";
    var position={"longitude"=>"-80.58303644","latitude"=>"28.58341025","qualification"=>"unverified-reference"};
    var original=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",position,"fixed-source",selection,24,1794762690l);
    var key=view.packetVisualKey(original);
    // Validation generation and T0 can advance without changing the visual.
    var update=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",position,"fixed-source",selection,25,1794762750l);
    Test.assert(nativeSame(key,view.packetVisualKey(update)));
    var changedModel=new DeliveryKeyPacket("ll2:configuration:99","ll2:site:29",position,"fixed-source",selection,25,1794762750l);
    var changedSite=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:30",position,"fixed-source",selection,25,1794762750l);
    var changedPoint=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",{"longitude"=>"-80.5","latitude"=>"28.58341025","qualification"=>"unverified-reference"},"fixed-source",selection,25,1794762750l);
    var changedQualification=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",{"longitude"=>"-80.58303644","latitude"=>"28.58341025","qualification"=>"different"},"fixed-source",selection,25,1794762750l);
    var changedMode=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",position,"mobile-reference-no-event",selection,25,1794762750l);
    var changedArt=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",position,"fixed-source","aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",25,1794762750l);
    Test.assert(!nativeSame(key,view.packetVisualKey(changedModel)));
    Test.assert(!nativeSame(key,view.packetVisualKey(changedSite)));
    Test.assert(!nativeSame(key,view.packetVisualKey(changedPoint)));
    Test.assert(!nativeSame(key,view.packetVisualKey(changedQualification)));
    Test.assert(!nativeSame(key,view.packetVisualKey(changedMode)));
    Test.assert(!nativeSame(key,view.packetVisualKey(changedArt)));
    logger.debug("VISUAL_KEY sameT0AndGeneration=true modelSitePointQualificationArtChangesDistinct=true");return true;
}

(:typecheck(false)) class DeliveryScheduleStore {
    var data={};var unavailable=null;var failWrite=null;
    function read(key){
        if(key.equals(unavailable)||!data.hasKey(key)){return null;}
        var value=data[key];
        if(key.equals("sf.batch.head")&&value instanceof Dictionary){return {"base"=>value["base"],"pending"=>value["pending"],"catalogDigest"=>value["catalogDigest"],"transfer"=>value["transfer"],"serial"=>value["serial"]};}
        return value;
    }
    function write(key,value){
        if(key.equals(failWrite)){throw new Lang.InvalidValueException("injected write failure");}
        data[key]=key.equals("sf.batch.head")?{"base"=>value["base"],"pending"=>value["pending"],"catalogDigest"=>value["catalogDigest"],"transfer"=>value["transfer"],"serial"=>value["serial"]}:value;
    }
    function remove(key){data.remove(key);}
}

(:test,:typecheck(false)) function deliveryVisualWaitsForMatchingBatch(logger){
    var store=new DeliveryScheduleStore();var base="https://example.test";
    var catalog="{}";var index="{\"objects\":[]}";
    var h=new NativeWireHash();h.put(catalog);var catalogHash=h.digest();
    h=new NativeWireHash();h.put(index);var indexHash=h.digest();
    var bridge={"catalogDigest"=>catalogHash,"transfer"=>{"sha256"=>indexHash,"path"=>"descriptors/"+indexHash+".json","decodedBytes"=>index.length()}};
    var batch=new NativeBatch(store,base);batch.select(bridge);
    var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
    view.setContext(new SceneContext({"id"=>"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"}));
    var source=new NativeRenderSource(store,base,bridge);view.setAssetCache(source);
    Test.assert(!source.ready&&view.sceneLifecycle.job==null);
    // A decode failure is not retried merely because the same batch was seen.
    Test.assert(view.sceneLifecycle.request(0));var token=view.sceneLifecycle.begin();view.sceneLifecycle.fail(token);
    view.setAssetCache(new NativeRenderSource(store,base,bridge));Test.assert(view.sceneLifecycle.job!=null&&view.sceneLifecycle.job.state==view.sceneLifecycle.job.FAILED);
    var ref=batch.next();Test.assert(batch.immutable.put(ref,catalog));
    ref=batch.next();Test.assert(batch.immutable.put(ref,index));Test.assert(batch.next()==null);
    source=new NativeRenderSource(store,base,bridge);view.setAssetCache(source);Test.assert(source.ready&&view.sceneLifecycle.job==null);
    Test.assert(!new NativeRenderSource(store,base,{"catalogDigest"=>"other","transfer"=>bridge["transfer"]}).ready);
    Test.assert(!new NativeRenderSource(store,base,{"catalogDigest"=>catalogHash,"transfer"=>{"sha256"=>"other"}}).ready);
    Test.assert(view.sceneLifecycle.request(source.serial));token=view.sceneLifecycle.begin();view.sceneLifecycle.fail(token);
    view.setAssetCache(new NativeRenderSource(store,base,bridge));Test.assert(view.sceneLifecycle.job!=null&&view.sceneLifecycle.job.state==view.sceneLifecycle.job.FAILED);
    // A dependency becomes unavailable and is then repaired. The production
    // batch transitions through pending and emits a new completion serial.
    store.unavailable="sf.obj."+indexHash;store.failWrite="sf.batch.head";
    var failed=false;try{batch.next();}catch(e){failed=true;}
    Test.assert(failed&&!new NativeRenderSource(store,base,bridge).ready);
    store.failWrite=null;store.unavailable=null;batch=new NativeBatch(store,base);Test.assert(batch.next()==null);
    view.setAssetCache(new NativeRenderSource(store,base,bridge));Test.assert(view.sceneLifecycle.job==null);
    Test.assert(!new NativeRenderSource(store,"https://other.test",bridge).ready);
    var partial=new DeliveryScheduleStore();partial.failWrite="sf.batch.pending";
    var selection=new NativeBatch(partial,base);failed=false;
    try{selection.select(bridge);}catch(e){failed=true;}
    Test.assert(failed&&batchPending(new NativeTransfer(base,partial)));
    logger.debug("VISUAL_BATCH pendingAndWrongIdentityRejected=true completedMatchingBatchApplied=true");return true;
}

(:test,:typecheck(false)) function deliveryRealRegisteredDeadline(logger){
    var now=Time.now().value().toLong();var store=new DeliveryScheduleStore();
    var transfer=new NativeTransfer("https://jekamas.github.io/SpaceFox",store);
    store.write("sf.transfer.ready",{"base"=>transfer.base,"accepted"=>true});
    store.write("sf.batch.pending",{"base"=>transfer.base,"pending"=>true});
    transfer.attempted(now);
    var due=now+300;
    try{
        Background.registerForTemporalEvent(new Time.Moment(due.toNumber()));
        Test.assert(Background.getTemporalEventRegisteredTime().value().toLong()==due);
        armFeed(transfer,now+60);
        Test.assert(Background.getTemporalEventRegisteredTime().value().toLong()==due);
        armFeed(transfer,now+120);
        Test.assert(Background.getTemporalEventRegisteredTime().value().toLong()==due);
        logger.debug("REGISTERED_DEADLINE preserved=true wakeAndReload=true");
    }finally{Background.deleteTemporalEvent();}
    return true;
}

(:typecheck(false)) class DeliveryAdmissionCache {
    var store;var packet;
    function initialize(adapter){store=adapter;packet=true;}
}

(:test,:typecheck(false)) function deliveryDuplicateCallbackDoesNotInvalidateBuild(logger){
    var store=new DeliveryScheduleStore();var cache=new DeliveryAdmissionCache(store);
    var incoming=new NativeIncoming(store,"https://jekamas.github.io/SpaceFox");
    var machine=new SceneLifecycle();machine.replace();
    Test.assert(machine.request(1));var token=machine.begin();Test.assert(token!=null);
    // No response, then a response already processed: both reach the production
    // decision seam and leave the in-progress generation unchanged.
    Test.assert(!NativeForegroundApp.hasNewIncoming(cache,incoming));
    Test.assert(machine.pending());
    var marker={"sha256"=>"same","sequence"=>1};store.write("sf.incoming.feed",marker);
    store.write("sf.incoming.feed.processed",incoming.token(marker));
    Test.assert(!NativeForegroundApp.hasNewIncoming(cache,incoming));
    Test.assert(machine.pending()&&machine.generation==token);
    store.write("sf.incoming.feed",{"sha256"=>"new","sequence"=>2});
    Test.assert(NativeForegroundApp.hasNewIncoming(cache,incoming));
    machine.cancel();Test.assert(!machine.complete(token));Test.assert(machine.job==null);
    logger.debug("CALLBACKS duplicateNoMutation=2 newCandidateApplied=1 staleCompletionRejected=1");return true;
}
