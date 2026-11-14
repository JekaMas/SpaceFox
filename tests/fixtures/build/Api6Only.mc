import Toybox.Application;
import Toybox.Communications;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;

// Original minimal negative watchface fixture. Background+Communications are
// granted only in its temporary manifest to isolate the API availability edge.
class Api6OnlyApp extends Application.AppBase {
    function initialize() {
        AppBase.initialize();
        System.println(Communications.HTTP_RESPONSE_CONTENT_TYPE_OCTET_STREAM);
    }
}
