import Toybox.Graphics;
import Toybox.Lang;

(:typecheck(false))
class NativeVisualRenderer {
    var bitmap=null;var manifest=null;var animations=null;var prepared=0;var transform=null;var drawOptions=null;var fitScale=1.0;var frameX=22.0;var frameY=118.0;var frameScale=1.0;
    function initialize(){transform=new Graphics.AffineTransform();drawOptions={:transform=>transform};}
    function duration(){return animations!=null&&animations[0]>0?animations[0].toFloat()/1000.0:2.5;}
    // Source translations use the SAME uniform aspect fit on both axes. The
    // source is already centered in54x124; scale pivots around its center27,62.
    function prepareCanvas(canvas){fitScale=54.0/canvas[0];var sy=124.0/canvas[1];if(sy<fitScale){fitScale=sy;}}
    function prepareFrame(progress,ascent){
        frameX=22.0;frameY=118.0-ascent;frameScale=1.0;
        if(animations!=null&&animations[0]>0&&progress>0){var elapsed=(progress>1?1.0:progress)*animations[0];var frames=animations[1];for(var i=1;i<frames.size();i+=1){if(elapsed<=frames[i][0]){var a=frames[i-1];var b=frames[i];var f=(elapsed-a[0])/(b[0]-a[0]);frameX+=(a[1]+(b[1]-a[1])*f)*fitScale/32.0;frameY+=(a[2]+(b[2]-a[2])*f)*fitScale/32.0;frameScale=(a[3]+(b[3]-a[3])*f)/256.0;break;}}}
    }
    // The source transform scales about the 54x124 frame center. Use the
    // union of translation-before/after-scale bounds and a pixel of rounding
    // margin: only frames that cannot intersect the intended clip are skipped.
    function frameIntersects(ascent){
        var tx=27.0-27.0*frameScale;var ty=62.0-62.0*frameScale;
        var sx=tx*frameScale;var sy=ty*frameScale;
        var left=frameX+(tx<sx?tx:sx)-1;var right=frameX+(tx>sx?tx:sx)+bitmap.getWidth()*frameScale+1;
        var top=frameY+(ty<sy?ty:sy)-1;var bottom=frameY+(ty>sy?ty:sy)+bitmap.getHeight()*frameScale+1;
        return right>22 && left<76 && bottom>118-ascent && top<242-ascent;
    }
    function draw(dc,progress,ascent){
        if(bitmap==null){return;}prepareFrame(progress,ascent);if(!frameIntersects(ascent)){return;}
        transform.setToTranslation((27-27*frameScale).toFloat(),(62-62*frameScale).toFloat());transform.scale(frameScale.toFloat(),frameScale.toFloat());
        dc.setClip(22,118-ascent,54,124);dc.drawBitmap2(frameX,frameY,bitmap,drawOptions);dc.clearClip();
    }
}
