import Toybox.Application;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;
(:test,:typecheck(false)) function trustedSnapshotBench(logger){
 var keys=["id","rocket","operator","operatorShort","purpose","site","modelId","operatorId","siteId","point","target","precision","displayTarget","sourceValidated","stale","rescheduled","reminderEligible"];
 var ids=[Rez.JsonData.Object,Rez.JsonData.Array];
 for(var v=0;v<2;v+=1){
  var before=System.getSystemStats().usedMemory;var start=System.getTimer();var payload=WatchUi.loadResource(ids[v]);var load=System.getTimer()-start;var loaded=System.getSystemStats().usedMemory;
  start=System.getTimer();Application.Storage.setValue("bench.slot",payload);Application.Storage.setValue("bench.active",1);var write=System.getTimer()-start;
  payload=null;start=System.getTimer();var read=Application.Storage.getValue("bench.slot");var row=read["rows"][0];if(v==1){var mapped={};for(var j=0;j<keys.size();j+=1){mapped[keys[j]]=row[j];}row=mapped;}
  var scene=new SceneContext(row);var readFact=System.getTimer()-start;
  Test.assert(scene.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));Test.assert(scene.point!=null&&scene.displayTarget==1795042200l);Test.assertEqual(read["rows"].size(),3);
  logger.debug("CANDIDATE variant="+v+" resourceMs="+load+" writeMs="+write+" readFactMs="+readFact+" usedBefore="+before+" usedLoaded="+loaded+" sampled=true");scene=null;read=null;row=null;Application.Storage.deleteValue("bench.slot");Application.Storage.deleteValue("bench.active");
 }
 return true;
}
