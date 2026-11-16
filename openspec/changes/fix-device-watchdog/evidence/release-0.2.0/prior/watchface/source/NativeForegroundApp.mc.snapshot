import Toybox.Time;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Background;
(:extendedCode, :typecheck(false))
module NativeForegroundApp {
    function initial(app) as [WatchUi.WatchFace] {
        app.view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
        try{app.view.setSettings(app.initialSettings());}catch(e){}app.view.bootstrapPending=true;app.view.pendingLoader=app.method(:reloadFeed);app.view.cancelAdmission=app.method(:cancelWork);app.view.syncDisplayMode(System.getDisplayMode());return [app.view as WatchUi.WatchFace];
    }
    function display(app,cache){
        if(app.view==null){return;}var now=Time.now().value().toLong();if(cache.packet==null||app.view.packet!=cache.packet||cache.packet.document.hasKey("dictionaries")||app.view.context!=cache.packet.presentation){app.view.setPacket(cache.packet);}if(cache.packet!=null){try{var owner=cache.packet.document["publisher"]["instance"];var saved=new NativeUpcomingCache(cache.store,cache.base,owner).load();app.view.mergeSaved(saved,now,cache.packet.terminalUpdates);}catch(e){}app.view.setAssetCache(new NativeRenderSource(cache.store,cache.base,cache.packet.bridge));}LaunchReminderForeground.publishQueue(cache,now,app.view.queueSnapshots());
        // Background uses this compact source-bound result rather than treating
        // an unvalidated commit marker as an accepted schedule.
        try{var accepted=cache.packet!=null;var prior=cache.store.read("sf.transfer.ready");if(!(prior instanceof Dictionary)||!(prior["base"] instanceof String)||!prior["base"].equals(cache.base)||prior["accepted"]!=accepted){cache.store.write("sf.transfer.ready",{"base"=>cache.base,"accepted"=>accepted});}}catch(e){}
    }
    function savePlan(cache,p,view){
        var next=[p["normal_interval_seconds"],p["near_interval_seconds"],p["fast_interval_seconds"]];var targets=[];var scenes=view.queueSnapshots();for(var i=0;i<scenes.size();i+=1){var value=scenes[i].retentionTarget;if(i==0&&cache.packet.presentation==scenes[i]){value=cache.packet.refreshTarget();}if(value!=null&&targets.indexOf(value)<0){targets.add(value);}}var target=targets.size()>0?targets[0]:null;
        var old=cache.store.read("sf.transfer.plan");if(old instanceof Dictionary&&old["base"] instanceof String&&old["base"].equals(cache.base)&&old["target"]==target&&nativeSame(old["targets"],targets)&&old["policy"] instanceof Array&&old["policy"].size()==3&&old["policy"][0]==next[0]&&old["policy"][1]==next[1]&&old["policy"][2]==next[2]){return;}cache.store.write("sf.transfer.plan",{"base"=>cache.base,"target"=>target,"targets"=>targets,"policy"=>next});
    }
    // Restore one stage per timer callback. First display is independent of
    // strict cache reconstruction; an existing scene remains the fallback.
    function restoreStep(app){
        var selected=app.feed;var url=new NativeTransfer(configuredFeedUrl(),null).base;
        if(!(selected instanceof NativeCache)||!selected.base.equals(url)){if(app.restoreJob!=null){app.restoreJob.dispose();}app.restoreJob=null;app.restoreSeal=null;app.restorePending=false;app.view.admissionPending=false;reload(app);return;}
        if(app.restoreJob==null){app.view.stopFitness();app.view.stopAnimation();app.view.cancelSfrBuild();app.view.releaseVisualForSettings();app.view.assetCache=null;app.view.visualKey=null;app.view.presentation.suspend();app.view.admissionPending=true;WatchUi.requestUpdate();app.restoreJob=new NativeRestoreJob(selected,Time.now().value().toLong(),app.restoreSeal);app.queueRestore();return;}
        if(!app.restoreJob.step()){app.queueRestore();return;}
        var accepted=app.restoreJob.accepted;app.restoreJob=null;app.view.admissionPending=false;
        if(accepted){app.restoreSeal=null;app.restorePending=false;display(app,selected);savePlan(selected,selected.packet.document["refreshPolicy"],app.view);}
        else if(app.restoreSeal==null){app.restorePending=false;display(app,selected);}
        if(!app.restorePending){var incoming=new NativeIncoming(selected.store,selected.base);if(hasNewIncoming(selected,incoming)){beginAdmission(app,selected,incoming,Time.now().value().toLong());return;}}
        if(!app.restorePending){app.view.resumeAfterAdmission();}
        var transfer=new NativeTransfer(selected.base,selected.store);transfer.load();armFeed(transfer,Time.now().value().toLong());
    }
    // Only a new provisional feed can replace the scene. Duplicate callbacks
    // leave an in-progress visual build and its generation untouched.
    function hasNewIncoming(cache, incoming) {
        var pending = cache.store.read("sf.incoming.feed");
        if (!incoming.validFeedMarker(pending)) { return false; }
        var token=incoming.token(pending);var deferred=cache.store.read("sf.incoming.feed.deferred");
        if(deferred instanceof Dictionary&&deferred["token"] instanceof String&&deferred["token"].equals(token)&&(deferred["until"] instanceof Number||deferred["until"] instanceof Long)&&Time.now().value().toLong()<deferred["until"]){return false;}
        var rejected=cache.store.read("sf.incoming.feed.rejected");
        if(rejected instanceof Dictionary&&rejected["token"] instanceof String&&rejected["token"].equals(token)&&(rejected["until"] instanceof Number||rejected["until"] instanceof Long)){return Time.now().value().toLong()>=rejected["until"];}
        var done = cache.store.read("sf.incoming.feed.processed");
        return cache.packet == null || !(done instanceof String && token.equals(done));
    }

    // Prepare exactly one provisional input in lifecycle-aware timer slices.
    // The durable pointer is still published only by acceptPrepared after full
    // validation. A changed provisional marker invalidates the in-flight job.
    function beginAdmission(app,cache,incoming,now){
        app.view.cancelSfrBuild();
        app.view.stopFitness();app.view.stopAnimation();app.view.releaseVisualForSettings();app.view.assetCache=null;app.view.visualKey=null;app.view.presentation.suspend();app.view.packet=null;
        app.view.admissionPending=true;WatchUi.requestUpdate();
        var seal=cache.commit instanceof Dictionary?cache.commit["seal"]:null;
        // A provisional wire digest equal to an already accepted packet can
        // reuse that packet only after the incoming chunks authenticate.
        var pending=cache.store.read("sf.incoming.feed");var duplicate=cache.packet instanceof NativeFeed&&pending instanceof Dictionary&&pending["sha256"] instanceof String&&pending["sha256"].equals(cache.packet.wireHash)?cache.packet:null;
        var key=cache.commitKey;cache.releaseForTransfer(now);
        app.admissionJob={"cache"=>cache,"incoming"=>incoming,"setting"=>configuredFeedUrl(),"seal"=>seal,"key"=>key,"now"=>now,"row"=>null,"reader"=>null,"packet"=>null,"promotion"=>null,"duplicate"=>duplicate};
        app.queueAdmission();
    }
    function failAdmission(app){
        var job=app.admissionJob;if(job==null){return;}var cache=job["cache"];
        if(job["packet"]!=null){job["packet"].disposePreparation();}app.admissionJob=null;app.view.clearForRestore();cache.packet=null;cache.commit=null;cache.commitKey=job["key"];
        app.restoreSeal=job["seal"];app.restorePending=job["seal"]!=null;app.view.admissionPending=app.restorePending;if(app.restorePending){app.queueRestore();}else{display(app,cache);app.view.resumeAfterAdmission();}
    }
    function admissionStep(app){
        var job=app.admissionJob;if(job==null){return;}
        var incoming=job["incoming"];var cache=job["cache"];
        if(!job["setting"].equals(configuredFeedUrl())){failAdmission(app);return;}
        try{
            if(job["row"]==null){
                if(job["reader"]==null){job["reader"]=new NativeIncomingReadJob(incoming);app.queueAdmission();return;}
                var reader=job["reader"];if(!reader.step()){app.queueAdmission();return;}var row=reader.result;job["reader"]=null;
                if(row==null){var pending=cache.store.read("sf.incoming.feed");if(incoming.validFeedMarker(pending)){try{incoming.defer(pending,Time.now().value().toLong());}catch(ignore){}}failAdmission(app);return;}
                var latest=cache.store.read("sf.incoming.feed");if(!(latest instanceof Dictionary)||!(latest["sha256"] instanceof String)||!incoming.token(latest).equals(incoming.token(row[0]))){failAdmission(app);return;}
                if(job["duplicate"]!=null&&row[0]["sha256"].equals(job["duplicate"].wireHash)){
                    cache.packet=job["duplicate"];cache.packet.advance(job["now"]);cache.requestWake=null;try{incoming.processed("feed",row[0]);incoming.clearRejected(row[0]);incoming.clearDeferred();}catch(ignore){}
                    app.admissionJob=null;app.view.admissionPending=false;display(app,cache);savePlan(cache,cache.packet.document["refreshPolicy"],app.view);app.view.resumeAfterAdmission();return;
                }
                job["duplicate"]=null;job["row"]=row;job["packet"]=new NativePreparedBridgeFeed(row[1],job["now"],cache.store);app.queueAdmission();return;
            }
            var marker=cache.store.read("sf.incoming.feed");var row=job["row"];
            if(!(marker instanceof Dictionary)||!(marker["sha256"] instanceof String)||!incoming.token(marker).equals(incoming.token(row[0]))){failAdmission(app);return;}
            var packet=job["packet"];
            if(packet.preparePhase<8){packet.prepareStep();app.queueAdmission();return;}
            if(job["promotion"]==null){job["promotion"]=new NativeFeedPromotion(cache,incoming.takeRaw(row),packet,job["now"],app.view);app.queueAdmission();return;}
            var promotion=job["promotion"];if(!promotion.step()){app.queueAdmission();return;}var accepted=promotion.accepted;
            if(accepted){try{incoming.processed("feed",row[0]);incoming.clearRejected(row[0]);incoming.clearDeferred();}catch(ignore){}}else if(!cache.failure.equals("admission-retry")){incoming.rejected(row[0],Time.now().value().toLong());incoming.processed("feed",row[0]);}
            if(!accepted){failAdmission(app);return;}
            app.admissionJob=null;app.view.admissionPending=false;reload(app);app.view.resumeAfterAdmission();
        }catch(e){
            // A malformed complete feed is consumed just as in synchronous
            // admission; a missing catalog remains retryable.
            try{if(job["row"]!=null){if(e.getErrorMessage().equals("Bridge catalog incomplete")){incoming.defer(job["row"][0],Time.now().value().toLong());}else{incoming.rejected(job["row"][0],Time.now().value().toLong());incoming.processed("feed",job["row"][0]);}}}catch(ignore){}
            failAdmission(app);
        }
    }

    function reload(app) {
        var url = new NativeTransfer(configuredFeedUrl(),null).base;
        var selected = app.feed;
        var now = Time.now().value().toLong();
        var rebuild = false;
        try {
            if (!(selected instanceof NativeCache) || !selected.base.equals(url)) {
                // Host changes own a separate identity namespace.
                if (app.view != null && app.view.renderer != null) {
                    rebuild=true;app.view.releaseRenderer();
                }
                if (app.view != null) { app.view.setPacket(null); }
                selected=new NativeCache(url,null);app.feed=selected;
                if(app.view!=null){app.view.resetRollover();app.view.admissionPending=true;}app.restoreSeal=null;if(app.restoreJob!=null){app.restoreJob.dispose();}app.restoreJob=null;app.restorePending=true;app.queueRestore();return;
            }
            if (!selected.base.equals("")) {
                var incoming=new NativeIncoming(selected.store,selected.base);
                var admission=hasNewIncoming(selected,incoming);
                if(admission&&app.view!=null){
                    beginAdmission(app,selected,incoming,now);return;
                }

            }
            display(app,selected);
            if(selected.packet!=null&&app.view!=null){savePlan(selected,selected.packet.document["refreshPolicy"],app.view);}
        } finally {
            if (rebuild && !app.view.admissionPending) { app.view.prepareRenderer(); }
        }
        if (app.view != null && System.getDisplayMode() == System.DISPLAY_MODE_HIGH_POWER) { app.view.prepareVisual(); }

        var transfer=new NativeTransfer(selected.base,selected.store);transfer.load();armFeed(transfer,now);
    }
}
