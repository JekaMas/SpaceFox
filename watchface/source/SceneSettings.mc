import Toybox.Application;
import Toybox.Lang;
import Toybox.System;

// Parsing/loading runs outside redraw; keep cold settings code off the small heap.
(:extendedCode)
class SceneSettings {
    var slots as Array<String>;
    var language as String = "en";
    var autoLanguage as Boolean=false;
    function initialize(values as Dictionary<String, Object or Null> or Null) {
        slots = ["steps", "energy", "heart", "stress"];
        if (values == null) { return; }
        for (var i = 0; i < 4; i += 1) {
            var key = "Field" + (i+1);
            var assigned = values[key];
            if(assigned instanceof Number && assigned>=0 && assigned<6){slots[i]=["steps","energy","heart","stress","calories","battery"][assigned];}
            else if (validRole(assigned)) { slots[i] = assigned as String; }
        }
        var languageValue=values["Language"];
        if((languageValue instanceof Number&&languageValue==36)||(languageValue instanceof String&&languageValue.equals("auto"))){autoLanguage=true;refreshLanguage();}
        else {language=SceneStrings.locale(SceneStrings.index(languageValue));}
    }
    function selectSystemLanguage(code as Object or Null) as Void {if(autoLanguage){language=SceneStrings.locale(SceneStrings.systemIndex(code));}}
    function refreshLanguage() as Void {if(autoLanguage){selectSystemLanguage(System.getDeviceSettings().systemLanguage);}}
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
        var keys = ["Language"];
        for (var j = 0; j < keys.size(); j += 1) {
            try { values[keys[j]] = Application.Properties.getValue(keys[j]); } catch (e) {}
        }
        return new SceneSettings(values);
    }
}
