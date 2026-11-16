import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.Timer;
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

// Current marker, recovery and cleanup are real promotion objects. A newly
// protected slot must never be swept by a continuation already in progress.
(:test,:typecheck(false)) function b1TailCleanupRechecksOwnership(logger){
 var base="https://fixture.invalid/profile-a";var now=1794551202l;var older=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];var newer=WatchUi.loadResource(Rez.JsonData.B1ProfileNext)["raw"];
 for(var mode=0;mode<3;mode+=1){
  var store=new B1MemoryStore();var batch=new NativeBatch(store,base);Test.assert(batch.begin(older));var a=batch.next();Test.assert(a!=null&&batch.immutable.put(a,b1ProfileResponse(a["path"])));Test.assert(batch.begin(newer));var b=batch.next();Test.assert(b!=null&&batch.immutable.put(b,WatchUi.loadResource(Rez.JsonData.B1ProfileNextCatalog)["raw"]));
  var cache=new NativeCache(base,store);Test.assert(b1Promote021(cache,older,now));var original=store.read("sf.commit");var packet=new NativePreparedBridgeFeed(newer,now,store);var n=0;while(!packet.prepareStep()){n+=1;Test.assert(n<2000);}var promotion=new NativeFeedPromotion(cache,newer,packet,now,null);
  n=0;while(promotion.phase!=7&&!promotion.done){promotion.step();n+=1;Test.assert(n<40);}Test.assert(!promotion.done&&promotion.cleanupAt<16);var stale="sf.feed."+promotion.slot+"."+promotion.cleanupAt;store.write(stale,"stale");
  if(mode==1){store.write("sf.commit",promotion.marker);}else if(mode==2){store.write("sf.recovery",promotion.marker);}
  var before=promotion.cleanupAt;var completed=promotion.step();
  if(mode==0){Test.assert(!completed&&promotion.cleanupAt==before+1&&store.read(stale)==null&&store.read("sf.commit")["seal"].equals(original["seal"]));n=0;while(!promotion.step()){n+=1;Test.assert(n<40);}Test.assert(promotion.accepted);}
  else{Test.assert(completed&&!promotion.accepted&&cache.failure.equals("admission-retry")&&store.read(stale).equals("stale"));if(mode==1){Test.assert(store.read("sf.commit")["seal"].equals(promotion.marker["seal"]));}else{Test.assert(store.read("sf.commit")["seal"].equals(original["seal"])&&store.read("sf.recovery")["seal"].equals(promotion.marker["seal"]));}}
 }
 logger.debug("B1_TAIL_SLICES onePerStep=true activeAndRecoveryRechecked=true takeoverRefused=true");return true;
}

(:test,:typecheck(false)) class B1StopPacket {var disposed=false;function disposePreparation(){disposed=true;}}
(:test,:typecheck(false)) function b1OwnerStopReleasesPendingWork(logger){
 var app=new SpaceFoxApp();var view=new SpaceFoxView(new B1Clock(),new ScheduleState(null,"empty"));var store=new B1MemoryStore();var packet=new B1StopPacket();app.view=view;app.feed=new NativeCache("https://fixture.invalid/stop",store);view.pendingLoader=app.method(:reloadFeed);view.cancelAdmission=app.method(:cancelWork);app.admissionJob={"packet"=>packet};app.admissionTimer=new Timer.Timer();app.restoreTimer=new Timer.Timer();app.restoreJob=new NativeRestoreJob(app.feed,1794551202l,null);app.restorePending=true;app.deferredRestore=true;app.deferredSeal="old";
 app.onStop(null);Test.assert(packet.disposed&&app.admissionJob==null&&app.restoreJob==null&&app.admissionTimer==null&&app.restoreTimer==null&&!app.restorePending&&!app.deferredRestore&&app.deferredSeal==null&&app.view==null&&app.feed==null&&view.pendingLoader==null&&view.cancelAdmission==null);
 app.onStop(null);Test.assert(app.view==null&&app.admissionJob==null);logger.debug("B1_OWNER_STOP pendingPacketDisposed=true timersAndJobsCleared=true callbacksReleased=true idempotent=true");return true;
}

// A missing provisional chunk must defer the input and leave the sealed old
// closure recoverable. This drives the real foreground admission and restore
// owners; it is not a device heap or OS callback observation.
(:test,:typecheck(false)) function b1MissingChunkRecovery022(logger){
    var base="https://fixture.invalid/profile-a";var now=1794551202l;var older=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];var newer=WatchUi.loadResource(Rez.JsonData.B1ProfileNext)["raw"];
    var store=new B1FailingStore021();var batch=new NativeBatch(store,base);Test.assert(batch.begin(older));var ref=batch.next();Test.assert(ref!=null&&batch.immutable.put(ref,b1ProfileResponse(ref["path"])));
    var cache=new NativeCache(base,store);Test.assert(b1Promote021(cache,older,now));var seal=cache.commit["seal"];var validation=cache.packet.validation;Test.assert(new NativeTransfer(base,store).stage("feed",newer,null));var marker=store.read("sf.incoming.feed");store.remove("sf.incoming.feed."+marker["parts"][0]+".0");
    var app=new SpaceFoxApp();var view=new SpaceFoxView(new B1DecodeClock(),new ScheduleState(null,"empty"));app.view=view;app.feed=cache;view.setPacket(cache.packet);app.batchingForeground=true;view.onShow();NativeForegroundApp.beginAdmission(app,cache,new NativeIncoming(store,base),now);
    var n=0;while(app.admissionJob!=null){NativeForegroundApp.admissionStep(app);n+=1;Test.assert(n<100);}Test.assert(app.restorePending&&view.admissionPending&&view.context!=null&&store.read("sf.commit")["seal"].equals(seal)&&store.read("sf.incoming.feed.deferred")!=null);
    var restore=new NativeRestoreJob(cache,now,seal);n=0;while(!restore.step()){n+=1;Test.assert(n<3000);}Test.assert(restore.accepted&&cache.packet.validation==validation&&cache.commit["seal"].equals(seal));app.batchingForeground=false;view.onHide();logger.debug("B1_MISSING_CHUNK deferred=true priorContext=true sealedRestore=true");return true;
}

(:test,:typecheck(false)) class B1QueueReadStore022 extends B1MemoryStore {
    var queueReads=0;function initialize(){B1MemoryStore.initialize();}
    function read(key){if(key.find("sf.upcoming.")==0){queueReads+=1;}return B1MemoryStore.read(key);}
}
(:test,:typecheck(false)) class B1QueueView022 extends SpaceFoxView {
    function initialize(){SpaceFoxView.initialize(new B1DecodeClock(),new ScheduleState(null,"empty"));}
    function mergeSaved(saved,now,terminal){SpaceFoxView.mergeSaved(saved,1794551202l,terminal);}
}
(:test,:typecheck(false)) function b1ReboundQueueRead022(logger){
    var base="https://fixture.invalid/profile-a";var now=1794551202l;var raw=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];var store=new B1QueueReadStore022();var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));var ref=batch.next();Test.assert(ref!=null&&batch.immutable.put(ref,b1ProfileResponse(ref["path"])));var cache=new NativeCache(base,store);Test.assert(b1Promote021(cache,raw,now));var app=new SpaceFoxApp();var view=new B1QueueView022();app.view=view;app.feed=cache;app.batchingForeground=true;
    NativeForegroundApp.display(app,cache);var count=store.queueReads;logger.debug("QUEUE_READ first="+count+" context="+(view.context!=null)+" same="+(view.context==cache.packet.presentation));Test.assertMessage(count==1&&view.context!=null,"first bind reads queue and preserves facts");NativeForegroundApp.display(app,cache);logger.debug("QUEUE_READ second="+store.queueReads+" same="+(view.context==cache.packet.presentation));Test.assertMessage(store.queueReads==count&&view.context!=null,"same packet reuses in-memory queue");view.setPacket(null);NativeForegroundApp.display(app,cache);logger.debug("QUEUE_READ rebound="+store.queueReads);Test.assertMessage(store.queueReads==count+1&&view.context!=null,"new bind reads queue");app.batchingForeground=false;logger.debug("B1_REBOUND_QUEUE first=true samePacketNoRead=true rebindReads=true");return true;
}
