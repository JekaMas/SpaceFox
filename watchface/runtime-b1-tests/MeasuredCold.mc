import Toybox.Lang;
import Toybox.Application;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;

// Current public capture, with the HTTP response boundary substituted. These
// wall-clock samples are diagnostic test-host observations, not physical limits.
(:test,:typecheck(false)) function b1MeasureCapturedCallbacks(logger) {
    // Scoped to the isolated diagnostic test UUID, never the production app.
    Application.Storage.clearValues();
    var base="https://jekamas.github.io/SpaceFox";var store=new NativeStore();var transfer=new NativeTransfer(base,store);
    var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];var start=System.getTimer();Test.assert(transfer.stage("feed",raw,null));var stage=System.getTimer()-start;
    start=System.getTimer();var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));raw=null;var begin=System.getTimer()-start;
    start=System.getTimer();var request=batch.next();var maxScan=System.getTimer()-start;var maxPut=0;var objects=0;
    while(request!=null){var response=b1Response(request["path"]);Test.assert(response!=null);start=System.getTimer();Test.assert(batch.immutable.put(request,response));var elapsed=System.getTimer()-start;if(elapsed>maxPut){maxPut=elapsed;}response=null;objects+=1;Test.assert(objects<=27);start=System.getTimer();request=batch.next();elapsed=System.getTimer()-start;if(elapsed>maxScan){maxScan=elapsed;}}
    logger.debug("B1_CAPTURED_PRE_ADMIT downloaded="+objects);Test.assertEqual(objects,27);var cache=new TestNativeCache(base,store);start=System.getTimer();Test.assert(new TestNativeIncoming(store,base).admitFeed(cache,1794818604l));var admit=System.getTimer()-start;
    Test.assert(cache.packet!=null&&new NativeRenderSource(store,base,cache.packet.bridge).ready);
    logger.debug("B1_CAPTURED_CALLBACKS objects="+objects+" stageMs="+stage+" beginMs="+begin+" maxScanMs="+maxScan+" maxPutMs="+maxPut+" admitMs="+admit+" testHost=true");return true;
}
