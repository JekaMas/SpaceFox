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
    var feed as NativeCache or Null=null;var trustedToken as Number or Long or Null=null;var failedToken as Number or Long or Null=null;
    function initialize(){AppBase.initialize();view=null;}
    (:typecheck(disableBackgroundCheck)) function initialSettings() as SceneSettings {return new SceneSettings(null).load();}
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
        var current=view;if(current!=null){current.pendingLoader=null;current.cancelAdmission=null;current.onHide();}
        view=null;feed=null;
    }
    function getServiceDelegate() as [System.ServiceDelegate] {return [new FeedService()];}
    (:typecheck(disableBackgroundCheck))
    function onBackgroundData(data as Application.PersistableType) as Void {System.println("SF_FG background_delivery");failedToken=null;if(view==null||System.getDisplayMode()==System.DISPLAY_MODE_OFF){return;}if(view.canForegroundWork()){try{reloadFeed();}catch(e){}}WatchUi.requestUpdate();}
    (:typecheck(disableBackgroundCheck))
    function reloadFeed() as Void {try{performReload();}catch(e){System.println("SF_FG reload_error");}}
    (:typecheck(false)) function performReload() as Void {NativeForegroundApp.reload(self);}
    (:typecheck(disableBackgroundCheck))
    function onDisplayModeChanged() as Void {
        var current=view;var mode=System.getDisplayMode();
        if(current==null){return;}
        current.syncDisplayMode(mode);
        if(mode==System.DISPLAY_MODE_HIGH_POWER && current.canForegroundWork()){current.prepareVisual();}
    }
    (:typecheck(disableBackgroundCheck))
    function onSettingsChanged() as Void {try{var now=Time.now().value().toLong();var reminderTransfer=new NativeTransfer(configuredFeedUrl(),null);reminderTransfer.load();LaunchReminder.syncEnable(reminderTransfer.store,now);armFeed(reminderTransfer,now);}catch(e){}var current=view;if(current!=null){try{current.setSettings(new SceneSettings(null).load());}catch(e){current.releaseRenderer();}if(current.canForegroundWork()){reloadFeed();}WatchUi.requestUpdate();}}
}
