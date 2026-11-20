import Toybox.Lang;
import Toybox.System;
import Toybox.Test;

(:test,:typecheck(false)) class OffLowView extends PbtView {
 var aodPreparations=0;var loads=0;var pointSeen=false;var timerSeen="";
 function initialize(){PbtView.initialize();}
 function prepareOptionalAod() as Void {aodPreparations+=1;}
 function loadOnce() as Void {loads+=1;}
 function drawPendingLow(dc){pointSeen=mapDecision.pointVisible(true);timerSeen=snapshotAt(clock.now).lowCountdown;PbtView.drawPendingLow(dc);}
}
(:test,:typecheck(false)) function offToLowReentersAod(logger) {
 var view=new OffLowView();view.onShow();view.fakeMode=System.DISPLAY_MODE_LOW_POWER;view.onEnterSleep();
 var before=view.aodPreparations;view.fakeMode=System.DISPLAY_MODE_OFF;view.syncDisplayMode(view.fakeMode);
 view.fakeMode=System.DISPLAY_MODE_LOW_POWER;view.syncDisplayMode(view.fakeMode);
 Test.assertMessage(view.aodPreparations>before,"OFF to LOW must re-enter AOD and restore its resources");view.onHide();return true;
}

// The model receives only visibility, OS observations, callbacks and logical
// frame events. It never reads the SUT state to choose an expected result.
(:test,:typecheck(false)) function offLowEventSequences(logger) {
 var total=0;var offNo=0;var hiddenNo=0;var lowPaint=0;var sameNo=0;var offLow=0;var wakeEvents=0;
 for(var seed=1;seed<=24;seed+=1){
  var startOff=offNo;var startHidden=hiddenNo;var startPaint=lowPaint;var startSame=sameNo;var startOffLow=offLow;var startWake=wakeEvents;
  var rng=new OwnerRandom(seed);var view=new PbtView();var dc=new PbtGraphics();
  var visible=false;var os=1;var state=0;var minute=null;var initial=true;var trace=[];
  var prefix=[0,2,4,6,2,5,6,6,6,3,7,6,1,5,6,0,6];var count=prefix.size()+24+rng.draw(25);
  for(var i=0;i<count;i+=1){
   var e=i<prefix.size()?prefix[i]:rng.draw(8);trace.add(e);
   var beforePaint=view.lowFrames+view.fallbackFrames;var beforeRead=view.fitnessCalls+view.lowSnapshots;
   if(e==0){if(!visible){visible=true;state=3;minute=null;var next=os==2?3:(os==1?2:1);if(state!=next){state=next;minute=null;}}view.onShow();}
   else if(e==1){if(visible){visible=false;state=0;minute=null;}view.onHide();}
   else if(e==2){os=2;view.fakeMode=System.DISPLAY_MODE_OFF;}
   else if(e==3){os=1;view.fakeMode=System.DISPLAY_MODE_HIGH_POWER;}
   else if(e==4){var next=os==2?3:(os==1?2:1);if(visible&&state!=next){if(state==3&&next==1){offLow+=1;}state=next;minute=null;}view.onEnterSleep();}
   else if(e==5){os=0;view.fakeMode=System.DISPLAY_MODE_LOW_POWER;}
   else if(e==7){var next=os==2?3:(os==1?2:1);if(visible&&state!=next){if(state==3&&next==1){offLow+=1;}state=next;minute=null;}wakeEvents+=1;view.onExitSleep();}
   else {var next=os==2?3:(os==1?2:1);if(visible&&state!=next){if(state==3&&next==1){offLow+=1;}state=next;minute=null;}var wasLow=view.lowFrames;var expectedPaint=0;
    if(!visible){hiddenNo+=1;}else if(state==3){offNo+=1;}else if(state==1){var m=(view.clock.now/60).toLong();if(minute==m){sameNo+=1;}else{minute=m;lowPaint+=1;expectedPaint=1;if(initial){initial=false;minute=null;}}}
    view.onUpdate(dc);ownerCheck(view.lowFrames-wasLow==expectedPaint,"off-low-paint",seed,i,trace,expectedPaint,view.lowFrames-wasLow);
   }
   if(!visible||state==3){ownerCheck(view.lowFrames+view.fallbackFrames==beforePaint&&view.fitnessCalls+view.lowSnapshots==beforeRead,"off-hidden-work",seed,i,trace,0,view.lowFrames+view.fallbackFrames-beforePaint);}
   var expected=state==2?1:(state==3?-1:0);ownerCheck(view.visible()==visible&&view.displayMode()==expected&&view.lastLowFrameMinute()==minute,"off-low-model",seed,i,trace,[visible,os,state,minute],[view.visible(),view.displayMode(),view.lastLowFrameMinute()]);total+=1;
  }
  ownerCheck(offNo>startOff&&hiddenNo>startHidden&&lowPaint>startPaint&&sameNo>startSame&&offLow>startOffLow&&wakeEvents>startWake,"off-low-required-per-seed",seed,count,trace,true,[offNo-startOff,hiddenNo-startHidden,lowPaint-startPaint,sameNo-startSame,offLow-startOffLow]);view.onHide();pbtCheckViewReleased(view,seed,count,trace);
 }
 Test.assert(offNo>0&&hiddenNo>0&&lowPaint>0&&sameNo>0&&offLow>0);logger.debug("OFF_LOW seeds=24 events="+total+" off_no="+offNo+" hidden_no="+hiddenNo+" low_paint="+lowPaint+" same_no="+sameNo+" off_low="+offLow+" wake="+wakeEvents);return true;
}

(:test,:typecheck(false)) function offLateSettingsAndFirstFrame(logger) {
 var view=new OffLowView();var dc=new PbtGraphics();view.pendingLoader=view.method(:loadOnce);view.onShow();
 view.fakeMode=System.DISPLAY_MODE_OFF;view.syncDisplayMode(view.fakeMode);var before=view.updates;var reads=view.fitnessCalls+view.lowSnapshots;
 view.setSettings(new SceneSettings(null));view.fieldsChanged(new Toybox.Complications.Id(2));view.onUpdate(dc);
 Test.assertMessage(view.updates==before&&view.fitnessCalls+view.lowSnapshots==reads&&view.loads==0&&view.lowFrames==0,"OFF may not schedule, sample, load or paint");
 view.fakeMode=System.DISPLAY_MODE_LOW_POWER;view.onUpdate(dc);Test.assertMessage(view.lowFrames==1&&view.lowSnapshots==1&&view.loads==1,"first LOW frame consumes one cold snapshot and pending loader");
 view.onUpdate(dc);Test.assert(view.lowFrames==2);view.onUpdate(dc);Test.assertMessage(view.lowFrames==2&&view.lowSnapshots==1&&view.loads==1,"same minute quiesces after one data invalidation");
 view.fakeMode=System.DISPLAY_MODE_HIGH_POWER;view.onEnterSleep();Test.assertMessage(view.displayMode()==1,"OS HIGH before late sleep callback remains ACTIVE");
 view.onHide();before=view.updates;reads=view.fitnessCalls+view.lowSnapshots;view.fieldsChanged(new Toybox.Complications.Id(2));view.onUpdate(dc);Test.assert(view.updates==before&&view.fitnessCalls+view.lowSnapshots==reads);return true;
}

(:test,:typecheck(false)) function lowPointRetainedAcrossLifecycle(logger) {
 var v=new OffLowView();var dc=new PbtGraphics();var scene=new SceneContext({"id"=>"simulated:launch","point"=>[-120.61,34.63],"site"=>"Vandenberg","target"=>1794819000,"displayTarget"=>1794819000,"precision"=>"exact"});
 v.setContext(scene);v.fakeMode=System.DISPLAY_MODE_LOW_POWER;v.onShow();v.onUpdate(dc);
 Test.assertMessage(v.pointSeen&&v.mapDecision.pointVisible(true)&&!v.timerSeen.equals("--:--"),"cold LOW retains qualified point and countdown");
 v.onHide();v.onShow();v.pointSeen=false;v.onUpdate(dc);Test.assert(v.pointSeen&&v.mapDecision.pointVisible(true));
 v.fakeMode=System.DISPLAY_MODE_OFF;v.syncDisplayMode(v.fakeMode);v.fakeMode=System.DISPLAY_MODE_LOW_POWER;v.pointSeen=false;v.onUpdate(dc);Test.assert(v.pointSeen&&v.mapDecision.pointVisible(true));
 v.beginAdmission();v.clock.now+=60;v.pointSeen=false;v.onUpdate(dc);Test.assertMessage(v.pointSeen&&v.mapDecision.pointVisible(true),"admission fallback retains qualified point");
 v.admissionPending=false;v.setContext(new SceneContext({"id"=>"simulated:unknown"}));v.onUpdate(dc);Test.assertMessage(!v.mapDecision.pointVisible(true),"unknown coordinates cannot invent a point");v.onHide();
 logger.debug("LOW_POINT cold menu OFF_LOW admission=true unknown=false; draw intent with actual map owner");return true;
}
