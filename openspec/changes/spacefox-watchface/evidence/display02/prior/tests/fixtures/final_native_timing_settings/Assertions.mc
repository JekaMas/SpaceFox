import Toybox.Application;
import Toybox.Test;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
(:typecheck(false)) class FinalPacketStore {
 var data;function initialize(d){data=d;}
 function read(key){return key.equals("sf.obj."+data["catalogDigest"])?data["catalog"]:null;}
}
(:typecheck(false)) function finalRead(label,now){
 var data=WatchUi.loadResource(Rez.JsonData.FinalPackets);var raw=data[label];
 var p=new NativeBridgeFeed(raw,1794576343,new FinalPacketStore(data));
 var precision=p.document["launch"]["timing"]["precision"];var identity=p.launchId();
 var clock=new ControlledClock(now,"08:08");var v=new SpaceFoxView(clock,new ScheduleState(null,"unknown"));v.setPacket(p);
 return [v,v.snapshot(),precision,identity];
}
(:test,:typecheck(false)) function finalTimingPositive(log){
 var times=[1794583543-176523,1794583543-59,1794583543-1,1794583543,1794583543+899,1794583543+900,1794583543+901];
 var expected=["T- 49:02:03","T- 00:00:59","T- 00:00:01","T+ 00:00:00","T+ 00:14:59","T+ 00:15:00","T+ 00:15:01"];
 for(var i=0;i<times.size();i+=1){var r=finalRead("exact",times[i]);Test.assertEqual(r[1].countdown,expected[i]);Test.assertEqual(r[0].presentation.countdown(r[1],true),expected[i]);Test.assertEqual(r[3],"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a");}
 var started=finalRead("started",1794583543+899);Test.assertEqual(started[1].countdown,"T+ 00:14:59");Test.assertEqual(started[3],"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a");
 var minute=finalRead("minute",1794592440+899);Test.assertEqual(minute[1].countdown,"T+ 00:14:59");Test.assertEqual(minute[2],"source-coarse");
 log.debug("production schema3 parser->FeedScene->ScheduleState->View: all7literal states exact and nominalMIN precision preserved; no local liftoff state");return true;
}
(:test,:typecheck(false)) function finalTimingNegative(log){
 var unknown=finalRead("unknown",1794584444);Test.assertEqual(unknown[1].countdown,"--:--:--");
 var corrected=finalRead("exact",1794583543-1);Test.assertEqual(corrected[1].countdown,"T- 00:00:01");
 var huge=new ScheduleState(253402300799l,"exact");Test.assertEqual(huge.display(-62135596800l,true),"T- 87649415:59:59");
 Test.assertEqual(new ScheduleState(null,"exact").display(0,true),"--:--:--");
 Test.assertEqual(new ScheduleState(1794583543,"date").display(1794583543,true),"--:--:--");
 log.debug("unknown/date cannot inherit a precise timer; clock correction unlatches elapsed; signed Long UTC does not wrap");return true;
}
(:test,:typecheck(false)) function finalParserUpdatePositive(log){
 var before=finalRead("exact",1794583643);var postponed=finalRead("postponed",1794583643);var withdrawn=finalRead("withdrawn",1794583643);
 Test.assertEqual(before[1].countdown,"T+ 00:01:40");Test.assertEqual(postponed[1].countdown,"T- 00:18:20");Test.assertEqual(withdrawn[1].countdown,"--:--:--");
 var nominal=finalRead("postponedMinute",1794592540);Test.assertEqual(nominal[1].countdown,"T- 00:18:20");Test.assertEqual(nominal[2],"source-coarse");Test.assert(nominal[0].context.rescheduled);
 Test.assertEqual(before[3],postponed[3]);Test.assertEqual(before[3],withdrawn[3]);Test.assert(postponed[0].context.rescheduled);Test.assert(withdrawn[0].context.rescheduled);
 log.debug("accepted sameID reschedule/targetwithdrawal replaces elapsed coherently through actual parser/context");return true;
}
(:test,:typecheck(false)) function finalParserUpdateNegative(log){
 var data=WatchUi.loadResource(Rez.JsonData.FinalPackets);var rejected=false;try{new NativeBridgeFeed(data["invalid"],1794576343,new FinalPacketStore(data));}catch(e){rejected=true;}Test.assert(rejected);
 var p=finalRead("minute",1794576343);Test.assertEqual(p[2],"source-coarse");Test.assertEqual(p[1].countdown,"T- 04:28:17");
 log.debug("contradictory exact target/sourceNET is rejected; nominalMIN never relabelled exact");return true;
}
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
