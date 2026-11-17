import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

(:test,:typecheck(false)) class VolatileService extends SequenceService {
 var delivered=null;function initialize(){SequenceService.initialize();}
 function leave() as Void {exits+=1;delivered=volatileSnapshot;}
}
(:test,:typecheck(false)) class VolatileCountingView extends SpaceFoxView {
 var lowPaints=0;function initialize(){SpaceFoxView.initialize(new WatchClock(),new ScheduleState(null,"empty"));}
 function drawPendingLow(dc){lowPaints+=1;SpaceFoxView.drawPendingLow(dc);}
}
// The SDK service and foreground are separate processes. This generator
// exercises both production owners with a fake transport/storage; actual OS
// serialization and its 8 KiB bound require a separate integration witness.
(:test,:typecheck(false)) function volatileSnapshotSequences(logger){
 var total=0;var base="https://jekamas.github.io/SpaceFox";
 for(var seed=0;seed<8;seed+=1){
  var store=new SequenceStore();var writer=new NativeTrustedStore(store,base);
  var old=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];Test.assert(writer.save(old));
  var app=new SpaceFoxApp();var view=new VolatileCountingView();app.view=view;app.feed=new NativeCache(base,store);view.pendingLoader=app.method(:reloadFeed);view.onShow();app.performReload();view.onEnterSleep();
  var svc=new VolatileService();svc.transfer=new NativeTransfer(base,store);svc.startDeadline();
  var next=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];next[1]["generation"]=57;next[1]["selectionValidatedUtc"]=1794812998l;next[3][15]=1794812998l;next[3][20]=1795042260l;
  var expected=1795042200l;var expectedSlots=1;var expectedPointers=1;var coverage={"start_applied"=>0,"failure_observed_no_mutation"=>0,"delivery_applied"=>0,"late_observed_no_mutation"=>0,"stale_observed_no_mutation"=>0,"wrongSource_observed_no_mutation"=>0,"reopen_observed_no_mutation"=>0,"retry_applied"=>0,"hide_applied"=>0,"show_applied"=>0,"render_applied"=>0};
  var events=["start","failure","hide","delivery","stale","show","render","late","wrongSource","reopen","retry"];
  for(var i=0;i<events.size();i+=1){var event=events[i];
   if(event.equals("start")){svc.request("watch",svc.method(:receiveSnapshot));coverage["start_applied"]+=1;}
   else if(event.equals("failure")){store.failKind=(seed&1)==0?1:2;svc.sent[0].invoke(200,{"data"=>next});store.failKind=0;if((seed&1)==0){expectedSlots+=1;}Test.assert(svc.delivered!=null);coverage["failure_observed_no_mutation"]+=1;}
   else if(event.equals("hide")){var beforeHide=Toybox.Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();view.updateForDisplayMode(beforeHide,Toybox.System.DISPLAY_MODE_LOW_POWER);Test.assert(view.lastLowFrameMinute()!=null);view.onHide();coverage["hide_applied"]+=1;}
   else if(event.equals("delivery")){app.onBackgroundData({"base"=>base,"volatileSnapshot"=>svc.delivered});coverage["delivery_applied"]+=1;}
   else if(event.equals("show")){view.onShow();coverage["show_applied"]+=1;}
   else if(event.equals("render")){var dc=Toybox.Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();var beforePaint=view.lowPaints;view.updateForDisplayMode(dc,Toybox.System.DISPLAY_MODE_LOW_POWER);Test.assert(view.lowPaints>beforePaint);expected=1795042260l;view.updateForDisplayMode(dc,Toybox.System.DISPLAY_MODE_LOW_POWER);var paintedMinute=view.lastLowFrameMinute();var paintedGeneration=view.sceneLifecycle.generation;var paints=view.lowPaints;Test.assert(paintedMinute!=null&&view.lastLowFrameMinute()==paintedMinute);view.updateForDisplayMode(dc,Toybox.System.DISPLAY_MODE_LOW_POWER);Test.assertEqual(view.lastLowFrameMinute(),paintedMinute);Test.assertEqual(view.sceneLifecycle.generation,paintedGeneration);Test.assertEqual(view.lowPaints,paints);coverage["render_applied"]+=1;}
   else if(event.equals("late")){svc.sent[0].invoke(200,{"data"=>old});coverage["late_observed_no_mutation"]+=1;}
   else if(event.equals("stale")){var generation=view.sceneLifecycle.generation;app.onBackgroundData({"base"=>base,"volatileSnapshot"=>old});Test.assertEqual(view.sceneLifecycle.generation,generation);coverage["stale_observed_no_mutation"]+=1;}
   else if(event.equals("wrongSource")){var generation=view.sceneLifecycle.generation;app.onBackgroundData({"base"=>"https://example.invalid","volatileSnapshot"=>next});Test.assertEqual(view.sceneLifecycle.generation,generation);coverage["wrongSource_observed_no_mutation"]+=1;}
   else if(event.equals("reopen")){var restored=new NativeTrustedPacket(new NativeTrustedStore(store,base).load());Test.assert(restored.presentation.displayTarget==1795042200l);app.performReload();coverage["reopen_observed_no_mutation"]+=1;}
   else{Test.assert(writer.save(next));expectedSlots+=1;expectedPointers+=1;app.onBackgroundData({});coverage["retry_applied"]+=1;}
   Test.assert(view.context!=null&&view.context.displayTarget==expected);Test.assert(view.context.pointText[0].equals("111.589567")&&view.context.pointText[1].equals("38.863128"));
   Test.assertEqual(view.displayMode(),view.LOW);Test.assertEqual(store.slots,expectedSlots);Test.assertEqual(store.pointers,expectedPointers);total+=1;
  }
  var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){Test.assertMessage(coverage[keys[k]]>0,"seed="+seed+" missing "+keys[k]);}
  view.onHide();logger.debug("VOLATILE_SEED "+seed+" applied_and_observed=true");
 }
 logger.debug("VOLATILE_GENERATOR seeds=8 events="+total+" after_every_event=true");return true;
}

(:test,:typecheck(false)) class PayloadFailService extends FeedService {
 var sent=null;var calls=0;var outcome=null;
 function initialize(){FeedService.initialize();}
 function nowMillis() as Number {return 0;}
 function sendRequest(path,callback){sent=callback;}
 function rearm() as Void {}
 function deliverBackground(data) as Void {calls+=1;if(data.hasKey("volatileSnapshot")){throw new Toybox.Background.ExitDataSizeLimitException();}outcome=data;}
}
(:test,:typecheck(false)) function volatileDeliveryLimit(logger){
 var base="https://jekamas.github.io/SpaceFox";var store=new SequenceStore();var writer=new NativeTrustedStore(store,base);Test.assert(writer.save(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]));
 var service=new PayloadFailService();service.transfer=new NativeTransfer(base,store);service.startDeadline();service.request("watch",service.method(:receiveSnapshot));
 var newer=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];newer[3][20]=1795042260l;store.failKind=2;service.sent.invoke(200,{"data"=>newer});store.failKind=0;
 Test.assertEqual(service.calls,2);Test.assert(service.outcome["volatileDeliveryFailed"]==true&&service.volatileSnapshot==null);Test.assert(new NativeTrustedPacket(writer.load()).presentation.displayTarget==1795042200l);
 logger.debug("IPC_LIMIT failure_event=true pointer_unchanged=true single_payload=true");return true;
}

(:test,:typecheck(false)) function networkFailureRetainsMap(logger){
 var base="https://jekamas.github.io/SpaceFox";var store=new SequenceStore();var writer=new NativeTrustedStore(store,base);Test.assert(writer.save(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]));
 var app=new SpaceFoxApp();var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));app.view=view;app.feed=new NativeCache(base,store);view.onShow();app.performReload();view.onEnterSleep();
 var service=new VolatileService();service.transfer=new NativeTransfer(base,store);service.startDeadline();service.request("watch",service.method(:receiveSnapshot));service.sent[0].invoke(503,null);app.onBackgroundData({});
 Test.assert(view.context!=null&&view.context.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60")&&view.context.displayTarget==1795042200l);
 Test.assert(view.mapDecision.pointVisible(view.visible())&&view.mapDecision.identity.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));Test.assertEqual(view.displayMode(),view.LOW);Test.assertEqual(service.sent.size(),1);Test.assertEqual(service.exits,1);view.onHide();
 logger.debug("NETWORK_FAILURE prior_facts=true point=true low=true no_duplicate_request=true");return true;
}

// Every seed exercises a complete pre-view or hidden delivery with a durable
// predecessor; both OS show/sleep orders are represented. Expected facts come
// from the literal input sequence, not the cache being tested.
(:test,:typecheck(false)) function volatileBeforeViewSequences(logger){
 var base="https://jekamas.github.io/SpaceFox";var eventsTotal=0;
 for(var seed=0;seed<8;seed+=1){
  var store=new SequenceStore();var writer=new NativeTrustedStore(store,base);var old=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];Test.assert(writer.save(old));
  var next=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];next[1]["generation"]=57;next[1]["selectionValidatedUtc"]=1794812998l;next[3][15]=1794812998l;next[3][20]=1795042260l;
  var app=new SpaceFoxApp();app.feed=new NativeCache(base,store);var expected=null;var shown=false;var created=false;var delivered=false;
  var coverage={"delivery_applied"=>0,"create_applied"=>0,"bootstrap_applied"=>0,"show_applied"=>0,"sleep_applied"=>0,"frame_applied"=>0,"stale_observed_no_mutation"=>0};
  var events=(seed&1)==0?["delivery","create","bootstrap","show","sleep","frame","stale"]:["create","bootstrap","delivery","sleep","show","frame","stale"];
  for(var i=0;i<events.size();i+=1){var event=events[i];
   if(event.equals("delivery")){app.onBackgroundData({"base"=>base,"volatileSnapshot"=>next});delivered=true;coverage["delivery_applied"]+=1;}
   else if(event.equals("create")){app.getInitialView();created=true;coverage["create_applied"]+=1;}
   else if(event.equals("bootstrap")){app.performReload();expected=1795042200l;coverage["bootstrap_applied"]+=1;}
   else if(event.equals("show")){app.view.onShow();shown=true;coverage["show_applied"]+=1;}
   else if(event.equals("sleep")){app.view.onEnterSleep();coverage["sleep_applied"]+=1;}
   else if(event.equals("frame")){var dc=Toybox.Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();app.view.updateForDisplayMode(dc,Toybox.System.DISPLAY_MODE_LOW_POWER);expected=1795042260l;app.view.updateForDisplayMode(dc,Toybox.System.DISPLAY_MODE_LOW_POWER);coverage["frame_applied"]+=1;}
   else{var before=app.view.sceneLifecycle.generation;app.onBackgroundData({"base"=>base,"volatileSnapshot"=>old});Test.assertEqual(app.view.sceneLifecycle.generation,before);coverage["stale_observed_no_mutation"]+=1;}
   if(created){Test.assertEqual(app.view.visible(),shown);if(expected==null){Test.assert(app.view.context==null);}else{Test.assert(app.view.context!=null&&app.view.context.displayTarget==expected&&app.view.context.pointText[0].equals("111.589567"));}}
   else{Test.assert(app.view==null);}
   Test.assertEqual(store.pointers,1);if(delivered&&(!event.equals("frame")&&expected!=1795042260l)){Test.assert(app.feed.pendingVolatile!=null);}eventsTotal+=1;
  }
  var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){Test.assertMessage(coverage[keys[k]]>0,"pre-view seed="+seed+" missing "+keys[k]);}
  app.view.onHide();logger.debug("VOLATILE_PREVIEW_SEED "+seed+" effective=true");
 }
 logger.debug("VOLATILE_PREVIEW seeds=8 events="+eventsTotal+" two_causal_orders=true");return true;
}

// A queued event can become obsolete while hidden bootstrap admits a newer
// durable publication. Consumption must reject it before cancelling art.
(:test,:typecheck(false)) function queuedVolatileObsolete(logger){
 var base="https://jekamas.github.io/SpaceFox";var store=new SequenceStore();var writer=new NativeTrustedStore(store,base);
 var queued=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];queued[1]["generation"]=57;queued[1]["selectionValidatedUtc"]=1794812998l;
 var durable=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];durable[1]["generation"]=58;durable[1]["selectionValidatedUtc"]=1794812999l;durable[3][20]=1795042320l;
 var app=new SpaceFoxApp();app.feed=new NativeCache(base,store);app.view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
 app.onBackgroundData({"base"=>base,"volatileSnapshot"=>queued});Test.assert(writer.save(durable));app.performReload();app.view.onShow();
 Test.assert(app.view.sceneLifecycle.request(1));var token=app.view.sceneLifecycle.begin();var generation=app.view.sceneLifecycle.generation;
 app.performReload();Test.assertEqual(app.view.sceneLifecycle.generation,generation);Test.assert(app.view.sceneLifecycle.pending()&&app.view.sceneLifecycle.job.token==token);
 Test.assert(app.feed.pendingVolatile==null&&app.view.packet==app.feed.packet&&app.view.context.displayTarget==1795042320l);app.view.onHide();
 logger.debug("QUEUED_STALE newer_durable_retained=true art_cancel=0 consumed_once=true");return true;
}
