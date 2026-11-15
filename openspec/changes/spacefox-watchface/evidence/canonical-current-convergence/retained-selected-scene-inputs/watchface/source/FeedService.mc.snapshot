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
    function requestUrl(path as String) as String {return ((transfer as NativeTransfer).base as String)+"/"+path;}
    (:typecheck(false))
    function onTemporalEvent() as Void {
        started=System.getTimer();requests=0;NativeMetrics.sample("temporal-start");try{Background.registerForTemporalEvent(new Time.Duration(3600));}catch(e){}
        try{transfer=createTransfer();if(transfer.base.equals("")){Background.deleteTemporalEvent();Background.exit(null);return;}batch=new NativeBatch(transfer.store,transfer.base);transfer.load();var now=Time.now().value().toLong();NativeMetrics.sample("pre-request");if(transfer.due(now)){transfer.attempted(now);request("feed.json",method(:receive));}else{optional();}}catch(e){finish();}
    }
    (:typecheck(false))
    function request(path as String,callback as Method) as Void {if(requests>=44||System.getTimer()-started>=22000){finish();return;}requests+=1;try{if(NativeMetrics.enabled){System.println("NATIVE_GET path="+path+" n="+requests+" owner="+NativeMetrics.ownerTag);}Communications.makeWebRequest(requestUrl(path),{}, {:method=>Communications.HTTP_REQUEST_METHOD_GET,:headers=>{"Accept"=>"application/json"},:responseType=>Communications.HTTP_RESPONSE_CONTENT_TYPE_TEXT_PLAIN},callback);}catch(e){finish();}}
    (:typecheck(false))
    function receive(code as Number,data as Dictionary or String or Null) as Void {
        NativeMetrics.sample("feed-transfer-complete");if(NativeMetrics.enabled){System.println("NATIVE_RESPONSE feed code="+code+" characters="+(data instanceof String?data.length():-1)+" owner="+NativeMetrics.ownerTag);}
        try{if(code==200&&data instanceof String){var before=transfer.store.writes;if(transfer.stage("feed",data,null)){batch.begin(data);}NativeMetrics.writes("provisional-feed",transfer.store.writes-before);NativeMetrics.sample("feed-provisional-staged");}}catch(e){NativeMetrics.failure(e.getErrorMessage());}optional();
    }
    (:typecheck(false))
    function optional() as Void {try{if(batch!=null){assetRequest=batch.next();if(assetRequest!=null){request(assetRequest["path"],method(:receiveBatch));return;}if(batch.head!=null){finish();return;}}}catch(e){NativeMetrics.failure(e.getErrorMessage());}finish();}
    (:typecheck(false))
    function receiveBatch(code as Number,data as Dictionary or String or Null) as Void {NativeMetrics.sample("batch-transfer-complete");try{if(code==200&&data instanceof String&&batch.immutable.put(assetRequest,data)){optional();return;}}catch(e){NativeMetrics.failure(e.getErrorMessage());}finish();}
    (:typecheck(false))
    function finish() as Void {try{if(transfer!=null){armFeed(transfer,Time.now().value().toLong());}}catch(e){}if(transfer!=null){NativeMetrics.writes("background-total",transfer.store.writes);}NativeMetrics.sample("background-exit");Background.exit({"provisional"=>true});}
}
(:background, :typecheck(false))
function armFeed(cache,now){
    if(cache.base.equals("")){try{Background.deleteTemporalEvent();}catch(e){}return;}var next=cache.nextWake(now);try{var batch=cache.store.read("sf.batch.pending");if(batch instanceof Dictionary&&batch["base"] instanceof String&&batch["base"].equals(cache.base)&&batch["pending"]==true&&next>now+300){next=now+300;}}catch(e){}var last=Background.getLastTemporalEventTime();if(last!=null&&next<last.value().toLong()+300){next=last.value().toLong()+300;}try{Background.registerForTemporalEvent(new Time.Moment(next.toNumber()));if(NativeMetrics.enabled){var registered=Background.getTemporalEventRegisteredTime();System.println("NATIVE_SCHEDULE now="+now+" requested="+next+" registered="+(registered==null?"null":registered.value())+" last="+(last==null?"null":last.value())+" owner="+NativeMetrics.ownerTag);NativeMetrics.sample("temporal-scheduled");}}catch(e){NativeMetrics.failure(e.getErrorMessage());}
}
(:background)
function configuredFeedUrl() as String {try{var value=Application.Properties.getValue("FeedBaseUrl");return value instanceof String?value:"";}catch(e){return "";}}

