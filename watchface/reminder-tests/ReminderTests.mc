import Toybox.Application;
import Toybox.Background;
import Toybox.Lang;
import Toybox.Test;
import Toybox.Time;
import Toybox.WatchUi;

(:test,:typecheck(false)) class ReminderStore {
 var data={};var writes=0;var failWrite=false;var replaceCommitOnAttempt=false;
 function read(k){return data[k];}
 function write(k,v){if(failWrite){throw new Lang.InvalidValueException("write");}writes+=1;data[k]=v;if(replaceCommitOnAttempt&&k.equals("sf.reminder.attempt")){data["sf.commit"]={"base"=>"https://example.invalid","seal"=>"new"};}}
 function remove(k){writes+=1;data.remove(k);}
}
(:test,:typecheck(false)) class ReminderCache {
 var store;var packet=null;var commit=null;var commitKey="sf.commit";var base="https://example.invalid";
 function initialize(){store=new ReminderStore();}
}
(:test,:typecheck(false)) class ReminderProjection extends NativeFeed {
 function initialize(doc){document=doc;}
}
(:test,:typecheck(false)) class ReminderSink {
 var calls=0;var fail=false;
 function post(slot,s){calls+=1;if(fail){throw new Lang.InvalidValueException("post");}}
}
(:typecheck(false)) function reminderFixture(){
 return {"base"=>"https://example.invalid","id"=>"source:launch:one","target"=>1000000l,"title"=>"Mission","validated"=>999000l,"since"=>998000l,"stale"=>false,"policy"=>[7200,3600,null,4],"seal"=>"one","commitKey"=>"sf.commit"};
}
(:typecheck(false)) function reminderReady(c){c.store.data["sf.commit"]={"base"=>c.base,"seal"=>"one"};c.store.data["sf.reminder.snapshot"]=reminderFixture();c.store.data["sf.reminder.control"]={"enabled"=>true,"since"=>998000l};Application.Properties.setValue("LaunchReminders",1);}
(:test,:typecheck(false)) function settingsPositive(logger){
 Test.assertEqual(SettingsMenu.keys()[12],"LaunchReminders");Test.assertEqual(SettingsMenuText.reminderChoices("en")[0],"Off");Test.assertEqual(SettingsMenuText.reminderChoices("ru")[1],"Вкл.");
 Application.Properties.setValue("FeedBaseUrl","");Application.Properties.setValue("LaunchReminders",0);var app=new SpaceFoxApp();SettingsMenu.apply(app,"LaunchReminders",1);Test.assertEqual(Application.Properties.getValue("LaunchReminders"),1);SettingsMenu.apply(app,"LaunchReminders",0);Test.assertEqual(Application.Properties.getValue("LaunchReminders"),0);Application.Properties.setValue("FeedBaseUrl","https://jekamas.github.io/SpaceFox");Background.deleteTemporalEvent();return true;
}
(:test,:typecheck(false)) function cadencePositive(logger){
 var c=new ReminderCache();reminderReady(c);var sink=new ReminderSink();
 var times=[999100l,999400l,999700l,1000000l];for(var i=0;i<times.size();i+=1){LaunchReminder.wakeWith(c,times[i],false,sink.method(:post));Test.assertEqual(sink.calls,i+1);}
 Application.Properties.setValue("LaunchReminders",0);return true;
}
(:test,:typecheck(false)) function cadenceNegative(logger){
 var c=new ReminderCache();reminderReady(c);var sink=new ReminderSink();Application.Properties.setValue("LaunchReminders",0);
 LaunchReminder.wakeWith(c,999100l,false,sink.method(:post));Test.assertEqual(sink.calls,0);
 Application.Properties.setValue("LaunchReminders",1);c.store.data["sf.reminder.control"]={"enabled"=>true,"since"=>999101l};LaunchReminder.wakeWith(c,999101l,false,sink.method(:post));Test.assertEqual(sink.calls,0);
 LaunchReminder.wakeWith(c,1000001l,false,sink.method(:post));Test.assertEqual(sink.calls,0);Application.Properties.setValue("LaunchReminders",0);return true;
}
(:test,:typecheck(false)) function quietPositive(logger){Test.assert(!LaunchReminder.quiet(false,true,false,79200,25200,43200));return true;}
(:test,:typecheck(false)) function quietNegative(logger){
 Test.assert(LaunchReminder.quiet(true,true,false,79200,25200,43200));Test.assert(LaunchReminder.quiet(false,false,false,79200,25200,43200));Test.assert(LaunchReminder.quiet(false,true,true,79200,25200,43200));
 Test.assert(LaunchReminder.quiet(false,true,null,79200,25200,43200));Test.assert(LaunchReminder.quiet(false,true,false,null,25200,43200));Test.assert(LaunchReminder.quiet(false,true,false,79200,25200,82800));Test.assert(LaunchReminder.quiet(false,true,false,79200,25200,18000));
 var c=new ReminderCache();reminderReady(c);var sink=new ReminderSink();LaunchReminder.wakeWith(c,999100l,true,sink.method(:post));LaunchReminder.wakeWith(c,999101l,false,sink.method(:post));Test.assertEqual(sink.calls,0);Application.Properties.setValue("LaunchReminders",0);return true;
}
(:test,:typecheck(false)) function identityPositive(logger){
 var c=new ReminderCache();reminderReady(c);var sink=new ReminderSink();LaunchReminder.wakeWith(c,999100l,false,sink.method(:post));LaunchReminder.wakeWith(c,999101l,false,sink.method(:post));Test.assertEqual(sink.calls,1);
 var reopened=new ReminderCache();reopened.store=c.store;LaunchReminder.wakeWith(reopened,999102l,false,sink.method(:post));Test.assertEqual(sink.calls,1);
 var moved=reopened.store.data["sf.reminder.snapshot"];moved["target"]=1000600l;moved["since"]=999102l;moved["seal"]="two";reopened.store.data["sf.commit"]["seal"]="two";
 LaunchReminder.wakeWith(reopened,999400l,false,sink.method(:post));Test.assertEqual(sink.calls,1);LaunchReminder.wakeWith(reopened,999700l,false,sink.method(:post));Test.assertEqual(sink.calls,2);LaunchReminder.wakeWith(reopened,999701l,false,sink.method(:post));Test.assertEqual(sink.calls,2);
 // Repeated callbacks at one instant around A→B→A must not erase A.
 var x=new ReminderCache();reminderReady(x);var out=new ReminderSink();var a=x.store.data["sf.reminder.snapshot"];
 LaunchReminder.wakeWith(x,999400l,false,out.method(:post));Test.assertEqual(out.calls,1);
 a["target"]=1000300l;a["seal"]="b";x.store.data["sf.commit"]["seal"]="b";
 LaunchReminder.wakeWith(x,999400l,false,out.method(:post));Test.assertEqual(out.calls,2);
 a["target"]=1000000l;a["seal"]="a";x.store.data["sf.commit"]["seal"]="a";
 var again=new ReminderCache();again.store=x.store;LaunchReminder.wakeWith(again,999400l,false,out.method(:post));Test.assertEqual(out.calls,2);
 // A backward clock cannot revive an expired row after bounded pruning.
 a["target"]=1001000l;a["seal"]="c";x.store.data["sf.commit"]["seal"]="c";
 LaunchReminder.wakeWith(x,1000100l,false,out.method(:post));Test.assertEqual(out.calls,3);
 a["target"]=1000000l;a["seal"]="a";x.store.data["sf.commit"]["seal"]="a";
 LaunchReminder.wakeWith(x,999400l,false,out.method(:post));Test.assertEqual(out.calls,3);
 // Full history fails closed while all retained identities are actionable.
 var full=new ReminderCache();reminderReady(full);var all=[];for(var k=0;k<16;k+=1){all.add({"base"=>full.base,"id"=>"other:"+k,"target"=>1000001l,"last"=>0});}full.store.data["sf.reminder.attempt"]={"watermark"=>999100l,"rows"=>all};
 var suppressed=new ReminderSink();LaunchReminder.wakeWith(full,999100l,false,suppressed.method(:post));Test.assertEqual(suppressed.calls,0);Test.assertEqual(full.store.data["sf.reminder.attempt"]["rows"].size(),16);
 Application.Properties.setValue("LaunchReminders",0);return true;
}
(:test,:typecheck(false)) function identityNegative(logger){
 var c=new ReminderCache();reminderReady(c);var sink=new ReminderSink();var s=c.store.data["sf.reminder.snapshot"];
 var exact=WatchUi.loadResource(Rez.JsonData.ReminderExact);var projection=new ReminderProjection(exact);Test.assert(projection.reminderProjection()!=null);exact["launch"]["status"]="unknown";Test.assert(projection.reminderProjection()==null);
 var minute=WatchUi.loadResource(Rez.JsonData.ReminderMinute);var minProjection=new ReminderProjection(minute);Test.assert(minProjection.reminderProjection()!=null);var timing=minute["launch"]["timing"];var originalStart=timing["window_start_utc"];timing["window_start_utc"]=timing["nominal_utc"]+1;Test.assert(minProjection.reminderProjection()==null);timing["window_start_utc"]=originalStart;timing["source_precision_id"]=2;Test.assert(minProjection.reminderProjection()==null);
 c.store.data["sf.incoming.feed"]={"base"=>c.base,"sha256"=>"new","sequence"=>1};LaunchReminder.wakeWith(c,999100l,false,sink.method(:post));Test.assertEqual(sink.calls,0);c.store.remove("sf.incoming.feed");
 c.store.replaceCommitOnAttempt=true;LaunchReminder.wakeWith(c,999100l,false,sink.method(:post));Test.assertEqual(sink.calls,0);c.store.replaceCommitOnAttempt=false;c.store.data["sf.commit"]["seal"]="one";c.store.remove("sf.reminder.attempt");
 s["stale"]=true;LaunchReminder.wakeWith(c,999100l,false,sink.method(:post));Test.assertEqual(sink.calls,0);s["stale"]=false;s["validated"]=980000l;LaunchReminder.wakeWith(c,999100l,false,sink.method(:post));Test.assertEqual(sink.calls,0);s["validated"]=999000l;c.store.data["sf.commit"]["seal"]="changed";LaunchReminder.wakeWith(c,999100l,false,sink.method(:post));Test.assertEqual(sink.calls,0);Application.Properties.setValue("LaunchReminders",0);return true;
}
(:test,:typecheck(false)) function schedulerPositive(logger){var s=reminderFixture();Test.assertEqual(LaunchReminder.next(s,999000l,null,998000l),999100l);Test.assertEqual(LaunchReminder.next(s,999101l,999101l,998000l),999401l);return true;}
(:test,:typecheck(false)) function schedulerNegative(logger){
 var s=reminderFixture();Test.assertEqual(LaunchReminder.next(s,999300l,999300l,998000l),999700l);Test.assert(LaunchReminder.next(s,1000001l,null,998000l)==null);
 var c=new ReminderCache();reminderReady(c);var sink=new ReminderSink();c.store.failWrite=true;LaunchReminder.wakeWith(c,999100l,false,sink.method(:post));Test.assertEqual(sink.calls,0);c.store.failWrite=false;LaunchReminder.wakeWith(c,999101l,false,sink.method(:post));LaunchReminder.wakeWith(c,999102l,false,sink.method(:post));Test.assertEqual(sink.calls,1);Application.Properties.setValue("LaunchReminders",0);return true;
}

(:typecheck(false)) function reminderIncoming(store,raw){
 var h=new NativeWireHash();h.put(raw);var sha=h.digest();var parts=[];var n=0;for(var start=0;start<raw.length();start+=512){var end=start+512;if(end>raw.length()){end=raw.length();}store.data["sf.incoming.feed.0."+n]=raw.substring(start,end);parts.add(0);n+=1;}
 var marker={"v"=>2,"kind"=>"feed","parts"=>parts,"sha256"=>sha,"sequence"=>1,"bytes"=>h.count};store.data["sf.incoming.feed"]=marker;return marker;
}
(:typecheck(false)) function reminderAccepted(){return {"instance"=>"40655f8a46c4c47ecb6f6d4a8608bde8396c6c440807e09d962b1f7fde006204","generation"=>13,"precision"=>"exact","validated"=>1794631193l,"content"=>reminderContentHash(),"wire"=>"prior","policy"=>[3600,900,null,3]};}
(:test,:typecheck(false)) function equivalencePositive(logger){var store=new ReminderStore();var raw=reminderRawFixture();var m=reminderIncoming(store,raw);Test.assert(LaunchReminder.sameIncoming(store,reminderAccepted(),m,1794631300l));return true;}
(:typecheck(false)) function reminderReplace(raw,needle,replacement){var at=raw.find(needle);if(at==null){return raw;}return raw.substring(0,at)+replacement+raw.substring(at+needle.length(),raw.length());}
(:test,:typecheck(false)) function equivalenceNegative(logger){
 var store=new ReminderStore();var raw=reminderRawFixture();var changed=reminderReplace(raw,"\"status\":\"pending\"","\"status\":\"started\"");Test.assert(!changed.equals(raw));var m=reminderIncoming(store,changed);Test.assert(!LaunchReminder.sameIncoming(store,reminderAccepted(),m,1794631300l));
 changed=reminderReplace(raw,"\"stale\":false","\"stale\":true");Test.assert(!changed.equals(raw));m=reminderIncoming(store,changed);Test.assert(!LaunchReminder.sameIncoming(store,reminderAccepted(),m,1794631300l));return true;
}

(:test,:typecheck(false)) function sharedRegistration(logger){
 Background.deleteTemporalEvent();var now=Time.now().value().toLong();var c=new ReminderCache();var store=c.store;var transfer=new NativeTransfer(c.base,store);transfer.lastAttempt=now;
 var snapshot=reminderFixture();snapshot["target"]=now+1800;snapshot["validated"]=now;snapshot["since"]=now-1;snapshot["base"]=c.base;store.data["sf.commit"]={"base"=>c.base,"seal"=>"one"};store.data["sf.reminder.snapshot"]=snapshot;store.data["sf.reminder.control"]={"enabled"=>true,"since"=>now-1};Application.Properties.setValue("LaunchReminders",1);
 armFeed(transfer,now);var first=Background.getTemporalEventRegisteredTime();Test.assert(first!=null);Test.assertEqual(first.value().toLong(),now+300);
 store.data["sf.transfer.ready"]={"base"=>c.base,"accepted"=>true};store.data["sf.transfer.plan"]={"base"=>c.base,"target"=>now+1800,"policy"=>[3600,3600,null]};
 armFeed(transfer,now);var second=Background.getTemporalEventRegisteredTime();Test.assert(second!=null);Test.assertEqual(second.value().toLong(),now+900);
 Background.deleteTemporalEvent();Application.Properties.setValue("LaunchReminders",0);logger.debug("SHARED_REGISTRATION feed=300 reminder=900");return true;
}

(:test,:typecheck(false)) class ReminderPacketFixture {
 var reminderData={"id"=>"source:launch:one","target"=>1000000l,"precision"=>"exact","title"=>"Launch"};
 var validation=999000l;var stale=false;var contentHash="content";var wireHash="wire";
 var document={"refreshPolicy"=>{"normal_interval_seconds"=>3600,"near_interval_seconds"=>900,"fast_interval_seconds"=>null,"stale_cycles"=>3},"publisher"=>{"instance"=>"publisher","generation"=>1}};
}
(:test,:typecheck(false)) function snapshotWrites(logger){
 var c=new ReminderCache();c.packet=new ReminderPacketFixture();c.commit={"seal"=>"one"};LaunchReminderForeground.publish(c,999000l);Test.assertEqual(c.store.writes,1);
 LaunchReminderForeground.publish(c,999001l);Test.assertEqual(c.store.writes,1);c.commit={"seal"=>"two"};LaunchReminderForeground.publish(c,999002l);Test.assertEqual(c.store.writes,2);c.packet=null;LaunchReminderForeground.publish(c,999003l);Test.assertEqual(c.store.writes,3);LaunchReminderForeground.publish(c,999004l);Test.assertEqual(c.store.writes,3);
 // Exercise the real foreground cache: accept a source, verify its durable
 // commit on reopen, preserve its fresh snapshot without another write, and
 // reconstruct an absent snapshot only from that fully parsed accepted feed.
 var store=new ReminderStore();var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
 var cache=new NativeCache("https://example.invalid",store);var now=1794551202l;Test.assert(cache.accept(WatchUi.loadResource(Rez.JsonData.DisplayInitial)["raw"],now));
 LaunchReminderForeground.publish(cache,now);var admitted=store.read("sf.reminder.snapshot");Test.assert(admitted instanceof Dictionary);Test.assert(LaunchReminder.bound(store,admitted,cache.base,now));
 var reopened=new NativeCache(cache.base,store);Test.assert(reopened.load(now)!=null);Test.assert(reopened.packet instanceof NativeBridgeFeed);
 var before=store.writes;LaunchReminderForeground.publish(reopened,now+1);Test.assertEqual(store.writes,before);Test.assert(nativeSame(admitted,store.read("sf.reminder.snapshot")));
 store.remove("sf.reminder.snapshot");before=store.writes;LaunchReminderForeground.publish(reopened,now+1);Test.assertEqual(store.writes,before+1);var restored=store.read("sf.reminder.snapshot");Test.assert(restored instanceof Dictionary);Test.assert(LaunchReminder.bound(store,restored,reopened.base,now+1));
 store.data["sf.commit"]["seal"]="invalid";var rejected=new NativeCache(cache.base,store);Test.assert(rejected.load(now+2)==null);LaunchReminderForeground.publish(rejected,now+2);Test.assert(store.read("sf.reminder.snapshot")==null);return true;
}
