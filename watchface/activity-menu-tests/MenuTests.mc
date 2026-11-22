import Toybox.Timer;import Toybox.Graphics;import Toybox.Lang;import Toybox.System;import Toybox.Test;import Toybox.WatchUi;
(:test,:typecheck(false)) class MenuClock extends WatchClock {function utcSeconds(){return 1794818604l;}function localTimeText(){return "08:25";}function localCalendar(){return [3,17,11];}}
(:test,:typecheck(false)) class MenuDraw extends Graphics.Dc {
 var icons=0;var markers=0;var pointMarks=0;var failLowMap=false;var time=false;var recoveryClock=false;var metricTexts=0;var candidates=[];var clears=0;var failMap=false;var failArt=false;var mapFaults=0;var artFaults=0;
 function initialize(){candidates=[WatchUi.loadResource(Rez.Drawables.Metric_steps),WatchUi.loadResource(Rez.Drawables.Metric_energy),WatchUi.loadResource(Rez.Drawables.Metric_heart),WatchUi.loadResource(Rez.Drawables.Metric_stress)];}
 function getWidth(){return 390;}function getHeight(){return 390;}
 function setColor(a,b){}function clear(){clears+=1;icons=0;time=false;recoveryClock=false;metricTexts=0;}function drawBitmap(x,y,b){if(failLowMap&&x==0&&y==0){failLowMap=false;throw new Lang.InvalidValueException("LOW map unavailable");}if(failArt&&x>=22&&x<76&&y>=118&&y<242){failArt=false;artFaults+=1;throw new Lang.InvalidValueException("art fault");}for(var i=0;i<candidates.size();i+=1){if(b==candidates[i]){icons+=1;}}}function drawBitmap2(x,y,b,o){if(failMap){failMap=false;mapFaults+=1;throw new Lang.InvalidValueException("map fault");}}
 function setClip(x,y,w,h){}function clearClip(){}function fillCircle(x,y,r){if(r==3){pointMarks+=1;}}function drawCircle(x,y,r){markers+=1;}function fillPolygon(p){}function drawLine(a,b,c,d){}function fillRectangle(a,b,c,d){}
 function getTextWidthInPixels(t,f){return t.length()*8;}function getFontHeight(f){return 22;}
 function drawText(x,y,f,t,flags){if(y==109&&t.equals("08:25")&&f==WatchUi.loadResource(Rez.Fonts.Time80)){time=true;}if(t.equals("08:25")&&f==Graphics.FONT_NUMBER_MEDIUM){recoveryClock=true;}if(t.equals("10115")||t.equals("75")||t.equals("60")||t.equals("30")){metricTexts+=1;}}
}
(:typecheck(false)) module MenuObserve {var icons=[];var time=false;var values=0;var resources=[];var frames=0;var failMandatory=false;var failOptionalLoad=false;var countdown=null;var metricFonts=[];var clockFont=null;}
(:test,:typecheck(false)) class MenuRenderer extends SceneRenderer {
 function initialize(owner){SceneRenderer.initialize(owner);}
 function active(dc,current,settings,values,fitness,progress){MenuObserve.frames+=1;MenuObserve.countdown=current.countdown;SceneRenderer.active(dc,current,settings,values,fitness,progress);}
 function load(id){MenuObserve.resources.add(id);if(MenuObserve.failOptionalLoad&&(id==Rez.Drawables.MapView0||id==Rez.Drawables.Art_unknown)){throw new Lang.InvalidValueException("optional resource unavailable");}return SceneRenderer.load(id);}
 function icon(dc,x,y,role){if(icons.hasKey(role)){MenuObserve.icons.add([role,x,y]);}SceneRenderer.icon(dc,x,y,role);}
 function text(dc,x,y,font,value,color,width,contour){if(y==109&&value.equals("08:25")){MenuObserve.clockFont=font;if(font==fonts["time"]){MenuObserve.time=true;}}if(y==240||y==278){MenuObserve.values+=1;MenuObserve.metricFonts.add(font);}var result=SceneRenderer.text(dc,x,y,font,value,color,width,contour);if(MenuObserve.failMandatory&&y==240){MenuObserve.failMandatory=false;throw new Lang.InvalidValueException("mandatory metric paint fault");}return result;}
}
(:typecheck(false)) function menuReset(){MenuObserve.icons=[];MenuObserve.time=false;MenuObserve.values=0;MenuObserve.resources=[];MenuObserve.frames=0;MenuObserve.countdown=null;MenuObserve.metricFonts=[];MenuObserve.clockFont=null;}
(:test,:typecheck(false)) class MenuBuild extends NativeSfrBuild {
 function initialize(){result=new NativeSfrRenderer();result.scene={"position"=>null};result.selectionHash="3557175b3da4c08b8cf84d3a57334ce72fa84cbaf410861636e21b41bdb3c226";result.bitmap=WatchUi.loadResource(Rez.Drawables.Metric_steps);}
 function step(){return true;}
 function dispose(){}
}
(:test,:typecheck(false)) class MenuRasterStore extends PbtMemoryStore {
 var failActive=false;
 function write(key,value){if(failActive&&key.equals("sf.raster.active")){throw new Lang.InvalidValueException("injected raster pointer failure");}PbtMemoryStore.write(key,value);}
}
(:test,:typecheck(false)) class MenuView extends SpaceFoxView {
 var timers=[];var mode=System.DISPLAY_MODE_HIGH_POWER;var fakeHeap=0;function initialize(){SpaceFoxView.initialize(new MenuClock(),new ScheduleState(null,"empty"));}
 function deviceMode() as System.DisplayMode {return mode;}function requestFrame() as Void {}function logMode() as Void {}
 function newViewTimer() as Timer.Timer {var t=new PbtTimer();timers.add(t);return t;}function optionalHeapFree(){return fakeHeap;}
 function createSfrBuild(store,base,packet){return new MenuBuild();}
 function createSceneRenderer() as SceneRenderer {return new MenuRenderer(presentation);}
 function refreshFitnessWork() as Void {}function refreshLocale() as Void {}
}
(:test,:typecheck(false)) function menuDeferredDecodeKeepsComposition(logger){
 var raw=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var bridge=raw[6];var store=new PbtMemoryStore();var base="https://example.invalid";
 store.write("sf.batch.head",{"base"=>base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>1});store.write("sf.batch.pending",{"base"=>base,"pending"=>false});
 var cache=new NativeRenderSource(store,base,bridge);Test.assert(cache.ready);
 var view=new MenuView();view.setPacket(new NativeTrustedPacket(raw));view.values={"steps"=>10115,"energy"=>75,"heart"=>60,"stress"=>30};view.onShow();
 var before=new MenuDraw();view.onLayout(before);Test.assert(MenuObserve.resources.indexOf(Rez.Fonts.Time80)>=0);menuReset();view.onUpdate(before);logger.debug("before icons="+MenuObserve.icons.size()+" time="+MenuObserve.time+" values="+MenuObserve.values);var baseline=MenuObserve.icons.size()==4&&MenuObserve.time&&MenuObserve.values==4;
 view.onHide();view.onShow();var after=new MenuDraw();view.onLayout(after);view.onUpdate(after);view.setAssetCache(cache);view.prepareVisual();view.sfrStep();var deferred=new MenuDraw();menuReset();view.onUpdate(deferred);
 logger.debug("deferred icons="+MenuObserve.icons.size()+" time="+MenuObserve.time+" values="+MenuObserve.values);
 Test.assertMessage(baseline,"normal ACTIVE baseline");Test.assertMessage(MenuObserve.icons.size()==4&&MenuObserve.time&&MenuObserve.values==4,"deferred decode must preserve canonical icons and time font");view.onHide();return true;
}

(:test,:typecheck(false)) function menuGeneratedComposition(logger){
 var trace=[];var events=0;var checks=0;var cov=[0,0,0,0,0,0,0,0,0,0,0,0,0];
 for(var seed=1;seed<=8;seed+=1){
  var raw=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var bridge=raw[6];var store=new PbtMemoryStore();var base="https://example.invalid";
  store.write("sf.batch.head",{"base"=>base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>seed});store.write("sf.batch.pending",{"base"=>base,"pending"=>false});var cache=new NativeRenderSource(store,base,bridge);
  var view=new MenuView();view.setPacket(new NativeTrustedPacket(raw));var shown=false;var mode=0;var asleep=false;var reversed=false;var prefix=[0,1,2,1,0,1,6,7,1,10,11,12,1,3,1,4,1,8,1,9,1,5,1,4,1,2];var rng=seed;trace=[];
  for(var i=0;i<34;i+=1){rng=(rng*73+19)%997;var e=i<prefix.size()?prefix[i]:rng%13;trace.add(e);cov[e]+=1;
   if(e==0){view.onShow();shown=true;mode=view.mode==System.DISPLAY_MODE_OFF?2:(view.mode==System.DISPLAY_MODE_HIGH_POWER&&!asleep?0:1);}
   else if(e==1){}
   else if(e==2){view.onHide();shown=false;}
   else if(e==3){view.mode=System.DISPLAY_MODE_LOW_POWER;view.onEnterSleep();asleep=true;mode=1;}
   else if(e==4){view.mode=System.DISPLAY_MODE_HIGH_POWER;view.onExitSleep();asleep=false;mode=0;}
   else if(e==5){view.mode=System.DISPLAY_MODE_OFF;mode=2;}
   else if(e==6){view.setAssetCache(cache);view.prepareVisual();}
   else if(e==7){view.sfrStep();}
   else if(e==8){view.beginAdmission();}
   else if(e==10){view.fakeHeap=50000;view.sfrStep();}
   else if(e==11){view.sfrStep();}
   else if(e==12){view.sfrStep();}
   else{view.endAdmission();reversed=!reversed;if(reversed){view.setSettings(new SceneSettings({"Field1"=>3,"Field2"=>2,"Field3"=>1,"Field4"=>0,"Language"=>1}));}else{view.setSettings(new SceneSettings(null));}}
   menuReset();var dc=new MenuDraw();view.onUpdate(dc);
   if(shown&&mode==0){Test.assert(view.context!=null&&view.context.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));checks+=1;var expected=reversed?["stress","heart","energy","steps"]:["steps","energy","heart","stress"];if(MenuObserve.frames!=1||!MenuObserve.time||MenuObserve.icons.size()!=4||MenuObserve.values!=4){logger.debug("MENU_FAIL seed="+seed+" index="+i+" trace="+trace+" frames="+MenuObserve.frames+" time="+MenuObserve.time+" icons="+MenuObserve.icons);Test.assert(false);}for(var j=0;j<4;j+=1){Test.assert(MenuObserve.icons[j][0].equals(expected[j]));Test.assert(MenuObserve.icons[j][2]==(j<2?249:287));checks+=2;}checks+=3;}
   else{Test.assert(MenuObserve.frames==0);if(!shown||mode==2){Test.assert(dc.clears==0);checks+=1;}checks+=1;}
   if(i==7){Test.assert(view.sfrDeferred&&view.sceneLifecycle.pending());checks+=2;}
   if(i==11){Test.assert(!view.sceneLifecycle.pending());checks+=1;}
   events+=1;
  }
  view.onHide();
 }
 for(var c=0;c<cov.size();c+=1){Test.assert(cov[c]>0);}
 logger.debug("MENU_GENERATED seeds=8 events="+events+" checks="+checks+" event_counts="+cov+" after_each=true");return true;
}

(:test,:typecheck(false)) function menuRetainedAndReplacedVisual(logger){
 var raw=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var bridge=raw[6];var store=new PbtMemoryStore();var base="https://retention.invalid";
 store.write("sf.batch.head",{"base"=>base,"pending"=>false,"catalogDigest"=>bridge["catalogDigest"],"transfer"=>bridge["transfer"],"serial"=>1});store.write("sf.batch.pending",{"base"=>base,"pending"=>false});var cache=new NativeRenderSource(store,base,bridge);
 var view=new MenuView();view.fakeHeap=50000;view.setPacket(new NativeTrustedPacket(raw));view.onShow();view.onUpdate(new MenuDraw());view.setAssetCache(cache);view.prepareVisual();view.sfrStep();view.sfrStep();
 var original=view.downloaded;Test.assert(original!=null&&original.bitmap!=null);
 // A repeated immutable selection is an input event, not a mutation of owner state.
 var identical=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];view.setPacket(new NativeTrustedPacket(identical));Test.assert(view.downloaded==original&&original.bitmap!=null);
 // The next candidate has a different validly shaped identity; the old lease must be released.
 var next=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var b=next[6];var digest="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";b["selection"]={"sha256"=>digest,"decodedBytes"=>100,"path"=>"descriptors/"+digest+".json"};view.setPacket(new NativeTrustedPacket(next));
 Test.assert(view.downloaded==null&&(view.renderer==null||view.renderer.downloaded!=original));view.onHide();logger.debug("same immutable bitmap retained; replaced selection detaches previous bitmap");return true;
}
(:test,:typecheck(false)) function menuOptionalDrawFaults(logger){
 var raw=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var view=new MenuView();view.setPacket(new NativeTrustedPacket(raw));view.onShow();
 var mapDc=new MenuDraw();mapDc.failMap=true;menuReset();view.onUpdate(mapDc);Test.assert(mapDc.mapFaults==1);Test.assert(MenuObserve.frames==1&&MenuObserve.time&&MenuObserve.icons.size()==4&&MenuObserve.values==4);
 var artDc=new MenuDraw();artDc.failArt=true;menuReset();view.onUpdate(artDc);Test.assert(artDc.artFaults==1);Test.assert(MenuObserve.frames==1&&MenuObserve.time&&MenuObserve.icons.size()==4&&MenuObserve.values==4);
 Test.assert(view.context!=null&&view.context.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));view.onHide();logger.debug("optional map/art faults: canonical time and four identities retained");return true;
}
(:test,:typecheck(false)) function menuRootProjectionCase(resource,expected){
 var packet=new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.RootPayload)["payload"]);var build=new NativeSfrBuild(null,"https://example.invalid",packet);
 var parser=new NativeIncrementalJson();parser.feedMode=true;parser.commonKeys=["decodedBytes","path","sha256"];parser.nodeOwner=build;parser.rootOwner=build;var ok=true;
 try{parser.begin(WatchUi.loadResource(resource)["raw"],4096);var steps=0;while(!parser.step()){steps+=1;if(steps>5000){throw new Lang.InvalidValueException("step bound");}}build.scene=parser.result;build.finishBegin();build.roleRef("rocket");}catch(e){ok=false;}parser.dispose();build.dispose();Test.assertMessage(ok==expected,"root projection refusal/acceptance");return true;
}
(:test,:typecheck(false)) function menuRootProjection(logger){
 menuRootProjectionCase(Rez.JsonData.RootValid,true);menuRootProjectionCase(Rez.JsonData.RootMaxSource,true);
 menuRootProjectionCase(Rez.JsonData.RootMissing,false);menuRootProjectionCase(Rez.JsonData.RootIdentity,false);
 menuRootProjectionCase(Rez.JsonData.RootRole,false);menuRootProjectionCase(Rez.JsonData.RootProvenance,false);
 menuRootProjectionCase(Rez.JsonData.RootDuplicate,false);menuRootProjectionCase(Rez.JsonData.RootUnknown,false);
 logger.debug("ROOT_PROJECTION valid/maxSource accepted; missing/identity/role/provenance/duplicate/unknown refused");return true;
}
(:test,:typecheck(false)) function menuHiddenResourceCycle(logger){
 var raw=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];var view=new MenuView();view.setPacket(new NativeTrustedPacket(raw));
 for(var i=0;i<3;i+=1){view.onShow();view.onUpdate(new MenuDraw());view.queueResumeAfterFrame();for(var t=0;t<view.timers.size();t+=1){(view.timers[t] as PbtTimer).fire();}view.onHide();
  Test.assert(view.renderer==null&&view.sfrTimer==null&&view.presentation.label==null&&view.presentation.dictionary==null);
  view.setSettings(new SceneSettings({"Language"=>1}));Test.assert(view.presentation.label==null&&view.presentation.dictionary==null);
  for(var j=0;j<view.timers.size();j+=1){Test.assert(view.timers[j].callback==null);}
 }
 logger.debug("HIDDEN_RESOURCE cycles=3 callbacks_released=true hidden_settings_no_reload=true");return true;
}
(:test,:typecheck(false)) function menuCompactClosure(logger){
 var packet=new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.RootPayload)["payload"]);var store=new PbtMemoryStore();var b=new NativeSfrBuild(store,"https://example.invalid",packet);
 var a="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";var c="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
 var first=b.addTuple(1,sfrCompactDigest(a),17);var again=b.addTuple(1,sfrCompactDigest(a),17);Test.assert(first==again&&b.expected.size()==1&&b.rasterBytes==17);
 var refused=false;try{b.addTuple(1,sfrCompactDigest(a),18);}catch(e){refused=true;}Test.assert(refused);refused=false;try{b.addTuple(0,sfrCompactDigest(a),17);}catch(e){refused=true;}Test.assert(refused);
 b.addTuple(1,sfrCompactDigest(c),19);b.readKind=2;b.arrayElement("/objects",0,[1,a,17],1);b.arrayElement("/objects",1,[1,c,19],1);
 refused=false;try{b.arrayElement("/objects",0,[1,c,19],1);}catch(e){refused=true;}Test.assert(refused);
 store.write("sf.obj."+a,"corrupted");refused=false;try{b.checkRaw(first);}catch(e){refused=true;}Test.assert(refused);
 b.scene={"position"=>null};b.closure();var saved=store.read("sf.raster.active");Test.assert(saved["refs"][0][1].equals(a)&&saved["refs"][1][1].equals(c));
 b.dispose();logger.debug("COMPACT_CLOSURE byte_value_dedup/conflicts/order/corrupt_ref/canonical_durable passed");return true;
}
(:test,:typecheck(false)) function menuRasterCommitFailure(logger){
 var packet=new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.RootPayload)["payload"]);var store=new MenuRasterStore();var prior={"base"=>"https://example.invalid","selectionHash"=>"old","refs"=>[[0,"old",1]]};store.write("sf.raster.active",prior);
 var b=new NativeSfrBuild(store,"https://example.invalid",packet);b.addTuple(1,sfrCompactDigest("aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),17);b.scene={"position"=>null};store.failActive=true;
 var refused=false;try{b.closure();}catch(e){refused=true;}Test.assert(refused&&!b.complete&&store.read("sf.raster.active")==prior&&store.read("sf.raster.recovery")==prior);b.dispose();
 logger.debug("RASTER_COMMIT failure retains old active/recovery and does not publish candidate");return true;
}
(:test,:typecheck(false)) function menuShardCase(resource,accepted){
 var fixture=WatchUi.loadResource(resource);var packet=new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.RootPayload)["payload"]);var b=new NativeSfrBuild(null,"https://example.invalid",packet);b.readKind=1;
 var parser=new NativeIncrementalJson();parser.feedMode=true;parser.commonKeys=["decodedBytes","path","sha256"];parser.nodeOwner=b;var ok=true;
 try{parser.begin(fixture["raw"],4096);var n=0;while(!parser.step()){n+=1;if(n>5000){throw new Lang.InvalidValueException("step bound");}}var d=b.finishRole("map",parser.result);var shards=d["shards"];Test.assert(sfrDigestText(shards[0][1]).equals(fixture["first"])&&sfrDigestText(shards[shards.size()-1][1]).equals(fixture["last"]));Test.assert(shards[0]==b.expected[0]);}catch(e){ok=false;}parser.dispose();b.dispose();Test.assert(ok==accepted);return true;
}
(:test,:typecheck(false)) function menuShardProjection(logger){menuShardCase(Rez.JsonData.ShardValid,true);menuShardCase(Rez.JsonData.ShardBadHash,false);menuShardCase(Rez.JsonData.ShardOver,false);logger.debug("SHARD_PROJECTION captured19 accepted; malformed digest and oversized input refused");return true;}
(:test,:typecheck(false)) function menuCompactPixel(logger){
 var raw="SFR1:0:1:AAECAw==";var h=new NativeWireHash();h.put(raw);var digest=h.digest();
 for(var i=0;i<2;i+=1){var store=new PbtMemoryStore();store.write("sf.obj."+digest,raw);var good="039058c6f2c0cb492c533b0a4d14ef77cc0f78abccced5287d84a1a2011cfb81";var d={"canvas"=>[1,1],"channels"=>3,"pixelSha256"=>i==0?good:"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","shards"=>[[1,sfrCompactDigest(digest),h.count]]};var accepted=true;
  try{var decoder=new NativeSfrDecoder(store,d);var n=0;while(!decoder.step()){n+=1;if(n>10){throw new Lang.InvalidValueException("step bound");}}}catch(e){accepted=false;}Test.assert(accepted==(i==0));
 }
 logger.debug("COMPACT_PIXEL valid accepted; wrong pixel hash refused");return true;
}
(:test,:typecheck(false)) function menuAffectedBatch(logger){
 Test.assert(menuDeferredDecodeKeepsComposition(logger));
 Test.assert(menuRetainedAndReplacedVisual(logger));
 Test.assert(menuOptionalDrawFaults(logger));
 Test.assert(menuRootProjection(logger));
 Test.assert(menuHiddenResourceCycle(logger));
 Test.assert(menuCompactClosure(logger));
 Test.assert(menuRasterCommitFailure(logger));
 Test.assert(menuShardProjection(logger));
 Test.assert(menuCompactPixel(logger));
 Test.assert(menuGeneratedComposition(logger));
 Test.assert(customFieldMissingIconKeepsSlotMarker(logger));
 Test.assert(menuSameAndChangedSource(logger));
 Test.assert(menuFontPreflightRecovery(logger));
 Test.assert(menuOptionalPreflight(logger));
 Test.assert(menuLowPointAfterMapFailure(logger));
 Test.assert(menuCanonicalFontIdentityAfterReturn(logger));
 logger.debug("MENU_AFFECTED directed=15 generated=1");return true;
}

(:test,:typecheck(false)) function menuMandatoryPaintRecovery(logger){
 var view=new MenuView();
 view.setPacket(new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"]));
 view.values={"steps"=>10115,"energy"=>75,"heart"=>60,"stress"=>30};view.onShow();
 var dc=new MenuDraw();MenuObserve.failMandatory=true;menuReset();view.onUpdate(dc);
 Test.assert(dc.clears>=2&&!dc.recoveryClock&&view.renderer==null);
 Test.assertMessage(dc.icons==0&&dc.metricTexts==0,"mandatory recovery must clear partial paint and omit orphan values");
 Test.assert(view.context.launchId.equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60")&&view.displayMode()==view.NOT_LOW);
 var healthy=new MenuDraw();menuReset();view.onUpdate(healthy);
 logger.debug("healthy rebind time="+MenuObserve.time+" icons="+MenuObserve.icons.size()+" values="+MenuObserve.values+" metric_draw_calls="+healthy.metricTexts);
 Test.assert(MenuObserve.time&&MenuObserve.icons.size()==4&&MenuObserve.values==4&&healthy.metricTexts>0);
 view.onHide();logger.debug("mandatory paint failure clears partial frame; healthy canonical rebind");return true;
}
(:test,:typecheck(false)) function menuPeerControls(logger){
 Test.assert(menuMandatoryPaintRecovery(logger));return true;
}

(:test,:typecheck(false)) class MenuCadenceClock extends WatchClock {var now=1795042100;function utcSeconds(){return now;}function localTimeText(){return "08:25";}function localCalendar(){return [3,17,11];}}
(:test,:typecheck(false)) class MenuCadenceView extends MenuView {var clock;function initialize(){clock=new MenuCadenceClock();SpaceFoxView.initialize(clock,new ScheduleState(null,"empty"));timers=[];}}
(:test,:typecheck(false)) function menuCadenceFrames(logger){
 var raw=WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"];Test.assertEqual(raw[3][20],1795042200);var v=new MenuCadenceView();v.setPacket(new NativeTrustedPacket(raw));v.values={"steps"=>10115,"energy"=>75,"heart"=>60,"stress"=>30};var dc=new MenuDraw();v.onShow();v.onLayout(dc);
 var expected=["T- 00:01:40","T- 00:01:39","T- 00:01:29"];for(var i=0;i<3;i+=1){if(i==1){v.clock.now+=1;}if(i==2){v.onHide();v.clock.now+=10;v.onShow();v.onLayout(dc);}menuReset();v.onUpdate(dc);Test.assertMessage(MenuObserve.countdown.equals(expected[i]),"UTC countdown at actual ACTIVE paint");Test.assert(MenuObserve.time&&MenuObserve.icons.size()==4&&MenuObserve.values==4);var roles=["steps","energy","heart","stress"];for(var j=0;j<4;j+=1){Test.assert(MenuObserve.icons[j][0].equals(roles[j]));}}
 v.onHide();logger.debug("MENU_CADENCE actual_renderer=3 frames countdown_and_four_positions=true");return true;
}

(:test,:typecheck(false)) function customFieldMissingIconKeepsSlotMarker(logger){
 var owner=new LocalePresentation();var renderer=new SceneRenderer(owner);var dc=new MenuDraw();
 renderer.drawProviderIcon(dc,null,55,244,0xFFFFFF,"custom1");renderer.drawProviderIcon(dc,false,207,244,0xFFFFFF,"custom2");
 var ids=[1,2,3,18,22,23,4];var expected=["battery","steps","calories","heart","stress","energy",null];
 for(var i=0;i<ids.size();i+=1){var role=FieldCatalog.bundledIconRole(new Toybox.Complications.Id(ids[i]));if(expected[i]==null){Test.assert(role==null);}else{Test.assert(role.equals(expected[i]));}}
 Test.assertMessage(dc.markers==2,"missing or released provider graphics retain visible slot markers");
 logger.debug("custom icon missing/released: two markers");return true;
}

(:test,:typecheck(false)) function menuSameAndChangedSource(logger){
 var view=new MenuView();var fields=new PbtSelectedFields();view.selectedFields=fields;view.fitness.selectedFields=fields;
 var settings=new SceneSettings({"Field1"=>6,"Field2"=>6,"Field3"=>6,"Field4"=>6});
 view.setSettings(settings);fields.fakeApi.values=[11,22,33,44];fields.start(settings.slots,fields.method(:callback));fields.read("en");
 Test.assert(fields.display("custom1").equals("11")&&fields.label("custom1").equals("src"));
 var renderer=new SceneRenderer(new LocalePresentation());renderer.selectedFields=fields;renderer.prepare(null,settings);
 Test.assertMessage(renderer.iconRoles["custom1"].equals("steps"),"current source supplies the matching bundled identity");
 view.setSettings(new SceneSettings({"Field1"=>6,"Field2"=>6,"Field3"=>6,"Field4"=>6}));
 Test.assertMessage(fields.display("custom1").equals("11")&&fields.label("custom1").equals("src"),"unchanged source retains its own prior snapshot");
 fields.fakeApi.kinds=[1,3,6,7];view.setSettings(new SceneSettings({"Field1"=>6,"Field2"=>6,"Field3"=>6,"Field4"=>6}));
 Test.assertMessage(fields.display("custom1").equals("—")&&fields.label("custom1").equals(""),"changed source invalidates old value and identity before paint");
 renderer.prepare(null,settings);Test.assertMessage(renderer.iconRoles["custom1"].equals("battery"),"changed source replaces old icon");
 logger.debug("MENU_SOURCES unchanged retained; changed ID cleared");return true;
}
(:test,:typecheck(false)) class MenuFailFont extends LocalePresentation {
 var failFont=false;
 function vectorFont(faces,size){if(failFont){throw new Lang.InvalidValueException("injected mandatory font failure");}return LocalePresentation.vectorFont(faces,size);}
}
(:test,:typecheck(false)) class MenuPreflightView extends MenuView {
 function initialize(){MenuView.initialize();}
 function createPresentation() as LocalePresentation {return new MenuFailFont();}
}
(:test,:typecheck(false)) function menuFontPreflightRecovery(logger){
 var view=new MenuPreflightView();view.setPacket(new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"]));view.onShow();
 var p=view.presentation as MenuFailFont;p.suspend();p.failFont=true;var before=new MenuDraw();menuReset();view.onUpdate(before);
 Test.assertMessage(before.clears==0&&view.renderer==null,"font preflight failure leaves previous frame untouched");
 p.failFont=false;var after=new MenuDraw();menuReset();view.onUpdate(after);
 Test.assertMessage(MenuObserve.time&&MenuObserve.icons.size()==4&&MenuObserve.values==4,"font recovery paints canonical frame");
 view.onHide();logger.debug("FONT_PREFLIGHT no paint on failure; canonical frame after retry");return true;
}

(:test,:typecheck(false)) function menuOptionalPreflight(logger){
 var view=new MenuView();view.onShow();MenuObserve.failOptionalLoad=true;var dc=new MenuDraw();menuReset();view.onUpdate(dc);MenuObserve.failOptionalLoad=false;
 Test.assertMessage(MenuObserve.time&&MenuObserve.icons.size()==4&&MenuObserve.values==4,"missing optional resources must preserve canonical ACTIVE frame");view.onHide();return true;
}
(:test,:typecheck(false)) function menuLowPointAfterMapFailure(logger){
 var p=new LocalePresentation();p.prepareAodFonts();var settings=new SceneSettings(null);var clock=new ClockSnapshot("08:25","T- 00:10");clock.localCalendar=[3,17,11];var map=WatchUi.loadResource(Rez.Drawables.AodMap0);var font=WatchUi.loadResource(Rez.Fonts.Aod40);
 for(var phase=0;phase<4;phase+=1){var dc=new MenuDraw();dc.failLowMap=true;SceneAod.draw(dc,clock,phase,p,font,settings,map,true,335,165,[-120.61,34.63]);Test.assertMessage(dc.pointMarks==1,"fallback world draws qualified point after map draw fault");}
 logger.debug("LOW_MAP_FAULT point retained on four phases; graphics-call observer");return true;
}

// Production renderer is used; this subclass only records the calls that reach
// the four selected source slots, including their actual font and placement.
(:test,:typecheck(false)) class CatalogFrameRenderer extends SceneRenderer {
 var slotCalls=[];var valueCalls=[];var expectedValue="";
 function initialize(owner){SceneRenderer.initialize(owner);}
 function drawProviderIcon(dc,icon,left,top,color,role){slotCalls.add([role,left,top]);SceneRenderer.drawProviderIcon(dc,icon,left,top,color,role);}
 function text(dc,x,y,font,value,color,width,contour){var result=SceneRenderer.text(dc,x,y,font,value,color,width,contour);if(value.equals(expectedValue)){valueCalls.add([x,y,font,result]);}return result;}
}
(:typecheck(false)) function catalogFrame(fields){
 var settings=new SceneSettings({"Field1"=>6,"Field2"=>6,"Field3"=>6,"Field4"=>6});var fit=new Fitness();fit.selectedFields=fields;
 var renderer=new CatalogFrameRenderer(new LocalePresentation());renderer.selectedFields=fields;renderer.prepare(null,settings);return [renderer,settings,fit,new MenuDraw()];
}
(:typecheck(false)) function verifyCatalogFrame(frame,expected,logger){
 var renderer=frame[0];renderer.slotCalls=[];renderer.valueCalls=[];renderer.expectedValue=expected;
 renderer.active(frame[3],new ClockSnapshot("08:25","T- 00:10:00"),frame[1],{},frame[2],0.0);
 Test.assertMessage(renderer.slotCalls.size()==4&&renderer.valueCalls.size()==4,"each selected source reaches the actual renderer");
 var numeric=["0","0%","—","101","102","103","2","111","112","15","20","3","50%"].indexOf(expected)>=0;
 for(var i=0;i<4;i+=1){var slot=renderer.slotCalls[i];var value=renderer.valueCalls[i];Test.assert(slot[0].equals("custom"+(i+1))&&slot[1]==(i%2==0?55:207)&&slot[2]==(i<2?244:282));Test.assert(value[0]==(i%2==0?135:287));Test.assert(value[1]==(i<2?(numeric?240:250):(numeric?278:288)));Test.assert(value[2]==renderer.fonts[numeric?"metric":"small"]);}
}

(:test,:typecheck(false)) function menuCanonicalFontIdentityAfterReturn(logger){
 var view=new MenuView();view.setPacket(new NativeTrustedPacket(WatchUi.loadResource(Rez.JsonData.CountdownCaptured)["payload"]));view.values={"steps"=>10115,"energy"=>75,"heart"=>60,"stress"=>30};view.onShow();
 var a=new MenuDraw();menuReset();view.onUpdate(a);var before=MenuObserve.icons;var beforeFonts=MenuObserve.metricFonts;var beforeResources=MenuObserve.resources;
 Test.assertMessage(MenuObserve.time&&before.size()==4&&beforeFonts.size()==4,"first ACTIVE has complete identity and native fonts");
 view.onHide();view.onShow();var b=new MenuDraw();menuReset();view.onUpdate(b);Test.assert(MenuObserve.time&&MenuObserve.icons.size()==4&&MenuObserve.metricFonts.size()==4);
 Test.assert(beforeResources.indexOf(Rez.Fonts.Time80)>=0&&beforeResources.indexOf(Rez.Fonts.Metric32)>=0&&MenuObserve.resources.indexOf(Rez.Fonts.Time80)>=0&&MenuObserve.resources.indexOf(Rez.Fonts.Metric32)>=0);
 var current=view.renderer as SceneRenderer;Test.assert(MenuObserve.clockFont==current.fonts["time"]);
 for(var i=0;i<4;i+=1){Test.assert(before[i][0].equals(MenuObserve.icons[i][0])&&before[i][1]==MenuObserve.icons[i][1]&&before[i][2]==MenuObserve.icons[i][2]);Test.assert(MenuObserve.metricFonts[i]==current.fonts["metric"]);}
 Test.assertMessage(!b.recoveryClock&&MenuObserve.icons.size()==4,"historical thin/no-icon fingerprint is not the normal resumed frame");view.onHide();logger.debug("MENU_CANONICAL identical four icon placements, Time80, Metric32 across hide/show");return true;
}

(:test,:typecheck(false)) class CatalogLifecycleView extends MenuView {
 var expectedText="—";function initialize(){MenuView.initialize();}
 function createSceneRenderer() as SceneRenderer {var r=new CatalogFrameRenderer(presentation);r.expectedValue=expectedText;return r;}
 function refreshFitnessWork() as Void {readFitnessSnapshot(1794818604l);}
}
(:typecheck(false)) function catalogViewPaint(v,expected){
 v.expectedText=expected;if(v.renderer!=null){var prior=v.renderer as CatalogFrameRenderer;prior.expectedValue=expected;prior.slotCalls=[];prior.valueCalls=[];}
 var dc=new MenuDraw();v.onUpdate(dc);var r=v.renderer as CatalogFrameRenderer;
 Test.assertMessage(r!=null&&r.slotCalls.size()==4&&r.valueCalls.size()==4,"actual view produced four selected values and identities");
 var numeric=["0","0%","—","101","102","103","2","111","112","15","20","3","50%"].indexOf(expected)>=0;
 for(var i=0;i<4;i+=1){Test.assert(r.slotCalls[i][0].equals("custom"+(i+1)));Test.assert(r.slotCalls[i][1]==(i%2==0?55:207)&&r.slotCalls[i][2]==(i<2?244:282));Test.assert(r.valueCalls[i][2]==r.fonts[numeric?"metric":"small"]);}
}
(:test,:typecheck(false)) function generatedCatalogViewLifecycle(logger){
 var checks=0;for(var kind=1;kind<=42;kind+=1){
  var v=new CatalogLifecycleView();var fields=new PbtSelectedFields();fields.fakeApi.kinds=[kind,kind,kind,kind];var raw=(kind==6||kind==7||kind==12||kind==26||kind==39||kind==41)?"sample":0;fields.fakeApi.values=[raw,raw,raw,raw];
  v.selectedFields=fields;v.fitness.selectedFields=fields;var settings=new SceneSettings({"Field1"=>6,"Field2"=>6,"Field3"=>6,"Field4"=>6});v.setSettings(settings);v.onShow();catalogViewPaint(v,"—");
  Test.assert(v.timers.size()>0&&v.timers[v.timers.size()-1].fire());
  var expected=raw instanceof String?"sample":"0";if(kind>=8&&kind<=11){expected="Clear";}else if(kind==13||kind==14){expected="00:00";}else if(kind==21){expected="0 min";}else if(kind==16){expected="0.0 hPa";}else if(kind==1||kind==35||kind==37){expected="0%";}else if(kind==38){expected="0.0°C";}else if(kind==15){expected="0.0 m";}else if(kind==19||kind==20){expected="0.0 km";}else if(kind>=31&&kind<=34){expected="0.0 km/h";}else if(kind>=27&&kind<=30){expected="0:00";}
  catalogViewPaint(v,expected);v.onHide();var hiddenDc=new MenuDraw();v.onUpdate(hiddenDc);Test.assert(hiddenDc.clears==0);
  v.onShow();catalogViewPaint(v,expected);Test.assert(v.timers[v.timers.size()-1].fire());fields.fakeApi.values=[null,null,null,null];v.fieldsChanged(new Toybox.Complications.Id(kind));catalogViewPaint(v,"—");
  v.onHide();checks+=1;
 }
 logger.debug("CATALOG_VIEW kinds="+checks+" slots=4 actual_view=true hide_reopen_callback=true controlled=true");return true;
}

(:test,:typecheck(false)) function generatedLocalViewLifecycle(logger){
 var keys=["distance","stepGoal","floorsClimbedGoal","floorsDescended","metersClimbed","metersDescended","moveBarLevel","activeMinutesWeekGoal","activeMinutesDayTotal","activeMinutesDayModerate","activeMinutesDayVigorous","activeMinutesWeekTotal","activeMinutesWeekModerate","activeMinutesWeekVigorous","pushes","pushGoal","pushDistance","timeToRecovery","respirationRate","stressScore","floorsClimbed","system:batteryInDays","system:charging","system:solarIntensity"];
 var expected=["1.0 km","101","102","103","104.0 m","105.0 m","2","110 min","10 min","6 min","4 min","10 min","6 min","4 min","111","112","1.0 km","5 h","15","20","3","2.0 d","Connected","50%"];
 for(var k=0;k<keys.size();k+=1){var v=new CatalogLifecycleView();var fields=new PbtLocalFields();fields.source=keys[k];v.selectedFields=fields;v.fitness.selectedFields=fields;
  var s=new SceneSettings({"Field1"=>6,"Field2"=>6,"Field3"=>6,"Field4"=>6});v.setSettings(s);v.onShow();catalogViewPaint(v,"—");Test.assert(v.timers[v.timers.size()-1].fire());catalogViewPaint(v,expected[k]);
  v.onHide();var hiddenDc=new MenuDraw();v.onUpdate(hiddenDc);Test.assert(hiddenDc.clears==0);v.onShow();catalogViewPaint(v,expected[k]);
  fields.source=keys[(k+1)%keys.size()];v.setSettings(s);catalogViewPaint(v,"—");v.onHide();
 }
 logger.debug("LOCAL_VIEW keys="+keys.size()+" slots=4 actual_view=true reopen_and_changed_id=true controlled=true");return true;
}

(:test,:typecheck(false)) function generatedBuiltinSlotMatrix(logger){
 var names=["steps","energy","heart","stress","calories","battery"];var checks=0;
 for(var role=0;role<names.size();role+=1){for(var slot=0;slot<4;slot+=1){
  var v=new MenuView();var settings={"Field1"=>0,"Field2"=>1,"Field3"=>2,"Field4"=>3};settings["Field"+(slot+1)]=role;v.setSettings(new SceneSettings(settings));v.values={"steps"=>10,"energy"=>20,"heart"=>30,"stress"=>40,"calories"=>50,"battery"=>60};v.onShow();menuReset();v.onUpdate(new MenuDraw());
  Test.assertMessage(MenuObserve.time&&MenuObserve.icons.size()==4&&MenuObserve.values==4,"canonical frame must contain four preset slots");Test.assert(MenuObserve.icons[slot][0].equals(names[role]));Test.assert(MenuObserve.icons[slot][2]==(slot<2?244:282)+(names[role].equals("battery")?2:5));v.onHide();checks+=1;
 }}logger.debug("BUILTIN_MATRIX roles=6 slots=4 view_frames="+checks+" controlled=true");return true;
}
