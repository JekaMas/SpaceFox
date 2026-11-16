import Toybox.Application;
import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

(:typecheck(false)) function b1PutCapturedCatalog(store){
    var ref={"path"=>"wire3/catalogs/83226c3bce7f6da4d3830ffbff16aefe5632054f2eb23675ed2cc6ec8dcc82d0.json","sha256"=>"83226c3bce7f6da4d3830ffbff16aefe5632054f2eb23675ed2cc6ec8dcc82d0","decodedBytes"=>1386};
    Test.assert(new NativeImmutable(store).put(ref,b1Response(ref["path"])));
}
(:test,:typecheck(false)) function b1StagedLiveFeedAdmission(logger){
    Application.Storage.clearValues();var base="https://jekamas.github.io/SpaceFox";var store=new NativeStore();b1PutCapturedCatalog(store);
    var transfer=new NativeTransfer(base,store);var raw=WatchUi.loadResource(Rez.JsonData.B1LiveFeed)["raw"];Test.assert(transfer.stage("feed",raw,null));raw=null;
    var cache=new NativeCache(base,store);var job=new NativeAdmissionJob(cache,null,1794821936l);
    for(var i=0;i<7;i+=1){Test.assert(!job.step());Test.assert(store.read("sf.commit")==null);Test.assert(cache.packet==null);}
    Test.assert(job.raw==null&&job.candidate.raw.equals("")&&store.read("sf.feed.0.0")!=null);
    Test.assert(job.step()&&job.finished&&job.accepted);Test.assert(cache.packet!=null);
    Test.assertEqual(cache.packet.wireHash,"68336209054817f30ed03e2d9965c11de241a0a87f1bf38309b2e10be1f06b4d");
    Test.assertEqual(cache.packet.launchId(),"ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60");
    logger.debug("B1_STAGED_VALIDATION actual="+cache.packet.validation+" commit="+(store.read("sf.commit")!=null));
    Test.assert(cache.packet.validation==1794820332l);Test.assert(store.read("sf.commit")!=null);
    logger.debug("B1_STAGED live_red_bytes=true phases=8 no_early_commit=true source_age_preserved=true");return true;
}
(:test,:typecheck(false)) function b1StagedSupersededToken(logger){
    Application.Storage.clearValues();var base="https://jekamas.github.io/SpaceFox";var store=new NativeStore();b1PutCapturedCatalog(store);
    var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",WatchUi.loadResource(Rez.JsonData.B1LiveFeed)["raw"],null));
    var cache=new NativeCache(base,store);var job=new NativeAdmissionJob(cache,null,1794821936l);
    for(var i=0;i<5;i+=1){Test.assert(!job.step());}
    Test.assert(transfer.stage("feed",WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"],null));
    Test.assert(!job.step());Test.assert(job.step()&&job.finished&&!job.accepted&&job.retry);
    Test.assert(store.read("sf.commit")==null&&store.read("sf.incoming.feed.processed")==null);
    logger.debug("B1_STAGED superseded_token_no_promotion=true");return true;
}
(:test,:typecheck(false)) function b1StagedRestoreExactAndRecovery(logger){
    Application.Storage.clearValues();var base="https://jekamas.github.io/SpaceFox";var store=new NativeStore();b1PutCapturedCatalog(store);
    var transfer=new NativeTransfer(base,store);var cache=new NativeCache(base,store);
    Test.assert(transfer.stage("feed",WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"],null));
    var first=new NativeAdmissionJob(cache,null,1794821936l);while(!first.step()){}Test.assert(first.accepted);var oldSeal=cache.commit["seal"];
    Test.assert(transfer.stage("feed",WatchUi.loadResource(Rez.JsonData.B1LiveFeed)["raw"],null));
    var second=new NativeAdmissionJob(cache,null,1794821936l);while(!second.step()){}Test.assert(second.accepted);
    var fresh=new NativeCache(base,store);var current=new NativeRestoreJob(fresh,1794821936l,null);var steps=0;
    while(!current.step()){Test.assert(fresh.packet==null);steps+=1;Test.assert(steps<20);}Test.assert(current.restored&&fresh.packet!=null);
    Test.assertEqual(fresh.packet.wireHash,"68336209054817f30ed03e2d9965c11de241a0a87f1bf38309b2e10be1f06b4d");
    Test.assert(fresh.packet.validation==1794820332l);
    var wanted=new NativeCache(base,store);var old=new NativeRestoreJob(wanted,1794821936l,oldSeal);steps=0;while(!old.step()){Test.assert(wanted.packet==null);steps+=1;Test.assert(steps<25);}Test.assert(old.restored&&wanted.packet.validation==1794812997l);
    store.write("sf.commit",{"v"=>0});var recovered=new NativeCache(base,store);var recovery=new NativeRestoreJob(recovered,1794821936l,null);steps=0;while(!recovery.step()){Test.assert(recovered.packet==null);steps+=1;Test.assert(steps<25);}Test.assert(recovery.restored&&recovered.packet.validation==1794812997l);
    Test.assertEqual(recovered.commitKey,"sf.recovery");logger.debug("B1_RESTORE exact_live=true expected_seal_old=true corrupt_commit_recovery=true no_early_publish=true");return true;
}

// The compacting path must retain the exact selected/successor facts and timing
// that the original full validated document projects, including coarse targets.
(:test,:typecheck(false)) function b1CompactingProjectionEquality(logger){
    Application.Storage.clearValues();var store=new NativeStore();b1PutCapturedCatalog(store);
    var raw=WatchUi.loadResource(Rez.JsonData.B1LiveFeed)["raw"];var now=1794821936l;
    var original=new NativeBridgeFeed(raw,now,store);var selected=feedScene(original,now).cacheRow();var rows=[];
    for(var i=0;i<original.upcomingScenes.size();i+=1){rows.add(original.upcomingScenes[i].cacheRow());}
    original=null;var compacted=new NativeBridgeFeed(raw,now,store);compacted.preparePresentation();var projected=feedSceneCompacting(compacted,now);
    Test.assert(nativeSame(selected,projected.cacheRow()));Test.assert(rows.size()==compacted.upcomingScenes.size());
    for(var j=0;j<rows.size();j+=1){Test.assert(nativeSame(rows[j],compacted.upcomingScenes[j].cacheRow()));}
    Test.assert(compacted.document["dictionaries"]==null);compacted.compact();
    Test.assertEqual(compacted.launchId(),"ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60");
    logger.debug("B1_PROJECTION captured_selected_and_successors_equal=true compact_identity=true");return true;
}

(:test,:typecheck(false)) function b1PreparedSupersededToken(logger){
    Application.Storage.clearValues();var base="https://jekamas.github.io/SpaceFox";var store=new NativeStore();b1PutCapturedCatalog(store);
    var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",WatchUi.loadResource(Rez.JsonData.B1LiveFeed)["raw"],null));
    var cache=new NativeCache(base,store);var job=new NativeAdmissionJob(cache,null,1794821936l);
    for(var i=0;i<7;i+=1){Test.assert(!job.step());Test.assert(store.read("sf.commit")==null);}
    Test.assert(transfer.stage("feed",WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"],null));
    Test.assert(job.step()&&!job.accepted&&job.retry&&store.read("sf.commit")==null&&store.read("sf.incoming.feed.processed")==null);
    logger.debug("B1_PREPARED newer_token_never_commits=true");return true;
}

(:test,:typecheck(false)) class B1FaultStore extends NativeStore {
    var failKey=null;
    function write(key,value){if(failKey!=null&&key.equals(failKey)){failKey=null;throw new Lang.InvalidValueException("injected storage failure");}NativeStore.write(key,value);}
}
(:test,:typecheck(false)) function b1PreparedFailureKeepsOldCommit(logger){
    for(var n=0;n<2;n+=1){
        Application.Storage.clearValues();var base="https://jekamas.github.io/SpaceFox";var store=new B1FaultStore();b1PutCapturedCatalog(store);
        var transfer=new NativeTransfer(base,store);var cache=new NativeCache(base,store);
        Test.assert(transfer.stage("feed",WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"],null));
        var first=new NativeAdmissionJob(cache,null,1794821936l);while(!first.step()){}Test.assert(first.accepted);var seal=cache.commit["seal"];
        Test.assert(transfer.stage("feed",WatchUi.loadResource(Rez.JsonData.B1LiveFeed)["raw"],null));
        var next=new NativeAdmissionJob(cache,null,1794821936l);for(var i=0;i<6;i+=1){Test.assert(!next.step());}
        store.failKey=n==0?"sf.feed.1.0":"sf.commit";
        while(!next.step()){}Test.assert(!next.accepted&&next.retry&&store.read("sf.commit")["seal"].equals(seal));
        var reopened=new NativeCache(base,store);var restore=new NativeRestoreJob(reopened,1794821936l,seal);while(!restore.step()){}
        Test.assert(restore.restored&&reopened.packet.validation==1794812997l);
    }
    logger.debug("B1_PREPARED chunk_and_commit_failures_preserve_old=true");return true;
}
