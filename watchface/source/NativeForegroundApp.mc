import Toybox.Time;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Background;
(:extendedCode, :typecheck(false))
module NativeForegroundApp {
    function traceWake(stage){try{var now=Time.now().value();var registered=Background.getTemporalEventRegisteredTime();var last=Background.getLastTemporalEventTime();System.println("SF_WAKE "+stage+" build="+NativeVersion.BUILD+" id="+NativeVersion.ID+" now="+now+" registered="+(registered==null?"none":registered.value())+" last="+(last==null?"none":last.value()));}catch(ignore){System.println("SF_WAKE status_unavailable");}}
    // Fixed metadata only: the app reads its own durable state without dumping
    // stored launch text, settings, URL, health values, tokens or hashes.
    function traceStored(cache,key){try{var row=cache.store.read(key);if(row==null){System.println("SF_STORE "+key+" absent");return;}if(!(row instanceof Dictionary)){System.println("SF_STORE "+key+" type=other");return;}var msg="SF_STORE "+key+" type=dict";var names=["v","generation","sequence","pending","until","utc"];for(var i=0;i<names.size();i+=1){var k=names[i];if(row.hasKey(k)){var value=row[k];if(value instanceof Number||value instanceof Long||value instanceof Boolean){msg+=" "+k+"="+value;}}}if(key.equals("sf.attempt")&&row["build"] instanceof String){var build=row["build"];var valid=build.length()>0&&build.length()<=16;for(var b=0;b<build.length()&&valid;b+=1){if("0123456789.".find(build.substring(b,b+1))==null){valid=false;}}if(valid){msg+=" build="+build;}}System.println(msg);}catch(ignore){System.println("SF_STORE "+key+" unavailable");}}
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
    function savePlan(cache,p,view){
        var next=[p["normal_interval_seconds"],p["near_interval_seconds"],p["fast_interval_seconds"]];var targets=[];var scenes=view.queueSnapshots();for(var i=0;i<scenes.size();i+=1){var value=scenes[i].retentionTarget;if(i==0&&cache.packet.presentation==scenes[i]){value=cache.packet.refreshTarget();}if(value!=null&&targets.indexOf(value)<0){targets.add(value);}}var target=targets.size()>0?targets[0]:null;
        var marker=new NativeTrustedStore(cache.store,cache.base).marker();var sequence=marker==null?null:marker["sequence"];var old=cache.store.read("sf.transfer.plan");if(old instanceof Dictionary&&old["sequence"]==sequence&&old["base"] instanceof String&&old["base"].equals(cache.base)&&old["target"]==target&&nativeSame(old["targets"],targets)&&old["policy"] instanceof Array&&old["policy"].size()==3&&old["policy"][0]==next[0]&&old["policy"][1]==next[1]&&old["policy"][2]==next[2]){return;}cache.store.write("sf.transfer.plan",{"base"=>cache.base,"sequence"=>sequence,"target"=>target,"targets"=>targets,"policy"=>next});
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
                if(value!=null){selected.packet=new NativeTrustedPacket(value);value=null;app.trustedToken=sequence;app.failedToken=null;app.view.admissionPending=false;display(app,selected);savePlan(selected,selected.packet.document["refreshPolicy"],app.view);}else{app.failedToken=sequence;}
            }catch(e){app.failedToken=sequence;System.println("SF_FG snapshot_error");}
            app.view.admissionPending=false;app.view.resumeAfterAdmission();
        }else if(selected.packet!=null){display(app,selected);savePlan(selected,selected.packet.document["refreshPolicy"],app.view);}
        if(app.view!=null&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){app.view.prepareVisual();}
        var transfer=new NativeTransfer(selected.base,selected.store);transfer.load();armFeed(transfer,now);
    }
}
