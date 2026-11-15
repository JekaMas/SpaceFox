import Toybox.Application;
import Toybox.Background;
import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

(:test,:typecheck(false)) function currentMenuSettings(logger) {
    var keys=SettingsMenu.keys();
    Test.assertEqual(keys.size(),12);Test.assertEqual(keys[0],"Language");Test.assertEqual(keys[11],"FeedBaseUrl");
    Test.assertEqual(Application.Properties.getValue("FeedBaseUrl"),"https://jekamas.github.io/SpaceFox");
    Test.assertEqual(SettingsMenu.labels(0).size(),6);Test.assertEqual(SettingsMenu.labels(1).size(),6);
    var app=new SpaceFoxApp();app.view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
    SettingsMenu.apply(app,"Language",1);Test.assertEqual(app.view.settings.language,"ru");
    SettingsMenu.apply(app,"Field2",5);Test.assertEqual(app.view.settings.slots[1],"battery");
    var url=new SettingsUrlDelegate(app);Test.assert(url.onTextEntered("https://final-native-timing.invalid",true));
    Test.assertEqual(Application.Properties.getValue("FeedBaseUrl"),"https://final-native-timing.invalid");
    var reload=new SceneSettings(null).load();Test.assertEqual(reload.language,"ru");Test.assertEqual(reload.slots[1],"battery");
    Application.Properties.setValue("Language",0);Application.Properties.setValue("Field2",1);Application.Properties.setValue("FeedBaseUrl","https://jekamas.github.io/SpaceFox");Background.deleteTemporalEvent();
    logger.debug("CURRENT_MENU defaultUrl=true primaryChoices=6 metricChoices=6 russianCallback=true rolePersist=true urlDelegate=true");return true;
}
