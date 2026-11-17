import Toybox.Lang;
// Publish only after the existing cache admission and commit verification.
(:extendedCode, :typecheck(false))
module LaunchReminderForeground {
 // One compact atomic projection mirrors the view's bounded ordered queue.
 // Source validation time travels with each scene; refresh cannot rejuvenate it.
 function publishQueue(cache,now,scenes){try{
  var p=cache.packet;var marker=new NativeTrustedStore(cache.store,cache.base).marker();var old=cache.store.read("sf.reminder.snapshot");
  if(p==null||!(marker instanceof Dictionary)||!(marker["sequence"] instanceof Number||marker["sequence"] instanceof Long)||scenes.size()==0){if(old!=null){cache.store.remove("sf.reminder.snapshot");}return;}
  var rows=[];
  for(var i=0;i<scenes.size()&&i<3;i+=1){var scene=scenes[i];var since=now;
   if(old instanceof Dictionary&&LaunchReminder.same(old["base"],cache.base)){
    var prior=old["rows"];if(prior instanceof Array){for(var j=0;j<prior.size();j+=1){var r=prior[j];if(r instanceof Array&&r.size()==10&&LaunchReminder.same(r[0],scene.launchId)&&r[1]==scene.retentionTarget&&LaunchReminder.number(r[6])&&r[6]<=now){since=r[6];break;}}}
   }
   var policy=scene.freshnessPolicy;var compact=policy instanceof Dictionary?[policy["normal_interval_seconds"],policy["near_interval_seconds"],policy["fast_interval_seconds"],policy["stale_cycles"]]:null;
   var title=scene.rocket;if(scene.purpose.length()>0){title+=(title.length()>0?" · ":"")+scene.purpose;}if(title.length()==0){title="Launch";}
   rows.add([scene.launchId,scene.retentionTarget,scene.sourcePrecision.equals("minute")?"source-coarse":scene.sourcePrecision,title,scene.sourceValidated,scene.stale,since,compact,scene.retentionDeadline,scene.reminderEligible]);
  }
  var snapshot={"base"=>cache.base,"rows"=>rows,"sequence"=>marker["sequence"]};
  if(!(old instanceof Dictionary)||!nativeSame(old,snapshot)){cache.store.write("sf.reminder.snapshot",snapshot);}
 }catch(e){try{cache.store.remove("sf.reminder.snapshot");}catch(ignore){}}}
}
