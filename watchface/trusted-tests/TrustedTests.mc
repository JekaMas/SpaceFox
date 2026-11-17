import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;
(:test,:typecheck(false)) function trustedSnapshotBench(logger){
 var keys=["id","rocket","operator","operatorShort","purpose","site","modelId","operatorId","siteId","point","target","precision","displayTarget","sourceValidated","stale","rescheduled","reminderEligible"];
 var ids=[Rez.JsonData.Object,Rez.JsonData.Array];
 for(var v=0;v<2;v+=1){
  var before=System.getSystemStats().usedMemory;var start=System.getTimer();var payload=WatchUi.loadResource(ids[v]);var load=System.getTimer()-start;var loaded=System.getSystemStats().usedMemory;
  start=System.getTimer();Application.Storage.setValue("bench.slot",payload);Application.Storage.setValue("bench.active",1);var write=System.getTimer()-start;
  payload=null;start=System.getTimer();var read=Application.Storage.getValue("bench.slot");var row=read["rows"][0];if(v==1){var mapped={};for(var j=0;j<keys.size();j+=1){mapped[keys[j]]=row[j];}row=mapped;}
  var scene=new SceneContext(row);var readFact=System.getTimer()-start;
  Test.assert(scene.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));Test.assert(scene.point!=null&&scene.displayTarget==1795042200l);Test.assertEqual(read["rows"].size(),3);
  logger.debug("CANDIDATE variant="+v+" resourceMs="+load+" writeMs="+write+" readFactMs="+readFact+" usedBefore="+before+" usedLoaded="+loaded+" sampled=true");scene=null;read=null;row=null;Application.Storage.deleteValue("bench.slot");Application.Storage.deleteValue("bench.active");
 }
 return true;
}
(:test,:typecheck(false)) class SnapshotTestStore {
 var values={};var fail=false;var failSlot=false;var slotReads=0;
 function read(k){if(k.find("sf.snapshot.0:")==0||k.find("sf.snapshot.1:")==0){slotReads+=1;if(failSlot){throw new Lang.InvalidValueException("injected read failure");}}return values[k];}
 function write(k,v){if(fail&&k.find("sf.snapshot.active:")==0){throw new Lang.InvalidValueException("injected interrupted pointer");}values[k]=v;}
}
(:test,:typecheck(false)) function trustedSnapshotFlow(logger){
 var store=new SnapshotTestStore();var owner=new NativeTrustedStore(store,"https://jekamas.github.io/SpaceFox");
 var coarse=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];var exact=WatchUi.loadResource(Rez.JsonData.Exact)["payload"];
 Test.assert(owner.save(coarse));var old=new NativeTrustedPacket(owner.load());Test.assertEqual(old.presentation.displayTarget,1795042200l);Test.assert(old.presentation.schedule.remainingSeconds(1794818604l)==null);Test.assertEqual(old.upcomingScenes.size(),2);Test.assert(old.presentation.point!=null);
 store.fail=true;var interrupted=false;try{owner.save(exact);}catch(e){interrupted=true;}store.fail=false;Test.assert(interrupted);
 var retained=new NativeTrustedPacket(owner.load());Test.assertEqual(retained.presentation.launchId,old.presentation.launchId);Test.assert(owner.save(exact));
 var next=new NativeTrustedPacket(owner.load());logger.debug("FLOW exact="+next.presentation.schedule.remainingSeconds(1794677000l)+" eligible="+next.presentation.reminderEligible+" point="+(next.presentation.point!=null));Test.assert(next.presentation.schedule.remainingSeconds(1794677000l)==550);Test.assert(next.presentation.reminderEligible);Test.assert(next.presentation.point!=null);
 logger.debug("trusted snapshot: actual coarse + exact, interrupted pointer preserves old, successor saved");return true;
}

(:test,:typecheck(false)) class TrustedClock extends WatchClock {
 var now=1794818604;
 function utcSeconds(){return now;}
 function localTimeText(){return "13:23";}
}
(:test,:typecheck(false)) function trustedViewModes(logger){
 var snapshot=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];var store=new SnapshotTestStore();var owner=new NativeTrustedStore(store,"https://jekamas.github.io/SpaceFox");Test.assert(owner.save(snapshot));var packet=new NativeTrustedPacket(owner.load());
 var clock=new TrustedClock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();view.setPacket(packet);view.onShow();view.onLayout(dc);
 view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);var a=view.snapshotAt(clock.now);Test.assert(view.context.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60")&&view.context.point!=null&&a.countdown.find("T-")==0);
 clock.now+=1;var b=view.snapshotAt(clock.now);Test.assert(!a.countdown.equals(b.countdown));view.syncDisplayMode(System.DISPLAY_MODE_LOW_POWER);view.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);var low=view.snapshotAt(clock.now);Test.assert(low.lowCountdown.find("T-")==0&&view.context.point!=null);
 var reference=packet.presentation.displayTarget;var only=new SpaceFoxView(clock,new ScheduleState(null,"empty"));only.setContext(packet.presentation);Test.assert(only.snapshotAt(reference-1).countdown.find("T-")==0);Test.assert(only.snapshotAt(reference+30).countdown.find("T+")==0);Test.assert(!packet.presentation.reminderEligible&&packet.presentation.sourcePrecision.equals("window"));
 view.syncDisplayMode(System.DISPLAY_MODE_HIGH_POWER);view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assert(view.context.point!=null);view.setSettings(new SceneSettings({"Language"=>"ru"}));view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assert(view.context.point!=null&&view.snapshotAt(clock.now).countdown.find("T-")==0);view.syncDisplayMode(System.DISPLAY_MODE_LOW_POWER);view.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);Test.assert(view.context.point!=null);view.onHide();logger.debug("trusted view EN/RU ACTIVE seconds, LOW point/minutes, wake retained");return true;
}
(:test,:typecheck(false)) function trustedAssetLifecycle(logger){
 Application.Storage.clearValues();var url="https://jekamas.github.io/SpaceFox";var store=new NativeStore();var payload=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];var owner=new NativeTrustedStore(store,url);Test.assert(owner.save(payload));var packet=new NativeTrustedPacket(owner.load());var batch=new NativeBatch(store,url);batch.select(packet.bridge);var request=batch.next();var count=0;
 while(request!=null){var raw=b1Response(request["path"]);Test.assert(raw!=null);Test.assert(batch.immutable.put(request,raw));raw=null;count+=1;Test.assert(count<=27);request=batch.next();}
 Test.assertEqual(count,27);var ready=new NativeRenderSource(store,url,packet.bridge);Test.assert(ready.ready);var build=new NativeSfrBuild(store,url,packet);var steps=0;while(!build.step()&&steps<5000){steps+=1;}Test.assert(build.complete&&build.result!=null);logger.debug("trusted assets downloaded="+count+" decodeSteps="+steps);build.dispose();return true;
}

(:test,:typecheck(false)) function trustedReminderAndBackgroundCadence(logger){
 var base="https://jekamas.github.io/SpaceFox";var store=new SnapshotTestStore();var owner=new NativeTrustedStore(store,base);
 var coarse=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];var exact=WatchUi.loadResource(Rez.JsonData.Exact)["payload"];
 var emptyTransfer=new NativeTransfer(base,store);var now=1794631793l;Test.assert(emptyTransfer.due(now,true));Test.assert(owner.save(exact));emptyTransfer.attempted(now);emptyTransfer.completed(true);
 Test.assert(!emptyTransfer.due(now+3599,true));Test.assert(emptyTransfer.due(now+3600,true));
 var plan=store.read("sf.transfer.plan:"+base);var future=plan["targets"];plan["targets"]=[];Test.assert(emptyTransfer.due(now+1,true));Test.assert(!emptyTransfer.due(now+1,false));Test.assert(emptyTransfer.due(now+300,false));plan["targets"]=future;
 var another="https://another.example";var otherOwner=new NativeTrustedStore(store,another);Test.assert(otherOwner.save(exact));var otherTransfer=new NativeTransfer(another,store);otherTransfer.attempted(now+1);otherTransfer.completed(true);
 var reopened=new NativeTransfer(base,store);reopened.load();Test.assert(!reopened.due(now+3599,true));Test.assert(reopened.due(now+3600,true));
 emptyTransfer.attempted(now+3600);Test.assert(emptyTransfer.due(now+3600,true));Test.assert(!emptyTransfer.due(now+3600,false));Test.assert(emptyTransfer.due(now+3900,false));Test.assert(emptyTransfer.due(now+3601,true));
 logger.debug("TRUST_CADENCE healthy_hour=true failure_connected=true offline300=true reopen=true");
 var p=new NativeTrustedPacket(owner.load());var s=p.presentation;var pol=s.freshnessPolicy;var since=s.sourceValidated+60;
 var q={"base"=>base,"sequence"=>owner.marker()["sequence"],"rows"=>[[s.launchId,s.retentionTarget,s.sourcePrecision,s.rocket,s.sourceValidated,s.stale,since,[pol["normal_interval_seconds"],pol["near_interval_seconds"],pol["fast_interval_seconds"],pol["stale_cycles"]],s.retentionDeadline,s.reminderEligible]]};
 var row=LaunchReminder.selected(q,since);Test.assert(row!=null&&LaunchReminder.bound(store,row,base,since));
 Test.assert(owner.save(coarse));Test.assert(!LaunchReminder.bound(store,row,base,since));var c=new NativeTrustedPacket(owner.load());Test.assert(!c.presentation.reminderEligible);
 var isolated=new NativeTrustedStore(store,"https://empty.example");Test.assert(isolated.load()==null);logger.debug("trusted reminder exact eligible, new pointer invalidates old, coarse excluded, cadence and namespace retained");return true;
}

(:test,:typecheck(false)) function trustedFailureStopsRetry(logger){
 var base="https://jekamas.github.io/SpaceFox";var store=new SnapshotTestStore();var owner=new NativeTrustedStore(store,base);var data=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];Test.assert(owner.save(data));var packet=new NativeTrustedPacket(owner.load());
 var app=new SpaceFoxApp();app.view=new SpaceFoxView(new TrustedClock(),new ScheduleState(null,"empty"));app.feed=new NativeCache(base,store);app.feed.packet=packet;app.trustedToken=owner.marker()["sequence"];app.view.setPacket(packet);app.view.onShow();
 Test.assert(owner.save(data));store.failSlot=true;NativeForegroundApp.reload(app);var reads=store.slotReads;Test.assert(app.failedToken==owner.marker()["sequence"]);Test.assert(app.view.context!=null&&app.view.context.launchId.equals(packet.presentation.launchId));
 NativeForegroundApp.reload(app);Test.assertEqual(store.slotReads,reads);store.failSlot=false;app.failedToken=null;NativeForegroundApp.reload(app);Test.assert(app.feed.packet!=null&&app.view.context!=null&&app.view.context.launchId.equals(packet.presentation.launchId));app.view.onHide();logger.debug("trusted failure preserves facts, avoids hot retry and resumes on later delivery");return true;
}

(:test,:typecheck(false)) function trustedActualStorageReopen(logger){
 Application.Storage.clearValues();var base="https://jekamas.github.io/SpaceFox";var owner=new NativeTrustedStore(null,base);var data=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];Test.assert(owner.save(data));data=null;
 var app=new SpaceFoxApp();var views=app.getInitialView();var view=views[0];view.onShow();var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();view.onLayout(dc);app.performReload();Test.assert(view.context!=null&&view.context.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60")&&view.context.point!=null);app.onStop({});
 var reopened=new SpaceFoxApp();var again=reopened.getInitialView()[0];again.onShow();again.onLayout(dc);reopened.performReload();Test.assert(again.context!=null&&again.context.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60")&&again.context.point!=null);reopened.onStop({});logger.debug("trusted actual Application.Storage snapshot restores on app reopen");return true;
}

// Use the production event/callback/optional owners. Only HTTP and OS exit are
// substituted; a due 300-second schedule must not starve the captured asset job.
(:test,:typecheck(false)) class TrustedAssetEvent extends FeedService {
 var memory;var payload;var code=200;var requested=null;var snapshots=0;var exits=0;
 function initialize(adapter,value){FeedService.initialize();memory=adapter;payload=value;}
 function createTransfer() as NativeTransfer {return new NativeTransfer("https://jekamas.github.io/SpaceFox",memory);}
 function phoneConnected() as Boolean {return true;}
 function requestSnapshot(){snapshots+=1;receiveSnapshot(code,{"data"=>payload});}
 function request(path as String,callback as Method) as Void {requested=path;inFlight=true;}
 function rearm() as Void {}
 function leave() as Void {exits+=1;}
}
(:test,:typecheck(false)) function trustedDueSnapshotAssets(logger){
 var base="https://jekamas.github.io/SpaceFox";var store=new SnapshotTestStore();var data=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];
 var duplicate=new FeedService();duplicate.startDeadline();duplicate.inFlight=true;duplicate.requestSnapshot();Test.assertEqual(duplicate.requests,0);
 var first=new TrustedAssetEvent(store,data);first.onTemporalEvent();
 Test.assertMessage(first.snapshots==1&&first.requested!=null,"due snapshot also starts optional assets");
 var packet=new NativeTrustedPacket(new NativeTrustedStore(store,base).load());Test.assert(packet.presentation.point!=null&&packet.presentation.displayTarget==1795042200l);
 Test.assert(first.requested.find("wire3/catalogs/")==0);first.receiveBatch(200,b1Response(first.requested));Test.assert(first.exits==1);
 // Next due event has a failed schedule response. The already accepted facts
 // survive, and the existing optional transfer still requests its next object.
 store.write("sf.attempt:"+base,{"base"=>base,"utc"=>Toybox.Time.now().value().toLong()-301l,"success"=>false});
 var second=new TrustedAssetEvent(store,data);second.code=503;second.onTemporalEvent();
 Test.assertMessage(second.snapshots==1&&second.requested!=null&&second.requested.find("wire3/catalogs/")==null,"failed due snapshot does not block pending assets");
 second.receiveBatch(500,null);Test.assert(second.exits==1);
 var retained=new NativeTrustedPacket(new NativeTrustedStore(store,base).load());Test.assert(retained.presentation.launchId.equals(packet.presentation.launchId)&&retained.presentation.point!=null);
 logger.debug("TRUST_DUE_ASSETS retry=true snapshotPublishedBeforeArt=true failedSnapshotContinuesAssets=true failedArtKeepsFacts=true");return true;
}
