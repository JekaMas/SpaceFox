import Toybox.Application;
import Toybox.Background;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
import Toybox.WatchUi;
(:typecheck(false)) class ArtProbeClock extends WatchClock {
 var advance=0l;function utcSeconds(){return Time.now().value().toLong()+advance;}
}
(:typecheck(false)) class ArtProbeView extends SpaceFoxView {
 var probeClock;var tested=false;var completed=false;
 function initialize(c){SpaceFoxView.initialize(c,new ScheduleState(null,"empty"));probeClock=c;}
 function onUpdate(dc){
  SpaceFoxView.onUpdate(dc);
  if(!tested&&sfrBuild!=null){
   tested=true;var build=sfrBuild;var generation=sceneLifecycle.generation;var before=System.getSystemStats().usedMemory;
   probeClock.advance=60l;refreshFitness();
   System.println("SF_ART_HEALTH building="+(sfrBuild==build)+" generation_same="+(sceneLifecycle.generation==generation)+" used_before="+before+" used_after="+System.getSystemStats().usedMemory+" bodyReady="+(values["energy"]!=null)+" heartReady="+(values["heart"]!=null)+" stressReady="+(values["stress"]!=null));
  }
  if(!completed&&downloaded!=null){completed=true;System.println("SF_ART_COMPLETE used_sample="+System.getSystemStats().usedMemory+" metric="+tested);}
 }
}
(:background,:typecheck(false)) class ArtProbeApp extends SpaceFoxApp {
 function initialize(){SpaceFoxApp.initialize();}
 function getInitialView(){view=new ArtProbeView(new ArtProbeClock());try{view.setSettings(initialSettings());}catch(e){}view.bootstrapPending=true;view.pendingLoader=method(:reloadFeed);view.cancelAdmission=null;view.syncDisplayMode(System.getDisplayMode());return [view];}
}
