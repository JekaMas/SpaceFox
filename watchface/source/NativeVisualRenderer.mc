import Toybox.Graphics;
import Toybox.Lang;

// Descriptors can retain a validated timeline, but the face paints only the
// decoded image at its fixed, aspect-fitted frame.
(:typecheck(false))
class NativeVisualRenderer {
    var bitmap=null;
    function initialize(){}
    function draw(dc,progress,ascent){
        if(bitmap==null){return;}
        dc.setClip(22,118,54,124);dc.drawBitmap(22,118,bitmap);dc.clearClip();
    }
}
