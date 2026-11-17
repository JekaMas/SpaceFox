import Toybox.Test;
import Toybox.WatchUi;
import Toybox.Graphics;
import Toybox.System;
(:test,:typecheck(false)) class SiteStore {
 var data={};function read(key){return data[key];}function write(key,value){data[key]=value;}
}
(:test,:typecheck(false)) class SiteDrawTrace {
 var points=0;var questions=0;
 function setColor(a,b){} function fillCircle(x,y,r){points+=1;}
 function drawText(x,y,font,value,flags){if(value.equals("?")){questions+=1;}}
}
(:test,:typecheck(false)) function knownSiteSnapshotBoundary(logger){
 var value=WatchUi.loadResource(Rez.JsonData.UnknownPad)["payload"];
 var memory=new SiteStore();var store=new NativeTrustedStore(memory,"https://fixture.invalid");Test.assert(store.save(value));
 var packet=new NativeTrustedPacket(store.load());var scene=packet.presentation;
 Test.assert(scene.pointText[0].equals("-0.7692")&&scene.pointText[1].equals("60.8184"));
 var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));view.setPacket(packet);view.onShow();
 var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();view.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
 Test.assert(view.mapDecision.pointVisible(true)&&view.mapDecision.identity.equals(scene.launchId));
 view.onEnterSleep();view.updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);Test.assert(view.mapDecision.pointVisible(true));
 var trace=new SiteDrawTrace();FallbackMap.point(trace,scene.point,97,15);Test.assert(trace.points==1&&trace.questions==0);
 view.onHide();logger.debug("SITE_SNAPSHOT stored_reopened=true active_low_point=true fallback_question=0");return true;
}
(:test,:typecheck(false)) function knownSitePacketAndPoint(logger){
 var data=WatchUi.loadResource(Rez.JsonData.UnknownPad)["payload"];var memory=new SiteStore();var owner=new NativeTrustedStore(memory,"https://fixture.invalid");Test.assert(owner.save(data));
 var scene=new NativeTrustedPacket(owner.load()).presentation;Test.assert(scene.pointText[0].equals("-0.7692")&&scene.pointText[1].equals("60.8184"));
 var policy=new MapPresentation();policy.bind(scene);Test.assert(policy.pointVisible(true)&&policy.identity.equals(scene.launchId));
 var dc=new SiteDrawTrace();FallbackMap.point(dc,scene.point,97,15);Test.assert(dc.points==1&&dc.questions==0);
 var unknown=WatchUi.loadResource(Rez.JsonData.UnknownPad)["payload"];unknown[3][9]=null;var other=new NativeTrustedPacket(unknown).presentation;policy.bind(other);Test.assert(!policy.pointVisible(true)&&policy.point==null);
 logger.debug("SITE_PACKET persisted_reopened=true point_identity=true fallback_marker=1 question=0 missing_point=0");return true;
}
