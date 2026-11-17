import Toybox.Lang;
// Events from the watch OS own display state; data and artwork never set it.
class NativeDisplayLifecycle {
    const HIDDEN=0;const LOW=1;const ACTIVE=2;
    var state as Number=HIDDEN;
    var sleeping as Boolean=false;
    var frameMinute as Long or Null=null;
    function frameDue(minute as Long) as Boolean {return frameMinute==null||frameMinute!=minute;}
    function framePainted(minute as Long) as Void {frameMinute=minute;}
    function invalidateFrame() as Void {frameMinute=null;}
    function shown() as Boolean {return state!=HIDDEN;}
    function awake() as Boolean {return !sleeping;}
    function mode() as Number {return state==ACTIVE?1:0;}
    function show() as Void {if(state==HIDDEN){state=LOW;invalidateFrame();}}
    function hide() as Void {state=HIDDEN;invalidateFrame();}
    function sleep() as Void {sleeping=true;}
    function wake() as Void {sleeping=false;}
    function setMode(value as Number) as Void {if(state!=HIDDEN){state=value==1?ACTIVE:LOW;}}
}
