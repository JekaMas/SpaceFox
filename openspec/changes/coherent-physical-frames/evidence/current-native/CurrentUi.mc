import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

(:test, :typecheck(false))
function currentFivePrimaryAndBitmapFonts(logger as Test.Logger) as Boolean {
    var p = new LocalePresentation();
    var dc = Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    var locales = ["en", "ru", "de", "fr", "es"];
    var samples = ["T- 25:01:01", "T+ 25:01:01", "23:59", "100%", "—", "0123456789"];
    for (var i=0; i<locales.size(); i+=1) {
        var index=SceneStrings.index(locales[i]);
        Test.assert(SceneStrings.available(index));
        p.prepare(locales[i]);
        Test.assert(p.locale.equals(locales[i]) && p.dictionary!=null && p.count!=null && p.small!=null);
        p.prepareAodFonts();
        Test.assert(p.aodContextFont!=null);
        for (var j=0; j<samples.size(); j+=1) {
            var value=samples[j];
            var fitted=p.fit(dc,value,p.count,275);
            Test.assert(!fitted.equals("") && dc.getTextWidthInPixels(fitted,p.count)<=275);
        }
        var keys=["hour","minute","day","second","noSchedule","dateOnly","window","timeUnknown","awaitUpdate","companyUnknown","missionUnknown","communications"];
        for(var q=0;q<keys.size();q+=1){
            var word=p.word(keys[q]);Test.assert(word.equals(p.dictionary[keys[q]])&&!word.equals(""));
            var shown=p.fit(dc,word,p.small,282);Test.assert(!shown.equals("")&&dc.getTextWidthInPixels(shown,p.small)>0&&dc.getTextWidthInPixels(shown,p.small)<=282);
            dc.drawText(195,70,p.small,shown,Graphics.TEXT_JUSTIFY_CENTER);
        }
        for(var weekday=1;weekday<=7;weekday+=1){var date=p.calendar([weekday,17,11]);Test.assert(!date.equals("")&&dc.getTextWidthInPixels(date,p.calendarFont)>0&&dc.getTextWidthInPixels(date,p.calendarFont)<=282);dc.drawText(195,90,p.calendarFont,date,Graphics.TEXT_JUSTIFY_CENTER);}
        Test.assert(p.mission("Communications").equals(p.dictionary["communications"]));
        var day=p.calendar([2,17,11]);
        Test.assert(!day.equals("") && dc.getTextWidthInPixels(day,p.calendarFont)>0);
        logger.debug("CURRENT_PRIMARY locale="+locales[i]+" date="+day);
    }
    var fonts=[WatchUi.loadResource(Rez.Fonts.Time80),WatchUi.loadResource(Rez.Fonts.Metric32),WatchUi.loadResource(Rez.Fonts.Aod40)];
    for (var k=0; k<fonts.size(); k+=1) {
        Test.assert(fonts[k]!=null && dc.getTextWidthInPixels("0123456789",fonts[k])>0);
        dc.drawText(195,100,fonts[k],"0123456789",Graphics.TEXT_JUSTIFY_CENTER);
    }
    logger.debug("CURRENT_PRIMARY_COMPLETE locales=5 bitmapFonts=3 uiWords=60 calendarStates=35");
    return true;
}
