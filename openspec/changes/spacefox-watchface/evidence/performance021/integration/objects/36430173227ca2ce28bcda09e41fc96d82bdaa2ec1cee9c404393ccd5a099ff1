import Toybox.Application;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
import Toybox.WatchUi;

// One ordinary AppBase UUID and immutable package. Separate wall-clock phase
// boundaries make the reader independent of app Storage. The read phase is
// reentrant and never writes; a later explicitly invoked phase tests mutations.
(:typecheck(false)) class CrossVmView extends WatchUi.WatchFace {
 var app;function initialize(a){WatchFace.initialize();app=a;}function onUpdate(dc){app.step();}
}
(:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 var store;var c;var a;var b;var newer;var badInstance;var nonce;var stage;var before;
 function initialize(){AppBase.initialize();}
 function onStop(state){System.println("CROSSVM_APP_STOP stage="+stage);}
 function ensure(ok,message){if(!ok){System.println("CROSSVM_FAIL "+message);throw new Lang.InvalidValueException(message);}}
 function getInitialView(){
  store=new NativeStore();c=new NativeCache("https://fixture.invalid/crossvm",store);
  a=WatchUi.loadResource(Rez.JsonData.CrossA)["raw"];b=WatchUi.loadResource(Rez.JsonData.CrossB)["raw"];newer=WatchUi.loadResource(Rez.JsonData.CrossNewer)["raw"];badInstance=WatchUi.loadResource(Rez.JsonData.CrossBadInstance)["raw"];
  nonce=Application.Storage.getValue("sf.crossvm.nonce");var epoch=Time.now().value().toLong();stage=epoch<@@BOUNDARY@@l?0:epoch<@@BOUNDARY2@@l?10:20;
  System.println("CROSSVM_OPEN nonce="+nonce+" stage="+stage+" epoch="+epoch+" uptime="+System.getTimer());
  if(stage!=0&&(nonce==null||!nonce.equals("@@NONCE@@"))){System.println("CROSSVM_READER_REFUSED missingOrWrongNonce=true noWrites=true");System.exit();stage=99;}
  else if(stage==0&&nonce!=null){System.println("CROSSVM_WRITER_REFUSED existingNonce=true noWrites=true");System.exit();stage=99;}
  return [new CrossVmView(self)];
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
   ensure(c.packet.wireHash.equals("@@HASH_B@@"),"B wire");var floor=store.read(c.pinKey);
   ensure(floor["instance"].equals("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")&&floor["generation"]==2&&floor["selectionValidatedUtc"]==1794603900l&&floor["wireHash"].equals("@@HASH_B@@"),"B floor");
   Application.Storage.setValue("sf.crossvm.nonce","@@NONCE@@");
   System.println("CROSSVM_PHASE1 nonce=@@NONCE@@ id="+c.packet.launchId()+" target="+c.packet.refreshTarget()+" validation="+c.packet.validation+" rescheduled="+c.packet.rescheduled+" stale="+c.packet.stale+" generation="+floor["generation"]+" origin="+floor["selectionValidatedUtc"]+" wire="+c.packet.wireHash+" seed=true");stage=99;System.exit();return;
  }
  if(stage==10||stage==20){
   before=store.writes;var other=new NativeCache("https://fixture.invalid/other-crossvm",store);ensure(other.load(1794612901l)==null,"namespace isolated");
   ensure(c.load(1794612901l)!=null,"reopen B from SDK Storage");ensure(c.packet.launchId().equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"),"reopened identity");
   ensure(c.packet.refreshTarget()==1794611100l&&c.packet.validation==1794603900l&&c.packet.rescheduled&&c.packet.stale,"reopened MIN facts and slept-through stale");
   ensure(c.packet.interval(1794612901l)==3600&&c.packet.wireHash.equals("@@HASH_B@@"),"reopened hourly B wire");
   var floor=store.read(c.pinKey);ensure(floor["instance"].equals("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")&&floor["generation"]==2&&floor["selectionValidatedUtc"]==1794603900l&&floor["wireHash"].equals("@@HASH_B@@"),"persisted floor");
   ensure(store.writes==before,"reader wrote storage");
   if(stage==10){System.println("CROSSVM_PHASE2_READ nonce=@@NONCE@@ id="+c.packet.launchId()+" target="+c.packet.refreshTarget()+" validation="+c.packet.validation+" stale="+c.packet.stale+" rescheduled="+c.packet.rescheduled+" generation="+floor["generation"]+" origin="+floor["selectionValidatedUtc"]+" wire="+c.packet.wireHash+" noReseed=true noWrites=true");stage=99;System.exit();return;}
   stage=21;again();return;
  }
  if(stage==21){before=store.writes;ensure(c.accept(b,1794612901l)&&c.packet.stale&&store.writes==before,"old replay cannot renew or rewrite");stage=22;again();return;}
  if(stage==22){ensure(!c.accept(a,1794612901l),"old generation rejected");stage=23;again();return;}
  if(stage==23){ensure(!c.accept(badInstance,1794612901l),"changed publisher instance rejected");var pin=store.read(c.pinKey);ensure(pin["instance"].equals("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")&&pin["generation"]==2&&pin["selectionValidatedUtc"]==1794603900l,"instance floor retained");stage=24;again();return;}
  if(stage==24){ensure(c.accept(newer,1794612901l),"newer admitted");ensure(c.packet.validation==1794612901l&&!c.packet.stale&&c.packet.rescheduled&&c.packet.refreshTarget()==1794611100l,"newer clears stale");stage=25;again();return;}
  if(stage==25){
   var reopened=new NativeCache("https://fixture.invalid/crossvm",store);ensure(reopened.load(1794612901l)!=null&&reopened.packet.validation==1794612901l&&!reopened.packet.stale&&reopened.packet.rescheduled,"newer persisted");
   var next=store.read(reopened.pinKey);ensure(next["instance"].equals("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")&&next["generation"]==3&&next["selectionValidatedUtc"]==1794612901l,"new floor");
   System.println("CROSSVM_PHASE3_MUTATE nonce=@@NONCE@@ id="+reopened.packet.launchId()+" target="+reopened.packet.refreshTarget()+" replayNoWrite=true oldRejected=true changedInstanceRejected=true newValidation="+reopened.packet.validation+" newStale="+reopened.packet.stale+" rescheduled="+reopened.packet.rescheduled+" newGeneration="+next["generation"]+" origin="+next["selectionValidatedUtc"]+" noReseed=true");stage=99;System.exit();return;
  }
  if(stage==99){return;}ensure(false,"invalid phase");
 }
}
