import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
(:typecheck(false)) module MaskObserver {
 var cases=["00:00","17:57","08:38"];var current=0;
 function sample(){current=((System.getTimer()/8000)%12).toNumber();}
 function clock(){return cases[current/4];}
 function utc(){return 1794551040+(current%4)*60;}
 function visible(id){return id.equals("clock");}
 function clear(dc){dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();}
 function barcode(dc){var x=(dc.getWidth()-48)/2;dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.fillRectangle(x-2,8,52,10);dc.setColor(Graphics.COLOR_WHITE,Graphics.COLOR_TRANSPARENT);dc.fillRectangle(x,10,4,6);dc.fillRectangle(x+40,10,4,6);for(var bit=0;bit<6;bit+=1){if((current & (1<<bit))!=0){dc.fillRectangle(x+5+bit*5,10,4,6);}}}
}
