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
    function initialize(){AppBase.initialize();view=null;}
    (:typecheck(disableBackgroundCheck))
    function getInitialView() as [Views] or [Views, InputDelegates] {
        return NativeForegroundApp.initial(self);
    }

    function getServiceDelegate() as [System.ServiceDelegate] {return [new FeedService()];}
    (:typecheck(disableBackgroundCheck)) function refreshSyncStatus() as Void {if(view!=null&&feed!=null){NativeForegroundApp.status(self,feed);}}
    (:typecheck(disableBackgroundCheck))
    function onBackgroundData(data as Application.PersistableType) as Void {if(view==null){NativeMetrics.sample("foreground-deferred-before-view");return;}try{reloadFeed();}catch(e){NativeMetrics.failure(e.getErrorMessage());if(NativeMetrics.enabled){e.printStackTrace();}}WatchUi.requestUpdate();}
    (:typecheck(disableBackgroundCheck))
    function reloadFeed() as Void {
        if(restorePending){queueRestore();return;}NativeForegroundApp.reload(self);
    }

    (:typecheck(disableBackgroundCheck))
    function queueRestore() as Void {if(restoreTimer==null&&view!=null&&view.canForegroundWork()&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){restoreTimer=new Timer.Timer();restoreTimer.start(method(:restoreFeed),50,false);}}
    (:typecheck(disableBackgroundCheck))
    function restoreFeed() as Void {restoreTimer=null;if(!restorePending||view==null||!view.canForegroundWork()||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}restorePending=false;NativeForegroundApp.restore(self);}
    (:typecheck(disableBackgroundCheck))
    function onDisplayModeChanged() as Void {var current=view;if(current!=null){current.syncDisplayMode(System.getDisplayMode());if(System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){if(restorePending){queueRestore();}else{current.prepareVisual();}}else if(restoreTimer!=null){restoreTimer.stop();restoreTimer=null;}}}
    (:typecheck(disableBackgroundCheck))
    function onSettingsChanged() as Void {if(view!=null){view.setSettings(new SceneSettings(null).load());reloadFeed();WatchUi.requestUpdate();}}
}
