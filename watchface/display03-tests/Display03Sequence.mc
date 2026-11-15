import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Test;
import Toybox.WatchUi;

(:test,:typecheck(false)) class D03Store {
 var data={};var writes=0;function read(k){return data.hasKey(k)?data[k]:null;}function write(k,v){data[k]=v;writes+=1;}function remove(k){data.remove(k);writes+=1;}
}
(:test,:typecheck(false)) class D03Recording extends SceneRenderer {
 var activeCount=0;var lowCount=0;var activeText=null;var lowText=null;
 function initialize(){SceneRenderer.initialize(null);}
 function active(dc,s,settings,values,fitness,progress){activeCount+=1;activeText=s.countdown;SceneRenderer.active(dc,s,settings,values,fitness,progress);}
 function aod(dc,s,minute,settings){lowCount+=1;lowText=s.countdown;SceneRenderer.aod(dc,s,minute,settings);}
}
(:typecheck(false)) function d03ActiveOracle(target,now){var n=target-now;var sign=n>0?"T- ":"T+ ";if(n<0){n=-n;}return sign+(n/3600).format("%02d")+":"+((n%3600)/60).format("%02d")+":"+(n%60).format("%02d");}
(:typecheck(false)) function d03LowOracle(target,now){var n=target-now;var future=n>0;var minutes=future?(n+59)/60:(-n)/60;return (future?"T- ":"T+ ")+(minutes/60).format("%02d")+":"+(minutes%60).format("%02d");}
(:test,:typecheck(false)) function display03CausalSequence(logger){
 // Generated tail follows a directed prefix. Expectations use literal fixture
 // target times and event history, never a value read from the SUT.
 var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);
 var initial=WatchUi.loadResource(Rez.JsonData.DisplayInitial)["raw"];
 var moved=WatchUi.loadResource(Rez.JsonData.DisplayMoved)["raw"];
 for(var seed=1;seed<=5;seed+=1){
  var clock=new Display03Clock();clock.now=1794551202;var store=new D03Store();store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);
  var cache=new NativeCache("https://fixture.invalid/display03",store);Test.assert(cache.accept(initial,clock.now));
  var v=new SpaceFoxView(clock,new ScheduleState(null,"empty"));v.setPacket(cache.packet);var d=new D03Recording();d.prepare(v.context,v.settings);v.renderer=d;v.onShow();
  var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();var target=1794609900;var awake=true;var display=System.DISPLAY_MODE_HIGH_POWER;var previousMode=1;var lastLow=null;
  var events=["tick","sleep","ready","sleep","high","tick","wake","wake","low","tick","tick","advance","tick","high","tick","move","reject","tick"];
  var random=seed;for(var k=0;k<12;k+=1){random=(random*73+19)%997;events.add(["sleep","wake","low","high","advance","tick"][random%6]);}
  var matrix={};
  for(var i=0;i<events.size();i+=1){
   var event=events[i];var disposition="applied";
   if(event.equals("sleep")){if(!awake&&previousMode==0){disposition="observed_no_mutation";}awake=false;v.onEnterSleep();if(previousMode!=0){lastLow=null;}previousMode=0;Test.assertEqual(v.displayMode(),0);}
   else if(event.equals("wake")){if(awake&&previousMode==1){disposition="observed_no_mutation";}awake=true;v.onExitSleep();if(previousMode!=1){lastLow=null;}previousMode=1;Test.assertEqual(v.displayMode(),1);}
   else if(event.equals("low")||event.equals("high")){
    display=event.equals("low")?System.DISPLAY_MODE_LOW_POWER:System.DISPLAY_MODE_HIGH_POWER;
    var nextMode=awake&&display==System.DISPLAY_MODE_HIGH_POWER?1:0;v.syncDisplayMode(display);
    if(previousMode==nextMode){disposition="observed_no_mutation";}else{lastLow=null;}previousMode=nextMode;Test.assertEqual(v.displayMode(),nextMode);
   }
   else if(event.equals("advance")){clock.now+=1;}
   else if(event.equals("ready")){var bridge=cache.packet.bridge;store.write("sf.batch.head",{"base"=>cache.base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>1});store.write("sf.batch.pending",{"base"=>cache.base,"pending"=>false});v.setAssetCache(new NativeRenderSource(store,cache.base,bridge));v.prepareVisual();Test.assert(v.assetCache.ready&&v.sceneLifecycle.pending()&&v.sfrTimer==null);}
   else if(event.equals("move")){Test.assert(cache.accept(moved,clock.now));target=1794611100;v.setPacket(cache.packet);lastLow=null;}
   else if(event.equals("reject")){var before=store.writes;Test.assert(!cache.accept(initial,clock.now));Test.assertEqual(store.writes,before);disposition="observed_no_mutation";}
   else {
    var mode=awake&&display==System.DISPLAY_MODE_HIGH_POWER?1:0;var ac=d.activeCount;var lc=d.lowCount;
    if(mode!=previousMode){lastLow=null;}previousMode=mode;var minute=clock.now/60;
    v.updateForDisplayMode(dc,display);
    if(mode==1){Test.assert(d.activeCount==ac+1&&d.lowCount==lc);Test.assertEqual(d.activeText,d03ActiveOracle(target,clock.now));}
    else if(lastLow==minute){Test.assert(d.lowCount==lc&&d.activeCount==ac);disposition="observed_no_mutation";}
    else{Test.assert(d.lowCount==lc+1&&d.activeCount==ac);Test.assertEqual(d.lowText,d03LowOracle(target,clock.now));lastLow=minute;}
    Test.assertEqual(v.displayMode(),mode);
   }
   Test.assertEqual(v.snapshot().countdown,d03ActiveOracle(target,clock.now));
   var key=event+":"+disposition;matrix[key]=matrix.hasKey(key)?matrix[key]+1:1;
  }
  var required=["tick:applied","tick:observed_no_mutation","sleep:applied","sleep:observed_no_mutation","wake:applied","wake:observed_no_mutation","low:applied","high:applied","advance:applied","ready:applied","move:applied","reject:observed_no_mutation"];
  for(var j=0;j<required.size();j+=1){Test.assert(matrix.hasKey(required[j])&&matrix[required[j]]>0);}
  logger.debug("D03_SEQUENCE seed="+seed+" events="+events.size()+" required_dispositions="+required.size()+" skipped=0");
  v.onHide();
 }
 return true;
}
(:test,:typecheck(false)) class D03Loader {var calls=0;function load(){calls+=1;}}
(:test,:typecheck(false)) function display03ReadyAndErrorOnWake(logger){
 var clock=new Display03Clock();clock.now=1794551202;var store=new D03Store();var cat=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);store.write("sf.obj."+cat["catalogDigest"],cat["catalog"]);
 var cache=new NativeCache("https://fixture.invalid/display03-ready",store);var initial=WatchUi.loadResource(Rez.JsonData.DisplayInitial)["raw"];var moved=WatchUi.loadResource(Rez.JsonData.DisplayMoved)["raw"];Test.assert(cache.accept(initial,clock.now));
 var v=new SpaceFoxView(clock,new ScheduleState(null,"empty"));v.setPacket(cache.packet);var d=new D03Recording();d.prepare(v.context,v.settings);v.renderer=d;var loader=new D03Loader();v.pendingLoader=loader.method(:load);
 v.onShow();v.onEnterSleep();Test.assert(cache.accept(moved,clock.now));v.setPacket(cache.packet);var identity=v.context.launchId;
 var writes=store.writes;Test.assert(!cache.accept(initial,clock.now));Test.assertEqual(store.writes,writes);Test.assertEqual(v.context.launchId,identity);Test.assertEqual(v.snapshot().countdown,d03ActiveOracle(1794611100,clock.now));
 var bridge=cache.packet.bridge;store.write("sf.batch.head",{"base"=>cache.base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>1});store.write("sf.batch.pending",{"base"=>cache.base,"pending"=>false});
 v.setAssetCache(new NativeRenderSource(store,cache.base,bridge));Test.assert(v.assetCache.ready);v.prepareVisual();Test.assert(v.sceneLifecycle.pending()&&v.sfrTimer==null&&loader.calls==0);
 v.onExitSleep();var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);
 Test.assert(d.activeCount==1&&loader.calls==0&&v.sfrTimer==null);Test.assertEqual(d.activeText,d03ActiveOracle(1794611100,clock.now));Test.assertEqual(v.context.launchId,identity);v.onHide();
 logger.debug("READY_ERROR sleep accepted_target retained rejected_old no_load_until_first_active_frame=true");return true;
}
(:background,:test,:typecheck(false)) class D03CountingApp extends SpaceFoxApp {
 var reloads=0;function initialize(){SpaceFoxApp.initialize();}
 (:typecheck(disableBackgroundCheck)) function reloadFeed(){reloads+=1;}
}
(:test,:typecheck(false)) function display03BackgroundBeforeFrame(logger){
 var app=new D03CountingApp();var clock=new Display03Clock();var v=new SpaceFoxView(clock,new ScheduleState(1794762690,"exact"));var d=new Display03ModeRenderer();v.renderer=d;app.view=v;v.pendingLoader=app.method(:reloadFeed);
 v.onShow();v.onEnterSleep();app.onBackgroundData({"ready"=>true});Test.assert(app.reloads==1);
 v.onExitSleep();app.onBackgroundData({"ready"=>true});Test.assert(app.reloads==1);
 var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();v.updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);Test.assert(d.activeCalls==1&&app.reloads==1);
 app.onBackgroundData({"ready"=>true});Test.assert(app.reloads==1);v.onHide();logger.debug("BACKGROUND sleep_applied=true wake_first_frame no_reload=true");return true;
}
