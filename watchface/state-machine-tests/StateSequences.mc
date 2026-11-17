import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;
(:test,:typecheck(false)) class SequenceService extends FeedService {
 var sent=[];var accepted=[];var clock=0;
 function initialize(){FeedService.initialize();}
 function nowMillis() as Number {return clock;}
 function sendRequest(path,cb){sent.add(cb);}
 function received(code,data){if(callbackAllowed()){accepted.add(data);}}
 function rearm() as Void {}
 function leave() as Void {}
 function cancelOutstanding() as Void {}
}
// Generator exercises the real service, while the expected accepted sequence is
// constructed independently from the events and never read from the service.
(:typecheck(false)) function sameAccepted(service,expected){Test.assertEqual(service.accepted.size(),expected.size());for(var n=0;n<expected.size();n+=1){Test.assert(service.accepted[n].equals(expected[n]));}}
(:test,:typecheck(false)) function requestEventSequences(logger){
 var coverage={"start_applied"=>0,"start_observed_no_mutation"=>0,"response_applied"=>0,"response_observed_no_mutation"=>0,"finish_applied"=>0,"finish_observed_no_mutation"=>0,"advance_applied"=>0};
 var totalEvents=0;
 // Every mask generates a different ordered trace. No SUT value feeds the
 // reference transition table below; sent Methods are only delivery handles.
 for(var mask=0;mask<8;mask+=1){
  logger.debug("REQUEST_TRACE_SEED mask="+mask);var s=new SequenceService();s.startDeadline();
  var events=[["start","a"],["start","duplicate"],["response",0,200,"a"],["response",0,200,"duplicate"],["start","b"],["response",0,200,"late"]];
  if((mask&1)!=0){events.add(["advance",250]);}
  if((mask&2)!=0){events.add(["finish"]);}
  events.add(["response",1,(mask&4)!=0?503:200,(mask&4)!=0?"failure":"b"]);
  events.add(["response",1,200,"duplicate-b"]);events.add(["finish"]);events.add(["finish"]);events.add(["start","after-finish"]);
  var state=0;var active=-1;var sent=0;var expected=[];var logical=0;
  for(var i=0;i<events.size();i+=1){var e=events[i];var name=e[0];var disposition="observed_no_mutation";
   if(name.equals("start")){if(state==0){active=sent;sent+=1;state=1;disposition="applied";}s.request(e[1],s.method(:received));}
   else if(name.equals("response")){if(state==1&&e[1]==active){state=0;expected.add(e[3]);disposition="applied";}s.sent[e[1]].invoke(e[2],e[3]);}
   else if(name.equals("finish")){if(state!=2){state=2;disposition="applied";}s.finish();}
   else{logical+=e[1];s.clock=logical;disposition="applied";}
   var key=name+"_"+disposition;coverage[key]=coverage[key]+1;totalEvents+=1;
   Test.assertEqual(s.sent.size(),sent);sameAccepted(s,expected);Test.assertEqual(s.flight.canStart(),state==0);Test.assertEqual(s.flight.finished(),state==2);
  }
 }
 var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){Test.assertMessage(coverage[keys[k]]>0,"missing disposition: "+keys[k]);logger.debug("REQUEST_COVERAGE "+keys[k]+"="+coverage[keys[k]]);}
 logger.debug("REQUEST_GENERATOR seeds=8 events="+totalEvents+" oracle=after_every_event");return true;
}
(:test,:typecheck(false)) class SequenceStore {
 var data={};var failKind=0;var slots=0;var pointers=0;
 function read(key){return data[key];}
 function write(key,value){if(failKind==3&&key.find("sf.queue:")==0){throw new Lang.InvalidValueException("queue checkpoint failure");}if(failKind==1&&key.find("sf.snapshot.active:")==0){throw new Lang.InvalidValueException("pointer failure");}if(failKind==2&&(key.find("sf.snapshot.0:")==0||key.find("sf.snapshot.1:")==0)){throw new Lang.InvalidValueException("slot failure");}if(key.find("sf.snapshot.active:")==0){pointers+=1;}else if(key.find("sf.snapshot.0:")==0||key.find("sf.snapshot.1:")==0){slots+=1;}data[key]=value;}
}
(:test,:typecheck(false)) function cacheEventSequences(logger){
 var base="https://jekamas.github.io/SpaceFox";var ids=["ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60","ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"];
 var successes=0;var interruptions=0;var reopens=0;
 for(var seed=0;seed<8;seed+=1){logger.debug("CACHE_TRACE_SEED "+seed);var store=new SequenceStore();var owner=new NativeTrustedStore(store,base);var expected=null;var slots=0;var pointers=0;
  var events=["first","reopen","candidate","reopen","retry","reopen"];
  for(var n=0;n<events.size();n+=1){var event=events[n];
   if(event.equals("first")){Test.assert(owner.save(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]));expected=ids[0];slots+=1;pointers+=1;successes+=1;}
   else if(event.equals("candidate")){var fail=seed%3;store.failKind=fail;try{owner.save(WatchUi.loadResource(Rez.JsonData.Exact)["payload"]);}catch(e){}store.failKind=0;if(fail==0){expected=ids[1];slots+=1;pointers+=1;successes+=1;}else{interruptions+=1;if(fail==1){slots+=1;}}}
   else if(event.equals("retry")){Test.assert(owner.save(WatchUi.loadResource(Rez.JsonData.Exact)["payload"]));expected=ids[1];slots+=1;pointers+=1;successes+=1;}
   else{owner=new NativeTrustedStore(store,base);reopens+=1;}
   var actual=new NativeTrustedPacket(owner.load());Test.assert(actual.presentation.launchId.equals(expected)&&actual.presentation.point!=null);Test.assertEqual(store.slots,slots);Test.assertEqual(store.pointers,pointers);
  }
 }
 Test.assert(successes>0&&interruptions>0&&reopens>0);logger.debug("CACHE_GENERATOR seeds=8 events=48 commit="+successes+" observed_no_mutation="+interruptions+" reopen="+reopens+" oracle=after_every_event");return true;
}
(:test,:typecheck(false)) function lowBackgroundDelivery(logger){
 var base="https://jekamas.github.io/SpaceFox";var store=new SequenceStore();var owner=new NativeTrustedStore(store,base);Test.assert(owner.save(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]));
 var app=new SpaceFoxApp();var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));app.view=view;app.feed=new NativeCache(base,store);view.onShow();app.performReload();
 Test.assert(view.context!=null&&view.context.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));
 view.onEnterSleep();Test.assertEqual(view.displayMode(),view.LOW);var replacement=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];replacement[3][20]=1795042260l;Test.assert(owner.save(replacement));app.onBackgroundData({});
 Test.assertMessage(view.context!=null&&view.context.displayTarget==1795042260l,"new committed facts must bind while sleeping");Test.assert(view.context.point!=null&&view.displayMode()==view.LOW);view.onHide();logger.debug("LOW background commit binds current point without changing mode");return true;
}

// OS event sequences are applied to the actual production view. The reference
// table uses only the input event and simulator HIGH mode, not view internals.
(:test,:typecheck(false)) function displayEventSequences(logger){
 var applied=0;var unchanged=0;var rendered=0;var callbacks=0;
 for(var seed=0;seed<8;seed+=1){logger.debug("DISPLAY_TRACE_SEED "+seed);var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));var shown=false;var sleeping=false;var now=1794818604l;
  var words=["show","show","sleep","sleep","time","callback","render","wake","wake","hide","hide"];
  if((seed&1)!=0){words.add("show");words.add("hide");}
  var service=new SequenceService();service.startDeadline();service.request("x",service.method(:received));var dc=Toybox.Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
  for(var j=0;j<words.size();j+=1){var event=words[j];var change=false;
   if(event.equals("show")){change=!shown;shown=true;view.onShow();}else if(event.equals("hide")){change=shown;shown=false;view.onHide();}else if(event.equals("sleep")){change=!sleeping;sleeping=true;view.onEnterSleep();}else if(event.equals("wake")){change=sleeping;sleeping=false;view.onExitSleep();}else if(event.equals("time")){now+=1;view.snapshotAt(now);}else if(event.equals("callback")){service.sent[0].invoke(200,"ok");callbacks+=1;}else{view.updateForDisplayMode(dc,Toybox.System.DISPLAY_MODE_LOW_POWER);rendered+=1;}
   if(change){applied+=1;}else{unchanged+=1;}var expected=shown&&!sleeping?1:0;Test.assertEqual(view.displayMode(),expected);
  }
 }
 Test.assert(applied>0&&unchanged>0&&rendered>0&&callbacks>0);logger.debug("DISPLAY_GENERATOR seeds=8 applied="+applied+" observed_no_mutation="+unchanged+" render="+rendered+" callback="+callbacks+" oracle=after_every_event");return true;
}
(:test,:typecheck(false)) function artworkEventSequences(logger){
 var applied=0;var ignored=0;
 for(var seed=0;seed<8;seed+=1){logger.debug("ART_TRACE_SEED "+seed);var owner=new SceneLifecycle();var state=0;var first=null;var second=null;
  var events=["request","begin",(seed&1)!=0?"cancel":"fail","late","request2","begin2","complete","replace","late2"];
  for(var i=0;i<events.size();i+=1){var event=events[i];
   if(event.equals("request")){Test.assert(owner.request(1));state=1;applied+=1;}
   else if(event.equals("begin")){first=owner.begin();Test.assertEqual(first,0);applied+=1;}
   else if(event.equals("cancel")){owner.cancel();state=0;applied+=1;}
   else if(event.equals("fail")){owner.fail(first);state=0;applied+=1;}
   else if(event.equals("late")){Test.assert(!owner.complete(first));ignored+=1;}
   else if(event.equals("request2")){Test.assert(owner.request(2));state=1;applied+=1;}
   else if(event.equals("begin2")){second=owner.begin();Test.assertEqual(second,1);applied+=1;}
   else if(event.equals("complete")){Test.assert(owner.complete(second));state=2;applied+=1;}
   else if(event.equals("replace")){owner.replace();state=0;applied+=1;}
   else{Test.assert(!owner.complete(second));ignored+=1;}
   Test.assertEqual(owner.presentationState,state);
  }
 }
 Test.assert(applied>0&&ignored>0);logger.debug("ART_GENERATOR seeds=8 events=72 applied="+applied+" observed_no_mutation="+ignored+" oracle=after_every_event");return true;
}
(:test,:typecheck(false)) function cadenceEventSequences(logger){
 var changed=0;var unchanged=0;var checks=0;
 for(var seed=0;seed<8;seed+=1){logger.debug("CADENCE_TRACE_SEED "+seed);var base="https://jekamas.github.io/SpaceFox";var store=new SequenceStore();var snapshot=new NativeTrustedStore(store,base);var payload=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];var future=(seed&1)==0;
  if(!future){payload[3]=null;payload[4]=[];}Test.assert(snapshot.save(payload));var owner=new NativeTransfer(base,store);var now=1794818604l;var last=null;var success=false;var connected=true;
  var events=[["attempt"],["success"],["advance",3599],["disconnect"],["disconnect"],["advance",1],["connect"],["connect"],["attempt"],["failure"],["disconnect"],["advance",299],["advance",1],["connect"]];
  for(var i=0;i<events.size();i+=1){var event=events[i];var kind=event[0];
   if(kind.equals("attempt")){owner.attempted(now);last=now;success=false;}
   else if(kind.equals("success")){owner.completed(true);success=true;}
   else if(kind.equals("failure")){owner.completed(false);success=false;}
   else if(kind.equals("advance")){now+=event[1];}
   else{var next=kind.equals("connect");if(next==connected){unchanged+=1;}else{changed+=1;}connected=next;}
   var due=last==null||now<last||(success&&future?now>=last+3600:(connected||now>=last+300));Test.assertEqual(owner.due(now,connected),due);checks+=1;
  }
 }
 Test.assert(changed>0&&unchanged>0);logger.debug("CADENCE_GENERATOR seeds=8 events="+checks+" connection_applied="+changed+" connection_observed_no_mutation="+unchanged+" oracle=after_every_event");return true;
}
// First delivery while already LOW uses the production app/view and a fake
// storage adapter; it does not claim a physical sleep or phone observation.
(:test,:typecheck(false)) function lowFirstDeliveryFrame(logger){
 var base="https://jekamas.github.io/SpaceFox";var store=new SequenceStore();var app=new SpaceFoxApp();var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
 app.view=view;app.feed=new NativeCache(base,store);view.bootstrapPending=true;view.pendingLoader=app.method(:reloadFeed);view.onShow();view.onEnterSleep();
 Test.assert(view.context==null);var owner=new NativeTrustedStore(store,base);Test.assert(owner.save(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]));app.onBackgroundData({});
 Test.assert(view.context!=null&&view.context.point!=null&&view.context.displayTarget==1795042200l);Test.assertEqual(view.displayMode(),0);
 var dc=Toybox.Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();view.updateForDisplayMode(dc,Toybox.System.DISPLAY_MODE_LOW_POWER);
 var frame=view.snapshotAt(1794818604l);Test.assert(frame.lowCountdown.find("T-")==0&&view.context.point!=null);Test.assertEqual(view.displayMode(),0);view.onHide();
 logger.debug("LOW first delivery: normal LOW draw with point and target; no ACTIVE event between delivery and frame");return true;
}
(:test,:typecheck(false)) function lateResponseAcrossSleep(logger){
 var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));view.onShow();var service=new SequenceService();service.startDeadline();service.request("first",service.method(:received));var old=service.sent[0];
 view.onEnterSleep();old.invoke(200,"first");Test.assertEqual(service.accepted.size(),1);service.request("second",service.method(:received));view.onExitSleep();old.invoke(200,"stale");Test.assertEqual(service.accepted.size(),1);service.sent[1].invoke(200,"second");Test.assertEqual(service.accepted.size(),2);Test.assert(service.accepted[1].equals("second"));view.onHide();return true;
}
// One connected domain trace checks the reference state after every event.
// Dependency counters observe actual production writes and request dispatches.
(:test,:typecheck(false)) function connectedEventTrace(logger){
 var events=["show","sleep","request","duplicate-start","commit","render","time","response","wake","late","hide"];
 var covered={};var base="https://jekamas.github.io/SpaceFox";var store=new SequenceStore();var app=new SpaceFoxApp();var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));app.view=view;app.feed=new NativeCache(base,store);
 var service=new SequenceService();service.startDeadline();var target=null;var mode=0;var sent=0;var slotWrites=0;var pointerWrites=0;var current=1794818604l;var callback=null;
 for(var i=0;i<events.size();i+=1){var event=events[i];covered[event]=true;
  if(event.equals("show")){view.onShow();mode=1;}
  else if(event.equals("sleep")){view.onEnterSleep();mode=0;}
  else if(event.equals("request")){service.request("schedule",service.method(:received));callback=service.sent[0];sent=1;}
  else if(event.equals("duplicate-start")){service.request("duplicate",service.method(:received));}
  else if(event.equals("commit")){var owner=new NativeTrustedStore(store,base);Test.assert(owner.save(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]));slotWrites=1;pointerWrites=1;target=1795042200l;app.onBackgroundData({});}
  else if(event.equals("render")){var dc=Toybox.Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();view.updateForDisplayMode(dc,Toybox.System.DISPLAY_MODE_LOW_POWER);}
  else if(event.equals("time")){current+=1;}
  else if(event.equals("response")){callback.invoke(200,"success");}
  else if(event.equals("wake")){view.onExitSleep();mode=1;}
  else if(event.equals("late")){callback.invoke(200,"duplicate");}
  else if(event.equals("hide")){view.onHide();mode=0;}
  Test.assertEqual(view.displayMode(),mode);Test.assertEqual(service.sent.size(),sent);Test.assertEqual(store.slots,slotWrites);Test.assertEqual(store.pointers,pointerWrites);
  if(target==null){Test.assert(view.context==null);}else{Test.assert(view.context!=null&&view.context.displayTarget==target&&view.context.point!=null);var text=view.snapshotAt(current).countdown;Test.assert(text.equals(current==1794818604l?"T- 62:06:36":"T- 62:06:35"));}
 }
 for(var j=0;j<events.size();j+=1){Test.assert(covered[events[j]]);}Test.assertEqual(service.accepted.size(),1);
 logger.debug("TRACE show/sleep/request/duplicate/commit/render/time/response/wake/late/hide: oracle checked after each event");return true;
}

(:test,:typecheck(false)) function queueFailureStillBinds(logger){
 var base="https://jekamas.github.io/SpaceFox";var store=new SequenceStore();var owner=new NativeTrustedStore(store,base);var app=new SpaceFoxApp();var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));app.view=view;app.feed=new NativeCache(base,store);view.onShow();
 Test.assert(owner.save(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]));app.performReload();Test.assert(view.context!=null&&view.context.displayTarget==1795042200l);
 var replacement=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];replacement[3][20]=1795042260l;Test.assert(owner.save(replacement));store.failKind=3;app.performReload();
 Test.assert(view.context!=null&&view.context.displayTarget==1795042260l&&view.context.point!=null);view.onHide();logger.debug("queue checkpoint failure does not block a committed newer snapshot");return true;
}
