import Toybox.Application;
import Toybox.Background;
import Toybox.Communications;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
(:background)
class FeedService extends System.ServiceDelegate {
    var transfer as NativeTransfer or Null;var assetRequest as Dictionary or Null;var batch as NativeBatch or Null=null;var started as Number=0;var requests as Number=0;
    function initialize(){ServiceDelegate.initialize();transfer=null;assetRequest=null;}
    function createTransfer() as NativeTransfer {return new NativeTransfer(configuredFeedUrl(),null);}
    function requestUrl(path as String) as String {return ((transfer as NativeTransfer).base as String)+"/"+path+".txt";}
    (:typecheck(false))
    function onTemporalEvent() as Void {
        started=System.getTimer();requests=0;try{Background.registerForTemporalEvent(new Time.Duration(3600));}catch(e){}
        try{transfer=createTransfer();if(transfer.base.equals("")){Background.deleteTemporalEvent();Background.exit(null);return;}batch=new NativeBatch(transfer.store,transfer.base);transfer.load();var now=Time.now().value().toLong();LaunchReminder.wake(transfer,now);if(transfer.due(now)){transfer.attempted(now);armFeed(transfer,now);request("feed.json",method(:receive));}else{optional();}}catch(e){finish();}
    }
    (:typecheck(false))
    function request(path as String,callback as Method) as Void {if(requests>=44||System.getTimer()-started>=22000){finish();return;}requests+=1;try{Communications.makeWebRequest(requestUrl(path),{}, {:method=>Communications.HTTP_REQUEST_METHOD_GET,:headers=>{"Accept"=>"text/plain"},:responseType=>Communications.HTTP_RESPONSE_CONTENT_TYPE_TEXT_PLAIN},callback);}catch(e){finish();}}
    (:typecheck(false))
    function receive(code as Number,data as Dictionary or String or Null) as Void {

        try{if(code==200&&data instanceof String){if(transfer.stage("feed",data,null)&&batch.begin(data)){optional();return;}}}catch(e){}finish();
    }
    (:typecheck(false))
    function optional() as Void {try{if(batch!=null){assetRequest=batch.next();if(assetRequest!=null){request(assetRequest["path"],method(:receiveBatch));return;}if(batch.head!=null){finish();return;}}}catch(e){}finish();}
    (:typecheck(false))
    function receiveBatch(code as Number,data as Dictionary or String or Null) as Void {try{if(code==200&&data instanceof String&&batch.immutable.put(assetRequest,data)){
        // The catalog is the admission prerequisite. Exit now so the foreground
        // can display the validated schedule; the durable pending batch resumes
        // optional visual downloads at the next permitted background event.
        if(assetRequest["path"].find("wire3/catalogs/")==0){finish();return;}optional();return;}}catch(e){}finish();}
    (:typecheck(false))
    function finish() as Void {try{if(transfer!=null){armFeed(transfer,Time.now().value().toLong());}}catch(e){}Background.exit({"provisional"=>true});}
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

(:background, :typecheck(false))
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
    var next = pendingWake(now, cache.nextWake(now), registeredAt, lastAt, pending);
    var reminder = LaunchReminder.nextWake(cache, now, lastAt);
    if (reminder != null && reminder < next) { next = reminder; }
    if (!registrationNeeded(now, next, registeredAt, lastAt, pending)) { return; }
    try {
        Background.registerForTemporalEvent(new Time.Moment(next.toNumber()));
    } catch(e) {  }
}
(:background)
function feedUrlValue(value as Object or Null) as String {return value instanceof String?value:"https://jekamas.github.io/SpaceFox";}
(:background)
function configuredFeedUrl() as String {try{return feedUrlValue(Application.Properties.getValue("FeedBaseUrl"));}catch(e){return feedUrlValue(null);}}

