import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;

(:typecheck(false)) class SparseRecordingDc {
    var color = 0; var rows = []; var dots = 0;
    function setColor(foreground, background) { color = foreground; }
    function clear() {}
    function drawText(x, y, font, value, justify) { rows.add([x,y,value,color]); }
    function getTextWidthInPixels(value, font) { return value.length() * 10; }
    function fillCircle(x,y,radius) { dots += 1; }
}
(:test,:typecheck(false)) function sparseStatusAllCombinations(logger) {
    // Actual captured Vulcan context; unknown timing is a technical condition.
    for (var r=0; r<2; r+=1) {
        for (var s=0; s<2; s+=1) {
            var c=new SceneContext({"id"=>"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a","rocket"=>"Vulcan VC6L","operator"=>"United Launch Alliance","purpose"=>"Communications","site"=>"US · Cape Canaveral SFS, FL, USA"});
            c.rescheduled=r==1; c.stale=s==1;
            var d=new SceneRenderer(null); d.prepare(c,new SceneSettings(null));
            var snap=new ClockSnapshot("08:08","--:--:--");
            var dc=new SparseRecordingDc();
            d.aod(dc,snap,0);
            if (dc.rows.size()!=2 || !dc.rows[0][2].equals("08:08") || dc.rows[0][3]!=0x777777 || !dc.rows[1][2].equals("--:--:--") || dc.rows[1][3]!=(r==1?0xA8752D:0x558A78) || (dc.dots>0)!=(s==1) || snap.rescheduled!=(r==1) || snap.stale!=(s==1)) { return false; }
            logger.debug("SPARSE_STATUS rescheduled="+r+" stale="+s+" timeColor="+dc.rows[0][3]+" countColor="+dc.rows[1][3]+" dots="+dc.dots+" unknown="+dc.rows[1][2]);
        }
    }
    return true;
}
