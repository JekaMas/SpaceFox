import Toybox.Lang;
// Events from the watch OS own display state; data and artwork never set it.
class NativeDisplayLifecycle {
    const HIDDEN=0;const LOW=1;const ACTIVE=2;
    var state as Number=HIDDEN;
    var sleeping as Boolean=false;
    var frameMinute as Long or Null=null;
    var lastFitness as Long or Null=null;
    var initialFitness as Boolean=true;
    function rearmInitialFitness() as Void {initialFitness=true;}
    function takeInitialLowFitness() as Boolean {if(state!=LOW||!initialFitness){return false;}initialFitness=false;return true;}
    function resetFitness() as Void {lastFitness=null;}
    function takeFitness(now as Long) as Boolean {if(state!=ACTIVE){return false;}if(lastFitness!=null&&now>=lastFitness&&now-lastFitness<60){return false;}lastFitness=now;initialFitness=false;return true;}
    function frameDue(minute as Long) as Boolean {return frameMinute==null||frameMinute!=minute;}
    function framePainted(minute as Long) as Void {frameMinute=minute;}
    function invalidateFrame() as Void {frameMinute=null;}
    function shown() as Boolean {return state!=HIDDEN;}
    function awake() as Boolean {return !sleeping;}
    function mode() as Number {return state==ACTIVE?1:0;}
    function show() as Boolean {if(state!=HIDDEN){return false;}state=LOW;invalidateFrame();return true;}
    function hide() as Boolean {if(state==HIDDEN){return false;}state=HIDDEN;invalidateFrame();return true;}
    function sleep() as Boolean {if(sleeping){return false;}sleeping=true;return true;}
    function wake() as Boolean {if(!sleeping){return false;}sleeping=false;return true;}
    function setMode(value as Number) as Void {if(state!=HIDDEN){state=value==1?ACTIVE:LOW;}}
}
