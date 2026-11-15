import Toybox.Lang;
import Toybox.Graphics;
import Toybox.Test;

// Dynamic test double counts actual renderer draw calls; both animations pass
// the production NativeAnimation validator, including its limit values.
(:test,:typecheck(false)) class D03RocketBitmap { function getWidth(){return 54;} function getHeight(){return 124;} }
(:test,:typecheck(false)) class D03RocketDc {
 var draws=0;var clips=0;var clears=0;
 function setClip(x,y,w,h){clips+=1;}
 function drawBitmap2(x,y,bitmap,options){draws+=1;}
 function clearClip(){clears+=1;}
}
(:test,:typecheck(false)) function display03SkipInvisibleRocket(logger){
 var invisible=[2500,[[0,0,0,256],[2500,2048,0,128]]];
 var partial=[2500,[[0,0,0,256],[2500,1248,0,128]]];
 new NativeAnimation().validate(invisible);new NativeAnimation().validate(partial);
 var r=new NativeVisualRenderer();r.bitmap=new D03RocketBitmap();r.prepareCanvas([54,124]);
 var dc=new D03RocketDc();r.animations=invisible;r.draw(dc,1.0,0);
 logger.debug("ROCKET_CLIP invisible draws="+dc.draws+" clips="+dc.clips);
 Test.assert(dc.draws==0&&dc.clips==0&&dc.clears==0);
 r.animations=partial;r.draw(dc,1.0,0);Test.assert(dc.draws==1&&dc.clips==1&&dc.clears==1);
 r.animations=invisible;r.draw(dc,0.0,0);Test.assert(dc.draws==2&&dc.clips==2&&dc.clears==2);
 // Independent SDK affine matrix oracle: never cull an intersecting transformed
 // raster, including near-boundary positions and all admitted scale extrema.
 var scales=[0.5,0.75,1.0,1.5,2.0];var shifts=[-150,-80,-40,-1,0,1,39,64,150];var checked=0;
 for(var i=0;i<scales.size();i+=1){for(var j=0;j<shifts.size();j+=1){for(var k=0;k<shifts.size();k+=1){
  var scale=scales[i];r.frameScale=scale;r.frameX=22.0+shifts[j];r.frameY=118.0+shifts[k];
  var matrix=new Graphics.AffineTransform();matrix.setToTranslation((27-27*scale).toFloat(),(62-62*scale).toFloat());matrix.scale(scale.toFloat(),scale.toFloat());
  var a=matrix.transformPoint([0.0,0.0]);var b=matrix.transformPoint([54.0,124.0]);
  var intersects=r.frameX+b[0]>22&&r.frameX+a[0]<76&&r.frameY+b[1]>118&&r.frameY+a[1]<242;
  if(intersects){Test.assert(r.frameIntersects(0));}checked+=1;
 }}}
 logger.debug("ROCKET_CLIP native affine comparisons="+checked);Test.assert(checked==405);return true;
}
