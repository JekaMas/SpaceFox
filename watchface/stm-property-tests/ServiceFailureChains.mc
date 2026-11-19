import Toybox.Lang;
import Toybox.Test;
// Arbitrary service chains. The model owns logical clock, request identity,
// persisted outcome and expected IPC effects; it never reads a SUT decision.
(:test,:typecheck(false)) class ServiceChainTrace {
 var service;var store;var services=[];var callbacks=[];var identities=[];var epoch=0;
 var now=1794818604l;var millis=0;var configured=true;var online=true;var fault=0;var sendError=false;var ipcError=false;
 var state=0;var serial=0;var started=0;var hasTransfer=false;var bound=false;
 var last=null;var succeeded=false;var disk=0;var slots=0;var pointers=0;
 var sends=0;var localCallbacks=0;var cancellations=0;var arms=0;var registrations=0;var reminders=0;var exits=0;var deliveries=[];var trace=[];
 var coverage={"empty"=>0,"reconfigured"=>0,"send_throw"=>0,"slot_fail"=>0,"pointer_fail"=>0,"checkpoint_fail"=>0,"ipc_fail"=>0,"commit"=>0,"network_fail"=>0,"stale"=>0,"old_owner"=>0,"timeout"=>0,"cancel"=>0,"healthy_no"=>0,"offline"=>0,"restart"=>0};
 function initialize(){store=new PbtMemoryStore();newService();}
 function newService(){service=new PbtTemporalService();services.add(service);service.fakeStore=store;service.fakeUtc=now;service.fakeMillis=millis;service.testUrl=configured?"https://pbt.invalid":"";service.connected=online;service.sendFails=sendError;service.deliveryFails=ipcError;
  state=0;serial=0;hasTransfer=false;bound=false;sends=0;localCallbacks=0;cancellations=0;arms=0;registrations=0;reminders=0;exits=0;deliveries=[];}
 function terminal(kind,generation){
  if(state==2){return;}if(state==1){cancellations+=1;coverage["cancel"]+=1;}
  state=2;serial+=1;if(hasTransfer){arms+=1;}exits+=1;
  if(kind==1&&ipcError){exits+=1;kind=2;generation=0;coverage["ipc_fail"]+=1;}
  deliveries.add([kind,generation]);
 }
 function entryModel(){
  if(state==1){if(millis-started>=22000){coverage["timeout"]+=1;terminal(0,0);}return;}
  serial+=1;state=0;started=millis;registrations+=1;hasTransfer=true;bound=configured;
  if(!configured){exits+=1;coverage["empty"]+=1;return;}
  reminders+=1;var due=last==null||now<last;
  if(!due){if(succeeded&&disk!=0&&1795041780l>now){var deadline=last+3600;if(1795041780l<deadline){deadline=1795041780l;}due=now>=deadline;}
   else{due=online||now>=last+300;}}
  if(!due){coverage["healthy_no"]+=1;terminal(0,0);return;}
  last=now;succeeded=false;arms+=1;
  if(!online){coverage["offline"]+=1;terminal(0,0);return;}
  sends+=1;serial+=1;state=1;
  if(sendError){coverage["send_throw"]+=1;state=0;terminal(0,0);return;}
  identities.add([epoch,serial]);localCallbacks+=1;
 }
 function responseModel(index,code,generation){
  var current=index>=0&&state==1&&identities[index][0]==epoch&&identities[index][1]==serial;
  if(!current){coverage["stale"]+=1;if(index>=0&&identities[index][0]!=epoch){coverage["old_owner"]+=1;}return;}
  state=0;
  if(millis-started>=22000){coverage["timeout"]+=1;terminal(0,0);return;}
  if(code!=200){coverage["network_fail"]+=1;terminal(0,0);return;}
  // The independent input model uses one epoch/instance and an immutable
  // deterministic payload for each generation. Older content is rejected;
  // identical replay is a successful read without a second slot/pointer.
  if(disk!=0&&generation<=disk){if(generation==disk&&fault!=4){succeeded=true;}terminal(0,0);return;}
  if(fault==1){coverage["slot_fail"]+=1;terminal(1,generation);return;}
  slots+=1;if(fault==2){coverage["pointer_fail"]+=1;terminal(1,generation);return;}
  pointers+=1;disk=generation;coverage["commit"]+=1;
  if(fault==4){coverage["checkpoint_fail"]+=1;}else{succeeded=true;}
  terminal(0,0);
 }
 function step(event,a,b,seed,i){
  trace.add([event,a,b]);
  if(event==0){var prior=identities.size();entryModel();service.onTemporalEvent();if(identities.size()>prior){callbacks.add(service.sent[localCallbacks-1]);}}
  else if(event==1){var index=-1;if(identities.size()>0){index=a<0?identities.size()-1:a%identities.size();}responseModel(index,b[0],b[1]);
   var data=b[0]==200?{"data"=>pbtSnapshot(b[1],1795042200l+b[1]*60)}:null;
   if(index<0){service.receiveSnapshot(b[0],data);}else{callbacks[index].invoke(b[0],data);}}
  else if(event==2){now+=a;millis+=b;service.fakeUtc=now;service.fakeMillis=millis;}
  else if(event==3){configured=a==1;service.testUrl=configured?"https://pbt.invalid":"";if(configured){coverage["reconfigured"]+=1;}}
  else if(event==4){fault=a;store.fail=a;}
  else if(event==5){sendError=a==1;service.sendFails=sendError;}
  else if(event==6){ipcError=a==1;service.deliveryFails=ipcError;}
  else if(event==7){online=a==1;service.connected=online;}
  else if(event==8){terminal(0,0);service.finish();}
  else{terminal(0,0);service.finish();epoch+=1;newService();coverage["restart"]+=1;}
  verify(seed,i);
 }
 function verify(seed,i){
  ownerCheck(service.flight.state==state&&service.flight.serial==serial&&service.sends==sends&&service.sent.size()==localCallbacks&&service.cancellations==cancellations&&service.arms==arms&&service.registrations==registrations&&service.reminderCalls==reminders&&service.exits==exits&&service.deliveries.size()==deliveries.size()&&service.forbidden==0,"service-chain-effects",seed,i,trace,[state,serial,sends,localCallbacks,cancellations,arms,registrations,reminders,exits,deliveries.size()],[service.flight.state,service.flight.serial,service.sends,service.sent.size(),service.cancellations,service.arms,service.registrations,service.reminderCalls,service.exits,service.deliveries.size()]);
  for(var j=0;j<deliveries.size();j+=1){var got=service.deliveries[j];var kind=got.hasKey("volatileSnapshot")?1:(got["volatileDeliveryFailed"]==true?2:0);var generation=kind==1?got["volatileSnapshot"][1]["generation"]:0;
   ownerCheck(kind==deliveries[j][0]&&generation==deliveries[j][1],"service-chain-delivery",seed,i,trace,deliveries[j],[kind,generation]);}
  var marker=store.values["sf.snapshot.active:https://pbt.invalid"];var actual=0;var value=null;if(marker!=null){value=store.values["sf.snapshot."+marker["slot"]+":https://pbt.invalid"];actual=value[1]["generation"];}
  ownerCheck(actual==disk&&store.slots==slots&&store.pointers==pointers,"service-chain-durable",seed,i,trace,[disk,slots,pointers],[actual,store.slots,store.pointers]);
  if(value!=null){ownerCheck(value[3][9][0].equals("111.589567")&&value[3][9][1].equals("38.863128")&&value[3][20]==1795042200l+disk*60,"service-chain-facts",seed,i,trace,disk,value[3][20]);}
 }
 function final(seed,n){verify(seed,n);var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"service-chain-coverage",seed,n,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);}
}
(:typecheck(false)) function runGeneratedServiceFailure(firstSeed,seedCount){
 var total=0;
 for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){var rng=new OwnerRandom(seed);var run=new ServiceChainTrace();
  var prefix=[[3,0,0],[0,0,0],[3,1,0],[5,1,0],[0,0,0],[5,0,0],[0,0,0],[1,-1,[200,1]],[0,0,0],
   [2,3600,3600000],[4,1,0],[0,0,0],[1,-1,[200,2]],[4,0,0],[0,0,0],[1,0,[200,9]],[1,-1,[200,3]],
   [2,3600,3600000],[4,2,0],[6,1,0],[0,0,0],[1,-1,[200,4]],[4,0,0],[6,0,0],[0,0,0],[1,-1,[200,5]],
   [2,3600,3600000],[4,4,0],[0,0,0],[1,-1,[200,6]],[4,0,0],[0,0,0],[1,-1,[503,0]],[0,0,0],[2,0,22000],[0,0,0],[0,0,0],[8,0,0],
   [7,0,0],[2,300,300000],[0,0,0],[7,1,0],[9,0,0],[0,0,0],[1,0,[200,9]],[1,-1,[200,7]]];
  var events=prefix.size()+12+rng.draw(37);
  for(var i=0;i<events;i+=1){var e;var a;var b;if(i<prefix.size()){e=prefix[i][0];a=prefix[i][1];b=prefix[i][2];}else{e=rng.draw(10);a=rng.draw(5);b=0;
    if(e==1){a=rng.draw(8);b=[rng.draw(2)==0?200:503,1+rng.draw(9)];}else if(e==2){a=rng.draw(4)*300;b=a*1000;}else if(e==4){a=[0,1,2,4][rng.draw(4)];}else{a=a%2;}}
   run.step(e,a,b,seed,i);total+=1;}
  run.step(8,0,0,seed,events);total+=1;run.final(seed,events+1);
  // Preserve every old owner/Method throughout the trace, then release the fake OS registries.
  for(var j=0;j<run.services.size();j+=1){run.services[j].releaseHistory();}run.callbacks=[];
 }return total;
}
// Small causal replays for the two independently found lifetime failures.
(:test,:typecheck(false)) function serviceRetryConsumesVolatileLease(logger){
 var s=new PbtTemporalService();s.onTemporalEvent();s.fakeStore.fail=1;
 s.sent[0].invoke(200,{"data"=>pbtSnapshot(2,1795042320l)});
 Test.assert(s.deliveries[0]["volatileSnapshot"][1]["generation"]==2);
 s.fakeStore.fail=0;s.onTemporalEvent();s.sent[1].invoke(200,{"data"=>pbtSnapshot(3,1795042380l)});
 Test.assertMessage(s.deliveries[1]["provisional"]==true&&!s.deliveries[1].hasKey("volatileSnapshot"),"a consumed volatile lease must not redeliver after a newer durable success");
 Test.assert(new NativeTrustedStore(s.fakeStore,"https://pbt.invalid").load()[1]["generation"]==3);return true;
}
(:test,:typecheck(false)) function selectedFieldsStoppedReadRetainsSnapshot(logger){
 var f=new PbtSelectedFields();f.start(["custom1","custom2","custom3","custom4"],f.method(:callback));f.fakeApi.values[0]=27;f.read("en");f.stop();f.read("ru");
 Test.assertMessage(f.display("custom1").equals("27")&&f.state("custom1").equals("READY")&&f.fakeApi.gets==4,"an inactive read must preserve the accepted LOW field snapshot without querying providers");return true;
}
(:test,:typecheck(false)) class PbtLowMetricView extends PbtView {
 function initialize(){PbtView.initialize();fitness=new PbtFitness();selectedFields=new PbtEnergyFields();fitness.selectedFields=selectedFields;
  fitness.stepsValue=27;selectedFields.fakeApi.values[18]=72;selectedFields.fakeApi.values[22]=35;selectedFields.fakeApi.values[23]=68;}
 function readFitnessSnapshot(now as Number or Long) as Void {SpaceFoxView.readFitnessSnapshot(now);}
 function refreshFitnessWork() as Void {SpaceFoxView.refreshFitnessWork();}
}
(:test,:typecheck(false)) function coldLowAcquiresOneFieldSnapshot(logger){
 var v=new PbtLowMetricView();v.fakeMode=Toybox.System.DISPLAY_MODE_LOW_POWER;v.onShow();v.onUpdate(new PbtGraphics());
 Test.assert(v.displayMode()==v.LOW&&v.values["steps"]==27&&v.values["energy"]==68&&v.values["heart"]==72&&v.values["stress"]==35);
 Test.assert(v.timers.size()==0&&v.fitnessTimer==null&&!v.selectedFields.active());
 v.onUpdate(new PbtGraphics());v.onUpdate(new PbtGraphics());
 Test.assert(v.fitness.activityCalls==1&&v.fitness.heartCalls==0&&v.fitness.stressCalls==0&&v.selectedFields.fakeApi.gets==3);
 v.fitness.stepsValue=40;v.fakeMode=Toybox.System.DISPLAY_MODE_HIGH_POWER;v.syncDisplayMode(v.fakeMode);v.refreshFitness();
 Test.assert(v.values["steps"]==40&&v.selectedFields.fakeApi.gets==6&&v.fitness.activityCalls==2);v.fakeMode=Toybox.System.DISPLAY_MODE_LOW_POWER;v.onEnterSleep();
 Test.assert(v.values["steps"]==40&&!v.selectedFields.active()&&v.fitnessTimer==null);return true;
}
(:test,:typecheck(false)) function peerLifetimeControls(logger){
 Test.assert(serviceRetryConsumesVolatileLease(logger));Test.assert(selectedFieldsStoppedReadRetainsSnapshot(logger));Test.assert(coldLowAcquiresOneFieldSnapshot(logger));Test.assert(campaignBudgetExcludesControlGaps(logger));
 logger.debug("PEER_LIFETIME controls=4 service_lease=true frozen_fields=true cold_low_once=true productive_budget=true");return true;
}
(:test,:typecheck(false)) function peerAffectedProperties(logger){
 Test.assert(generatedServiceFailure(logger));Test.assert(generatedSelectedFields(logger));Test.assert(generatedViewLifecycle(logger));Test.assert(generatedSourceSwitch(logger));Test.assert(generatedForegroundDelivery(logger));
 logger.debug("PEER_AFFECTED families=5 service_fields_view_source_foreground=true");return true;
}

// Reproduce the cumulative fake-OS history leak past the observed 658-seed
// prefix, then exercise the same callback/timer/loader ownership closure.
(:test,:typecheck(false)) function peerFakeHistoryControls(logger){
 var temporal=runGeneratedTemporalService(1600001,768);
 var view=runGeneratedViewLifecycle(1600001,32);
 var foreground=runGeneratedForegroundDelivery(1600001,32);
 var source=runGeneratedSourceSwitch(1600001,32);
 var art=runGeneratedArtLease(1600001,32);
 var failure=runGeneratedServiceFailure(1600001,32);
 logger.debug("PBT_FAKE_HISTORY temporal_seeds=768 other_family_seeds=32 temporal="+temporal+" view="+view+" foreground="+foreground+" source="+source+" art="+art+" service="+failure+" after_each=true terminal_checked=true");return true;
}
