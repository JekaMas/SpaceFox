import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
(:typecheck(false)) module MaskObserver {
 var ids=["none","date","battery"];var current=0;
 function sample() as Void {current=(((System.getTimer()/6000)+0)%(2*ids.size())).toNumber();}
 function white() as Boolean {return (current%2)==1;}
 function selected() as String {return ids[(current/2)%ids.size()];}
 function barcode(dc as Graphics.Dc) as Void {
  var x=(dc.getWidth()-48)/2;dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.fillRectangle(x-2,8,52,10);
  dc.setColor(Graphics.COLOR_WHITE,Graphics.COLOR_TRANSPARENT);dc.fillRectangle(x,10,4,6);dc.fillRectangle(x+40,10,4,6);
  for(var bit=0;bit<6;bit+=1){if((current & (1<<bit))!=0){dc.fillRectangle(x+5+bit*5,10,4,6);}}
 }
 function visible(id as String) as Boolean {return id.equals(selected());}
 function clear(dc as Graphics.Dc) as Void {var color=white()?Graphics.COLOR_WHITE:Graphics.COLOR_BLACK;dc.setColor(color,color);dc.clear();}
}
