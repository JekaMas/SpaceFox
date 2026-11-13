import Toybox.Lang;
import Toybox.Time;
import Toybox.Test;
// Explicit substitutes for Garmin modules/return objects. No real health values,
// permission revocation, storage, network, raw sensor or physical-device proof.
module AvailableFeatures {module ActivityMonitor {} module SensorHistory {}}
module UnavailableFeatures {}
module MetricSDK {
 var activity as ActivityApi or NoApis=new ActivityApi();
 var history as HistoryApi or MissingHistory=new HistoryApi();
 var system as SystemApi=new SystemApi();
 var mode as Number=0;
 var trace as Array<String> =[];
 function reset(value as Number) as Void {mode=value;trace=[];activity=new ActivityApi();history=new HistoryApi();system=new SystemApi();}
}
class NoApis {function initialize(){}}
class MissingHistory {var ORDER_NEWEST_FIRST as Number=91;function initialize(){}}
class MissingFields {function initialize(){}}
class MetricInfo {var steps as Number=0;var calories as Number=2345;function initialize(){}}
class MetricStats {var battery as Number=82;function initialize(){}}
class MetricSample {var data as Number;var when as Time.Moment;function initialize(v as Number,t as Time.Moment){data=v;when=t;}}
class MetricIterator {
 var role as String;var calls as Number=0;
 function initialize(value as String){role=value;}
 function next() as MetricSample or Null {calls+=1;MetricSDK.trace.add(role+".next");if(calls>1){throw new Lang.InvalidValueException("full history traversal forbidden");}
  if(MetricSDK.mode==3){return null;}
  return new MetricSample(role.equals("heart")?72:role.equals("energy")?68:0,new Time.Moment(1800000000));}
}
class ActivityApi {
 function initialize(){}
 function getInfo() as MetricInfo or MissingFields {MetricSDK.trace.add("activity.info");if(MetricSDK.mode==1){throw new Lang.InvalidValueException("denied ActivityMonitor");}return MetricSDK.mode==3?new MissingFields():new MetricInfo();}
}
class SystemApi {
 function initialize(){}
 function getSystemStats() as MetricStats {MetricSDK.trace.add("system.stats");if(MetricSDK.mode==1){throw new Lang.InvalidValueException("unavailable stats");}return new MetricStats();}
}
class HistoryApi {
 var ORDER_NEWEST_FIRST as Number=91; // Deliberately distinctive boundary constant.
 function initialize(){}
 function open(role as String,options as Dictionary<Symbol,Number>) as MetricIterator {MetricSDK.trace.add(role+".open");if(options.size()!=2||options[:period]!=1||options[:order]!=91){throw new Lang.InvalidValueException("history request not one newest sample");}if(MetricSDK.mode==1){throw new Lang.InvalidValueException("denied SensorHistory");}return new MetricIterator(role);}
 function getHeartRateHistory(options as Dictionary<Symbol,Number>) as MetricIterator {return open("heart",options);}
 function getBodyBatteryHistory(options as Dictionary<Symbol,Number>) as MetricIterator {return open("energy",options);}
 function getStressHistory(options as Dictionary<Symbol,Number>) as MetricIterator {return open("stress",options);}
}
function traceEquals(expected as Array<String>) as Boolean {if(MetricSDK.trace.size()!=expected.size()){return false;}for(var i=0;i<expected.size();i+=1){if(!MetricSDK.trace[i].equals(expected[i])){return false;}}return true;}
(:test)
function metricAvailable(logger as Test.Logger) as Boolean {
 MetricSDK.reset(0);var f=new BoundaryFitness();var v=f.sample(1800000300);
 logger.debug("BOUNDARY available distinct sources; steps/stress legitimate zero; exact one newest sample per history API; no network/raw-sensor objects");
 return v["steps"]==0&&v["calories"]==2345&&v["battery"]==82&&v["heart"]==72&&v["energy"]==68&&v["stress"]==0&&f.display(v,"battery").equals("82%")&&f.display(v,"energy").equals("68")&&traceEquals(["activity.info","system.stats","heart.open","heart.next","energy.open","energy.next","stress.open","stress.next"]);
}
(:test)
function metricDenied(logger as Test.Logger) as Boolean {
 MetricSDK.reset(1);var f=new BoundaryFitness();var v=f.sample(1800000300);var ok=v.size()==6;var items=v.values();for(var i=0;i<items.size();i+=1){ok=ok&&items[i]==null;}
 logger.debug("BOUNDARY denied/unavailable calls throw; all six null without crash; each independent source attempted; no fabricated replacement");
 return ok&&f.display(v,"heart").equals("—")&&traceEquals(["activity.info","system.stats","heart.open","energy.open","stress.open"]);
}
(:test)
function metricUnsupported(logger as Test.Logger) as Boolean {
 MetricSDK.reset(0);var f=new BoundaryFitness();var v=new UnsupportedFitness().sample(1800000300);
 var moduleAbsent=v["steps"]==null&&v["heart"]==null&&v["energy"]==null&&v["stress"]==null&&v["calories"]==null&&v["battery"]==82&&traceEquals(["system.stats"]);
 logger.debug("moduleAbsent="+moduleAbsent+" values="+v+" trace="+MetricSDK.trace);
 MetricSDK.reset(0);MetricSDK.activity=new NoApis();MetricSDK.history=new MissingHistory();v=f.sample(1800000300);
 logger.debug("functionAbsent values="+v+" trace="+MetricSDK.trace);
 logger.debug("BOUNDARY absent modules then absent functions; guarded reads omitted; independent system watch charge still available");
 return moduleAbsent&&v["steps"]==null&&v["heart"]==null&&v["energy"]==null&&v["stress"]==null&&v["battery"]==82&&traceEquals(["system.stats"]);
}
(:test)
function metricMissing(logger as Test.Logger) as Boolean {
 MetricSDK.reset(3);var f=new BoundaryFitness();var v=f.sample(1800000300);
 logger.debug("BOUNDARY missing info fields and absent history samples retain null; charge remains real boundary value82; old history beyond300seconds unavailable");
 return v["steps"]==null&&v["calories"]==null&&v["heart"]==null&&v["energy"]==null&&v["stress"]==null&&v["battery"]==82&&f.recentValue(68,1800000000,1800000301,100,false)==null&&traceEquals(["activity.info","system.stats","heart.open","heart.next","energy.open","energy.next","stress.open","stress.next"]);
}
