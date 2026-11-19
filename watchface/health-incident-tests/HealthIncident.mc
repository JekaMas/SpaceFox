import Toybox.Complications;import Toybox.Lang;import Toybox.Test;import Toybox.Time;
(:test,:typecheck(false)) class IncidentValue {var value;var shortLabel="Body";var longLabel="Body";var unit=null;function initialize(v){value=v;}}
(:test,:typecheck(false)) class IncidentApi extends FieldComplicationApi {
 var values={18=>null,22=>null,23=>null};var calls=0;
 function register(cb){}function subscribe(id){return true;}function unsubscribe(id){}function get(id){calls+=1;return new IncidentValue(values[id.getType()]);}
}
(:test,:typecheck(false)) class IncidentSample {var data;var when;function initialize(value,stamp){data=value;when=new Time.Moment(stamp);}}
(:test,:typecheck(false)) class IncidentIterator {var rows;var i=0;function initialize(r){rows=r;}function next(){if(i>=rows.size()){return null;}var v=rows[i];i+=1;return v;}}
(:test,:typecheck(false)) class IncidentFields extends SelectedFields {
 var fakeNow=1800000000;var samples={22=>[],23=>[]};var historyCalls=0;var historyFailure=false;
 function healthNow(){return fakeNow;}
 function historySamples(kind){historyCalls+=1;if(historyFailure){throw new Lang.InvalidValueException("history failure");}return new IncidentIterator(samples[kind]);}
 function savedField(slot){return new Complications.Id(23);}
 function callback(id){}
}
(:test,:typecheck(false)) function incidentFreshHistory(logger){
 var f=new IncidentFields();f.api=new IncidentApi();f.samples[23]=[new IncidentSample(68,1800000000)];f.samples[22]=[new IncidentSample(0,1799999990)];
 f.start(["steps","energy","heart","stress"],f.method(:callback));f.read("en");logger.debug("HISTORY_WITNESS calls="+f.historyCalls+" energy="+f.healthValue("energy")+" stress="+f.healthValue("stress")+" heart="+f.healthValue("heart"));
 Test.assertMessage(f.healthValue("energy")==68&&f.healthValue("stress")==0&&f.healthValue("heart")==null,"fresh Garmin history must supply built-in Body Battery/stress without inventing pulse");f.stop();return true;
}
(:test,:typecheck(false)) function incidentHistoryPolicy(logger){
 var f=new IncidentFields();var api=new IncidentApi();f.api=api;f.start(["steps","energy","heart","stress"],f.method(:callback));
 f.samples[23]=[new IncidentSample(null,1800000000),new IncidentSample(61,1799999700)];f.samples[22]=[new IncidentSample(35,1799999699)];api.values[18]=0;f.read("en");
 Test.assert(f.healthValue("energy")==61&&f.healthValue("stress")==null&&f.healthValue("heart")==null&&f.historyCalls==2);
 f.readChanged("en",new Complications.Id(23));Test.assert(f.historyCalls==2&&f.healthValue("energy")==61);
 f.fakeNow+=1;Test.assert(f.expireHistory(f.fakeNow)&&f.healthValue("energy")==null);
 f.fakeNow+=60;f.samples[23]=[new IncidentSample(99,1800000200),new IncidentSample(0,1800000050)];f.samples[22]=[new IncidentSample(101,1800000050),new IncidentSample(27,1800000050)];f.read("en");
 Test.assert(f.healthValue("energy")==0&&f.healthValue("stress")==27&&f.historyCalls==4);
 api.values[23]=73;api.values[22]=18;api.values[18]=72;f.read("en");Test.assert(f.healthValue("energy")==73&&f.healthValue("stress")==18&&f.healthValue("heart")==72&&f.historyCalls==4);
 f.stop();var before=f.historyCalls;f.read("en");Test.assert(f.historyCalls==before);f.start(["custom1","steps","heart","stress"],f.method(:callback));api.values[23]=null;f.read("en");Test.assert(f.display("custom1").equals("—")&&f.historyCalls==before);
 f.stop();logger.debug("HISTORY_POLICY exact300 expiry301 bounded_callbacks true zero_and_custom true");return true;
}
(:test,:typecheck(false)) function incidentCustomDuplicateOrdering(logger){
 var roles=[["custom1","energy","heart","stress"],["energy","custom2","heart","stress"]];
 for(var i=0;i<roles.size();i+=1){var f=new IncidentFields();f.api=new IncidentApi();f.samples[23]=[new IncidentSample(47,1800000000)];f.samples[22]=[];f.start(roles[i],f.method(:callback));f.read("en");var key=i==0?"custom1":"custom2";
 Test.assert(f.healthValue("energy")==47&&f.display(key).equals("—"));f.readChanged("en",new Complications.Id(23));Test.assert(f.healthValue("energy")==47&&f.display(key).equals("—"));Test.assert(f.historyCalls==2);f.stop();}
 logger.debug("CUSTOM_SAME_ID both_orders=true callback=true no_history_text=true");return true;
}
(:test,:typecheck(false)) function incidentGeneratedHistory(logger){
 var total=0;var reads=0;var expiries=0;var updates=0;
 for(var seed=1;seed<=16;seed+=1){var f=new IncidentFields();var api=new IncidentApi();f.api=api;api.values[22]=14;f.start(["steps","energy","heart","stress"],f.method(:callback));var now=1800000000;var sampleValue=null;var sampleTime=now;var lastQuery=null;var cachedValue=null;var cachedTime=null;var expected=null;var expiry=null;var queries=0;var state=seed;
 for(var i=0;i<60;i+=1){state=(state*37+17)%10007;var e=state%5;
  if(e==0){sampleValue=(state%101);sampleTime=now;f.samples[23]=[new IncidentSample(sampleValue,sampleTime)];updates+=1;}
  else if(e==1){sampleValue=null;f.samples[23]=[new IncidentSample(null,now)];updates+=1;}
  else if(e==2){now+=(state%91);f.fakeNow=now;}
  else if(e==3){f.read("en");expected=null;expiry=null;reads+=1;if(lastQuery==null||now-lastQuery>=60){lastQuery=now;queries+=1;if(cachedValue!=null&&now-cachedTime>300){cachedValue=null;}if(sampleValue!=null&&now-sampleTime<=300&&(cachedValue==null||sampleTime>=cachedTime)){cachedValue=sampleValue;cachedTime=sampleTime;}}if(cachedValue!=null&&now>=cachedTime&&now-cachedTime<=300){expected=cachedValue;expiry=cachedTime+300;}}
  else{f.expireHistory(now);if(expiry!=null&&now>expiry){expected=null;expiry=null;}expiries+=1;}
  Test.assertMessage(f.healthValue("energy")==expected,"history generated independent model seed="+seed+" event="+i);Test.assert(f.historyCalls==queries);total+=1;
 }
 Test.assert(f.healthValue("energy")==expected);f.stop();}
 Test.assert(reads>0&&expiries>0&&updates>0);logger.debug("HISTORY_GENERATED seeds=16 events="+total+" reads="+reads+" expiries="+expiries+" inputs="+updates+" after_each=true end=true");return true;
}
(:test,:typecheck(false)) function incidentFreshCacheTransientFailure(logger){var f=new IncidentFields();f.api=new IncidentApi();f.samples[23]=[new IncidentSample(68,1800000000)];f.samples[22]=[];f.start(["steps","energy","heart","stress"],f.method(:callback));f.read("en");f.fakeNow+=60;f.samples[23]=[];f.read("en");Test.assertMessage(f.healthValue("energy")==68,"a temporary missing history response must retain a still-fresh accepted sample");f.fakeNow+=60;f.historyFailure=true;f.read("en");Test.assert(f.healthValue("energy")==68);f.fakeNow+=181;f.expireHistory(f.fakeNow);Test.assert(f.healthValue("energy")==null);f.stop();return true;}
