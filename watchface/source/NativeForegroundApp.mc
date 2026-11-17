import Toybox.Time;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Background;
(:extendedCode, :typecheck(false))
module NativeForegroundApp {
    function traceWake(stage){try{var now=Time.now().value();var registered=Background.getTemporalEventRegisteredTime();var last=Background.getLastTemporalEventTime();System.println("SF_WAKE "+stage+" build="+NativeVersion.BUILD+" id="+NativeVersion.ID+" now="+now+" registered="+(registered==null?"none":registered.value())+" last="+(last==null?"none":last.value()));}catch(ignore){System.println("SF_WAKE status_unavailable");}}
    function initial(app) as [WatchUi.WatchFace] {
        app.view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
        try{app.view.setSettings(app.initialSettings());}catch(e){}app.view.bootstrapPending=true;app.view.pendingLoader=app.method(:reloadFeed);app.view.cancelAdmission=null;app.view.syncDisplayMode(System.getDisplayMode());return [app.view as WatchUi.WatchFace];
    }
    function display(app,cache){
        if(app.view==null){return;}var now=Time.now().value().toLong();var rebound=cache.packet==null||app.view.packet!=cache.packet||cache.packet.document.hasKey("dictionaries")||app.view.context!=cache.packet.presentation;
        if(rebound){app.view.setPacket(cache.packet);}
        if(cache.packet!=null){
            // A saved queue is merged when the packet is rebound. Reopening it
            // on every wake retains a second full queue beside decoded artwork.
            if(rebound){try{var owner=cache.packet.document["publisher"]["instance"];var saved=new NativeUpcomingCache(cache.store,cache.base,owner).load();app.view.mergeSaved(saved,now,cache.packet.terminalUpdates);}catch(e){}}
            if(app.view.context==cache.packet.presentation){app.view.setAssetCache(new NativeRenderSource(cache.store,cache.base,cache.packet.bridge));}
        }LaunchReminderForeground.publishQueue(cache,now,app.view.queueSnapshots());
        // Background uses this compact source-bound result rather than treating
        // an unvalidated commit marker as an accepted schedule.
        try{var accepted=cache.packet!=null;var prior=cache.store.read("sf.transfer.ready");if(!(prior instanceof Dictionary)||!(prior["base"] instanceof String)||!prior["base"].equals(cache.base)||prior["accepted"]!=accepted){cache.store.write("sf.transfer.ready",{"base"=>cache.base,"accepted"=>accepted});}}catch(e){}
    }
    function savePlan(cache,view){
        var targets=[];var scenes=view.queueSnapshots();for(var i=0;i<scenes.size();i+=1){var value=scenes[i].orderingUtc;if(value!=null&&targets.indexOf(value)<0){targets.add(value);}}
        var marker=new NativeTrustedStore(cache.store,cache.base).marker();var sequence=marker==null?null:marker["sequence"];var old=cache.store.read("sf.transfer.plan:"+cache.base);if(old instanceof Dictionary&&old["sequence"]==sequence&&old["base"] instanceof String&&old["base"].equals(cache.base)&&nativeSame(old["targets"],targets)){return;}cache.store.write("sf.transfer.plan:"+cache.base,{"base"=>cache.base,"sequence"=>sequence,"targets"=>targets});
    }
    // The background service publishes one complete projected snapshot. Read
    // the pointer first; a later wake with the same pointer need not allocate a
    // second scene or disturb a running optional artwork job.
    function reload(app) {
        var url=new NativeTransfer(configuredFeedUrl(),null).base;var now=Time.now().value().toLong();var selected=app.feed;
        if(!(selected instanceof NativeCache)||!selected.base.equals(url)){
            if(app.view!=null){app.view.releaseRenderer();app.view.setPacket(null);app.view.resetRollover();}
            selected=new NativeCache(url,null);app.feed=selected;app.trustedToken=null;app.failedToken=null;
        }
        var marker=new NativeTrustedStore(selected.store,url).marker();var sequence=marker instanceof Dictionary&&marker["base"] instanceof String&&marker["base"].equals(url)?marker["sequence"]:null;
        if(sequence!=null&&sequence!=app.trustedToken&&sequence!=app.failedToken&&app.view!=null){
            if(selected.packet!=null){try{new NativeUpcomingCache(selected.store,url,selected.packet.document["publisher"]["instance"]).save(app.view.queueSnapshots());}catch(e){System.println("SF_FG queue_save_error");return;}}
            app.view.beginAdmission();selected.packet=null;
            try{
                var value=new NativeTrustedStore(selected.store,url).load();
                if(value!=null){selected.packet=new NativeTrustedPacket(value);value=null;app.trustedToken=sequence;app.failedToken=null;app.view.admissionPending=false;display(app,selected);savePlan(selected,app.view);}else{app.failedToken=sequence;}
            }catch(e){app.failedToken=sequence;System.println("SF_FG snapshot_error");}
            app.view.admissionPending=false;app.view.resumeAfterAdmission();
        }else if(selected.packet!=null){display(app,selected);savePlan(selected,app.view);}
        if(app.view!=null&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){app.view.prepareVisual();}
        var transfer=new NativeTransfer(selected.base,selected.store);transfer.load();armFeed(transfer,now);
    }
}
