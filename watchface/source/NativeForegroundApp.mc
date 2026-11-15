import Toybox.Time;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Background;
(:extendedCode, :typecheck(false))
module NativeForegroundApp {
    function initial(app) as [WatchUi.WatchFace] {
        app.view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
        app.view.setSettings(new SceneSettings(null).load());var selected=new NativeCache(configuredFeedUrl(),null);app.feed=selected;var now=Time.now().value().toLong();selected.load(now);if(selected.packet!=null){savePlan(selected,selected.packet.document["refreshPolicy"]);}display(app,selected);app.view.pendingLoader=app.method(:reloadFeed);app.view.syncDisplayMode(System.getDisplayMode());return [app.view as WatchUi.WatchFace];
    }
    function display(app,cache){
        if(app.view==null){return;}LaunchReminderForeground.publish(cache,Time.now().value().toLong());if(cache.packet==null||cache.packet.document.hasKey("dictionaries")||app.view.context!=cache.packet.presentation){app.view.setPacket(cache.packet);}if(cache.packet!=null){try{var owner=cache.packet.document["publisher"]["instance"];var saved=new NativeUpcomingCache(cache.store,cache.base,owner).load();app.view.mergeSaved(saved,Time.now().value().toLong(),cache.packet.terminalUpdates);}catch(e){}app.view.setAssetCache(new NativeRenderSource(cache.store,cache.base,cache.packet.bridge));}
        // Background uses this compact source-bound result rather than treating
        // an unvalidated commit marker as an accepted schedule.
        try{var accepted=cache.packet!=null;var prior=cache.store.read("sf.transfer.ready");if(!(prior instanceof Dictionary)||!(prior["base"] instanceof String)||!prior["base"].equals(cache.base)||prior["accepted"]!=accepted){cache.store.write("sf.transfer.ready",{"base"=>cache.base,"accepted"=>accepted});}}catch(e){}
    }
    function savePlan(cache,p){
        var next=[p["normal_interval_seconds"],p["near_interval_seconds"],p["fast_interval_seconds"]];var targets=[];var target=cache.packet.refreshTarget();if(target!=null){targets.add(target);}var scenes=cache.packet.upcomingScenes;if(scenes instanceof Array){for(var i=0;i<scenes.size();i+=1){var value=scenes[i].retentionTarget;if(value!=null&&targets.indexOf(value)<0){targets.add(value);}}}
        var old=cache.store.read("sf.transfer.plan");if(old instanceof Dictionary&&old["base"] instanceof String&&old["base"].equals(cache.base)&&old["target"]==target&&nativeSame(old["targets"],targets)&&old["policy"] instanceof Array&&old["policy"].size()==3&&old["policy"][0]==next[0]&&old["policy"][1]==next[1]&&old["policy"][2]==next[2]){return;}cache.store.write("sf.transfer.plan",{"base"=>cache.base,"target"=>target,"targets"=>targets,"policy"=>next});
    }
    function restore(app){
        var selected=app.feed;var url=new NativeTransfer(configuredFeedUrl(),null).base;
        if(!(selected instanceof NativeCache)||!selected.base.equals(url)){app.restoreSeal=null;reload(app);return;}
        var now=Time.now().value().toLong();
        // Detach only for this synchronous parse and rebind before returning to
        // the UI. Preserve the accepted scene if strict restore cannot complete.
        app.view.releaseRenderer();
        try{selected.restoreAccepted(now,app.restoreSeal);if(selected.packet!=null){app.restoreSeal=null;display(app,selected);}else{app.restorePending=true;}}
        finally{app.view.prepareRenderer();}
        if(System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){app.view.prepareVisual();}

        var transfer=new NativeTransfer(selected.base,selected.store);transfer.load();armFeed(transfer,now);
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
        var rebuild = false;
        try {
            if (!(selected instanceof NativeCache) || !selected.base.equals(url)) {
                // Host changes own a separate identity namespace.
                if (app.view != null && app.view.renderer != null) {
                    rebuild=true;app.view.releaseRenderer();
                }
                if (app.view != null) { app.view.setPacket(null); }
                selected=new NativeCache(url,null);app.feed=selected;
                selected.load(now);if(app.view!=null){app.view.resetRollover();}
            }
            if (!selected.base.equals("")) {
                var incoming=new NativeIncoming(selected.store,selected.base);
                var admission=hasNewIncoming(selected,incoming);
                if (admission && app.view != null) {
                    if (app.view.sceneLifecycle.pending()) { app.view.cancelSfrBuild(); }
                    if (app.view.renderer != null) {
                        rebuild=true;app.view.releaseRenderer();app.view.packet=null;

                    }
                }
                incoming.admitFeedForView(selected,now,app.view);
                if (incoming.needsRestore) {
                    app.restoreSeal=incoming.restoreSeal;app.restorePending=true;
                    app.queueRestore();return;
                }

                if (selected.packet != null) {
                    savePlan(selected,selected.packet.document["refreshPolicy"]);

                }
            }
            display(app,selected);
        } finally {
            if (rebuild) { app.view.prepareRenderer(); }
        }
        if (app.view != null && System.getDisplayMode() == System.DISPLAY_MODE_HIGH_POWER) { app.view.prepareVisual(); }

        var transfer=new NativeTransfer(selected.base,selected.store);transfer.load();armFeed(transfer,now);
    }
}
