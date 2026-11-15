import Toybox.Lang;
import Toybox.Complications;
import Toybox.Graphics;
import Toybox.System;
import Toybox.Test;

// Fitness is compiled from the production body with only Garmin module
// references mapped to the counting API fake in MetricBoundary.mc.
(:test,:typecheck(false)) function display03MetricRolesAndAge(logger){
 var f=new BoundaryFitness();f.selectedRoles=["energy","energy","battery","calories"];f.currentBodyBattery=68;
 MetricSDK.reset(0);var atLimit=f.sample(1800000300);
 Test.assert(atLimit["energy"]==68&&atLimit["battery"]==82&&atLimit["calories"]==2345);
 Test.assert(atLimit["heart"]==null&&atLimit["stress"]==null);
 Test.assert(traceEquals(["activity.info","system.stats"]));
 MetricSDK.reset(0);var aged=f.sample(1800000301);Test.assert(aged["energy"]==68&&f.recentValue(72,1800000000,1800000301,300,true)==null);
 f.currentBodyBattery=null;MetricSDK.reset(3);var absent=f.sample(1800000000);Test.assert(absent["energy"]==null);
 MetricSDK.reset(1);var denied=f.sample(1800000000);Test.assert(denied["energy"]==null);
 f.currentBodyBattery=68;MetricSDK.reset(0);var fresh=f.sample(1800000000);Test.assert(fresh["energy"]==68);
 f.selectedRoles=["heart","heart","heart","heart"];MetricSDK.reset(0);f.sample(1800000000);
 Test.assert(traceEquals(["heart.open","heart.next"]));
 f.selectedRoles=[];MetricSDK.reset(0);f.sample(1800000000);Test.assert(traceEquals([]));
 Test.assert(f.recentValue(0,1800000000,1800000000,100,false)==0);
 logger.debug("METRIC_ROLE duplicate=one historyAgeBound=unchanged energy=currentComplication absent=unavailable fresh=restored");return true;
}
(:test,:typecheck(false)) class D03CountFitness extends Fitness {
 var calls=0;function initialize(){Fitness.initialize();}
 function sample(now){calls+=1;return {"steps"=>null,"calories"=>null,"battery"=>null,"heart"=>null,"energy"=>currentBodyBattery,"stress"=>null};}
}
(:test,:typecheck(false)) function display03LowDoesNotSample(logger){
 var v=new SpaceFoxView(new Display03Clock(),new ScheduleState(null,"empty"));var f=new D03CountFitness();v.fitness=f;
 v.onEnterSleep();v.refreshFitness();Test.assert(f.calls==0);v.onHide();return true;
}
(:test,:typecheck(false)) function display03OffStopsWork(logger){
 var v=new SpaceFoxView(new Display03Clock(),new ScheduleState(null,"empty"));var f=new D03CountFitness();v.fitness=f;
 var d=new Display03ModeRenderer();v.renderer=d;v.onShow();Test.assert(v.sceneLifecycle.request(1));
 var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();var loads=d.resourceLoads;
 v.updateForDisplayMode(dc,System.DISPLAY_MODE_OFF);Test.assert(d.activeCalls==0&&d.lowCalls==0&&f.calls==0&&d.resourceLoads==loads&&!v.sceneLifecycle.pending());
 var generation=v.sceneLifecycle.generation;v.updateForDisplayMode(dc,System.DISPLAY_MODE_OFF);Test.assert(v.sceneLifecycle.generation==generation&&d.resourceLoads==loads);
 v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assert(d.activeCalls==1&&f.calls==0);v.onHide();
 logger.debug("OFF noPaintOrSampling=true cancelOnce=true highFirstFrameBeforeSampling=true");return true;
}

(:test,:typecheck(false)) class D03FakeBody extends BodyBatterySource {
 var starts=0;var reads=0;var stops=0;var next=68;
 function start(callback){if(!subscribed){starts+=1;subscribed=true;}return true;}
 function read(){reads+=1;observed=true;value=next;return value;}
 function stop(){if(subscribed){stops+=1;}subscribed=false;observed=false;value=null;}
}
(:test,:typecheck(false)) function display03CurrentBodyBatteryLifecycle(logger){
 var clock=new Display03Clock();var v=new SpaceFoxView(clock,new ScheduleState(null,"empty"));var body=new D03FakeBody();v.bodyBattery=body;v.fitness=new D03CountFitness();
 v.setSettings(new SceneSettings({"Field1"=>1,"Field2"=>1,"Field3"=>1,"Field4"=>1}));v.renderer=new Display03ModeRenderer();v.onShow();
 var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
 Test.assert(body.starts==0&&body.reads==0);v.resumeAfterFrame();Test.assert(body.starts==1&&body.reads==1&&v.values["energy"]==68);
 v.refreshFitness();Test.assert(body.starts==1&&body.reads==1);
 var id=new Complications.Id(Complications.COMPLICATION_TYPE_BODY_BATTERY);body.next=null;v.bodyBatteryChanged(id);Test.assert(body.reads==2&&v.values["energy"]==null);
 body.next=0;clock.now+=60;v.refreshFitness();Test.assert(body.reads==3&&v.values["energy"]==0);
 v.onEnterSleep();Test.assert(body.stops==1&&v.values["energy"]==null);v.bodyBatteryChanged(id);Test.assert(body.reads==3);
 v.onExitSleep();v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assert(body.reads==3);v.resumeAfterFrame();Test.assert(body.starts==2&&body.reads==4&&v.values["energy"]==0);
 v.setSettings(new SceneSettings({"Field1"=>0,"Field2"=>0,"Field3"=>0,"Field4"=>0}));Test.assert(body.stops==2&&v.values["energy"]==null);v.onHide();
 logger.debug("BODY_CURRENT selectedOnly=true duplicatesOne=true callbackNullAndZero=true lowNoRead=true wakeAfterFrame=true deselectionUnsubscribes=true");return true;
}

(:typecheck(false)) class D03Id {var kind;function initialize(k){kind=k;}function getType(){return kind;}}
(:typecheck(false)) class D03ComplicationValue {var value;function initialize(v){value=v;}}
(:typecheck(false)) module D03Complications {
 const BODY=23;var registration=0;var subscriptions=0;var removals=0;var reads=0;var next=null;var deny=false;var failRead=false;
 function reset(){registration=0;subscriptions=0;removals=0;reads=0;next=null;deny=false;failRead=false;}
 function registerComplicationChangeCallback(callback){registration+=1;}
 function subscribeToUpdates(id){subscriptions+=1;if(deny){return false;}return true;}
 function unsubscribeFromUpdates(id){removals+=1;}
 function getComplication(id){reads+=1;if(failRead){throw new Lang.InvalidValueException("unavailable");}return new D03ComplicationValue(next);}
}
(:typecheck(false)) class D03ComplicationObserver {function changed(id){}}
(:test,:typecheck(false)) function display03ComplicationSourceBoundary(logger){
 D03Complications.reset();var source=new MappedBodyBatterySource();var observer=new D03ComplicationObserver();
 Test.assert(source.start(observer.method(:changed)));Test.assert(source.start(observer.method(:changed)));
 Test.assert(D03Complications.subscriptions==1&&D03Complications.registration==1);
 D03Complications.next=68;Test.assert(source.read()==68);D03Complications.next=0;Test.assert(source.read()==0);
 D03Complications.next=null;Test.assert(source.read()==null);D03Complications.next=101;Test.assert(source.read()==null);
 D03Complications.failRead=true;Test.assert(source.read()==null);source.stop();Test.assert(D03Complications.removals==1&&!source.subscribed&&!source.observed);
 D03Complications.reset();D03Complications.deny=true;Test.assert(!source.start(observer.method(:changed))&&!source.subscribed);
 D03Complications.next=48;Test.assert(source.read()==48);D03Complications.failRead=true;Test.assert(source.read()==null);
 logger.debug("BODY_SOURCE startDedup=true nullZeroRange=true deniedSubscription=true unavailableRead=null currentReadAllowed=true");return true;
}

(:test,:typecheck(false)) class D03ActualComplicationObserver {function changed(id){}}
(:test,:typecheck(false)) function display03ActualComplicationApi(logger){
 var source=new BodyBatterySource();var observer=new D03ActualComplicationObserver();var subscribed=source.start(observer.method(:changed));
 var current=source.read();Test.assert(current==null||(current>=0&&current<=100));source.stop();
 Test.assert(!source.subscribed&&!source.observed);logger.debug("BODY_API subscription="+subscribed+" valuePresent="+(current!=null)+" valueRangeChecked=true stopped=true");return true;
}
