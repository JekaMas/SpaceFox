import Toybox.Lang;
import Toybox.WatchUi;

// Resource dictionaries are read only while settings or the selected source
// needs them; no full multilingual catalog is resident with the active scene.
(:extendedCode, :typecheck(false))
module FieldText {
    function index(locale){if(locale.equals("ru")){return 1;}if(locale.equals("de")){return 2;}if(locale.equals("fr")){return 3;}if(locale.equals("es")){return 4;}return 0;}
    function menu(locale){var ids=[Rez.JsonData.FieldMenu0,Rez.JsonData.FieldMenu1,Rez.JsonData.FieldMenu2,Rez.JsonData.FieldMenu3,Rez.JsonData.FieldMenu4];return WatchUi.loadResource(ids[index(locale)]);}
    function weather(locale){var ids=[Rez.JsonData.FieldWeather0,Rez.JsonData.FieldWeather1,Rez.JsonData.FieldWeather2,Rez.JsonData.FieldWeather3,Rez.JsonData.FieldWeather4];return WatchUi.loadResource(ids[index(locale)])["labels"];}
    function status(locale){var ids=[Rez.JsonData.FieldStatus0,Rez.JsonData.FieldStatus1,Rez.JsonData.FieldStatus2,Rez.JsonData.FieldStatus3,Rez.JsonData.FieldStatus4];return WatchUi.loadResource(ids[index(locale)])["labels"];}
}
