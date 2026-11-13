import Toybox.Test;
import Toybox.Lang;
import Toybox.Graphics;
import Toybox.System;
import Toybox.WatchUi;
(:test,:typecheck(false)) function localeSelectionPositive(logger){
 var s=new SceneSettings({"Language"=>1,"Field1"=>5,"Field2"=>4});
 Test.assertEqual(s.language,"ru");Test.assertEqual(s.slots[0],"battery");Test.assertEqual(s.slots[1],"calories");
 var automatic=new SceneSettings({"Language"=>36});Test.assert(automatic.autoLanguage);automatic.selectSystemLanguage(System.LANGUAGE_RUS);Test.assertEqual(automatic.language,"ru");automatic.selectSystemLanguage(System.LANGUAGE_THA);Test.assertEqual(automatic.language,"th");automatic.selectSystemLanguage("zzz");Test.assertEqual(automatic.language,"en");s.selectSystemLanguage("eng");Test.assertEqual(s.language,"ru");
 Test.assertEqual(new SceneSettings({"Language"=>0}).language,"en");Test.assertEqual(SceneStrings.systemIndex("zhs"),26);Test.assertEqual(SceneStrings.systemIndex("zht"),27);
 var system=[System.LANGUAGE_ENG,System.LANGUAGE_RUS,System.LANGUAGE_DEU,System.LANGUAGE_FRE,System.LANGUAGE_SPA,System.LANGUAGE_ITA,System.LANGUAGE_POR,System.LANGUAGE_DUT,System.LANGUAGE_POL,System.LANGUAGE_UKR,System.LANGUAGE_CES,System.LANGUAGE_SLO,System.LANGUAGE_HUN,System.LANGUAGE_RON,System.LANGUAGE_BUL,System.LANGUAGE_HRV,System.LANGUAGE_SLV,System.LANGUAGE_GRE,System.LANGUAGE_TUR,System.LANGUAGE_DAN,System.LANGUAGE_SWE,System.LANGUAGE_NOB,System.LANGUAGE_FIN,System.LANGUAGE_EST,System.LANGUAGE_LAV,System.LANGUAGE_LIT,System.LANGUAGE_CHS,System.LANGUAGE_CHT,System.LANGUAGE_JPN,System.LANGUAGE_KOR,System.LANGUAGE_ARA,System.LANGUAGE_HEB,System.LANGUAGE_IND,System.LANGUAGE_ZSM,System.LANGUAGE_VIE,System.LANGUAGE_THA];
 for(var j=0;j<system.size();j+=1){Test.assertEqual(SceneStrings.systemIndex(system[j]),j);}Test.assertEqual(SceneStrings.systemIndex(-1),0);
 for(var i=0;i<36;i+=1){Test.assertEqual(new SceneSettings({"Language"=>i}).language,SceneStrings.locale(i));}
 return true;
}
(:test,:typecheck(false)) function localeSelectionNegative(logger){
 Test.assertEqual(new SceneSettings({"Language"=>-1}).language,"en");Test.assertEqual(new SceneSettings({"Language"=>999}).language,"en");Test.assertEqual(new SceneSettings({"Language"=>"unsupported"}).language,"en");
 var p=new LocalePresentation();p.prepare("sk");Test.assertEqual(p.locale,"en");p.prepare("ar");Test.assertEqual(p.locale,"en");p.prepare("unsupported");Test.assertEqual(p.locale,"en");return true;
}
(:test,:typecheck(false)) function localeFormatsPositive(logger){
 var p=new LocalePresentation();p.prepare("ru");Test.assertEqual(p.number("12345"),"12 345");Test.assertEqual(p.date("2026-11-12"),"12/11/2026");
 var c=new ClockSnapshot("12:00","DATE ONLY");c.date="2026-11-12";Test.assertEqual(p.countdown(c,true),"--:--:--");
 p.prepare("en");var mixed=new ClockSnapshot("12:00","");mixed.remaining=93780;Test.assertEqual(p.countdown(mixed,true),"26:03:00");p.prepare("ru");Test.assertEqual(p.countdown(mixed,true),"26:03:00");
 p.prepare("en");Test.assertEqual(p.number("12345"),"12,345");Test.assertEqual(p.date("2026-11-12"),"11/12/2026");
 p.prepare("de");Test.assertEqual(p.date("2026-11-12"),"12/11/2026");
 var w=new WatchClock();Test.assertEqual(w.formatLocal(0,0),"00:00");Test.assertEqual(w.formatLocal(12,0),"12:00");Test.assertEqual(w.formatLocal(23,7),"23:07");return true;
}
(:test,:typecheck(false)) function localeFormatsNegative(logger){
 var p=new LocalePresentation();p.prepare("en");Test.assertEqual(p.number("—"),"—");var c=new ClockSnapshot("08:08","TIME UNKNOWN");Test.assertEqual(p.countdown(c,true),"--:--:--");c.remaining=0;Test.assertEqual(p.countdown(c,false),"00:00:00");return true;
}
