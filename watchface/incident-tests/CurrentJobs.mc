import Toybox.Time;

// Test-only synchronous drivers for the real production continuation jobs.
// Individual tests still assert their original integrity and recovery results;
// scheduler/lifecycle behavior is exercised separately by b1ShortWakeResume.
(:typecheck(false)) class TestNativeCache extends NativeCache {
    function initialize(url,adapter){NativeCache.initialize(url,adapter);}
    function load(now){var job=new NativeRestoreJob(self,now,null);while(!job.step()){}return job.accepted?packet:null;}
    function restoreAccepted(now,seal){var job=new NativeRestoreJob(self,now,seal);while(!job.step()){}return job.accepted?packet:null;}
    function accept(raw,now){
        try{var prepared=new NativePreparedBridgeFeed(raw,now,store);while(!prepared.prepareStep()){}var job=new NativeFeedPromotion(self,raw,prepared,now,queueView);while(!job.step()){}return job.accepted;}
        catch(e){failure=e.getErrorMessage().equals("Bridge catalog incomplete")?"admission-retry":"update-rejected";return false;}
    }
}
(:typecheck(false)) class TestNativeIncoming extends NativeIncoming {
    var needsRestore=false;var restoreSeal=null;
    function initialize(adapter,url){NativeIncoming.initialize(adapter,url);}
    function read(name,force){if(!name.equals("feed")){return null;}var job=new NativeIncomingReadJob(self);while(!job.step()){}if(job.result==null){return null;}var done=store.read("sf.incoming.feed.processed");return !force&&done instanceof String&&done.equals(token(job.result[0]))?null:job.result;}
    function admitFeed(cache,now){return admitFeedForView(cache,now,null);}
    function admitFeedForView(cache,now,view){
        needsRestore=false;restoreSeal=cache.commit instanceof Dictionary?cache.commit["seal"]:null;var pending=store.read("sf.incoming.feed");var done=store.read("sf.incoming.feed.processed");if(!(pending instanceof Dictionary)||cache.packet!=null&&pending["sha256"] instanceof String&&done instanceof String&&token(pending).equals(done)){return false;}
        var commitKey=cache.commitKey;cache.releaseForTransfer(now);var accepted=false;var row=null;
        try{row=read("feed",true);if(row!=null&&row[0]["kind"] instanceof String&&row[0]["kind"].equals("feed")){cache.queueView=view;try{accepted=cache.accept(takeRaw(row),now);}finally{cache.queueView=null;}if(accepted||!cache.failure.equals("admission-retry")){processed("feed",row[0]);}}}catch(e){}
        if(!accepted){if(view!=null){view.clearForRestore();}cache.packet=null;cache.commit=null;cache.commitKey=commitKey;if(view==null){var restore=new NativeRestoreJob(cache,now,restoreSeal);while(!restore.step()){} }else{needsRestore=true;}}
        return accepted;
    }
}
(:typecheck(false)) function nativeTestRestoreApp(app){var job=new NativeRestoreJob(app.feed,Time.now().value().toLong(),app.restoreSeal);while(!job.step()){}if(job.accepted){app.restoreSeal=null;NativeForegroundApp.display(app,app.feed);NativeForegroundApp.savePlan(app.feed,app.feed.packet.document["refreshPolicy"],app.view);}else{app.restorePending=true;}app.view.prepareRenderer();}
(:typecheck(false)) class TestNativeBridgeFeed extends NativePreparedBridgeFeed {
    function initialize(text,now,adapter){NativePreparedBridgeFeed.initialize(text,now,adapter);while(!prepareStep()){} }
}
(:typecheck(false)) class TestNativeSfrBuild extends NativeSfrBuild {
    function initialize(adapter,url,packet){NativeSfrBuild.initialize(adapter,url,packet);while(!beginStep()){} }
    function prepareRole(name){var r=roleRef(name);if(r==null){return null;}var job=new NativeSfrReadJob(self,r,false);while(!job.step()){}return finishRole(name,job.result);}
}
