import Toybox.Application;
import Toybox.Background;
import Toybox.Communications;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
(:background, :extendedCode)
class FeedService extends System.ServiceDelegate {
    var transfer as NativeTransfer or Null;var assetRequest as Dictionary or Null;var batch as NativeBatch or Null=null;var started as Number=0;var requests as Number=0;
    var deadlineArmed as Boolean=false;var flight as NativeRequestLifecycle;var volatileSnapshot as Array or Null=null;
    function initialize(){ServiceDelegate.initialize();transfer=null;assetRequest=null;flight=new NativeRequestLifecycle();}
    function createTransfer() as NativeTransfer {return new NativeTransfer(configuredFeedUrl(),null);}
    function requestUrl(path as String) as String {return ((transfer as NativeTransfer).base as String)+"/"+path+".txt";}
    function nowMillis() as Number {return System.getTimer();}
    function phoneConnected() as Boolean {try{return System.getDeviceSettings().phoneConnected;}catch(e){return false;}}
    function startDeadline() as Void {started=nowMillis();requests=0;deadlineArmed=true;flight.reset();}
    (:typecheck(false))
    function sendRequest(path as String,callback as Method) as Void {Communications.makeWebRequest(requestUrl(path),{}, {:method=>Communications.HTTP_REQUEST_METHOD_GET,:headers=>{"Accept"=>"text/plain"},:responseType=>Communications.HTTP_RESPONSE_CONTENT_TYPE_TEXT_PLAIN},callback);}
    function cancelOutstanding() as Void {Communications.cancelAllRequests();}
    function rearm() as Void {if(transfer!=null){armFeed(transfer,Time.now().value().toLong());}}
    (:typecheck(false)) function deliverBackground(data) as Void {Background.exit(data);}
    (:typecheck(false)) function leave() as Void {
        if(volatileSnapshot!=null){
            try{deliverBackground({"base"=>transfer.base,"volatileSnapshot"=>volatileSnapshot});return;}
            catch(e){System.println("SF_BG volatile_delivery_failed");volatileSnapshot=null;deliverBackground({"volatileDeliveryFailed"=>true});return;}
        }
        deliverBackground({"provisional"=>true});
    }
    (:typecheck(false))
    function onTemporalEvent() as Void {
        try{var settings=System.getDeviceSettings();var registered=Background.getTemporalEventRegisteredTime();var last=Background.getLastTemporalEventTime();System.println("SF_BG enter phone="+settings.phoneConnected+" registered="+(registered==null?"none":registered.value())+" last="+(last==null?"none":last.value()));}catch(ignore){}
        startDeadline();try{Background.registerForTemporalEvent(new Time.Duration(300));}catch(e){}
        try{transfer=createTransfer();if(transfer.base.equals("")){Background.deleteTemporalEvent();Background.exit(null);return;}batch=new NativeBatch(transfer.store,transfer.base);transfer.load();var now=Time.now().value().toLong();LaunchReminder.wake(transfer,now);var connected=phoneConnected();if(transfer.due(now,connected)){transfer.attempted(now);armFeed(transfer,now);if(connected){requestSnapshot();}else{optional();}}else{optional();}}catch(e){System.println("SF_BG start_error");finish();}
    }
    (:typecheck(false))
    function request(path as String,callback as Method) as Void {if(!flight.canStart()){return;}if(requests>=44||nowMillis()-started>=22000){System.println("SF_BG request_budget");finish();return;}requests+=1;var serial=flight.begin();var pending=new NativeRequestCallback(self,serial,callback);try{sendRequest(path,pending.method(:deliver));}catch(e){flight.abandon();System.println("SF_BG request_error");finish();}}
    (:typecheck(false)) function requestSnapshot() as Void {
        if(!flight.canStart()){return;}if(requests>=44||nowMillis()-started>=22000){finish();return;}
        requests+=1;var serial=flight.begin();var pending=new NativeRequestCallback(self,serial,method(:receiveSnapshot));
        try{Communications.makeWebRequest(transfer.base+"/watch.json",{}, {:method=>Communications.HTTP_REQUEST_METHOD_GET,:headers=>{"Accept"=>"application/json"},:responseType=>Communications.HTTP_RESPONSE_CONTENT_TYPE_JSON},pending.method(:deliver));}catch(e){flight.abandon();System.println("SF_BG snapshot_request_error");finish();}
    }
    (:typecheck(false)) function receiveSnapshot(code,data) as Void {
        if(!callbackAllowed()){return;}
        if(code==200&&data instanceof Dictionary&&data["data"] instanceof Array){
            var snapshot=data["data"];var accepted=false;
            if(snapshot.size()!=7||snapshot[0]!=1){data=null;finish();return;}
            var owner=new NativeTrustedStore(transfer.store,transfer.base);
            try{owner.normalize(snapshot);}catch(e){System.println("SF_BG snapshot_invalid");data=null;finish();return;}
            try{accepted=owner.saveNormalized(snapshot);}catch(e){System.println("SF_BG snapshot_storage_error");
                // The SDK background and foreground heaps are separate. Only
                // a complete response can be offered through bounded OS IPC.
                if(snapshot.size()==7&&snapshot[0]==1){volatileSnapshot=snapshot;}}
            if(accepted){
                try{if(batch!=null&&snapshot[6]!=null){batch.select(snapshot[6]);}}catch(ignore){}
                transfer.completed(true);System.println("SF_BG snapshot_ready");
            }
            if(volatileSnapshot!=null){data=null;finish();return;}
        }
        // Release the parsed response before the bounded asset scanner runs.
        // A failed schedule response can still continue the existing art job;
        // an art failure never rolls back the already published snapshot.
        data=null;optional();
    }
    function callbackAllowed() as Boolean {if(!flight.consume()){return false;}if(deadlineArmed&&nowMillis()-started>=22000){finish();return false;}return true;}
    (:typecheck(false))
    function optional() as Void {try{if(batch!=null){assetRequest=batch.next();if(assetRequest!=null){request(assetRequest["path"],method(:receiveBatch));return;}if(batch.head!=null){finish();return;}}}catch(e){System.println("SF_BG batch_error");}finish();}
    (:typecheck(false))
    function receiveBatch(code as Number,data as Dictionary or String or Null) as Void {if(!callbackAllowed()){return;}try{System.println("SF_BG object_http="+code+" catalog="+(assetRequest["path"].find("wire3/catalogs/")==0));if(code==200&&data instanceof String&&batch.immutable.put(assetRequest,data)){
        // The catalog is the admission prerequisite. Exit now so the foreground
        // can display the validated schedule; the durable pending batch resumes
        // optional visual downloads at the next permitted background event.
        if(assetRequest["path"].find("wire3/catalogs/")==0){System.println("SF_BG catalog_ready");finish();return;}optional();return;}}catch(e){System.println("SF_BG object_error");}finish();}
    (:typecheck(false))
    function finish() as Void {if(flight.finished()){return;}var cancel=flight.finish();if(cancel){try{cancelOutstanding();}catch(e){}}try{rearm();}catch(e){}leave();}
}
// Request transitions: IDLE -> IN_FLIGHT -> IDLE, or either -> ENDED.
// A monotonically increasing identity rejects late and duplicate callbacks.
(:background, :extendedCode, :typecheck(false))
class NativeRequestLifecycle {
    const IDLE=0;const IN_FLIGHT=1;const ENDED=2;
    var state=0;var serial=0;
    function reset(){serial+=1;state=IDLE;}
    function canStart(){return state==IDLE;}
    function begin(){if(!canStart()){return null;}serial+=1;state=IN_FLIGHT;return serial;}
    function isCurrent(id){return state==IN_FLIGHT&&serial==id;}
    function consume(){if(state!=IN_FLIGHT){return false;}state=IDLE;return true;}
    function abandon(){if(state==IN_FLIGHT){state=IDLE;}}
    function finished(){return state==ENDED;}
    function finish(){var cancel=state==IN_FLIGHT;state=ENDED;serial+=1;return cancel;}
}
// Each OS callback is bound to the request that created it.  A delayed or
// duplicate response cannot consume the next request's mutable asset descriptor.
(:background, :extendedCode, :typecheck(false))
class NativeRequestCallback {
    var owner;var serial;var target;
    function initialize(service,id,callback){owner=service;serial=id;target=callback;}
    function deliver(code,data) as Void {
        if(!owner.flight.isCurrent(serial)){return;}
        target.invoke(code,data);
    }
}
// Keep a pending download's earliest registered deadline across foreground
// wakes. The OS enforces five minutes since the last dispatched event.
(:background, :typecheck(false))
function pendingWake(now, next, registered, last, pending) {
    if (pending) {
        if (next > now + 300) { next = now + 300; }
        if (registered != null) {
            var due = registered > now ? registered : now;
            if (due < next) { next = due; }
        }
    }
    if (last != null && next < last + 300) { next = last + 300; }
    return next;
}

// A registered event newer than the last dispatched event belongs to the OS,
// even if its dispatch is late. Do not replace it during foreground reload.
(:background, :typecheck(false))
function registrationNeeded(now, next, registered, last, pending) {
    if (registered == null) { return true; }
    if (registered == next) { return false; }
    if (pending && registered <= now &&
        (last == null || (registered > last && registered >= last + 300))) { return false; }
    return true;
}

(:background, :typecheck(false))
function batchPending(cache) {
    var pending = false;
    try {
        var batch = cache.store.read("sf.batch.pending");
        pending = batch instanceof Dictionary && batch["base"] instanceof String &&
            batch["base"].equals(cache.base) && batch["pending"] == true;
    } catch(e) {}
    // Either half may survive a failed paired write. Preserve the early
    // wake until the batch scanner reconciles both durable markers.
    try {
        var head = cache.store.read("sf.batch.head");
        pending = pending || (head instanceof Dictionary && head["base"] instanceof String &&
            head["base"].equals(cache.base) && head["pending"] == true);
    } catch(e) {}
    return pending;
}

(:background, :extendedCode, :typecheck(false))
function armFeed(cache, now) {
    if (cache.base.equals("")) {
        try { Background.deleteTemporalEvent(); } catch(e) {}
        return;
    }
    var pending = batchPending(cache);
    var registered = Background.getTemporalEventRegisteredTime();
    var last = Background.getLastTemporalEventTime();
    var registeredAt = registered == null ? null : registered.value().toLong();
    var lastAt = last == null ? null : last.value().toLong();
    // The OS may forget its last event after reopening the face. Keep the
    // persisted attempt as a conservative lower bound for registration.
    if(cache.lastAttempt!=null&&cache.lastAttempt<=now&&(lastAt==null||cache.lastAttempt>lastAt)){lastAt=cache.lastAttempt;}
    var next = pendingWake(now, cache.nextWake(now, System.getDeviceSettings().phoneConnected), registeredAt, lastAt, pending);
    var reminder = LaunchReminder.nextWake(cache, now, lastAt);
    if (reminder != null && reminder < next) { next = reminder; }
    if (!registrationNeeded(now, next, registeredAt, lastAt, pending)) { System.println("SF_WAKE registration_kept pending="+pending+" next="+next);return; }
    try {
        Background.registerForTemporalEvent(new Time.Moment(next.toNumber()));System.println("SF_WAKE registration_ok pending="+pending+" next="+next);
    } catch(e) { System.println("SF_WAKE registration_error pending="+pending+" next="+next+" error="+e.getErrorMessage()); }
}
(:background)
function feedUrlValue(value as Object or Null) as String {return value instanceof String?value:"https://jekamas.github.io/SpaceFox";}
(:background)
function configuredFeedUrl() as String {try{return feedUrlValue(Application.Properties.getValue("FeedBaseUrl"));}catch(e){return feedUrlValue(null);}}

