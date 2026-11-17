import Toybox.Application;
import Toybox.Lang;
import Toybox.Test;
import Toybox.Time;
import Toybox.System;
import Toybox.Graphics;
import Toybox.WatchUi;

// Actual durable storage and production transfer, batch, immutable, parser and
// cache owners. The fixture substitutes only the HTTP response boundary.
(:test,:typecheck(false)) function b1ColdAcquisition(logger) {
    Application.Storage.clearValues(); // test UUID only; each cold replay starts empty
    var store=new NativeStore();var base="https://jekamas.github.io/SpaceFox";
    // Replay the captured response at its recorded capture instant, without
    // rebasing source timestamps or claiming this is a live provider request.
    var now=1794818604l;var cache=new TestNativeCache(base,store);
    Test.assertMessage(cache.load(now)==null,"cold installation must start without a committed packet");
    var transfer=new NativeTransfer(base,store);var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];
    Test.assert(transfer.stage("feed",raw,null));var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));raw=null;
    var request=batch.next();Test.assert(request!=null&&request["path"].find("wire3/catalogs/")==0);
    var response=b1Response(request["path"]);Test.assert(response!=null);Test.assert(batch.immutable.put(request,response));response=null;
    var measuredRaw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];var measured=new B1MeasuredFeed(store);measured.measure(measuredRaw,now,logger);
    var cancelled=new NativePreparedBridgeFeed(measuredRaw,now,store);cancelled.prepareStep();var abandonedParser=cancelled.parser;Test.assert(abandonedParser!=null&&abandonedParser.rowOwner==cancelled&&abandonedParser.nodeOwner==cancelled);cancelled.disposePreparation();Test.assert(cancelled.parser==null&&abandonedParser.rowOwner==null&&abandonedParser.nodeOwner==null&&abandonedParser.source.equals(""));cancelled=null;abandonedParser=null;
    var staged=new NativePreparedBridgeFeed(measuredRaw,now,store);var steps=0;var maxStep=0;var maxUsed=0;var finished=false;while(!finished){var tick=System.getTimer();finished=staged.prepareStep();var elapsed=System.getTimer()-tick;if(elapsed>maxStep){maxStep=elapsed;}var used=System.getSystemStats().usedMemory;if(used>maxUsed){maxUsed=used;}steps+=1;Test.assert(steps<2000);}
    Test.assert(steps>7&&staged.wireHash.equals(measured.wireHash)&&staged.contentHash.equals(measured.contentHash)&&staged.recordHash.equals(measured.recordHash));
    // Successor rows are compacted only after their full validation. Compare
    // every retained scene field to the independent synchronous oracle and
    // compare the rest of the complete document and all raw identity spans.
    var actualRows=staged.document["upcoming"];var expectedRows=measured.document["upcoming"];
    Test.assert(actualRows instanceof Array&&expectedRows instanceof Array&&actualRows.size()==expectedRows.size());
    for(var q=0;q<actualRows.size();q+=1){var expectedRow=expectedRows[q];var actualRow=actualRows[q];if(expectedRow.hasKey("terminal")){Test.assert(nativeSame(actualRow,expectedRow));}else{var point=expectedRow["sitePosition"];var site=point==null?null:{"positionMode"=>"fixed-source","position"=>point};var expectedScene=feedSceneRow(measured,expectedRow,site,false);Test.assert(actualRow instanceof SceneContext&&nativeSame(actualRow.cacheRow(),expectedScene.cacheRow()));}}
    var checkedLaunch=measured.document["launch"];var removed=["mission_name","source_updated_utc","source_updated_subsecond","source_updated_iso","source_status_name"];for(var di=0;di<removed.size();di+=1){checkedLaunch.remove(removed[di]);}var removedTiming=["source_net","source_precision_name","source_precision_abbrev","source_precision_description"];for(var ti=0;ti<removedTiming.size();ti+=1){checkedLaunch["timing"].remove(removedTiming[ti]);}
    staged.document.remove("upcoming");measured.document.remove("upcoming");
    Test.assertMessage(nativeSame(staged.document,measured.document)&&nativeSame(staged.spans,measured.spans)&&nativeSame(staged.ignored,measured.ignored),"incremental parser and owners must match the original parser");
    staged.document["upcoming"]=actualRows;measured.document["upcoming"]=expectedRows;
    for(var mask=1;mask<=3;mask+=1){if(staged.recordHashes[mask]!=null){Test.assertMessage(staged.recordHashes[mask].equals(measured.recordIdentity(mask)),"prepared record enrichment hash mismatch");}}
    logger.debug("B1_CANCEL parser_cycle_released=true retry=true");logger.debug("B1_PREPARE phases="+steps+" hashes_match=true maxStepMs="+maxStep+" sampledUsedBytes="+maxUsed);measured=null;measuredRaw=null;
    var incoming=new TestNativeIncoming(store,base);var reader=new NativeIncomingReadJob(incoming);var readSteps=0;while(!reader.step()){readSteps+=1;Test.assert(readSteps<=16);}Test.assert(reader.result!=null&&reader.result[1].equals(WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"]));logger.debug("B1_READ parts="+readSteps+" digest=true");
    var sourceRow=reader.result;cache.releaseForTransfer(now);var promotion=new NativeFeedPromotion(cache,incoming.takeRaw(sourceRow),staged,now,null);var promotionSteps=0;while(!promotion.step()){promotionSteps+=1;Test.assert(promotionSteps<30);}Test.assertMessage(promotion.accepted,"catalog-first real feed must be admitted");staged=null;promotion=null;reader=null;logger.debug("B1_ADMISSION promotionSteps="+promotionSteps);
    Test.assert(cache.packet!=null&&cache.packet.launchId().equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));
    var context=feedScene(cache.packet,now);Test.assert(context!=null&&context.point!=null);
    Test.assert(context.schedule.remainingSeconds(now)==null); // captured HR source remains coarse
    var count=1;var batchMax=0;
    while(true){var batchTick=System.getTimer();request=batch.next();if(request!=null){response=b1Response(request["path"]);Test.assertMessage(response!=null,"captured immutable object missing");Test.assert(batch.immutable.put(request,response));response=null;count+=1;Test.assert(count<=27);}var batchMs=System.getTimer()-batchTick;if(batchMs>batchMax){batchMax=batchMs;}if(request==null){break;}}
    logger.debug("B1_BATCH_CALLBACK maxMs="+batchMax+" objects="+count+" includesFinalClosure=true");var source=new NativeRenderSource(store,base,cache.packet.bridge);Test.assert(source.ready);
    var reopened=new TestNativeCache(base,store);var restore=new NativeRestoreJob(reopened,now,null);var reopenSteps=0;while(!restore.step()){reopenSteps+=1;Test.assert(reopenSteps<3000);}Test.assert(restore.accepted);var restored=feedScene(reopened.packet,now);
    Test.assert(restored!=null&&restored.launchId.equals(context.launchId)&&restored.point!=null);
    var renderTick=System.getTimer();var build=new NativeSfrBuild(store,base,reopened.packet);var renderInit=System.getTimer()-renderTick;var renderMax=renderInit;var renderWhere="init";var renderSteps=0;while(!build.complete){var role=build.role;var hadDecoder=build.decoder!=null;renderTick=System.getTimer();build.step();var renderMs=System.getTimer()-renderTick;if(renderMs>renderMax){renderMax=renderMs;renderWhere="role:"+role+" decoder:"+hadDecoder;}renderSteps+=1;Test.assert(renderSteps<2000);}logger.debug("B1_RENDER_CALLBACK maxMs="+renderMax+" initMs="+renderInit+" where="+renderWhere+" steps="+renderSteps+" closure=true");
    logger.debug("B1_COLD status=200 text/plain catalog_first=true staged_objects="+count+" strict_reopen=true captured_hour_precision_unknown=true");return true;
}

// Seed only the service's provisional feed and catalog, never an accepted
// packet or a READY visual. The stock app performs its own foreground parsing.
(:test,:typecheck(false)) function b1SeedProvisional(logger) {
    var store=new NativeStore();var base="https://jekamas.github.io/SpaceFox";
    var cache=new TestNativeCache(base,store);Test.assert(cache.load(1794818604l)==null);
    var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];
    var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",raw,null));
    var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));raw=null;
    var request=batch.next();Test.assert(request!=null&&request["path"].find("wire3/catalogs/")==0);
    var response=b1Response(request["path"]);Test.assert(response!=null&&batch.immutable.put(request,response));
    Test.assert(store.read("sf.commit")==null);
    logger.debug("B1_SEED provisional_feed=true catalog=true accepted=false visual_ready=false");return true;
}

// Timings characterize the same production methods on the captured input;
// this is not a physical device watchdog measurement.
(:test,:typecheck(false)) class B1MeasuredFeed extends NativeBridgeFeed {
    function initialize(adapter){catalogStore=adapter;}
    function parse(value){
        catalogPin=nativeHeaderText(value,"catalogDigest");catalogOperatorId=nativeHeaderText(value,"operator_id");catalogSiteId=nativeHeaderText(value,"site_id");if(!hex(catalogPin)){fail();}
        var rawCatalog=catalogStore.read("sf.obj."+catalogPin);if(!(rawCatalog instanceof String)||rawCatalog.length()>4096){throw new Lang.InvalidValueException("Bridge catalog incomplete");}var hash=new NativeWireHash();hash.put(rawCatalog);if(!hash.digest().equals(catalogPin)||hash.count>4096){throw new Lang.InvalidValueException("Bridge catalog incomplete");}
        var parser=new NativeJson();parser.feedMode=true;parser.catalogMode=true;parser.rowOwner=self;catalogData=parser.parse(rawCatalog,4096);rawCatalog=null;parser=null;hash=null;parseSource(value);
    }
    function parseSource(text){var parser=new NativeJson();parser.feedMode=true;parser.keepCatalogNames=!backgroundNames;parser.rowOwner=self;document=parser.parse(text,8192);spans=parser.spans;ignored=parser.ignored;}
    function hashRaw(text){var wire=new NativeWireHash();wire.put(text);return wire.digest();}
    function validate(now){
        var d=document;header(d);
        phase="publisher";var publisher=d["publisher"];shape(publisher,["instance","generation","selectionValidatedUtc"],[]);
        if(!hex(publisher["instance"])||!integer(publisher["generation"])||publisher["generation"]<1||publisher["generation"]>253402300799l||publisher["selectionValidatedUtc"]!=null&&(!utc(publisher["selectionValidatedUtc"])||publisher["selectionValidatedUtc"]>now)){fail();}
        phase="policy";var policy=d["refreshPolicy"];shape(policy,["normal_interval_seconds","near_interval_seconds","fast_interval_seconds","stale_cycles"],[]);
        var normal=policy["normal_interval_seconds"];var near=policy["near_interval_seconds"];var fast=policy["fast_interval_seconds"];
        var poll=d["pollIntervalSeconds"];if(!policyInteger(normal,300)||!policyInteger(near,300)||policyCompare(near,normal)>0||fast!=null&&(!policyInteger(fast,300)||policyCompare(fast,near)>0)||!policyInteger(policy["stale_cycles"],1)||!policyInteger(poll,300)||policyCompare(poll,normal)!=0&&policyCompare(poll,near)!=0&&(fast==null||policyCompare(poll,fast)!=0)){fail();}
        // Retain native-width policies byte-for-byte in v6 projections so old
        // accepted Long policies remain reopenable. They already calculate
        // safely (division, and bounded wake addition). An overflow policy was
        // never admitted by the old format; normalize its entire policy so
        // mixed Long/lexeme ordering still holds after calculation projection.
        if(normal instanceof NativeIntegerLexeme||near instanceof NativeIntegerLexeme||fast instanceof NativeIntegerLexeme||policy["stale_cycles"] instanceof NativeIntegerLexeme){var policyKeys=["normal_interval_seconds","near_interval_seconds","fast_interval_seconds","stale_cycles"];for(var pi=0;pi<policyKeys.size();pi+=1){policy[policyKeys[pi]]=policyValue(policy[policyKeys[pi]]);}d["pollIntervalSeconds"]=policyValue(poll);}
        phase="dictionaries";var rows=d["dictionaries"];var unresolved=d["unresolvedCatalogIds"];if(!(rows instanceof Dictionary)||!(unresolved instanceof Array)){fail();}
        // Each row was fully schema-checked by dictionaryRow while parsing.
        var last=null;for(var k=0;k<unresolved.size();k+=1){var gap=unresolved[k];if(!(gap instanceof String)||rows.hasKey(gap)||last!=null && last.compareTo(gap)>=0){fail();}if(!id(gap,"configuration",false)&&!id(gap,"organization",false)&&!id(gap,"site",false)&&!id(gap,"country",false)){fail();}last=gap;}
        phase="catalog-hash";catalogHash(d);
        phase="selection";var selection=d["selection"];shape(selection,["acceptedRecords","includedRecords","scope","worldwideCompleteness"],[]);var launch=d["launch"];
        if(!integer(selection["acceptedRecords"])||selection["acceptedRecords"]<0||selection["acceptedRecords"]>128||!integer(selection["includedRecords"])||selection["includedRecords"]!=(launch==null?0:1)||selection["includedRecords"]>selection["acceptedRecords"]||!same(selection["scope"],"selected-launch")||!(selection["worldwideCompleteness"] instanceof Boolean)||selection["worldwideCompleteness"]){fail();}
        if(launch==null){if(!same(d["timingState"],"no-schedule")){fail();}}else{phase="launch";validateLaunch(launch,now,false);}
        hasUpcomingMetadata=d.hasKey("upcoming");
        if(hasUpcomingMetadata){
            phase="upcoming";var upcomingRows=d["upcoming"];if(!(upcomingRows instanceof Array)||upcomingRows.size()>128||upcomingRows.size()+(launch==null?0:1)>selection["acceptedRecords"]){fail();}var ids={};if(launch!=null){ids[launch["launch_id"]]=true;}
            var futureCount=0;terminalUpdates=[];
            for(var u=0;u<upcomingRows.size();u+=1){var item=upcomingRows[u];
                if(item instanceof Dictionary&&item.hasKey("terminal")){shape(item,["terminal"],[]);var terminal=item["terminal"];shape(terminal,["launch_id","status","source_validated_utc","source_updated_utc","source_updated_subsecond"],[]);var tid=terminal["launch_id"];var checked=terminal["source_validated_utc"];var updated=terminal["source_updated_utc"];var sub=terminal["source_updated_subsecond"];if(!id(tid,"launch",false)||ids.hasKey(tid)||["cancelled","completed"].indexOf(terminal["status"])<0||!utc(checked)||checked>now||d["publisher"]["selectionValidatedUtc"]==null||updated!=null&&(!utc(updated)||updated>checked)||!integer(sub)||sub<0||sub>999999||updated==null&&sub!=0){fail();}ids[tid]=true;terminalUpdates.add(terminal);continue;}
                futureCount+=1;if(futureCount>2||!item.hasKey("sitePosition")||!item.hasKey("siteSource")){fail();}var next=item;validateLaunch(next,now,true);if(ids.hasKey(next["launch_id"])){fail();}ids[next["launch_id"]]=true;var point=item["sitePosition"];var source=item["siteSource"];
                if(source!=null){shape(source,["path","sha256","decodedBytes"],[]);if(!hex(source["sha256"])||!same(source["path"],"sources/"+source["sha256"]+".json")||!integer(source["decodedBytes"])||source["decodedBytes"]<1||source["decodedBytes"]>1048576){fail();}}
                if(point!=null){if(source==null){fail();}shape(point,["encoding","latitude","longitude","units","qualification"],[]);if(!same(point["encoding"],"decimal-text-v1")||!same(point["units"],"degrees")||!same(point["qualification"],"unverified-reference")){fail();}decimal(point["latitude"],90);decimal(point["longitude"],180);}
            }
        }
        if(launch!=null){launch["source_updated_iso"]=null;launch["timing"]["source_net"]=null;}phase="traversal";var traversal=d["providerTraversal"];if(traversal!=null){shape(traversal,["query","complete","reportedCount","receivedUpcoming","detailRequests","worldwideCompleteness"],[]);if(!text(traversal["query"],false)||!(traversal["complete"] instanceof Boolean)||!(traversal["worldwideCompleteness"] instanceof Boolean)||traversal["worldwideCompleteness"]||!integer(traversal["reportedCount"])||traversal["reportedCount"]<0||traversal["reportedCount"]>1000000||!integer(traversal["receivedUpcoming"])||traversal["receivedUpcoming"]<0||traversal["receivedUpcoming"]>80||traversal["receivedUpcoming"]>traversal["reportedCount"]||traversal["complete"]&&traversal["receivedUpcoming"]!=traversal["reportedCount"]||!integer(traversal["detailRequests"])||traversal["detailRequests"]<0||traversal["detailRequests"]>4){fail();}}
    }
    function semanticHash(){var hash=new NativeWireHash();var start=0;for(var i=0;i<ignored.size();i+=1){var span=ignored[i];hash.range(raw,start,span[0]);hash.put("null");start=span[1];}hash.range(raw,start,raw.length());return hash.digest();}
    function recordRange(hash,start,end,extra,mask){
        var fields=[spans["/launch/country_code"],extra,spans["/launch/site_location_name"]];
        for(var i=0;i<fields.size();i+=1){var item=fields[i];if(item==null||item[1]<=start||item[0]>=end){continue;}if(item[0]<start||item[1]>end){fail();}hash.range(raw,start,item[0]);if(i!=1){hash.put((mask & (i==0?1:2))!=0?"null":raw.substring(item[0],item[1]));}start=item[1];}hash.range(raw,start,end);
    }
    function recordIdentity(mask){var span=spans["/launch"];var hash=new NativeWireHash();var start=span[0];var ascent=spans["/launch/ascent_end"];var extra=spans["/launch/operator_abbrev"];if(ascent!=null){hash.range(raw,start,start+1);start=ascent[1]+1;}for(var i=0;i<ignored.size();i+=1){var item=ignored[i];if(item[0]<start||item[1]>span[1]){continue;}recordRange(hash,start,item[0],extra,mask);hash.put("null");start=item[1];}recordRange(hash,start,span[1],extra,mask);return hash.digest();}
    function measure(text,now,logger){
        raw=text;var t=System.getTimer();parse(text);logger.debug("B1_PHASE parse_ms="+(System.getTimer()-t));
        t=System.getTimer();validate(now);logger.debug("B1_PHASE validate_ms="+(System.getTimer()-t));
        validation=document["launch"]==null?null:document["launch"]["source_validated_utc"];stale=document["launch"]!=null&&document["launch"]["stale"];rescheduled=document["launch"]!=null&&document["launch"]["rescheduled"];
        t=System.getTimer();contentHash=semanticHash();logger.debug("B1_PHASE semantic_ms="+(System.getTimer()-t));
        t=System.getTimer();wireHash=hashRaw(text);logger.debug("B1_PHASE wire_ms="+(System.getTimer()-t));
        t=System.getTimer();timingKey=timingIdentity();recordHash=recordIdentity(0);reminderData=reminderProjection();logger.debug("B1_PHASE identity_ms="+(System.getTimer()-t));
    }
}

// Existing refreshJsonRefusals literals, applied to the new parser as well.
(:test,:typecheck(false)) function b1IncrementalRefusals(logger){
    var malformed=["{\"x\":1,\"x\":2}","[01]","[true,]","[1]x"];
    for(var i=0;i<malformed.size();i+=1){var rejected=false;try{var p=new NativeIncrementalJson();p.begin(malformed[i],8192);while(!p.step()){} }catch(e){rejected=true;}Test.assertMessage(rejected,"incremental parser accepted existing malformed fixture "+i);}
    logger.debug("B1_REFUSALS existing_literals=4");return true;
}

(:test,:typecheck(false)) class B1MemoryStore {
    var values={};var commits=0;function initialize(){}function read(k){return values[k];}function write(k,v){values[k]=v;if(k.equals("sf.commit")){commits+=1;}}function remove(k){values.remove(k);}
}
(:test,:typecheck(false)) function b1PreparedPromotion(logger){
    var store=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var now=1794818604l;var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];
    var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));var ref=batch.next();Test.assert(ref!=null);Test.assert(batch.immutable.put(ref,b1Response(ref["path"])));
    var prepared=new NativePreparedBridgeFeed(raw,now,store);var count=0;while(!prepared.prepareStep()){count+=1;Test.assert(count<2000);}
    var cache=new TestNativeCache(base,store);var promotion=new NativeFeedPromotion(cache,raw,prepared,now,null);var promotions=0;var releasedBeforeSeal=false;while(!promotion.step()){Test.assertMessage(store.read("sf.commit")==null,"commit became visible before promotion completed");if(promotion.phase==10){releasedBeforeSeal=promotion.mustYield&&prepared.raw.equals("")&&prepared.presentation!=null&&prepared.parser==null;}promotions+=1;Test.assert(promotions<30);}Test.assert(releasedBeforeSeal&&promotion.accepted&&cache.packet!=null&&cache.commit!=null);
    var reopened=new TestNativeCache(base,store);Test.assert(reopened.load(now)!=null);Test.assert(reopened.packet.launchId().equals(cache.packet.launchId()));
    var expectedId=reopened.packet.launchId();var expectedSeal=reopened.commit["seal"];cache=null;promotion=null;prepared=null;reopened=null;
    var sliced=new TestNativeCache(base,store);var restore=new NativeRestoreJob(sliced,now,null);var restoreSteps=0;while(!restore.step()){restoreSteps+=1;Test.assert(restoreSteps<3000);}Test.assert(restore.accepted&&sliced.packet.launchId().equals(expectedId)&&sliced.commit["seal"].equals(expectedSeal));
    logger.debug("B1_PROMOTION slices="+promotions+" strict_reopen=true sliced_restore="+restoreSteps);return true;
}

(:test) class B1ExactClock extends WatchClock {
    var now as Number=1794677000;
    function utcSeconds() as Number{return now;}
}

// Exercise the actual app/view admission owner around a simulated LOW/wake.
(:test,:typecheck(false)) function b1ShortWakeResume(logger){
    var store=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var now=1794818604l;var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];
    var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",raw,null));var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));var ref=batch.next();Test.assert(ref!=null&&batch.immutable.put(ref,b1Response(ref["path"])));
    var exactRaw=WatchUi.loadResource(Rez.JsonData.B1ExactFeed)["raw"];var exactCatalog=WatchUi.loadResource(Rez.JsonData.B1ExactCatalog)["raw"];var exactHash=new NativeWireHash();exactHash.put(exactCatalog);var exactDigest=exactHash.digest();Test.assert(new NativeImmutable(store).put({"sha256"=>exactDigest,"decodedBytes"=>exactHash.count},exactCatalog));var exact=new NativePreparedBridgeFeed(exactRaw,1794677000l,store);while(!exact.prepareStep()){}var exactScene=feedScene(exact,1794677000l);Test.assert(exactScene!=null&&exactScene.schedule.remainingSeconds(1794677000l)==550);exact=null;exactRaw=null;exactCatalog=null;
    var app=new SpaceFoxApp();var clock=new B1ExactClock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));view.setContext(exactScene);app.view=view;app.feed=new TestNativeCache(base,store);var frame=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();view.onLayout(frame.getDc());Test.assert(view.renderer!=null);view.onShow();view.queueResumeAfterFrame();view.stopResume();
    Test.assertMessage(view.canForegroundWork(),"test requires HIGH simulator mode");NativeForegroundApp.beginAdmission(app,app.feed,new TestNativeIncoming(store,base),now);Test.assert(view.renderer==null&&view.downloaded==null&&view.context==exactScene);
    view.updateForDisplayMode(frame.getDc(),System.DISPLAY_MODE_HIGH_POWER);var first=view.snapshotAt(clock.now).countdown;clock.now+=1;view.updateForDisplayMode(frame.getDc(),System.DISPLAY_MODE_HIGH_POWER);var second=view.snapshotAt(clock.now).countdown;Test.assert(first.equals("T- 00:09:10")&&second.equals("T- 00:09:09"));
    var ticks=0;while(app.admissionJob!=null&&(app.admissionJob["packet"]==null||app.admissionJob["packet"].preparePhase<3)){if(app.admissionTimer!=null){app.admissionTimer.stop();app.admissionTimer=null;}app.admissionStep();ticks+=1;Test.assert(ticks<2000);}
    var held=app.admissionJob;Test.assert(held!=null);var before=held["packet"].preparePhase;view.transitionMode(0);if(app.admissionTimer!=null){app.admissionTimer.stop();app.admissionTimer=null;}var lowUsed=System.getSystemStats().usedMemory;view.drawPendingLow(frame.getDc());logger.debug("B1_PENDING_LOW_DURING_PARSE before="+lowUsed+" after="+System.getSystemStats().usedMemory);app.admissionStep();Test.assert(app.admissionJob==held&&held["packet"].preparePhase==before);
    view.transitionMode(1);view.queueResumeAfterFrame();view.stopResume();Test.assert(view.canForegroundWork());
    while(app.admissionJob!=null){if(app.admissionTimer!=null){app.admissionTimer.stop();app.admissionTimer=null;}app.admissionStep();ticks+=1;Test.assert(ticks<3000);}
    Test.assert(app.feed.packet!=null&&app.feed.packet.launchId().equals("ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60"));Test.assert(!view.admissionPending&&store.commits==1);
    view.onHide();logger.debug("B1_SHORT_WAKE same_job=true resumed=true exact_seconds=true admitted=true slices="+ticks);return true;
}

(:test,:typecheck(false)) function b1BatchCorruption(logger){
    var store=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));
    var catalog=batch.next();Test.assert(catalog!=null&&batch.immutable.put(catalog,b1Response(catalog["path"])));var next=batch.next();Test.assert(next!=null);
    // Corrupt the previously verified catalog while later immutable objects
    // are still downloading; the fresh completion scan must request it again.
    store.write("sf.obj."+catalog["sha256"],"corrupt");var delivered=0;
    while(next!=null&&!next["sha256"].equals(catalog["sha256"])){var value=b1Response(next["path"]);Test.assert(value!=null&&batch.immutable.put(next,value));next=batch.next();delivered+=1;Test.assert(delivered<=27);}
    Test.assertMessage(next!=null&&next["sha256"].equals(catalog["sha256"]),"corrupted prefix must be re-requested before closure");Test.assert(batch.immutable.put(next,b1Response(next["path"])));Test.assert(batch.next()==null);
    logger.debug("B1_BATCH corrupt_prefix_redownload=true delivered="+delivered);return true;
}

(:test,:typecheck(false)) function b1SeedBadCache(logger){
    var store=new NativeStore();store.write("sf.commit",{"v"=>6,"base"=>"https://jekamas.github.io/SpaceFox","seal"=>"invalid"});
    logger.debug("B1_BAD_CACHE seed=invalid_commit");return true;
}

(:test,:typecheck(false)) function b1RejectedFeedCooldown(logger){
    var store=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];var invalid="["+raw.substring(1,raw.length());var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",invalid,null));var batch=new NativeBatch(store,base);Test.assert(batch.begin(invalid));var ref=batch.next();Test.assert(ref!=null&&batch.immutable.put(ref,b1Response(ref["path"])));
    var app=new SpaceFoxApp();var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));app.view=view;app.feed=new NativeCache(base,store);view.onShow();view.queueResumeAfterFrame();view.stopResume();Test.assert(view.canForegroundWork());var incoming=new NativeIncoming(store,base);NativeForegroundApp.beginAdmission(app,app.feed,incoming,Time.now().value().toLong());
    var steps=0;while(app.admissionJob!=null){if(app.admissionTimer!=null){app.admissionTimer.stop();app.admissionTimer=null;}app.admissionStep();steps+=1;Test.assert(steps<2000);}Test.assert(app.feed.packet==null);Test.assertMessage(!NativeForegroundApp.hasNewIncoming(app.feed,incoming),"rejected complete feed must not restart each wake");
    var rejected=store.read("sf.incoming.feed.rejected");Test.assert(rejected instanceof Dictionary);rejected["until"]=Time.now().value().toLong()-1;Test.assert(NativeForegroundApp.hasNewIncoming(app.feed,incoming));store.remove("sf.incoming.feed.rejected");store.remove("sf.incoming.feed.processed");Test.assertMessage(NativeForegroundApp.hasNewIncoming(app.feed,incoming),"unprocessed missing-catalog work must stay retryable");view.onHide();logger.debug("B1_REJECT cooldown=true finite_retry=true unprocessed_retry=true");return true;
}

(:test,:typecheck(false)) function b1MissingCatalogWait(logger){
    var store=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",raw,null));var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));var ref=batch.next();Test.assert(ref!=null);
    var app=new SpaceFoxApp();var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));app.view=view;app.feed=new NativeCache(base,store);view.onShow();view.queueResumeAfterFrame();view.stopResume();Test.assert(view.canForegroundWork());var incoming=new NativeIncoming(store,base);NativeForegroundApp.beginAdmission(app,app.feed,incoming,Time.now().value().toLong());
    var steps=0;while(app.admissionJob!=null){if(app.admissionTimer!=null){app.admissionTimer.stop();app.admissionTimer=null;}app.admissionStep();steps+=1;Test.assert(steps<2000);}Test.assertMessage(!NativeForegroundApp.hasNewIncoming(app.feed,incoming),"missing catalog must not cause a hot wake loop");Test.assert(store.read("sf.incoming.feed.processed")==null);
    Test.assert(batch.immutable.put(ref,b1Response(ref["path"])));view.queueResumeAfterFrame();view.stopResume();app.onBackgroundData({"provisional"=>true});Test.assertMessage(app.admissionJob!=null,"background catalog arrival must resume immediately");while(app.admissionJob!=null){if(app.admissionTimer!=null){app.admissionTimer.stop();app.admissionTimer=null;}app.admissionStep();steps+=1;Test.assert(steps<4000);}Test.assert(app.feed.packet!=null);view.onHide();logger.debug("B1_CATALOG wait=true background_resume=true accepted=true");return true;
}

(:test,:typecheck(false)) function b1DuplicateAdmission(logger){
    var store=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var now=1794818604l;var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",raw,null));var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));var ref=batch.next();Test.assert(ref!=null&&batch.immutable.put(ref,b1Response(ref["path"])));
    var cache=new NativeCache(base,store);var prepared=new NativePreparedBridgeFeed(raw,now,store);while(!prepared.prepareStep()){}var promotion=new NativeFeedPromotion(cache,raw,prepared,now,null);while(!promotion.step()){}Test.assert(promotion.accepted);var accepted=cache.packet;var seal=cache.commit["seal"];
    var app=new SpaceFoxApp();var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));app.view=view;app.feed=cache;view.setPacket(accepted);view.onShow();view.queueResumeAfterFrame();view.stopResume();Test.assert(view.canForegroundWork());NativeForegroundApp.beginAdmission(app,cache,new NativeIncoming(store,base),now);
    var ticks=0;while(app.admissionJob!=null){if(app.admissionTimer!=null){app.admissionTimer.stop();app.admissionTimer=null;}app.admissionStep();ticks+=1;Test.assert(ticks<30);}Test.assert(cache.packet==accepted&&view.packet==accepted&&cache.commit["seal"].equals(seal)&&store.commits==1);Test.assert(store.read("sf.incoming.feed.processed") instanceof String);view.onHide();logger.debug("B1_DUPLICATE authenticated=true same_packet=true same_seal=true callbacks="+ticks);return true;
}

(:test,:typecheck(false)) function b1SeedBadFeed(logger){
    var store=new NativeStore();var base="https://jekamas.github.io/SpaceFox";var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];var invalid="["+raw.substring(1,raw.length());var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",invalid,null));var batch=new NativeBatch(store,base);Test.assert(batch.begin(invalid));var ref=batch.next();Test.assert(ref!=null&&batch.immutable.put(ref,b1Response(ref["path"])));logger.debug("B1_BAD_FEED seed=complete_invalid catalog=true");return true;
}

// Outside the stock app, prepare both source-bound generations; the stock
// diagnostic later flips only the already-staged marker on a real frame.
(:test,:typecheck(false)) function b1SeedWarm(logger){
    var store=new NativeStore();var base="https://jekamas.github.io/SpaceFox";var old=store.read("sf.incoming.feed");Test.assert(old instanceof Dictionary);var cache=new TestNativeCache(base,store);Test.assert(cache.load(Time.now().value().toLong())!=null);var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];var needle="\"generation\":56";var at=raw.find(needle);Test.assert(at!=null);var changed=raw.substring(0,at)+"\"generation\":57"+raw.substring(at+needle.length(),raw.length());
    var incoming=new NativeIncoming(store,base);incoming.processed("feed",old);var transfer=new NativeTransfer(base,store);Test.assert(transfer.stage("feed",changed,null));var next=store.read("sf.incoming.feed");Test.assert(next instanceof Dictionary&&!next["sha256"].equals(old["sha256"]));store.write("sf.wd.warm",next);store.write("sf.incoming.feed",old);logger.debug("B1_WARM_SEED old="+old["sha256"]+" new="+next["sha256"]);return true;
}

// Real captured text; observe whether a short substring alone retains its
// separately allocated full-feed backing after the creating frame returns.
(:typecheck(false)) function b1HeldFeedSubstring(){
    var original=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];
    var bytes=Toybox.StringUtil.convertEncodedString(original,{:fromRepresentation=>Toybox.StringUtil.REPRESENTATION_STRING_PLAIN_TEXT,:toRepresentation=>Toybox.StringUtil.REPRESENTATION_BYTE_ARRAY,:encoding=>Toybox.StringUtil.CHAR_ENCODING_UTF8});original=null;
    var copy=Toybox.StringUtil.convertEncodedString(bytes,{:fromRepresentation=>Toybox.StringUtil.REPRESENTATION_BYTE_ARRAY,:toRepresentation=>Toybox.StringUtil.REPRESENTATION_STRING_PLAIN_TEXT,:encoding=>Toybox.StringUtil.CHAR_ENCODING_UTF8});bytes=null;
    return copy.substring(0,48);
}
(:test,:typecheck(false)) function b1SubstringRetention(logger){
    var before=System.getSystemStats().usedMemory;var held=b1HeldFeedSubstring();var withHeld=System.getSystemStats().usedMemory;Test.assert(held.length()==48);held=null;var after=System.getSystemStats().usedMemory;
    logger.debug("B1_SUBSTRING before="+before+" held="+withHeld+" released="+after+" held_delta="+(withHeld-after));return true;
}

// Run outside the stock app: expose the already-staged replacement before the
// unmodified production process starts, with its requested RU setting.
(:test,:typecheck(false)) function b1SeedImmediateReplacement(logger){
    var store=new NativeStore();var marker=store.read("sf.wd.warm");Test.assert(marker instanceof Dictionary);store.write("sf.incoming.feed",marker);store.remove("sf.wd.warm");Toybox.Application.Properties.setValue("Language",1);logger.debug("B1_PRESTART replacement=true language=ru");return true;
}

// Read only, in a separate test VM after the pure production process exits.
(:test,:typecheck(false)) function b1InspectImmediateReplacement(logger){
    var store=new NativeStore();var commit=store.read("sf.commit");var incoming=store.read("sf.incoming.feed");var processed=store.read("sf.incoming.feed.processed");Test.assert(commit instanceof Dictionary&&commit["publisher"] instanceof Dictionary&&commit["publisher"]["generation"]==57);Test.assert(incoming instanceof Dictionary&&processed instanceof String&&processed.equals(new NativeIncoming(store,"https://jekamas.github.io/SpaceFox").token(incoming)));logger.debug("B1_PRESTART_RESULT publisher=57 incoming_processed=true");return true;
}

(:test,:typecheck(false)) function b1InspectBadFeed(logger){
    var store=new NativeStore();var base="https://jekamas.github.io/SpaceFox";var marker=store.read("sf.incoming.feed");var rejected=store.read("sf.incoming.feed.rejected");var incoming=new NativeIncoming(store,base);var cache=new NativeCache(base,store);Test.assert(marker instanceof Dictionary&&rejected instanceof Dictionary&&rejected["token"].equals(incoming.token(marker)));Test.assert(!NativeForegroundApp.hasNewIncoming(cache,incoming));logger.debug("B1_BAD_FEED_RESULT rejected=true cooled=true");return true;
}

(:test,:typecheck(false)) function b1AbandonedRetry(logger){
    var store=new B1MemoryStore();var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];var cache=new NativeCache("https://jekamas.github.io/SpaceFox",store);var app=new SpaceFoxApp();var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));view.setContext(new SceneContext({"id"=>"source:launch:one","rocket"=>"Previous rocket","purpose"=>"Previous purpose","site"=>"Previous site","precision"=>"exact","target"=>1794820000l}));app.view=view;app.feed=cache;var candidate=new NativePreparedBridgeFeed(raw,1794818604l,store);candidate.prepareStep();var parser=candidate.parser;var previous=view.context;Test.assert(previous!=null&&previous.rocket.equals("Previous rocket"));app.admissionJob={"cache"=>cache,"packet"=>candidate,"seal"=>"old-seal","key"=>"sf.commit"};view.admissionPending=true;app.abandonForegroundWork();Test.assert(app.admissionJob==null&&!app.restorePending&&app.restoreTimer==null&&app.admissionTimer==null&&!view.admissionPending&&view.context==previous);Test.assert(app.deferredRestore&&app.deferredSeal.equals("old-seal")&&cache.packet==null&&parser.rowOwner==null);app.reloadFeed();Test.assert(!app.deferredRestore&&app.restorePending&&app.restoreSeal.equals("old-seal"));logger.debug("B1_ABANDON terminal=true deferred_event_retry=true owner_released=true");return true;
}

// The LOW frame remains available while the current incremental parser and
// its retained schedule own the foreground heap. This is an SDK resource
// smoke check; screenshots and stock heap remain separate observations.
(:test,:typecheck(false)) function b1PendingLowComposition(logger){
    var store=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];
    var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));var catalog=batch.next();Test.assert(batch.immutable.put(catalog,b1Response(catalog["path"])));
    var packet=new NativePreparedBridgeFeed(raw,1794818604l,store);while(!packet.prepareStep()){}var scene=feedScene(packet,1794818604l);Test.assert(scene!=null&&scene.point!=null);packet.disposePreparation();packet=null;raw=null;batch=null;store=null;
    var frame=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();
    for(var i=0;i<2;i+=1){var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));view.settings.language=i==0?"en":"ru";view.presentation.prepare(view.settings.language);view.setContext(scene);view.presentation.suspend();view.admissionPending=true;view.drawPendingLow(frame.getDc());Test.assert(view.lastLowFrameMinute()!=null&&view.presentation.aodContextFont==null&&view.presentation.aodBatteryFont==null);view=null;}
    var cold=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));cold.admissionPending=true;cold.presentation.suspend();cold.drawPendingLow(frame.getDc());Test.assert(cold.lastLowFrameMinute()!=null&&cold.context==null);logger.debug("B1_PENDING_LOW EN_RU=true retained_point=true cold_map=true temporary_fonts_released=true");return true;
}

// FeedService exits as soon as the first catalog arrives. The next background
// process must resume the same pending immutable batch even when polling is not
// yet due, rather than starting or accepting a different closure.
(:test,:typecheck(false)) function b1NextBackgroundResumesCatalogBatch(logger){
    var store=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var now=Time.now().value().toLong();var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];
    var transfer=new NativeTransfer(base,store);transfer.attempted(now);Test.assert(transfer.stage("feed",raw,null));var first=new NativeBatch(store,base);Test.assert(first.begin(raw));var catalog=first.next();Test.assert(catalog!=null&&catalog["path"].find("wire3/catalogs/")==0);Test.assert(first.immutable.put(catalog,b1Response(catalog["path"])));first=null;raw=null;
    var nextTransfer=new NativeTransfer(base,store);nextTransfer.load();Test.assert(!nextTransfer.due(now+1));Test.assert(batchPending(nextTransfer));var next=new NativeBatch(store,base);var ref=next.next();Test.assert(ref!=null&&ref["path"].find("descriptors/")==0);var delivered=0;
    while(ref!=null){var data=b1Response(ref["path"]);Test.assert(data!=null&&next.immutable.put(ref,data));ref=next.next();delivered+=1;Test.assert(delivered<=41);}
    Test.assert(!batchPending(nextTransfer));logger.debug("B1_NEXT_BACKGROUND polling_due=false resumed=true remaining_objects="+delivered+" closure_verified=true");return true;
}

// A later event may receive the same feed after its closure is complete.
// Its persisted reference rows must be compared without changing the durable
// format; a damaged row must be repaired before final closure succeeds.
(:test,:typecheck(false)) function b1SameBatchReloadAndRepair(logger){
    var store=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];var first=new NativeBatch(store,base);Test.assert(first.begin(raw));var ref=first.next();var count=0;while(ref!=null){var data=b1Response(ref["path"]);Test.assert(data!=null&&first.immutable.put(ref,data));ref=first.next();count+=1;Test.assert(count<42);}Test.assert(count>1);
    var saved=store.read("sf.batch.refs");Test.assert(saved instanceof Dictionary&&saved["refs"] instanceof Array&&saved["refs"].size()>0);var original=saved["refs"][0]["path"];saved["refs"][0]["path"]="damaged";store.write("sf.batch.refs",saved);first=null;saved=null;
    var later=new NativeBatch(store,base);Test.assert(later.begin(raw));Test.assert(later.next()==null);var repaired=store.read("sf.batch.refs");Test.assert(repaired["refs"][0]["path"].equals(original));Test.assert(!batchPending(new NativeTransfer(base,store)));logger.debug("B1_REPEAT_BATCH corrupt_saved_refs_repaired=true closure_verified=true objects="+count);return true;
}

// The selected real captured HR-precision launch has an announced NET, not
// an exact instant. Arithmetic here is display-only; retention, reminders and
// source identity remain the accepted coarse values.
(:test,:typecheck(false)) function b1AnnouncedNetDisplayAndReopen(logger){
    var store=new B1MemoryStore();var base="https://jekamas.github.io/SpaceFox";var raw=WatchUi.loadResource(Rez.JsonData.B1Feed)["raw"];var batch=new NativeBatch(store,base);Test.assert(batch.begin(raw));var catalog=batch.next();Test.assert(batch.immutable.put(catalog,b1Response(catalog["path"])));
    var packet=new NativePreparedBridgeFeed(raw,1794818604l,store);while(!packet.prepareStep()){}var scene=feedScene(packet,1794818604l);Test.assert(scene!=null&&scene.displayTarget==1795042200l&&scene.schedule.remainingSeconds(1794818604l)==null&&scene.retentionTarget==null);
    var view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));view.setContext(scene);var t=scene.displayTarget;
    var day=view.snapshotAt(t-90061);Test.assertEqual(day.countdown,"T- 25:01:01");Test.assertEqual(day.lowCountdown,"T- 25:02");
    var near=view.snapshotAt(t-59);Test.assertEqual(near.countdown,"T- 00:00:59");Test.assertEqual(near.lowCountdown,"T- 00:01");
    var zero=view.snapshotAt(t);Test.assertEqual(zero.countdown,"T+ 00:00:00");Test.assertEqual(zero.lowCountdown,"T+ 00:00");
    var later=view.snapshotAt(t+30);Test.assertEqual(later.countdown,"T+ 00:00:30");Test.assert(scene.schedule.remainingSeconds(t)==null&&scene.retentionTarget==null);
    var queue=new NativeUpcomingCache(store,base,packet.document["publisher"]["instance"]);var oldRow=scene.cacheRow();oldRow.remove("displayTarget");Test.assert(queue.validRow(oldRow));var badRow=scene.cacheRow();badRow["displayTarget"]="not-a-time";Test.assert(!queue.validRow(badRow));queue.save([scene]);var reopened=queue.load();Test.assert(reopened.size()==1&&reopened[0].displayTarget==t&&reopened[0].retentionTarget==null);view.setContext(reopened[0]);Test.assertEqual(view.snapshotAt(t-59).countdown,"T- 00:00:59");
    var unknown=new SceneContext({"id"=>"source:launch:unknown","precision"=>"unknown"});view.setContext(unknown);Test.assertEqual(view.snapshotAt(t).countdown,"--:--:--");
    logger.debug("B1_NET HR_estimated=true over_day=true subminute=true zero_plus=true durable=true schedule_unchanged=true unknown=true");return true;
}

(:test,:typecheck(false)) function b1EstimatedCountdownGlyphWidth(logger){
    var dc=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get().getDc();
    for(var i=0;i<2;i+=1){var presentation=new LocalePresentation();presentation.prepare(i==0?"en":"ru");presentation.prepareAodFonts();var low=presentation.aodContextFont;Test.assertMessage(low!=null,"measure the actual prepared LOW font");var active=presentation.count;var lowWidth=dc.getTextWidthInPixels("T- 25:02",low);var plainLow=dc.getTextWidthInPixels("T- 25:02",low);Test.assertMessage(lowWidth==plainLow&&lowWidth<=300,"over-day LOW value must fit");var activeValue="T- 25:01:01";var activeFont=dc.getTextWidthInPixels(activeValue,active)>275?presentation.small:active;var activeWidth=dc.getTextWidthInPixels(activeValue,activeFont);Test.assert(activeWidth<=275&&dc.getTextWidthInPixels("T-",activeFont)>0);logger.debug("B1_NET_GLYPH locale="+(i==0?"en":"ru")+" lowWidth="+lowWidth+" activeWidth="+activeWidth);}
    return true;
}
