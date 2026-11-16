import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;

// Expected device dimensions and margins are injected by the compiler driver.
// These assertions reach the actual production view, not a Python projection.
(:test, :typecheck(false))
function devices020ViewportAndModes(logger) {
    var target=Graphics.createBufferedBitmap({:width=>Devices020.W,:height=>Devices020.H,:colorDepth=>16}).get();
    var dc=target.getDc();var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
    view.onLayout(dc);
    if(Devices020.W==390&&Devices020.H==390){Test.assert(view.sceneBuffer==null);}
    else {Test.assert(view.sceneBuffer!=null&&view.sceneScaleOptions!=null);Test.assert(view.sceneWidth==Devices020.W&&view.sceneHeight==Devices020.H);Test.assert(view.sceneX==Devices020.X&&view.sceneY==Devices020.Y);}
    view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
    view.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);
    view.releaseVisualForSettings();view.onLayout(dc);
    if(Devices020.W!=390||Devices020.H!=390){Test.assert(view.sceneScaleOptions!=null&&view.sceneX==Devices020.X&&view.sceneY==Devices020.Y);}
    Test.assert(view.settings.slots.size()==4);
    logger.debug("VIEWPORT "+Devices020.W+"x"+Devices020.H+" margin="+Devices020.X+","+Devices020.Y+" modes=HIGH,LOW fields=4 recreated=true");return true;
}
(:test, :typecheck(false))
function devices020PrimaryFonts(logger) {
    var bitmap=Graphics.createBufferedBitmap({:width=>390,:height=>390,:colorDepth=>16}).get();var dc=bitmap.getDc();var p=new LocalePresentation();
    var codes=["en","ru","de","fr","es"];
    for(var i=0;i<codes.size();i+=1){p.prepare(codes[i]);Test.assert(p.locale.equals(codes[i]));Test.assert(p.count!=null&&p.count!=Graphics.FONT_SMALL&&p.label!=Graphics.FONT_TINY);Test.assert(dc.getTextWidthInPixels("12:34",p.count)>0);}
    p.prepare("ru");Test.assert(dc.getTextWidthInPixels("Космодром",p.small)>0);
    logger.debug("FONTS five primary modes; scalable clock and Latin labels; Cyrillic width positive");return true;
}
