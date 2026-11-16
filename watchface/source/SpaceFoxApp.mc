import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.Background;
import Toybox.System;
import Toybox.Time;
import Toybox.Timer;

(:background)
class SpaceFoxApp extends Application.AppBase {
    var view as SpaceFoxView or Null;
    var feed as NativeCache or Null=null;
    var restoreSeal as String or Null=null;var restorePending as Boolean=false;var restoreTimer as Timer.Timer or Null=null;
    var incomingJob as NativeAdmissionJob or Null=null;var incomingTimer as Timer.Timer or Null=null;
    var restoreJob as NativeRestoreJob or Null=null;
    function initialize(){AppBase.initialize();view=null;}
    (:typecheck(disableBackgroundCheck))
    function initialSettings() as SceneSettings {return new SceneSettings(null).load();}
    (:typecheck(disableBackgroundCheck))
    function getInitialView() as [Views] or [Views, InputDelegates] {
        return NativeForegroundApp.initial(self);
    }

    (:typecheck(disableBackgroundCheck))
    function getSettingsView() as [Views] or [Views, InputDelegates] or Null {if(view!=null){view.releaseForSettings();}return SettingsMenu.root(self);}

    function getServiceDelegate() as [System.ServiceDelegate] {return [new FeedService()];}
    (:typecheck(disableBackgroundCheck))
    function onBackgroundData(data as Application.PersistableType) as Void {if(view==null||System.getDisplayMode()==System.DISPLAY_MODE_OFF){return;}if(view.canAcceptBackground()){try{reloadFeed();}catch(e){}}WatchUi.requestUpdate();}
    (:typecheck(disableBackgroundCheck))
    function reloadFeed() as Void {
        // Keep failures inside the callback boundary; propagating through
        // Method.invoke can be reported as an unhandled simulator exception.
        try{if(restorePending){queueRestore();return;}performReload();}catch(e){}
    }
    (:typecheck(disableBackgroundCheck))
    function performReload() as Void {NativeForegroundApp.reload(self);}

    (:typecheck(disableBackgroundCheck))
    function startIncoming(cache as NativeCache,now as Long) as Void {
        if(incomingJob!=null||view==null){return;}view.beginAdmission();incomingJob=new NativeAdmissionJob(cache,view,now);queueIncoming();
    }
    (:typecheck(disableBackgroundCheck))
    function queueIncoming() as Void {if(incomingTimer==null&&incomingJob!=null&&view!=null&&view.canForegroundWork()&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){incomingTimer=new Timer.Timer();incomingTimer.start(method(:incomingStep),50,false);}}
    (:typecheck(disableBackgroundCheck))
    function incomingStep() as Void {
        incomingTimer=null;var job=incomingJob;if(job==null){return;}
        if(view==null||!view.canForegroundWork()||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER||feed!=job.cache){cancelIncoming();return;}
        var incomingCache=job.cache as NativeCache;var incomingBase=incomingCache.base as String;var incomingUrl=incomingCache.normalize(configuredFeedUrl()) as String;if(!incomingBase.equals(incomingUrl)){switchSourceAfterWork();return;}
        if(job.finished){incomingJob=null;try{NativeForegroundApp.completeIncoming(self,job);}catch(e){var current=view;if(current!=null){current.endAdmission();}}return;}
        try{job.step();}catch(e){job.abort();}queueIncoming();
    }
    (:typecheck(disableBackgroundCheck))
    function cancelIncoming() as Void {
        if(incomingTimer!=null){incomingTimer.stop();incomingTimer=null;}var job=incomingJob;if(job==null){return;}incomingJob=null;job.abort();
        if(!job.accepted&&job.restoreSeal instanceof String){restoreSeal=job.restoreSeal as String;restorePending=true;}
        if(view!=null){view.admissionPending=false;}
    }
    (:typecheck(disableBackgroundCheck))
    function cancelWork() as Void {cancelIncoming();cancelRestore();}
    (:typecheck(disableBackgroundCheck))
    function switchSourceAfterWork() as Void {cancelWork();restorePending=false;restoreSeal=null;feed=null;var current=view;if(current!=null){current.setPacket(null);current.resetRollover();current.endAdmission();}}
    (:typecheck(disableBackgroundCheck))
    function cancelRestore() as Void {if(restoreTimer!=null){restoreTimer.stop();restoreTimer=null;}if(restoreJob!=null){restoreJob.abort();restoreJob=null;}if(view!=null){view.admissionPending=false;}}
    (:typecheck(disableBackgroundCheck))
    function startRestore(cache as NativeCache,now as Long) as Void {if(view==null){return;}restorePending=true;view.beginAdmission();restoreJob=new NativeRestoreJob(cache,now,restoreSeal);queueRestore();}

    (:typecheck(disableBackgroundCheck))
    function queueRestore() as Void {if(restoreTimer==null&&view!=null&&view.canForegroundWork()&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){restoreTimer=new Timer.Timer();restoreTimer.start(method(:restoreFeed),50,false);}}
    (:typecheck(disableBackgroundCheck))
    function restoreFeed() as Void {
        restoreTimer=null;var current=view;if(!restorePending||current==null||!current.canForegroundWork()||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){cancelRestore();return;}
        var selected=feed;if(!(selected instanceof NativeCache)){restorePending=false;current.endAdmission();return;}
        var selectedBase=selected.base as String;var selectedUrl=selected.normalize(configuredFeedUrl()) as String;if(!selectedBase.equals(selectedUrl)){switchSourceAfterWork();return;}
        if(restoreJob==null){current.beginAdmission();restoreJob=new NativeRestoreJob(selected,Time.now().value().toLong(),restoreSeal);}
        var job=restoreJob;
        if(job.finished){restoreJob=null;try{NativeForegroundApp.completeRestore(self,job);}catch(e){current.admissionPending=false;WatchUi.requestUpdate();}return;}
        try{job.step();}catch(e){job.abort();}queueRestore();
    }
    (:typecheck(disableBackgroundCheck))
    function onDisplayModeChanged() as Void {
        var current=view;var mode=System.getDisplayMode();
        if(current==null){return;}
        current.syncDisplayMode(mode);
        if(mode==System.DISPLAY_MODE_HIGH_POWER && current.canForegroundWork()){if(restorePending){queueRestore();}else{current.prepareVisual();}}
        else if((mode==System.DISPLAY_MODE_LOW_POWER||mode==System.DISPLAY_MODE_OFF)&&restoreTimer!=null){restoreTimer.stop();restoreTimer=null;}
    }
    (:typecheck(disableBackgroundCheck))
    function onSettingsChanged() as Void {try{var now=Time.now().value().toLong();var reminderTransfer=new NativeTransfer(configuredFeedUrl(),null);reminderTransfer.load();LaunchReminder.syncEnable(reminderTransfer.store,now);armFeed(reminderTransfer,now);}catch(e){}var current=view;if(current!=null){try{current.setSettings(new SceneSettings(null).load());}catch(e){current.releaseRenderer();}if(current.canForegroundWork()){reloadFeed();}WatchUi.requestUpdate();}}
}
