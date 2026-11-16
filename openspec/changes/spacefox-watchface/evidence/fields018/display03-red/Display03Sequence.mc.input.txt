import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;
import Toybox.Time;
import Toybox.Application;

(:test,:typecheck(false)) class D03Store {
 var data={};var writes=0;function read(k){return data.hasKey(k)?data[k]:null;}function write(k,v){data[k]=v;writes+=1;}function remove(k){data.remove(k);writes+=1;}
}
(:test,:typecheck(false)) class D03Recording extends SceneRenderer {
 var activeCount=0;var lowCount=0;var activeText=null;var lowText=null;
 function initialize(){SceneRenderer.initialize(null);}
 function active(dc,s,settings,values,fitness,progress){activeCount+=1;activeText=s.countdown;SceneRenderer.active(dc,s,settings,values,fitness,progress);}
 function aod(dc,s,minute,settings){lowCount+=1;lowText=s.countdown;SceneRenderer.aod(dc,s,minute,settings);}
}
(:typecheck(false)) function d03ActiveOracle(target,now){var n=target-now;var sign=n>0?"T- ":"T+ ";if(n<0){n=-n;}return sign+(n/3600).format("%02d")+":"+((n%3600)/60).format("%02d")+":"+(n%60).format("%02d");}
(:typecheck(false)) function d03LowOracle(target,now){var n=target-now;var future=n>0;var minutes=future?(n+59)/60:(-n)/60;return (future?"T- ":"T+ ")+(minutes/60).format("%02d")+":"+(minutes%60).format("%02d");}
(:test,:typecheck(false)) function display03CausalSequence(logger){
 // Generated tail follows a directed prefix. Expectations use literal fixture
 // target times and event history, never a value read from the SUT.
 var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);
 var initial=WatchUi.loadResource(Rez.JsonData.DisplayInitial)["raw"];
 var moved=WatchUi.loadResource(Rez.JsonData.DisplayMoved)["raw"];
 for(var seed=1;seed<=5;seed+=1){
  var clock=new Display03Clock();clock.now=1794551202;var store=new D03Store();store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
  var cache=new NativeCache("https://fixture.invalid/display03",store);Test.assert(cache.accept(initial,clock.now));
  var v=new SpaceFoxView(clock,new ScheduleState(null,"empty"));v.setPacket(cache.packet);var d=new D03Recording();d.prepare(v.context,v.settings);v.renderer=d;v.onShow();
  var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();var target=1794609900;var awake=true;var display=System.DISPLAY_MODE_HIGH_POWER;var previousMode=1;var lastLow=null;
  var events=["tick","sleep","ready","sleep","high","tick","wake","wake","low","tick","tick","advance","tick","high","tick","move","reject","tick"];
  var random=seed;for(var k=0;k<12;k+=1){random=(random*73+19)%997;events.add(["sleep","wake","low","high","advance","tick"][random%6]);}
  var matrix={};
  for(var i=0;i<events.size();i+=1){
   var event=events[i];var disposition="applied";
   if(event.equals("sleep")){if(!awake&&previousMode==0){disposition="observed_no_mutation";}awake=false;v.onEnterSleep();if(previousMode!=0){lastLow=null;}previousMode=0;Test.assertEqual(v.displayMode(),0);}
   else if(event.equals("wake")){if(awake&&previousMode==1){disposition="observed_no_mutation";}awake=true;v.onExitSleep();if(previousMode!=1){lastLow=null;}previousMode=1;Test.assertEqual(v.displayMode(),1);}
   else if(event.equals("low")||event.equals("high")){
    display=event.equals("low")?System.DISPLAY_MODE_LOW_POWER:System.DISPLAY_MODE_HIGH_POWER;
    var nextMode=awake&&display==System.DISPLAY_MODE_HIGH_POWER?1:0;v.syncDisplayMode(display);
    if(previousMode==nextMode){disposition="observed_no_mutation";}else{lastLow=null;}previousMode=nextMode;Test.assertEqual(v.displayMode(),nextMode);
   }
   else if(event.equals("advance")){clock.now+=1;}
   else if(event.equals("ready")){var bridge=cache.packet.bridge;store.write("sf.batch.head",{"base"=>cache.base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>1});store.write("sf.batch.pending",{"base"=>cache.base,"pending"=>false});v.setAssetCache(new NativeRenderSource(store,cache.base,bridge));v.prepareVisual();Test.assert(v.assetCache.ready&&v.sceneLifecycle.pending()&&v.sfrTimer==null);}
   else if(event.equals("move")){Test.assert(cache.accept(moved,clock.now));target=1794611100;v.setPacket(cache.packet);lastLow=null;}
   else if(event.equals("reject")){var before=store.writes;Test.assert(!cache.accept(initial,clock.now));Test.assertEqual(store.writes,before);disposition="observed_no_mutation";}
   else {
    var mode=awake&&display==System.DISPLAY_MODE_HIGH_POWER?1:0;var ac=d.activeCount;var lc=d.lowCount;
    if(mode!=previousMode){lastLow=null;}previousMode=mode;var minute=clock.now/60;
    v.updateForDisplayMode(dc,display);
    if(mode==1){Test.assert(d.activeCount==ac+1&&d.lowCount==lc);Test.assertEqual(d.activeText,d03ActiveOracle(target,clock.now));}
    else if(lastLow==minute){Test.assert(d.lowCount==lc&&d.activeCount==ac);disposition="observed_no_mutation";}
    else{Test.assert(d.lowCount==lc+1&&d.activeCount==ac);Test.assertEqual(d.lowText,d03LowOracle(target,clock.now));lastLow=minute;}
    Test.assertEqual(v.displayMode(),mode);
   }
   Test.assertEqual(v.snapshot().countdown,d03ActiveOracle(target,clock.now));
   var key=event+":"+disposition;matrix[key]=matrix.hasKey(key)?matrix[key]+1:1;
  }
  var required=["tick:applied","tick:observed_no_mutation","sleep:applied","sleep:observed_no_mutation","wake:applied","wake:observed_no_mutation","low:applied","high:applied","advance:applied","ready:applied","move:applied","reject:observed_no_mutation"];
  for(var j=0;j<required.size();j+=1){Test.assert(matrix.hasKey(required[j])&&matrix[required[j]]>0);}
  logger.debug("D03_SEQUENCE seed="+seed+" events="+events.size()+" required_dispositions="+required.size()+" skipped=0");
  v.onHide();
 }
 return true;
}
(:test,:typecheck(false)) class D03Loader {var calls=0;function load(){calls+=1;}}
(:test,:typecheck(false)) function display03ReadyAndErrorOnWake(logger){
 var clock=new Display03Clock();clock.now=1794551202;var store=new D03Store();var cat=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);store.write("sf.obj."+cat["catalogDigest"],cat["catalog"]);
 var cache=new NativeCache("https://fixture.invalid/display03-ready",store);var initial=WatchUi.loadResource(Rez.JsonData.DisplayInitial)["raw"];var moved=WatchUi.loadResource(Rez.JsonData.DisplayMoved)["raw"];Test.assert(cache.accept(initial,clock.now));
 var v=new SpaceFoxView(clock,new ScheduleState(null,"empty"));v.setPacket(cache.packet);var d=new D03Recording();d.prepare(v.context,v.settings);v.renderer=d;var loader=new D03Loader();v.pendingLoader=loader.method(:load);
 v.onShow();v.onEnterSleep();Test.assert(cache.accept(moved,clock.now));v.setPacket(cache.packet);var identity=v.context.launchId;
 var writes=store.writes;Test.assert(!cache.accept(initial,clock.now));Test.assertEqual(store.writes,writes);Test.assertEqual(v.context.launchId,identity);Test.assertEqual(v.snapshot().countdown,d03ActiveOracle(1794611100,clock.now));
 var bridge=cache.packet.bridge;store.write("sf.batch.head",{"base"=>cache.base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>1});store.write("sf.batch.pending",{"base"=>cache.base,"pending"=>false});
 v.setAssetCache(new NativeRenderSource(store,cache.base,bridge));Test.assert(v.assetCache.ready);v.prepareVisual();Test.assert(v.sceneLifecycle.pending()&&v.sfrTimer==null&&loader.calls==0);
 v.onExitSleep();var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
 Test.assert(d.activeCount==1&&loader.calls==0&&v.sfrTimer==null);Test.assertEqual(d.activeText,d03ActiveOracle(1794611100,clock.now));Test.assertEqual(v.context.launchId,identity);v.onHide();
 logger.debug("READY_ERROR sleep accepted_target retained rejected_old no_load_until_first_active_frame=true");return true;
}
(:background,:test,:typecheck(false)) class D03CountingApp extends SpaceFoxApp {
 var reloads=0;function initialize(){SpaceFoxApp.initialize();}
 (:typecheck(disableBackgroundCheck)) function reloadFeed(){reloads+=1;}
}
(:test,:typecheck(false)) function display03BackgroundBeforeFrame(logger){
 var app=new D03CountingApp();var clock=new Display03Clock();var v=new SpaceFoxView(clock,new ScheduleState(1794762690,"exact"));var d=new Display03ModeRenderer();v.renderer=d;app.view=v;v.pendingLoader=app.method(:reloadFeed);
 v.onShow();v.onEnterSleep();app.onBackgroundData({"ready"=>true});Test.assert(app.reloads==1);
 v.onExitSleep();app.onBackgroundData({"ready"=>true});Test.assert(app.reloads==1);
 var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assert(d.activeCalls==1&&app.reloads==1);
 app.onBackgroundData({"ready"=>true});Test.assert(app.reloads==1);v.onHide();logger.debug("BACKGROUND sleep_applied=true wake_first_frame no_reload=true");return true;
}

(:test,:typecheck(false)) class D03TransientStore extends D03Store {
 var rejected=null;var remaining=0;var selectionReads=0;
 function read(k){if(rejected!=null&&k.equals(rejected)){selectionReads+=1;if(remaining>0){remaining-=1;throw new Lang.InvalidValueException("transient selected-object read");}}return D03Store.read(k);}
}
// Real accepted bridge carries the same transfer and selection identities
// across batch publication; a failed decode may retry only on a new serial.
(:test,:typecheck(false)) function display03FailedSameDigestRetry(logger){
 var store=new D03TransientStore();var clock=new Display03Clock();var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);
 store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);var base="https://fixture.invalid/display03-retry";
 var cache=new NativeCache(base,store);Test.assert(cache.accept(WatchUi.loadResource(Rez.JsonData.DisplayInitial)["raw"],clock.now));
 var bridge=cache.packet.bridge;Test.assert(bridge["selection"]!=null);
 var objectKey="sf.obj."+bridge["selection"]["sha256"];store.write(objectKey,WatchUi.loadResource(Rez.JsonData.D03RetrySelection)["raw"]);store.rejected=objectKey;store.remaining=1;
 store.write("sf.batch.pending",{"base"=>base,"pending"=>false});
 store.write("sf.batch.head",{"base"=>base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>1});
 var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.setPacket(cache.packet);view.onShow();
 view.setAssetCache(new NativeRenderSource(store,base,bridge));view.prepareVisual();Test.assert(view.sceneLifecycle.pending());
 var old=view.sceneLifecycle.job.token;view.sfrStep();Test.assert(store.selectionReads==1&&view.sceneLifecycle.job.state==view.sceneLifecycle.job.FAILED);
 view.prepareVisual();Test.assert(!view.sceneLifecycle.pending()&&store.selectionReads==1);
 store.write("sf.batch.head",{"base"=>base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>2});
 view.setAssetCache(new NativeRenderSource(store,base,bridge));view.prepareVisual();
 Test.assertMessage(view.sceneLifecycle.pending(),"same digest new serial must retry failed job");
 view.sfrStep();Test.assert(store.selectionReads==2&&view.sfrBuild!=null&&view.sceneLifecycle.job.state==view.sceneLifecycle.job.BUILDING);
 Test.assert(!view.sceneLifecycle.complete(old));view.onHide();Test.assert(!view.sceneLifecycle.complete(old));
 logger.debug("FAILED_RETRY realTransientSelectionRead=true sameSerialNoSpin=true newSerialBuild=true staleCompletionRejected=true");return true;
}

// LL2's published structured status 5 means On Hold. The fixture is otherwise
// the captured accepted packet; elapsed time, unknown and stale are independent.
(:test,:typecheck(false)) function display03SourcedHoldCache(logger){
 var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);var raw=WatchUi.loadResource(Rez.JsonData.DisplayInitial)["raw"];
 var marker="\"source_status_id\":8";var pos=raw.find(marker);Test.assert(pos!=null);
 var held=raw.substring(0,pos)+"\"source_status_id\":5"+raw.substring(pos+marker.length(),raw.length());
 var statusName="\"source_status_name\":\"To Be Confirmed\"";var namePos=held.find(statusName);Test.assert(namePos!=null);
 held=held.substring(0,namePos)+"\"source_status_name\":\"On Hold\""+held.substring(namePos+statusName.length(),held.length());
 var settings=new SceneSettings(null);var values=[raw,held];
 for(var i=0;i<2;i+=1){var store=new D03Store();store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);var base="https://fixture.invalid/hold"+i;var clock=new Display03Clock();clock.now=1794551202;var cache=new NativeCache(base,store);Test.assert(cache.accept(values[i],clock.now));
  var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.setPacket(cache.packet);Test.assert(view.context.sourceHold==(i==1));
  var snapshot=view.snapshot();Test.assert(SceneAod.countdownColor(snapshot,settings)==(i==1?0xFF6B6B:settings.countdownColor));
  snapshot.stale=true;Test.assert(SceneAod.countdownColor(snapshot,settings)==(i==1?0xFF6B6B:settings.countdownColor));
  var reopened=new NativeCache(base,store);Test.assert(reopened.load(clock.now)!=null);view.setPacket(reopened.packet);Test.assert(view.context.sourceHold==(i==1));
  snapshot=view.snapshot();Test.assert(SceneAod.countdownColor(snapshot,settings)==(i==1?0xFF6B6B:settings.countdownColor));
  snapshot.rescheduled=true;Test.assert(SceneAod.countdownColor(snapshot,settings)==0xFF6B6B);
 }
 logger.debug("SOURCED_HOLD status5=true staleIndependent=true cacheReopen=true");return true;
}

(:test,:typecheck(false)) function display03WarmAodResources(logger){
 var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);var store=new D03Store();store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
 var clock=new Display03Clock();clock.now=1794551202;var cache=new NativeCache("https://fixture.invalid/warm",store);
 Test.assert(cache.accept(WatchUi.loadResource(Rez.JsonData.DisplayInitial)["raw"],clock.now));
 var v=new SpaceFoxView(clock,new ScheduleState(null,"empty"));v.setPacket(cache.packet);var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
 v.onLayout(dc);Test.assert(v.renderer.aodMap!=null);var loads=v.renderer.resourceLoads;var first=v.renderer.aodMap;
 v.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);v.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);
 Test.assert(v.renderer.resourceLoads==loads&&v.renderer.aodMap==first);
 v.syncDisplayMode(System.DISPLAY_MODE_HIGH_POWER);v.onEnterSleep();v.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);
 Test.assert(v.renderer.resourceLoads==loads&&v.renderer.aodMap==first);
 v.renderer.prepare(v.context,v.settings);Test.assert(v.renderer.resourceLoads==loads&&v.renderer.aodMap==first);
 v.onHide();logger.debug("WARM_AOD drawLoads=0 wakeReloads=0 duplicatePrepareLoads=0");return true;
}

(:test,:typecheck(false)) function display03SameSceneRefreshKeepsJob(logger){
 var store=new D03Store();var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
 var clock=new Display03Clock();clock.now=1794551202;var base="https://fixture.invalid/refresh";var cache=new NativeCache(base,store);
 Test.assert(cache.accept(WatchUi.loadResource(Rez.JsonData.DisplayInitial)["raw"],clock.now));var bridge=cache.packet.bridge;
 store.write("sf.batch.pending",{"base"=>base,"pending"=>false});store.write("sf.batch.head",{"base"=>base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>1});
 var v=new SpaceFoxView(clock,new ScheduleState(null,"empty"));v.setPacket(cache.packet);var source=new NativeRenderSource(store,base,bridge);v.setAssetCache(source);Test.assert(v.sceneLifecycle.request(1));
 var job=v.sceneLifecycle.job;var generation=v.sceneLifecycle.generation;var reopen=new NativeCache(base,store);Test.assert(reopen.load(clock.now)!=null);
 v.setPacket(reopen.packet);Test.assert(v.sceneLifecycle.job==job&&v.sceneLifecycle.generation==generation&&v.assetCache==source);
 Test.assert(v.context.launchId.equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"));v.onHide();
 logger.debug("SAME_SCENE_REFRESH acceptedReopen=true queuedJobRetained=true assetSourceRetained=true");return true;
}

// Drive the production foreground admission path with a real staged feed and
// immutable visual bridge. A duplicate must not cancel, while a changed target
// must become visible without waiting for optional scene construction.
(:test,:typecheck(false)) function display03ForegroundReloadDuringBuild(logger){
 var previousBase=Application.Properties.getValue("FeedBaseUrl");Application.Properties.setValue("FeedBaseUrl","https://fixture.invalid/display03-foreground");
 try{
 var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);var store=new D03Store();store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
 var base=new NativeTransfer(configuredFeedUrl(),null).base;Test.assert(!base.equals(""));var now=Time.now().value().toLong();
 var cache=new NativeCache(base,store);var initial=WatchUi.loadResource(Rez.JsonData.DisplayInitial)["raw"];var moved=WatchUi.loadResource(Rez.JsonData.DisplayMoved)["raw"];
 Test.assert(cache.accept(initial,now));var bridge=cache.packet.bridge;
 store.write("sf.batch.pending",{"base"=>base,"pending"=>false});store.write("sf.batch.head",{"base"=>base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>1});
 var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",initial,null));var incoming=new NativeIncoming(store,base);store.write("sf.incoming.feed.processed",incoming.token(store.read("sf.incoming.feed")));
 var app=new SpaceFoxApp();var clock=new Display03Clock();var v=new SpaceFoxView(clock,new ScheduleState(null,"empty"));app.feed=cache;app.view=v;v.setPacket(cache.packet);v.setAssetCache(new NativeRenderSource(store,base,bridge));v.onShow();
 Test.assert(v.sceneLifecycle.request(1));var token=v.sceneLifecycle.begin();Test.assert(token!=null);var job=v.sceneLifecycle.job;
 logger.debug("RELOAD_STAGE duplicate");Test.assert(transfer.stage("feed",initial,null));NativeForegroundApp.reload(app);Test.assert(v.sceneLifecycle.job==job);var writes=store.writes;
 NativeForegroundApp.reload(app);Test.assert(v.sceneLifecycle.job==job&&store.writes==writes);
 logger.debug("RELOAD_STAGE moved");Test.assert(transfer.stage("feed",moved,null));var start=System.getTimer();NativeForegroundApp.reload(app);var elapsed=System.getTimer()-start;
 Test.assertMessage(v.context!=null&&v.context.schedule.remainingSeconds(0)==1794611100,"new schedule must activate while optional scene is building");
 Test.assertMessage(elapsed<3000,"foreground schedule activation exceeded 3 seconds");Test.assert(!v.sceneLifecycle.complete(token));
 logger.debug("RELOAD_STAGE reject");var before=System.getSystemStats();Test.assert(transfer.stage("feed","{invalid",null));NativeForegroundApp.reload(app);
 Test.assert(app.restorePending&&v.context.schedule.remainingSeconds(0)==1794611100);logger.debug("RELOAD_STAGE restore");NativeForegroundApp.restore(app);app.restorePending=false;
 Test.assert(v.context.schedule.remainingSeconds(0)==1794611100);var after=System.getSystemStats();
 v.onHide();logger.debug("FOREGROUND_RELOAD duplicateJobRetained=true duplicateWrites=0 movedTargetVisible=true oldCompletionRejected=true rejectedRetainsTarget=true elapsedMs="+elapsed+" appUsedBefore="+before.usedMemory+" appUsedAfter="+after.usedMemory+" appTotal="+after.totalMemory);return true;
 }finally{Application.Properties.setValue("FeedBaseUrl",previousBase);}
}

// Actual decoder boundary: canonical SFR1 payload succeeds with its independent
// pixel digest; noncanonical padding and altered pad bits cannot be admitted.
(:test,:typecheck(false)) function display03StreamWireValidation(logger){
 var raws=["SFR1:0:1:AAECAw==","SFR1:0:1:AAECAx==","SFR1:0:1:AA=CAw=="];
 for(var i=0;i<raws.size();i+=1){var store=new D03Store();var h=new NativeWireHash();h.put(raws[i]);var digest=h.digest();store.write("sf.obj."+digest,raws[i]);
  var descriptor={"canvas"=>[1,1],"channels"=>3,"pixelSha256"=>"039058c6f2c0cb492c533b0a4d14ef77cc0f78abccced5287d84a1a2011cfb81","shards"=>[[digest,h.count]]};
  var accepted=true;try{var decoder=new NativeSfrDecoder(store,descriptor);var steps=0;while(!decoder.step()){steps+=1;Test.assert(steps<10);}Test.assert(decoder.done);}catch(e){accepted=false;}
  Test.assert(accepted==(i==0));
 }
 logger.debug("STREAM_WIRE canonical=true padBitsRejected=true interiorPaddingRejected=true");return true;
}
