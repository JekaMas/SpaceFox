
import Toybox.Lang;

// Garmin's current Body Battery complication is a Number or null. Unlike a
// history sample it has no application-invented age cutoff. Subscribe only
// while the energy role is visible; no source values leave the device.
(:extendedCode, :typecheck(false))
class MappedBodyBatterySource {
    var id=null;var subscribed=false;var value as Number or Null=null;var observed=false;
    function start(callback as Method) as Boolean {
        if(subscribed){return true;}
        try {
            if(id==null){id=new D03Id(D03Complications.BODY);}
            D03Complications.registerComplicationChangeCallback(callback);
            if(!D03Complications.subscribeToUpdates(id)){D03Complications.registerComplicationChangeCallback(null);return false;}
            subscribed=true;return true;
        } catch(e) {
            try{D03Complications.registerComplicationChangeCallback(null);}catch(ignored){}
            subscribed=false;return false;
        }
    }
    function read() as Number or Null {
        value=null;observed=true;
        try {
            if(id==null){id=new D03Id(D03Complications.BODY);}
            var item=D03Complications.getComplication(id);var current=item.value;
            if(current instanceof Number && current>=0 && current<=100){value=current;}
        } catch(e) {}
        return value;
    }
    function stop() as Void {
        if(subscribed){try{D03Complications.unsubscribeFromUpdates(id);}catch(e){}try{D03Complications.registerComplicationChangeCallback(null);}catch(e){}}
        subscribed=false;value=null;observed=false;
    }
}
