import Toybox.Application;
import Toybox.Lang;
import Toybox.Test;
import Toybox.Time;
import Toybox.WatchUi;

(:test,:typecheck(false)) class B3Sink {
 var entries=[];
 function post(slot,s){entries.add([slot,s["id"],s["target"]]);}
}
(:test,:typecheck(false)) class B3Store extends B1MemoryStore {
 var writes=0;function initialize(){B1MemoryStore.initialize();}function write(k,v){writes+=1;B1MemoryStore.write(k,v);}
}
(:test,:typecheck(false)) class B3Packet {
 var contentHash="content";var wireHash="wire";
 var document={"publisher"=>{"instance"=>"fixture","generation"=>1}};
}
(:test,:typecheck(false)) function b3Scene(id,target,valid,eligible){
 return new SceneContext({"id"=>id,"rocket"=>"Starship V3","purpose"=>"Flight Test","precision"=>"minute","target"=>target,"retentionDeadline"=>target+900l,"sourceValidated"=>valid,"freshnessPolicy"=>{"normal_interval_seconds"=>7200,"near_interval_seconds"=>3600,"fast_interval_seconds"=>null,"stale_cycles"=>4},"reminderEligible"=>eligible});
}
(:test,:typecheck(false)) function b3QueueAndRollover(logger){
 var now=999000l;var c=new NativeCache("https://fixture.invalid",new B3Store());c.packet=new B3Packet();c.commit={"seal"=>"one"};c.store.write("sf.commit",{"base"=>c.base,"seal"=>"one"});
 var a=b3Scene("ll2:launch:a",1000000l,998900l,true);var b=b3Scene("ll2:launch:b",1001500l,998950l,true);
 LaunchReminderForeground.publishQueue(c,now,[a,b]);var q=c.store.read("sf.reminder.snapshot");Test.assertEqual(q["rows"].size(),2);Test.assertEqual(LaunchReminder.selected(q,now)["id"],a.launchId);Test.assertEqual(LaunchReminder.selected(q,1000900l)["id"],b.launchId);Test.assertEqual(LaunchReminder.selected(q,1000900l)["validated"],998950l);
 var sink=new B3Sink();Application.Properties.setValue("LaunchReminders",1);c.store.write("sf.reminder.control",{"enabled"=>true,"since"=>now});
 Test.assertEqual(LaunchReminder.nextWake(c,now,null),999100l);LaunchReminder.wakeWith(c,999100l,false,sink.method(:post));LaunchReminder.wakeWith(c,999101l,false,sink.method(:post));Test.assertEqual(sink.entries.size(),1);Test.assertEqual(sink.entries[0][0],0);Test.assertEqual(sink.entries[0][1],a.launchId);
 // Successor's T-15 preceded selection, so no late replay; T-10 is allowed.
 Test.assertEqual(LaunchReminder.nextWake(c,1000900l,null),1000900l);LaunchReminder.wakeWith(c,1000900l,false,sink.method(:post));Test.assertEqual(sink.entries.size(),2);Test.assertEqual(sink.entries[1][0],1);Test.assertEqual(sink.entries[1][1],b.launchId);
 var before=c.store.writes;LaunchReminderForeground.publishQueue(c,now+1,[a,b]);Test.assertEqual(c.store.writes,before);
 Application.Properties.setValue("LaunchReminders",0);logger.debug("B3_QUEUE retainedA successorB deadline sourceAge noDuplicate noCatchup");return true;
}
(:test,:typecheck(false)) function b3AdmissionAndUnknown(logger){
 var store=new B1MemoryStore();var base="https://fixture.invalid/profile-a";var now=1794551202l;var raw=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));var ref=batch.next();Test.assert(batch.immutable.put(ref,b1ProfileResponse(ref["path"])));var c=new NativeCache(base,store);Test.assert(b1Promote021(c,raw,now));var admitted=feedScene(c.packet,now);Test.assert(admitted.reminderEligible);Test.assertEqual(admitted.sourcePrecision,"minute");Test.assertEqual(admitted.sourceValidated,1794551192l);
 var v=new SpaceFoxView(new B1DecodeClock(),new ScheduleState(null,"empty"));v.setPacket(c.packet);LaunchReminderForeground.publishQueue(c,now,v.queueSnapshots());var selected=LaunchReminder.selected(store.read("sf.reminder.snapshot"),now);Test.assertEqual(selected["id"],admitted.launchId);Test.assertEqual(selected["validated"],1794551192l);Test.assert(LaunchReminder.bound(store,selected,c.base,now));
 var blocked=b3Scene("ll2:launch:a",1000000l,998900l,false);var next=b3Scene("ll2:launch:b",1001500l,998950l,true);var q={"rows"=>[[blocked.launchId,blocked.retentionTarget,"source-coarse","Starship",blocked.sourceValidated,false,999000l,[7200,3600,null,4],blocked.retentionDeadline,false],[next.launchId,next.retentionTarget,"source-coarse","Starship",next.sourceValidated,false,999000l,[7200,3600,null,4],next.retentionDeadline,true]]};Test.assert(LaunchReminder.selected(q,999100l)==null);Test.assertEqual(LaunchReminder.selected(q,1000900l)["id"],next.launchId);
 // The new per-scene eligibility gate must reject actual source shapes,
 // independently of the queue's controlled false flag above.
 var parsed=new NativePreparedBridgeFeed(raw,now,store);while(!parsed.prepareStep()){}var row=parsed.document["launch"];var timing=row["timing"];var priorStatus=row["status"];row["status"]="unknown";Test.assert(!feedSceneRow(parsed,row,null,false).reminderEligible);row["status"]=priorStatus;var oldStart=timing["window_start_utc"];timing["window_start_utc"]=timing["nominal_utc"]+1;Test.assert(!feedSceneRow(parsed,row,null,false).reminderEligible);timing["window_start_utc"]=oldStart;timing["source_precision_id"]=2;Test.assert(!feedSceneRow(parsed,row,null,false).reminderEligible);
 Test.assert(!LaunchReminder.valid(selected,base,now+20000l));
 logger.debug("B3_ADMISSION realMIN sourceAge unknownBlocks sourceBound");return true;
}
(:test,:typecheck(false)) function b3QuietProvider(logger){var now=Time.now().value().toLong();var result=LaunchReminder.isQuiet(now);Test.assert(result instanceof Boolean);logger.debug("B3_QUIET_PROVIDER sdkResult="+result+" actualAPI noDeliveryClaim");return true;}
(:test,:typecheck(false)) function b3StorageSeed(logger){
 Application.Storage.clearValues();var c=new NativeCache("https://fixture.invalid",null);c.packet=new B3Packet();c.commit={"seal"=>"one"};c.store.write("sf.commit",{"base"=>c.base,"seal"=>"one"});var a=b3Scene("ll2:launch:a",1000000l,998900l,true);var b=b3Scene("ll2:launch:b",1001500l,998950l,true);LaunchReminderForeground.publishQueue(c,999000l,[a,b]);var s=LaunchReminder.selected(c.store.read("sf.reminder.snapshot"),999100l);Test.assertEqual(LaunchReminder.consume(c.store,s,999100l,999000l),0);logger.debug("B3_STORAGE_SEED selectedA slot0");return true;
}
(:test,:typecheck(false)) function b3StorageReopen(logger){
 var c=new NativeCache("https://fixture.invalid",null);var q=c.store.read("sf.reminder.snapshot");var a=LaunchReminder.selected(q,999101l);Test.assertEqual(a["id"],"ll2:launch:a");Test.assert(LaunchReminder.consume(c.store,a,999101l,999000l)==null);var b=LaunchReminder.selected(q,1000900l);Test.assertEqual(b["id"],"ll2:launch:b");Test.assertEqual(b["validated"],998950l);Test.assertEqual(LaunchReminder.consume(c.store,b,1000900l,b["since"]),1);logger.debug("B3_STORAGE_REOPEN duplicateSuppressed successorB originalAge");return true;
}
(:test,:typecheck(false)) function b3RescheduleAndQuiet(logger){
 var c=new NativeCache("https://fixture.invalid",new B3Store());c.packet=new B3Packet();c.commit={"seal"=>"one"};c.store.write("sf.commit",{"base"=>c.base,"seal"=>"one"});Application.Properties.setValue("LaunchReminders",1);c.store.write("sf.reminder.control",{"enabled"=>true,"since"=>999000l});var sink=new B3Sink();
 var a=b3Scene("ll2:launch:a",1000000l,998900l,true);var b=b3Scene("ll2:launch:a",1000300l,998900l,true);
 LaunchReminderForeground.publishQueue(c,999000l,[a]);LaunchReminder.wakeWith(c,999400l,false,sink.method(:post));Test.assertEqual(sink.entries.size(),1);Test.assertEqual(sink.entries[0][0],1);
 LaunchReminderForeground.publishQueue(c,999400l,[b]);LaunchReminder.wakeWith(c,999400l,false,sink.method(:post));Test.assertEqual(sink.entries.size(),2);Test.assertEqual(sink.entries[1][0],0);
 LaunchReminderForeground.publishQueue(c,999400l,[a]);LaunchReminder.wakeWith(c,999400l,false,sink.method(:post));Test.assertEqual(sink.entries.size(),2);
 Test.assert(LaunchReminder.quiet(null,true,false,79200,25200,43200));Test.assert(LaunchReminder.quiet(true,true,false,79200,25200,43200));Test.assert(LaunchReminder.quiet(false,true,true,79200,25200,43200));
 LaunchReminder.wakeWith(c,999700l,true,sink.method(:post));LaunchReminder.wakeWith(c,999701l,false,sink.method(:post));Test.assertEqual(sink.entries.size(),2);Application.Properties.setValue("LaunchReminders",0);logger.debug("B3_RESCHEDULE AtoBtoA consumedQuiet unknownSafe");return true;
}
(:test,:typecheck(false)) function b3OrdinaryReopen(logger){
 Application.Storage.clearValues();Application.Properties.setValue("LaunchReminders",1);var app=new SpaceFoxApp();app.getInitialView();app.view.onShow();var first=new NativeCache("https://fixture.invalid",null);first.packet=new B3Packet();first.commit={"seal"=>"one"};first.store.write("sf.commit",{"base"=>first.base,"seal"=>"one"});first.store.write("sf.reminder.control",{"enabled"=>true,"since"=>999000l});var a=b3Scene("ll2:launch:a",1000000l,998900l,true);var b=b3Scene("ll2:launch:b",1001500l,998950l,true);LaunchReminderForeground.publishQueue(first,999000l,[a,b]);var sink=new B3Sink();LaunchReminder.wakeWith(first,999100l,false,sink.method(:post));Test.assertEqual(sink.entries.size(),1);
 app.view.onHide();app=null;first=null;
 var reopened=new SpaceFoxApp();reopened.getInitialView();reopened.view.onShow();var cache=new NativeCache("https://fixture.invalid",null);var q=cache.store.read("sf.reminder.snapshot");var selected=LaunchReminder.selected(q,999101l);Test.assertEqual(selected["id"],"ll2:launch:a");Test.assertEqual(selected["validated"],998900l);LaunchReminder.wakeWith(cache,999101l,false,sink.method(:post));Test.assertEqual(sink.entries.size(),1);LaunchReminder.wakeWith(cache,999400l,false,sink.method(:post));Test.assertEqual(sink.entries.size(),2);Test.assertEqual(sink.entries[1][0],1);
 var successor=LaunchReminder.selected(q,1000900l);Test.assertEqual(successor["id"],"ll2:launch:b");Test.assertEqual(successor["validated"],998950l);LaunchReminder.wakeWith(cache,1000900l,false,sink.method(:post));Test.assertEqual(sink.entries.size(),3);Test.assertEqual(sink.entries[2][1],"ll2:launch:b");reopened.view.onHide();Application.Properties.setValue("LaunchReminders",0);logger.debug("B3_ORDINARY_REOPEN realStorage hideShow newApp newCache duplicateSuppressed sourceAge");return true;
}

// Exercise the production display/merge/publish owner after a real admission.
// The two technical scenes carry controlled times over real display strings.
(:test,:typecheck(false)) function b3DisplayRetainedSelection(logger){
 var store=new B1MemoryStore();var base="https://fixture.invalid/profile-a";var now=Time.now().value().toLong();
 var raw=WatchUi.loadResource(Rez.JsonData.B1ProfileFeed)["raw"];var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));var ref=batch.next();Test.assert(batch.immutable.put(ref,b1ProfileResponse(ref["path"])));
 var c=new NativeCache(base,store);Test.assert(b1Promote021(c,raw,now));
 var a=b3Scene("ll2:launch:a",now+1800,now-10,true);var b=b3Scene("ll2:launch:b",now+3600,now-5,true);
 var owner=c.packet.document["publisher"]["instance"];new NativeUpcomingCache(store,base,owner).save([a]);
 c.packet.presentation=b;c.packet.upcomingScenes=[];
 var app=new SpaceFoxApp();app.getInitialView();NativeForegroundApp.display(app,c);
 Test.assertEqual(app.view.context.launchId,a.launchId);var q=store.read("sf.reminder.snapshot");var selected=LaunchReminder.selected(q,now);
 Test.assertEqual(selected["id"],a.launchId);
 Test.assertEqual(selected["target"],a.retentionTarget);
 Test.assertEqual(selected["validated"],a.sourceValidated);
 Test.assert(LaunchReminder.bound(store,selected,base,Time.now().value().toLong()));
 Test.assertEqual(LaunchReminder.selected(q,a.retentionDeadline)["id"],b.launchId);
 logger.debug("B3_DISPLAY admittedPacket savedEarlierSelection actualDisplayQueue successor");return true;
}

(:test,:typecheck(false)) function b3EstimatedQueueBinding(logger){
 var now=999000l;var target=1000000l;var policy={"normal_interval_seconds"=>7200,"near_interval_seconds"=>3600,"fast_interval_seconds"=>null,"stale_cycles"=>4};
 var coarse=new SceneContext({"id"=>"ll2:launch:a","rocket"=>"Starship V3","purpose"=>"Flight Test","precision"=>"source-coarse","target"=>null,"displayTarget"=>target,"sourceValidated"=>998900l,"freshnessPolicy"=>policy,"reminderEligible"=>false});
 var minute=b3Scene("ll2:launch:b",1001500l,998950l,true);var store=new B3Store();var base="https://fixture.invalid";var pinCache=new NativeCache(base,store);pinCache.rememberPublisher({"instance"=>"fixture","generation"=>1,"selectionValidatedUtc"=>998900l},"wire");var queue=new NativeUpcomingCache(store,base,"fixture");queue.save([coarse,minute]);var rows=queue.load();Test.assertEqual(rows.size(),2);Test.assert(rows[0].displayTarget==target&&!rows[0].reminderEligible&&rows[0].schedule.remainingSeconds(now)==null);Test.assert(rows[1].reminderEligible&&rows[1].retentionTarget==1001500l);
 var row=coarse.cacheRow();Test.assert(queue.validRow(row));row.remove("displayTarget");Test.assert(queue.validRow(row));row.remove("reminderEligible");Test.assert(queue.validRow(row));var displayOnly=coarse.cacheRow();displayOnly.remove("reminderEligible");Test.assert(queue.validRow(displayOnly));
 var view=new SpaceFoxView(new B1Clock(),new ScheduleState(null,"empty"));view.setContext(rows[0]);Test.assertEqual(view.snapshotAt(now).countdown,CountdownFormat.format(target-now));
 var cache=new NativeCache(base,store);cache.packet=new B3Packet();cache.commit={"seal"=>"one"};LaunchReminderForeground.publishQueue(cache,now,rows);var snapshot=store.read("sf.reminder.snapshot");Test.assert(snapshot instanceof Dictionary&&LaunchReminder.selected(snapshot,now)==null);Test.assert(!rows[0].reminderEligible&&rows[1].reminderEligible);
 logger.debug("B3_NET_QUEUE sealedRoundtrip=true approximateNotReminder=true nearestNotSkipped=true");return true;
}
