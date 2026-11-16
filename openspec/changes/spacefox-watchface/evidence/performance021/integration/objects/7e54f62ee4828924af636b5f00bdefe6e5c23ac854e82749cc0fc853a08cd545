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

    (:typecheck(disableBackgroundCheck))
    function getSettingsView() as [Views] or [Views, InputDelegates] or Null {if(view!=null){view.releaseForSettings();}return SettingsMenu.root(self);}

    // This is the application-owner boundary, not an ordinary hide or settings
    // transition. Break the app/view Method cycle and cancel owned callbacks.
    (:typecheck(disableBackgroundCheck))
    function onStop(state as Dictionary or Null) as Void {
        if(restoreTimer!=null){restoreTimer.stop();restoreTimer=null;}
        restorePending=false;restoreSeal=null;
        var current=view;if(current!=null){current.pendingLoader=null;current.onHide();}
        view=null;feed=null;
    }

    function getServiceDelegate() as [System.ServiceDelegate] {return [new FeedService()];}
    (:typecheck(disableBackgroundCheck))
    function onBackgroundData(data as Application.PersistableType) as Void {if(view==null||System.getDisplayMode()==System.DISPLAY_MODE_OFF){return;}if(view.canAcceptBackground()){try{reloadFeed();}catch(e){}}WatchUi.requestUpdate();}
    (:typecheck(disableBackgroundCheck))
    function reloadFeed() as Void {
        if(restorePending){queueRestore();return;}NativeForegroundApp.reload(self);
    }

    (:typecheck(disableBackgroundCheck))
    function queueRestore() as Void {if(restoreTimer==null&&view!=null&&view.canForegroundWork()&&System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){restoreTimer=new Timer.Timer();restoreTimer.start(method(:restoreFeed),50,false);}}
    (:typecheck(disableBackgroundCheck))
    function restoreFeed() as Void {restoreTimer=null;if(!restorePending||view==null||!view.canForegroundWork()||System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}restorePending=false;NativeForegroundApp.restore(self);}
    (:typecheck(disableBackgroundCheck))
    function onDisplayModeChanged() as Void {
        var current=view;var mode=System.getDisplayMode();
        if(current==null){return;}
        current.syncDisplayMode(mode);
        if(mode==System.DISPLAY_MODE_HIGH_POWER && current.canForegroundWork()){if(restorePending){queueRestore();}else{current.prepareVisual();}}
        else if((mode==System.DISPLAY_MODE_LOW_POWER||mode==System.DISPLAY_MODE_OFF)&&restoreTimer!=null){restoreTimer.stop();restoreTimer=null;}
    }
    (:typecheck(disableBackgroundCheck))
    function onSettingsChanged() as Void {try{var now=Time.now().value().toLong();var reminderTransfer=new NativeTransfer(configuredFeedUrl(),null);reminderTransfer.load();LaunchReminder.syncEnable(reminderTransfer.store,now);armFeed(reminderTransfer,now);}catch(e){}var current=view;if(current!=null){current.setSettings(new SceneSettings(null).load());if(current.canForegroundWork()){reloadFeed();}WatchUi.requestUpdate();}}
}
