import Toybox.Graphics;
import Toybox.Application;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;

(:test,:typecheck(false)) class B1DecodeClock extends WatchClock {
    var now=1794551202;
    function utcSeconds(){return now;}
    function localTimeText(){return "08:38";}
}
(:test,:typecheck(false)) class B1DecodeRecorder extends SceneRenderer {
    var calls=0;var currentText=null;
    function initialize(){SceneRenderer.initialize(null);}
    function active(dc,current,settings,values,fitness,progress){calls+=1;currentText=current.countdown;}
}
(:test,:typecheck(false)) class B1DecodeView extends SpaceFoxView {
    var observedClock;var fallbackText=null;
    function initialize(clock){SpaceFoxView.initialize(clock,new ScheduleState(null,"empty"));observedClock=clock;}
    function drawClockFallback(dc){SpaceFoxView.drawClockFallback(dc);fallbackText=snapshotAt(observedClock.now).countdown;}
}
// Keep fixture staging and parser invocation in a smaller frame than the
// measurement observer. The earlier larger-frame stack failure is retained.
(:typecheck(false)) function b1StageProfile(store,base) {
    var raw=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];
    var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",raw,null));
    var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));raw=null;
    var started=System.getTimer();var request=batch.next();var objects=0;var maxScan=System.getTimer()-started;var maxPut=0;
    while(request!=null){var start=System.getTimer();var response=b1ProfileResponse(request["path"]);Test.assert(response!=null&&batch.immutable.put(request,response));var elapsed=System.getTimer()-start;if(elapsed>maxPut){maxPut=elapsed;}response=null;objects+=1;Test.assert(objects<=18);start=System.getTimer();request=batch.next();elapsed=System.getTimer()-start;if(elapsed>maxScan){maxScan=elapsed;}}
    Test.assertEqual(objects,18);return [objects,maxScan,maxPut];
}
(:typecheck(false)) function b1ObserveDecode(logger,store,cache,clock,counts) {
    var view=new B1DecodeView(clock);view.setPacket(cache.packet);
    var recorder=new B1DecodeRecorder();recorder.prepare(view.context,view.settings);view.renderer=recorder;
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();view.onShow();view.onLayout(dc);
    view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);logger.debug("B1_DECODE_INITIAL countdown="+recorder.currentText);Test.assertEqual(recorder.currentText,"T- 16:18:18");
    view.setAssetCache(new NativeRenderSource(store,cache.base,cache.packet.bridge));view.prepareVisual();var beginAt=System.getTimer();view.sfrStep();var beginMs=System.getTimer()-beginAt;Test.assert(view.sfrBuild!=null&&view.fallbackClockTimer!=null);
    var maxSlice=0;var maxPhase="";var maxRole=-1;var maxRow=-1;var steps=0;
    while(steps<20&&view.sfrBuild!=null){var job=view.sfrBuild;var role=job.role;var phase=job.decoder==null?"role":(job.decoder.data==null?"chunk":"rows");var row=job.decoder==null?-1:job.decoder.y;var start=System.getTimer();view.sfrStep();var elapsed=System.getTimer()-start;if(elapsed>maxSlice){maxSlice=elapsed;maxRole=role;maxPhase=phase;maxRow=row;}steps+=1;}
    Test.assert(view.sfrBuild!=null&&view.renderer==null);clock.now+=2;view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assertEqual(view.fallbackText,"T- 16:18:16");
    clock.now+=31;view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assertEqual(view.fallbackText,"T- 16:17:45");
    var preserved=view.sfrBuild;Test.assert(preserved.decoder!=null);var previousRow=preserved.decoder.y;
    for(var cycle=0;cycle<3;cycle+=1){
        var sleeping=cycle==1?System.DISPLAY_MODE_OFF:System.DISPLAY_MODE_LOW_POWER;
        view.syncDisplayMode(sleeping);Test.assert(view.sfrBuild==preserved&&view.sfrTimer==null&&view.fallbackClockTimer==null);
        view.updateForDisplayMode(dc,sleeping);Test.assert(view.sfrBuild==preserved&&view.sfrTimer==null);
        Test.assertEqual(view.snapshotAt(clock.now).lowCountdown,"T- 16:18");
        view.syncDisplayMode(System.DISPLAY_MODE_HIGH_POWER);view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assertEqual(view.fallbackText,"T- 16:17:45");
        view.stopResume();view.resumeAfterFrame();for(var step=0;step<8;step+=1){view.sfrStep();}
        Test.assert(view.sfrBuild==preserved&&preserved.decoder!=null&&preserved.decoder.y>previousRow);previousRow=preserved.decoder.y;
    }
    view.onHide();Test.assert(view.sfrBuild==null&&view.sfrTimer==null);
    logger.debug("B1_REAL_DECODE selected_min=true objects="+counts[0]+" beginMs="+beginMs+" slices="+steps+" maxSliceMs="+maxSlice+" maxPhase="+maxPhase+" maxRole="+maxRole+" maxRow="+maxRow+" maxBatchScanMs="+counts[1]+" maxPutMs="+counts[2]+" activeCatchup=true lowOffHighCyclesAdvance=true hideCancel=true testHost=true");return true;
}
// Production parser, durable store, immutable closure and SFR builder execute;
// the renderer observer captures countdown text rather than pixels. This is a
// test-host execution, not an ordinary app heap or graphics-pool measurement.
(:test,:typecheck(false)) function b1RealDecodeTicksAndCancels(logger) {
    Application.Storage.clearValues();
    var base="https://fixture.invalid/profile-a";var store=new NativeStore();
    var counts=b1StageProfile(store,base);var clock=new B1DecodeClock();var cache=new NativeCache(base,store);
    Test.assert(new NativeIncoming(store,base).admitFeed(cache,clock.now));
    return b1ObserveDecode(logger,store,cache,clock,counts);
}

(:test,:typecheck(false)) class B1BudgetDecodeView extends B1DecodeView {
    var freeBytes=0;
    function initialize(clock){B1DecodeView.initialize(clock);}
    function optionalHeapFree(){return freeBytes;}
}
(:test,:typecheck(false)) function b1LowHeapDefersOptionalDecode(logger){
    Application.Storage.clearValues();var base="https://fixture.invalid/profile-a";var store=new NativeStore();b1StageProfile(store,base);
    var clock=new B1DecodeClock();var cache=new NativeCache(base,store);Test.assert(new NativeIncoming(store,base).admitFeed(cache,clock.now));
    var view=new B1BudgetDecodeView(clock);view.setPacket(cache.packet);var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    view.onShow();view.onLayout(dc);view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);view.setAssetCache(new NativeRenderSource(store,base,cache.packet.bridge));view.prepareVisual();
    view.freeBytes=view.sfrReadReserve()-1;view.sfrStep();Test.assert(view.sfrBuild==null&&view.sfrDeferred&&view.sceneLifecycle.pending()&&view.fallbackClockTimer!=null);
    // A deferred preflight has no builder yet, but still owns the optional
    // memory budget. Settings and LOW/HIGH wake must not restart fitness.
    var fields=new B1AdmissionFields();view.selectedFields=fields;view.fitness=new B1AdmissionFitness();
    var settings=new SceneSettings({"Field1"=>1,"Field2"=>2,"Field3"=>3,"Field4"=>4});
    view.setSettings(settings);view.refreshFitness();view.fieldsChanged(new Toybox.Complications.Id(23));
    Test.assert(fields.starts==0&&fields.reads==0&&view.fitnessTimer==null);
    view.syncDisplayMode(System.DISPLAY_MODE_LOW_POWER);view.syncDisplayMode(System.DISPLAY_MODE_HIGH_POWER);
    view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);view.stopResume();view.resumeAfterFrame();
    Test.assert(fields.starts==0&&fields.reads==0&&view.fitnessTimer==null&&view.sfrBuild==null&&!view.animationRunning);
    view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assert(view.renderer==null&&LocaleGraphemes.data==null);Test.assertEqual(view.fallbackText,"T- 16:18:18");clock.now+=2;view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assertEqual(view.fallbackText,"T- 16:18:16");
    view.freeBytes=view.sfrReadReserve();view.sfrStep();Test.assert(view.sfrBuild!=null&&!view.sfrDeferred);
    view.freeBytes=view.sfrReadReserve();view.sfrStep();Test.assert(view.sfrBuild.decoder!=null&&view.sfrBuild.decoder.shard==0);
    var shardReserve=view.sfrReadReserve();view.freeBytes=shardReserve-1;view.sfrStep();
    Test.assert(view.sfrDeferred&&view.sfrBuild.decoder.shard==0&&view.sfrBuild.decoder.data==null);
    view.freeBytes=shardReserve;view.sfrStep();Test.assert(!view.sfrDeferred&&view.sfrBuild.decoder.shard==1&&view.sfrBuild.decoder.data!=null);
    view.syncDisplayMode(System.DISPLAY_MODE_LOW_POWER);Test.assert(view.sfrBuild!=null&&view.sfrTimer==null&&view.fallbackClockTimer==null);view.onHide();Test.assert(view.sfrBuild==null);
    logger.debug("B1_OPTIONAL_RESERVE deferred_without_allocation=true ticking=true recovery=true low_pause_hide_cancel=true");return true;
}
