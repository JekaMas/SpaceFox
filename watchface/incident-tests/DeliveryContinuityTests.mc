import Toybox.Background;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
import Toybox.Time;
import Toybox.WatchUi;
import Toybox.Test;

(:test,:typecheck(false)) function deliveryModeCallbacksAreIdempotent(logger){
 var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
 var modes=[System.DISPLAY_MODE_HIGH_POWER,System.DISPLAY_MODE_HIGH_POWER,System.DISPLAY_MODE_LOW_POWER,System.DISPLAY_MODE_LOW_POWER,System.DISPLAY_MODE_OFF,System.DISPLAY_MODE_HIGH_POWER];
 var expected=[view.NOT_LOW,view.NOT_LOW,view.LOW,view.LOW,view.LOW,view.NOT_LOW];
 for(var i=0;i<modes.size();i+=1){view.syncDisplayMode(modes[i]);Test.assert(view.displayMode()==expected[i]);}
 view.onEnterSleep();Test.assert(view.displayMode()==view.LOW);logger.debug("MODE highLowOff normalized; duplicate callbacks stable");return true;
}

// Isolated view boundary only. A separate live-feed run establishes that the
// selected visual was acquired by the same native application before rejection.
(:test,:typecheck(false)) function deliveryRejectedResponseRetainsScene(logger){
    var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
    var scene=new SceneContext({"id"=>"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a","rocket"=>"Vulcan VC6L","site"=>"US · Cape Canaveral SFS","target"=>1794762690l,"precision"=>"exact"});
    view.setContext(scene);view.prepareRenderer();
    var visual=new NativeSfrRenderer();view.downloaded=visual;view.renderer.downloaded=visual;
    view.clearForRestore();
    Test.assert(view.context==scene);
    Test.assert(view.downloaded==visual);
    Test.assert(view.renderer!=null&&view.renderer.downloaded==visual);
    logger.debug("REJECTED_RESPONSE retainedAcceptedScene=true");return true;
}

(:test,:typecheck(false)) function deliveryPendingDeadlineDoesNotMove(logger){
    // Expected deadlines are stated from the event history, not read back from
    // the production helper. The OS minimum may delay an impossible event.
    var last=1000l;var deadline=pendingWake(1000l,4600l,null,last,true);
    Test.assert(deadline==1300l);
    deadline=pendingWake(1100l,4700l,deadline,last,true);
    Test.assert(deadline==1300l);
    deadline=pendingWake(1200l,4800l,deadline,last,true);
    Test.assert(deadline==1300l);
    Test.assert(pendingWake(1200l,4800l,1100l,800l,true)==1200l);
    Test.assert(pendingWake(1300l,4900l,1300l,1300l,true)==1600l);
    Test.assert(pendingWake(1200l,1250l,1300l,1000l,false)==1300l);
    Test.assert(!registrationNeeded(1200l,1300l,1300l,1000l,true));
    Test.assert(!registrationNeeded(1301l,1301l,1300l,1000l,true));
    Test.assert(!registrationNeeded(1361l,1361l,1300l,1000l,true));
    Test.assert(registrationNeeded(1301l,1600l,1300l,1300l,true));
    Test.assert(registrationNeeded(1200l,1300l,1100l,1000l,true));
    logger.debug("PENDING_DEADLINE first=1300 wake=1300 reload=1300 osMinimum=1600");return true;
}

(:test,:typecheck(false)) function deliverySceneEventsAndLateCompletion(logger){
 var job=new SceneLifecycle();job.replace();Test.assert(job.request(1));Test.assert(!job.request(1));var old=job.begin();job.cancel();Test.assert(!job.complete(old));Test.assert(job.request(2));var current=job.begin();Test.assert(job.complete(current));job.replace();Test.assert(!job.complete(current));logger.debug("JOB duplicate blocked; cancelled and old completion rejected; current applied");return true;
}

(:typecheck(false)) class DeliveryKeyPacket {
    var bridge;var generation;var target;
    function initialize(model,site,position,mode,selection,generationValue,targetValue){
        bridge={"selection"=>{"sha256"=>selection},
            "ids"=>["ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a",model,"ll2:organization:124",site,"ll2:country:2"],
            "site"=>{"position"=>position,"positionMode"=>mode}};
        generation=generationValue;target=targetValue;
    }
}

(:test,:typecheck(false)) function deliveryVisualIdentityCases(logger){
    var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
    var selection="77d4b3173b019ee84b7eb751e81ccb7a47edfba560a54166bfb47f441e8b7b37";
    var position={"longitude"=>"-80.58303644","latitude"=>"28.58341025","qualification"=>"unverified-reference"};
    var original=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",position,"fixed-source",selection,24,1794762690l);
    var key=view.packetVisualKey(original);
    // Validation generation and T0 can advance without changing the visual.
    var update=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",position,"fixed-source",selection,25,1794762750l);
    Test.assert(nativeSame(key,view.packetVisualKey(update)));
    var changedModel=new DeliveryKeyPacket("ll2:configuration:99","ll2:site:29",position,"fixed-source",selection,25,1794762750l);
    var changedSite=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:30",position,"fixed-source",selection,25,1794762750l);
    var changedPoint=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",{"longitude"=>"-80.5","latitude"=>"28.58341025","qualification"=>"unverified-reference"},"fixed-source",selection,25,1794762750l);
    var changedQualification=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",{"longitude"=>"-80.58303644","latitude"=>"28.58341025","qualification"=>"different"},"fixed-source",selection,25,1794762750l);
    var changedMode=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",position,"mobile-reference-no-event",selection,25,1794762750l);
    var changedArt=new DeliveryKeyPacket("ll2:configuration:479","ll2:site:29",position,"fixed-source","aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",25,1794762750l);
    Test.assert(!nativeSame(key,view.packetVisualKey(changedModel)));
    Test.assert(!nativeSame(key,view.packetVisualKey(changedSite)));
    Test.assert(!nativeSame(key,view.packetVisualKey(changedPoint)));
    Test.assert(!nativeSame(key,view.packetVisualKey(changedQualification)));
    Test.assert(!nativeSame(key,view.packetVisualKey(changedMode)));
    Test.assert(!nativeSame(key,view.packetVisualKey(changedArt)));
    logger.debug("VISUAL_KEY sameT0AndGeneration=true modelSitePointQualificationArtChangesDistinct=true");return true;
}

(:typecheck(false)) class DeliveryScheduleStore {
    var data={};var unavailable=null;var failWrite=null;
    function read(key){
        if(key.equals(unavailable)||!data.hasKey(key)){return null;}
        var value=data[key];
        if(key.equals("sf.batch.head")&&value instanceof Dictionary){return {"base"=>value["base"],"pending"=>value["pending"],"catalogDigest"=>value["catalogDigest"],"transfer"=>value["transfer"],"serial"=>value["serial"]};}
        return value;
    }
    function write(key,value){
        if(key.equals(failWrite)){throw new Lang.InvalidValueException("injected write failure");}
        data[key]=key.equals("sf.batch.head")?{"base"=>value["base"],"pending"=>value["pending"],"catalogDigest"=>value["catalogDigest"],"transfer"=>value["transfer"],"serial"=>value["serial"]}:value;
    }
    function remove(key){data.remove(key);}
}

(:test,:typecheck(false)) function deliveryVisualWaitsForMatchingBatch(logger){
    var store=new DeliveryScheduleStore();var base="https://example.test";
    var catalog="{}";var index="{\"objects\":[]}";
    var h=new NativeWireHash();h.put(catalog);var catalogHash=h.digest();
    h=new NativeWireHash();h.put(index);var indexHash=h.digest();
    var bridge={"catalogDigest"=>catalogHash,"transfer"=>{"sha256"=>indexHash,"path"=>"descriptors/"+indexHash+".json","decodedBytes"=>index.length()}};
    var batch=new NativeBatch(store,base);batch.select(bridge);
    var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));
    view.setContext(new SceneContext({"id"=>"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"}));
    var source=new NativeRenderSource(store,base,bridge);view.setAssetCache(source);
    Test.assert(!source.ready&&view.sceneLifecycle.job==null);
    // A decode failure is not retried merely because the same batch was seen.
    Test.assert(view.sceneLifecycle.request(0));var token=view.sceneLifecycle.begin();view.sceneLifecycle.fail(token);
    view.setAssetCache(new NativeRenderSource(store,base,bridge));Test.assert(view.sceneLifecycle.job!=null&&view.sceneLifecycle.job.state==view.sceneLifecycle.job.FAILED);
    var ref=batch.next();Test.assert(batch.immutable.put(ref,catalog));
    ref=batch.next();Test.assert(batch.immutable.put(ref,index));Test.assert(batch.next()==null);
    source=new NativeRenderSource(store,base,bridge);view.setAssetCache(source);Test.assert(source.ready&&view.sceneLifecycle.job==null);
    Test.assert(!new NativeRenderSource(store,base,{"catalogDigest"=>"other","transfer"=>bridge["transfer"]}).ready);
    Test.assert(!new NativeRenderSource(store,base,{"catalogDigest"=>catalogHash,"transfer"=>{"sha256"=>"other"}}).ready);
    Test.assert(view.sceneLifecycle.request(source.serial));token=view.sceneLifecycle.begin();view.sceneLifecycle.fail(token);
    view.setAssetCache(new NativeRenderSource(store,base,bridge));Test.assert(view.sceneLifecycle.job!=null&&view.sceneLifecycle.job.state==view.sceneLifecycle.job.FAILED);
    // A dependency becomes unavailable and is then repaired. The production
    // batch transitions through pending and emits a new completion serial.
    store.unavailable="sf.obj."+indexHash;store.failWrite="sf.batch.head";
    var failed=false;try{batch.next();}catch(e){failed=true;}
    Test.assert(failed&&!new NativeRenderSource(store,base,bridge).ready);
    store.failWrite=null;store.unavailable=null;batch=new NativeBatch(store,base);Test.assert(batch.next()==null);
    view.setAssetCache(new NativeRenderSource(store,base,bridge));Test.assert(view.sceneLifecycle.job==null);
    Test.assert(!new NativeRenderSource(store,"https://other.test",bridge).ready);
    var partial=new DeliveryScheduleStore();partial.failWrite="sf.batch.pending";
    var selection=new NativeBatch(partial,base);failed=false;
    try{selection.select(bridge);}catch(e){failed=true;}
    Test.assert(failed&&batchPending(new NativeTransfer(base,partial)));
    logger.debug("VISUAL_BATCH pendingAndWrongIdentityRejected=true completedMatchingBatchApplied=true");return true;
}

(:test,:typecheck(false)) function deliveryRealRegisteredDeadline(logger){
    var now=Time.now().value().toLong();var store=new DeliveryScheduleStore();
    var transfer=new NativeTransfer("https://jekamas.github.io/SpaceFox",store);
    store.write("sf.transfer.ready",{"base"=>transfer.base,"accepted"=>true});
    store.write("sf.batch.pending",{"base"=>transfer.base,"pending"=>true});
    transfer.attempted(now);
    var due=now+300;
    try{
        Background.registerForTemporalEvent(new Time.Moment(due.toNumber()));
        Test.assert(Background.getTemporalEventRegisteredTime().value().toLong()==due);
        armFeed(transfer,now+60);
        Test.assert(Background.getTemporalEventRegisteredTime().value().toLong()==due);
        armFeed(transfer,now+120);
        Test.assert(Background.getTemporalEventRegisteredTime().value().toLong()==due);
        logger.debug("REGISTERED_DEADLINE preserved=true wakeAndReload=true");
    }finally{Background.deleteTemporalEvent();}
    return true;
}

(:typecheck(false)) class DeliveryAdmissionCache {
    var store;var packet;
    function initialize(adapter){store=adapter;packet=true;}
}

(:test,:typecheck(false)) function deliveryDuplicateCallbackDoesNotInvalidateBuild(logger){
    var store=new DeliveryScheduleStore();var cache=new DeliveryAdmissionCache(store);
    var incoming=new NativeIncoming(store,"https://jekamas.github.io/SpaceFox");
    var machine=new SceneLifecycle();machine.replace();
    Test.assert(machine.request(1));var token=machine.begin();Test.assert(token!=null);
    // No response, then a response already processed: both reach the production
    // decision seam and leave the in-progress generation unchanged.
    Test.assert(!NativeForegroundApp.hasNewIncoming(cache,incoming));
    Test.assert(machine.pending());
    var marker={"sha256"=>"same","sequence"=>1};store.write("sf.incoming.feed",marker);
    store.write("sf.incoming.feed.processed",incoming.token(marker));
    Test.assert(!NativeForegroundApp.hasNewIncoming(cache,incoming));
    Test.assert(machine.pending()&&machine.generation==token);
    store.write("sf.incoming.feed",{"sha256"=>"new","sequence"=>2});
    Test.assert(NativeForegroundApp.hasNewIncoming(cache,incoming));
    machine.cancel();Test.assert(!machine.complete(token));Test.assert(machine.job==null);
    logger.debug("CALLBACKS duplicateNoMutation=2 newCandidateApplied=1 staleCompletionRejected=1");return true;
}

// Counts actual immutable reads requested by the production batch scanner.
(:typecheck(false)) class DeliveryCountedImmutable {
    var actual;var counts={};
    function initialize(store){actual=new NativeImmutable(store);}
    function raw(ref){var key=ref["sha256"];counts[key]=counts.hasKey(key)?counts[key]+1:1;return actual.raw(ref);}
    function put(ref,value){return actual.put(ref,value);}
    function count(key){return counts.hasKey(key)?counts[key]:0;}
}
(:test,:typecheck(false)) function deliveryBatchPrefixLifetime(logger){
    var store=new DeliveryScheduleStore();var base="https://batch.test";var catalog="{}";
    var h=new NativeWireHash();h.put(catalog);var catalogHash=h.digest();
    var values=["one","two","three"];var refs=[];var rows=[];
    for(var i=0;i<values.size();i+=1){h=new NativeWireHash();h.put(values[i]);var digest=h.digest();refs.add({"path"=>"rasters/"+digest+".sfr","sha256"=>digest,"decodedBytes"=>values[i].length()});rows.add("[1,\""+digest+"\","+values[i].length()+"]");}
    var index="{\"objects\":["+rows[0]+","+rows[1]+","+rows[2]+"]}";h=new NativeWireHash();h.put(index);var indexHash=h.digest();
    var bridge={"catalogDigest"=>catalogHash,"transfer"=>{"path"=>"descriptors/"+indexHash+".json","sha256"=>indexHash,"decodedBytes"=>index.length()}};
    var b=new NativeBatch(store,base);b.select(bridge);var counted=new DeliveryCountedImmutable(store);b.immutable=counted;
    Test.assert(counted.put({"sha256"=>catalogHash,"decodedBytes"=>null},catalog));Test.assert(counted.put(bridge["transfer"],index));
    for(var i=0;i<3;i+=1){var requested=b.next();Test.assert(requested["sha256"].equals(refs[i]["sha256"]));Test.assert(counted.put(requested,values[i]));}
    Test.assert(b.next()==null);
    // Each missing object is checked once before and once after receipt. Earlier
    // verified objects must not be rehashed on every later receipt.
    for(var i=0;i<3;i+=1){Test.assert(counted.count(refs[i]["sha256"])==2);}
    // A completed scan is not permanent trust: corruption and a new event both
    // cause the matching object to be requested again.
    store.data["sf.obj."+refs[1]["sha256"]]="corrupt";var missing=b.next();Test.assert(missing["sha256"].equals(refs[1]["sha256"]));
    Test.assert(counted.put(missing,values[1]));Test.assert(b.next()==null);
    store.data["sf.obj."+refs[0]["sha256"]]="corrupt";var restarted=new NativeBatch(store,base);missing=restarted.next();Test.assert(missing["sha256"].equals(refs[0]["sha256"]));
    logger.debug("BATCH_PREFIX perObjectChecks=2 completionCorruptionAndRestartDetected=true");return true;
}

(:test,:typecheck(false)) function deliveryOwnerStopReleasesCycle(logger){
    var app=new SpaceFoxApp();var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));app.view=view;view.pendingLoader=app.method(:reloadFeed);
    view.onHide();Test.assert(view.pendingLoader!=null&&app.view==view);
    view.releaseForSettings();Test.assert(view.pendingLoader!=null&&app.view==view);
    app.onStop(null);Test.assert(view.pendingLoader==null&&app.view==null&&app.feed==null&&app.restoreTimer==null);
    Test.assert(view.sfrTimer==null&&view.fitnessTimer==null);app.onStop(null);
    logger.debug("OWNER_STOP hideSettingsRetainCallback=true stopClearsOwnerAndTimers=true");return true;
}

(:test,:typecheck(false)) function deliveryPackedMapIdentity(logger){
    // Original source literal values are the independent oracle; no regenerated
    // metadata is used to construct expected coordinates or resource IDs.
    var expected=[[-80.5657,28.4458,Rez.Drawables.MapView0],[130.9702486,30.3993934,Rez.Drawables.MapView1],[46.295814,48.569551,Rez.Drawables.MapView2],[63.310212,45.962121,Rez.Drawables.MapView3],[-106.9750602,32.9901856,Rez.Drawables.MapView4],[143.441389,42.5,Rez.Drawables.MapView5],[167.743,9.047861,Rez.Drawables.MapView6],[128.333932,51.884395,Rez.Drawables.MapView7],[-120.6262,34.5815,Rez.Drawables.MapView8],[111.58024,38.868222,Rez.Drawables.MapView9],[-152.353077,57.430673,Rez.Drawables.MapView10],[55.333939,36.200595,Rez.Drawables.MapView11],[-52.7758051,5.2222222,Rez.Drawables.MapView12],[40.7844727,62.9063889,Rez.Drawables.MapView13],[127.997806,51.7,Rez.Drawables.MapView14],[62.984806,46.051,Rez.Drawables.MapView15],[63.650806,45.943,Rez.Drawables.MapView16],[-3.0669721,30.7787318,Rez.Drawables.MapView17],[100.313229,41.306143,Rez.Drawables.MapView18],[-44.369984,-2.3177,Rez.Drawables.MapView19],[100.199634,40.855242,Rez.Drawables.MapView20],[40.210306,-2.9383333,Rez.Drawables.MapView21],[102.032944,28.242774,Rez.Drawables.MapView22],[40.526806,62.941,Rez.Drawables.MapView23],[110.951011,19.614334,Rez.Drawables.MapView24],[-75.4594162,37.9386111,Rez.Drawables.MapView25],[136.5300282,-30.9552778,Rez.Drawables.MapView26],[59.8400282,51.0938889,Rez.Drawables.MapView27],[129.665895,40.855799,Rez.Drawables.MapView28],[177.864469,-39.262833,Rez.Drawables.MapView29],[-97.154423,25.9962,Rez.Drawables.MapView30],[127.535069,34.431867,Rez.Drawables.MapView31],[-106.321944,32.416944,Rez.Drawables.MapView32],[135.630035,-34.937822,Rez.Drawables.MapView33],[-4.402414,58.022058,Rez.Drawables.MapView34],[136.7903215,-12.3892948,Rez.Drawables.MapView35],[-0.774196,60.8187,Rez.Drawables.MapView36],[-6.73863,37.09687,Rez.Drawables.MapView37],[124.736639,39.652861,Rez.Drawables.MapView38],[121.235103,36.676794,Rez.Drawables.MapView39],[133.448686,-31.885558,Rez.Drawables.MapView40],[135.889502,33.544224,Rez.Drawables.MapView41],[119.598667,35.391667,Rez.Drawables.MapView42],[21.166866,67.876724,Rez.Drawables.MapView43],[148.1129553,-19.958151,Rez.Drawables.MapView44],[56.822,18.7862,Rez.Drawables.MapView45],[78.0182402,8.3588887,Rez.Drawables.MapView46],[131.0791609,31.2519752,Rez.Drawables.MapView47],[80.235,13.733,Rez.Drawables.MapView48],[15.5895,69.1084,Rez.Drawables.MapView49],[53.920936,35.23462,Rez.Drawables.MapView50],[-159.759328,21.982029,Rez.Drawables.MapView51],[34.680278,31.884444,Rez.Drawables.MapView52],[-104.757121,31.422878,Rez.Drawables.MapView53]];
    Test.assert(NativeAssets.mapCoordinates.size()==expected.size()*8);
    for(var i=0;i<expected.size();i+=1){
        var x=NativeAssets.mapCoordinates.decodeNumber(Lang.NUMBER_FORMAT_FLOAT,{:offset=>i*8,:endianness=>Lang.ENDIAN_BIG});
        var y=NativeAssets.mapCoordinates.decodeNumber(Lang.NUMBER_FORMAT_FLOAT,{:offset=>i*8+4,:endianness=>Lang.ENDIAN_BIG});
        Test.assert(x==expected[i][0]&&y==expected[i][1]&&NativeAssets.mapResource(i)==expected[i][2]);
    }
    logger.debug("PACKED_MAP all54 exactOriginalFloatAndResource=true");return true;
}

(:test,:typecheck(false)) function deliverySettingsLocaleGroups(logger){
    var locales=["en","ru","de","fr","es"];
    var expectedTitles=["Language","Язык","Sprache","Langue","Idioma"];
    var expectedFields=["Steps","Шаги","Schritte","Pas","Pasos"];
    var expectedColors=["Mint","Мятный","Mint","Menthe","Menta"];
    for(var i=0;i<locales.size();i+=1){
        var titles=SettingsMenuText.values(locales[i],0);var languages=SettingsMenuText.values(locales[i],1);var fields=SettingsMenuText.values(locales[i],2);var colors=SettingsMenuText.values(locales[i],3);
        Test.assert(titles.size()==13&&titles[0].equals(expectedTitles[i]));Test.assert(languages.size()==6&&languages[0].equals("English"));
        Test.assert(fields.size()==6&&fields[0].equals(expectedFields[i]));Test.assert(colors.size()==6&&colors[0].equals(expectedColors[i]));
    }
    Test.assert(SettingsMenuText.values("unknown",0)[0].equals("Language"));
    logger.debug("SETTINGS_GROUPS fiveLocalesAndEnglishFallback=true");return true;
}

(:test,:typecheck(false)) function deliveryBundledFallbackTransitions(logger){
    var renderer=new SceneRenderer(null);var settings=new SceneSettings(null);var context=new SceneContext({"id"=>"ll2:launch:test","modelId"=>"falcon-9","point"=>[-80.5657,28.4458]});
    var coldStart=System.getTimer();renderer.prepare(context,settings);var coldMs=System.getTimer()-coldStart;var coldLoads=renderer.resourceLoads;var map=renderer.map;var art=renderer.art;Test.assert(map!=null&&art!=null&&renderer.pin&&renderer.aodResource!=null);
    var warmStart=System.getTimer();renderer.prepare(context,settings);var warmMs=System.getTimer()-warmStart;Test.assert(renderer.resourceLoads==coldLoads);
    var rich=new NativeSfrRenderer();rich.bitmap=art;rich.mapBitmap=map;renderer.useDownloaded(rich);
    Test.assert(renderer.art==null&&renderer.map==null&&renderer.pin&&renderer.aodResource!=null);renderer.prepareAod();Test.assert(renderer.aodMap!=null);
    renderer.useDownloaded(null);Test.assert(renderer.art!=null&&renderer.map!=null&&renderer.pin);
    var incomplete=new NativeSfrRenderer();renderer.useDownloaded(incomplete);Test.assert(renderer.art!=null&&renderer.map!=null);
    renderer.prepare(context,settings);Test.assert(renderer.art!=null&&renderer.map!=null);
    logger.debug("FALLBACK completeReleasesOnlyReplaced=true lowAndIncompleteRetained=true coldPrepareMs="+coldMs+" coldCumulativeLoads="+coldLoads+" warmPrepareMs="+warmMs+" warmAdditionalLoads=0");return true;
}

(:typecheck(false)) class DeliveryDeadlineService extends FeedService {
    var finishes=0;
    function finish(){if(!ended){ended=true;finishes+=1;}}
}
(:test,:typecheck(false)) function deliveryLateCallbackCannotStage(logger){
    var store=new DeliveryScheduleStore();var service=new DeliveryDeadlineService();service.transfer=new NativeTransfer("https://late.test",store);service.batch=new NativeBatch(store,service.transfer.base);
    store.write("sf.commit",{"seal"=>"accepted"});service.deadlineArmed=true;service.started=System.getTimer()-22001;service.inFlight=true;
    service.receive(200,"late body");Test.assert(service.finishes==1&&store.read("sf.incoming.feed")==null&&store.read("sf.commit")["seal"].equals("accepted"));
    service.receiveBatch(200,"duplicate body");Test.assert(service.finishes==1&&store.read("sf.incoming.feed")==null&&store.read("sf.commit")["seal"].equals("accepted"));
    logger.debug("LATE_CALLBACK noStageOrAcceptedMutation=true duplicateIgnored=true");return true;
}

(:test,:typecheck(false)) function deliveryProvisionalFragmentCleanup(logger){
    var store=new DeliveryScheduleStore();var base="https://fragments.test";var transfer=new NativeTransfer(base,store);var longText="";
    for(var i=0;i<1100;i+=1){longText+="a";}Test.assert(transfer.stage("feed",longText,null));
    var before=store.read("sf.incoming.feed");Test.assert(before["parts"].size()==3);
    Test.assert(transfer.stage("feed","short",null));var marker=store.read("sf.incoming.feed");Test.assert(marker["parts"].size()==1);
    for(var i=0;i<16;i+=1){for(var bank=0;bank<2;bank+=1){var value=store.read("sf.incoming.feed."+bank+"."+i);if(i==0&&bank==marker["parts"][0]){Test.assert(value.equals("short"));}else{Test.assert(value==null);}}}
    var incoming=new NativeIncoming(store,base);var row=incoming.read("feed",true);Test.assert(row!=null&&row[1].equals("short"));
    store.data["sf.incoming.feed."+marker["parts"][0]+".0"]="broken";Test.assert(incoming.read("feed",true)==null);
    logger.debug("FRAGMENTS longToShortBounded=true currentReadable=true corruptRefused=true");return true;
}

(:test,:typecheck(false)) function deliveryCurrentPlanFallback(logger){
    var store=new DeliveryScheduleStore();var transfer=new NativeTransfer("https://plan.test",store);store.write("sf.transfer.ready",{"base"=>transfer.base,"accepted"=>true});store.write("sf.commit",{"seal"=>"accepted"});
    var plan={"base"=>transfer.base,"policy"=>[3600,900,null],"target"=>20000l,"targets"=>[20000l]};store.write("sf.transfer.plan",plan);
    Test.assert(transfer.interval(15000l)==900&&transfer.interval(1000l)==3600);
    plan["targets"]=[];Test.assert(transfer.interval(15000l)==3600);
    plan.remove("targets");Test.assert(transfer.planTargets(plan)==null&&transfer.interval(15000l)==900);
    plan["targets"]=["invalid"];Test.assert(transfer.interval(15000l)==900);Test.assert(store.read("sf.commit")["seal"].equals("accepted"));
    logger.debug("PLAN currentTargets=true missingOrCorruptNearCadence=true acceptedUnchanged=true");return true;
}

(:test,:typecheck(false)) function deliveryUpcomingPinnedAndRecovery(logger){
    var store=new DeliveryScheduleStore();var base="https://rollover017.fixture.invalid";var instance="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";var h=new NativeWireHash();h.put(base);var pin="sf.pin."+h.digest();store.write("sf.pins",[pin]);store.write(pin,{"instance"=>instance,"generation"=>1});
    var data={"id"=>"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a","rocket"=>"Vulcan VC6L","operator"=>"United Launch Alliance","operatorShort"=>"ULA","purpose"=>"Communications","site"=>"Cape Canaveral SFS","modelId"=>"ll2:configuration:479","operatorId"=>"ll2:organization:124","siteId"=>"ll2:site:29","point"=>[-80.58341025,28.58341025],"pointText"=>["-80.58341025","28.58341025"],"target"=>1794913022l,"precision"=>"exact","retentionDeadline"=>1794913922l,"orderingUtc"=>1794913022l,"sourceValidated"=>1794826622l,"freshnessPolicy"=>{"normal_interval_seconds"=>3600,"near_interval_seconds"=>900,"fast_interval_seconds"=>null,"stale_cycles"=>3}};
    var queue=new NativeUpcomingCache(store,base,instance);queue.save([new SceneContext(data)]);var reopened=new NativeUpcomingCache(store,base,instance);var loaded=reopened.load();Test.assert(loaded.size()==1&&loaded[0].launchId.equals(data["id"])&&loaded[0].retentionTarget==data["target"]);
    var pins=[pin];var urls=[base];for(var i=1;i<8;i+=1){var url="https://namespace"+i+".fixture.invalid";h=new NativeWireHash();h.put(url);var nextPin="sf.pin."+h.digest();pins.add(nextPin);urls.add(url);store.write(nextPin,{"instance"=>instance,"generation"=>1});}store.write("sf.pins",pins);
    for(var i=1;i<8;i+=1){new NativeUpcomingCache(store,urls[i],instance).save([new SceneContext(data)]);}
    var denied=false;try{new NativeUpcomingCache(store,"https://other.fixture.invalid",instance).save([]);}catch(e){denied=true;}Test.assert(denied&&reopened.load().size()==1);
    for(var i=0;i<8;i+=1){Test.assert(new NativeUpcomingCache(store,urls[i],instance).load()[0].retentionTarget==1794913022l);}
    var original=store.read(queue.key);store.failWrite=queue.key;data["target"]=1794916622l;data["retentionDeadline"]=1794917522l;data["orderingUtc"]=1794916622l;var failed=false;try{queue.save([new SceneContext(data)]);}catch(e){failed=true;}store.failWrite=null;Test.assert(failed&&store.read(queue.key)==original&&reopened.load()[0].retentionTarget==1794913022l);
    store.data[queue.key]={"value"=>original["value"],"seal"=>"0000000000000000000000000000000000000000000000000000000000000000"};Test.assert(reopened.load().size()==0);store.data[queue.key]=original;Test.assert(reopened.load().size()==1);
    logger.debug("UPCOMING eightPinnedRestored=true ninthUnpinnedRefused=true failedWritePreserved=true corruptSealRefused=true");return true;
}

(:test,:typecheck(false)) class DeliveryCountingPresentation extends LocalePresentation {
    var fits=0;function initialize(){LocalePresentation.initialize();}
    function fit(dc,value,font,width){fits+=1;return LocalePresentation.fit(dc,value,font,width);}
}
(:test,:typecheck(false)) class DeliveryCountingRenderer extends SceneRenderer {
    var captured=[];function initialize(p){SceneRenderer.initialize(p);}
    function text(dc,x,y,font,value,color,width,contour){var shown=SceneRenderer.text(dc,x,y,font,value,color,width,contour);captured.add(shown);return shown;}
}
(:test,:typecheck(false)) function deliveryWarmLayoutIdentity(logger){
    var p=new DeliveryCountingPresentation();var renderer=new DeliveryCountingRenderer(p);var settings=new SceneSettings(null);var context=new SceneContext({"id"=>"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a","rocket"=>"Falcon 9","operator"=>"SpaceX","modelId"=>"falcon-9","point"=>[-80.5657,28.4458]});renderer.prepare(context,settings);
    var bitmap=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();var dc=bitmap.getDc();var fitness=new Fitness();var values={"steps"=>1234,"energy"=>55,"heart"=>80,"stress"=>30};var clock=new ClockSnapshot("08:08","T- 01:00:00");
    var start=p.fits;renderer.active(dc,clock,settings,values,fitness,0.0);var cold=p.fits-start;renderer.captured=[];start=p.fits;renderer.active(dc,clock,settings,values,fitness,0.0);var warm=p.fits-start;
    Test.assert(warm<cold&&renderer.captured.indexOf("Falcon 9")>=0&&renderer.captured.indexOf("1,234")>=0);
    values["steps"]=2345;clock.countdown="T- 00:59:59";renderer.captured=[];renderer.active(dc,clock,settings,values,fitness,0.0);Test.assert(renderer.captured.indexOf("2,345")>=0&&renderer.captured.indexOf("T- 00:59:59")>=0);
    context.rocket="Electron";renderer.captured=[];renderer.active(dc,clock,settings,values,fitness,0.0);Test.assert(renderer.captured.indexOf("Electron")>=0&&renderer.captured.indexOf("Falcon 9")<0);
    logger.debug("LAYOUT coldFitCalls="+cold+" warmFitCalls="+warm+" dynamicMetricCountdownAndTitle=true");return true;
}

(:typecheck(false)) function deliveryCopy(value){
    if(value instanceof Dictionary){var result={};var keys=value.keys();for(var i=0;i<keys.size();i+=1){result[keys[i]]=deliveryCopy(value[keys[i]]);}return result;}
    if(value instanceof Array){var result=[];for(var i=0;i<value.size();i+=1){result.add(deliveryCopy(value[i]));}return result;}return value;
}
(:test,:typecheck(false)) function deliveryRawProjectionIntegrity(logger){
    var fixture=WatchUi.loadResource(Rez.JsonData.DisplayInitial);var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);var store=new DeliveryScheduleStore();store.write("sf.obj."+catalog["catalogDigest"],catalog["catalog"]);var cache=new NativeCache("https://projection.fixture.invalid",store);var now=1794551192l;
    Test.assert(cache.accept(fixture["raw"],now));var marker=store.read("sf.commit");var seal=marker["seal"];var loaded=cache.readCommit(marker,now);Test.assert(loaded!=null&&loaded.refreshTarget()==1794609900l);
    // Optional derived fields are rebuilt from the authenticated current raw
    // packet, and every field actually stored still has to match that packet.
    var subset=deliveryCopy(marker);subset["prior"][0]["launch"]["timing"].remove("refresh_utc");subset["priorHash"]=cache.priorHash(subset["prior"]);subset["seal"]=cache.seal(subset);loaded=cache.readCommit(subset,now);Test.assert(loaded!=null&&loaded.refreshTarget()==1794609900l);
    var changed=deliveryCopy(marker);changed["prior"][0]["launch"]["configuration_id"]="ll2:configuration:479";changed["priorHash"]=cache.priorHash(changed["prior"]);changed["seal"]=cache.seal(changed);Test.assert(cache.readCommit(changed,now)==null);
    changed=deliveryCopy(marker);changed["prior"][0]["launch"]["timing"]["refresh_utc"]=1794609960l;changed["priorHash"]=cache.priorHash(changed["prior"]);changed["seal"]=cache.seal(changed);Test.assert(cache.readCommit(changed,now)==null);
    var key="sf.feed."+marker["slot"]+".0";var piece=store.read(key);store.data[key]=piece+"x";Test.assert(cache.readCommit(marker,now)==null);store.data[key]=piece;Test.assert(store.read("sf.commit")["seal"].equals(seal)&&cache.readCommit(marker,now)!=null);
    logger.debug("RAW_PROJECTION currentAndOptionalRebuilt=true readdressedIdentityAndTimeTamperRefused=true rawCorruptionRefused=true acceptedSealUnchanged=true");return true;
}

(:test,:typecheck(false)) class DeliveryTimedService extends FeedService {
    var logical=1000;var sends=0;var cancels=0;var rearms=0;var exits=0;
    function nowMillis() as Number{return logical;}
    function sendRequest(path as String,callback as Method) as Void{sends+=1;}
    function cancelOutstanding() as Void{cancels+=1;}
    function rearm() as Void{rearms+=1;}
    function leave() as Void{exits+=1;}
}
(:test,:typecheck(false)) function deliveryDeadlineEventSequence(logger){
    var fixture=WatchUi.loadResource(Rez.JsonData.DisplayInitial);var catalog=WatchUi.loadResource(Rez.JsonData.DisplayCatalog);var store=new DeliveryScheduleStore();store.write("sf.commit",{"seal"=>"accepted"});var service=new DeliveryTimedService();service.transfer=new NativeTransfer("https://deadline.fixture.invalid",store);service.batch=new NativeBatch(store,service.transfer.base);
    service.startDeadline();service.request("feed.json",service.method(:receive));Test.assert(service.sends==1&&service.inFlight);service.logical=2000;service.receive(200,fixture["raw"]);Test.assert(service.sends==2&&service.inFlight&&store.read("sf.incoming.feed") instanceof Dictionary);
    service.logical=23000;service.receiveBatch(200,catalog["catalog"]);Test.assert(service.exits==1&&service.rearms==1&&service.cancels==0&&!service.inFlight&&store.read("sf.obj."+catalog["catalogDigest"])==null&&store.read("sf.commit")["seal"].equals("accepted"));service.receiveBatch(200,catalog["catalog"]);Test.assert(service.exits==1);
    var stopped=new DeliveryTimedService();stopped.transfer=new NativeTransfer("https://deadline.fixture.invalid",store);stopped.startDeadline();stopped.request("feed.json",stopped.method(:receive));stopped.finish();stopped.finish();stopped.receive(200,fixture["raw"]);Test.assert(stopped.sends==1&&stopped.cancels==1&&stopped.rearms==1&&stopped.exits==1);
    logger.debug("DEADLINE onTimeStage=true lateNoWrite=true ownerCancelOnce=true duplicateIgnored=true acceptedUnchanged=true");return true;
}

(:test,:typecheck(false)) function deliveryBatchCausalSequences(logger){
    // The order and dispositions are generated from seed, while expected
    // requests come from the independently constructed fixture order.
    for(var seed=0;seed<6;seed+=1){
        var store=new DeliveryScheduleStore();var base="https://sequence.fixture.invalid";var imm=new NativeImmutable(store);var catalog="{}";var h=new NativeWireHash();h.put(catalog);var catalogHash=h.digest();Test.assert(imm.put({"sha256"=>catalogHash,"decodedBytes"=>null},catalog));
        var values=["one","two","three"];var refs=[];var rows=[];for(var i=0;i<3;i+=1){h=new NativeWireHash();h.put(values[i]);var digest=h.digest();refs.add({"path"=>"rasters/"+digest+".sfr","sha256"=>digest,"decodedBytes"=>values[i].length()});rows.add("[1,\""+digest+"\","+values[i].length()+"]");}
        var a="{\"objects\":["+rows[0]+","+rows[1]+","+rows[2]+"]}";var z="{\"objects\":["+rows[2]+","+rows[1]+","+rows[0]+"]}";h=new NativeWireHash();h.put(a);var ah=h.digest();h=new NativeWireHash();h.put(z);var zh=h.digest();
        var ar={"path"=>"descriptors/"+ah+".json","sha256"=>ah,"decodedBytes"=>a.length()};var zr={"path"=>"descriptors/"+zh+".json","sha256"=>zh,"decodedBytes"=>z.length()};Test.assert(imm.put(ar,a)&&imm.put(zr,z));
        var batch=new NativeBatch(store,base);batch.select({"catalogDigest"=>catalogHash,"transfer"=>ar});var applied=0;var corruptRejected=0;var duplicateObserved=0;var restarts=0;
        for(var i=0;i<3;i+=1){
            var requested=batch.next();Test.assert(requested["sha256"].equals(refs[i]["sha256"]));
            if(i==seed%3){Test.assert(!batch.immutable.put(requested,values[i]+"bad"));Test.assert(batch.next()["sha256"].equals(refs[i]["sha256"]));corruptRejected+=1;}
            if(i==(seed+1)%3){Test.assert(batch.next()["sha256"].equals(refs[i]["sha256"]));duplicateObserved+=1;batch=new NativeBatch(store,base);Test.assert(batch.next()["sha256"].equals(refs[i]["sha256"]));restarts+=1;}
            Test.assert(batch.immutable.put(requested,values[i]));applied+=1;
        }
        Test.assert(batch.next()==null);batch.select({"catalogDigest"=>catalogHash,"transfer"=>zr});Test.assert(batch.next()==null);
        var damaged=refs[seed%3];store.data["sf.obj."+damaged["sha256"]]="bad";batch=new NativeBatch(store,base);Test.assert(batch.next()["sha256"].equals(damaged["sha256"]));
        Test.assert(applied==3&&corruptRejected==1&&duplicateObserved==1&&restarts==1);
    }
    logger.debug("BATCH_SEQUENCE seeds=6 eachApplied=3 corruptRejected=1 duplicateObserved=1 restarted=1 replacementAndPostCompletionCorruption=true");return true;
}

// Independent SHA-256 oracle for actual Russian text straddling the old/new
// hash chunk boundaries, with whole, segmented and range entry points.
(:test,:typecheck(false)) function deliveryUtf8HashChunking(logger){
 var text="";for(var i=0;i<250;i+=1){text+="A";}text+="Россия · Восточный";for(var i=0;i<260;i+=1){text+="Z";}
 var expected="550e704288a9b41f053ba03ec031e8b61d2e3281d869093c42224b787c8ac9bf";var one=new NativeWireHash();one.put(text);var digest=one.digest();Test.assert(digest.equals(expected)&&one.count==544);
 var two=new NativeWireHash();two.put(text.substring(0,127));two.put(text.substring(127,256));two.put(text.substring(256,text.length()));Test.assert(two.digest().equals(expected)&&two.count==544);
 var three=new NativeWireHash();three.range(text,0,text.length());Test.assert(three.digest().equals(expected)&&three.count==544);logger.debug("UTF8_HASH bytes=544 wholeSegmentedRangeMatch=true");return true;
}
