import Toybox.Lang;
import Toybox.Graphics;
import Toybox.Test;

// Animation remains validated as input; the accepted display contract is static.
(:test,:typecheck(false)) class D03RocketBitmap { function getWidth(){return 54;} function getHeight(){return 124;} }
(:test,:typecheck(false)) class D03RocketDc {
 var draws=0;var clips=0;var clears=0;
 function setClip(x,y,w,h){clips+=1;}
 function drawBitmap(x,y,bitmap){draws+=1;}
 function clearClip(){clears+=1;}
}
(:test,:typecheck(false)) function display03SkipInvisibleRocket(logger){
 var invisible=[2500,[[0,0,0,256],[2500,2048,0,128]]];
 var partial=[2500,[[0,0,0,256],[2500,1248,0,128]]];
 new NativeAnimation().validate(invisible);new NativeAnimation().validate(partial);
 var r=new NativeVisualRenderer();r.bitmap=new D03RocketBitmap();var dc=new D03RocketDc();
 r.draw(dc,0.0,0);r.draw(dc,1.0,0);
 Test.assert(dc.draws==2&&dc.clips==2&&dc.clears==2);
 logger.debug("ROCKET_STATIC draws="+dc.draws+" clips="+dc.clips);return true;
}
