import Toybox.Graphics; import Toybox.Lang; import Toybox.System; import Toybox.Test;
(:test,:typecheck(false)) class PeerClock extends WatchClock {
 var now=0; function initialize(t){ WatchClock.initialize();now=t; } function utcSeconds(){return now;} function localTimeText(){return "08:08";}
}
(:test,:typecheck(false)) class PeerRenderer extends SceneRenderer {
 var activeText=null;var lowText=null;var activeDrawn=false;
 function initialize(){SceneRenderer.initialize(null);}
 function text(dc,x,y,font,value,color,width,contour){if(y==202){activeText=value;activeDrawn=true;}return SceneRenderer.text(dc,x,y,font,value,color,width,contour);}
 function aod(dc,current,minute,settings){lowText=current.countdown;SceneRenderer.aod(dc,current,minute,settings);}
}
(:test,:typecheck(false)) function peerCurrentCountdownTable(logger){
 var target=1794609900; var offsets=[-176523,-59,0,1,901];
 var active=["T- 49:02:03","T- 00:00:59","T+ 00:00:00","T+ 00:00:01","T+ 00:15:01"];
 var low=["T- 49:03","T- 00:01","T+ 00:00","T+ 00:00","T+ 00:15"];
 var bmp=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();
 for(var i=0;i<offsets.size();i+=1){
  var clock=new PeerClock(target+offsets[i]);var view=new SpaceFoxView(clock,new ScheduleState(target,"exact"));var renderer=new PeerRenderer();renderer.prepare(null,view.settings);view.renderer=renderer;
  view.updateForDisplayMode(bmp.getDc(),System.DISPLAY_MODE_HIGH_POWER);Test.assert(renderer.activeDrawn);Test.assertEqual(renderer.activeText,active[i]);
  view.onEnterSleep();view.updateForDisplayMode(bmp.getDc(),System.DISPLAY_MODE_LOW_POWER);Test.assertEqual(renderer.lowText,low[i]);
  logger.debug("PAIR offset="+offsets[i]+" active="+renderer.activeText+" low="+renderer.lowText+" sameTarget=true");
 }
 return true;
}
