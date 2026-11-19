import Toybox.Lang;
import Toybox.Test;
import Toybox.System;
import Toybox.WatchUi;
(:test,:typecheck(false)) class CountdownClock extends WatchClock {
 var now=1795043099l;
 function utcSeconds(){return now;}
 function localTimeText(){return "15:31";}
 function localCalendar(){return [2026,11,19];}
}
(:test,:typecheck(false)) class CountdownMemory {
 var rows={};var pointers=0;var slotReads=0;var failPointer=false;
 function read(key){if(key.find("sf.snapshot.0:")==0||key.find("sf.snapshot.1:")==0){slotReads+=1;}return rows[key];}
 function write(key,value){if(key.find("sf.snapshot.active:")==0){if(failPointer){throw new Lang.InvalidValueException("injected pointer failure");}pointers+=1;}rows[key]=value;}
}
(:test,:typecheck(false)) function capturedCoarseRollover(logger){
 var source=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];
 var store=new CountdownMemory();var trusted=new NativeTrustedStore(store,"https://example.invalid");Test.assert(trusted.save(source));
 var packet=new NativeTrustedPacket(trusted.load());var clock=new CountdownClock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));
 view.setPacket(packet);var first=view.snapshotAt(1795043099l);
 Test.assertEqual(view.context.launchId,"ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60");Test.assertEqual(first.countdown,"T+ 00:14:59");
 var crossed=view.snapshotAt(1795043100l);Test.assertEqual(view.context.launchId,"ll2:launch:76617033-4dc0-4448-b50c-e5b0d5a18539");
 Test.assert(crossed.countdown.find("T-")==0);
 var reopen=new NativeTrustedPacket(new NativeTrustedStore(store,"https://example.invalid").load());clock.now=1795087860l;
 var later=new SpaceFoxView(clock,new ScheduleState(null,"empty"));later.setPacket(reopen);Test.assertEqual(later.context.launchId,"ll2:launch:76617033-4dc0-4448-b50c-e5b0d5a18539");
 source[4]=[];var empty=new NativeTrustedPacket(source);var lone=new SpaceFoxView(clock,new ScheduleState(null,"empty"));lone.setPacket(empty);var shown=lone.snapshotAt(clock.now);Test.assert(lone.context==null);Test.assertEqual(shown.countdown,"--:--:--");Test.assertEqual(shown.lowCountdown,"--:--");
 logger.debug("captured coarse retention exact boundary + offline reopen + exhausted queue");return true;
}

// Network callbacks go through the production service owner; OS and network
// ports are fake, payloads are copies of the captured current schema.
(:test,:typecheck(false)) class CountdownService extends FeedService {
 var memory;var now=1795087860l;var ms=0;var callbacks=[];var exits=0;
 function initialize(store){FeedService.initialize();memory=store;}
 function createTransfer() as NativeTransfer{return new NativeTransfer("https://example.invalid",memory);}
 function nowUtc() as Long{return now;}
 function nowMillis() as Number{return ms;}
 function phoneConnected() as Boolean{return true;}
 function traceEntry() as Void {}
 function registerEntryWake() as Void {}
 function wakeReminders(t as NativeTransfer,at as Long) as Void {}
 function armTransfer(t as NativeTransfer,at as Long) as Void {}
 function createBatch(t as NativeTransfer) as NativeBatch or Null{return null;}
 function sendSnapshot(callback as Method) as Void{callbacks.add(callback);}
 function deliverBackground(data) as Void{exits+=1;}
 function log(message as String) as Void{}
}
(:typecheck(false)) function countdownSnapshot(source,generation,instance,epoch){
 var out=source.slice(0,source.size());out[1]={"generation"=>generation,"instance"=>instance,"selectionValidatedUtc"=>epoch};return out;
}
(:test,:typecheck(false)) function staleResponsePreservesDurableSnapshot(logger){
 var source=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var store=new CountdownMemory();var s=new CountdownService(store);
 var instance="40655f8a46c4c47ecb6f6d4a8608bde8396c6c440807e09d962b1f7fde006204";var epoch=1795080000l;
 s.onTemporalEvent();Test.assertEqual(s.callbacks.size(),1);s.callbacks[0].invoke(200,{"data"=>countdownSnapshot(source,101,instance,epoch)});
 var owner=new NativeTrustedStore(store,"https://example.invalid");var first=owner.load();logger.debug("first durable="+(first==null?"null":first[1]["generation"]));Test.assert(first!=null&&first[1]["generation"]==101);
 s.now+=3600;s.ms+=3600000;s.onTemporalEvent();Test.assertEqual(s.callbacks.size(),2);s.callbacks[1].invoke(200,{"data"=>countdownSnapshot(source,99,instance,epoch)});
 var reopened=new NativeTrustedStore(store,"https://example.invalid");var final=reopened.load();logger.debug("reopened durable="+(final==null?"null":final[1]["generation"]));Test.assert(final!=null&&final[1]["generation"]==101&&store.pointers==1);
 Test.assert(store.read("sf.attempt:https://example.invalid")["success"]==false);
 var clock=new CountdownClock();clock.now=s.now;var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.setPacket(new NativeTrustedPacket(final));
 var active=view.snapshotAt(clock.now);Test.assert(view.context.launchId.equals("ll2:launch:76617033-4dc0-4448-b50c-e5b0d5a18539"));Test.assert(active.countdown.find("T-")==0&&active.lowCountdown.find("T-")==0);
 // A tied epoch from a different publisher instance is not ordered.
 s.now+=1;s.ms+=1000;s.onTemporalEvent();Test.assertEqual(s.callbacks.size(),3);s.callbacks[2].invoke(200,{"data"=>countdownSnapshot(source,101,"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",epoch)});
 Test.assert(new NativeTrustedStore(store,"https://example.invalid").load()[1]["generation"]==101&&store.pointers==1);
 // Failed/stale requests do not hold the hourly success gate; the next valid
 // response can commit and the source epoch is not advanced by the rejection.
 s.now+=1;s.ms+=1000;s.onTemporalEvent();Test.assertEqual(s.callbacks.size(),4);s.callbacks[3].invoke(200,{"data"=>countdownSnapshot(source,102,instance,epoch)});
 var newest=new NativeTrustedStore(store,"https://example.invalid").load();Test.assert(newest[1]["generation"]==102&&newest[1]["selectionValidatedUtc"]==epoch&&store.pointers==2);
 // Interrupted pointer commit retains the last complete durable snapshot.
 s.now+=3600;s.ms+=3600000;store.failPointer=true;s.onTemporalEvent();Test.assertEqual(s.callbacks.size(),5);s.callbacks[4].invoke(200,{"data"=>countdownSnapshot(source,103,instance,epoch)});store.failPointer=false;
 Test.assert(new NativeTrustedStore(store,"https://example.invalid").load()[1]["generation"]==102&&store.pointers==2);
 // A newer source epoch may represent a publisher instance change.
 s.now+=1;s.ms+=1000;s.onTemporalEvent();Test.assertEqual(s.callbacks.size(),6);s.callbacks[5].invoke(200,{"data"=>countdownSnapshot(source,1,"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",epoch+1)});
 var changed=new NativeTrustedStore(store,"https://example.invalid").load();Test.assert(changed[1]["generation"]==1&&changed[1]["selectionValidatedUtc"]==epoch+1&&store.pointers==3);
 s.callbacks[0].invoke(200,{"data"=>countdownSnapshot(source,999,instance,epoch)});
 Test.assert(new NativeTrustedStore(store,"https://example.invalid").load()[1]["generation"]==1&&store.pointers==3);
 logger.debug("service 101->99 stale->tied-other->102, pointer failure, newer instance, late callback and reopen");return true;
}

(:test,:typecheck(false)) class CountdownEventView extends SpaceFoxView {
 var fakeMode=System.DISPLAY_MODE_HIGH_POWER;var frames=0;
 function initialize(clock){SpaceFoxView.initialize(clock,new ScheduleState(null,"empty"));}
 function deviceMode() as System.DisplayMode{return fakeMode;}
 function requestFrame() as Void {frames+=1;}
 function refreshLocale() as Void {}
}
(:typecheck(false)) function expectedActive(target,now){
 var d=target-now;var sign=d>0?"T- ":"T+ ";if(d<0){d= -d;}
 return sign+(d/3600).toNumber().format("%02d")+":"+((d%3600)/60).toNumber().format("%02d")+":"+(d%60).toNumber().format("%02d");
}
(:typecheck(false)) function expectedLow(target,now){
 var d=target-now;var sign=d>0?"T- ":"T+ ";var n=d>0?(d+59)/60:(-d)/60;
 return sign+(n/60).toNumber().format("%02d")+":"+(n%60).toNumber().format("%02d");
}
(:test,:typecheck(false)) function generatedCountdownLifecycle(logger){
 var source=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var events=0;var checks=0;var counts=[0,0,0,0,0,0];
 for(var seed=1;seed<=16;seed+=1){
  var store=new CountdownMemory();var saved=new NativeTrustedStore(store,"https://example.invalid");Test.assert(saved.save(source));
  var clock=new CountdownClock();clock.now=1795042080l;var view=new CountdownEventView(clock);view.setPacket(new NativeTrustedPacket(saved.load()));
  var rng=seed;var list=[2,0,0,3,4,1,2,5,0];
  for(var i=0;i<24;i+=1){
   rng=(rng*73+19)%997;var e=i<list.size()?list[i]:rng%6;counts[e]+=1;
   if(e==0){clock.now+=i==1?119:(i==2?1:[0,60,300,900][rng%4]);}
   else if(e==1){view.onHide();}
   else if(e==2){view.onShow();}
   else if(e==3){view.fakeMode=System.DISPLAY_MODE_LOW_POWER;view.onEnterSleep();}
   else if(e==4){view.fakeMode=System.DISPLAY_MODE_HIGH_POWER;view.onExitSleep();}
   else{view.onHide();view=new CountdownEventView(clock);view.setPacket(new NativeTrustedPacket(new NativeTrustedStore(store,"https://example.invalid").load()));view.onShow();}
   var x=view.snapshotAt(clock.now);var target=clock.now<1795043100l?1795042200l:1795142760l;
   var identity=clock.now<1795043100l?"ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60":"ll2:launch:76617033-4dc0-4448-b50c-e5b0d5a18539";
   Test.assert(view.context!=null&&view.context.launchId.equals(identity));Test.assertEqual(x.countdown,expectedActive(target,clock.now));Test.assertEqual(x.lowCountdown,expectedLow(target,clock.now));events+=1;checks+=3;
  }
  view.onHide();
 }
 for(var c=0;c<counts.size();c+=1){Test.assert(counts[c]>0);}
 logger.debug("COUNTDOWN_GENERATED seeds=16 events="+events+" per_event_assertions="+checks+" event_counts_advance_hide_show_sleep_wake_reopen="+counts+" logical_time=true");return true;
}

(:test,:typecheck(false)) function terminalSuppressesCachedFuture(logger){
 var source=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var clock=new CountdownClock();clock.now=1795045800l;
 var old=new SceneContext({"id"=>"ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60","target"=>1795049000l,"precision"=>"exact","retentionDeadline"=>1795049900l,"orderingUtc"=>1795049000l,"sourceValidated"=>1794970678l});
 var signal={"launch_id"=>old.launchId,"source_validated_utc"=>1795045800l};
 var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.setPacket(new NativeTrustedPacket(source));view.mergeSaved([old],clock.now,[signal]);
 Test.assertEqual(view.context.launchId,"ll2:launch:76617033-4dc0-4448-b50c-e5b0d5a18539");
 var control=new SpaceFoxView(clock,new ScheduleState(null,"empty"));control.setPacket(new NativeTrustedPacket(source));control.mergeSaved([old],clock.now,[]);Test.assertEqual(control.context.launchId,old.launchId);
 logger.debug("newer terminal suppresses cached future; omission negative control reselects it");return true;
}

(:test,:typecheck(false)) function emptyEpochThenFirstSource(logger){
 var source=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var store=new CountdownMemory();var s=new CountdownService(store);
 var instance="40655f8a46c4c47ecb6f6d4a8608bde8396c6c440807e09d962b1f7fde006204";
 var empty=countdownSnapshot(source,1,instance,null);empty[3]=null;empty[4]=[];empty[5]=[];empty[6]=null;
 s.onTemporalEvent();s.callbacks[0].invoke(200,{"data"=>empty});Test.assert(new NativeTrustedStore(store,"https://example.invalid").load()[1]["selectionValidatedUtc"]==null);
 s.now+=1;s.ms+=1000;s.onTemporalEvent();Test.assertEqual(s.callbacks.size(),2);s.callbacks[1].invoke(200,{"data"=>countdownSnapshot(source,2,instance,1795080000l)});
 var loaded=new NativeTrustedStore(store,"https://example.invalid").load();Test.assert(loaded[1]["generation"]==2&&loaded[1]["selectionValidatedUtc"]==1795080000l&&store.pointers==2);
 logger.debug("null epoch bootstrap accepts first real source; no invented epoch");return true;
}
(:test,:typecheck(false)) function immutableReplayAndConflict(logger){
 var source=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var store=new CountdownMemory();var s=new CountdownService(store);
 var instance="40655f8a46c4c47ecb6f6d4a8608bde8396c6c440807e09d962b1f7fde006204";var epoch=1795080000l;
 s.onTemporalEvent();s.callbacks[0].invoke(200,{"data"=>countdownSnapshot(source,101,instance,epoch)});
 s.now+=3600;s.ms+=3600000;s.onTemporalEvent();s.callbacks[1].invoke(200,{"data"=>countdownSnapshot(source,101,instance,epoch)});
 Test.assert(store.pointers==1&&store.read("sf.attempt:https://example.invalid")["success"]==true);
 var preserved=new NativeTrustedStore(store,"https://example.invalid").load();Test.assert(preserved[1]["selectionValidatedUtc"]==epoch);
 s.now+=3599;s.ms+=3599000;s.onTemporalEvent();Test.assertEqual(s.callbacks.size(),2);
 s.now+=1;s.ms+=1000;s.onTemporalEvent();Test.assertEqual(s.callbacks.size(),3);
 var conflict=countdownSnapshot(source,101,instance,epoch);conflict[3]=source[3].slice(0,source[3].size());conflict[3][1]="Different rocket";
 s.callbacks[2].invoke(200,{"data"=>conflict});Test.assert(store.pointers==1&&store.read("sf.attempt:https://example.invalid")["success"]==false);
 s.now+=1;s.ms+=1000;s.onTemporalEvent();Test.assertEqual(s.callbacks.size(),4);s.callbacks[3].invoke(200,{"data"=>countdownSnapshot(source,102,instance,epoch)});
 Test.assert(store.pointers==2&&new NativeTrustedStore(store,"https://example.invalid").load()[1]["generation"]==102);
 logger.debug("identical replay succeeds without writes or age change; same revision conflict fails and retries");return true;
}
(:typecheck(false)) function terminalReplaySnapshot(source,subsecond){
 var out=countdownSnapshot(source,101,"40655f8a46c4c47ecb6f6d4a8608bde8396c6c440807e09d962b1f7fde006204",1795080000l);
 out[5]=[{"terminal"=>{"launch_id"=>"ll2:launch:test","status"=>"cancelled","source_validated_utc"=>1795080000.0d,"source_updated_utc"=>1795079999.0d,"source_updated_subsecond"=>subsecond}}];return out;
}
(:test,:typecheck(false)) function terminalReplayJsonNumbers(logger){
 var source=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var store=new CountdownMemory();var s=new CountdownService(store);
 s.onTemporalEvent();s.callbacks[0].invoke(200,{"data"=>terminalReplaySnapshot(source,123457.0d)});
 s.now+=3600;s.ms+=3600000;s.onTemporalEvent();s.callbacks[1].invoke(200,{"data"=>terminalReplaySnapshot(source,123457.0d)});
 Test.assert(store.pointers==1&&store.read("sf.attempt:https://example.invalid")["success"]==true);
 s.now+=3600;s.ms+=3600000;s.onTemporalEvent();s.callbacks[2].invoke(200,{"data"=>terminalReplaySnapshot(source,123458.0d)});
 Test.assert(store.pointers==1&&store.read("sf.attempt:https://example.invalid")["success"]==false);
 logger.debug("identical terminal JSON numbers replay succeeds; conflicting subsecond refused");return true;
}
(:test,:typecheck(false)) function legacyMarkerAndBoundedReads(logger){
 var source=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var store=new CountdownMemory();
 var base="https://example.invalid";var instance="40655f8a46c4c47ecb6f6d4a8608bde8396c6c440807e09d962b1f7fde006204";var epoch=1795080000l;
 var owner=new NativeTrustedStore(store,base);var prior=countdownSnapshot(source,101,instance,epoch);owner.normalize(prior);
 // Model a complete v0.2.12 persisted slot and its old marker, not a private
 // cache-field mutation. No publisher stamp existed on the old pointer.
 store.write("sf.snapshot.0:"+base,prior);store.write("sf.snapshot.active:"+base,{"base"=>base,"slot"=>0,"sequence"=>1});
 var s=new CountdownService(store);s.onTemporalEvent();s.callbacks[0].invoke(200,{"data"=>countdownSnapshot(source,101,instance,epoch)});
 Test.assert(store.slotReads==1&&store.pointers==1&&store.read("sf.snapshot.active:"+base)["publisher"]==null);
 s.now+=1;s.ms+=1000;s.onTemporalEvent();s.callbacks[1].invoke(200,{"data"=>countdownSnapshot(source,102,instance,epoch)});
 Test.assert(store.slotReads==2&&store.read("sf.snapshot.active:"+base)["publisher"]["generation"]==102);
 s.now+=3600;s.ms+=3600000;s.onTemporalEvent();s.callbacks[2].invoke(200,{"data"=>countdownSnapshot(source,103,instance,epoch)});
 Test.assertMessage(store.slotReads==2,"newer stamped response must not load the complete previous slot");
 s.now+=3600;s.ms+=3600000;s.onTemporalEvent();s.callbacks[3].invoke(200,{"data"=>countdownSnapshot(source,103,instance,epoch)});
 Test.assertMessage(store.slotReads==3,"equal replay must compare the complete prior snapshot");
 logger.debug("legacy replay and newer transition read old slot; stamped newer no slot read; replay reads once");return true;
}
(:test,:typecheck(false)) class CountdownFrameView extends CountdownEventView {
 var testClock;var activeText="";var lowText="";
 function initialize(clock){testClock=clock;CountdownEventView.initialize(clock);}
 function newViewTimer() as Toybox.Timer.Timer{return new PbtTimer();}
 function onLayout(dc as Toybox.Graphics.Dc) as Void {}
 function drawClockFallback(dc){activeText=snapshotAt(testClock.now).countdown;}
 function drawPendingLow(dc){lowText=snapshotAt(testClock.now).lowCountdown;markLowFramePainted((testClock.now/60).toLong());}
}
(:test,:typecheck(false)) function capturedFrameIntent(logger){
 var source=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var clock=new CountdownClock();clock.now=1795043099l;
 var v=new CountdownFrameView(clock);v.setPacket(new NativeTrustedPacket(source));v.onShow();v.onUpdate(new PbtGraphics());
 Test.assertEqual(v.activeText,"T+ 00:14:59");v.fakeMode=System.DISPLAY_MODE_LOW_POWER;v.onEnterSleep();clock.now=1795043100l;v.onUpdate(new PbtGraphics());
 Test.assert(v.context.launchId.equals("ll2:launch:76617033-4dc0-4448-b50c-e5b0d5a18539"));Test.assert(v.lowText.find("T-")==0);
 v.fakeMode=System.DISPLAY_MODE_HIGH_POWER;v.onExitSleep();v.onUpdate(new PbtGraphics());Test.assert(v.activeText.find("T-")==0);v.onHide();
 logger.debug("actual view ACTIVE/LOW callback and frame intent; fake drawing port, not pixel evidence");return true;
}
(:test,:typecheck(false)) function countdownAffectedBatch(logger){
 Test.assert(capturedCoarseRollover(logger));Test.assert(staleResponsePreservesDurableSnapshot(logger));
 Test.assert(emptyEpochThenFirstSource(logger));Test.assert(immutableReplayAndConflict(logger));Test.assert(legacyMarkerAndBoundedReads(logger));
 Test.assert(generatedCountdownLifecycle(logger));Test.assert(terminalSuppressesCachedFuture(logger));Test.assert(capturedFrameIntent(logger));
 Test.assert(generatedStorageOwners(logger));Test.assert(generatedServiceFailure(logger));
 Test.assert(generatedWakeOwner(logger));Test.assert(generatedForegroundDelivery(logger));Test.assert(generatedCacheMapOwners(logger));
 logger.debug("COUNTDOWN_AFFECTED six_directed_or_generated plus_storage_service_wake_foreground_cache=true");return true;
}
