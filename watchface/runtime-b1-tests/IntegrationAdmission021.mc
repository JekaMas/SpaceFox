import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

(:test,:typecheck(false)) class B1FailingStore021 extends B1MemoryStore {
    var failKey=null;
    function initialize(){B1MemoryStore.initialize();}
    function write(key,value){if(failKey!=null&&key.equals(failKey)){failKey=null;throw new Lang.InvalidValueException("injected storage failure");}B1MemoryStore.write(key,value);}
}
(:typecheck(false)) function b1Catalog021(store,base,raw){
    var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));var ref=batch.next();Test.assert(ref!=null&&batch.immutable.put(ref,b1Response(ref["path"])));
}
(:typecheck(false)) function b1Promote021(cache,raw,now){
    var packet=new NativePreparedBridgeFeed(raw,now,cache.store);var n=0;while(!packet.prepareStep()){n+=1;Test.assert(n<2000);}
    var job=new NativeFeedPromotion(cache,raw,packet,now,null);n=0;while(!job.step()){n+=1;Test.assert(n<40);}return job.accepted;
}
(:test,:typecheck(false)) function b1SupersededDuringAdmission021(logger){
    var store=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var now=1794818604l;var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];
    Test.assert(new NativeTransfer(base,store).stage("feed",raw,null));b1Catalog021(store,base,raw);
    var app=new SpaceFoxApp();var view=new SpaceFoxView(new B1Clock(),new ScheduleState(null,"empty"));app.view=view;app.feed=new NativeCache(base,store);view.onShow();view.queueResumeAfterFrame();view.stopResume();app.batchingForeground=true;
    NativeForegroundApp.beginAdmission(app,app.feed,new NativeIncoming(store,base),now);
    var n=0;while(app.admissionJob!=null&&(app.admissionJob["packet"]==null||app.admissionJob["packet"].preparePhase<2)){NativeForegroundApp.admissionStep(app);n+=1;Test.assert(n<2000);}
    Test.assert(app.admissionJob!=null&&store.read("sf.commit")==null);var original=store.read("sf.incoming.feed");var changed={};var keys=original.keys();for(var i=0;i<keys.size();i+=1){changed[keys[i]]=original[keys[i]];}changed["sequence"]+=1;store.write("sf.incoming.feed",changed);
    NativeForegroundApp.admissionStep(app);Test.assert(app.admissionJob==null&&store.read("sf.commit")==null&&store.read("sf.incoming.feed.processed")==null);
    app.batchingForeground=false;view.onHide();logger.debug("B1_INTEGRATION supersession_no_commit=true stale_not_consumed=true");return true;
}
(:test,:typecheck(false)) function b1FailedPromotionRecovery021(logger){
    var base="https://fixture.invalid/profile-a";var now=1794551202l;var older=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];
    // B is a retained technical mutation, not a new launch or site observation.
    var newer=WatchUi.loadResource(Rez.JsonData.B1ProfileNext)["raw"];
    for(var mode=0;mode<2;mode+=1){
        var store=new B1FailingStore021();var batch=new NativeBatch(store,base);Test.assert(batch.begin(older));var a=batch.next();Test.assert(a!=null&&batch.immutable.put(a,b1ProfileResponse(a["path"])));Test.assert(batch.begin(newer));var b=batch.next();Test.assert(b!=null&&batch.immutable.put(b,WatchUi.loadResource(Rez.JsonData.B1ProfileNextCatalog)["raw"]));var cache=new NativeCache(base,store);Test.assert(b1Promote021(cache,older,now));var seal=cache.commit["seal"];var validation=cache.packet.validation;
        var packet=new NativePreparedBridgeFeed(newer,now,store);var n=0;while(!packet.prepareStep()){n+=1;Test.assert(n<2000);}var next=new NativeFeedPromotion(cache,newer,packet,now,null);
        if(mode==0){Test.assert(!next.step()&&!next.same);store.failKey="sf.feed."+next.slot+".0";}else{store.failKey="sf.commit";}
        n=0;while(!next.step()){n+=1;Test.assert(n<40);}Test.assert(!next.accepted&&store.read("sf.commit")["seal"].equals(seal));
        var reopened=new NativeCache(base,store);var restore=new NativeRestoreJob(reopened,now,seal);n=0;while(!restore.step()){n+=1;Test.assert(n<3000);}Test.assert(restore.accepted&&reopened.packet.validation==validation);
    }
    logger.debug("B1_INTEGRATION chunk_and_commit_failure_preserve_seal=true exact_age_restored=true");return true;
}

(:test,:typecheck(false)) function b1QueueCheckpointFailure021(logger){
    var base="https://fixture.invalid/profile-a";var now=1794551202l;var older=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];var newer=WatchUi.loadResource(Rez.JsonData.B1ProfileNext)["raw"];
    var store=new B1FailingStore021();var batch=new NativeBatch(store,base);Test.assert(batch.begin(older));var ref=batch.next();Test.assert(ref!=null&&batch.immutable.put(ref,b1ProfileResponse(ref["path"])));
    var cache=new NativeCache(base,store);Test.assert(b1Promote021(cache,older,now));var seal=cache.commit["seal"];Test.assert(new NativeTransfer(base,store).stage("feed",newer,null));
    var app=new SpaceFoxApp();var view=new SpaceFoxView(new B1DecodeClock(),new ScheduleState(null,"empty"));app.view=view;app.feed=cache;view.setPacket(cache.packet);view.onShow();app.batchingForeground=true;
    store.failKey=new NativeUpcomingCache(store,base,cache.packet.document["publisher"]["instance"]).key;
    NativeForegroundApp.beginAdmission(app,cache,new NativeIncoming(store,base),now);
    logger.debug("B1_QUEUE_DIAG job="+(app.admissionJob!=null)+" pending="+view.admissionPending+" failure="+cache.failure+" deferred="+(store.read("sf.incoming.feed.deferred")!=null)+" context="+(view.context!=null));
    Test.assert(app.admissionJob==null);Test.assert(!view.admissionPending);Test.assert(cache.failure.equals("admission-retry"));
    Test.assert(store.read("sf.commit")["seal"].equals(seal));Test.assert(store.read("sf.incoming.feed.deferred")!=null);Test.assert(view.context!=null);
    app.batchingForeground=false;view.onHide();logger.debug("B1_QUEUE_CHECKPOINT failure_keeps_commit_and_facts=true retry_deferred=true");return true;
}
