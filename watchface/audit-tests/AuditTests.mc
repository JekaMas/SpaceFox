import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.System;
import Toybox.WatchUi;

(:test,:typecheck(false)) class AuditClock extends WatchClock {
 var now=999100;function utcSeconds(){return now;}function localTimeText(){return "13:23";}
}
(:test,:typecheck(false)) class AuditStore {
 var values={};function read(k){return values[k];}function write(k,v){values[k]=v;}function remove(k){values.remove(k);}
}
(:test,:typecheck(false)) class AuditScene extends SceneContext {
 var advances=0;
 function initialize(data){SceneContext.initialize(data);}
 function advanceFreshness(now){advances+=1;SceneContext.advanceFreshness(now);}
}
(:test,:typecheck(false)) class AuditSink {
 var calls=0;function post(slot,s){calls+=1;}
}
(:test,:typecheck(false)) function auditFreshnessAndRollover(logger){
 var policy={"normal_interval_seconds"=>3600,"near_interval_seconds"=>900,"fast_interval_seconds"=>null,"stale_cycles"=>3};
 var a=new AuditScene({"id"=>"ll2:launch:a","precision"=>"exact","target"=>1000000l,"retentionDeadline"=>1000900l,"sourceValidated"=>999000l,"freshnessPolicy"=>policy});
 var b=new AuditScene({"id"=>"ll2:launch:b","precision"=>"exact","target"=>1005000l,"retentionDeadline"=>1005900l,"sourceValidated"=>997000l,"freshnessPolicy"=>policy});
 var packet=new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.Exact)["payload"]);packet.presentation=a;packet.upcomingScenes=[b];var clock=new AuditClock();clock.now=999100;var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.setPacket(packet);view.onShow();view.syncDisplayMode(System.DISPLAY_MODE_HIGH_POWER);view.prepareRenderer();var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();a.advances=0;view.drawScene(dc);Test.assertEqual(a.advances,1);Test.assert(!a.stale&&!packet.stale);
 a.stale=true;clock.now=999101;a.advances=0;view.drawScene(dc);Test.assertEqual(a.advances,1);Test.assert(a.stale&&packet.stale);
 view.setContext(b);b.advances=0;view.drawScene(dc);Test.assertEqual(b.advances,1);Test.assert(!b.stale&&packet.stale);
 view.setContext(a);view.upcoming=[b];clock.now=1000900;b.advances=0;view.drawScene(dc);Test.assertMessage(view.context==b&&view.packet==null,"successor selected");
 Test.assertEqual(b.advances,1);
 Test.assertMessage(b.stale,"successor own age reaches 2700s stale threshold");logger.debug("AUDIT_FRESHNESS sameOnce alternateOwnAge sticky rolloverSuccessor");return true;
}
(:test,:typecheck(false)) function auditReminderCurrentRows(logger){
 var base="https://jekamas.github.io/SpaceFox";var store=new AuditStore();var owner=new NativeTrustedStore(store,base);var payload=WatchUi.loadResource(Rez.JsonData.Exact)["payload"];Test.assert(owner.save(payload));var packet=new NativeTrustedPacket(owner.load());var scene=packet.presentation;var target=scene.sourceValidated+660;scene.retentionTarget=target;scene.retentionDeadline=target+900;var now=target-600;var c=new NativeCache(base,store);c.packet=packet;var sink=new AuditSink();Application.Properties.setValue("LaunchReminders",1);
 store.write("sf.reminder.control",{"enabled"=>true,"since"=>now-1});LaunchReminderForeground.publishQueue(c,now-1,[scene]);var current=store.read("sf.reminder.snapshot");Test.assert(LaunchReminder.selected(current,now)!=null);LaunchReminder.wakeWith(c,now,false,sink.method(:post));Test.assertEqual(sink.calls,1);var attempts=store.read("sf.reminder.attempt");
 store.write("sf.reminder.snapshot",{"base"=>base,"id"=>scene.launchId,"target"=>target,"sequence"=>owner.marker()["sequence"]});Test.assert(LaunchReminder.selected(store.read("sf.reminder.snapshot"),now)==null);LaunchReminder.wakeWith(c,now,false,sink.method(:post));Test.assertEqual(sink.calls,1);Test.assert(nativeSame(attempts,store.read("sf.reminder.attempt")));
 LaunchReminderForeground.publishQueue(c,now,[scene]);LaunchReminder.wakeWith(c,now,false,sink.method(:post));Test.assertEqual(sink.calls,1);
 // Same launch reschedules A→B→A at one callback instant. Its consumed A
 // slot must survive the temporary B target and the rejected flat snapshot.
 scene.retentionTarget=target+300;scene.retentionDeadline=target+1200;LaunchReminderForeground.publishQueue(c,now,[scene]);LaunchReminder.wakeWith(c,now,false,sink.method(:post));Test.assertEqual(sink.calls,2);
 scene.retentionTarget=target;scene.retentionDeadline=target+900;LaunchReminderForeground.publishQueue(c,now,[scene]);LaunchReminder.wakeWith(c,now,false,sink.method(:post));Test.assertEqual(sink.calls,2);
 LaunchReminder.wakeWith(c,now+300,true,sink.method(:post));LaunchReminder.wakeWith(c,now+301,false,sink.method(:post));Test.assertEqual(sink.calls,2);Application.Properties.setValue("LaunchReminders",0);logger.debug("AUDIT_REMINDER rowsPreserved oldShapeClosed ledgerRetained AtoBtoA quietConsumed");return true;
}
