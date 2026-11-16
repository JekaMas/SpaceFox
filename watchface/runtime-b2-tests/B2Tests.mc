import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

// Literal independent values, including accumulating hours and the zero boundary.
(:test,:typecheck(false)) function b2ArithmeticAndRetention(logger){
    var target=1800000000l;var state=new ScheduleState(target,"exact");
    Test.assertEqual(state.display(target-156131),"T- 43:22:11");
    Test.assertEqual(state.display(target-59),"T- 00:00:59");
    Test.assertEqual(state.display(target),"T+ 00:00:00");
    Test.assertEqual(state.display(target+1),"T+ 00:00:01");
    Test.assertEqual(CountdownFormat.minutes(1),"T- 00:01");
    Test.assertEqual(CountdownFormat.minutes(0),"T+ 00:00");
    Test.assertEqual(new ScheduleState(target,"source-coarse").display(target-59),"--:--:--");
    var v=new SpaceFoxView(new B1ExactClock(),state);
    var a=new SceneContext({"id"=>"ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b","precision"=>"exact","target"=>target,"retentionDeadline"=>target+1800});
    var b=new SceneContext({"id"=>"ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60","precision"=>"unknown"});
    v.setContext(a);v.upcoming=[b];v.advanceSelection(target+899);Test.assert(v.context==a);
    v.advanceSelection(target+1799);Test.assert(v.context==a);v.advanceSelection(target+1800);Test.assert(v.context==b);
    logger.debug("B2_ARITHMETIC literal43h under60 zero coarseUnknown laterAscentRetention");return true;
}

// Catalog and feed only: no decorative transfer closure or downloaded map.
(:test,:typecheck(false)) function b2AdmittedFactsWithoutArt(logger){
    var store=new B1MemoryStore();var base="https://fixture.invalid/profile-a";var now=1794551202l;
    var raw=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];var batch=new NativeBatch(store,base);
    Test.assert(batch.begin(raw));var ref=batch.next();Test.assert(ref!=null&&batch.immutable.put(ref,b1ProfileResponse(ref["path"])));
    var cache=new NativeCache(base,store);Test.assert(b1Promote021(cache,raw,now));var scene=feedScene(cache.packet,now);
    Test.assert(scene.launchId.equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"));
    Test.assert(scene.rocket.equals("Starship V3")&&scene.site.find("Starbase")!=null);
    Test.assert(scene.sourceValidated==1794551192l&&scene.point!=null&&scene.point[0]==-97.15799f&&scene.point[1]==25.99677f);
    Test.assertEqual(scene.schedule.display(now),"T- 16:18:18");
    var v=new SpaceFoxView(new B1DecodeClock(),new ScheduleState(null,"empty"));v.setPacket(cache.packet);
    Test.assertEqual(v.snapshotAt(now).countdown,"~T- 16:18:18");
    Test.assertEqual(v.snapshotAt(now).lowCountdown,"~T- 16:19");
    Test.assert(v.assetCache==null&&v.downloaded==null&&v.context.point!=null);
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    v.admissionPending=true;v.drawClockFallback(dc);Test.assert(v.renderer==null&&v.context.point!=null);
    var r=new SceneRenderer(null);r.prepare(v.context,v.settings);Test.assert(r.pin&&r.fullContext==v.context);
    logger.debug("B2_FACTS captured_MIN catalogOnly point=-97.15799,25.99677 sourceAge=1794551192 optionalArtAbsent");return true;
}

(:test,:typecheck(false)) function b2FailedAndInterruptedReplacement(logger){
    var base="https://fixture.invalid/profile-a";var now=1794551202l;
    var older=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];var newer=WatchUi.loadResource(Rez.JsonData.B1ProfileNext)["raw"];
    for(var mode=0;mode<3;mode+=1){
        var s=new B1FailingStore021();var batch=new NativeBatch(s,base);Test.assert(batch.begin(older));var a=batch.next();Test.assert(batch.immutable.put(a,b1ProfileResponse(a["path"])));
        Test.assert(batch.begin(newer));var b=batch.next();Test.assert(batch.immutable.put(b,WatchUi.loadResource(Rez.JsonData.B1ProfileNextCatalog)["raw"]));
        var cache=new NativeCache(base,s);Test.assert(b1Promote021(cache,older,now));var old=feedScene(cache.packet,now);var age=old.sourceValidated;var generation=cache.packet.document["publisher"]["generation"];var seal=cache.commit["seal"];
        var packet=new NativePreparedBridgeFeed(newer,now,s);while(!packet.prepareStep()){}var promotion=new NativeFeedPromotion(cache,newer,packet,now,null);
        if(mode==0){Test.assert(!promotion.step());s.failKey="sf.feed."+promotion.slot+".0";while(!promotion.step()){}Test.assert(!promotion.accepted);}
        else if(mode==1){s.failKey="sf.commit";while(!promotion.step()){}Test.assert(!promotion.accepted);}
        else{Test.assert(!promotion.step());} // process interruption before commit
        var reopened=new NativeCache(base,s);var restore=new NativeRestoreJob(reopened,now,seal);while(!restore.step()){}Test.assert(restore.accepted);
        var actual=feedScene(reopened.packet,now);Test.assert(reopened.packet.document["publisher"]["generation"]==generation);
        Test.assert(actual.launchId.equals(old.launchId)&&actual.rocket.equals(old.rocket)&&actual.site.equals(old.site)&&actual.point!=null&&old.point!=null&&actual.point[0]==old.point[0]&&actual.point[1]==old.point[1]);
        Test.assert(actual.retentionTarget==old.retentionTarget&&actual.sourceValidated==age&&age==1794551192l);
    }
    logger.debug("B2_RECOVERY chunk commit interruption oldIdentityGenerationPointTargetAge");return true;
}

(:test,:typecheck(false)) function b2CapturedHourAndMissingPoint(logger){
    var s=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var now=1794818604l;
    var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];b1Catalog021(s,base,raw);
    var cache=new NativeCache(base,s);Test.assert(b1Promote021(cache,raw,now));var selected=feedScene(cache.packet,now);
    Test.assert(selected.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));
    Test.assert(selected.point!=null&&selected.point[0]==111.589567f&&selected.point[1]==38.863128f);
    Test.assertEqual(selected.schedule.display(now),"--:--:--");var v=new SpaceFoxView(new B1Clock(),new ScheduleState(null,"empty"));v.setContext(selected);Test.assertEqual(v.snapshotAt(now).countdown,"~"+CountdownFormat.format(selected.displayTarget-now));
    var renderer=new SceneRenderer(null);renderer.prepare(selected,new SceneSettings(null));Test.assert(renderer.pin);
    // A mobile/unknown event position is represented by a null point, never a reference-as-event substitution.
    var absent=new SceneContext({"id"=>selected.launchId,"precision"=>"unknown"});renderer.prepare(absent,new SceneSettings(null));Test.assert(absent.point==null&&!renderer.pin&&!renderer.worldFallback);
    logger.debug("B2_HOUR actualTaiyuan sourcePointUnverified nominalNotExact missingNoPoint");return true;
}

(:test,:typecheck(false)) function b2RescheduleAndNewSelection(logger){
    var s=new B1MemoryStore();var base="https://fixture.invalid/profile-a";var now=1794551202l;
    var first=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];var moved=WatchUi.loadResource(Rez.JsonData.B2Moved)["raw"];var different=WatchUi.loadResource(Rez.JsonData.B2Different)["raw"];
    var batch=new NativeBatch(s,base);Test.assert(batch.begin(first));var a=batch.next();Test.assert(batch.immutable.put(a,b1ProfileResponse(a["path"])));
    Test.assert(batch.begin(different));var d=batch.next();Test.assert(batch.immutable.put(d,WatchUi.loadResource(Rez.JsonData.B2DifferentCatalog)["raw"]));
    var cache=new NativeCache(base,s);Test.assert(b1Promote021(cache,first,now));var v=new SpaceFoxView(new B1DecodeClock(),new ScheduleState(null,"empty"));v.setPacket(cache.packet);
    var initial=v.context;Test.assert(initial.launchId.equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b")&&initial.retentionTarget==1794609900l&&initial.sourceValidated==1794551192l);
    Test.assert(b1Promote021(cache,moved,now));v.setPacket(cache.packet);var rescheduled=v.context;
    Test.assert(rescheduled.launchId.equals(initial.launchId)&&rescheduled.retentionTarget==1794611100l&&rescheduled.sourceValidated==1794551193l&&rescheduled.rescheduled);
    Test.assert(cache.packet.document["publisher"]["generation"]==2&&rescheduled.point[0]==-97.15799f&&rescheduled.point[1]==25.99677f&&rescheduled.site.equals(initial.site));
    Test.assertEqual(v.snapshotAt(now).countdown,"~T- 16:38:18");
    Test.assert(b1Promote021(cache,different,now));v.setPacket(cache.packet);var next=v.context;
    // Existing fixture changes identity as a technical discriminator but retains real display strings.
    Test.assert(next.launchId.equals("ll2:launch:00000000-0000-4000-8000-000000000002")&&next.retentionTarget==1794609900l&&next.sourceValidated==1794551197l);
    Test.assert(cache.packet.document["publisher"]["generation"]==6&&next.point[0]==-97.15799f&&next.point[1]==25.99677f&&!next.rescheduled);
    Test.assert(v.downloaded==null&&v.assetCache==null);logger.debug("B2_REPLACEMENT reschedule=2 newSelection=6 coherent facts optionalArtAbsent");return true;
}

(:test,:typecheck(false)) function b2LowUnmatchedPoint(logger){
    // Technical coordinate boundary over an existing real display identity:
    // southern point is below the LOW foreground clearing band's upper edge.
    var scene=new SceneContext({"id"=>"ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b","rocket"=>"Starship V3","site"=>"Starbase","point"=>[-97.15799f,-80.0f],"precision"=>"minute","target"=>1794609900l});
    var settings=new SceneSettings(null);var renderer=new SceneRenderer(null);renderer.prepare(scene,settings);renderer.prepareAod();
    Test.assert(renderer.worldFallback&&!renderer.pin&&scene.point!=null);
    var frame=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();var clock=new ClockSnapshot("08:38","~T- 16:19");clock.localCalendar=[1,16,11];
    renderer.aod(frame.getDc(),clock,0l,settings);
    // Once a downloaded outline is ready, use its centered marker alone;
    // the fallback projection must not be overlaid at a second location.
    Test.assert(renderer.aodWorldPoint(false,false)!=null);
    Test.assert(renderer.aodWorldPoint(false,true)==null);
    var rich=new NativeSfrRenderer();rich.scene={"position"=>scene.point};rich.mapOutline=frame;renderer.downloaded=rich;
    renderer.aod(frame.getDc(),clock,1l,settings);
    // The same unmatched source point must also be drawable before admission
    // and optional artwork finish, through the normal pending owners.
    var pending=new SpaceFoxView(new B1Clock(),new ScheduleState(null,"empty"));pending.setContext(scene);pending.admissionPending=true;pending.drawPendingLow(frame.getDc());pending.admissionPending=false;pending.sfrFallbackPrepared=true;pending.drawDecodingFrame(frame.getDc());Test.assert(pending.context==scene&&scene.point!=null);
    logger.debug("B2_LOW unmatchedSouthernPoint fallbackRendererDraw completed");return true;
}

(:test,:typecheck(false)) function b2SourcedAscentRetention(logger){
    var store=new B1MemoryStore();var base="https://fixture.invalid/ascent";var now=1794576345l;
    var raw=WatchUi.loadResource(Rez.JsonData.B2Ascent)["raw"];var catalog=WatchUi.loadResource(Rez.JsonData.B2AscentCatalog)["raw"];
    var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));var ref=batch.next();Test.assert(ref!=null&&batch.immutable.put(ref,catalog));
    var cache=new NativeCache(base,store);Test.assert(b1Promote021(cache,raw,now));var scene=feedScene(cache.packet,now);
    // The fixture is a technical sourced-supplement mutation over a real launch,
    // not an assertion that the example.invalid URL supplied a real ascent.
    Test.assert(scene.launchId.equals("ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"));
    Test.assert(scene.retentionTarget==1794583543l&&scene.retentionDeadline==1794585343l&&scene.sourceValidated==1794576343l);
    var v=new SpaceFoxView(new B1ExactClock(),new ScheduleState(null,"empty"));v.setContext(scene);
    var successor=new SceneContext({"id"=>"ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b","precision"=>"unknown"});v.upcoming=[successor];
    v.advanceSelection(1794584443l);Test.assert(v.context==scene);v.advanceSelection(1794585342l);Test.assert(v.context==scene);
    v.advanceSelection(1794585343l);Test.assert(v.context==successor);
    logger.debug("B2_ASCENT acceptedSupplement targetPlus1800 retainedThrough1799 successorAt1800 originalAge=true");return true;
}

(:test,:typecheck(false)) function b2CrossVmSeedInterrupted(logger){
    Toybox.Application.Storage.clearValues(); // isolated diagnostic UUID only
    var store=new NativeStore();var base="https://fixture.invalid/profile-a";var now=1794551202l;
    var older=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];var newer=WatchUi.loadResource(Rez.JsonData.B1ProfileNext)["raw"];
    var batch=new NativeBatch(store,base);Test.assert(batch.begin(older));var a=batch.next();Test.assert(batch.immutable.put(a,b1ProfileResponse(a["path"])));
    Test.assert(batch.begin(newer));var b=batch.next();Test.assert(batch.immutable.put(b,WatchUi.loadResource(Rez.JsonData.B1ProfileNextCatalog)["raw"]));
    var cache=new NativeCache(base,store);Test.assert(b1Promote021(cache,older,now));var seal=cache.commit["seal"];
    var packet=new NativePreparedBridgeFeed(newer,now,store);while(!packet.prepareStep()){}var promotion=new NativeFeedPromotion(cache,newer,packet,now,null);
    var steps=0;while(promotion.phase<4&&!promotion.done){promotion.step();steps+=1;Test.assert(steps<100);}
    Test.assert(!promotion.done&&promotion.phase==4&&store.read("sf.commit")["seal"].equals(seal));
    store.write("sf.b2.expectedSeal",seal);logger.debug("B2_VM_SEED oldCommit=1 newChunksWritten=1 newCommit=0 age=1794551192");return true;
}
(:test,:typecheck(false)) function b2CrossVmObserveRestored(logger){
    var store=new NativeStore();var base="https://fixture.invalid/profile-a";var seal=store.read("sf.b2.expectedSeal");Test.assert(seal instanceof String);
    var cache=new NativeCache(base,store);var restore=new NativeRestoreJob(cache,1794551202l,seal);while(!restore.step()){}Test.assert(restore.accepted);
    var scene=feedScene(cache.packet,1794551202l);Test.assert(cache.packet.document["publisher"]["generation"]==1);
    Test.assert(scene.launchId.equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b")&&scene.rocket.equals("Starship V3")&&scene.site.find("Starbase")!=null);
    Test.assert(scene.point[0]==-97.15799f&&scene.point[1]==25.99677f&&scene.retentionTarget==1794609900l&&scene.sourceValidated==1794551192l);
    logger.debug("B2_VM_OBSERVE restoredOldIdentityGenerationPointTargetAge");return true;
}
