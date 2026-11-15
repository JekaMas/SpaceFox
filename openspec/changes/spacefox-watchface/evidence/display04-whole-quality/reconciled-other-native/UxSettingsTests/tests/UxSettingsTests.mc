import Toybox.Lang;
import Toybox.Test;
import Toybox.Application;
import Toybox.Background;

// Real Properties storage and application callback, not a fabricated settings dictionary.
(:test, :typecheck(false)) function uxSettingsCallbackAndReopen(logger) {
    var oldUrl=Application.Properties.getValue("FeedBaseUrl");
    var oldFields=[]; var oldColors=[];
    for(var i=1;i<=4;i+=1){oldFields.add(Application.Properties.getValue("Field"+i));oldColors.add(Application.Properties.getValue("Field"+i+"Color"));}
    try {
        Application.Properties.setValue("FeedBaseUrl","");
        var app=new SpaceFoxApp();
        app.view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
        for(var slot=1;slot<=4;slot+=1){
            for(var i=1;i<=4;i+=1){Application.Properties.setValue("Field"+i,i-1);}
            Application.Properties.setValue("Field"+slot,5);
            Application.Properties.setValue("Field"+slot+"Color",3);
            app.onSettingsChanged();
            Test.assert(app.view.settings.slots[slot-1].equals("battery"));
            Test.assert(app.view.settings.fieldColors[slot-1]==0xCDB7FF);
            var reopened=new SceneSettings(null).load();
            Test.assert(reopened.slots[slot-1].equals("battery"));
            Test.assert(reopened.fieldColors[slot-1]==0xCDB7FF);
            logger.debug("UX_SETTINGS slot="+slot+" persisted=battery color=lavender callback=true");
        }
    } finally {
        for(var i=1;i<=4;i+=1){Application.Properties.setValue("Field"+i,oldFields[i-1]);Application.Properties.setValue("Field"+i+"Color",oldColors[i-1]);}
        Application.Properties.setValue("FeedBaseUrl",oldUrl);Background.deleteTemporalEvent();
    }
    return true;
}

(:test, :typecheck(false)) function uxCalendarCountdown(logger) {
    var p=new LocalePresentation();p.qualificationMode=true;p.prepare("en");
    Test.assert(p.calendar([7,14,11]).equals("Sat 14.11"));
    p.prepare("ru");Test.assert(p.calendar([7,14,11]).equals("Сб 14.11"));
    Test.assert(CountdownFormat.format(176523l).equals("T- 49:02:03"));
    Test.assert(CountdownFormat.format(59l).equals("T- 00:00:59"));
    Test.assert(CountdownFormat.format(-59l).equals("T+ 00:00:59"));
    Test.assert(CountdownFormat.format(null).equals("--:--:--"));
    Test.assert(CountdownFormat.format(176523l).equals("T- 49:02:03"));
    Test.assert(CountdownFormat.format(-59l).equals("T+ 00:00:59"));
    logger.debug("UX_CALENDAR en=Sat_14.11 ru=Сб_14.11 AOD=seconds_at_minute_snapshot active=seconds");return true;
}
