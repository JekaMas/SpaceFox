import Toybox.System;
import Toybox.Lang;
import Toybox.Time;
// Off in production. Experiment applications enable only SDK memory/time samples.
// No health values, network telemetry or on-watch measurement log is persisted.
(:background)
module NativeMetrics {
    var enabled as Boolean=false;
    var traceStores as Boolean=false;
    var ownerTag as String="";
    var highest as Number=0;
    function failure(value as Object or Null) as Void {if(enabled){System.println("NATIVE_REJECTION "+value+" owner="+ownerTag);}}
    function writes(phase as String,value as Number) as Void {if(enabled){System.println("NATIVE_WRITES phase="+phase+" count="+value+" owner="+ownerTag);}}
    function sample(phase as String) as Void {
        if(!enabled){return;}var stats=System.getSystemStats();if(stats.usedMemory>highest){highest=stats.usedMemory;}
        System.println("NATIVE_METRIC phase="+phase+" used="+stats.usedMemory+" free="+stats.freeMemory+" total="+stats.totalMemory+" sampledHigh="+highest+" utc="+Time.now().value()+" ms="+System.getTimer()+" owner="+ownerTag);
    }
}
