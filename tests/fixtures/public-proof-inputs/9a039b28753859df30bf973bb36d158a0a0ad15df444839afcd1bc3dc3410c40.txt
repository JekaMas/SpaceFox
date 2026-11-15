import Toybox.Time;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
(:extendedCode, :typecheck(false))
module NativeForegroundApp {
    function initial(app) as [WatchUi.WatchFace] {
        app.view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
        app.view.setSettings(new SceneSettings(null).load());var selected=new NativeCache(configuredFeedUrl(),null);app.feed=selected;var now=Time.now().value().toLong();selected.load(now);display(app,selected);app.view.pendingLoader=app.method(:reloadFeed);app.view.syncDisplayMode(System.getDisplayMode());NativeMetrics.sample("foreground-initial-complete");return [app.view as WatchUi.WatchFace];
    }
    function display(app,cache){
        if(app.view==null){return;}if(cache.packet==null||cache.packet.document.hasKey("dictionaries")||app.view.context!=cache.packet.presentation){app.view.setPacket(cache.packet);}if(cache.packet!=null){app.view.setAssetCache(new NativeRenderSource(cache.store,cache.base));}
    }
    function savePlan(cache,p){
        var next=[p["normal_interval_seconds"],p["near_interval_seconds"],p["fast_interval_seconds"]];var old=cache.store.read("sf.transfer.plan");if(old instanceof Dictionary&&old["base"] instanceof String&&old["base"].equals(cache.base)&&old["target"]==cache.packet.target()&&old["policy"] instanceof Array&&old["policy"].size()==3&&old["policy"][0]==next[0]&&old["policy"][1]==next[1]&&old["policy"][2]==next[2]){return;}cache.store.write("sf.transfer.plan",{"base"=>cache.base,"target"=>cache.packet.target(),"policy"=>next});
    }
    function restore(app){
        var selected=app.feed;var url=new NativeTransfer(configuredFeedUrl(),null).base;
        if(!(selected instanceof NativeCache)||!selected.base.equals(url)){app.restoreSeal=null;reload(app);return;}
        var now=Time.now().value().toLong();var before=selected.store.writes;
        selected.restoreAccepted(now,app.restoreSeal);app.restoreSeal=null;display(app,selected);app.view.prepareRenderer();
        if(System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){app.view.prepareVisual();}
        NativeMetrics.writes("foreground-restore-total",selected.store.writes-before);NativeMetrics.sample("foreground-restore-complete");
        var transfer=new NativeTransfer(selected.base,selected.store);transfer.load();armFeed(transfer,now);
    }
    function reload(app){
        if(app.view!=null&&(app.view.sfrBuild!=null||app.view.sfrRequested)){app.view.cancelSfrBuild();}
        var url=new NativeTransfer(configuredFeedUrl(),null).base;var selected=app.feed;var now=Time.now().value().toLong();var before=0;var rebuild=false;var deferred=false;
        try{
        if(!(selected instanceof NativeCache)||!selected.base.equals(url)){
            // Reopening another namespace reconstructs a complete raw feed too.
            // A changed host owns a different identity namespace. Clear the old
            // scene before reconstruction so its packet/bitmap cannot compete
            // with the new full raw feed or appear under the new host.
            if(app.view!=null&&app.view.renderer!=null){rebuild=true;app.view.releaseRenderer();NativeMetrics.sample("foreground-renderer-released");}
            if(app.view!=null){app.view.setPacket(null);}
            selected=new NativeCache(url,null);app.feed=selected;before=selected.store.writes;selected.load(now);
        }else{before=selected.store.writes;}
        if(!selected.base.equals("")){
            var incoming=new NativeIncoming(selected.store,selected.base);var pending=selected.store.read("sf.incoming.feed");var done=selected.store.read("sf.incoming.feed.processed");
            // Admission can allocate the full 8KiB raw document and parser AST.
            // Keep the working scene/packet/optional bitmap, but release the
            // reconstructible renderer resources for this synchronous work.
            // Rebind them here, outside redraw, even when admission rejects.
            if(app.view!=null&&app.view.renderer!=null&&pending instanceof Dictionary&&(selected.packet==null||!(pending["sha256"] instanceof String&&done instanceof String&&incoming.token(pending).equals(done)))){rebuild=true;app.view.releaseRenderer();app.view.packet=null;NativeMetrics.sample("foreground-renderer-released");}
            pending=null;done=null;incoming.admitFeedForView(selected,now,app.view);if(incoming.needsRestore){deferred=true;app.restoreSeal=incoming.restoreSeal;app.restorePending=true;app.queueRestore();NativeMetrics.sample("foreground-restore-queued");return;}
            NativeMetrics.sample("foreground-incoming-complete");if(selected.packet!=null){var policy=selected.packet.document["refreshPolicy"];savePlan(selected,policy);NativeMetrics.sample("foreground-plan-complete");}
        }
        NativeMetrics.sample("foreground-before-view");display(app,selected);
        }finally{if(rebuild&&!deferred){app.view.prepareRenderer();NativeMetrics.sample("foreground-renderer-restored");}}
        if(app.view!=null&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){app.view.prepareVisual();}
        NativeMetrics.writes("foreground-reload-total",selected.store.writes-before);var transfer=new NativeTransfer(selected.base,selected.store);transfer.load();armFeed(transfer,now);
    }
}
