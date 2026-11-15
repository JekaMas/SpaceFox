import Toybox.Application;
import Toybox.Lang;
import Toybox.System;
import Toybox.WatchUi;

// One ordinary AppBase UUID, same immutable package in both phases. Network is
// substituted by source-bound real-producer packet resources. Only phase one
// seeds objects. The nonce is created once, then read after a simulator restart.
(:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 function initialize(){AppBase.initialize();NativeMetrics.ownerTag="36e82a5e135d4dac86b1a59ac636813b|cross-vm|97617aca74ef";System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);}
 function ensure(ok,message){if(!ok){System.println("CROSSVM_FAIL "+message);throw new Lang.InvalidValueException(message);}}
 function getInitialView(){
  var store=new NativeStore();var url="https://fixture.invalid/crossvm";var c=new NativeCache(url,store);
  var a=WatchUi.loadResource(Rez.JsonData.CrossA)["raw"];var b=WatchUi.loadResource(Rez.JsonData.CrossB)["raw"];
  var newer=WatchUi.loadResource(Rez.JsonData.CrossNewer)["raw"];
  var nonce=Application.Storage.getValue("sf.crossvm.nonce");
  if(nonce==null){
   ensure(store.read("sf.commit")==null,"fresh namespace");var cat=WatchUi.loadResource(Rez.JsonData.CrossCatalog);
   store.write("sf.obj."+cat["digest"],cat["raw"]);
   ensure(c.accept(a,1794603900l),"accept A");ensure(c.accept(b,1794603900l),"accept B");
   ensure(c.packet.launchId().equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"),"B identity");
   ensure(c.packet.refreshTarget()==1794611100l&&c.packet.validation==1794603900l&&c.packet.rescheduled&&!c.packet.stale,"B facts");
   ensure(c.packet.wireHash.equals("c686f5e57622097a9184be9d0e8b3008a61bb421cbc273b194dbbc05d1964a14"),"B wire");var floor=store.read(c.pinKey);
   ensure(floor["generation"]==2&&floor["selectionValidatedUtc"]==1794603900l&&floor["wireHash"].equals("c686f5e57622097a9184be9d0e8b3008a61bb421cbc273b194dbbc05d1964a14"),"B floor");
   Application.Storage.setValue("sf.crossvm.nonce","d45844e588b54d79998450a8f53a79c2");
   System.println("CROSSVM_PHASE1 nonce=d45844e588b54d79998450a8f53a79c2 id="+c.packet.launchId()+" target="+c.packet.refreshTarget()+" validation="+c.packet.validation+" rescheduled="+c.packet.rescheduled+" stale="+c.packet.stale+" generation="+floor["generation"]+" origin="+floor["selectionValidatedUtc"]+" wire="+c.packet.wireHash+" seed=true");
  }else{
   ensure(nonce.equals("d45844e588b54d79998450a8f53a79c2"),"persisted phase nonce");
   var other=new NativeCache("https://fixture.invalid/other-crossvm",store);ensure(other.load(1794612901l)==null,"namespace isolated");
   ensure(c.load(1794612901l)!=null,"reopen B from SDK Storage");
   ensure(c.packet.launchId().equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"),"reopened identity");
   ensure(c.packet.refreshTarget()==1794611100l&&c.packet.validation==1794603900l&&c.packet.rescheduled&&c.packet.stale,"reopened MIN facts and slept-through stale");
   ensure(c.packet.interval(1794612901l)==3600&&c.packet.wireHash.equals("c686f5e57622097a9184be9d0e8b3008a61bb421cbc273b194dbbc05d1964a14"),"reopened hourly B wire");
   var floor=store.read(c.pinKey);ensure(floor["generation"]==2&&floor["selectionValidatedUtc"]==1794603900l&&floor["wireHash"].equals("c686f5e57622097a9184be9d0e8b3008a61bb421cbc273b194dbbc05d1964a14"),"persisted floor");
   var before=store.writes;ensure(c.accept(b,1794612901l)&&c.packet.stale&&store.writes==before,"old replay cannot renew or rewrite");
   ensure(!c.accept(a,1794612901l),"old generation rejected");ensure(c.accept(newer,1794612901l),"newer admitted");
   ensure(c.packet.validation==1794612901l&&!c.packet.stale&&c.packet.rescheduled&&c.packet.refreshTarget()==1794611100l,"newer clears stale");
   var again=new NativeCache(url,store);ensure(again.load(1794612901l)!=null&&again.packet.validation==1794612901l&&!again.packet.stale&&again.packet.rescheduled,"newer persisted");
   var next=store.read(again.pinKey);ensure(next["generation"]==3&&next["selectionValidatedUtc"]==1794612901l,"new floor");
   System.println("CROSSVM_PHASE2 nonce=d45844e588b54d79998450a8f53a79c2 id="+again.packet.launchId()+" target="+again.packet.refreshTarget()+" oldValidation=1794603900 oldStale=true oldGeneration=2 oldWire=c686f5e57622097a9184be9d0e8b3008a61bb421cbc273b194dbbc05d1964a14 replayNoWrite=true oldRejected=true newValidation="+again.packet.validation+" newStale="+again.packet.stale+" rescheduled="+again.packet.rescheduled+" newGeneration="+next["generation"]+" origin="+next["selectionValidatedUtc"]+" noReseed=true");
   Application.Storage.clearValues();System.println("CROSSVM_CLEAN appNamespaceOnly=true");
  }
  System.exit();return [new WatchUi.WatchFace()];
 }
}
