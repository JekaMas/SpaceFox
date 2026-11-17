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
        var day=p.calendar([2,17,11]);
        Test.assert(!day.equals("") && dc.getTextWidthInPixels(day,p.calendarFont)>0);
        logger.debug("CURRENT_PRIMARY locale="+locales[i]+" date="+day);
    }
    var fonts=[WatchUi.loadResource(Rez.Fonts.Time80),WatchUi.loadResource(Rez.Fonts.Metric32),WatchUi.loadResource(Rez.Fonts.Aod40)];
    for (var k=0; k<fonts.size(); k+=1) {
        Test.assert(fonts[k]!=null && dc.getTextWidthInPixels("0123456789",fonts[k])>0);
    }
    logger.debug("CURRENT_PRIMARY_COMPLETE locales=5 bitmapFonts=3");
    return true;
}
