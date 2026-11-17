import Toybox.Lang;
import Toybox.Test;
import Toybox.System;

// Test-only coverage counters are isolated per simulator worker.
(:typecheck(false)) module PbtMetrics {var assertions=0;var skipped=0;var coverage={};}
(:typecheck(false)) function recordCoverage(values){var keys=values.keys();for(var i=0;i<keys.size();i+=1){var k=keys[i];if(!PbtMetrics.coverage.hasKey(k)){PbtMetrics.coverage[k]=0;}PbtMetrics.coverage[k]+=values[k];}}

// Small reproducible PRNG; business time is represented only by generated events.
(:test,:typecheck(false)) class OwnerRandom {
    var value;
    function initialize(seed){value=seed%1000003;}
    function draw(n){value=(value*109+1021)%1000003;return value%n;}
}
(:test,:typecheck(false)) function ownerCheck(ok,kind,seed,index,trace,expected,actual){
    PbtMetrics.assertions+=1;if(!ok){System.println("STM_FAIL owner="+kind+" seed="+seed+" index="+index+" trace="+trace+" expected="+expected+" actual="+actual);Test.assert(false);}
}

// The model is independent scalar data; every event calls the real owner.
(:typecheck(false)) function runGeneratedDisplayOwners(firstSeed,seedCount){
    var count=0;
    for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){
        var random=new OwnerRandom(seed);var sut=new NativeDisplayLifecycle();var state=0;var sleeping=false;var minute=null;var trace=[];
        var coverage={"show_applied"=>0,"show_no"=>0,"hide_applied"=>0,"hide_no"=>0,"active_applied"=>0,"mode_hidden_no"=>0,"sleep_applied"=>0,"sleep_no"=>0,"wake_applied"=>0,"wake_no"=>0,"frame_applied"=>0,"invalidate_applied"=>0};
        var prefix=[0,0,4,5,2,2,3,3,1,1,4,6,7];var events=prefix.size()+12+random.draw(37);
        for(var i=0;i<events;i+=1){var event=0;if(i<prefix.size()){event=prefix[i];}else{event=random.draw(8);}var stamp=100+random.draw(4);trace.add([event,stamp]);
            if(event==0){var applied=state==0;if(applied){coverage["show_applied"]+=1;state=1;minute=null;}else{coverage["show_no"]+=1;}ownerCheck(sut.show()==applied,"display-show",seed,i,trace,applied,sut.state);}
            else if(event==1){var applied=state!=0;if(applied){coverage["hide_applied"]+=1;state=0;minute=null;}else{coverage["hide_no"]+=1;}ownerCheck(sut.hide()==applied,"display-hide",seed,i,trace,applied,sut.state);}
            else if(event==2){var applied=!sleeping;if(applied){coverage["sleep_applied"]+=1;}else{coverage["sleep_no"]+=1;}sleeping=true;ownerCheck(sut.sleep()==applied,"display-sleep",seed,i,trace,applied,sut.sleeping);}
            else if(event==3){var applied=sleeping;if(applied){coverage["wake_applied"]+=1;}else{coverage["wake_no"]+=1;}sleeping=false;ownerCheck(sut.wake()==applied,"display-wake",seed,i,trace,applied,sut.sleeping);}
            else if(event==4){if(state==0){coverage["mode_hidden_no"]+=1;}else if(state!=2){coverage["active_applied"]+=1;}if(state!=0){state=2;}sut.setMode(1);}
            else if(event==5){if(state!=0){state=1;}sut.setMode(0);}
            else if(event==6){coverage["frame_applied"]+=1;minute=stamp;sut.framePainted(stamp.toLong());}
            else{if(minute!=null){coverage["invalidate_applied"]+=1;}minute=null;sut.invalidateFrame();}
            var actual=[sut.state,sut.sleeping,sut.frameMinute];var expected=[state,sleeping,minute];
            ownerCheck(sut.state==state&&sut.sleeping==sleeping&&sut.frameMinute==minute,"display",seed,i,trace,expected,actual);
            ownerCheck(sut.shown()==(state!=0)&&sut.awake()==!sleeping&&((sut.mode()==1&&state==2)||(sut.mode()==0&&state!=2))&&sut.frameDue(stamp.toLong())==(minute==null||minute!=stamp),"display-effects",seed,i,trace,expected,actual);count+=1;
        }
        ownerCheck(sut.state==state&&sut.sleeping==sleeping&&sut.frameMinute==minute,"display-end",seed,events,trace,[state,sleeping,minute],[sut.state,sut.sleeping,sut.frameMinute]);
        var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"display-coverage",seed,events,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);
    }
    return count;
}
(:test,:typecheck(false)) function generatedDisplayOwners(logger){var count=runGeneratedDisplayOwners(1,64);logger.debug("GENERATED_DISPLAY seeds=64 events="+count+" variable_length=true after_each=true end=true");return true;
}

(:test,:typecheck(false)) class OwnerRequestFake {
    var flight;var delivered=0;
    function initialize(){flight=new NativeRequestLifecycle();}
    function receive(code,data){if(flight.consume()){delivered+=1;}}
}
(:typecheck(false)) function runGeneratedRequestOwners(firstSeed,seedCount){
    var count=0;
    for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){
        var random=new OwnerRandom(seed);var owner=new OwnerRequestFake();var state=0;var serial=0;var delivered=0;var callbacks=[];var ids=[];var trace=[];
        var coverage={"start_applied"=>0,"start_no"=>0,"callback_applied"=>0,"callback_no"=>0,"reset_applied"=>0,"session_no"=>0,"finish_cancel"=>0,"finish_idle"=>0};
        var prefix=[0,2,0,1,1,0,3,1,2,3,2,0,1,3];var events=prefix.size()+12+random.draw(37);
        for(var i=0;i<events;i+=1){var event=0;if(i<prefix.size()){event=prefix[i];}else{event=random.draw(4);}var which=0;if(callbacks.size()>0&&i>=prefix.size()){which=random.draw(callbacks.size());}trace.add([event,which]);
            if(event==0){var id=owner.flight.begin();if(state==0){coverage["start_applied"]+=1;serial+=1;state=1;ids.add(serial);callbacks.add(new NativeRequestCallback(owner,id,owner.method(:receive)));}else{coverage["start_no"]+=1;ownerCheck(id==null,"request-start",seed,i,trace,"null",id);}}
            else if(event==1){if(callbacks.size()>0){if(state==1&&ids[which]==serial){coverage["callback_applied"]+=1;state=0;delivered+=1;}else{coverage["callback_no"]+=1;}callbacks[which].deliver(200,null);}}
            else if(event==2){var allowed=state!=1;if(allowed){coverage["reset_applied"]+=1;serial+=1;state=0;}else{coverage["session_no"]+=1;}var action=owner.flight.startSession(false);var expectedAction=0;if(allowed){expectedAction=1;}ownerCheck(action==expectedAction,"request-session",seed,i,trace,expectedAction,action);}
            else{var expectedCancel=state==1;if(expectedCancel){coverage["finish_cancel"]+=1;}else{coverage["finish_idle"]+=1;}state=2;serial+=1;var cancelled=owner.flight.finish();ownerCheck(cancelled==expectedCancel,"request-cancel",seed,i,trace,expectedCancel,cancelled);}
            var expected=[state,serial,delivered];var actual=[owner.flight.state,owner.flight.serial,owner.delivered];
            ownerCheck(state==owner.flight.state&&serial==owner.flight.serial&&delivered==owner.delivered&&owner.flight.canStart()==(state==0)&&owner.flight.finished()==(state==2),"request",seed,i,trace,expected,actual);count+=1;
        }
        ownerCheck(state==owner.flight.state&&serial==owner.flight.serial&&delivered==owner.delivered,"request-end",seed,events,trace,[state,serial,delivered],[owner.flight.state,owner.flight.serial,owner.delivered]);
        var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"request-coverage",seed,events,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);
    }
    return count;
}
(:test,:typecheck(false)) function generatedRequestOwners(logger){var n=runGeneratedRequestOwners(1,64);logger.debug("GENERATED_REQUESTOWNERS seeds=64 events="+n+" after_each=true end=true");return true;}


(:typecheck(false)) function runGeneratedSceneOwners(firstSeed,seedCount){
 var count=0;
 for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){
  var rng=new OwnerRandom(seed);var sut=new SceneLifecycle();var generation=0;var presentation=0;var job=-1;var jobSerial=0;var token=-1;var tokens=[];var trace=[];
  var coverage={"request_applied"=>0,"request_no"=>0,"begin_applied"=>0,"fail_applied"=>0,"cancel_applied"=>0,"complete_applied"=>0,"complete_no"=>0,"replace_applied"=>0,"ready_applied"=>0};
  // Request/begin/failure/retry/cancel/late/completion are causal witnesses;
  // the following tail chooses arbitrary event order, payload and length.
  var prefix=[[0,1],[0,1],[1,0],[3,0],[0,1],[0,2],[1,0],[4,0],[2,0],[0,3],[1,0],[2,2],[5,0],[6,0]];
  var events=prefix.size()+12+rng.draw(37);
  for(var i=0;i<events;i+=1){var e=0;var arg=0;if(i<prefix.size()){e=prefix[i][0];arg=prefix[i][1];}else{e=rng.draw(7);arg=rng.draw(4)+1;}trace.add([e,arg]);
   if(e==0){var accept=job<0||(job==2&&arg>jobSerial);if(accept){generation+=1;job=0;jobSerial=arg;token=generation;presentation=1;coverage["request_applied"]+=1;}else{coverage["request_no"]+=1;}ownerCheck(sut.request(arg)==accept,"scene-request",seed,i,trace,accept,sut.presentationState);}
   else if(e==1){var expected=null;if(job==0){job=1;expected=token;tokens.add(token);coverage["begin_applied"]+=1;}var got=sut.begin();ownerCheck(got==expected,"scene-begin",seed,i,trace,expected,got);}
   else if(e==2){var candidate=-1;if(tokens.size()>0){var ix=arg%tokens.size();candidate=tokens[ix];}var accepted=job==1&&candidate==token&&candidate==generation;if(accepted){job=-1;presentation=2;coverage["complete_applied"]+=1;}else{coverage["complete_no"]+=1;}ownerCheck(sut.complete(candidate)==accepted,"scene-complete",seed,i,trace,accepted,sut.presentationState);}
   else if(e==3){var candidate=-1;if(tokens.size()>0){candidate=tokens[tokens.size()-1];}if(job==1&&candidate==token&&candidate==generation){job=2;presentation=0;coverage["fail_applied"]+=1;}sut.fail(candidate);}
   else if(e==4){job=-1;generation+=1;presentation=0;coverage["cancel_applied"]+=1;sut.cancel();}
   else if(e==5){job=-1;generation+=1;presentation=0;coverage["replace_applied"]+=1;sut.replace();}
   else{job=-1;presentation=2;coverage["ready_applied"]+=1;sut.bindReady();}
   var actualJob=-1;var actualSerial=0;var actualToken=-1;if(sut.job!=null){actualJob=sut.job.state;actualSerial=sut.job.batchSerial;actualToken=sut.job.token;}
   ownerCheck(sut.generation==generation&&sut.presentationState==presentation&&actualJob==job&&(job<0||(actualSerial==jobSerial&&actualToken==token))&&sut.pending()==(presentation==1&&job>=0),"scene",seed,i,trace,[generation,presentation,job,jobSerial,token],[sut.generation,sut.presentationState,actualJob,actualSerial,actualToken]);count+=1;
  }
  ownerCheck(sut.generation==generation&&sut.presentationState==presentation,"scene-end",seed,events,trace,[generation,presentation],[sut.generation,sut.presentationState]);var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"scene-coverage",seed,events,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);
 }
 return count;
}
(:test,:typecheck(false)) function generatedSceneOwners(logger){var n=runGeneratedSceneOwners(1,64);logger.debug("GENERATED_SCENEOWNERS seeds=64 events="+n+" after_each=true end=true");return true;}


// A completion from one finished job must never finish a later job.
(:test,:typecheck(false)) function sceneOldCompletionCannotFinishNewJob(logger){
 var sut=new SceneLifecycle();Test.assert(sut.request(1));var old=sut.begin();Test.assert(old!=null);Test.assert(sut.complete(old));
 Test.assert(sut.request(2));var current=sut.begin();Test.assert(current!=null);
 Test.assertMessage(!sut.complete(old),"old completion must not publish the new job");
 Test.assertMessage(sut.pending(),"new job must remain pending after an old completion");
 Test.assert(sut.complete(current));return true;
}

(:test,:typecheck(false)) function generatedCoreShort(logger){
 Test.assert(generatedDisplayOwners(logger));
 Test.assert(generatedRequestOwners(logger));
 Test.assert(generatedSceneOwners(logger));
 Test.assert(sceneOldCompletionCannotFinishNewJob(logger));
 logger.debug("CORE_SHORT owner_sets=3 deterministic_red_regression=true");return true;
}

(:test,:typecheck(false)) class PbtMemoryStore {
 var values={};var reads=0;var writes=0;var fail=0;var failSlotRead=false;var slots=0;var pointers=0;var controls=0;var attempts=0;
 function read(key){reads+=1;if(failSlotRead&&(key.find("sf.snapshot.0:")==0||key.find("sf.snapshot.1:")==0)){throw new Lang.InvalidValueException("injected slot read failure");}return values[key];}
 function write(key,value){
  writes+=1;var slot=key.find("sf.snapshot.0:")==0||key.find("sf.snapshot.1:")==0;var pointer=key.find("sf.snapshot.active:")==0;
  if((fail==1&&slot)||(fail==2&&pointer)||(fail==3&&key.equals("sf.reminder.attempt"))||(fail==4&&key.find("sf.attempt:")==0&&value["success"]==true)){throw new Lang.InvalidValueException("injected storage failure");}
  if(slot){slots+=1;}if(pointer){pointers+=1;}if(key.equals("sf.reminder.control")){controls+=1;}if(key.equals("sf.reminder.attempt")){attempts+=1;}values[key]=value;
 }
 function remove(key){writes+=1;values.remove(key);}
}
// All external boundaries are overridden before onTemporalEvent runs.
(:test,:typecheck(false)) class PbtTemporalService extends FeedService {
 var fakeStore;var fakeUtc=1794818604l;var fakeMillis=0;var connected=true;var sent=[];var arms=0;var registrations=0;var reminderCalls=0;var exits=0;var cancellations=0;var forbidden=0;var logs=0;var testUrl="https://pbt.invalid";var sendFails=false;var sends=0;var deliveryFails=false;var deliveries=[];
 function initialize(){FeedService.initialize();fakeStore=new PbtMemoryStore();}
 function createTransfer() as NativeTransfer {return new NativeTransfer(testUrl,fakeStore);}
 function nowMillis() as Number {return fakeMillis;}
 function nowUtc() as Long {return fakeUtc;}
 function phoneConnected() as Boolean {return connected;}
 function log(message as String) as Void {logs+=1;}
 function traceEntry() as Void {}
 function registerEntryWake() as Void {registrations+=1;}
 function stopEmptySource() as Void {exits+=1;}
 function createBatch(source as NativeTransfer) as NativeBatch or Null {return null;}
 function wakeReminders(source as NativeTransfer,now as Long) as Void {reminderCalls+=1;}
 function armTransfer(source as NativeTransfer,now as Long) as Void {arms+=1;}
 function sendSnapshot(callback as Method) as Void {sends+=1;if(sendFails){throw new Lang.InvalidValueException("injected send failure");}sent.add(callback);}
 function sendRequest(path as String,callback as Method) as Void {forbidden+=1;}
 // The fake OS retains old Methods for late-callback events within a trace.
 // Release that test-owned registry only after the terminal/end assertions.
 function releaseHistory(){sent=[];deliveries=[];}
 function cancelOutstanding() as Void {cancellations+=1;}
 function deliverBackground(data) as Void {exits+=1;if(deliveryFails&&data instanceof Dictionary&&data.hasKey("volatileSnapshot")){throw new Lang.InvalidValueException("injected delivery failure");}deliveries.add(data);}
}
(:test,:typecheck(false)) function duplicateTemporalEntryDoesNotRestartInFlight(logger){
 var service=new PbtTemporalService();service.onTemporalEvent();Test.assertEqual(service.sent.size(),1);var registrations=service.registrations;var writes=service.fakeStore.writes;
 service.onTemporalEvent();
 Test.assertMessage(service.sent.size()==1,"duplicate temporal entry must not create a second concurrent request");
 Test.assertEqual(service.registrations,registrations);Test.assertEqual(service.fakeStore.writes,writes);Test.assertEqual(service.forbidden,0);return true;
}

// Values are captured Taiyuan facts. Sequence/generation and target variation
// are test event payloads; no expected value is read from production state.
(:test,:typecheck(false)) function pbtSnapshot(generation,target){
 var policy={"normal_interval_seconds"=>3600,"near_interval_seconds"=>900,"fast_interval_seconds"=>null,"stale_cycles"=>3};
 var row=["ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60","Long March 2D","China Aerospace Science and Technology Corporation","CASC","Unknown","CN · Taiyuan Satellite Launch Center","ll2:configuration:17","ll2:organization:88","ll2:site:25",["111.589567","38.863128"],null,"window",null,null,1795041780l,1794812997l,policy,false,false,false,target,false];
 return [1,{"generation"=>generation,"instance"=>"40655f8a46c4c47ecb6f6d4a8608bde8396c6c440807e09d962b1f7fde006204","selectionValidatedUtc"=>1794812997l},policy,row,[],[],null];
}
(:test,:typecheck(false)) class StorageTrace {
 var store;var owner;var accepted=null;var slots=0;var pointers=0;var phase=0;var trace=[];var coverage={"commit_applied"=>0,"slot_no"=>0,"pointer_no"=>0,"reopen_no"=>0,"invalid_no"=>0};
 function initialize(){store=new PbtMemoryStore();owner=new NativeTrustedStore(store,"https://pbt.invalid");}
 function step(e,generation,seed,i){
  var target=1795042200l+generation*60;trace.add([e,generation]);
  if(e==0){Test.assert(owner.save(pbtSnapshot(generation,target)));accepted=target;slots+=1;pointers+=1;phase=3;coverage["commit_applied"]+=1;}
  else if(e==1||e==2){if(e==1){store.fail=1;}else{store.fail=2;}var caught=false;try{owner.save(pbtSnapshot(generation,target));}catch(error){caught=true;}store.fail=0;ownerCheck(caught,"storage-failure",seed,i,trace,true,caught);if(e==1){phase=1;coverage["slot_no"]+=1;}else{phase=2;slots+=1;coverage["pointer_no"]+=1;}}
  else if(e==3){owner=new NativeTrustedStore(store,"https://pbt.invalid");phase=0;coverage["reopen_no"]+=1;}
  else{ownerCheck(!owner.save([1]),"storage-invalid",seed,i,trace,false,true);coverage["invalid_no"]+=1;}
  verify(seed,i);
 }
 function verify(seed,i){
  var actual=owner.load();var observed=null;if(actual!=null){observed=actual[3][20];}
  ownerCheck(observed==accepted&&store.slots==slots&&store.pointers==pointers&&owner.phase==phase,"storage",seed,i,trace,[accepted,slots,pointers,phase],[observed,store.slots,store.pointers,owner.phase]);
  if(actual!=null){ownerCheck(actual[3][9][0].equals("111.589567")&&actual[3][9][1].equals("38.863128"),"storage-point",seed,i,trace,"Taiyuan",actual[3][9]);}
 }
 function final(seed,n){verify(seed,n);var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"storage-coverage",seed,n,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);}
}
(:typecheck(false)) function runGeneratedStorageOwners(firstSeed,seedCount){
 var count=0;
 for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){
  var rng=new OwnerRandom(seed);var run=new StorageTrace();var prefix=[0,3,1,3,2,3,0,4];var events=prefix.size()+12+rng.draw(37);
  for(var i=0;i<events;i+=1){var e=0;if(i<prefix.size()){e=prefix[i];}else{e=rng.draw(5);}run.step(e,seed*100+i+1,seed,i);count+=1;}
  run.final(seed,events);
 }
 return count;
}
(:test,:typecheck(false)) function generatedStorageOwners(logger){var n=runGeneratedStorageOwners(1,64);logger.debug("GENERATED_STORAGEOWNERS seeds=64 events="+n+" after_each=true end=true");return true;}


// Real FeedService and NativeTransfer with all service/time/storage boundaries
// substituted before entry. Model counters are derived only from event inputs.
(:typecheck(false)) function runGeneratedTemporalService(firstSeed,seedCount){
 var total=0;
 for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){
  var rng=new OwnerRandom(seed);var s=new PbtTemporalService();var now=1794818604l;var millis=0;var connected=true;var started=0;var last=null;var success=false;var future=null;
  var state=0;var serial=0;var sentIds=[];var writes=0;var reads=0;var slots=0;var pointers=0;var arms=0;var registrations=0;var reminders=0;var exits=0;var cancellations=0;var logs=0;var accepted=null;var trace=[];
  var coverage={"entry_applied"=>0,"entry_no"=>0,"healthy_no"=>0,"reply_success"=>0,"reply_failure"=>0,"reply_no"=>0,"timeout_applied"=>0,"timeout_entry"=>0,"cancel_applied"=>0,"session_after_terminal"=>0};
  var prefix=[[0,0],[0,0],[3,22000],[0,0],[1,0],[0,0],[3,22000],[1,1],[0,0],[1,0],[1,2],[0,0],[4,3600],[0,0],[2,0],[1,3],[0,0],[5,4]];
  var events=prefix.size()+12+rng.draw(25);
  for(var i=0;i<events;i+=1){var event=0;var arg=0;if(i<prefix.size()){event=prefix[i][0];arg=prefix[i][1];}else{event=rng.draw(7);arg=rng.draw(4);if(event==3){arg=arg*11000;}if(event==4){arg=arg*300;}if((event==1||event==5)&&sentIds.size()>0){arg=rng.draw(sentIds.size());}}trace.add([event,arg]);
   if(event==0){
    if(state==1){if(millis-started>=22000){coverage["timeout_entry"]+=1;state=2;serial+=1;cancellations+=1;arms+=1;exits+=1;}else{coverage["entry_no"]+=1;}}
    else{
     if(state==2){coverage["session_after_terminal"]+=1;}serial+=1;state=0;started=millis;registrations+=1;reminders+=1;reads+=1;
     var due=false;if(last==null||now<last){due=true;}else{reads+=2;if(success&&future!=null&&future>now){var next=last+3600;if(future<next){next=future;}due=now>=next;}else{due=connected||now>=last+300;}}
     if(due){last=now;success=false;writes+=1;arms+=1;if(connected){serial+=1;state=1;sentIds.add(serial);coverage["entry_applied"]+=1;}else{state=2;serial+=1;arms+=1;exits+=1;}}
     else{coverage["healthy_no"]+=1;state=2;serial+=1;arms+=1;exits+=1;}
    }
    s.onTemporalEvent();
   }else if(event==1||event==5){
    if(sentIds.size()>0){var index=arg%sentIds.size();var current=state==1&&sentIds[index]==serial;var code=200;if(event==5){code=503;}
     if(current){state=0;if(millis-started>=22000){coverage["timeout_applied"]+=1;}else if(code==200){reads+=1;writes+=4;slots+=1;pointers+=1;success=true;future=1795041780l;accepted=1795042200l+seed*60;logs+=1;coverage["reply_success"]+=1;}else{coverage["reply_failure"]+=1;}state=2;serial+=1;arms+=1;exits+=1;}
     else{coverage["reply_no"]+=1;}
     if(code==200){s.sent[index].invoke(200,{"data"=>pbtSnapshot(seed,1795042200l+seed*60)});}else{s.sent[index].invoke(503,null);}
    }
   }else if(event==2){if(state!=2){if(state==1){cancellations+=1;coverage["cancel_applied"]+=1;}state=2;serial+=1;arms+=1;exits+=1;}s.finish();}
   else if(event==3){millis+=arg;s.fakeMillis=millis;}
   else if(event==4){now+=arg;millis+=arg*1000;s.fakeUtc=now;s.fakeMillis=millis;}
   else{connected=!connected;s.connected=connected;}
   var actual=[s.flight.state,s.flight.serial,s.sent.size(),s.fakeStore.reads,s.fakeStore.writes,s.fakeStore.slots,s.fakeStore.pointers,s.arms,s.registrations,s.reminderCalls,s.exits,s.cancellations,s.forbidden,s.logs];
   var expected=[state,serial,sentIds.size(),reads,writes,slots,pointers,arms,registrations,reminders,exits,cancellations,0,logs];
   ownerCheck(s.flight.state==state&&s.flight.serial==serial&&s.sent.size()==sentIds.size()&&s.fakeStore.reads==reads&&s.fakeStore.writes==writes&&s.fakeStore.slots==slots&&s.fakeStore.pointers==pointers&&s.arms==arms&&s.registrations==registrations&&s.reminderCalls==reminders&&s.exits==exits&&s.cancellations==cancellations&&s.forbidden==0&&s.logs==logs,"temporal",seed,i,trace,expected,actual);total+=1;
   var marker=s.fakeStore.values["sf.snapshot.active:https://pbt.invalid"];var observed=null;if(marker!=null){var saved=s.fakeStore.values["sf.snapshot."+marker["slot"]+":https://pbt.invalid"];observed=saved[3][20];ownerCheck(saved[3][9][0].equals("111.589567")&&saved[3][9][1].equals("38.863128"),"temporal-point",seed,i,trace,"Taiyuan",saved[3][9]);}
   ownerCheck(observed==accepted,"temporal-facts",seed,i,trace,accepted,observed);
  }
  var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"temporal-coverage",seed,events,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);
  ownerCheck(s.flight.state==state&&s.fakeStore.pointers==pointers&&s.forbidden==0,"temporal-end",seed,events,trace,[state,pointers,0],[s.flight.state,s.fakeStore.pointers,s.forbidden]);
  trace.add([2,0]);if(state!=2){if(state==1){cancellations+=1;}state=2;serial+=1;arms+=1;exits+=1;}s.finish();total+=1;
  ownerCheck(s.flight.state==2&&s.flight.serial==serial&&s.cancellations==cancellations&&s.arms==arms&&s.exits==exits,"temporal-teardown",seed,events,trace,[2,serial,cancellations,arms,exits],[s.flight.state,s.flight.serial,s.cancellations,s.arms,s.exits]);
  s.releaseHistory();
 }
 return total;
}
(:test,:typecheck(false)) function generatedTemporalService(logger){var n=runGeneratedTemporalService(1,32);logger.debug("GENERATED_TEMPORALSERVICE seeds=32 events="+n+" after_each=true end=true");return true;}


(:test,:typecheck(false)) function generatedIntegrationShort(logger){
 Test.assert(generatedCoreShort(logger));
 Test.assert(duplicateTemporalEntryDoesNotRestartInFlight(logger));
 Test.assert(generatedStorageOwners(logger));
 Test.assert(generatedTemporalService(logger));
 logger.debug("INTEGRATION_SHORT all_selected=true");return true;
}

(:test,:typecheck(false)) function storageSnapshotOnly(logger){
 logger.debug("SNAPSHOT_BUILD_START");var value=pbtSnapshot(1,1795042260l);logger.debug("SNAPSHOT_BUILT");Test.assertEqual(value[3][20],1795042260l);return true;
}
(:test,:typecheck(false)) function storageOneSave(logger){
 logger.debug("STORAGE_SETUP_START");var s=new PbtMemoryStore();var owner=new NativeTrustedStore(s,"https://pbt.invalid");var value=pbtSnapshot(1,1795042260l);logger.debug("STORAGE_SAVE_START");Test.assert(owner.save(value));logger.debug("STORAGE_SAVED");return true;
}

// Cache and map inputs are independent event payloads; no expected publisher,
// target, map state or point is read back from the SUT to construct the model.
(:test,:typecheck(false)) class CacheMapTrace {
 var store;var cache;var map;var current=0;var pending=0;var ram=0;var shown=false;var ready=false;var failed=false;var identity=false;var trace=[];
 var coverage={"queue_applied"=>0,"queue_no"=>0,"delivery_applied"=>0,"delivery_no"=>0,"volatile_no"=>0,"durable_no"=>0,"source_applied"=>0,"map_error"=>0,"map_restored"=>0};
 function initialize(){store=new PbtMemoryStore();cache=new NativeCache("https://pbt.invalid",store);map=new MapPresentation();}
 function packet(n){return new NativeTrustedPacket(pbtSnapshot(n,1795042200l+n*60));}
 function bind(){if(current==0){map.bind(null);}else{map.bind(cache.packet.presentation);}if((current!=0)!=identity){failed=false;identity=current!=0;}}
 function step(e,n,seed,i){
  trace.add([e,n]);
  if(e==0){var allowed=n>current&&(pending==0||n>pending);if(allowed){pending=n;coverage["queue_applied"]+=1;}else{coverage["queue_no"]+=1;}ownerCheck(cache.queueVolatile(pbtSnapshot(n,1795042200l+n*60))==allowed,"cache-queue",seed,i,trace,allowed,n);}
  else if(e==1){var deliver=pending>current;var prior=pending;pending=0;var value=cache.takeVolatile();ownerCheck((value!=null)==deliver,"cache-take",seed,i,trace,deliver,value!=null);if(deliver){current=prior;ram=1;Test.assert(cache.acceptVolatile(new NativeTrustedPacket(value)));bind();coverage["delivery_applied"]+=1;}else{coverage["delivery_no"]+=1;}}
  else if(e==2){var accept=current==0||n>current;if(accept){current=n;ram=1;}else{coverage["volatile_no"]+=1;}ownerCheck(cache.acceptVolatile(packet(n))==accept,"cache-volatile",seed,i,trace,accept,n);if(accept){bind();}}
  else if(e==3){var accept=ram!=1||current==0||n>=current;if(accept){current=n;ram=2;}else{coverage["durable_no"]+=1;}ownerCheck(cache.acceptDurable(packet(n))==accept,"cache-durable",seed,i,trace,accept,n);if(accept){bind();}}
  else if(e==4){cache=new NativeCache("https://other.invalid",store);current=0;pending=0;ram=0;bind();coverage["source_applied"]+=1;}
  else if(e==5){shown=!shown;}
  else if(e==6){ready=!ready;}
  else if(e==7){map.failure();failed=true;coverage["map_error"]+=1;}
  else{map.restored();failed=false;coverage["map_restored"]+=1;}
  verify(seed,i);
 }
 function verify(seed,i){
  var actual=cache.packet;var actualGeneration=0;var target=null;var point=null;if(actual!=null){actualGeneration=actual.document["publisher"]["generation"];target=actual.presentation.displayTarget;point=actual.presentation.pointText;}
  var expectedTarget=null;if(current!=0){expectedTarget=1795042200l+current*60;}
  ownerCheck(actualGeneration==current&&cache.ramState==ram&&((cache.pendingVolatile==null&&pending==0)||(cache.pendingVolatile!=null&&pending!=0&&cache.pendingVolatile[1]["generation"]==pending))&&target==expectedTarget&&store.reads==0&&store.writes==0,"cache",seed,i,trace,[current,pending,ram,expectedTarget,0,0],[actualGeneration,cache.pendingVolatile,cache.ramState,target,store.reads,store.writes]);
  var expectedMode=0;if(shown){expectedMode=1;if(ready&&!failed&&current!=0){expectedMode=2;}}
  ownerCheck(map.mode(shown,ready)==expectedMode&&map.pointVisible(shown)==(shown&&current!=0),"map-mode",seed,i,trace,[expectedMode,shown&&current!=0],[map.mode(shown,ready),map.pointVisible(shown)]);
  if(current!=0){ownerCheck(point[0].equals("111.589567")&&point[1].equals("38.863128")&&map.identity.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"),"map-point",seed,i,trace,"Taiyuan",point);}
 }
 function final(seed,n){verify(seed,n);var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"cache-map-coverage",seed,n,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);}
}
(:typecheck(false)) function runGeneratedCacheMapOwners(firstSeed,seedCount){
 var count=0;
 for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){var rng=new OwnerRandom(seed);var run=new CacheMapTrace();var prefix=[[0,2],[0,1],[1,0],[1,0],[2,1],[3,1],[0,3],[1,0],[7,0],[8,0],[5,0],[6,0],[4,0]];var events=prefix.size()+12+rng.draw(37);
  for(var i=0;i<events;i+=1){var e=0;var n=0;if(i<prefix.size()){e=prefix[i][0];n=prefix[i][1];}else{e=rng.draw(9);n=rng.draw(4)+1;}run.step(e,n,seed,i);count+=1;}
  run.final(seed,events);
 }
 return count;
}
(:test,:typecheck(false)) function generatedCacheMapOwners(logger){var n=runGeneratedCacheMapOwners(1,64);logger.debug("GENERATED_CACHEMAPOWNERS seeds=64 events="+n+" after_each=true end=true");return true;}


(:test,:typecheck(false)) class PbtTimer extends Toybox.Timer.Timer {
 var starts=0;var stops=0;var fires=0;var callback=null;var period=0;var repeating=false;
 function initialize(){}
 function start(cb as Method,ms as Number,repeat as Boolean) as Void {starts+=1;callback=cb;period=ms;repeating=repeat;}
 function stop() as Void {stops+=1;callback=null;}
 function fire(){if(callback==null){return false;}var cb=callback;if(!repeating){callback=null;}fires+=1;cb.invoke();return true;}
}
(:test,:typecheck(false)) class PbtTimerReceiver {var calls=0;function fire(){calls+=1;}}
(:test,:typecheck(false)) function pbtTimerControl(logger){
 var receiver=new PbtTimerReceiver();var timer=new PbtTimer();timer.start(receiver.method(:fire),50,false);Test.assertEqual(timer.starts,1);Test.assertEqual(receiver.calls,0);timer.callback.invoke();Test.assertEqual(receiver.calls,1);timer.stop();Test.assertEqual(timer.stops,1);Test.assert(timer.callback==null);return true;
}

(:test,:typecheck(false)) class PbtClock extends WatchClock {
 var now=1794818604;function initialize(){WatchClock.initialize();}
 function utcSeconds() as Number {return now;}
 function localTimeText() as String {return "08:25";}
 function localCalendar() as Array<Number> {return [3,17,11];}
}
(:test,:typecheck(false)) class PbtGraphics extends Toybox.Graphics.Dc {function initialize(){}}
(:test,:typecheck(false)) class PbtLocale extends LocalePresentation {
 var restores=0;var suspends=0;function initialize(){}
 function restore(requested){restores+=1;locale=requested;}
 function suspend(){suspends+=1;locale="";}
}
(:test,:typecheck(false)) class PbtView extends SpaceFoxView {
 var fakeMode=Toybox.System.DISPLAY_MODE_HIGH_POWER;var timers=[];var updates=0;var lowFrames=0;var fallbackFrames=0;var layouts=0;var fitnessCalls=0;var animationStarts=0;var animationStops=0;var modeLogs=0;var lowSnapshots=0;var clock;
 function initialize(){clock=new PbtClock();SpaceFoxView.initialize(clock,new ScheduleState(null,"empty"));}
 function createPresentation() as LocalePresentation {return new PbtLocale();}
 function deviceMode() as Toybox.System.DisplayMode {return fakeMode;}
 function requestFrame() as Void {updates+=1;}
 function logMode() as Void {modeLogs+=1;}
 function newViewTimer() as Toybox.Timer.Timer {var t=new PbtTimer();timers.add(t);return t;}
 function onLayout(dc as Toybox.Graphics.Dc) as Void {layouts+=1;}
 function refreshFitnessWork() as Void {fitnessCalls+=1;selectedFields.claimInitialSnapshot();}
 function readFitnessSnapshot(now as Number or Long) as Void {lowSnapshots+=1;}
 function drawPendingLow(dc){lowFrames+=1;markLowFramePainted((clock.now/60).toLong());}
 function drawClockFallback(dc){fallbackFrames+=1;}
}
(:typecheck(false)) function pbtCheckViewReleased(view,seed,index,trace){
 for(var n=0;n<view.timers.size();n+=1){ownerCheck(view.timers[n].callback==null,"fake-timer-release",seed,index,trace,null,view.timers[n].callback);}
}
(:test,:typecheck(false)) function duplicateShowDoesNotScheduleAgain(logger){
 var view=new PbtView();view.onShow();var first=view.updates;view.onShow();
 Test.assertMessage(view.updates==first,"duplicate OS show must not issue an extra redraw");return true;
}
(:test,:typecheck(false)) function hiddenWakeDoesNotRequestFrame(logger){
 var view=new PbtView();view.onEnterSleep();var before=view.updates;view.onExitSleep();
 Test.assertMessage(view.updates==before,"wake while hidden must not request a visible frame");return true;
}

// The view's OS, timer, layout and paint ports are fake before the first event.
// The event model predicts scheduling/paint permission, not pixels.
(:test,:typecheck(false)) class ViewTrace {
 var view;var dc;var state=0;var sleeping=false;var high=true;var now=1794818604;var minute=null;var pending=false;var timer=-1;var timers=[];var updates=0;var modeLogs=0;var low=0;var fallback=0;var layouts=0;var fitness=0;var stops=0;var fires=0;var initialSnapshot=true;var lowSnapshots=0;var trace=[];
 var coverage={"show_applied"=>0,"show_no"=>0,"hide_applied"=>0,"hide_no"=>0,"sleep_applied"=>0,"sleep_no"=>0,"wake_applied"=>0,"wake_no"=>0,"hidden_wake_no"=>0,"low_paint"=>0,"same_minute_no"=>0,"hidden_frame_no"=>0,"timer_applied"=>0,"timer_no"=>0,"mode_change"=>0};
 function initialize(){view=new PbtView();dc=new PbtGraphics();}
 function stopTimer(){if(timer>=0){timers[timer]=0;timer=-1;stops+=1;}}
 function transition(next){if(state!=0&&state!=next){state=next;minute=null;updates+=1;modeLogs+=1;if(next==1){pending=false;stopTimer();}else{pending=true;}}}
 function sync(){var next=1;if(!sleeping&&high){next=2;}transition(next);}
 function step(e,arg,seed,i){
  trace.add([e,arg]);
  if(e==0){if(state==0){coverage["show_applied"]+=1;state=1;minute=null;sync();if(state==2){pending=true;updates+=1;}}else{coverage["show_no"]+=1;}view.onShow();}
  else if(e==1){if(state!=0){coverage["hide_applied"]+=1;state=0;minute=null;pending=false;stopTimer();}else{coverage["hide_no"]+=1;}view.onHide();}
  else if(e==2){if(!sleeping){coverage["sleep_applied"]+=1;sleeping=true;sync();}else{coverage["sleep_no"]+=1;}view.onEnterSleep();}
  else if(e==3){var wasSleeping=sleeping;var before=state;if(sleeping){coverage["wake_applied"]+=1;sleeping=false;}else{coverage["wake_no"]+=1;}sync();if(wasSleeping&&state!=0&&state==before){updates+=1;}else if(wasSleeping&&state==0){coverage["hidden_wake_no"]+=1;}view.onExitSleep();}
  else if(e==4){high=!high;if(high){view.fakeMode=Toybox.System.DISPLAY_MODE_HIGH_POWER;}else{view.fakeMode=Toybox.System.DISPLAY_MODE_LOW_POWER;}var before=state;sync();if(before!=state){coverage["mode_change"]+=1;}view.syncDisplayMode(view.fakeMode);}
  else if(e==5){now+=arg;view.clock.now=now;}
  else if(e==6){
   if(state==0){coverage["hidden_frame_no"]+=1;}
   else{sync();if(state==1){var m=(now/60).toLong();if(minute==m){coverage["same_minute_no"]+=1;}else{minute=m;low+=1;coverage["low_paint"]+=1;if(initialSnapshot){initialSnapshot=false;lowSnapshots+=1;minute=null;updates+=1;}}}
    else{layouts+=1;fallback+=1;if(pending&&timer<0){pending=false;timer=timers.size();timers.add(1);}}}
   view.onUpdate(dc);
  }else{var ix=0;if(timers.size()>0){ix=arg%timers.size();}var allowed=timers.size()>0&&timers[ix]==1;if(allowed){coverage["timer_applied"]+=1;timers[ix]=0;timer=-1;fires+=1;if(state==2&&high){fitness+=2;initialSnapshot=false;}}else{coverage["timer_no"]+=1;}var ran=false;if(view.timers.size()>0){ran=view.timers[ix].fire();}ownerCheck(ran==allowed,"view-timer",seed,i,trace,allowed,ran);}
  verify(seed,i);
 }
 function verify(seed,i){
  var actualStops=0;var actualFires=0;for(var n=0;n<view.timers.size();n+=1){actualStops+=view.timers[n].stops;actualFires+=view.timers[n].fires;}
  var expectedMode=0;if(state==2){expectedMode=1;}
  ownerCheck(view.visible()==(state!=0)&&view.displayMode()==expectedMode&&view.lastLowFrameMinute()==minute&&view.updates==updates&&view.modeLogs==modeLogs&&view.lowFrames==low&&view.fallbackFrames==fallback&&view.layouts==layouts&&view.fitnessCalls==fitness&&view.lowSnapshots==lowSnapshots&&view.timers.size()==timers.size()&&actualStops==stops&&actualFires==fires,"view",seed,i,trace,[state,sleeping,high,minute,updates,low,fallback,layouts,fitness,timers.size(),stops,fires],[view.visible(),view.displayMode(),view.lastLowFrameMinute(),view.updates,view.lowFrames,view.fallbackFrames,view.layouts,view.fitnessCalls,view.timers.size(),actualStops,actualFires]);
 }
 function final(seed,n){verify(seed,n);var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"view-coverage",seed,n,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);}
}
(:typecheck(false)) function runGeneratedViewLifecycle(firstSeed,seedCount){
 var total=0;
 for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){var rng=new OwnerRandom(seed);var run=new ViewTrace();var prefix=[[4,0],[0,0],[6,0],[6,0],[6,0],[1,0],[4,0],[0,0],[0,0],[6,0],[7,0],[7,0],[2,0],[2,0],[6,0],[6,0],[5,60],[6,0],[3,0],[3,0],[4,0],[4,0],[1,0],[1,0],[6,0],[2,0],[3,0]];var events=prefix.size()+12+rng.draw(25);
  for(var i=0;i<events;i+=1){var e=0;var arg=0;if(i<prefix.size()){e=prefix[i][0];arg=prefix[i][1];}else{e=rng.draw(8);arg=rng.draw(5)*30;}run.step(e,arg,seed,i);total+=1;}
  run.final(seed,events);run.step(1,0,seed,events);total+=1;pbtCheckViewReleased(run.view,seed,events,run.trace);
 }
 return total;
}
(:test,:typecheck(false)) function generatedViewLifecycle(logger){var n=runGeneratedViewLifecycle(1,32);logger.debug("GENERATED_VIEWLIFECYCLE seeds=32 events="+n+" after_each=true end=true");return true;}


// Real application adapter with fake dependencies installed by constructor
// overrides. The store is a dependency shared across a simulated process reopen.
(:test,:typecheck(false)) class PbtForegroundApp extends SpaceFoxApp {
 var testStore;var testUrl="https://pbt.invalid";var now=1794818604l;var osMode=Toybox.System.DISPLAY_MODE_LOW_POWER;var armCalls=0;var frameRequests=0;var reminderSyncs=0;var viewCreated=0;var logs=0;
 function initialize(store){SpaceFoxApp.initialize();testStore=store;}
 function createView() as SpaceFoxView {viewCreated+=1;var result=new PbtView();result.fakeMode=osMode;return result;}
 function initialSettings() as SceneSettings {return new SceneSettings(null);}
 function feedUrl() as String {return testUrl;}
 function createCache(url as String) as NativeCache {return new NativeCache(url,testStore);}
 function createForegroundTransfer(url as String,adapter as Object or Null) as NativeTransfer {if(adapter==null){adapter=testStore;}return new NativeTransfer(url,adapter);}
 function currentUtc() as Long {return now;}
 function currentDisplayMode() as Toybox.System.DisplayMode {return osMode;}
 function armForeground(transfer as NativeTransfer,when as Long) as Void {armCalls+=1;}
 function syncForegroundReminders(store as Object,when as Long) as Void {reminderSyncs+=1;}
 function requestForegroundFrame() as Void {frameRequests+=1;}
 function traceMessage(message as String) as Void {logs+=1;}
}
(:test,:typecheck(false)) function volatileBeforeViewBindsOnLowFrame(logger){
 var store=new PbtMemoryStore();var base="https://pbt.invalid";var disk=new NativeTrustedStore(store,base);Test.assert(disk.save(pbtSnapshot(1,1795042260l)));
 var app=new PbtForegroundApp(store);app.onBackgroundData({"base"=>base,"volatileSnapshot"=>pbtSnapshot(2,1795042320l)});
 Test.assert(app.view==null&&app.feed!=null&&app.feed.pendingVolatile!=null);app.getInitialView();app.performReload();Test.assertEqual(app.view.context.displayTarget,1795042260l);
 var view=app.view as PbtView;view.onShow();view.onUpdate(new PbtGraphics());
 Test.assertMessage(view.context!=null&&view.context.displayTarget==1795042320l,"new queued facts must win after durable bootstrap in LOW");
 Test.assert(view.mapDecision.pointVisible(true)&&view.mapDecision.identity.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));Test.assert(app.feed.pendingVolatile==null);Test.assertEqual(view.displayMode(),view.LOW);
 var generation=view.sceneLifecycle.generation;app.onBackgroundData({"base"=>base,"volatileSnapshot"=>pbtSnapshot(1,1795042260l)});Test.assertEqual(view.sceneLifecycle.generation,generation);Test.assertEqual(view.context.displayTarget,1795042320l);return true;
}
(:test,:typecheck(false)) function durableWhileHiddenBindsOnLowShow(logger){
 var store=new PbtMemoryStore();var disk=new NativeTrustedStore(store,"https://pbt.invalid");Test.assert(disk.save(pbtSnapshot(1,1795042260l)));
 var app=new PbtForegroundApp(store);app.getInitialView();app.performReload();var view=app.view as PbtView;view.onShow();view.onUpdate(new PbtGraphics());Test.assertEqual(view.context.displayTarget,1795042260l);
 view.onHide();Test.assert(disk.save(pbtSnapshot(2,1795042320l)));var frames=app.frameRequests;app.onBackgroundData({});Test.assertMessage(app.frameRequests==frames,"hidden delivery must not request a visible frame");view.onShow();view.onUpdate(new PbtGraphics());
 Test.assertMessage(view.context!=null&&view.context.displayTarget==1795042320l,"LOW show must admit a complete snapshot delivered while hidden");
 Test.assert(view.mapDecision.pointVisible(true)&&view.mapDecision.identity.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));return true;
}
(:test,:typecheck(false)) function foregroundRegressions(logger){
 Test.assert(duplicateShowDoesNotScheduleAgain(logger));Test.assert(hiddenWakeDoesNotRequestFrame(logger));
 Test.assert(volatileBeforeViewBindsOnLowFrame(logger));Test.assert(durableWhileHiddenBindsOnLowShow(logger));return true;
}
(:test,:typecheck(false)) function expiredTemporalEntryCancelsAndAllowsRetry(logger){
 var s=new PbtTemporalService();s.onTemporalEvent();Test.assertEqual(s.sent.size(),1);s.fakeMillis=22000;s.onTemporalEvent();
 Test.assertMessage(s.cancellations==1&&s.exits==1,"expired in-flight session must terminate and cancel");s.onTemporalEvent();Test.assertEqual(s.sent.size(),2);
 var before=s.fakeStore.writes;s.sent[0].invoke(200,{"data"=>pbtSnapshot(1,1795042260l)});Test.assertEqual(s.fakeStore.writes,before);return true;
}

// Actual app -> cache -> view lifecycle, with independent durable/RAM model.
// Fake paint marks frame permission; it does not claim pixel rendering.
(:test,:typecheck(false)) class ForegroundTrace {
 var store;var app;var disk=0;var sequence=0;var next=0;var hasCache=false;var ram=0;var kind=0;var pending=0;var token=0;var context=0;var exists=false;var shown=false;var boot=false;var lowCheck=false;var dirty=true;var trace=[];var skipped=0;
 var coverage={"commit_applied"=>0,"slot_failure"=>0,"pointer_failure"=>0,"create_applied"=>0,"bootstrap_applied"=>0,"show_applied"=>0,"hide_applied"=>0,"frame_applied"=>0,"frame_no"=>0,"hidden_volatile"=>0,"volatile_applied"=>0,"stale_no"=>0,"hidden_durable"=>0,"duplicate_durable_no"=>0,"reopen_applied"=>0};
 function initialize(){store=new PbtMemoryStore();app=new PbtForegroundApp(store);}
 function newValue(){next+=1;return next;}
 function target(n){return 1795042200l+n*60;}
 function flush(){if(pending>ram){ram=pending;kind=1;context=pending;pending=0;dirty=true;coverage["volatile_applied"]+=1;}else{pending=0;}}
 function reloadModel(){
  hasCache=true;if(exists&&shown&&pending!=0){flush();}
  if(exists&&sequence!=0&&sequence!=token){if(kind!=1||disk>=ram){ram=disk;kind=2;context=disk;dirty=true;}token=sequence;}
  else if(exists&&ram!=0&&context!=ram){context=ram;dirty=true;}
 }
 function deliverVolatile(n){
  hasCache=true;if(n>ram&&(pending==0||n>pending)){pending=n;if(shown&&exists){flush();}else{coverage["hidden_volatile"]+=1;}}
  else{coverage["stale_no"]+=1;}
  app.onBackgroundData({"base"=>"https://pbt.invalid","volatileSnapshot"=>pbtSnapshot(n,target(n))});
 }
 function step(e,seed,i){
  trace.add(e);
  if(e==0){var n=newValue();var owner=new NativeTrustedStore(store,"https://pbt.invalid");Test.assert(owner.save(pbtSnapshot(n,target(n))));disk=n;sequence+=1;coverage["commit_applied"]+=1;}
  else if(e==1||e==2){var n=newValue();var owner=new NativeTrustedStore(store,"https://pbt.invalid");if(e==1){store.fail=1;}else{store.fail=2;}var caught=false;try{owner.save(pbtSnapshot(n,target(n)));}catch(error){caught=true;}store.fail=0;ownerCheck(caught,"foreground-failure",seed,i,trace,true,caught);if(e==1){coverage["slot_failure"]+=1;}else{coverage["pointer_failure"]+=1;}deliverVolatile(n);}
  else if(e==3){if(!exists){app.getInitialView();exists=true;boot=true;dirty=true;coverage["create_applied"]+=1;}else{skipped+=1;}}
  else if(e==4){if(exists){reloadModel();app.performReload();coverage["bootstrap_applied"]+=1;}else{skipped+=1;}}
  else if(e==5){if(exists){if(!shown){shown=true;lowCheck=true;dirty=true;coverage["show_applied"]+=1;}app.view.onShow();}else{skipped+=1;}}
  else if(e==6){if(exists){if(shown){shown=false;lowCheck=false;dirty=true;coverage["hide_applied"]+=1;}app.view.onHide();}else{skipped+=1;}}
  else if(e==7){if(exists){if(shown&&dirty){dirty=false;coverage["frame_applied"]+=1;if(boot||lowCheck){boot=false;lowCheck=false;reloadModel();}}else{coverage["frame_no"]+=1;}app.view.onUpdate(new PbtGraphics());}else{skipped+=1;}}
  else if(e==8){var before=app.frameRequests;var duplicate=exists&&shown&&hasCache&&(sequence==0||sequence==token);if(exists&&shown&&!duplicate){reloadModel();}else if(!exists||!shown){coverage["hidden_durable"]+=1;}app.onBackgroundData({});if(duplicate){coverage["duplicate_durable_no"]+=1;ownerCheck(app.frameRequests==before,"foreground-duplicate-no",seed,i,trace,before,app.frameRequests);}}
  else if(e==9){app.onStop(null);app=new PbtForegroundApp(store);hasCache=false;ram=0;kind=0;pending=0;token=0;context=0;exists=false;shown=false;boot=false;lowCheck=false;dirty=true;coverage["reopen_applied"]+=1;}
  else{deliverVolatile(1);}
  verify(seed,i);
 }
 function verify(seed,i){
  ownerCheck((app.view!=null)==exists&&(app.feed!=null)==hasCache,"foreground-owners",seed,i,trace,[exists,hasCache],[app.view!=null,app.feed!=null]);
  if(hasCache){var actual=0;var actualPending=0;if(app.feed.packet!=null){actual=app.feed.packet.document["publisher"]["generation"];}if(app.feed.pendingVolatile!=null){actualPending=app.feed.pendingVolatile[1]["generation"];}
   ownerCheck(actual==ram&&actualPending==pending&&app.feed.ramState==kind,"foreground-cache",seed,i,trace,[ram,pending,kind],[actual,actualPending,app.feed.ramState]);}
  if(exists){var view=app.view as PbtView;var actualTarget=null;if(view.context!=null){actualTarget=view.context.displayTarget;}
   var expectedTarget=null;if(context!=0){expectedTarget=target(context);}ownerCheck(view.visible()==shown&&view.displayMode()==view.LOW&&actualTarget==expectedTarget,"foreground-view",seed,i,trace,[shown,expectedTarget],[view.visible(),view.displayMode(),actualTarget]);
   ownerCheck(view.mapDecision.pointVisible(shown)==(shown&&context!=0),"foreground-map",seed,i,trace,shown&&context!=0,view.mapDecision.pointVisible(shown));
   if(context!=0){ownerCheck(view.context.pointText[0].equals("111.589567")&&view.context.pointText[1].equals("38.863128"),"foreground-point",seed,i,trace,"Taiyuan",view.context.pointText);}
  }
  var marker=store.values["sf.snapshot.active:https://pbt.invalid"];var actualDisk=0;var actualSeq=0;if(marker!=null){actualSeq=marker["sequence"];var value=store.values["sf.snapshot."+marker["slot"]+":https://pbt.invalid"];actualDisk=value[1]["generation"];}
  ownerCheck(actualDisk==disk&&actualSeq==sequence,"foreground-disk",seed,i,trace,[disk,sequence],[actualDisk,actualSeq]);
 }
 function final(seed,n){verify(seed,n);var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"foreground-coverage",seed,n,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);}
}
(:typecheck(false)) function runGeneratedForegroundDelivery(firstSeed,seedCount){
 var total=0;var skips=0;
 for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){var rng=new OwnerRandom(seed);var run=new ForegroundTrace();var prefix=[0,3,4,5,7,8,7,6,1,5,7,10,6,0,8,5,7,2,9,3,5,7];var events=prefix.size()+12+rng.draw(25);
  for(var i=0;i<events;i+=1){var e=0;if(i<prefix.size()){e=prefix[i];}else{e=rng.draw(11);}run.step(e,seed,i);total+=1;}run.final(seed,events);
  run.trace.add("stop");var stoppedView=run.app.view;run.app.onStop(null);run.shown=false;run.exists=false;run.hasCache=false;run.verify(seed,events);total+=1;
  if(stoppedView!=null){pbtCheckViewReleased(stoppedView,seed,events,run.trace);ownerCheck(!stoppedView.visible()&&stoppedView.pendingLoader==null&&stoppedView.cancelAdmission==null,"foreground-loader-release",seed,events,run.trace,true,!stoppedView.visible()&&stoppedView.pendingLoader==null&&stoppedView.cancelAdmission==null);}
  skips+=run.skipped;PbtMetrics.skipped+=run.skipped;
 }
 return total;
}
(:test,:typecheck(false)) function generatedForegroundDelivery(logger){var n=runGeneratedForegroundDelivery(1,32);logger.debug("GENERATED_FOREGROUNDDELIVERY seeds=32 events="+n+" after_each=true end=true");return true;}


(:test,:typecheck(false)) class PbtComplication {
 var value;var shortLabel="field";var longLabel="field";var unit=0;var kind;
 function initialize(k,v){kind=k;value=v;}
 function getType(){return kind;}
}
(:test,:typecheck(false)) class PbtComplicationApi extends FieldComplicationApi {
 var values=[null,null,null,null];var failures=[false,false,false,false];var gets=0;var registers=0;var unregistrations=0;var subscriptions=0;var unsubscriptions=0;var kinds=[2,3,6,7];
 function register(callback){if(callback==null){unregistrations+=1;}else{registers+=1;}}
 function subscribe(id){subscriptions+=1;return true;}
 function unsubscribe(id){unsubscriptions+=1;}
 function get(id){gets+=1;var i=kinds.indexOf(id.getType());if(i<0){throw new Lang.InvalidValueException("unexpected source");}if(failures[i]){throw new Lang.InvalidValueException("provider failure");}if(values[i]==null){return null;}return new PbtComplication(kinds[i],values[i]);}
}
(:test,:typecheck(false)) class PbtSelectedFields extends SelectedFields {
 var fakeApi;var forbidden=0;
 function initialize(){SelectedFields.initialize();fakeApi=new PbtComplicationApi();api=fakeApi;}
 function savedField(slot){return new Toybox.Complications.Id(fakeApi.kinds[slot-1]);}
 function systemInfo(){forbidden+=1;throw new Lang.InvalidValueException("unexpected real system");}
 function activityInfo(){forbidden+=1;throw new Lang.InvalidValueException("unexpected real activity");}
 function callback(id){}
}
(:test,:typecheck(false)) class FieldTrace {
 var fields;var active=false;var values=[null,null,null,null];var failed=[false,false,false,false];var expected=[null,null,null,null];var states=["WAITING","WAITING","WAITING","WAITING"];var gets=0;var registers=0;var unregistrations=0;var subscriptions=0;var unsubscriptions=0;var trace=[];
 var coverage={"start_applied"=>0,"stop_applied"=>0,"stopped_no"=>0,"stopped_read_no"=>0,"read_applied"=>0,"change_applied"=>0,"ready_applied"=>0,"missing_applied"=>0,"failure_applied"=>0};
 function initialize(){fields=new PbtSelectedFields();}
 function applyValue(index){if(failed[index]){expected[index]=null;states[index]="UNAVAILABLE";coverage["failure_applied"]+=1;}else if(values[index]==null){expected[index]=null;states[index]="WAITING";coverage["missing_applied"]+=1;}else{expected[index]=values[index].toString();states[index]="READY";coverage["ready_applied"]+=1;}}
 function step(e,arg,seed,i){trace.add([e,arg]);var index=arg%4;
  if(e==0){if(active){unregistrations+=1;unsubscriptions+=4;}active=true;registers+=1;subscriptions+=4;fields.start(["custom1","custom2","custom3","custom4"],fields.method(:callback));coverage["start_applied"]+=1;}
  else if(e==1){if(active){active=false;unregistrations+=1;unsubscriptions+=4;coverage["stop_applied"]+=1;}else{coverage["stopped_no"]+=1;}fields.stop();}
  else if(e==2){values[index]=arg+20;failed[index]=false;fields.fakeApi.values[index]=arg+20;fields.fakeApi.failures[index]=false;}
  else if(e==3){values[index]=null;failed[index]=false;fields.fakeApi.values[index]=null;fields.fakeApi.failures[index]=false;}
  else if(e==4){failed[index]=true;fields.fakeApi.failures[index]=true;}
  else if(e==5){if(active){for(var j=0;j<4;j+=1){applyValue(j);}gets+=4;coverage["read_applied"]+=1;}else{coverage["stopped_read_no"]+=1;}fields.read("en");}
  else{if(active){applyValue(index);gets+=1;coverage["change_applied"]+=1;}else{coverage["stopped_no"]+=1;}fields.readChanged("en",new Toybox.Complications.Id(fields.fakeApi.kinds[index]));}
  verify(seed,i);
 }
 function verify(seed,i){
  for(var j=0;j<4;j+=1){var role="custom"+(j+1);var actual=fields.display(role);var wanted="—";if(expected[j]!=null){wanted=expected[j];}ownerCheck(fields.state(role).equals(states[j])&&actual.equals(wanted),"fields-value",seed,i,trace,[states[j],wanted],[fields.state(role),actual]);}
  ownerCheck(fields.fakeApi.gets==gets&&fields.fakeApi.registers==registers&&fields.fakeApi.unregistrations==unregistrations&&fields.fakeApi.subscriptions==subscriptions&&fields.fakeApi.unsubscriptions==unsubscriptions&&fields.forbidden==0,"fields-effects",seed,i,trace,[gets,registers,unregistrations,subscriptions,unsubscriptions,0],[fields.fakeApi.gets,fields.fakeApi.registers,fields.fakeApi.unregistrations,fields.fakeApi.subscriptions,fields.fakeApi.unsubscriptions,fields.forbidden]);
 }
 function final(seed,n){verify(seed,n);var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"fields-coverage",seed,n,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);}
}
(:typecheck(false)) function runGeneratedSelectedFields(firstSeed,seedCount){
 var total=0;for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){var rng=new OwnerRandom(seed);var run=new FieldTrace();var prefix=[[0,0],[2,0],[3,1],[4,2],[2,3],[5,0],[2,2],[6,2],[1,0],[5,0],[6,1],[0,0],[5,0]];var events=prefix.size()+12+rng.draw(37);
  for(var i=0;i<events;i+=1){var e=0;var arg=0;if(i<prefix.size()){e=prefix[i][0];arg=prefix[i][1];}else{e=rng.draw(7);arg=rng.draw(32);}run.step(e,arg,seed,i);total+=1;}run.final(seed,events);
 }
 return total;
}
(:test,:typecheck(false)) function generatedSelectedFields(logger){var n=runGeneratedSelectedFields(1,64);logger.debug("GENERATED_SELECTEDFIELDS seeds=64 events="+n+" after_each=true end=true");return true;}


(:test,:typecheck(false)) class PbtActivity {var steps;var calories;function initialize(a,b){steps=a;calories=b;}}
(:test,:typecheck(false)) class PbtFitness extends Fitness {
 var stepsValue=null;var activityCalls=0;var heartCalls=0;var stressCalls=0;var batteryCalls=0;
 function activityAvailable() as Boolean {return true;}
 function activityInfo(){activityCalls+=1;return new PbtActivity(stepsValue,null);}
 function batteryValue(){batteryCalls+=1;throw new Lang.InvalidValueException("unexpected battery");}
}
(:test,:typecheck(false)) class PbtEnergyApi extends FieldComplicationApi {
 var values={18=>null,22=>null,23=>null};var failures={18=>false,22=>false,23=>false};var gets=0;var registers=0;var unregistrations=0;var subscriptions=0;var unsubscriptions=0;
 function register(callback){if(callback==null){unregistrations+=1;}else{registers+=1;}}
 function subscribe(id){subscriptions+=1;return true;}
 function unsubscribe(id){unsubscriptions+=1;}
 function get(id){gets+=1;var kind=id.getType();if(failures[kind]){throw new Lang.InvalidValueException("health provider");}if(values[kind]==null){return null;}return new PbtComplication(kind,values[kind]);}
}
(:test,:typecheck(false)) class PbtEnergyFields extends SelectedFields {
 var fakeApi;var forbidden=0;
 function initialize(){SelectedFields.initialize();fakeApi=new PbtEnergyApi();api=fakeApi;}
 function savedField(slot){forbidden+=1;throw new Lang.InvalidValueException("unexpected field storage");}
 function systemInfo(){forbidden+=1;throw new Lang.InvalidValueException("unexpected system");}
 function activityInfo(){forbidden+=1;throw new Lang.InvalidValueException("unexpected activity");}
 function callback(id){}
}
(:test,:typecheck(false)) class FitnessTrace {
 var fitness;var fields;var active=false;var now=1794818604;var steps=null;var input=[null,null,null];var failures=[false,false,false];var accepted=[null,null,null];var acceptedStates=["WAITING","WAITING","WAITING"];var reads=0;var samples=0;var expected=null;var expectedStates=null;var result=null;var trace=[];
 var coverage={"start_applied"=>0,"stop_applied"=>0,"sample_applied"=>0,"ready"=>0,"missing"=>0,"failure"=>0,"zero"=>0,"read_applied"=>0,"inactive_read_no"=>0};
 function initialize(){fitness=new PbtFitness();fields=new PbtEnergyFields();fitness.selectedRoles=["steps","energy","heart","stress"];fitness.selectedFields=fields;}
 function step(e,arg,seed,i){trace.add([e,arg]);
  if(e==0){if(active){fields.stop();}fields.start(["steps","energy","heart","stress"],fields.method(:callback));active=true;coverage["start_applied"]+=1;}
  else if(e==1){fields.stop();active=false;coverage["stop_applied"]+=1;}
  else if(e==2){steps=arg;fitness.stepsValue=arg;}
  else if(e==3){input[1]=arg;fields.fakeApi.values[18]=arg;}
  else if(e==4){input[2]=arg;fields.fakeApi.values[22]=arg;}
  else if(e==5){input[0]=arg;fields.fakeApi.values[23]=arg;}
  else if(e==6){input[1]=null;fields.fakeApi.values[18]=null;}
  else if(e==7){failures[1]=!failures[1];fields.fakeApi.failures[18]=failures[1];}
  else if(e==8){failures[2]=!failures[2];fields.fakeApi.failures[22]=failures[2];}
  else if(e==9){if(active){fields.read("en");reads+=1;coverage["read_applied"]+=1;for(var n=0;n<3;n+=1){accepted[n]=null;acceptedStates[n]="WAITING";if(failures[n]){acceptedStates[n]="UNAVAILABLE";coverage["failure"]+=1;}else if(input[n]!=null&&input[n]>=0&&input[n]<=100){accepted[n]=input[n];acceptedStates[n]="READY";coverage["ready"]+=1;if(input[n]==0){coverage["zero"]+=1;}}else{coverage["missing"]+=1;}}}else{fields.readChanged("en",new Toybox.Complications.Id(23));coverage["inactive_read_no"]+=1;}}
  else if(e==10){failures[0]=!failures[0];fields.fakeApi.failures[23]=failures[0];}
  else{samples+=1;expected=[steps,accepted[0],accepted[1],accepted[2]];expectedStates=[steps==null?"WAITING":"READY",acceptedStates[0],acceptedStates[1],acceptedStates[2]];result=fitness.sample(now);coverage["sample_applied"]+=1;}
  verify(seed,i);
 }
 function verify(seed,i){
  ownerCheck(fields.fakeApi.gets==reads*3&&fitness.activityCalls==samples&&fitness.heartCalls==0&&fitness.stressCalls==0&&fitness.batteryCalls==0&&fields.forbidden==0,"fitness-effects",seed,i,trace,[reads*3,samples,0],[fields.fakeApi.gets,fitness.activityCalls,fields.forbidden]);
  if(result!=null){var roles=["steps","energy","heart","stress"];for(var j=0;j<4;j+=1){ownerCheck(result[roles[j]]==expected[j]&&fitness.fieldState(roles[j]).equals(expectedStates[j]),"fitness-value",seed,i,trace,[roles[j],expected[j],expectedStates[j]],[result[roles[j]],fitness.fieldState(roles[j])]);}}
 }
 function final(seed,n){verify(seed,n);var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"fitness-coverage",seed,n,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);}
}
(:typecheck(false)) function runGeneratedFitnessOwners(firstSeed,seedCount){
 var total=0;for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){var rng=new OwnerRandom(seed);var run=new FitnessTrace();var prefix=[[0,0],[11,0],[2,27],[3,0],[4,35],[5,68],[9,0],[11,0],[7,0],[9,0],[11,0],[7,0],[6,0],[9,0],[11,0],[1,0],[9,0],[0,0],[3,72],[9,0],[11,0]];var events=prefix.size()+12+rng.draw(37);
  for(var i=0;i<events;i+=1){var e=0;var arg=0;if(i<prefix.size()){e=prefix[i][0];arg=prefix[i][1];}else{e=rng.draw(12);arg=rng.draw(101);}run.step(e,arg,seed,i);total+=1;}run.final(seed,events);
 }
 return total;
}
(:test,:typecheck(false)) function generatedFitnessOwners(logger){var n=runGeneratedFitnessOwners(1,64);logger.debug("GENERATED_FITNESSOWNERS seeds=64 events="+n+" after_each=true end=true");return true;}

(:test,:typecheck(false)) function pbtExactSnapshot(generation,target){
 var v=pbtSnapshot(generation,null);var row=v[3];
 row[0]="ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a";row[1]="Vulcan VC6L";row[2]="United Launch Alliance";row[3]="ULA";row[4]="Communications";row[5]="US · Cape Canaveral SFS";row[6]="ll2:configuration:479";row[7]="ll2:organization:124";row[8]="ll2:site:29";row[9]=["-80.58303644","28.58341025"];row[10]=target;row[11]="exact";row[13]=target+900;row[14]=target;row[15]=target-1000;row[20]=null;row[21]=true;
 v[1]["selectionValidatedUtc"]=target-1000;return v;
}
(:test,:typecheck(false)) class PbtReminderServices {
 var isEnabled=true;var quiet=false;var time=1794676650l;var enabledCalls=0;var timeCalls=0;var quietCalls=0;var posts=[];
 function enabled(){enabledCalls+=1;return isEnabled;}
 function now(){timeCalls+=1;return time;}
 function isQuiet(when){quietCalls+=1;return quiet;}
 function post(slot,scene){posts.add([slot,scene["target"]]);}
}
(:test,:typecheck(false)) class ReminderTrace {
 var store;var cache;var services;var now=1794676650l;var target=1794677550l;var rowSince=1794676650l;var publishedTarget=null;var generation=0;var sequence=0;var control=null;var controlSince=null;var controlWrites=0;var attemptWrites=0;var attempts={};var expectedPosts=[];var enabled=true;var quiet=false;var fail=false;var enabledCalls=0;var timeCalls=0;var quietCalls=0;var trace=[];
 var coverage={"publish_applied"=>0,"wake_post"=>0,"wake_no"=>0,"quiet_consumed"=>0,"write_failure"=>0,"disabled_no"=>0,"reopen_applied"=>0};
 function initialize(){store=new PbtMemoryStore();cache=new NativeCache("https://pbt.invalid",store);services=new PbtReminderServices();}
 function publish(){generation+=1;var value=pbtExactSnapshot(generation,target);var owner=new NativeTrustedStore(store,"https://pbt.invalid");Test.assert(owner.save(value));sequence+=1;var packet=new NativeTrustedPacket(value);Test.assert(cache.acceptDurable(packet));LaunchReminderForeground.publishQueue(cache,now,[packet.presentation]);if(publishedTarget==null||publishedTarget!=target){rowSince=now;}publishedTarget=target;coverage["publish_applied"]+=1;}
 function wakeModel(){
  enabledCalls+=1;if(control==null||control!=enabled||controlSince>now){control=enabled;controlSince=now;controlWrites+=1;}
  if(!enabled){coverage["disabled_no"]+=1;return;}
  if(generation==0||now<target-1000||now>=target+900){coverage["wake_no"]+=1;return;}
  var since=controlSince;if(rowSince>since){since=rowSince;}var slot=-1;var times=[target-900,target-600,target-300,target];
  for(var j=0;j<4;j+=1){var deadline=times[j];var end=deadline+90;if(j==3){end=deadline;}if(deadline>=since&&now>=deadline&&now<=end){slot=j;}}
  var key=target.toString();if(slot<0||(attempts.hasKey(key)&&attempts[key]>=slot)){coverage["wake_no"]+=1;return;}
  if(fail){coverage["write_failure"]+=1;return;}
  attempts[key]=slot;attemptWrites+=1;timeCalls+=1;quietCalls+=1;if(quiet){coverage["quiet_consumed"]+=1;}else{enabledCalls+=1;expectedPosts.add([slot,target]);coverage["wake_post"]+=1;}
 }
 function step(e,arg,seed,i){trace.add([e,arg]);
  if(e==0){publish();}
  else if(e==1){now+=arg;services.time=now;}
  else if(e==2){enabled=!enabled;services.isEnabled=enabled;}
  else if(e==3){quiet=!quiet;services.quiet=quiet;}
  else if(e==4){fail=!fail;if(fail){store.fail=3;}else{store.fail=0;}}
  else if(e==5){wakeModel();LaunchReminder.wakeWithServices(cache,now,null,services.method(:post),services);}
  else if(e==6){cache=new NativeCache("https://pbt.invalid",store);var value=new NativeTrustedStore(store,"https://pbt.invalid").load();if(value!=null){Test.assert(cache.acceptDurable(new NativeTrustedPacket(value)));}coverage["reopen_applied"]+=1;}
  else{target=now+900;publish();}
  verify(seed,i);
 }
 function verify(seed,i){
  ownerCheck(store.controls==controlWrites&&store.attempts==attemptWrites&&services.posts.size()==expectedPosts.size()&&services.enabledCalls==enabledCalls&&services.timeCalls==timeCalls&&services.quietCalls==quietCalls,"reminder-effects",seed,i,trace,[controlWrites,attemptWrites,expectedPosts,enabledCalls,timeCalls,quietCalls],[store.controls,store.attempts,services.posts,services.enabledCalls,services.timeCalls,services.quietCalls]);
  for(var j=0;j<expectedPosts.size();j+=1){ownerCheck(services.posts[j][0]==expectedPosts[j][0]&&services.posts[j][1]==expectedPosts[j][1],"reminder-post",seed,i,trace,expectedPosts,services.posts);}
  var saved=store.values["sf.reminder.attempt"];if(saved!=null){var rows=saved["rows"];for(var k=0;k<rows.size();k+=1){var key=rows[k]["target"].toString();ownerCheck(attempts.hasKey(key)&&attempts[key]==rows[k]["last"],"reminder-durable",seed,i,trace,attempts,rows);}}
 }
 function final(seed,n){verify(seed,n);var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"reminder-coverage",seed,n,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);}
}
(:typecheck(false)) function runGeneratedReminderOwners(firstSeed,seedCount){
 var total=0;for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){var rng=new OwnerRandom(seed);var run=new ReminderTrace();
  var prefix=[[0,0],[5,0],[5,0],[1,300],[3,0],[5,0],[3,0],[1,300],[4,0],[5,0],[4,0],[5,0],[2,0],[5,0],[2,0],[6,0],[1,300],[5,0]];var events=prefix.size()+12+rng.draw(25);
  for(var i=0;i<events;i+=1){var e=0;var arg=0;if(i<prefix.size()){e=prefix[i][0];arg=prefix[i][1];}else{e=rng.draw(8);arg=rng.draw(4)*90;}run.step(e,arg,seed,i);total+=1;}run.final(seed,events);
 }
 return total;
}
(:test,:typecheck(false)) function generatedReminderOwners(logger){var n=runGeneratedReminderOwners(1,32);logger.debug("GENERATED_REMINDEROWNERS seeds=32 events="+n+" after_each=true end=true");return true;}

(:test,:typecheck(false)) function lowSettingsSourceChangeLoadsNewFacts(logger){
 var store=new PbtMemoryStore();var a=new NativeTrustedStore(store,"https://pbt.invalid");var b=new NativeTrustedStore(store,"https://other.invalid");
 Test.assert(a.save(pbtSnapshot(1,1795042260l)));var newer=pbtExactSnapshot(1,1795042500l);newer[1]["selectionValidatedUtc"]=1794812997l;newer[3][15]=1794812997l;Test.assert(b.save(newer));
 var app=new PbtForegroundApp(store);app.getInitialView();app.performReload();var view=app.view as PbtView;view.onShow();view.onUpdate(new PbtGraphics());
 Test.assert(view.context.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));Test.assert(view.sceneLifecycle.request(1));var oldJob=view.sceneLifecycle.begin();app.testUrl="https://other.invalid";app.onSettingsChanged();
 Test.assertMessage(app.feed.base.equals("https://other.invalid")&&view.context!=null&&view.context.launchId.equals("ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"),"LOW settings source change must admit the new source");
 Test.assert(view.mapDecision.pointVisible(true)&&view.mapDecision.identity.equals("ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"));Test.assert(!view.sceneLifecycle.complete(oldJob));var generation=view.sceneLifecycle.generation;var frames=app.frameRequests;app.onBackgroundData({"base"=>"https://pbt.invalid","volatileSnapshot"=>pbtSnapshot(2,1795042320l)});Test.assertEqual(view.sceneLifecycle.generation,generation);Test.assertEqual(app.frameRequests,frames);Test.assert(view.context.launchId.equals("ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"));return true;
}

(:test,:typecheck(false)) class SourceTrace {
 var store;var app;var view;var source=0;var ram=1;var pending=0;var context=1;var shown=true;var lowCheck=false;var dirty=true;var activeToken=null;var staleToken=null;var trace=[];var skipped=0;
 var coverage={"switch_applied"=>0,"hidden_switch"=>0,"old_source_no"=>0,"delivery_applied"=>0,"hide_applied"=>0,"show_applied"=>0,"frame_applied"=>0,"art_applied"=>0,"late_art_no"=>0};
 function url(n){if(n==0){return "https://pbt.invalid";}return "https://other.invalid";}
 function identity(n){if(n==0){return "ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60";}return "ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a";}
 function value(which,generation){var target=1795042200l+generation*60;if(which==0){return pbtSnapshot(generation,target);}var v=pbtExactSnapshot(generation,target);v[1]["selectionValidatedUtc"]=1794812997l;v[3][15]=1794812997l;return v;}
 function initialize(){
  store=new PbtMemoryStore();Test.assert(new NativeTrustedStore(store,url(0)).save(value(0,1)));Test.assert(new NativeTrustedStore(store,url(1)).save(value(1,1)));
  app=new PbtForegroundApp(store);app.getInitialView();app.performReload();view=app.view as PbtView;view.onShow();view.onUpdate(new PbtGraphics());dirty=false;
 }
 function step(e,arg,seed,i){trace.add([e,arg]);
  if(e==0){var next=arg%2;if(next!=source){source=next;ram=0;pending=0;context=0;dirty=true;if(activeToken!=null){staleToken=activeToken;activeToken=null;}coverage["switch_applied"]+=1;if(!shown){coverage["hidden_switch"]+=1;}if(shown){ram=1;context=1;}}
   if(shown&&ram==0){ram=1;context=1;}if(shown&&pending>ram){ram=pending;pending=0;context=ram;}
   dirty=true;app.testUrl=url(next);app.onSettingsChanged();}
  else if(e==1){if(shown){shown=false;dirty=true;lowCheck=false;if(activeToken!=null){staleToken=activeToken;activeToken=null;}coverage["hide_applied"]+=1;}view.onHide();}
  else if(e==2){if(!shown){shown=true;lowCheck=true;dirty=true;coverage["show_applied"]+=1;}view.onShow();}
  else if(e==3){if(shown&&dirty){dirty=false;coverage["frame_applied"]+=1;if(lowCheck){lowCheck=false;if(pending>ram){ram=pending;pending=0;context=ram;dirty=true;if(activeToken!=null){staleToken=activeToken;activeToken=null;}}else if(ram==0){ram=1;context=1;dirty=true;}}}view.onUpdate(new PbtGraphics());}
  else if(e==4){var before=view.sceneLifecycle.generation;var frames=app.frameRequests;var other=1-source;app.onBackgroundData({"base"=>url(other),"volatileSnapshot"=>value(other,99)});ownerCheck(view.sceneLifecycle.generation==before&&app.frameRequests==frames,"source-old-callback",seed,i,trace,[before,frames],[view.sceneLifecycle.generation,app.frameRequests]);coverage["old_source_no"]+=1;}
  else if(e==5){if(2>ram&&2>pending){pending=2;if(shown){ram=2;context=2;pending=0;dirty=true;if(activeToken!=null){staleToken=activeToken;activeToken=null;}coverage["delivery_applied"]+=1;}}app.onBackgroundData({"base"=>url(source),"volatileSnapshot"=>value(source,2)});}
  else if(e==6){if(activeToken==null&&context!=0){var granted=view.sceneLifecycle.request(100+i);ownerCheck(granted,"source-art-permission",seed,i,trace,true,granted);activeToken=view.sceneLifecycle.begin();ownerCheck(activeToken!=null,"source-art-lease",seed,i,trace,"non-null",activeToken);coverage["art_applied"]+=1;}else{skipped+=1;}}
  else{if(staleToken!=null){Test.assert(!view.sceneLifecycle.complete(staleToken));coverage["late_art_no"]+=1;}else{skipped+=1;}}
  verify(seed,i);
 }
 function verify(seed,i){
  var actual=null;if(view.context!=null){actual=view.context.launchId;}
  var expected=null;if(context!=0){expected=identity(source);}
  ownerCheck((actual==null&&expected==null)||(actual!=null&&expected!=null&&actual.equals(expected)),"source-context",seed,i,trace,expected,actual);
  ownerCheck(view.visible()==shown&&view.displayMode()==view.LOW&&view.mapDecision.pointVisible(shown)==(shown&&context!=0),"source-map",seed,i,trace,[shown,context],[view.visible(),view.mapDecision.pointVisible(shown)]);
  ownerCheck(app.feed!=null&&app.feed.base.equals(url(source)),"source-cache",seed,i,trace,url(source),app.feed.base);
 }
 function final(seed,n){verify(seed,n);var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"source-coverage",seed,n,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);}
}
(:typecheck(false)) function runGeneratedSourceSwitch(firstSeed,seedCount){
 var total=0;var skips=0;for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){var rng=new OwnerRandom(seed);var run=new SourceTrace();var prefix=[[6,0],[0,1],[4,0],[7,0],[1,0],[0,0],[2,0],[3,0],[5,0],[4,0],[0,1],[5,0]];var events=prefix.size()+12+rng.draw(25);
  for(var i=0;i<events;i+=1){var e=0;var arg=0;if(i<prefix.size()){e=prefix[i][0];arg=prefix[i][1];}else{e=rng.draw(8);arg=rng.draw(4);}run.step(e,arg,seed,i);total+=1;}run.final(seed,events);run.trace.add("stop");run.app.onStop(null);run.shown=false;total+=1;pbtCheckViewReleased(run.view,seed,events,run.trace);
  ownerCheck(run.app.view==null&&run.app.feed==null&&!run.view.visible()&&!run.view.mapDecision.pointVisible(false),"source-stop",seed,events,run.trace,true,run.app.view==null&&run.app.feed==null&&!run.view.visible()&&!run.view.mapDecision.pointVisible(false));
  ownerCheck(run.view.pendingLoader==null&&run.view.cancelAdmission==null,"source-loader-release",seed,events,run.trace,true,run.view.pendingLoader==null&&run.view.cancelAdmission==null);skips+=run.skipped;PbtMetrics.skipped+=run.skipped;
 }
 return total;
}
(:test,:typecheck(false)) function generatedSourceSwitch(logger){var n=runGeneratedSourceSwitch(1,32);logger.debug("GENERATED_SOURCESWITCH seeds=32 events="+n+" after_each=true end=true");return true;}


// Production view/SceneLifecycle routing with a fake optional decoder lease.
// Direct tick events model delivered timer callbacks; they do not prove Garmin
// timer dispatch or actual raster decoding. No product fields are injected.
(:test,:typecheck(false)) class PbtArtBuild extends NativeSfrBuild {
 var owner;var outcome=0;var released=false;
 function initialize(parent){owner=parent;result=null;}
 function dispose(){if(!released){released=true;owner.disposals+=1;}}
 function step(){owner.steps+=1;if(outcome==2){throw new Toybox.Lang.InvalidValueException("fake asset failure");}if(outcome==1){released=true;owner.completions+=1;return true;}return false;}
}
(:test,:typecheck(false)) class PbtArtSource extends NativeRenderSource {
 function initialize(adapter){store=adapter;base="https://pbt.invalid";ready=true;serial=1;transferHash="transfer";selectionHash="selection";}
}
(:test,:typecheck(false)) class PbtArtView extends PbtView {
 var creations=0;var disposals=0;var steps=0;var completions=0;var restored=0;var free=20000;var lastBuild=null;
 function initialize(){PbtView.initialize();}
 function optionalHeapFree(){return free;}
 function sfrReadReserve(){return 10000;}
 function createSfrBuild(store,base,packet){creations+=1;lastBuild=new PbtArtBuild(self);return lastBuild;}
 function prepareRenderer() as Void {restored+=1;}
}
(:test,:typecheck(false)) class ArtTrace {
 var view;var store;var packet;var job=0;var build=false;var allocations=0;var disposed=0;var steps=0;var complete=0;var restores=0;var free=true;var trace=[];
 var coverage={"prepare_applied"=>0,"prepare_no"=>0,"start"=>0,"step"=>0,"refuse"=>0,"cancel_applied"=>0,"cancel_no"=>0,"fail"=>0,"complete"=>0,"hide_release"=>0,"sleep_retains"=>0};
 function initialize(){
  store=new PbtMemoryStore();view=new PbtArtView();view.onShow();var value=pbtSnapshot(1,1795042260l);
  value[6]={"selection"=>{"sha256"=>"selection"},"transfer"=>{"sha256"=>"transfer"},"ids"=>[],"site"=>null};
  packet=new NativeTrustedPacket(value);bind();
 }
 function bind(){view.setPacket(packet);view.setAssetCache(new PbtArtSource(store));job=0;build=false;}
 function step(e,seed,i){trace.add(e);
  if(e==0){view.prepareVisual();if(job==0||job==3){job=1;coverage["prepare_applied"]+=1;}else{coverage["prepare_no"]+=1;}}
  else if(e==1){if(job==1&&!build){if(free){build=true;job=2;allocations+=1;coverage["start"]+=1;}else{coverage["refuse"]+=1;}}else if(job==2&&build&&free){steps+=1;coverage["step"]+=1;}view.sfrStep();}
  else if(e==2){if(job==1&&!build&&free){build=true;job=2;allocations+=1;coverage["start"]+=1;}else if(job==2&&build&&free){view.lastBuild.outcome=1;steps+=1;complete+=1;restores+=1;build=false;job=3;coverage["complete"]+=1;}view.sfrStep();}
  else if(e==3){if(job==1&&!build&&free){build=true;job=2;allocations+=1;coverage["start"]+=1;}else if(job==2&&build&&free){view.lastBuild.outcome=2;steps+=1;disposed+=1;build=false;job=4;coverage["fail"]+=1;}view.sfrStep();}
  else if(e==4){if(job!=0){coverage["cancel_applied"]+=1;}else{coverage["cancel_no"]+=1;}if(build){disposed+=1;}view.beginAdmission();bind();view.endAdmission();}
  else if(e==5){free=!free;view.free=free?20000:0;}
  else if(e==6){if(build){disposed+=1;coverage["hide_release"]+=1;}view.onHide();build=false;job=0;
   ownerCheck(view.disposals==disposed&&view.sfrBuild==null,"art-hide-release",seed,i,trace,[disposed,false],[view.disposals,view.sfrBuild!=null]);view.onShow();}
  else{var before=build;view.fakeMode=Toybox.System.DISPLAY_MODE_LOW_POWER;view.onEnterSleep();
   ownerCheck((view.sfrBuild!=null)==before&&view.disposals==disposed,"art-sleep-retains",seed,i,trace,[before,disposed],[view.sfrBuild!=null,view.disposals]);coverage["sleep_retains"]+=1;
   view.fakeMode=Toybox.System.DISPLAY_MODE_HIGH_POWER;view.onExitSleep();}
  ownerCheck(view.creations==allocations&&view.disposals==disposed&&view.steps==steps&&view.completions==complete&&view.restored==restores&&(view.sfrBuild!=null)==build,"art-lease",seed,i,trace,[allocations,disposed,steps,complete,restores,build],[view.creations,view.disposals,view.steps,view.completions,view.restored,view.sfrBuild!=null]);
  ownerCheck(view.context!=null&&view.mapDecision.pointVisible(true),"art-facts",seed,i,trace,true,view.context!=null&&view.mapDecision.pointVisible(true));
 }
 function final(seed,n){var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"art-coverage",seed,n,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);}
}
(:typecheck(false)) function runGeneratedArtLease(firstSeed,seedCount){
 var total=0;for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){var rng=new OwnerRandom(seed);var run=new ArtTrace();var prefix=[4,0,0,5,1,5,1,7,1,3,4,0,1,2,0,1,6];var events=prefix.size()+12+rng.draw(25);
  for(var i=0;i<events;i+=1){var e=i<prefix.size()?prefix[i]:rng.draw(8);run.step(e,seed,i);total+=1;}run.final(seed,events);run.trace.add(8);if(run.build){run.disposed+=1;}run.view.onHide();total+=1;
  ownerCheck(run.view.sfrBuild==null&&run.view.disposals==run.disposed,"art-terminal-release",seed,events,run.trace,[false,run.disposed],[run.view.sfrBuild!=null,run.view.disposals]);pbtCheckViewReleased(run.view,seed,events,run.trace);
  // lastBuild is a fake inspection handle. Its owner back-reference is not a production lease.
  run.view.lastBuild=null;
 }return total;
}
(:test,:typecheck(false)) function generatedArtLease(logger){var n=runGeneratedArtLease(1,32);logger.debug("GENERATED_ART_LEASE seeds=32 events="+n+" fake_decoder=true after_each=true end=true");return true;}

(:test,:typecheck(false)) class PbtWakePorts extends FeedWakePorts {
 var reg=null;var lastAt=null;var online=true;var reminderAt=null;var registrations=[];var attempts=0;var failRegister=false;var logs=0;var deletes=0;
 function registered(){return reg;} function last(){return lastAt;} function connected(){return online;}
 function reminder(cache,now,last){return reminderAt;} function register(next){attempts+=1;if(failRegister){throw new Lang.InvalidValueException("injected registration failure");}reg=next;registrations.add(next);}
 function deleteEvent(){deletes+=1;reg=null;} function log(value){logs+=1;}
}
(:test,:typecheck(false)) class WakeTrace {
 var store;var cache;var ports;var now=1794818604l;var attempt=null;var connected=true;var pending=false;var registered=null;var last=null;var reminder=null;var writes=0;var registerAttempts=0;var registerFailure=false;var logs=0;var success=false;var future=null;var trace=[];
 var coverage={"arm"=>0,"register"=>0,"kept"=>0,"pending"=>0,"offline"=>0,"reminder"=>0,"floor"=>0,"healthy"=>0,"registration_failure"=>0};
 function initialize(){store=new PbtMemoryStore();cache=new NativeTransfer("https://pbt.invalid",store);ports=new PbtWakePorts();}
 function arm(){
  var next=now;if(attempt!=null&&now>=attempt){if(success&&future!=null&&future>now){next=attempt+3600;if(future<next){next=future;}coverage["healthy"]+=1;}else if(!connected&&now<attempt+300){next=attempt+300;}}
  var lastBound=last;if(attempt!=null&&attempt<=now&&(lastBound==null||attempt>lastBound)){lastBound=attempt;}
  if(pending){if(next>now+300){next=now+300;}if(registered!=null){var due=registered>now?registered:now;if(due<next){next=due;}}coverage["pending"]+=1;}
  if(lastBound!=null&&next<lastBound+300){next=lastBound+300;coverage["floor"]+=1;}
  if(reminder!=null&&reminder<next){next=reminder;coverage["reminder"]+=1;}
  var needed=registered==null||registered!=next;
  if(pending&&registered!=null&&registered<=now&&(lastBound==null||(registered>lastBound&&registered>=lastBound+300))){needed=false;}
  if(needed){registerAttempts+=1;if(registerFailure){coverage["registration_failure"]+=1;}else{registered=next;writes+=1;coverage["register"]+=1;}}else{coverage["kept"]+=1;}
  logs+=1;coverage["arm"]+=1;armFeedWithPorts(cache,now,ports);
 }
 function step(e,arg,seed,i){trace.add([e,arg]);
  if(e==0){arm();}
  else if(e==1){now+=arg*100;}
  else if(e==2){connected=!connected;ports.online=connected;if(!connected){coverage["offline"]+=1;}}
  else if(e==3){attempt=now;success=false;cache.attempted(now);}
  else if(e==4){pending=!pending;store.values["sf.batch.pending"]={"base"=>"https://pbt.invalid","pending"=>pending};}
  else if(e==5){last=now-arg*100;ports.lastAt=last;}
  else if(e==6){reminder=now+arg*100;ports.reminderAt=reminder;}
  else if(e==7){reminder=null;ports.reminderAt=null;}
  else if(e==8){if(attempt==null){attempt=now;cache.attempted(now);}future=now+7200;var v=pbtSnapshot(1,future);v[3][14]=future;Test.assert(new NativeTrustedStore(store,"https://pbt.invalid").save(v));cache.completed(true);success=true;}
  else{registerFailure=!registerFailure;ports.failRegister=registerFailure;}
  ownerCheck(ports.reg==registered&&ports.registrations.size()==writes&&ports.attempts==registerAttempts&&ports.logs==logs&&ports.deletes==0,"wake-registration",seed,i,trace,[registered,writes,registerAttempts,logs],[ports.reg,ports.registrations.size(),ports.attempts,ports.logs]);
 }
 function final(seed,n){var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){ownerCheck(coverage[keys[k]]>0,"wake-coverage",seed,n,trace,keys[k],coverage[keys[k]]);}recordCoverage(coverage);}
}
(:typecheck(false)) function runGeneratedWakeOwner(firstSeed,seedCount){
 var total=0;for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){var rng=new OwnerRandom(seed);var run=new WakeTrace();var prefix=[[0,0],[0,0],[9,0],[1,4],[0,0],[9,0],[2,0],[3,0],[4,0],[6,1],[0,0],[1,4],[0,0],[7,0],[8,0],[0,0]];var events=prefix.size()+12+rng.draw(25);
  for(var i=0;i<events;i+=1){var e=0;var arg=0;if(i<prefix.size()){e=prefix[i][0];arg=prefix[i][1];}else{e=rng.draw(10);arg=rng.draw(5);}run.step(e,arg,seed,i);total+=1;}run.final(seed,events);
 }return total;
}
(:test,:typecheck(false)) function generatedWakeOwner(logger){var n=runGeneratedWakeOwner(1,32);logger.debug("GENERATED_WAKE seeds=32 events="+n+" fake_os=true after_each=true end=true");return true;}

// Directed failure permutations supplement arbitrary temporal chains. Each
// branch enters the real service, supplies an independent fault and observes
// terminal effects and retained durable state before a later successful retry.
(:test,:typecheck(false)) class ServiceFailureTrace {
 var service;var fault;var trace=[];
 function initialize(which){fault=which;trace.add(["fault",which]);service=new PbtTemporalService();if(which==0){service.testUrl="";}if(which==1){service.sendFails=true;}if(which==2){service.fakeStore.fail=1;}if(which==3||which==4){service.fakeStore.fail=2;}if(which==4){service.deliveryFails=true;}if(which==5){service.fakeStore.fail=4;}}
 function run(seed,index){
  trace.add("entry");service.onTemporalEvent();
  if(fault==0){ownerCheck(service.sends==0&&service.exits==1&&service.flight.state==0,"service-empty",seed,index,trace,[0,1,0],[service.sends,service.exits,service.flight.state]);service.testUrl="https://pbt.invalid";service.onTemporalEvent();}
  else if(fault==1){ownerCheck(service.sends==1&&service.sent.size()==0&&service.flight.finished(),"service-send-throw",seed,index,trace,[1,0,true],[service.sends,service.sent.size(),service.flight.finished()]);service.sendFails=false;service.onTemporalEvent();}
  ownerCheck(service.flight.state==1&&service.sent.size()==1,"service-request",seed,index,trace,[1,1],[service.flight.state,service.sent.size()]);
  trace.add("response");service.sent[0].invoke(200,{"data"=>pbtSnapshot(1,1795042260l)});
  var saved=new NativeTrustedStore(service.fakeStore,"https://pbt.invalid").load();
  if(fault>=2&&fault<=4){ownerCheck(saved==null&&service.deliveries.size()==1,"service-storage-fail",seed,index,trace,[null,1],[saved,service.deliveries.size()]);var delivered=service.deliveries[0];
   if(fault==4){ownerCheck(delivered["volatileDeliveryFailed"]==true&&service.exits==2,"service-ipc-fail",seed,index,trace,true,delivered);}else{ownerCheck(delivered["volatileSnapshot"] instanceof Array&&service.exits==1,"service-ipc",seed,index,trace,true,delivered);}}
  else{ownerCheck(saved!=null&&saved[3][0].equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"),"service-save",seed,index,trace,true,saved);}
  ownerCheck(service.flight.finished(),"service-terminal",seed,index,trace,true,service.flight.finished());
  var previous=service.sent[0];trace.add("retry");if(fault<2){service.fakeUtc+=3600;service.fakeMillis+=3600000;}service.fakeStore.fail=0;service.deliveryFails=false;service.onTemporalEvent();
  ownerCheck(service.sent.size()==2&&service.flight.state==1,"service-retry",seed,index,trace,[2,1],[service.sent.size(),service.flight.state]);
  previous.invoke(200,{"data"=>pbtSnapshot(2,1795042320l)});ownerCheck(service.flight.state==1,"service-late",seed,index,trace,1,service.flight.state);
  service.sent[1].invoke(200,{"data"=>pbtSnapshot(3,1795042380l)});saved=new NativeTrustedStore(service.fakeStore,"https://pbt.invalid").load();
  ownerCheck(service.flight.finished()&&saved!=null&&saved[1]["generation"]==3,"service-retry-save",seed,index,trace,[true,3],[service.flight.finished(),saved==null?null:saved[1]["generation"]]);recordCoverage({"fault_"+fault=>1});return 4;
 }
}
(:typecheck(false)) function runServiceFailureRegressions(firstSeed,seedCount){
 var total=0;for(var seed=firstSeed;seed<firstSeed+seedCount;seed+=1){var shift=new OwnerRandom(seed).draw(6);for(var j=0;j<6;j+=1){var which=(j+shift)%6;total+=new ServiceFailureTrace(which).run(seed,j);}}return total;
}
(:test,:typecheck(false)) function generatedServiceFailure(logger){Test.assert(runServiceFailureRegressions(1,1)>0);var n=runGeneratedServiceFailure(1,16);logger.debug("GENERATED_SERVICE_FAILURE seeds=16 events="+n+" fake_ports=true after_each=true end=true");return true;}

// Old-source callbacks cannot clear the current source's failure checkpoint.
(:test,:typecheck(false)) function oldSourceCannotClearFailedAdmission(logger){
 var store=new PbtMemoryStore();var disk=new NativeTrustedStore(store,"https://pbt.invalid");Test.assert(disk.save(pbtSnapshot(1,1795042260l)));
 var app=new PbtForegroundApp(store);app.getInitialView();app.performReload();var view=app.view as PbtView;view.onShow();
 Test.assert(disk.save(pbtSnapshot(2,1795042320l)));store.failSlotRead=true;app.performReload();
 Test.assertMessage(app.failedToken!=null,"controlled slot read must establish the failed admission checkpoint");var before=app.failedToken;
 app.onBackgroundData({"base"=>"https://other.invalid","volatileSnapshot"=>pbtSnapshot(3,1795042380l)});
 Test.assertMessage(app.failedToken==before,"old-source delivery must not clear the current admission failure");
 var frames=app.frameRequests;app.onBackgroundData({});
 Test.assertMessage(app.failedToken==before&&app.frameRequests==frames,"duplicate notification must not clear or redraw a failed admission");
 store.failSlotRead=false;Test.assert(disk.save(pbtSnapshot(3,1795042380l)));app.onBackgroundData({});
 Test.assertMessage(app.failedToken==null&&view.context!=null&&view.context.displayTarget==1795042380l,"new durable pointer must still admit facts");return true;
}

(:test,:typecheck(false)) function peerReminderContinuityReplay(logger){
 var actual=runGeneratedReminderOwners(2000330,1);
 var r=new ReminderTrace();var seq=[[0,0],[5,0],[1,660],[0,0],[5,0],[5,0]];
 for(var i=0;i<seq.size();i+=1){r.step(seq[i][0],seq[i][1],2000330,i);}
 Test.assert(r.services.posts.size()==2);Test.assert(r.services.posts[0][0]==0&&r.services.posts[1][0]==2);Test.assert(r.services.posts[0][1]==1794677550l&&r.services.posts[1][1]==1794677550l);
 logger.debug("REMINDER_CONTINUITY exact_seed=2000330 arbitrary_events="+actual+" reduced_events=6 same_target_since_retained=true duplicate_no_post=true");return true;
}
