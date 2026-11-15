import Toybox.Application;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;

(:test,:typecheck(false)) function finalSettingsPositive(log){
 var keys=["ClockColor","CountdownColor","Field1Color","Field2Color","Field3Color","Field4Color"];var wanted=[2,3,0,4,5,1];
 Test.assertEqual(new SceneSettings(null).language,"en");var app=new SpaceFoxApp();Application.Properties.setValue("FeedBaseUrl","https://final-native-timing.invalid");var v=app.getInitialView()[0];
 Application.Properties.setValue("Language",1);for(var i=0;i<keys.size();i+=1){Application.Properties.setValue(keys[i],wanted[i]);}Application.Properties.setValue("Field1",4);Application.Properties.setValue("Field2",5);Application.Properties.setValue("Field3",2);Application.Properties.setValue("Field4",3);app.onSettingsChanged();
 var reopened=new SceneSettings(null).load();Test.assertEqual(v.settings.language,"ru");Test.assertEqual(reopened.language,"ru");Test.assertEqual(v.presentation.locale,"ru");Test.assert(!v.presentation.qualificationMode);
 Test.assertEqual(v.settings.clockColor,0x9ad5ff);Test.assertEqual(reopened.countdownColor,0xcdb7ff);for(var k=0;k<4;k+=1){Test.assertEqual(reopened.fieldColors[k],[0x7fe7c6,0xffd686,0xffafcf,0xf7f9fc][k]);}Test.assertEqual(reopened.slots[0],"calories");Test.assertEqual(reopened.slots[1],"battery");Test.assertEqual(reopened.slots[2],"heart");Test.assertEqual(reopened.slots[3],"stress");Test.assertEqual(Application.Properties.getValue("FeedBaseUrl"),"https://final-native-timing.invalid");
 for(var j=0;j<keys.size();j+=1){Application.Properties.setValue(keys[j],j<2?0:1);}Application.Properties.setValue("Language",0);Application.Properties.setValue("Field1",0);Application.Properties.setValue("Field2",1);Application.Properties.setValue("Field3",2);Application.Properties.setValue("Field4",3);Application.Properties.setValue("FeedBaseUrl","");
 log.debug("actual Properties/app.onSettingsChanged/load; distinct6colors+RU, retained4roles andFeedBaseUrl; UI/mobile selection not claimed");return true;
}
(:test,:typecheck(false)) function finalSettingsNegative(log){
 var s=new SceneSettings({"Language"=>null,"ClockColor"=>99,"CountdownColor"=>-1,"Field1Color"=>true,"Field2Color"=>"2","Field3Color"=>1.5,"Field4Color"=>null,"Field1"=>99});
 Test.assertEqual(s.language,"en");Test.assertEqual(s.clockColor,0x7fe7c6);Test.assertEqual(s.countdownColor,0x7fe7c6);for(var j=0;j<4;j+=1){Test.assertEqual(s.fieldColors[j],0xf7f9fc);}Test.assertEqual(s.slots.size(),4);Test.assertEqual(s.slots[0],"steps");
 var presentation=new LocalePresentation();presentation.prepare("sk");Test.assertEqual(presentation.locale,"en");presentation.prepare("ar");Test.assertEqual(presentation.locale,"en");presentation.prepare("unsupported");Test.assertEqual(presentation.locale,"en");
 var automatic=new SceneSettings({"Language"=>36});automatic.selectSystemLanguage(System.LANGUAGE_RUS);Test.assert(automatic.autoLanguage);Test.assertEqual(automatic.language,"ru");
 for(var i=0;i<36;i+=1){Test.assertEqual(new SceneSettings({"Language"=>i}).language,SceneStrings.locale(i));}
 log.debug("unknown or wrongtyped palette values default individually; Auto+36 internalIDs retained; no new layout/clock options");return true;
}
