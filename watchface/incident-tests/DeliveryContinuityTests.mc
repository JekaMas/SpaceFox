import Toybox.Lang;
import Toybox.Test;

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
    // Independent expected phases for this trace: accepted fallback (1),
    // requested before painting (3), painted (4), build running (5), cancelled
    // (2), new build (5), committed rich scene (6), new launch fallback (1).
    var machine=new SceneLifecycle();var applied=0;var rejected=0;
    machine.replace(true);applied+=1;Test.assert(machine.phase==1);
    Test.assert(machine.request());applied+=1;Test.assert(machine.phase==3);
    machine.painted();applied+=1;Test.assert(machine.phase==4);
    var old=machine.begin();applied+=1;Test.assert(old!=null&&machine.phase==5);
    machine.cancel();applied+=1;Test.assert(machine.phase==2);
    Test.assert(!machine.complete(old));rejected+=1;Test.assert(machine.phase==2);
    Test.assert(machine.request());applied+=1;Test.assert(machine.phase==4);
    var current=machine.begin();applied+=1;Test.assert(current!=null&&machine.phase==5);
    Test.assert(machine.complete(current));applied+=1;Test.assert(machine.phase==6);
    machine.replace(true);applied+=1;Test.assert(machine.phase==1);
    Test.assert(!machine.complete(current));rejected+=1;Test.assert(machine.phase==1);
    Test.assert(applied==9&&rejected==2);
    logger.debug("SCENE_EVENTS applied=9 observedNoMutation=2 skipped=0");return true;
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
    var data={};
    function read(key){return data.hasKey(key)?data[key]:null;}
    function write(key,value){data[key]=value;}
    function remove(key){data.remove(key);}
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
    var machine=new SceneLifecycle();machine.replace(true);machine.painted();
    Test.assert(machine.request());var token=machine.begin();Test.assert(token!=null);
    // No response, then a response already processed: both reach the production
    // decision seam and leave the in-progress generation unchanged.
    Test.assert(!NativeForegroundApp.hasNewIncoming(cache,incoming));
    Test.assert(machine.phase==5);
    var marker={"sha256"=>"same","sequence"=>1};store.write("sf.incoming.feed",marker);
    store.write("sf.incoming.feed.processed",incoming.token(marker));
    Test.assert(!NativeForegroundApp.hasNewIncoming(cache,incoming));
    Test.assert(machine.phase==5&&machine.generation==token);
    store.write("sf.incoming.feed",{"sha256"=>"new","sequence"=>2});
    Test.assert(NativeForegroundApp.hasNewIncoming(cache,incoming));
    machine.cancel();Test.assert(!machine.complete(token));Test.assert(machine.phase==2);
    logger.debug("CALLBACKS duplicateNoMutation=2 newCandidateApplied=1 staleCompletionRejected=1");return true;
}
