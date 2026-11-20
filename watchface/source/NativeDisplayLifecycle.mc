import Toybox.Lang;
import Toybox.System;
// Events from the watch OS own display state; data and artwork never set it.
class NativeDisplayLifecycle {
    const HIDDEN=0;const LOW=1;const ACTIVE=2;const OFF=3;
    var state as Number=HIDDEN;
    var frameMinute as Long or Null=null;
    var lastFitness as Long or Null=null;
    var initialFitness as Boolean=true;
    function rearmInitialFitness() as Void {initialFitness=true;}
    function takeInitialLowFitness() as Boolean {if(state!=LOW||!initialFitness){return false;}initialFitness=false;return true;}
    function resetFitness() as Void {lastFitness=null;}
    function takeFitness(now as Long) as Boolean {if(state!=ACTIVE){return false;}if(lastFitness!=null&&now>=lastFitness&&now-lastFitness<60){return false;}lastFitness=now;initialFitness=false;return true;}
    function permitsPaint(minute as Long) as Boolean {return state==ACTIVE||(state==LOW&&(frameMinute==null||frameMinute!=minute));}
    function framePainted(minute as Long) as Void {frameMinute=minute;}
    function invalidateFrame() as Void {frameMinute=null;}
    function shown() as Boolean {return state!=HIDDEN;}
    function mode() as Number {if(state==OFF){return -1;}return state==ACTIVE?1:0;}
    function permitsFrame() as Boolean {return state==LOW||state==ACTIVE;}
    function permitsActive() as Boolean {return state==ACTIVE;}
    function show() as Boolean {if(state!=HIDDEN){return false;}state=OFF;invalidateFrame();return true;}
    function hide() as Boolean {if(state==HIDDEN){return false;}state=HIDDEN;invalidateFrame();return true;}
    // Raw OS observation is the only authority for visible display mode.
    function observe(value as System.DisplayMode) as Boolean {
        if(state==HIDDEN){return false;}
        var next=value==System.DISPLAY_MODE_OFF?OFF:(value==System.DISPLAY_MODE_HIGH_POWER?ACTIVE:LOW);
        if(state==next){return false;}state=next;invalidateFrame();resetFitness();return true;
    }
}
