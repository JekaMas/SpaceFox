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

(:test,:typecheck(false)) class D03FakeFields extends SelectedFields {
 var starts=0;var reads=0;var stops=0;var next=68;
 function start(slots,callback){starts+=1;selected=slots.indexOf("energy")>=0?[new Complications.Id(23)]:[null];}
 function read(locale){reads+=1;energy=selected[0] instanceof Complications.Id?next:null;}
 function stop(){if(selected.size()>0){stops+=1;}selected=[];energy=null;}
 function includes(id){return selected.size()>0&&id.getType()==23;}
}
(:test,:typecheck(false)) function display03CurrentBodyBatteryLifecycle(logger){
 var clock=new Display03Clock();var v=new SpaceFoxView(clock,new ScheduleState(null,"empty"));var fields=new D03FakeFields();v.selectedFields=fields;v.fitness=new D03CountFitness();
 v.setSettings(new SceneSettings({"Field1"=>1,"Field2"=>1,"Field3"=>1,"Field4"=>1}));v.renderer=new Display03ModeRenderer();v.onShow();
 var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
 Test.assert(fields.starts==0&&fields.reads==0);v.resumeAfterFrame();Test.assert(fields.starts==1&&fields.reads==1&&v.values["energy"]==68);
 v.refreshFitness();Test.assert(fields.starts==1&&fields.reads==1);
 var id=new Complications.Id(23);fields.next=null;v.fieldsChanged(id);Test.assert(fields.reads==2&&v.values["energy"]==null);
 fields.next=0;clock.now+=60;v.refreshFitness();Test.assert(fields.reads==3&&v.values["energy"]==0);
 v.onEnterSleep();Test.assert(fields.stops==1&&v.values["energy"]==null);v.fieldsChanged(id);Test.assert(fields.reads==3);
 v.onExitSleep();v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assert(fields.reads==3);v.resumeAfterFrame();Test.assert(fields.starts==2&&fields.reads==4&&v.values["energy"]==0);
 v.setSettings(new SceneSettings({"Field1"=>0,"Field2"=>0,"Field3"=>0,"Field4"=>0}));Test.assert(fields.stops==2&&v.values["energy"]==null);v.onHide();
 logger.debug("BODY_CURRENT unifiedOwner=true callbackNullAndZero=true lowNoRead=true wakeAfterFrame=true deselectionUnsubscribes=true");return true;
}
(:typecheck(false)) class D03ComplicationValue {
 var value;var unit=null;var shortLabel="Body Battery";var longLabel="Body Battery";
 function initialize(v){value=v;}function getType(){return 23;}
}
(:typecheck(false)) class D03Complications {
 var registration=0;var subscriptions=0;var removals=0;var reads=0;var next=null;var deny=false;var failRead=false;
 function register(callback){registration+=1;}function subscribe(id){subscriptions+=1;return !deny;}
 function unsubscribe(id){removals+=1;}function get(id){reads+=1;if(failRead){throw new Complications.ComplicationNotFoundException();}return new D03ComplicationValue(next);}
}
(:typecheck(false)) class D03ComplicationObserver {function changed(id){}}
(:test,:typecheck(false)) function display03ComplicationSourceBoundary(logger){
 var api=new D03Complications();var source=new SelectedFields();source.api=api;var observer=new D03ComplicationObserver();
 source.start(["energy","energy","energy","energy"],observer.method(:changed));Test.assert(api.subscriptions==1&&api.registration==1);
 api.next=68;source.read("en");Test.assert(source.energy==68&&api.reads==1);api.next=0;source.read("en");Test.assert(source.energy==0&&api.reads==2);
 api.next=null;source.read("en");Test.assert(source.energy==null);api.next=101;source.read("en");Test.assert(source.energy==null);
 api.failRead=true;source.read("en");Test.assert(source.energy==null);source.stop();Test.assert(api.removals==1&&!source.active()&&!source.callbackRegistered);
 api=new D03Complications();api.deny=true;source.api=api;source.start(["energy","energy","energy","energy"],observer.method(:changed));
 Test.assert(api.subscriptions==1&&source.subscribed.size()==0);api.next=48;source.read("en");Test.assert(source.energy==48);
 api.failRead=true;source.read("en");Test.assert(source.energy==null);source.stop();
 logger.debug("FIELD_SOURCE oneOwner=true duplicatesOne=true deniedSubscription=true currentReadAllowed=true stopped=true");return true;
}
(:test,:typecheck(false)) function display03ActualComplicationApi(logger){
 var source=new SelectedFields();var observer=new D03ComplicationObserver();source.start(["energy","energy","energy","energy"],observer.method(:changed));source.read("en");
 var current=source.energy;Test.assert(current==null||(current>=0&&current<=100));Test.assert(source.subscribed.size()<=1);source.stop();
 Test.assert(!source.active()&&!source.callbackRegistered);logger.debug("BODY_API valuePresent="+(current!=null)+" valueRangeChecked=true stopped=true");return true;
}
