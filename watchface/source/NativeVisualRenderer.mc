import Toybox.Graphics;
import Toybox.Lang;

// Descriptors can retain a validated timeline, but the face paints only the
// decoded image at its fixed, aspect-fitted frame.
(:typecheck(false))
class NativeVisualRenderer {
    var bitmap=null;var manifest=null;var animations=null;var prepared=0;
    function initialize(){}
    function prepareCanvas(canvas){}
    function draw(dc,progress,ascent){
        if(bitmap==null){return;}
        dc.setClip(22,118,54,124);dc.drawBitmap(22,118,bitmap);dc.clearClip();
    }
}
