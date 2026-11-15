import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;
(:typecheck(false)) class UiSettingsReopenView extends WatchUi.WatchFace {
    var done=false;
    function initialize(){WatchFace.initialize();}
    function ensure(ok,label){if(!ok){System.println("SETTINGS_REOPEN_FAIL "+label);throw new Lang.InvalidValueException(label);}}
    function onUpdate(dc){
        if(done){return;}done=true;var marker=Application.Storage.getValue("ui.settings.seeded");
        if(marker==null){
            Application.Properties.setValue("Language",1);var keys=["ClockColor","CountdownColor","Field1Color","Field2Color","Field3Color","Field4Color"];var colors=[2,3,0,4,5,1];for(var i=0;i<6;i+=1){Application.Properties.setValue(keys[i],colors[i]);}
            var fields=[4,5,0,1];for(var j=0;j<4;j+=1){Application.Properties.setValue("Field"+(j+1),fields[j]);}
            Application.Properties.setValue("FeedBaseUrl","https://final-native-timing.invalid");Application.Storage.setValue("ui.settings.seeded",true);
            var a=new SceneSettings(null).load();ensure(a.language.equals("ru")&&a.slots[0].equals("calories")&&a.slots[1].equals("battery"),"seed");System.println("SETTINGS_SEEDED ru=true fields=4 colors=6 url=true");System.exit();
        }else{
            var b=new SceneSettings(null).load();ensure(b.language.equals("ru")&&b.clockColor==0x9ad5ff&&b.countdownColor==0xcdb7ff,"locale-clock-colors");
            ensure(b.slots[0].equals("calories")&&b.slots[1].equals("battery")&&b.slots[2].equals("steps")&&b.slots[3].equals("energy"),"fields");
            ensure(b.fieldColors[0]==0x7fe7c6&&b.fieldColors[1]==0xffd686&&b.fieldColors[2]==0xffafcf&&b.fieldColors[3]==0xf7f9fc,"field-colors");
            ensure(Application.Properties.getValue("FeedBaseUrl").equals("https://final-native-timing.invalid"),"url");System.println("SETTINGS_COLD_REOPEN ru=true fields=4 colors=6 url=true");System.exit();
        }
    }
}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
    function initialize(){SpaceFoxApp.initialize();System.println("SFR_PROBE owner=9c561bc3f2744dc1acd4fc3c683cb459|settings-reopen|f46511d66294");}
    (:typecheck(disableBackgroundCheck)) function getInitialView(){return [new UiSettingsReopenView()];}
}
