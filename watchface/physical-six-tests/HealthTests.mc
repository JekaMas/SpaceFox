import Toybox.Complications;
import Toybox.Lang;
import Toybox.Test;

(:test,:typecheck(false)) class PhysicalHealthItem {
 var value;var shortLabel="";var longLabel="";
 function initialize(v){value=v;}
}
(:test,:typecheck(false)) class PhysicalHealthApi {
 var subscriptions=[];var calls=[];var values={18=>0,22=>37,23=>68};var failed=-1;var registerFailed=false;var registers=0;var refuseKind=-1;
 function register(callback){if(callback!=null){registers+=1;if(registerFailed){throw new Lang.InvalidValueException("registration");}}}
 function subscribe(id){if(id.getType()==refuseKind){return false;}subscriptions.add(id.getType());return true;}
 function unsubscribe(id){}
 function get(id){var kind=id.getType();calls.add(kind);if(kind==failed){throw new Lang.InvalidValueException("provider");}return new PhysicalHealthItem(values[kind]);}
}
(:test,:typecheck(false)) class PhysicalFakeFields extends SelectedFields {function historySamples(kind){return null;} function healthNow(){return 1800000000;}}
(:test,:typecheck(false)) class PhysicalHealthObserver {function changed(id) as Void {}}
(:test,:typecheck(false)) class PhysicalActivity {var steps=0;var calories=12;}
(:test,:typecheck(false)) class PhysicalFitness extends Fitness {
 function activityAvailable() as Boolean{return true;}
 function activityInfo(){return new PhysicalActivity();}
}

(:test,:typecheck(false)) function physicalSupportedHealthSubscriptions(logger){
 var fields=new PhysicalFakeFields();var api=new PhysicalHealthApi();var observer=new PhysicalHealthObserver();fields.api=api;
 fields.start(["steps","energy","heart","stress"],observer.method(:changed));
 Test.assertMessage(fields.includes(new Complications.Id(18)),"heart must subscribe to the supported Garmin heart complication");
 Test.assertMessage(fields.includes(new Complications.Id(22)),"stress must subscribe to the supported Garmin stress complication");
 Test.assertMessage(fields.includes(new Complications.Id(23)),"body battery must subscribe to the supported Garmin body battery complication");
 fields.stop();return true;
}

(:test,:typecheck(false)) function physicalHealthValuesAndFailures(logger){
 var fields=new PhysicalFakeFields();var api=new PhysicalHealthApi();var observer=new PhysicalHealthObserver();fields.api=api;
 fields.start(["steps","energy","heart","stress"],observer.method(:changed));fields.read("en");
 var fitness=new PhysicalFitness();fitness.selectedRoles=["steps","energy","heart","stress"];fitness.selectedFields=fields;
 var values=fitness.sample(1800000000);Test.assert(values["steps"]==0&&values["energy"]==68&&values["heart"]==null&&values["stress"]==37);
 Test.assert(fitness.status["heart"].equals("WAITING"));
 fields.stop();Test.assert(fields.healthValue("energy")==68&&fields.healthValue("heart")==null&&fields.healthValue("stress")==37);
 fields.start(["steps","energy","heart","stress"],observer.method(:changed));
 Test.assert(fields.healthValue("energy")==68&&fields.healthValue("heart")==null&&fields.healthValue("stress")==37);
 api.values[18]=72;fields.readChanged("en",new Complications.Id(18));
 Test.assert(fields.healthValue("heart")==72&&fields.healthValue("energy")==68&&fields.healthValue("stress")==37);
 api.failed=22;fields.readChanged("en",new Complications.Id(22));
 Test.assert(fields.healthValue("stress")==null&&fields.healthState("stress").equals("UNAVAILABLE"));
 Test.assert(fields.healthValue("heart")==72&&fields.healthValue("energy")==68);
 api.failed=-1;api.values[22]=null;fields.readChanged("en",new Complications.Id(22));
 Test.assert(fields.healthValue("stress")==null&&fields.healthState("stress").equals("WAITING"));
 fields.stop();api.registerFailed=true;fields.start(["steps","energy","heart","stress"],observer.method(:changed));fields.read("en");
 Test.assert(fields.healthValue("heart")==72&&fields.healthValue("energy")==68);
 fields.stop();logger.debug("Complication values, zero, per-source failure and stop/restart retention");return true;
}

(:test,:typecheck(false)) function physicalSimulatorActualProviders(logger){
 var fields=new SelectedFields();var observer=new PhysicalHealthObserver();
 fields.start(["steps","energy","heart","stress"],observer.method(:changed));fields.read("en");
 var fitness=new Fitness();fitness.selectedRoles=["steps","energy","heart","stress"];fitness.selectedFields=fields;
 var values=fitness.sample(Toybox.Time.now().value());var roles=["steps","energy","heart","stress"];
 for(var i=0;i<roles.size();i+=1){var role=roles[i];var value=values[role];Test.assert(value==null||value>=0);Test.assert(fitness.status[role].equals("READY")||fitness.status[role].equals("WAITING")||fitness.status[role].equals("UNAVAILABLE"));}
 logger.debug("ACTUAL_PROVIDER energy="+values["energy"]+"/"+fitness.status["energy"]+" heart="+values["heart"]+"/"+fitness.status["heart"]+" stress="+values["stress"]+"/"+fitness.status["stress"]+" steps="+values["steps"]+"/"+fitness.status["steps"]);
 fields.stop();return true;
}

(:test,:typecheck(false)) function physicalMetricCallbackKeepsSceneAndLowValues(logger){
 var view=new PhysicalWakeView();view.mode=Toybox.System.DISPLAY_MODE_HIGH_POWER;view.onShow();
 var api=new PhysicalHealthApi();view.selectedFields=new PhysicalFakeFields();view.selectedFields.api=api;view.fitness=new PhysicalFitness();view.fitness.selectedFields=view.selectedFields;
 view.readFitnessSnapshot(1800000000);Test.assert(view.values["steps"]==0&&view.values["energy"]==68&&view.values["heart"]==null&&view.values["stress"]==37);
 Test.assert(view.sceneLifecycle.request(1));var token=view.sceneLifecycle.begin();var generation=view.sceneLifecycle.generation;
 api.values[18]=72;view.fieldsChanged(new Complications.Id(18));
 Test.assert(view.values["heart"]==72&&view.values["energy"]==68&&view.values["stress"]==37);
 Test.assert(view.sceneLifecycle.generation==generation&&view.sceneLifecycle.job.token==token);
 view.mode=Toybox.System.DISPLAY_MODE_LOW_POWER;view.onEnterSleep();api.values[18]=99;view.fieldsChanged(new Complications.Id(18));
 Test.assert(view.values["heart"]==72&&view.values["energy"]==68&&view.values["stress"]==37);
 view.mode=Toybox.System.DISPLAY_MODE_HIGH_POWER;view.onExitSleep();Test.assert(view.values["heart"]==72&&view.values["energy"]==68&&view.values["stress"]==37);
 view.onHide();logger.debug("metric callback preserves unrelated fields, scene job and LOW snapshot");return true;
}

(:test,:typecheck(false)) function physicalHealthSubscriptionRearm(logger){
 var view=new PhysicalWakeView();view.mode=Toybox.System.DISPLAY_MODE_HIGH_POWER;view.onShow();
 var api=new PhysicalHealthApi();api.registerFailed=true;view.selectedFields=new PhysicalFakeFields();view.selectedFields.api=api;view.fitness=new PhysicalFitness();view.fitness.selectedFields=view.selectedFields;
 view.readFitnessSnapshot(1800000000);Test.assert(api.registers==1&&view.values["heart"]==null);
 api.registerFailed=false;api.refuseKind=22;view.readFitnessSnapshot(1800000060);
 Test.assertMessage(api.registers==2&&api.subscriptions.size()==3&&api.subscriptions.indexOf(2)>=0&&api.subscriptions.indexOf(23)>=0&&api.subscriptions.indexOf(18)>=0,"next scheduled refresh must retry callback registration and subscribe selected steps");
 api.refuseKind=-1;view.readFitnessSnapshot(1800000120);
 Test.assertMessage(api.registers==2&&api.subscriptions.size()==4&&api.subscriptions.indexOf(22)>=0,"next scheduled refresh must retry only the missing subscription");
 view.onHide();logger.debug("callback and missing subscription rearmed by bounded refresh");return true;
}

(:test,:typecheck(false)) function physicalHealthRearmRegressionBatch(logger){
 Test.assert(physicalSupportedHealthSubscriptions(logger));
 Test.assert(physicalHealthValuesAndFailures(logger));
 Test.assert(physicalSimulatorActualProviders(logger));
 Test.assert(physicalMetricCallbackKeepsSceneAndLowValues(logger));
 Test.assert(physicalHealthSubscriptionRearm(logger));
 logger.debug("HEALTH_REARM_BATCH cases=5 provider_and_view=true");return true;
}
