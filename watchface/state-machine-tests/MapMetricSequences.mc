import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

// Inputs and expectations below are literal captured launch coordinates and
// independent event rules. No SUT projection supplies an expected value.
(:test,:typecheck(false)) function mapMetricEventSequences(logger){
 var total=0;
 for(var seed=0;seed<8;seed+=1){
  var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));var fields=new MapMetricFakeFields();view.selectedFields=fields;view.fitness=new MapMetricSample();view.fitness.selectedFields=fields;
  var map=view.mapDecision;var art=view.sceneLifecycle;
  var coarse=new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]).presentation;
  var exact=new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.Exact)["payload"]).presentation;
  var unknownPayload=WatchUi.loadResource(Rez.JsonData.Exact)["payload"];unknownPayload[3][9]=null;var unknown=new NativeTrustedPacket(unknownPayload).presentation;
  var dc=Toybox.Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
  var shown=false;var sleeping=false;var point=false;var ready=false;var failed=false;var id=null;var lon=null;var lat=null;var generation=0;var job=null;var artState=0;
  var coverage={"show_applied"=>0,"show_observed_no_mutation"=>0,"hide_applied"=>0,"hide_observed_no_mutation"=>0,"sleep_applied"=>0,"sleep_observed_no_mutation"=>0,"wake_applied"=>0,"wake_observed_no_mutation"=>0,"source_applied"=>0,"art_start_applied"=>0,"art_complete_applied"=>0,"art_fail_applied"=>0,"art_cancel_applied"=>0,"art_late_observed_no_mutation"=>0,"metric_applied"=>0,"render_observed_no_mutation"=>0,"render_error_applied"=>0,"render_restored_applied"=>0,"unknown_applied"=>0};
  var events=["show","show","empty","source","sleep","sleep","render","wake","wake","start","art_fail","art_late","start2","art_cancel","art_late","start3","metric","complete","render","fault","render","restored","sourceUnknown","source2","hide","hide","render"];
  if((seed&1)!=0){events.add("show");events.add("hide");}
  for(var i=0;i<events.size();i+=1){var event=events[i];var key=null;
   if(event.equals("show")){key=shown?"show_observed_no_mutation":"show_applied";shown=true;view.onShow();}
   else if(event.equals("hide")){key=shown?"hide_applied":"hide_observed_no_mutation";if(shown){generation+=2;artState=0;ready=false;}shown=false;view.onHide();}
   else if(event.equals("sleep")){key=sleeping?"sleep_observed_no_mutation":"sleep_applied";sleeping=true;view.onEnterSleep();}
   else if(event.equals("wake")){key=sleeping?"wake_applied":"wake_observed_no_mutation";sleeping=false;view.onExitSleep();}
   else if(event.equals("empty")){view.setContext(null);generation+=1;point=false;ready=false;artState=0;id=null;lon=null;lat=null;key="source_applied";}
   else if(event.equals("sourceUnknown")){view.setContext(unknown);generation+=1;point=false;ready=false;failed=false;artState=0;id="ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a";lon=null;lat=null;key="unknown_applied";}
   else if(event.equals("source")||event.equals("source2")){var first=event.equals("source");view.setContext(first?coarse:exact);generation+=1;point=true;ready=false;failed=false;artState=0;id=first?"ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60":"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a";lon=first?111.589567:-80.58303644;lat=first?38.863128:28.58341025;key="source_applied";}
   else if(event.equals("start")||event.equals("start2")||event.equals("start3")){var serial=event.equals("start")?1:event.equals("start2")?2:3;Test.assert(art.request(serial));if(event.equals("start2")){generation+=1;}job=art.begin();artState=1;key="art_start_applied";}
   else if(event.equals("art_fail")){art.fail(job);ready=false;artState=0;key="art_fail_applied";}
   else if(event.equals("art_cancel")){art.cancel();generation+=1;ready=false;artState=0;key="art_cancel_applied";}
   else if(event.equals("art_late")){Test.assert(!art.complete(job));key="art_late_observed_no_mutation";}
   else if(event.equals("complete")){Test.assert(art.complete(job));ready=true;artState=2;key="art_complete_applied";}
   else if(event.equals("metric")){view.refreshFitness();fields.next=0;view.fieldsChanged(new Toybox.Complications.Id(23));Test.assert(view.values["energy"]==0&&art.pending()&&art.job.token==job);key="metric_applied";}
   else if(event.equals("fault")){map.failure();failed=true;key="render_error_applied";}
   else if(event.equals("restored")){map.restored();failed=false;key="render_restored_applied";}
   else{view.updateForDisplayMode(dc,Toybox.System.DISPLAY_MODE_HIGH_POWER);key="render_observed_no_mutation";}
   if(key!=null){coverage[key]+=1;}
   Test.assertEqual(view.visible(),shown);Test.assertEqual(view.displayMode(),shown&&!sleeping?1:0);
   var expectedMode=shown?(ready&&!failed?2:1):0;Test.assertEqual(map.mode(shown,ready),expectedMode);Test.assertEqual(map.pointVisible(shown),shown&&point);
   if(point){Test.assert(map.identity.equals(id));Test.assert(map.longitude>lon-0.0001&&map.longitude<lon+0.0001);Test.assert(map.latitude>lat-0.0001&&map.latitude<lat+0.0001);}else{Test.assert(map.point==null);if(id==null){Test.assert(map.identity==null);}else{Test.assert(map.identity.equals(id));Test.assert(map.reason(shown,false).equals(shown?"unqualified-point":"hidden"));}}
   Test.assertEqual(art.generation,generation);Test.assertEqual(art.presentationState,artState);total+=1;
  }
  var keys=coverage.keys();for(var j=0;j<keys.size();j+=1){Test.assertMessage(coverage[keys[j]]>0,"seed="+seed+" missing "+keys[j]);}
  logger.debug("MAP_METRIC_SEED "+seed+" effective=true");
 }
 logger.debug("MAP_METRIC sequences=8 events="+total+" independent_literals=true");return true;
}

(:test,:typecheck(false)) class MapMetricFakeFields extends SelectedFields {
 var next=68;var reads=0;function start(slots,callback){selected=[new Toybox.Complications.Id(23)];}
 function read(locale){reads+=1;energy=next;}
 function readChanged(locale,id){reads+=1;energy=next;}
 function stop(){selected=[];energy=null;}
 function includes(id){return id.getType()==23;}
}
(:test,:typecheck(false)) class MapMetricSample extends Fitness {
 var calls=0;function initialize(){Fitness.initialize();}
 function sample(now){calls+=1;return {"steps"=>123,"energy"=>(selectedFields==null?null:selectedFields.energy),"heart"=>72,"stress"=>35,"battery"=>null,"calories"=>null};}
}
(:test,:typecheck(false)) function metricOverlayDoesNotRestartArt(logger){
 var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));var fields=new MapMetricFakeFields();view.selectedFields=fields;view.fitness=new MapMetricSample();view.fitness.selectedFields=fields;
 var scene=new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]).presentation;view.setContext(scene);view.onShow();view.refreshFitness();
 Test.assert(view.sceneLifecycle.request(1));var token=view.sceneLifecycle.begin();var before=view.sceneLifecycle.generation;var point=view.mapDecision.identity;
 fields.next=0;view.fieldsChanged(new Toybox.Complications.Id(23));
 Test.assert(view.values["steps"]==123&&view.values["energy"]==0&&view.values["heart"]==72&&view.values["stress"]==35&&fields.reads==2);Test.assertEqual(view.sceneLifecycle.generation,before);Test.assert(view.sceneLifecycle.pending()&&view.sceneLifecycle.job.token==token);Test.assert(view.mapDecision.identity==point);
 view.onEnterSleep();Test.assert(view.values["steps"]==123&&view.values["energy"]==0&&view.values["heart"]==72&&view.values["stress"]==35);fields.next=99;view.fieldsChanged(new Toybox.Complications.Id(23));Test.assert(view.values["energy"]==0&&fields.reads==2);
 view.onExitSleep();Test.assert(view.values["steps"]==123&&view.values["energy"]==0&&view.values["heart"]==72&&view.values["stress"]==35);
 view.onHide();logger.debug("METRIC_OVERLAY provider_callback=true zero_valid=true job_restart=0");return true;
}

(:test,:typecheck(false)) class CatalogPointContext {
 var launchId;var point;
 function initialize(id,p){launchId=id;point=p;}
}
(:test,:typecheck(false)) function allBundledMapCenters(logger){
 var policy=new MapPresentation();var coords=NativeAssets.mapCoordinates();var extra=NativeAssets.aodCoordinates;var count=0;
 for(var pass=0;pass<2;pass+=1){var data=pass==0?coords:extra;
  for(var i=0;i<data.size()/8;i+=1){var lon=pass==0?data.decodeNumber(Lang.NUMBER_FORMAT_FLOAT,{:offset=>i*8,:endianness=>Lang.ENDIAN_BIG}):SceneAod.coordinate(data,i*8);var lat=pass==0?data.decodeNumber(Lang.NUMBER_FORMAT_FLOAT,{:offset=>i*8+4,:endianness=>Lang.ENDIAN_BIG}):SceneAod.coordinate(data,i*8+4);
   policy.bind(new CatalogPointContext("catalog-"+pass+"-"+i,[lon,lat]));
   Test.assertMessage(policy.matched&&policy.pointVisible(true)&&policy.x>=330&&policy.x<=340&&policy.y>=160&&policy.y<=170,"catalog pass="+pass+" index="+i);
   count+=1;
  }
 }
 logger.debug("MAP_CATALOG qualified_centers="+count+" all_projections_checked=true");return true;
}

(:test,:typecheck(false)) function clockDrawKeepsMetricsCached(logger){
 var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));var fields=new MapMetricFakeFields();var fitness=new MapMetricSample();view.selectedFields=fields;view.fitness=fitness;fitness.selectedFields=fields;
 view.setContext(new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.Coarse)["payload"]).presentation);view.onShow();view.refreshFitness();var initial=fitness.calls;var reads=fields.reads;var generation=view.sceneLifecycle.generation;var dc=Toybox.Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
 for(var i=0;i<5;i+=1){view.updateForDisplayMode(dc,Toybox.System.DISPLAY_MODE_HIGH_POWER);Test.assertEqual(fitness.calls,initial);Test.assertEqual(fields.reads,reads);Test.assertEqual(view.sceneLifecycle.generation,generation);}
 view.onHide();logger.debug("CLOCK_DRAWS count=5 additional_provider_reads=0 job_restarts=0");return true;
}

(:test,:typecheck(false)) function mapIdentityChangesAtSameSite(logger){
 var first=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];var second=WatchUi.loadResource(Rez.JsonData.Coarse)["payload"];
 second[3][0]="ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a";
 var a=new NativeTrustedPacket(first).presentation;var b=new NativeTrustedPacket(second).presentation;
 var renderer=new SceneRenderer(null);var settings=new SceneSettings(null);renderer.prepare(a,settings);renderer.prepare(b,settings);
 Test.assert(renderer.mapDecision.identity.equals("ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"));Test.assert(renderer.mapDecision.pointVisible(true)&&renderer.mapDecision.matched);
 logger.debug("MAP_IDENTITY same_center_new_launch=true");return true;
}
