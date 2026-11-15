import Toybox.Application;
import Toybox.Lang;
import Toybox.System;

// Parsing/loading runs outside redraw; keep cold settings code off the small heap.
(:extendedCode)
class SceneSettings {
    var slots as Array<String>;
    var language as String = "en";
    var autoLanguage as Boolean=false;
    var clockColor as Number=0x7FE7C6;
    var countdownColor as Number=0x7FE7C6;
    var fieldColors as Array<Number>;
    function initialize(values as Dictionary<String, Object or Null> or Null) {
        slots = ["steps", "energy", "heart", "stress"];
        fieldColors=[0xF7F9FC,0xF7F9FC,0xF7F9FC,0xF7F9FC];
        if (values == null) { return; }
        for (var i = 0; i < 4; i += 1) {
            var key = "Field" + (i+1);
            var assigned = values[key];
            if(assigned instanceof Number && assigned>=0 && assigned<6){slots[i]=["steps","energy","heart","stress","calories","battery"][assigned];}
            else if (validRole(assigned)) { slots[i] = assigned as String; }
        }
        clockColor=color(values["ClockColor"],0);
        countdownColor=color(values["CountdownColor"],0);
        for(var field=0;field<4;field+=1){fieldColors[field]=color(values["Field"+(field+1)+"Color"],1);}
        var languageValue=values["Language"];
        if((languageValue instanceof Number&&languageValue==36)||(languageValue instanceof String&&languageValue.equals("auto"))){autoLanguage=true;refreshLanguage();}
        else {language=SceneStrings.locale(SceneStrings.index(languageValue));}
    }
    function selectSystemLanguage(code as Object or Null) as Void {if(autoLanguage){language=SceneStrings.locale(SceneStrings.systemIndex(code));}}
    function refreshLanguage() as Void {if(autoLanguage){selectSystemLanguage(System.getDeviceSettings().systemLanguage);}}
    function color(value as Object or Null, fallback as Number) as Number {
        var palette=[0x7FE7C6,0xF7F9FC,0x9AD5FF,0xCDB7FF,0xFFD686,0xFFAFCF];
        return value instanceof Number&&value>=0&&value<palette.size()?palette[value]:palette[fallback];
    }
    function validRole(role as Object or Null) as Boolean {
        if (!(role instanceof String)) { return false; }
        return role.equals("steps") || role.equals("energy") || role.equals("heart") || role.equals("stress") || role.equals("calories") || role.equals("battery");
    }
    function load() as SceneSettings {
        var values = {};
        for (var i = 0; i < 4; i += 1) {
            var key = "Field" + (i+1);
            try { values[key] = Application.Properties.getValue(key); } catch (e) {}
        }
        var keys = ["Language","ClockColor","CountdownColor","Field1Color","Field2Color","Field3Color","Field4Color"];
        for (var j = 0; j < keys.size(); j += 1) {
            try { values[keys[j]] = Application.Properties.getValue(keys[j]); } catch (e) {}
        }
        return new SceneSettings(values);
    }
}
