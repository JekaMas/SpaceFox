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
    // Default ports preserve Garmin behavior; event tests override them before
    // application startup so time, source, scheduling and storage are fake.
    (:typecheck(disableBackgroundCheck)) function createView() as SpaceFoxView {return new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));}
    (:typecheck(disableBackgroundCheck)) function feedUrl() as String {return configuredFeedUrl();}
    (:typecheck(disableBackgroundCheck)) function createCache(url as String) as NativeCache {return new NativeCache(url,null);}
    (:typecheck(disableBackgroundCheck)) function createForegroundTransfer(url as String,adapter as Object or Null) as NativeTransfer {return new NativeTransfer(url,adapter);}
    (:typecheck(disableBackgroundCheck)) function currentUtc() as Long {return Time.now().value().toLong();}
    (:typecheck(disableBackgroundCheck)) function currentDisplayMode() as System.DisplayMode {return System.getDisplayMode();}
    (:typecheck(disableBackgroundCheck)) function armForeground(transfer as NativeTransfer,now as Long) as Void {armFeed(transfer,now);}
    (:typecheck(disableBackgroundCheck)) function syncForegroundReminders(store as Object,now as Long) as Void {LaunchReminder.syncEnable(store,now);}
    (:typecheck(disableBackgroundCheck)) function requestForegroundFrame() as Void {WatchUi.requestUpdate();}
    (:typecheck(disableBackgroundCheck)) function traceMessage(message as String) as Void {System.println(message);}
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
    function onBackgroundData(data as Application.PersistableType) as Void {
        traceMessage("SF_FG background_delivery");
        if(view!=null){view.syncDisplayMode(currentDisplayMode());}
        if(data instanceof Dictionary&&data.hasKey("volatileSnapshot")){
            try{NativeForegroundApp.receiveVolatile(self,data);}catch(e){traceMessage("SF_FG volatile_rejected");}
            return;
        }
        var current=view;if(current==null||!current.displayPermitsFrame()){return;}
        // A notification carries no source identity. Only a genuinely new
        // complete pointer for the currently bound source may trigger work.
        // Repeated or late notifications must not clear a failed admission.
        if(feed!=null){try{var bound=feed as NativeCache;var marker=new NativeTrustedStore(bound.store,bound.base).marker();
            if(!(marker instanceof Dictionary)||!(marker["base"] instanceof String)||!(marker["base"] as String).equals(bound.base as String)){return;}
            var sequence=marker["sequence"];
            if(!(sequence instanceof Number||sequence instanceof Long)||sequence==trustedToken||sequence==failedToken){return;}
        }catch(e){return;}}
        if(current.canAcceptBackground()){try{reloadFeed();}catch(e){}}if(current.displayPermitsFrame()){requestForegroundFrame();}
    }
    (:typecheck(disableBackgroundCheck))
    function reloadFeed() as Void {try{performReload();}catch(e){traceMessage("SF_FG reload_error");}}
    (:typecheck(false)) function performReload() as Void {NativeForegroundApp.reload(self);}
    (:typecheck(disableBackgroundCheck))
    function onDisplayModeChanged() as Void {
        var current=view;var mode=currentDisplayMode();
        if(current==null){return;}
        current.syncDisplayMode(mode);
        if(current.canForegroundWork()){current.prepareVisual();}
    }
    (:typecheck(disableBackgroundCheck))
    function onSettingsChanged() as Void {try{var now=currentUtc();var reminderTransfer=createForegroundTransfer(feedUrl(),null);NativeForegroundApp.bindSource(self,reminderTransfer.base);reminderTransfer.load();syncForegroundReminders(reminderTransfer.store as Object,now);armForeground(reminderTransfer,now);}catch(e){}var current=view;if(current!=null){current.syncDisplayMode(currentDisplayMode());try{current.setSettings(initialSettings());}catch(e){current.releaseRenderer();}if(current.canAcceptBackground()){reloadFeed();}if(current.displayPermitsFrame()){requestForegroundFrame();}}}
}
