import Toybox.Application;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;

// One ordinary AppBase UUID and the same package in both phases. Network is
// substituted by source-bound producer packet resources. Requested redraw
// callbacks separate operations; they are not an OS scheduling proof.
(:typecheck(false)) class CrossVmView extends WatchUi.WatchFace {
 var app;function initialize(a){WatchFace.initialize();app=a;}function onUpdate(dc){app.step();}
}
(:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 var store;var c;var a;var b;var newer;var nonce;var stage;var before;
 function initialize(){AppBase.initialize();NativeMetrics.ownerTag="af7af8c9fc16402888ff948fccbf8ddf|cross-vm|97617aca74ef";System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);}
 function ensure(ok,message){if(!ok){System.println("CROSSVM_FAIL "+message);throw new Lang.InvalidValueException(message);}}
 function getInitialView(){
  store=new NativeStore();c=new NativeCache("https://fixture.invalid/crossvm",store);
  a=WatchUi.loadResource(Rez.JsonData.CrossA)["raw"];b=WatchUi.loadResource(Rez.JsonData.CrossB)["raw"];newer=WatchUi.loadResource(Rez.JsonData.CrossNewer)["raw"];
  nonce=Application.Storage.getValue("sf.crossvm.nonce");stage=nonce==null?0:10;return [new CrossVmView(self)];
 }
 function again(){WatchUi.requestUpdate();}
 function step(){
  if(stage==0){
   ensure(store.read("sf.commit")==null,"fresh namespace");var cat=WatchUi.loadResource(Rez.JsonData.CrossCatalog);
   store.write("sf.obj."+cat["digest"],cat["raw"]);ensure(c.accept(a,1794603900l),"accept A");stage=1;again();return;
  }
  if(stage==1){
   ensure(c.accept(b,1794603900l),"accept B");ensure(c.packet.launchId().equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"),"B identity");
   ensure(c.packet.refreshTarget()==1794611100l&&c.packet.validation==1794603900l&&c.packet.rescheduled&&!c.packet.stale,"B facts");
   ensure(c.packet.wireHash.equals("c686f5e57622097a9184be9d0e8b3008a61bb421cbc273b194dbbc05d1964a14"),"B wire");var floor=store.read(c.pinKey);
   ensure(floor["generation"]==2&&floor["selectionValidatedUtc"]==1794603900l&&floor["wireHash"].equals("c686f5e57622097a9184be9d0e8b3008a61bb421cbc273b194dbbc05d1964a14"),"B floor");
   Application.Storage.setValue("sf.crossvm.nonce","1c078d173bbe49c6bfed3cee492e6112");
   System.println("CROSSVM_PHASE1 nonce=1c078d173bbe49c6bfed3cee492e6112 id="+c.packet.launchId()+" target="+c.packet.refreshTarget()+" validation="+c.packet.validation+" rescheduled="+c.packet.rescheduled+" stale="+c.packet.stale+" generation="+floor["generation"]+" origin="+floor["selectionValidatedUtc"]+" wire="+c.packet.wireHash+" seed=true");
   System.exit();return;
  }
  if(stage==10){
   ensure(nonce.equals("1c078d173bbe49c6bfed3cee492e6112"),"persisted phase nonce");var other=new NativeCache("https://fixture.invalid/other-crossvm",store);
   ensure(other.load(1794612901l)==null,"namespace isolated");ensure(c.load(1794612901l)!=null,"reopen B from SDK Storage");
   ensure(c.packet.launchId().equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"),"reopened identity");
   ensure(c.packet.refreshTarget()==1794611100l&&c.packet.validation==1794603900l&&c.packet.rescheduled&&c.packet.stale,"reopened MIN facts and slept-through stale");
   ensure(c.packet.interval(1794612901l)==3600&&c.packet.wireHash.equals("c686f5e57622097a9184be9d0e8b3008a61bb421cbc273b194dbbc05d1964a14"),"reopened hourly B wire");
   var floor=store.read(c.pinKey);ensure(floor["generation"]==2&&floor["selectionValidatedUtc"]==1794603900l&&floor["wireHash"].equals("c686f5e57622097a9184be9d0e8b3008a61bb421cbc273b194dbbc05d1964a14"),"persisted floor");
   before=store.writes;stage=11;again();return;
  }
  if(stage==11){ensure(c.accept(b,1794612901l)&&c.packet.stale&&store.writes==before,"old replay cannot renew or rewrite");stage=12;again();return;}
  if(stage==12){ensure(!c.accept(a,1794612901l),"old generation rejected");stage=13;again();return;}
  if(stage==13){ensure(c.accept(newer,1794612901l),"newer admitted");ensure(c.packet.validation==1794612901l&&!c.packet.stale&&c.packet.rescheduled&&c.packet.refreshTarget()==1794611100l,"newer clears stale");stage=14;again();return;}
  if(stage==14){
   var reopened=new NativeCache("https://fixture.invalid/crossvm",store);ensure(reopened.load(1794612901l)!=null&&reopened.packet.validation==1794612901l&&!reopened.packet.stale&&reopened.packet.rescheduled,"newer persisted");
   var next=store.read(reopened.pinKey);ensure(next["generation"]==3&&next["selectionValidatedUtc"]==1794612901l,"new floor");
   System.println("CROSSVM_PHASE2 nonce=1c078d173bbe49c6bfed3cee492e6112 id="+reopened.packet.launchId()+" target="+reopened.packet.refreshTarget()+" oldValidation=1794603900 oldStale=true oldGeneration=2 oldWire=c686f5e57622097a9184be9d0e8b3008a61bb421cbc273b194dbbc05d1964a14 replayNoWrite=true oldRejected=true newValidation="+reopened.packet.validation+" newStale="+reopened.packet.stale+" rescheduled="+reopened.packet.rescheduled+" newGeneration="+next["generation"]+" origin="+next["selectionValidatedUtc"]+" noReseed=true");
   Application.Storage.clearValues();System.println("CROSSVM_CLEAN appNamespaceOnly=true");System.exit();return;
  }
  ensure(false,"invalid phase");
 }
}
