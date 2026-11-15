import Toybox.Time;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Background;
(:extendedCode, :typecheck(false))
module NativeForegroundApp {
    function initial(app) as [WatchUi.WatchFace] {
        app.view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
        app.view.setSettings(new SceneSettings(null).load());var selected=new NativeCache(configuredFeedUrl(),null);app.feed=selected;var now=Time.now().value().toLong();selected.load(now);display(app,selected);app.view.pendingLoader=app.method(:reloadFeed);app.view.statusLoader=app.method(:refreshSyncStatus);app.view.syncDisplayMode(System.getDisplayMode());NativeMetrics.sample("foreground-initial-complete");return [app.view as WatchUi.WatchFace];
    }
    function display(app,cache){
        if(app.view==null){return;}if(cache.packet==null||cache.packet.document.hasKey("dictionaries")||app.view.context!=cache.packet.presentation){app.view.setPacket(cache.packet);}if(cache.packet!=null){app.view.setAssetCache(new NativeRenderSource(cache.store,cache.base,cache.packet.bridge));}
        // Background uses this compact source-bound result rather than treating
        // an unvalidated commit marker as an accepted schedule.
        try{var accepted=cache.packet!=null;var prior=cache.store.read("sf.transfer.ready");if(!(prior instanceof Dictionary)||!(prior["base"] instanceof String)||!prior["base"].equals(cache.base)||prior["accepted"]!=accepted){cache.store.write("sf.transfer.ready",{"base"=>cache.base,"accepted"=>accepted});}}catch(e){}
        status(app,cache);
    }
    function errorDetail(stage,value){var version=value["build"] instanceof String?value["build"]:"?";return (stage.equals("feedFailed")?"Feed: ":"Assets: ")+version+" "+value["code"]; }
    function incomplete(stage, now, utc, pending, registered, last) {
        if (now-utc<=60) { return false; }
        // A pending asset batch with an unconsumed OS registration remains a
        // normal wait, including a delayed OS dispatch after its deadline.
        if (stage.equals("assets") && pending && registered!=null && (last==null || registered>last)) { return false; }
        return true;
    }
    function status(app, cache) {
        var result = "waiting";
        var detail = "";
        if (cache.base.equals("")) {
            result = "url";
        } else {
            try {
                var value = cache.store.read("sf.sync.status");
                if (value instanceof Dictionary && value["base"] instanceof String &&
                    value["base"].equals(cache.base) && value["stage"] instanceof String) {
                    var stage = value["stage"];
                    if (["failed","feedFailed","assetFailed","received","requesting","assets"].indexOf(stage) >= 0) {
                        result = stage;
                        if ((stage.equals("feedFailed") || stage.equals("assetFailed")) && value["code"] instanceof Number) {
                            detail = cache.packet == null ? ""+value["code"] : errorDetail(stage,value);
                        }
                        var pending=false;var registeredAt=null;var lastAt=null;
                        if(stage.equals("assets")){
                            pending=batchPending(cache);
                            var registered=Background.getTemporalEventRegisteredTime();var last=Background.getLastTemporalEventTime();
                            registeredAt=registered==null?null:registered.value().toLong();lastAt=last==null?null:last.value().toLong();
                        }
                        if ((stage.equals("requesting") || stage.equals("assets")) &&
                            (value["utc"] instanceof Number || value["utc"] instanceof Long) &&
                            incomplete(stage,Time.now().value().toLong(),value["utc"],pending,registeredAt,lastAt)) {
                            result = "incomplete";
                            detail = stage.equals("assets") ? "Assets" : "Feed";
                        }
                    }
                } else if (Background.getTemporalEventRegisteredTime() == null) {
                    result = "unscheduled";
                }
                if (result.equals("received") || result.equals("assets")) {
                    var admission = cache.store.read("sf.sync.admission");
                    if (admission instanceof Dictionary && admission["base"] instanceof String &&
                        admission["base"].equals(cache.base) && admission["reason"] instanceof String) {
                        detail = "Admission: "+admission["reason"];
                    }
                }
            } catch(e) {}
        }
        // Identify this foreground executable even before a background callback.
        if (cache.packet == null) {
            detail = NativeVersion.BUILD+" "+NativeVersion.ID+(detail.equals("") ? "" : " "+detail);
        }
        app.view.setSyncStatus(result,detail);
    }
    function savePlan(cache,p){
        var next=[p["normal_interval_seconds"],p["near_interval_seconds"],p["fast_interval_seconds"]];var old=cache.store.read("sf.transfer.plan");if(old instanceof Dictionary&&old["base"] instanceof String&&old["base"].equals(cache.base)&&old["target"]==cache.packet.refreshTarget()&&old["policy"] instanceof Array&&old["policy"].size()==3&&old["policy"][0]==next[0]&&old["policy"][1]==next[1]&&old["policy"][2]==next[2]){return;}cache.store.write("sf.transfer.plan",{"base"=>cache.base,"target"=>cache.packet.refreshTarget(),"policy"=>next});
    }
    function restore(app){
        var selected=app.feed;var url=new NativeTransfer(configuredFeedUrl(),null).base;
        if(!(selected instanceof NativeCache)||!selected.base.equals(url)){app.restoreSeal=null;reload(app);return;}
        var now=Time.now().value().toLong();var before=selected.store.writes;
        // Detach only for this synchronous parse and rebind before returning to
        // the UI. Preserve the accepted scene if strict restore cannot complete.
        app.view.releaseRenderer();
        try{selected.restoreAccepted(now,app.restoreSeal);if(selected.packet!=null){app.restoreSeal=null;display(app,selected);}else{app.restorePending=true;}}
        finally{app.view.prepareRenderer();}
        if(System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){app.view.prepareVisual();}
        NativeMetrics.writes("foreground-restore-total",selected.store.writes-before);NativeMetrics.sample("foreground-restore-complete");
        var transfer=new NativeTransfer(selected.base,selected.store);transfer.load();armFeed(transfer,now);status(app,selected);
    }
    // Only a new provisional feed can replace the scene. Duplicate callbacks
    // leave an in-progress visual build and its generation untouched.
    function hasNewIncoming(cache, incoming) {
        var pending = cache.store.read("sf.incoming.feed");
        if (!(pending instanceof Dictionary)) { return false; }
        var done = cache.store.read("sf.incoming.feed.processed");
        return cache.packet == null || !(pending["sha256"] instanceof String &&
            done instanceof String && incoming.token(pending).equals(done));
    }

    function reload(app) {
        var url = new NativeTransfer(configuredFeedUrl(),null).base;
        var selected = app.feed;
        var now = Time.now().value().toLong();
        var before = 0;
        var rebuild = false;
        try {
            if (!(selected instanceof NativeCache) || !selected.base.equals(url)) {
                // Host changes own a separate identity namespace.
                if (app.view != null && app.view.renderer != null) {
                    rebuild=true;app.view.releaseRenderer();NativeMetrics.sample("foreground-renderer-released");
                }
                if (app.view != null) { app.view.setPacket(null); }
                selected=new NativeCache(url,null);app.feed=selected;
                before=selected.store.writes;selected.load(now);
            } else {
                before=selected.store.writes;
            }
            if (!selected.base.equals("")) {
                var incoming=new NativeIncoming(selected.store,selected.base);
                var admission=hasNewIncoming(selected,incoming);
                if (admission && app.view != null) {
                    if (app.view.sceneLifecycle.pending()) { app.view.cancelSfrBuild(); }
                    if (app.view.renderer != null) {
                        rebuild=true;app.view.releaseRenderer();app.view.packet=null;
                        NativeMetrics.sample("foreground-renderer-released");
                    }
                }
                incoming.admitFeedForView(selected,now,app.view);
                if (incoming.needsRestore) {
                    app.restoreSeal=incoming.restoreSeal;app.restorePending=true;
                    app.queueRestore();NativeMetrics.sample("foreground-restore-queued");return;
                }
                NativeMetrics.sample("foreground-incoming-complete");
                if (selected.packet != null) {
                    savePlan(selected,selected.packet.document["refreshPolicy"]);
                    NativeMetrics.sample("foreground-plan-complete");
                }
            }
            NativeMetrics.sample("foreground-before-view");display(app,selected);
        } finally {
            if (rebuild) { app.view.prepareRenderer();NativeMetrics.sample("foreground-renderer-restored"); }
        }
        if (app.view != null && System.getDisplayMode() == System.DISPLAY_MODE_HIGH_POWER) { app.view.prepareVisual(); }
        NativeMetrics.writes("foreground-reload-total",selected.store.writes-before);
        var transfer=new NativeTransfer(selected.base,selected.store);transfer.load();armFeed(transfer,now);status(app,selected);
    }
}
