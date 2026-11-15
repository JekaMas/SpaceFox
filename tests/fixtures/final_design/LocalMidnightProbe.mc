import Toybox.Application;
import Toybox.Lang;
import Toybox.Test;
import Toybox.Time;
import Toybox.Time.Gregorian;
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}
(:test,:typecheck(false)) function finalGregorianMidnight(logger as Test.Logger) as Boolean {
    // Anchor to the simulator's own local offset on this captured day. The
    // two absolute moments straddle 2026-11-14 00:00 local by one second.
    var moment=Time.now();var now=moment.value();var info=Gregorian.info(moment,Time.FORMAT_SHORT);
    var offset=info.hour*3600+info.min*60+info.sec-(now%86400);
    if(offset>50400){offset-=86400;}if(offset< -43200){offset+=86400;}
    var before=Gregorian.info(new Time.Moment(1794614400-offset-1),Time.FORMAT_SHORT);
    var after=Gregorian.info(new Time.Moment(1794614400-offset),Time.FORMAT_SHORT);
    logger.debug("actual Gregorian local boundary before="+before.day_of_week+"/"+before.day+"/"+before.month+" after="+after.day_of_week+"/"+after.day+"/"+after.month);
    return before.day_of_week==6 && before.day==13 && before.month==11 && after.day_of_week==7 && after.day==14 && after.month==11;
}
