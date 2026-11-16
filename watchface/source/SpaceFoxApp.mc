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
    var deferredRestore as Boolean=false;var deferredSeal as String or Null=null;var batchingForeground as Boolean=false;var restoreJob as NativeRestoreJob or Null=null;var admissionJob as Dictionary or Null=null;var admissionTimer as Timer.Timer or Null=null;
    function initialize(){AppBase.initialize();view=null;}
    (:typecheck(disableBackgroundCheck))
    function getInitialView() as [Views] or [Views, InputDelegates] {
        return NativeForegroundApp.initial(self);
    }

    (:typecheck(disableBackgroundCheck))
    function getSettingsView() as [Views] or [Views, InputDelegates] or Null {if(view!=null){view.releaseForSettings();}return SettingsMenu.root(self);}

    function getServiceDelegate() as [System.ServiceDelegate] {return [new FeedService()];}
    (:typecheck(disableBackgroundCheck))
    function onBackgroundData(data as Application.PersistableType) as Void {System.println("SF_FG background_delivery");try{if(feed!=null){new NativeIncoming(feed.store,feed.base).clearDeferred();}}catch(e){}if(view==null||System.getDisplayMode()==System.DISPLAY_MODE_OFF){return;}if(view.canAcceptBackground()){try{reloadFeed();}catch(e){}}WatchUi.requestUpdate();}
    (:typecheck(disableBackgroundCheck))
    function reloadFeed() as Void {
        if(deferredRestore){deferredRestore=false;restoreSeal=deferredSeal;deferredSeal=null;restorePending=true;}
        if(restorePending){queueRestore();return;}if(admissionJob!=null){queueAdmission();return;}NativeForegroundApp.reload(self);
    }

    (:typecheck(false))
    function abandonForegroundWork() as Void {
        try{if(admissionTimer!=null){admissionTimer.stop();}}catch(e){}try{if(restoreTimer!=null){restoreTimer.stop();}}catch(e){}
        var job=admissionJob;var retry=restorePending||restoreJob!=null;var seal=restoreSeal;
        if(job!=null){if(job["packet"]!=null){job["packet"].disposePreparation();}if(job["seal"] instanceof String){retry=true;seal=job["seal"];}}
        if(restoreJob!=null){restoreJob.dispose();}
        if(feed!=null&&(job==null||job["cache"]==feed)){feed.packet=null;feed.commit=null;if(job!=null){feed.commitKey=job["key"];}}
        deferredRestore=retry;deferredSeal=retry?seal:null;
        admissionTimer=null;restoreTimer=null;admissionJob=null;restoreJob=null;restorePending=false;restoreSeal=null;
        // A failure is terminal for this callback. The previous view remains;
        // a later lifecycle, settings or background event explicitly retries.
        if(view!=null){view.admissionPending=false;WatchUi.requestUpdate();}
    }
    (:typecheck(false))
    function queueAdmission() as Void {try{if(!batchingForeground&&admissionJob!=null&&admissionTimer==null&&view!=null&&view.canForegroundWork()&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){admissionTimer=new Timer.Timer();admissionTimer.start(method(:admissionStep),50,false);}}catch(e){abandonForegroundWork();}}
    (:typecheck(false))
    function admissionStep() as Void {admissionTimer=null;if(admissionJob==null||view==null||!view.canForegroundWork()||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}var started=System.getTimer();var steps=0;batchingForeground=true;try{while(admissionJob!=null&&view.canForegroundWork()&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER&&steps<4&&(steps==0||System.getTimer()-started<12)){NativeForegroundApp.admissionStep(self);steps+=1;if(admissionJob!=null&&admissionJob["packet"]!=null&&admissionJob["packet"].mustYield){admissionJob["packet"].mustYield=false;break;}if(admissionJob!=null&&admissionJob["promotion"]!=null&&admissionJob["promotion"].mustYield){admissionJob["promotion"].mustYield=false;break;}}batchingForeground=false;queueRestore();queueAdmission();}catch(e){batchingForeground=false;abandonForegroundWork();}}
    (:typecheck(disableBackgroundCheck))
    function queueRestore() as Void {try{if(!batchingForeground&&restorePending&&restoreTimer==null&&view!=null&&view.canForegroundWork()&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){restoreTimer=new Timer.Timer();restoreTimer.start(method(:restoreFeed),50,false);}}catch(e){abandonForegroundWork();}}
    (:typecheck(false))
    function restoreFeed() as Void {restoreTimer=null;if(!restorePending||view==null||!view.canForegroundWork()||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}var started=System.getTimer();var steps=0;batchingForeground=true;try{while(restorePending&&view.canForegroundWork()&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER&&steps<4&&(steps==0||System.getTimer()-started<12)){NativeForegroundApp.restoreStep(self);steps+=1;if(restoreJob!=null&&restoreJob.packet!=null&&restoreJob.packet.mustYield){restoreJob.packet.mustYield=false;break;}if(restoreJob!=null&&restoreJob.mustYield){restoreJob.mustYield=false;break;}}batchingForeground=false;queueRestore();queueAdmission();}catch(e){batchingForeground=false;abandonForegroundWork();}}
    (:typecheck(disableBackgroundCheck))
    function onDisplayModeChanged() as Void {
        var current=view;var mode=System.getDisplayMode();
        if(current==null){return;}
        current.syncDisplayMode(mode);
        if(mode==System.DISPLAY_MODE_HIGH_POWER && current.canForegroundWork()){if(restorePending){queueRestore();}else if(admissionJob!=null){queueAdmission();}else{current.prepareVisual();}}
        else if(mode==System.DISPLAY_MODE_LOW_POWER||mode==System.DISPLAY_MODE_OFF){if(restoreTimer!=null){restoreTimer.stop();restoreTimer=null;}if(admissionTimer!=null){admissionTimer.stop();admissionTimer=null;}}
    }
    (:typecheck(disableBackgroundCheck))
    function onSettingsChanged() as Void {try{var now=Time.now().value().toLong();var reminderTransfer=new NativeTransfer(configuredFeedUrl(),null);reminderTransfer.load();LaunchReminder.syncEnable(reminderTransfer.store,now);armFeed(reminderTransfer,now);}catch(e){}var current=view;if(current!=null){current.setSettings(new SceneSettings(null).load());if(current.canForegroundWork()){reloadFeed();}WatchUi.requestUpdate();}}
}
