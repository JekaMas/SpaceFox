import Toybox.ActivityMonitor;
import Toybox.Application;
import Toybox.Background;
import Toybox.Lang;
import Toybox.Notifications;
import Toybox.System;
import Toybox.Time;
import Toybox.Time.Gregorian;
import Toybox.UserProfile;

// One background owner posts; foreground only publishes accepted state and arms.
(:background, :extendedCode, :typecheck(false))
module LaunchReminder {
 function enabled(){try{return Application.Properties.getValue("LaunchReminders")==1;}catch(e){return false;}}
 function number(v){return v instanceof Number||v instanceof Long;}
 function same(a,b){return a instanceof String&&b instanceof String&&a.equals(b);}
 function syncEnable(store,now){
  var on=enabled();var state=store.read("sf.reminder.control");
  if(!(state instanceof Dictionary)||state["enabled"]!=on||!number(state["since"])||state["since"]>now){state={"enabled"=>on,"since"=>now};store.write("sf.reminder.control",state);}
  return state;
 }
 function valid(s,base,now){
  if(!(s instanceof Dictionary)||!same(s["base"],base)||!(s["id"] instanceof String)||!(s["seal"] instanceof String)||!number(s["target"])||!number(s["validated"])||!number(s["since"])||s["validated"]>now||s["since"]>now||s["stale"]!=false){return false;}
  var p=s["policy"];if(!(p instanceof Array)||p.size()!=4||!number(p[0])||!number(p[1])||p[2]!=null&&!number(p[2])||!number(p[3])||p[0]<300||p[1]<300||p[3]<1||p[2]!=null&&p[2]<300){return false;}
  var age=now-s["validated"];if(p[2]!=null){return age/p[2]<p[3];}
  if(age/p[0]>=p[3]){return false;}var end=now<s["target"]+1800?now:s["target"]+1800;
  return !(end>=s["target"]-7200&&end>=s["validated"]&&(end-s["validated"])/p[1]>=p[3]);
 }
 // Compare only unchanged, previously accepted content; do not advance age.
 function sameIncoming(store,s,m,now){try{
  if(m["v"]!=2||!same(m["kind"],"feed")||!(m["parts"] instanceof Array)||m["parts"].size()<1||m["parts"].size()>16||!(m["sha256"] instanceof String)||!number(m["sequence"])||m["sequence"]<1||!number(m["bytes"])||m["bytes"]<1||m["bytes"]>4096){return false;}
  var raw="";for(var i=0;i<m["parts"].size();i+=1){var slot=m["parts"][i];if(!number(slot)||slot<0||slot>1){return false;}var piece=store.read("sf.incoming.feed."+slot+"."+i);if(!(piece instanceof String)||piece.length()>512){return false;}raw+=piece;if(raw.length()>4096){return false;}}
  var wire=new NativeWireHash();wire.put(raw);if(wire.count>4096||!wire.digest().equals(m["sha256"])||wire.count!=m["bytes"]){return false;}
  var parser=new NativeJson();parser.feedMode=true;parser.keepCatalogNames=false;var doc=parser.parse(raw,4096);var launch=doc["launch"];var pub=doc["publisher"];
  if(!(launch instanceof Dictionary)||!(pub instanceof Dictionary)||!same(pub["instance"],s["instance"])||!number(pub["generation"])||pub["generation"]<s["generation"]||!number(pub["selectionValidatedUtc"])||pub["selectionValidatedUtc"]>now||!number(launch["source_validated_utc"])||launch["source_validated_utc"]<s["validated"]||launch["source_validated_utc"]>pub["selectionValidatedUtc"]||launch["stale"]!=false||!(launch["rescheduled"] instanceof Boolean)||["countdown","awaiting-update","uncertain"].indexOf(doc["timingState"])<0){return false;}
  if(pub["generation"]==s["generation"]&&!same(m["sha256"],s["wire"])){return false;}
  if(same(s["precision"],"exact")&&["countdown","awaiting-update"].indexOf(doc["timingState"])<0||same(s["precision"],"source-coarse")&&!same(doc["timingState"],"uncertain")||!same(s["precision"],"exact")&&!same(s["precision"],"source-coarse")){return false;}
  var current=store.read("sf.incoming.feed");if(!(current instanceof Dictionary)||current["sequence"]!=m["sequence"]||!same(current["sha256"],m["sha256"])){return false;}
  var poll=doc["pollIntervalSeconds"];var p=s["policy"];if(!number(poll)||poll!=p[0]&&poll!=p[1]&&(p[2]==null||poll!=p[2])){return false;}
  var h=new NativeWireHash();var start=0;for(var j=0;j<parser.ignored.size();j+=1){var span=parser.ignored[j];h.range(raw,start,span[0]);h.put("null");start=span[1];}h.range(raw,start,raw.length());return same(h.digest(),s["content"]);
 }catch(e){return false;}}
 function bound(store,s,base,now){
  if(!valid(s,base,now)||!(s["commitKey"] instanceof String)||["sf.commit","sf.recovery"].indexOf(s["commitKey"])<0){return false;}
  var marker=store.read(s["commitKey"]);if(!(marker instanceof Dictionary)||!same(marker["base"],base)||!same(marker["seal"],s["seal"])){return false;}
  var incoming=store.read("sf.incoming.feed");if(!(incoming instanceof Dictionary)||!same(incoming["base"],base)){return true;}
  var done=store.read("sf.incoming.feed.processed");var token=incoming["sha256"]+":"+incoming["sequence"];
  if(done instanceof String&&done.equals(token)){return true;}
  var old=store.read("sf.reminder.compare");if(old instanceof Dictionary&&same(old["seal"],s["seal"])&&old["same"]==false){return false;}
  if(old instanceof Dictionary&&same(old["seal"],s["seal"])&&same(old["token"],token)&&old["same"]==true){return true;}
  var sameContent=sameIncoming(store,s,incoming,now);store.write("sf.reminder.compare",{"seal"=>s["seal"],"token"=>token,"same"=>sameContent});return sameContent;
 }
 function quiet(dnd,vibrate,sleep,sleepStart,wake,localSeconds){
  if(!(dnd instanceof Boolean)||!(vibrate instanceof Boolean)||!(sleep instanceof Boolean)||!number(sleepStart)||!number(wake)||!number(localSeconds)||sleepStart<0||sleepStart>=86400||wake<0||wake>=86400||sleepStart==wake||localSeconds<0||localSeconds>=86400){return true;}
  if(dnd||!vibrate||sleep){return true;}return sleepStart<wake?localSeconds>=sleepStart&&localSeconds<wake:localSeconds>=sleepStart||localSeconds<wake;
 }
 function isQuiet(now){try{
  var ds=System.getDeviceSettings();if(!(ds has :doNotDisturb)||!(ds has :vibrateOn)){return true;}
  var info=ActivityMonitor.getInfo();if(info==null||!(info has :isSleepMode)){return true;}
  var profile=UserProfile.getProfile();if(profile==null||!(profile has :sleepTime)||!(profile has :wakeTime)||profile.sleepTime==null||profile.wakeTime==null){return true;}
  var local=Gregorian.info(new Time.Moment(now.toNumber()),Time.FORMAT_SHORT);
  return quiet(ds.doNotDisturb,ds.vibrateOn,info.isSleepMode,profile.sleepTime.value(),profile.wakeTime.value(),local.hour*3600+local.min*60+local.sec);
 }catch(e){return true;}}
 function next(s,now,last,since){
  var times=[s["target"]-900,s["target"]-600,s["target"]-300,s["target"]];
  for(var i=0;i<times.size();i+=1){var t=times[i];if(t<since){continue;}var candidate=now>t?now:t;if(last!=null&&candidate<last+300){candidate=last+300;}var limit=i==3?t:t+90;if(candidate<=limit){return candidate;}}
  return null;
 }
 function candidate(s,now,since,prior){
  var times=[s["target"]-900,s["target"]-600,s["target"]-300,s["target"]];var index=null;
  for(var i=0;i<times.size();i+=1){var t=times[i];if(t>=since&&now>=t&&now<=t+(i==3?0:90)){index=i;}}
  if(index==null){return null;}if(prior instanceof Dictionary&&same(prior["base"],s["base"])&&same(prior["id"],s["id"])&&prior["target"]==s["target"]&&number(prior["last"])&&prior["last"]>=index){return null;}return index;
 }
 // Retain every still-actionable identity; if full or the clock moves backward,
 // fail closed rather than forget a consumed slot. Expired rows can be dropped
 // only while preserving the monotonic watermark in the same durable write.
 function consume(store,s,now,since){
  var saved=store.read("sf.reminder.attempt");var rows=[];var watermark=now;
  if(saved!=null){
   if(!(saved instanceof Dictionary)){return null;}
   if(saved.hasKey("rows")){
    if(!(saved["rows"] instanceof Array)||saved["rows"].size()>16||!number(saved["watermark"])||now<saved["watermark"]){return null;}
    watermark=now;
    for(var i=0;i<saved["rows"].size();i+=1){var r=saved["rows"][i];if(!(r instanceof Dictionary)||!(r["base"] instanceof String)||!(r["id"] instanceof String)||!number(r["target"])||!number(r["last"])||r["last"]<0||r["last"]>3){return null;}if(r["target"]>=now){rows.add(r);}}
   }else{
    // Upgrade the initial 0.1.15 test state without losing its consumed slot.
    if(!(saved["base"] instanceof String)||!(saved["id"] instanceof String)||!number(saved["target"])||!number(saved["last"])||saved["last"]<0||saved["last"]>3){return null;}
    if(saved["target"]>=now){rows.add(saved);}
   }
  }
  var prior=null;var pos=null;for(var j=0;j<rows.size();j+=1){var r=rows[j];if(same(r["base"],s["base"])&&same(r["id"],s["id"])&&r["target"]==s["target"]){prior=r;pos=j;break;}}
  var slot=candidate(s,now,since,prior);if(slot==null){return null;}
  var entry={"base"=>s["base"],"id"=>s["id"],"target"=>s["target"],"last"=>slot};
  if(pos==null){if(rows.size()>=16){return null;}rows.add(entry);}else{rows[pos]=entry;}
  store.write("sf.reminder.attempt",{"watermark"=>watermark,"rows"=>rows});
  var check=store.read("sf.reminder.attempt");if(!(check instanceof Dictionary)||check["watermark"]!=watermark||!(check["rows"] instanceof Array)||check["rows"].size()!=rows.size()){return null;}
  var observed=check["rows"][pos==null?rows.size()-1:pos];if(!(observed instanceof Dictionary)||!same(observed["base"],s["base"])||!same(observed["id"],s["id"])||observed["target"]!=s["target"]||observed["last"]!=slot){return null;}
  return slot;
 }
 function post(slot,s){if(slot==3&&Time.now().value().toLong()>s["target"]){return;}var label=slot==3?"Scheduled launch time":"Launch in "+[15,10,5][slot]+" min";Notifications.showNotification(label,s["title"],{:dismissPrevious=>true});}
 function wake(cache,now){try{if(!enabled()){return;}wakeWith(cache,now,null,method(:post));}catch(e){}}
 function wakeWith(cache,now,quietState,postMethod){
  try{var control=syncEnable(cache.store,now);if(!control["enabled"]){return;}var s=cache.store.read("sf.reminder.snapshot");if(!bound(cache.store,s,cache.base,now)){return;}var since=control["since"]>s["since"]?control["since"]:s["since"];var slot=consume(cache.store,s,now,since);if(slot==null){return;}
   var checkNow=now;if(quietState==null){checkNow=Time.now().value().toLong();quietState=isQuiet(checkNow);}if(checkNow<now||quietState!=false||!enabled()||candidate(s,checkNow,since,null)!=slot){return;}
   var current=cache.store.read("sf.reminder.snapshot");if(!(current instanceof Dictionary)||!same(current["seal"],s["seal"])||!same(current["id"],s["id"])||current["target"]!=s["target"]||!bound(cache.store,s,cache.base,checkNow)){return;}postMethod.invoke(slot,s);
  }catch(e){}
 }
 function nextWake(cache,now,last){try{var control=syncEnable(cache.store,now);if(!control["enabled"]){return null;}var s=cache.store.read("sf.reminder.snapshot");if(!bound(cache.store,s,cache.base,now)){return null;}var since=control["since"]>s["since"]?control["since"]:s["since"];return next(s,now,last,since);}catch(e){return null;}}
}
