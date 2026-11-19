import Toybox.System;import Toybox.Graphics;import Toybox.Test;
(:test,:typecheck(false)) class HealthFrameClock extends WatchClock {var now=1800000000;function utcSeconds(){return now;}function localTimeText(){return "08:25";}function localCalendar(){return [3,17,11];}}
(:typecheck(false)) module HealthPaint {var energy;var stress;var paints=0;}
(:test,:typecheck(false)) class HealthFrameRenderer extends SceneRenderer {
 function initialize(p){SceneRenderer.initialize(p);}
 function active(dc,current,settings,values,fitness,progress){HealthPaint.energy=values["energy"];HealthPaint.stress=values["stress"];HealthPaint.paints+=1;}
}
(:test,:typecheck(false)) class HealthFrameView extends MenuView {
 var clock;
 function initialize(){clock=new HealthFrameClock();SpaceFoxView.initialize(clock,new ScheduleState(null,"empty"));timers=[];}
 function createSceneRenderer() as SceneRenderer {return new HealthFrameRenderer(presentation);}
}
(:test,:typecheck(false)) function incidentFirstPaintExpiry(logger){
 var v=new HealthFrameView();var f=new IncidentFields();f.api=new IncidentApi();f.samples[23]=[new IncidentSample(68,1800000000)];f.samples[22]=[new IncidentSample(0,1800000000)];f.start(["steps","energy","heart","stress"],f.method(:callback));f.read("en");v.selectedFields=f;v.fitness.selectedFields=f;v.values={"steps"=>1,"energy"=>f.healthValue("energy"),"heart"=>null,"stress"=>f.healthValue("stress")};
 var dc=new MenuDraw();v.onShow();v.onLayout(dc);v.onUpdate(dc);Test.assert(HealthPaint.energy==68&&HealthPaint.stress==0);var before=f.historyCalls;v.onHide();v.clock.now+=301;f.fakeNow+=301;v.onShow();v.onLayout(dc);v.onUpdate(dc);
 Test.assertMessage(HealthPaint.energy==null&&HealthPaint.stress==null,"first resumed paint must expire old samples before delayed refresh");Test.assert(f.historyCalls==before);v.onHide();logger.debug("FIRST_PAINT expiry=301 no_provider_poll=true paints="+HealthPaint.paints);return true;
}
