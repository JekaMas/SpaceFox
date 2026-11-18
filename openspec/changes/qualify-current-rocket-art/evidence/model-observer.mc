import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;
(:typecheck(false)) class ModelsClock extends WatchClock {function utcSeconds() as Number{return 1795041600;} function localTimeText() as String{return "08:25";}}
(:typecheck(false)) class ModelsObserverView extends SpaceFoxView {
 var ids=["ll2:configuration:164","ll2:configuration:161","ll2:configuration:143","ll2:configuration:173"];
 var stage=0;var drawn=-1;var shownAt=0;
 function initialize(){SpaceFoxView.initialize(new ModelsClock(),new ScheduleState(null,"empty"));loadStage();}
 function loadStage(){setContext(new SceneContext({"id"=>"controlled-model-"+stage,"rocket"=>"Model observer","modelId"=>ids[stage],"point"=>[-80.6,28.6],"target"=>1795042200,"precision"=>"exact"}));}
 function onUpdate(dc as Graphics.Dc) as Void {
  SpaceFoxView.onUpdate(dc);
  if(renderer!=null && renderer.art!=null && renderer.model==NativeModels.resource(ids[stage]) && drawn!=stage){
   drawn=stage;shownAt=System.getTimer();var stats=System.getSystemStats();System.println("MODEL_FRAME stage="+stage+" id="+ids[stage]+" total="+stats.totalMemory+" used="+stats.usedMemory);
  }
  if(drawn==stage && stage<3 && System.getTimer()-shownAt>3000){stage+=1;loadStage();}
 }
}
(:typecheck(false)) class ModelsObserverApp extends Application.AppBase {
 function initialize(){AppBase.initialize();}
 function getInitialView(){return [new ModelsObserverView()];}
}
