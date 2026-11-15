import Toybox.Application;
import Toybox.WatchUi;
(:background,:typecheck(false)) class SettingsProbeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();} function getInitialView(){Application.Properties.setValue("Language",0);feed=new NativeCache("https://jekamas.github.io/SpaceFox",null);feed.failure="update-rejected";return SettingsMenu.root(self);}}
