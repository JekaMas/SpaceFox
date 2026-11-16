import Toybox.Lang;
// Publish only after the existing cache admission and commit verification.
(:extendedCode, :typecheck(false))
module LaunchReminderForeground {
 function publish(cache,now){try{
  var p=cache.packet;var row=p==null?null:p.reminderData;var marker=cache.commit;var old=cache.store.read("sf.reminder.snapshot");
  if(row==null||!(marker instanceof Dictionary)||!(marker["seal"] instanceof String)){if(old!=null){cache.store.remove("sf.reminder.snapshot");}return;}
  var since=now;
  if(old instanceof Dictionary&&LaunchReminder.same(old["base"],cache.base)&&LaunchReminder.same(old["id"],row["id"])&&old["target"]==row["target"]&&LaunchReminder.number(old["since"])&&old["since"]<=now){since=old["since"];}
  var policy=p.document["refreshPolicy"];
  var snapshot={"base"=>cache.base,"id"=>row["id"],"target"=>row["target"],"precision"=>row["precision"],"title"=>row["title"],"validated"=>p.validation,"stale"=>p.stale,"since"=>since,"policy"=>[policy["normal_interval_seconds"],policy["near_interval_seconds"],policy["fast_interval_seconds"],policy["stale_cycles"]],"commitKey"=>cache.commitKey,"seal"=>marker["seal"],"content"=>p.contentHash,"wire"=>p.wireHash,"instance"=>p.document["publisher"]["instance"],"generation"=>p.document["publisher"]["generation"]};
  if(old instanceof Dictionary&&nativeSame(old,snapshot)){return;}cache.store.write("sf.reminder.snapshot",snapshot);
 }catch(e){}}
}
