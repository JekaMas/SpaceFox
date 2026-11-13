import Toybox.Lang;
import Toybox.Test;
import Toybox.Time;
import Toybox.System;
(:test, :typecheck(false)) class TimingStore {
 var values={}; var writes=0; var reads=0;
 function initialize(){} function read(k){reads+=1;return values[k];} function write(k,v){writes+=1;values[k]=v;} function remove(k){values.remove(k);}
}
(:test) class TimingClock extends WatchClock {
 var now as Number; var local as String;
 function initialize(n as Number,s as String){WatchClock.initialize();now=n;local=s;}
 function utcSeconds() as Number{return now;} function localTimeText() as String{return local;}
}
(:typecheck(false)) function timingView(raw,clock){
 var s=new TimingStore();var c=new NativeCache("https://fixture.invalid/clock",s);
 Test.assert(c.accept(raw,1800000000l));var reopened=new NativeCache("https://fixture.invalid/clock",s);
 Test.assert(reopened.load(1800000000l)!=null);var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.setPacket(reopened.packet);return view;
}
(:test, :typecheck(false)) function originalExactPositive(logger as Test.Logger) as Boolean {
 var c=new TimingClock(1800000000,"08:00");var v=timingView(TimingFixtures.exact(),c);v.onExitSleep();var a=v.snapshot();c.local="12:00";var b=v.snapshot();
 return a.remaining==7200 && b.remaining==7200 && a.localTime.equals("08:00") && b.localTime.equals("12:00") && b.countdown.equals("02:00:00");
}
(:test, :typecheck(false)) function originalExactNegative(logger as Test.Logger) as Boolean {
 var c=new TimingClock(1800000000,"08:00");var v=timingView(TimingFixtures.exact(),c);v.onExitSleep();c.local="12:00";var s=v.snapshot();var before=Time.now().value();var actual=new WatchClock().utcSeconds();var after=Time.now().value();
 return s.remaining==7200 && s.remaining!=7200-4*3600 && s.remaining!=7200-8*3600 && actual>=before && actual<=after;
}
(:test, :typecheck(false)) function originalUncertainPositive(logger as Test.Logger) as Boolean {
 var c=new TimingClock(1800000000,"08:00");var a=timingView(TimingFixtures.date(),c).snapshot();var b=timingView(TimingFixtures.window(),c).snapshot();var d=timingView(TimingFixtures.unknown(),c).snapshot();
 return a.date.equals("2027-01-15") && a.remaining==null && a.countdown.equals("DATE ONLY") && b.remaining==null && b.countdown.equals("LAUNCH WINDOW") && d.remaining==null && d.countdown.equals("TIME UNKNOWN");
}
(:test, :typecheck(false)) function originalUncertainNegative(logger as Test.Logger) as Boolean {
 var c=new TimingClock(1800000000,"08:00");var a=timingView(TimingFixtures.date(),c).snapshot();var b=timingView(TimingFixtures.window(),c).snapshot();
 return a.remaining==null && b.remaining==null && !a.countdown.equals("02:00:00") && !b.countdown.equals("02:00:00");
}
(:test, :typecheck(false)) function originalWakePositive(logger as Test.Logger) as Boolean {
 var c=new TimingClock(1800000000,"08:00");var v=timingView(TimingFixtures.wake(),c);v.onExitSleep();var a=v.snapshot();v.onEnterSleep();c.now=1800007200;c.local="10:00";v.onExitSleep();var b=v.snapshot();
 return a.remaining==10800 && b.remaining==3600 && b.countdown.equals("01:00:00");
}
(:test, :typecheck(false)) function originalWakeNegative(logger as Test.Logger) as Boolean {
 var c=new TimingClock(1800000000,"08:00");var v=timingView(TimingFixtures.wake(),c);v.onExitSleep();v.onEnterSleep();c.now=1800010900;v.onExitSleep();var a=v.snapshot();c.now=1800007200;var b=v.snapshot();c.now=1800003600;var d=v.snapshot();
 return a.remaining==0 && a.countdown.equals("AWAITING UPDATE") && b.remaining==3600 && d.remaining==7200;
}
