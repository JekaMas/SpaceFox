import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;

(:test,:typecheck(false)) class DisplayStore {
    var data={};var reads=0;var writes=0;
    function initialize(){}
    function read(k){reads+=1;return data.hasKey(k)?data[k]:null;}
    function write(k,v){writes+=1;data[k]=v;}
    function remove(k){writes+=1;data.remove(k);}
}
(:test) class DisplayClock extends WatchClock {
    var now as Number=1794551202;
    function initialize(){WatchClock.initialize();}
    function utcSeconds() as Number{return now;}
    function localTimeText() as String{return "08:08";}
}
(:test,:typecheck(false)) class DisplayRecordingRenderer extends SceneRenderer {
    var activeValue=null;var lowValue=null;var activeCalls=0;var lowCalls=0;
    function initialize(){SceneRenderer.initialize(null);}
    function active(dc,current,settings,values,fitness,progress){activeValue=current.countdown;activeCalls+=1;SceneRenderer.active(dc,current,settings,values,fitness,progress);}
    function aod(dc,current,minute,settings){lowValue=current.countdown;lowCalls+=1;SceneRenderer.aod(dc,current,minute,settings);}
}
(:typecheck(false)) function displayOracle(target,now){
    var delta=target-now;var sign=delta>0?"T- ":"T+ ";if(delta<0){delta=-delta;}
    var h=delta/3600;var m=(delta-h*3600)/60;var s=delta-h*3600-m*60;
    return sign+h.format("%02d")+":"+m.format("%02d")+":"+s.format("%02d");
}
(:typecheck(false)) function displayLowOracle(target,now){var n=target-now;var future=n>0;var m=future?(n+59)/60:(-n)/60;return (future?"T- ":"T+ ")+(m/60).format("%02d")+":"+(m%60).format("%02d");}
(:typecheck(false)) function displayPacket(id){return WatchUi.loadResource(id)["raw"];}
(:test,:typecheck(false)) function displayEventSequence(logger){
    // Causal prerequisites and expected target are independent literals from
    // the captured packet oracle. Regressing initial generation is rejected.
    var clock=new DisplayClock();var store=new DisplayStore();var cat=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);
    store.write("sf.obj."+cat["catalogDigest"],cat["catalog"]);
    var cache=new TestNativeCache("https://fixture.invalid/display02",store);
    Test.assert(cache.accept(displayPacket(Rez.JsonData.DisplayInitial),clock.now));
    var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.setPacket(cache.packet);
    var drawing=new DisplayRecordingRenderer();drawing.prepare(view.context,view.settings);view.renderer=drawing;
    var frame=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();var dc=frame.getDc();
    var target=1794609900;var applied=0;var observed=0;var rejected=0;var expectedMode=0;var awake=true;
    var events=[["time",target-176523],["drawHigh",0],["sleep",0],["sleep",0],["drawLow",0],["drawLow",0],["wake",0],["wake",0],["drawHigh",0],
                ["time",target-59],["drawLow",0],["drawHigh",0],["time",target],["drawHigh",0],["drawLow",0],
                ["time",target+901],["drawLow",0],["drawHigh",0],["reopen",0],["drawHigh",0],["move",0],["reject",0],["reopen",0],
                ["drawLow",0],["drawHigh",0],["sleep",0],["wake",0],["sleep",0],["wake",0],["off",0],["drawHigh",0]];
    var matrix={};
    for(var i=0;i<events.size();i+=1){
        var row=events[i];var event=row[0];var oldApplied=applied;var oldObserved=observed;var oldRejected=rejected;
        if(event.equals("time")){clock.now=row[1];applied+=1;}
        else if(event.equals("sleep")){view.onEnterSleep();if(!awake&&expectedMode==0){observed+=1;}else{applied+=1;}awake=false;expectedMode=0;}
        else if(event.equals("wake")){view.onExitSleep();if(awake&&expectedMode==1){observed+=1;}else{applied+=1;}awake=true;expectedMode=1;}
        else if(event.equals("move")){Test.assert(cache.accept(displayPacket(Rez.JsonData.DisplayMoved),clock.now));target=1794611100;view.setPacket(cache.packet);drawing.prepare(view.context,view.settings);applied+=1;}
        else if(event.equals("reject")){var writes=store.writes;Test.assert(!cache.accept(displayPacket(Rez.JsonData.DisplayInitial),clock.now));Test.assert(store.writes==writes);rejected+=1;}
        else if(event.equals("reopen")){cache=new TestNativeCache("https://fixture.invalid/display02",store);Test.assert(cache.load(clock.now)!=null);view.setPacket(cache.packet);drawing.prepare(view.context,view.settings);applied+=1;}
        else if(event.equals("off")){var a=drawing.activeCalls;var l=drawing.lowCalls;view.updateForDisplayMode(dc,System.DISPLAY_MODE_OFF);expectedMode=0;Test.assert(a==drawing.activeCalls&&l==drawing.lowCalls);observed+=1;}
        else {var high=event.equals("drawHigh");expectedMode=high&&awake?1:0;var count=expectedMode==1?drawing.activeCalls:drawing.lowCalls;view.updateForDisplayMode(dc,high?System.DISPLAY_MODE_HIGH_POWER:System.DISPLAY_MODE_LOW_POWER);var after=expectedMode==1?drawing.activeCalls:drawing.lowCalls;if(after>count){Test.assertEqual(expectedMode==1?drawing.activeValue:drawing.lowValue,expectedMode==1?displayOracle(target,clock.now):displayLowOracle(target,clock.now));applied+=1;}else{observed+=1;}}
        Test.assertEqual(view.displayMode(),expectedMode);
        Test.assertEqual(view.snapshot().countdown,displayOracle(target,clock.now));
        var disposition=applied>oldApplied?"applied":observed>oldObserved||rejected>oldRejected?"observed_no_mutation":"skipped_precondition";
        var key=event+":"+disposition;matrix[key]=matrix.hasKey(key)?matrix[key]+1:1;
    }
    var required=["time:applied","sleep:applied","sleep:observed_no_mutation","wake:applied","wake:observed_no_mutation","drawHigh:applied","drawLow:applied","drawLow:observed_no_mutation","off:observed_no_mutation","reopen:applied","move:applied","reject:observed_no_mutation"];
    for(var j=0;j<required.size();j+=1){Test.assert(matrix.hasKey(required[j])&&matrix[required[j]]>0);}
    Test.assert(applied>0&&observed>0&&rejected>0);Test.assert(drawing.activeCalls>0&&drawing.lowCalls>0);
    logger.debug("DISPLAY02 directed applied="+applied+" observed_no_mutation="+(observed+rejected)+" includes_rejected="+rejected+" skipped=0");
 return true;
}
(:test,:typecheck(false)) function displayRealSiteMarker(logger){
    var settings=new SceneSettings(null);var d=new SceneRenderer(null);
    var c=new SceneContext({"id"=>"ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b","rocket"=>"Starship V3","site"=>"Orbital Launch Pad 2","point"=>[-97.15799,25.99677]});
    d.prepare(c,settings);Test.assert(d.pin&&d.pinX==335&&d.pinY==165);
    var captured=new SceneContext({"id"=>"ll2:launch:de446468-057f-4c9d-a6a1-af99c93b541e","rocket"=>"Zhuque-2E Block 2","site"=>"Launch Area 96A","point"=>[100.245488,40.91491]});
    d.prepare(captured,settings);Test.assert(d.pin&&d.map!=null);
    d.prepare(new SceneContext({"id"=>"ll2:launch:de446468-057f-4c9d-a6a1-af99c93b541e"}),settings);Test.assert(!d.pin);
    logger.debug("MARKER real Starbase and captured Launch Area 96A; missing point rejected");return true;
}
import Toybox.Lang;
import Toybox.Test;
(:test,:typecheck(false)) function displayCapturedZhuqueMarker(logger){
 var d=new SceneRenderer(null);var c=new SceneContext({"id"=>"ll2:launch:de446468-057f-4c9d-a6a1-af99c93b541e","rocket"=>"Zhuque-2E Block 2","site"=>"Launch Area 96A","point"=>[100.245488,40.91491]});
 d.prepare(c,new SceneSettings(null));logger.debug("CAPTURED_ZHUQUE pin="+d.pin);Test.assert(d.pin);return true;
}

(:test,:typecheck(false)) function displayAssetJobSequence(logger){
 var m=new SceneLifecycle();m.replace();Test.assert(m.request(1));Test.assert(!m.request(1));var old=m.begin();Test.assert(old!=null);m.cancel();Test.assert(!m.complete(old));Test.assert(m.request(2));var now=m.begin();Test.assert(now!=null&&now!=old);m.fail(now);Test.assert(!m.pending()&&!m.request(2));m.replace();Test.assert(m.request(3));var current=m.begin();Test.assert(!m.complete(now));Test.assert(m.complete(current));Test.assert(m.job==null);logger.debug("JOB replace request duplicate begin cancel staleComplete fail blocked retry newBatch complete");return true;
}
(:test,:typecheck(false)) function displayPairedInputs(logger){
 var clock=new DisplayClock();var store=new DisplayStore();var cat=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);store.write("sf.obj."+cat["catalogDigest"],cat["catalog"]);
 var cache=new TestNativeCache("https://fixture.invalid/display-pair",store);Test.assert(cache.accept(displayPacket(Rez.JsonData.DisplayInitial),clock.now));
 var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.setPacket(cache.packet);var renderer=new DisplayRecordingRenderer();renderer.prepare(view.context,view.settings);view.renderer=renderer;
 var frame=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();var target=1794609900;var times=[target-176523,target-59,target,target+1,target+901];
 for(var i=0;i<times.size();i+=1){clock.now=times[i];view.updateForDisplayMode(frame.getDc(),System.DISPLAY_MODE_HIGH_POWER);view.updateForDisplayMode(frame.getDc(),System.DISPLAY_MODE_LOW_POWER);var expected=displayOracle(target,clock.now);Test.assertEqual(renderer.activeValue,expected);Test.assertEqual(renderer.lowValue,displayLowOracle(target,clock.now));logger.debug("PAIR utc="+clock.now+" target="+target+" active="+renderer.activeValue+" low="+renderer.lowValue+" oracle="+expected);}
 return true;
}
(:test,:typecheck(false)) function displayBatchRetry(logger){
 var store=new DisplayStore();var base="https://fixture.invalid/batch";var transfer={"sha256"=>"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"};var bridge={"catalogDigest"=>"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","transfer"=>transfer};
 store.write("sf.batch.head",{"base"=>base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>transfer,"serial"=>1});store.write("sf.batch.pending",{"base"=>base,"pending"=>false});
 var view=new SpaceFoxView(new DisplayClock(),new ScheduleState(null,"empty"));view.setContext(new SceneContext({"id"=>"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"}));view.setAssetCache(new NativeRenderSource(store,base,bridge));Test.assert(view.assetCache.ready);
 Test.assert(view.sceneLifecycle.request(1));var old=view.sceneLifecycle.begin();view.sceneLifecycle.fail(old);
 view.setAssetCache(new NativeRenderSource(store,base,bridge));Test.assert(!view.sceneLifecycle.request(1));
 store.write("sf.batch.head",{"base"=>base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>transfer,"serial"=>2});
 view.setAssetCache(new NativeRenderSource(store,base,bridge));Test.assert(view.sceneLifecycle.request(2));Test.assert(!view.sceneLifecycle.complete(old));var current=view.sceneLifecycle.begin();Test.assert(current!=old&&view.sceneLifecycle.complete(current));
 logger.debug("BATCH_RETRY sameBatchNoMutation=true newSerialApplied=true staleCompletionRejected=true");return true;
}
(:test,:typecheck(false)) function displayHighBeforeShow(logger){
 var store=new DisplayStore();var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);var base="https://fixture.invalid/display-show";
 var cache=new TestNativeCache(base,store);var clock=new DisplayClock();Test.assert(cache.accept(displayPacket(Rez.JsonData.DisplayInitial),clock.now));var bridge=cache.packet.bridge;
 store.write("sf.batch.head",{"base"=>base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>1});store.write("sf.batch.pending",{"base"=>base,"pending"=>false});
 Application.Properties.setValue("FeedBaseUrl",base);var app=new SpaceFoxApp();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));app.view=view;app.feed=cache;view.setPacket(cache.packet);view.setAssetCache(new NativeRenderSource(store,base,bridge));view.pendingLoader=app.method(:reloadFeed);
 view.syncDisplayMode(System.DISPLAY_MODE_HIGH_POWER);view.onShow();Test.assert(!view.sceneLifecycle.pending());Test.assert(view.sfrTimer==null);var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();view.onLayout(dc);view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assert(!view.canForegroundWork());view.onHide();Application.Properties.setValue("FeedBaseUrl","");
 logger.debug("HIGH_BEFORE_SHOW productionReloadWired=true completedBatch=true deferredThroughFirstFrame=true");return true;
}
