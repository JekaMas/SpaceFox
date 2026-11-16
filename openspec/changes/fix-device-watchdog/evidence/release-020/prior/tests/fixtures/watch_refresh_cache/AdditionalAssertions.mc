import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

(:typecheck(false)) function integrityPacket(name){
 var id=null;
 if(name.equals("wide")){id=Rez.JsonData.IntegrityWide;}else if(name.equals("badSchema")){id=Rez.JsonData.IntegrityBadSchema;}
 else if(name.equals("missingId")){id=Rez.JsonData.IntegrityMissingId;}else if(name.equals("badIso")){id=Rez.JsonData.IntegrityBadIso;}
 else if(name.equals("badPolicy")){id=Rez.JsonData.IntegrityBadPolicy;}else if(name.equals("negativeId")){id=Rez.JsonData.IntegrityNegativeId;}
 else if(name.equals("badGeometry")){id=Rez.JsonData.IntegrityBadGeometry;}
 else if(name.equals("nullId")){id=Rez.JsonData.IntegrityNullId;}else if(name.equals("boolId")){id=Rez.JsonData.IntegrityBoolId;}
 else if(name.equals("quotedId")){id=Rez.JsonData.IntegrityQuotedId;}else if(name.equals("badUtc")){id=Rez.JsonData.IntegrityBadUtc;}
 else if(name.equals("widePrecision")){id=Rez.JsonData.IntegrityWidePrecision;}else if(name.equals("finalRefresh")){id=Rez.JsonData.IntegrityFinalRefresh;}else if(name.equals("boolPolicy")){id=Rez.JsonData.IntegrityBoolPolicy;}else if(name.equals("negativePolicy")){id=Rez.JsonData.IntegrityNegativePolicy;}
 else if(name.equals("changedInstance")){id=Rez.JsonData.IntegrityChangedInstance;}else if(name.equals("nullSelection")){id=Rez.JsonData.IntegrityNullSelection;}else if(name.equals("regressedOrigin")){id=Rez.JsonData.IntegrityRegressedOrigin;}
 if(id==null){throw new Lang.InvalidValueException("unknown integrity fixture");}return WatchUi.loadResource(id)["raw"];
}
(:typecheck(false)) class MoreService extends FeedService {
 var finishes=0;var optionals=0;
 function finish() as Void {finishes+=1;}
 function optional() as Void {optionals+=1;}
}
(:test,:typecheck(false)) function moreServiceAcceptAndReplay(log){
 var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var c=refreshCache(s);
 Test.assert(c.accept(refreshPacket("initial"),1794551202l));var service=new MoreService();
 service.transfer=new NativeTransfer("https://fixture.invalid/refresh",s);service.batch=new NativeBatch(s,service.transfer.base);
 service.receive(200,refreshPacket("moved"));Test.assert(service.optionals==1&&service.finishes==0);
 Test.assert(c.packet.validation==1794551192l);Test.assert(s.read("sf.batch.pending")["pending"]==true);
 var incoming=new NativeIncoming(s,service.transfer.base);Test.assert(incoming.admitFeed(c,1794551202l));
 Test.assert(c.packet.validation==1794551193l&&c.packet.rescheduled&&refreshId(c.packet));
 service.receive(200,refreshPacket("initial"));Test.assert(service.optionals==2);Test.assert(!incoming.admitFeed(c,1794551202l));
 Test.assert(c.packet!=null&&c.packet.validation==1794551193l&&c.packet.rescheduled&&refreshId(c.packet));
 var reopened=refreshCache(s);Test.assert(reopened.load(1794551202l)!=null&&reopened.packet.validation==1794551193l);
 log.debug("actual 200 callback→provisional stage→foreground admission B; older 200 preserves B through reopen");return true;
}
(:test,:typecheck(false)) function moreCurrentIntegrity(log){
 var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var bad=WatchUi.loadResource(Rez.JsonData.IntegrityCatalog);s.write("sf.obj."+bad["catalogDigest"],bad["catalog"]);
 var c=refreshCache(s);Test.assert(c.accept(refreshPacket("initial"),1794551202l));var original=c.packet.wireHash;
 var names=["badSchema","missingId","badIso","badPolicy","negativeId","badGeometry","boolPolicy","negativePolicy"];
 for(var i=0;i<names.size();i+=1){Test.assertMessage(!c.accept(integrityPacket(names[i]),1794551202l),names[i]);var r=refreshCache(s);Test.assert(r.load(1794551202l)!=null&&r.packet.wireHash.equals(original));}
 var t=new NativeTransfer("https://fixture.invalid/refresh",s);var raw=refreshPacket("initial");while(raw.length()<8193){raw+=" ";}raw=raw.substring(0,8193);Test.assert(!t.stage("feed",raw,null));
 log.debug("current schema, identity, UTC/ISO, policy, metadata and real-site geometry refusals preserve A; 8193-byte provisional transfer refused");return true;
}
(:test,:typecheck(false)) function moreWidePolicy(log){
 var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var raw=integrityPacket("wide");var p=new NativeBridgeFeed(raw,1794551202l,s);var c=refreshCache(s);
 Test.assert(c.accept(raw,1794551202l));Test.assert(c.packet.wireHash.equals("34c51270a36c44af598afbcb7d3a30e02fe9ba60236d2b69f8ba1a49612e7322"));
 Test.assert(p.document["launch"]["source_status_id"] instanceof NativeIntegerLexeme);
 Test.assert(p.document["launch"]["source_status_id"].text.equals("9223372036854775808"));
 Test.assert(p.interval(1794551202l)==315537897600l);p.advance(253402300799l);Test.assert(!p.stale);
 Test.assert(c.packet.document["refreshPolicy"]["normal_interval_seconds"]==315537897600l);
 Test.assert(c.packet.document["refreshPolicy"]["stale_cycles"]==315537897600l);
 var r=refreshCache(s);Test.assert(r.load(1794551202l)!=null);Test.assert(r.packet.wireHash.equals("34c51270a36c44af598afbcb7d3a30e02fe9ba60236d2b69f8ba1a49612e7322"));
 Test.assert(r.packet.document["refreshPolicy"]["normal_interval_seconds"]==315537897600l);
 log.debug("current packet retains existing overflow metadata/policy literal in raw SHA; bounded UTC calculation projection survives reopen");return true;
}
(:test,:typecheck(false)) function moreCorruptRecovery(log){
 var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var c=refreshCache(s);
 Test.assert(c.accept(refreshPacket("initial"),1794551202l));Test.assert(c.accept(refreshPacket("moved"),1794551202l));
 var marker=s.read("sf.commit");s.write("sf.feed."+marker["slot"]+".0","corrupt");var reopened=refreshCache(s);
 Test.assert(reopened.load(1794551202l)!=null);Test.assert(refreshId(reopened.packet));
 Test.assert(reopened.packet.validation==1794551192l&&!reopened.packet.rescheduled);
 log.debug("corrupted current committed raw reopens the prior complete A, with its own age and reschedule state");return true;
}

(:test,:typecheck(false)) function moreTypedMetadata(log){
 var d=refreshInputs();var store=new RefreshFaultStore(null);refreshSeed(store,d);
 var a=new NativeBridgeFeed(integrityPacket("nullId"),1794551202l,store);Test.assert(a.document["launch"]["source_status_id"]==null);
 var wide=new NativeBridgeFeed(integrityPacket("widePrecision"),1794551202l,store);
 Test.assert(wide.document["launch"]["timing"]["source_precision_id"] instanceof NativeIntegerLexeme);
 Test.assert(wide.document["launch"]["timing"]["source_precision_id"].text.equals("9223372036854775808"));
 Test.assert(!wide.utc(253402300800l));var c=refreshCache(store);Test.assert(c.accept(refreshPacket("initial"),1794551202l));
 var names=["boolId","quotedId","badUtc"];for(var i=0;i<names.size();i+=1){Test.assert(!c.accept(integrityPacket(names[i]),1794551202l));}
 var r=refreshCache(store);Test.assert(r.load(1794551202l)!=null&&r.packet.validation==1794551192l);
 log.debug("current nullable status and existing wide precision literal admit; bool/string status and out-of-range UTC reject without replacing A");return true;
}
(:test,:typecheck(false)) function moreNearLatchReopen(log){
 var d=refreshFinal();var store=new RefreshFaultStore(null);refreshSeed(store,d);var url="https://fixture.invalid/near";
 var c=new NativeCache(url,store);Test.assert(c.accept(refreshFinalPacket("exact"),1794576343l));
 c.packet.advance(1794579042l);Test.assert(!c.packet.stale);c.packet.advance(1794579043l);Test.assert(c.packet.stale);
 var r=new NativeCache(url,store);Test.assert(r.load(1794585344l)!=null);Test.assert(r.packet.stale);Test.assert(r.packet.interval(1794585344l)==3600);
 Test.assert(r.accept(refreshFinalPacket("exact"),1794585344l));Test.assert(r.packet.stale);
 Test.assert(r.accept(integrityPacket("finalRefresh"),1794585344l));Test.assert(!r.packet.stale&&r.packet.validation==1794585344l);
 var again=new NativeCache(url,store);Test.assert(again.load(1794585344l)!=null&&!again.packet.stale);
 log.debug("near stale latch survives T+1801 hourly exit, process reopen and old replay; newer source validation clears it");return true;
}

(:test,:typecheck(false)) function moreOmissionPreservesAge(log){
 var first=WatchUi.loadResource(Rez.JsonData.OmissionInitial);var omitted=WatchUi.loadResource(Rez.JsonData.OmissionOmitted);
 var store=new RefreshFaultStore(null);store.write("sf.obj."+first["catalogDigest"],first["catalog"]);store.write("sf.obj."+omitted["catalogDigest"],omitted["catalog"]);
 var c=new NativeCache("https://fixture.invalid/omission",store);Test.assert(c.accept(first["raw"],1800000000l));
 Test.assert(c.accept(omitted["raw"],1800003600l));Test.assert(c.packet.validation==1800000000l&&c.packet.stale);
 Test.assert(c.packet.launchId().equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"));
 var parsed=new NativeBridgeFeed(omitted["raw"],1800003600l,store);Test.assert(parsed.document["launch"]["status"].equals("pending"));
 Test.assert(parsed.document["publisher"]["selectionValidatedUtc"]==1800003600l);
 Test.assert(parsed.document["launch"]["source_validated_utc"]==1800000000l);
 var r=new NativeCache("https://fixture.invalid/omission",store);Test.assert(r.load(1800003600l)!=null&&r.packet.stale&&r.packet.validation==1800000000l);
 log.debug("actual producer omission: selected A remains pending with own old source epoch while publisher and another record advance");return true;
}
(:test,:typecheck(false)) function moreOfflineEmpty(log){
 Application.Properties.setValue("FeedBaseUrl","");var app=new SpaceFoxApp();var view=app.getInitialView()[0];
 Test.assert(view.packet==null&&view.context==null);var snap=view.snapshot();Test.assert(snap.countdown.equals("--:--:--")&&!snap.stale&&snap.remaining==null);
 Test.assert(snap.localTime.length()>0);Test.assert(view.settings.slots.size()==4);
 view.values={"steps"=>123,"energy"=>45,"heart"=>67,"stress"=>8,"battery"=>82,"calories"=>456};
 var image=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();view.onLayout(image.getDc());view.onUpdate(image.getDc());
 Test.assert(view.renderer.metricText(view.fitness,view.values,view.settings.slots[0],view.settings).equals("123"));
 Test.assert(view.renderer.metricText(view.fitness,view.values,view.settings.slots[1],view.settings).equals("45"));
 Test.assert(view.renderer.metricText(view.fitness,view.values,view.settings.slots[2],view.settings).equals("67"));
 Test.assert(view.renderer.metricText(view.fitness,view.values,view.settings.slots[3],view.settings).equals("8"));
 Test.assert(view.context==null&&view.packet==null&&!view.snapshot().stale);log.debug("actual empty-cache startup and graphics: local time/four controlled values, no schedule or stale invention");return true;
}
(:test,:typecheck(false)) function moreCurrentIsoLiterals(log){
 Test.assert(nativeSourceIso("2026-11-10T22:06:46Z",1794348406l,0));
 Test.assert(nativeSourceIso("2026-11-10T22:06:46.123456Z",1794348406l,123456));
 Test.assert(nativeSourceIso("2026-W46-2T00Z",1794268800l,0));
 Test.assert(nativeSourceIso("2020-W53-7T00Z",1609632000l,0));
 Test.assert(!nativeSourceIso("2021-W53-1T00Z",1794268800l,0));
 Test.assert(!nativeSourceIso("2026-11-10T22:06:46+24",1794348406l,0));
 Test.assert(!nativeSourceIso("2026-11-10T22:06:46Z",1794348407l,0));
 log.debug("captured ISO/subsecond and retained week-date literals preserve exact UTC; invalid week and mismatched epoch reject");return true;
}

(:test,:typecheck(false)) function moreCanonicalCurrent(log){
 var raw=unresolvedResource("real2");var doc=new NativeJson().parse(raw,8192);
 Test.assert(doc["launch"]["site_name"].equals("Chang’e 6 landing site"));
 var hash=new NativeCanonical();hash.emit(doc);Test.assert(hash.digest().equals("8b51bf813ede8599b87a4df380e7b1c1f4259675228bcce2b37fc518d9a39196"));
 var wide=integrityPacket("wide");var parsed=new NativeJson().parse(wide,8192);
 Test.assert(parsed["launch"]["source_status_id"] instanceof NativeIntegerLexeme);
 var wideHash=new NativeCanonical();wideHash.emit(parsed);Test.assert(wideHash.digest().equals("34c51270a36c44af598afbcb7d3a30e02fe9ba60236d2b69f8ba1a49612e7322"));
 log.debug("actual canonical SHA of real Unicode captured record and current overflow literal matches independent producer hashes");return true;
}

(:test,:typecheck(false)) function morePublisherFloor(log){
 var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var c=refreshCache(s);
 Test.assert(c.accept(refreshPacket("initial"),1794551202l));var hash=c.packet.wireHash;
 var names=["changedInstance","nullSelection","regressedOrigin"];for(var i=0;i<names.size();i+=1){Test.assert(!c.accept(integrityPacket(names[i]),1794551202l));}
 var empty=new NativeCache("",s);Test.assert(!empty.accept(refreshPacket("initial"),1794551202l));
 var r=refreshCache(s);Test.assert(r.load(1794551202l)!=null&&r.packet.wireHash.equals(hash)&&r.packet.validation==1794551192l);
 log.debug("changed publisher instance, null/regressing selection origin and empty namespace cannot replace accepted A");return true;
}
(:test,:typecheck(false)) function moreSourceIdentity(log){
 var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);
 var a=new NativeBridgeFeed(refreshPacket("initial"),1794551202l,s);var b=new NativeBridgeFeed(refreshPacket("moved"),1794551202l,s);
 Test.assert(refreshId(a)&&refreshId(b));Test.assert(a.document["launch"]["timing"]["nominal_utc"]==1794609900l);
 Test.assert(b.document["launch"]["timing"]["nominal_utc"]==1794611100l);
 Test.assert(a.bridge["site"]["sourcePosition"]["latitude"].equals("25.99677"));
 Test.assert(a.bridge["site"]["sourcePosition"]["longitude"].equals("-97.15799"));
 // The old unconditional null-point assertion is retired; qualified coordinates remain independent of model/operator.
 var c=refreshCache(s);Test.assert(c.accept(refreshPacket("initial"),1794551202l));
 Test.assert(c.accept(refreshPacket("moved"),1794551202l));var r=refreshCache(s);Test.assert(r.load(1794551202l)!=null&&r.packet.validation==1794551193l&&refreshId(r.packet));
 Test.assert(s.read("sf.obj."+a.bridge["catalogDigest"]) instanceof String);
 log.debug("captured A/B IDs, nominal UTC and unverified source coordinates match; no asserted event point; B metadata reopens");return true;
}
(:test,:typecheck(false)) function moreRescheduledStale(log){
 var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var c=refreshCache(s);
 Test.assert(c.accept(refreshPacket("initial"),1794551202l));Test.assert(c.accept(refreshPacket("moved"),1794551202l));
 c.packet.advance(1794561992l);Test.assert(!c.packet.stale&&c.packet.rescheduled);
 c.packet.advance(1794561993l);Test.assert(c.packet.stale&&c.packet.rescheduled&&refreshId(c.packet));
 var r=refreshCache(s);Test.assert(r.load(1794561993l)!=null&&r.packet.stale&&r.packet.rescheduled);
 log.debug("same selected launch retains reschedule independently through normal stale threshold and reopen");return true;
}
(:test,:typecheck(false)) function moreSdkThreeSlots(log){
 var d=refreshInputs();var s=new RefreshSdkStore();
 try{refreshSeed(s,d);var c=refreshCache(s);Test.assert(c.accept(refreshPacket("initial"),1794551202l));var one=s.read("sf.commit")["slot"];
  Test.assert(c.accept(refreshPacket("moved"),1794551202l));var two=s.read("sf.commit")["slot"];
  Test.assert(c.accept(refreshPacket("withdrawn"),1794551202l));var three=s.read("sf.commit")["slot"];
  Test.assert(one!=two&&one!=three&&two!=three);s.write("sf.feed."+three+".0","corrupt");
  var r=refreshCache(s);Test.assert(r.load(1794551202l)!=null&&r.packet.validation==1794551193l&&r.packet.rescheduled&&refreshId(r.packet));
 }finally{s.cleanup();}
 log.debug("actual SDK Storage rotates all three feed slots; corrupted C reopens complete B");return true;
}

(:typecheck(false)) function ascentPacket(name){
 var id=null;if(name.equals("ascentGood")){id=Rez.JsonData.IntegrityAscentGood;}
 else if(name.equals("ascentBadId")){id=Rez.JsonData.IntegrityAscentBadId;}else if(name.equals("ascentBadTarget")){id=Rez.JsonData.IntegrityAscentBadTarget;}
 else if(name.equals("ascentBadEnd")){id=Rez.JsonData.IntegrityAscentBadEnd;}else if(name.equals("ascentBadUrl")){id=Rez.JsonData.IntegrityAscentBadUrl;}
 else if(name.equals("ascentBadFuture")){id=Rez.JsonData.IntegrityAscentBadFuture;}if(id==null){throw new Lang.InvalidValueException("unknown ascent fixture");}
 return WatchUi.loadResource(id)["raw"];
}
(:test,:typecheck(false)) function moreSourcedAscent(log){
 var d=refreshFinal();var s=new RefreshFaultStore(null);refreshSeed(s,d);var raw=ascentPacket("ascentGood");
 var p=new NativeBridgeFeed(raw,1794576345l,s);Test.assert(p.document["launch"]["ascent_end"]["end_utc"]==1794585343l);
 Test.assert(p.launchId().equals("ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a"));
 var c=new NativeCache("https://fixture.invalid/ascent",s);Test.assert(c.accept(refreshFinalPacket("exact"),1794576345l));var hash=c.packet.recordHash;
 Test.assert(c.accept(raw,1794576345l));Test.assert(c.packet.recordHash.equals(hash));var r=new NativeCache("https://fixture.invalid/ascent",s);
 Test.assert(r.load(1794576345l)!=null&&r.packet.launchId().equals(p.launchId())&&r.packet.validation==1794576343l);
 var names=["ascentBadId","ascentBadTarget","ascentBadEnd","ascentBadUrl","ascentBadFuture"];
 for(var i=0;i<names.size();i+=1){var rejected=false;try{new NativeBridgeFeed(ascentPacket(names[i]),1794576345l,s);}catch(e){rejected=true;}Test.assertMessage(rejected,names[i]);}
 log.debug("current parser/cache admits same-ID sourced +1800 ascent-end, preserves source epoch and rejects five invalid bindings");return true;
}

(:typecheck(false)) class MoreCountingStore extends RefreshFaultStore {
 var feedWrites=0;
 function initialize(){RefreshFaultStore.initialize(null);}
 function write(key,value){if(key.find("sf.feed.")==0){feedWrites+=1;}RefreshFaultStore.write(key,value);}
}
(:test,:typecheck(false)) function moreSourceOnlyReuse(log){
 var d=refreshInputs();var s=new MoreCountingStore();refreshSeed(s,d);var c=refreshCache(s);
 Test.assert(c.accept(refreshPacket("initial"),1794551202l));Test.assert(c.accept(refreshPacket("moved"),1794551202l));
 var before=s.feedWrites;Test.assert(c.accept(refreshPacket("refresh"),1794551202l));
 Test.assert(s.feedWrites==before&&c.packet.validation==1794551194l&&c.packet.rescheduled);
 var r=refreshCache(s);Test.assert(r.load(1794551202l)!=null&&r.packet.validation==1794551194l&&r.packet.rescheduled);
 log.debug("source-only newer validation retains raw feed chunks without rewriting them and reopens same identity");return true;
}
(:test,:typecheck(false)) function moreGenericRenderer(log){
 var s=new RefreshFaultStore(null);unresolvedSeed(s);var p=new NativeBridgeFeed(unresolvedResource("real2"),1794551192l,s);
 var context=feedScene(p,1794551192l);var renderer=new SceneRenderer(null);renderer.prepare(context,new SceneSettings(null));
 Test.assert(context.point==null&&!renderer.pin&&renderer.model==NativeAssets.models["generic"]);
 Test.assert(context.rocket.equals("Chang'e Sample Ascender")&&context.site.equals("Apollo crater"));
 var technical=new NativeBridgeFeed(unresolvedResource("technical1"),1794551192l,s);var next=feedScene(technical,1794551192l);renderer.prepare(next,new SceneSettings(null));
 Test.assert(next.point==null&&!renderer.pin&&renderer.model==NativeAssets.models["generic"]&&next.operator.equals("SpaceX"));
 log.debug("actual current parser→context→renderer: captured unresolved names, generic model and no fabricated map point");return true;
}

(:test,:typecheck(false)) function moreNonfinitePosition(log){
 var d=refreshInputs();var store=new RefreshFaultStore(null);refreshSeed(store,d);var bad=WatchUi.loadResource(Rez.JsonData.IntegrityNanCatalog);
 store.write("sf.obj."+bad["catalogDigest"],bad["catalog"]);var c=refreshCache(store);Test.assert(c.accept(refreshPacket("initial"),1794551202l));
 var raw=WatchUi.loadResource(Rez.JsonData.IntegrityNanGeometry)["raw"];Test.assert(!c.accept(raw,1794551202l));
 var r=refreshCache(store);Test.assert(r.load(1794551202l)!=null&&refreshId(r.packet)&&r.packet.validation==1794551192l);
 log.debug("nonfinite source-position text rejects current schema3 candidate without replacing accepted A");return true;
}
(:typecheck(false)) class MoreFullStore extends RefreshFaultStore {
 var full=false;var firedFull=false;
 function initialize(){RefreshFaultStore.initialize(null);}
 function write(key,value){if(full){full=false;firedFull=true;throw new Lang.StorageFullException("controlled capacity failure");}RefreshFaultStore.write(key,value);}
}
(:test,:typecheck(false)) function moreStorageFull(log){
 var d=refreshInputs();var s=new MoreFullStore();refreshSeed(s,d);var c=refreshCache(s);
 Test.assert(c.accept(refreshPacket("initial"),1794551202l));s.full=true;
 Test.assert(!c.accept(refreshPacket("moved"),1794551202l)&&s.firedFull);
 var r=refreshCache(s);Test.assert(r.load(1794551202l)!=null&&refreshId(r.packet)&&r.packet.validation==1794551192l);
 log.debug("injected SDK StorageFullException at a reached feed-cache write preserves complete A on reopen");return true;
}

(:test,:typecheck(false)) function moreMinuteRefresh(log){
 var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var c=refreshCache(s);
 Test.assert(c.accept(refreshPacket("initial"),1794551202l));var p=c.packet;
 Test.assert(p.target()==null&&p.refreshTarget()==1794609900l);
 Test.assert(p.interval(1794602699l)==3600&&p.interval(1794602700l)==900);
 Test.assert(p.interval(1794611700l)==900&&p.interval(1794611701l)==3600);
 var contextStore=new RefreshFaultStore(null);refreshSeed(contextStore,d);var cc=refreshCache(contextStore);
 Test.assert(cc.accept(refreshPacket("initial"),1794551202l));
 Test.assert(cc.accept(WatchUi.loadResource(Rez.JsonData.IntegrityMinuteContext)["raw"],1794551202l));
 Test.assert(!cc.packet.rescheduled&&cc.packet.refreshTarget()==1794609900l);
 var contextReopen=refreshCache(contextStore);Test.assert(contextReopen.load(1794551202l)!=null&&!contextReopen.packet.rescheduled);
 var marker=s.read("sf.commit");marker["prior"][0]["launch"]["timing"].remove("refresh_utc");marker["priorHash"]=c.priorHash(marker["prior"]);marker["seal"]=c.seal(marker);s.write("sf.commit",marker);
 var r=refreshCache(s);Test.assert(r.load(1794602700l)!=null&&r.packet.refreshTarget()==1794609900l);
 Test.assert(r.packet.interval(1794602700l)==900);
 NativeForegroundApp.savePlan(r,r.packet.document["refreshPolicy"]);
 var plan=s.read("sf.transfer.plan");Test.assert(plan["target"]==1794609900l);
 s.write("sf.transfer.ready",{"base"=>r.base,"accepted"=>true});var t=new NativeTransfer(r.base,s);
 Test.assert(t.interval(1794602699l)==3600&&t.interval(1794602700l)==900&&t.interval(1794611701l)==3600);
 Test.assert(c.accept(refreshPacket("moved"),1794551202l));Test.assert(c.accept(refreshPacket("withdrawn"),1794551202l));
 Test.assert(c.packet.refreshTarget()==null&&c.packet.interval(1794602700l)==3600);
 var nearRaw=WatchUi.loadResource(Rez.JsonData.IntegrityMinuteNear)["raw"];
 var ns=new RefreshFaultStore(null);refreshSeed(ns,d);var nc=refreshCache(ns);Test.assert(nc.accept(nearRaw,1794602700l));
 nc.packet.advance(1794605399l);Test.assert(!nc.packet.stale);nc.packet.advance(1794605400l);Test.assert(nc.packet.stale);
 var slept=refreshCache(ns);Test.assert(slept.load(1794611701l)!=null&&slept.packet.stale&&slept.packet.interval(1794611701l)==3600);
 Test.assert(slept.accept(nearRaw,1794611701l)&&slept.packet.stale);
 var newer=WatchUi.loadResource(Rez.JsonData.IntegrityMinuteNewer)["raw"];
 Test.assert(slept.accept(newer,1794611701l)&&!slept.packet.stale&&slept.packet.validation==1794611701l);
 var date=new NativeBridgeFeed(WatchUi.loadResource(Rez.JsonData.IntegrityMinuteDate)["raw"],1794602700l,ns);
 var window=new NativeBridgeFeed(WatchUi.loadResource(Rez.JsonData.IntegrityMinuteWindow)["raw"],1794602700l,ns);
 Test.assert(date.refreshTarget()==null&&date.interval(1794609900l)==3600);
 Test.assert(window.refreshTarget()==null&&window.interval(1794609900l)==3600);
 log.debug("captured MIN: inclusive window, older projection reopen and transfer plan; technical source epoch near stale 2699/2700 and slept-through exit");return true;
}
