import Toybox.Lang;
import Toybox.Test;

(:test,:typecheck(false)) class MetricStressFailure extends HistoryApi {
 function getStressHistory(options){MetricSDK.trace.add("stress.failed");throw new Lang.InvalidValueException("unavailable stress");}
}
(:test,:typecheck(false)) class MetricObserver {function changed(id) as Void {}}
(:test,:typecheck(false)) function actualMetricApi(logger){
 var fields=new SelectedFields();var probe=new MetricObserver();fields.start(["steps","energy","heart","stress"],probe.method(:changed));fields.read("en");
 var fitness=new Fitness();fitness.selectedRoles=["steps","energy","heart","stress"];fitness.selectedFields=fields;
 var result=fitness.sample(Toybox.Time.now().value().toLong());
 var roles=["steps","energy","heart","stress"];for(var i=0;i<roles.size();i+=1){var value=result[roles[i]];Test.assert(value==null||value>=0);Test.assert(fitness.status[roles[i]].equals("READY")||fitness.status[roles[i]].equals("WAITING")||fitness.status[roles[i]].equals("UNAVAILABLE"));}
 logger.debug("ACTUAL_GARMIN_APIS sampled=true bodyAvailable="+(result["energy"]!=null)+" heartAvailable="+(result["heart"]!=null)+" stressAvailable="+(result["stress"]!=null));fields.stop();return true;
}
(:test,:typecheck(false)) class MetricBatteryValue {var value;function initialize(v){value=v;}}
(:test,:typecheck(false)) class MetricBatteryApi {
 var next=null;function register(callback){}function subscribe(id){return true;}function unsubscribe(id){}function get(id){return new MetricBatteryValue(next);}
}
(:test,:typecheck(false)) function metricProviderSequences(logger){
 var events=0;
 for(var seed=0;seed<8;seed+=1){
  var fields=new SelectedFields();var api=new MetricBatteryApi();var observer=new MetricObserver();fields.api=api;fields.start(["steps","energy","heart","stress"],observer.method(:changed));
  var coverage={"available_applied"=>0,"partial_failure_applied"=>0,"missing_applied"=>0,"restore_applied"=>0,"unsupported_applied"=>0};
  var names=(seed&1)==0?["available","partial_failure","unsupported","missing","restore"]:["partial_failure","available","restore","unsupported","missing"];
  for(var i=0;i<names.size();i+=1){var event=names[i];var f=event.equals("unsupported")?new UnsupportedFitness():new BoundaryFitness();f.selectedRoles=["steps","energy","heart","stress"];f.selectedFields=fields;MetricSDK.reset(event.equals("missing")?3:0);if(event.equals("partial_failure")){MetricSDK.history=new MetricStressFailure();}api.next=event.equals("missing")?null:event.equals("restore")?0:68;fields.read("en");
   var value=f.sample(1800000300);coverage[event+"_applied"]+=1;events+=1;
   if(event.equals("unsupported")){Test.assert(value["steps"]==null&&value["energy"]==68&&value["heart"]==null&&value["stress"]==null);Test.assert(traceEquals([]));}
   else if(event.equals("missing")){Test.assert(value["steps"]==null&&value["energy"]==null&&value["heart"]==null&&value["stress"]==null);}
   else{Test.assert(value["steps"]==0&&value["energy"]==(event.equals("restore")?0:68)&&value["heart"]==72);Test.assert(event.equals("partial_failure")?value["stress"]==null:value["stress"]==0);}
   Test.assert(f.status["energy"].equals(event.equals("missing")?"WAITING":"READY"));Test.assert(f.status["steps"].equals(event.equals("unsupported")?"UNAVAILABLE":event.equals("missing")?"WAITING":"READY"));Test.assert(f.status["heart"].equals(event.equals("unsupported")?"UNAVAILABLE":event.equals("missing")?"WAITING":"READY"));
   Test.assert(f.status["stress"].equals(event.equals("partial_failure")||event.equals("unsupported")?"UNAVAILABLE":event.equals("missing")?"WAITING":"READY"));Test.assert(f.reason["stress"].equals(event.equals("unsupported")?"unsupported":event.equals("partial_failure")?"provider-error":event.equals("missing")?"no-sample":"available"));
  }
  fields.stop();var keys=coverage.keys();for(var k=0;k<keys.size();k+=1){Test.assertMessage(coverage[keys[k]]>0,"metric seed="+seed+" missing "+keys[k]);}
 }
 logger.debug("METRIC_PROVIDER seeds=8 events="+events+" isolated_failure=true oldest_age=300");return true;
}
