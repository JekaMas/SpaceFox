import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Background;
import Toybox.Time;
(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}
import Toybox.Application;
import Toybox.Graphics;
import Toybox.Lang;
import Toybox.Test;
import Toybox.WatchUi;

// Test-only Storage substitute: copy values on each operation, like a durable
// serialization boundary. Fault index is armed only after accepted A is loaded.
(:typecheck(false))
class RefreshFaultStore {
    var values={}; var reads=0; var writes=0; var operations=0;
    var failAt=0; var fired=false;
    function initialize(seed){if(seed!=null){values=copy(seed);}}
    function copy(value){
        if(value instanceof Dictionary){var out={};var keys=value.keys();for(var i=0;i<keys.size();i+=1){out[keys[i]]=copy(value[keys[i]]);}return out;}
        if(value instanceof Array){var out=[];for(var i=0;i<value.size();i+=1){out.add(copy(value[i]));}return out;}
        return value;
    }
    function touch(){operations+=1;if(failAt>0&&operations==failAt){fired=true;throw new Lang.InvalidValueException("controlled feed-cache interruption");}}
    function read(key){reads+=1;touch();return values.hasKey(key)?copy(values[key]):null;}
    function write(key,value){writes+=1;touch();values[key]=copy(value);}
    function remove(key){writes+=1;touch();values.remove(key);}
    function arm(index){operations=0;failAt=index;fired=false;}
    function disarm(){failAt=0;}
    function snapshot(){return copy(values);}
}

// This test app has its own UUID. Only keys written by this wrapper are removed.
(:typecheck(false))
class RefreshSdkStore {
    var inner;var keys=[];var reads=0;var writes=0;
    function initialize(){inner=new NativeStore();}
    function read(key){reads+=1;return inner.read(key);}
    function write(key,value){writes+=1;if(keys.indexOf(key)<0){keys.add(key);}inner.write(key,value);}
    function remove(key){writes+=1;inner.remove(key);}
    function cleanup(){for(var i=0;i<keys.size();i+=1){inner.remove(keys[i]);}}
}

(:typecheck(false)) function refreshInputs(){return null;}
(:typecheck(false)) function refreshFinal(){return WatchUi.loadResource(Rez.JsonData.FinalCatalog);}
(:typecheck(false)) function refreshPacket(name){
    var id=null;
    if(name.equals("initial")){id=Rez.JsonData.RefreshInitial;}
    else if(name.equals("unchanged")){id=Rez.JsonData.RefreshUnchanged;}
    else if(name.equals("moved")){id=Rez.JsonData.RefreshMoved;}
    else if(name.equals("refresh")){id=Rez.JsonData.RefreshRefresh;}
    else if(name.equals("withdrawn")){id=Rez.JsonData.RefreshWithdrawn;}
    else if(name.equals("withdrawn_refresh")){id=Rez.JsonData.RefreshWithdrawnRefresh;}
    else if(name.equals("different")){id=Rez.JsonData.RefreshDifferent;}
    if(id==null){throw new Lang.InvalidValueException("unknown refresh fixture");}
    return WatchUi.loadResource(id)["raw"];
}
(:typecheck(false)) function refreshFinalPacket(name){
    var id=name.equals("exact")?Rez.JsonData.FinalExact:Rez.JsonData.FinalInvalid;
    return WatchUi.loadResource(id)["raw"];
}
(:typecheck(false)) function refreshSeed(store,data){
    if(data!=null){store.write("sf.obj."+data["catalogDigest"],data["catalog"]);return;}
    var ids=[Rez.JsonData.RefreshCatalogInitial,Rez.JsonData.RefreshCatalogDifferent];
    for(var i=0;i<ids.size();i+=1){var row=WatchUi.loadResource(ids[i]);store.write("sf.obj."+row["catalogDigest"],row["catalog"]);}
}
(:typecheck(false)) function refreshCache(store){return new NativeCache("https://fixture.invalid/refresh",store);}
(:typecheck(false)) function refreshId(p){return p.launchId().equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b");}

(:test,:typecheck(false)) function refreshColdCache(log){
    var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var before=s.writes;
    var c=refreshCache(s);Test.assert(c.load(1794551202l)==null);Test.assert(c.packet==null);Test.assertEqual(s.writes,before);
    log.debug("empty accepted cache remains empty; bundled catalog cannot invent a launch");return true;
}

(:test,:typecheck(false)) function refreshCacheSequence(log){
    var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var c=refreshCache(s);
    var accepted=c.accept(refreshPacket("initial"),1794551202l);log.debug("cache initial accepted="+accepted+" failure="+c.failure+" reason="+c.failureReason+" id="+(c.packet==null?"null":c.packet.launchId()));Test.assert(accepted);Test.assert(refreshId(c.packet));
    Test.assert(c.packet.validation==1794551192l);Test.assert(!c.packet.rescheduled);
    var writes=s.writes;Test.assert(c.accept(refreshPacket("initial"),1794551202l));Test.assertEqual(s.writes,writes);
    Test.assert(c.accept(refreshPacket("moved"),1794551202l));Test.assert(refreshId(c.packet));
    Test.assert(c.packet.validation==1794551193l);Test.assert(c.packet.rescheduled);
    var reopened=refreshCache(s);Test.assert(reopened.load(1794551202l)!=null);Test.assert(refreshId(reopened.packet));
    Test.assert(reopened.packet.validation==1794551193l);Test.assert(reopened.packet.rescheduled);
    Test.assert(reopened.accept(refreshPacket("refresh"),1794551202l));Test.assert(reopened.packet.rescheduled);
    Test.assert(reopened.accept(refreshPacket("withdrawn"),1794551202l));Test.assert(reopened.packet.rescheduled);
    var unknown=new NativeBridgeFeed(refreshPacket("withdrawn"),1794551202l,s);
    Test.assertEqual(unknown.document["launch"]["timing"]["precision"],"unknown");
    Test.assert(unknown.document["launch"]["timing"]["exact_utc"]==null);
    Test.assert(reopened.accept(refreshPacket("withdrawn_refresh"),1794551202l));Test.assert(reopened.packet.rescheduled);
    Test.assert(reopened.accept(refreshPacket("different"),1794551202l));
    Test.assertEqual(reopened.packet.launchId(),"ll2:launch:00000000-0000-4000-8000-000000000002");
    Test.assert(!reopened.packet.rescheduled);var final=refreshCache(s);Test.assert(final.load(1794551202l)!=null);
    Test.assertEqual(final.packet.launchId(),"ll2:launch:00000000-0000-4000-8000-000000000002");
    log.debug("current A, exact replay, moved B, source refresh, withdrawal and new identity survive admission/reopen");return true;
}

(:test,:typecheck(false)) function refreshCacheRefusals(log){
    var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var c=refreshCache(s);
    Test.assert(c.accept(refreshPacket("initial"),1794551202l));Test.assert(c.accept(refreshPacket("moved"),1794551202l));
    var writes=s.writes;Test.assert(!c.accept(refreshPacket("initial"),1794551202l));Test.assertEqual(s.writes,writes);
    Test.assert(!c.accept(refreshPacket("unchanged"),1794551202l));Test.assertEqual(s.writes,writes);
    var r=refreshCache(s);Test.assert(r.load(1794551202l)!=null);Test.assert(refreshId(r.packet));
    Test.assert(r.packet.validation==1794551193l);Test.assert(r.packet.rescheduled);
    Test.assertEqual(r.packet.wireHash,"bd77f303a7e9dfcf4c03e420140fd1466800051e71efec5bdfe16c61be20be18");
    log.debug("older generation and same-generation conflicting bytes cannot replace B");return true;
}

(:test,:typecheck(false)) function refreshSourceAge(log){
    var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var c=refreshCache(s);
    Test.assert(c.accept(refreshPacket("initial"),1794551202l));c.packet.advance(1794561991l);Test.assert(!c.packet.stale);
    c.packet.advance(1794561992l);Test.assert(c.packet.stale);Test.assert(refreshId(c.packet));
    var r=refreshCache(s);Test.assert(r.load(1794561992l)!=null);Test.assert(r.packet.stale);
    var writes=s.writes;Test.assert(r.accept(refreshPacket("initial"),1794561992l));Test.assertEqual(s.writes,writes);Test.assert(r.packet.stale);
    Test.assert(r.accept(refreshPacket("unchanged"),1794561992l));Test.assert(!r.packet.stale);
    Test.assert(r.packet.validation==1794551193l);Test.assert(!r.packet.rescheduled);
    log.debug("normal age 10799/10800, durable old replay and strictly newer validation");return true;
}

(:test,:typecheck(false)) function refreshNearAndClock(log){
    var d=refreshFinal();var s=new RefreshFaultStore(null);refreshSeed(s,d);var p=new NativeBridgeFeed(refreshFinalPacket("exact"),1794576343l,s);
    Test.assertEqual(p.interval(1794576342l),3600);Test.assertEqual(p.interval(1794576343l),900);
    Test.assertEqual(p.interval(1794585343l),900);Test.assertEqual(p.interval(1794585344l),3600);
    p.advance(1794579042l);Test.assert(!p.stale);p.advance(1794579043l);Test.assert(p.stale);
    p.advance(1794585344l);Test.assert(p.stale);Test.assertEqual(p.interval(1794585344l),3600);
    var c=new ScheduleState(1794583543l,"exact");
    Test.assertEqual(c.display(1794407020l,true),"T- 49:02:03");
    Test.assertEqual(c.display(1794583484l,true),"T- 00:00:59");
    Test.assertEqual(c.display(1794583542l,true),"T- 00:00:01");
    Test.assertEqual(c.display(1794583543l,true),"T+ 00:00:00");
    Test.assertEqual(c.display(1794584443l,true),"T+ 00:15:00");
    log.debug("inclusive cadence edges, near stale latch on exit, clock-derived long/final/elapsed values");return true;
}

(:test,:typecheck(false)) function refreshNamespaces(log){
    var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);
    var a=refreshCache(s);Test.assert(a.accept(refreshPacket("initial"),1794551202l));Test.assert(a.accept(refreshPacket("moved"),1794551202l));
    var b=new NativeCache("https://fixture.invalid/other",s);Test.assert(b.accept(refreshPacket("initial"),1794551202l));
    var again=refreshCache(s);again.load(1794551202l);Test.assert(!again.accept(refreshPacket("initial"),1794551202l));
    Test.assert(again.accept(refreshPacket("moved"),1794551202l));Test.assert(again.packet.validation==1794551193l);
    log.debug("publisher floor for each URL survives switching; exact current generation remains admissible");return true;
}

(:test,:typecheck(false)) function refreshFeedCacheFaults(log){
    var d=refreshInputs();var seed=new RefreshFaultStore(null);refreshSeed(seed,d);var a=refreshCache(seed);
    Test.assert(a.accept(refreshPacket("initial"),1794551202l));var snapshot=seed.snapshot();
    var baseline=new RefreshFaultStore(snapshot);var normal=refreshCache(baseline);Test.assert(normal.load(1794551202l)!=null);
    baseline.arm(0);Test.assert(normal.accept(refreshPacket("moved"),1794551202l));var count=baseline.operations;Test.assert(count>0);
    var reached=0;for(var i=1;i<=count;i+=1){
        var store=new RefreshFaultStore(snapshot);var c=refreshCache(store);Test.assert(c.load(1794551202l)!=null);
        store.arm(i);c.accept(refreshPacket("moved"),1794551202l);Test.assert(store.fired);reached+=1;store.disarm();
        var r=refreshCache(store);Test.assert(r.load(1794551202l)!=null);Test.assert(refreshId(r.packet));
        if(r.packet.validation==1794551192l){Test.assert(!r.packet.rescheduled);Test.assertEqual(r.packet.wireHash,"7ac00c3289677eb4f1aaa2dc1ef9c8f5e57467d91b8c0dd0d65c84d53801291e");}
        else{Test.assert(r.packet.validation==1794551193l);Test.assert(r.packet.rescheduled);Test.assertEqual(r.packet.wireHash,"bd77f303a7e9dfcf4c03e420140fd1466800051e71efec5bdfe16c61be20be18");}
    }
    Test.assertEqual(reached,count);log.debug("feed-cache fault indices reached="+reached+"; every reopen is exact A or B");return true;
}

(:test,:typecheck(false)) function refreshParserRejects(log){
    var d=refreshFinal();var s=new RefreshFaultStore(null);refreshSeed(s,d);var c=new NativeCache("https://fixture.invalid/parser",s);
    Test.assert(c.accept(refreshFinalPacket("exact"),1794576343l));var prior=c.packet.wireHash;var writes=s.writes;
    Test.assert(!c.accept(refreshFinalPacket("invalid"),1794576343l));Test.assertEqual(s.writes,writes);
    var r=new NativeCache("https://fixture.invalid/parser",s);Test.assert(r.load(1794576343l)!=null);
    Test.assertEqual(r.packet.wireHash,prior);Test.assert(r.packet.validation==1794576343l);
    log.debug("current contradictory time packet rejected without replacing accepted cache");return true;
}

(:test,:typecheck(false)) function refreshSdkStorage(log){
    var d=refreshInputs();var s=new RefreshSdkStore();
    try{refreshSeed(s,d);var c=refreshCache(s);Test.assert(c.load(1794551202l)==null);
        Test.assert(c.accept(refreshPacket("initial"),1794551202l));Test.assert(c.accept(refreshPacket("moved"),1794551202l));
        var r=refreshCache(s);Test.assert(r.load(1794551202l)!=null);Test.assert(refreshId(r.packet));
        Test.assert(r.packet.validation==1794551193l);Test.assert(r.packet.rescheduled);
    }finally{s.cleanup();}
    log.debug("actual SDK Storage A-to-B and durable reopen, scoped test UUID");return true;
}

// Exact bytes were built locally from the retained current producer; one
// historical record has only its status changed for this selection test.
(:typecheck(false)) function unresolvedResource(name){
    var id=null;
    if(name.equals("emptyCatalog")){id=Rez.JsonData.UnresolvedEmptyCatalog;}
    else if(name.equals("realCatalog")){id=Rez.JsonData.UnresolvedRealCatalog;}
    else if(name.equals("technicalCatalog")){id=Rez.JsonData.UnresolvedTechnicalCatalog;}
    else if(name.equals("empty1")){id=Rez.JsonData.UnresolvedEmpty1;}
    else if(name.equals("real2")){id=Rez.JsonData.UnresolvedReal2;}
    else if(name.equals("empty3")){id=Rez.JsonData.UnresolvedEmpty3;}
    else if(name.equals("real4")){id=Rez.JsonData.UnresolvedReal4;}
    else if(name.equals("technical1")){id=Rez.JsonData.UnresolvedTechnical1;}
    else if(name.equals("realScene")){id=Rez.JsonData.UnresolvedRealScene;}
    else if(name.equals("technicalScene")){id=Rez.JsonData.UnresolvedTechnicalScene;}
    if(id==null){throw new Lang.InvalidValueException("unknown unresolved fixture");}
    return WatchUi.loadResource(id)["raw"];
}
(:typecheck(false)) function unresolvedSeed(s){
    s.write("sf.obj.83d62b40e5b3930b4c61ae7d8bb7d72ebcacd8a02fa3b7060baeef843fcabfb7",unresolvedResource("emptyCatalog"));
    s.write("sf.obj.160a681b17d814784a1796e707b3d14c520f32659b78c482dadc5e4ffde4fe46",unresolvedResource("realCatalog"));
    s.write("sf.obj.28ca28b1c56266709ea1be0a42966cbe786d416d6bff876a09d59d54cd5d13d1",unresolvedResource("technicalCatalog"));
    s.write("sf.obj.41abf304fe69c7ed2dd628e6946dbe48256e1919e375de41a0fdffa48cd4ff3f",unresolvedResource("realScene"));
    s.write("sf.obj.6f416f909314f13613e0d0f5bea19d0f2bd6c63d4180560a2557966e74acbf08",unresolvedResource("technicalScene"));
}
(:test,:typecheck(false)) function refreshUnresolvedSequence(log){
    var s=new RefreshFaultStore(null);unresolvedSeed(s);var c=new NativeCache("https://fixture.invalid/unresolved",s);
    Test.assert(c.accept(unresolvedResource("empty1"),1794551192l));Test.assert(c.packet.launchId()==null);
    Test.assert(c.accept(unresolvedResource("real2"),1794551192l));
    Test.assertEqual(c.packet.launchId(),"ll2:launch:a6bc9339-1a98-4483-9cdd-738768401c2e");
    var a=new NativeCache("https://fixture.invalid/unresolved",s);Test.assert(a.load(1794551192l)!=null);
    Test.assertEqual(a.packet.launchId(),"ll2:launch:a6bc9339-1a98-4483-9cdd-738768401c2e");
    Test.assert(a.accept(unresolvedResource("empty3"),1794551192l));Test.assert(a.packet.launchId()==null);
    Test.assert(a.accept(unresolvedResource("real4"),1794551192l));
    var r=new NativeCache("https://fixture.invalid/unresolved",s);Test.assert(r.load(1794551192l)!=null);
    Test.assertEqual(r.packet.launchId(),"ll2:launch:a6bc9339-1a98-4483-9cdd-738768401c2e");
    Test.assert(r.packet.validation==1794551192l);Test.assert(r.packet.presentation.point==null);
    log.debug("current producer→native cache empty/nonempty generations 1/2/3/4; real unresolved historical record with technical status");return true;
}
(:test,:typecheck(false)) function refreshUnresolvedScene(log){
    var s=new RefreshFaultStore(null);unresolvedSeed(s);
    var p=new NativeBridgeFeed(unresolvedResource("real2"),1794551192l,s);var row=p.document["launch"];
    Test.assertEqual(p.launchId(),"ll2:launch:a6bc9339-1a98-4483-9cdd-738768401c2e");
    Test.assertEqual(row["configuration_id"],"ll2:configuration:515");Test.assertEqual(row["site_id"],"ll2:site:233");
    log.debug("unresolved nominal="+row["timing"]["nominal_utc"]+" config="+row["configuration_name"]+" validation="+p.validation);Test.assert(row["timing"]["nominal_utc"]==1717457880l);Test.assertEqual(row["configuration_name"],"Chang'e Sample Ascender");
    Test.assertEqual(row["operator_name"],"China National Space Administration");Test.assertEqual(row["site_name"],"Chang’e 6 landing site");
    var context=feedScene(p,1794551192l);Test.assert(context.point==null);Test.assertEqual(context.modelId,"ll2:configuration:515");
    Test.assertEqual(context.rocket,"Chang'e Sample Ascender");Test.assertEqual(context.site,"Apollo crater");
    Test.assertEqual(p.bridge["selection"]["sha256"],"41abf304fe69c7ed2dd628e6946dbe48256e1919e375de41a0fdffa48cd4ff3f");
    var scene=new NativeSfrBuild(s,"https://fixture.invalid/unresolved",p);Test.assert(scene.scene["position"]==null);
    Test.assert(scene.scene["roles"]["rocket"]==null);Test.assert(scene.scene["roles"]["map"]==null);
    var t=new NativeBridgeFeed(unresolvedResource("technical1"),1794551192l,s);var tr=t.document["launch"];
    Test.assertEqual(tr["configuration_id"],"ll2:configuration:999999");Test.assertEqual(tr["operator_id"],"ll2:organization:999999");Test.assertEqual(tr["site_id"],"ll2:site:999999");
    Test.assertEqual(tr["configuration_name"],"Starship V3");Test.assertEqual(tr["operator_name"],"SpaceX");Test.assertEqual(tr["site_name"],"Orbital Launch Pad 2");
    Test.assert(tr["timing"]["nominal_utc"]==1794609900l);var tc=feedScene(t,1794551192l);
    Test.assert(tc.point==null);Test.assertEqual(tc.operator,"SpaceX");Test.assertEqual(tc.modelId,"ll2:configuration:999999");
    Test.assertEqual(t.bridge["selection"]["sha256"],"6f416f909314f13613e0d0f5bea19d0f2bd6c63d4180560a2557966e74acbf08");
    var ts=new NativeSfrBuild(s,"https://fixture.invalid/unresolved",t);Test.assert(ts.scene["position"]==null);
    Test.assert(ts.scene["roles"]["rocket"]==null);Test.assert(ts.scene["roles"]["map"]==null);
    log.debug("current producer→NativeBridgeFeed→feedScene→NativeSfrBuild.begin: exact captured text/UTC, unresolved IDs, no point or bound rocket/map; no drawing");return true;
}
(:test,:typecheck(false)) function refreshJsonRefusals(log){
    var malformed=["{\"x\":1,\"x\":2}","[01]","[true,]","[1]x"];
    for(var i=0;i<malformed.size();i+=1){var rejected=false;try{new NativeJson().parse(malformed[i],8192);}catch(e){rejected=true;}Test.assertMessage(rejected,"current parser accepted malformed fixture "+i);}
    var hash=new NativeWireHash();hash.put(refreshPacket("initial"));
    Test.assertEqual(hash.digest(),"7ac00c3289677eb4f1aaa2dc1ef9c8f5e57467d91b8c0dd0d65c84d53801291e");
    log.debug("existing duplicate, leading-zero, incomplete and trailing grammar literals rejected; current packet SHA agrees");return true;
}

// Callback substitution stops before Garmin Background.exit while exercising
// the real service response handler and real transfer/cache classes.
(:typecheck(false)) class RefreshCallbackService extends FeedService {
    var finishes=0;
    function finish() as Void {finishes+=1;}
}
(:test,:typecheck(false)) function refreshTransferBoundaries(log){
    var s=new RefreshFaultStore(null);var t=new NativeTransfer("https://fixture.invalid/refresh",s);
    s.write("sf.transfer.ready",{"base"=>t.base,"accepted"=>true});
    s.write("sf.transfer.plan",{"base"=>t.base,"target"=>1794583543l,"policy"=>[3600,900,null]});
    Test.assertEqual(t.interval(1794576342l),3600);Test.assertEqual(t.interval(1794576343l),900);
    Test.assertEqual(t.interval(1794585343l),900);Test.assertEqual(t.interval(1794585344l),3600);
    t.lastAttempt=1794576342l;Test.assert(t.nextWake(1794576342l)==1794576343l);
    t.lastAttempt=1794585343l;Test.assert(t.nextWake(1794585343l)==1794585344l);
    s.write("sf.transfer.plan",{"base"=>t.base,"target"=>null,"policy"=>[3600,900,null]});
    Test.assertEqual(t.interval(1794585344l),3600);
    s.write("sf.transfer.plan",{"base"=>t.base,"target"=>null,"policy"=>[3600,900,300]});
    Test.assertEqual(t.interval(1794585344l),300);
    log.debug("transfer: inclusive near boundaries, next wake transitions, unknown hourly and explicit fast policy");return true;
}
(:test,:typecheck(false)) function refreshNotModifiedCallback(log){
    var d=refreshInputs();var s=new RefreshFaultStore(null);refreshSeed(s,d);var c=refreshCache(s);
    Test.assert(c.accept(refreshPacket("initial"),1794551202l));var wire=c.packet.wireHash;
    var service=new RefreshCallbackService();service.transfer=new NativeTransfer("https://fixture.invalid/refresh",s);
    service.receive(304,null);Test.assertEqual(service.finishes,1);
    var r=refreshCache(s);Test.assert(r.load(1794561992l)!=null);Test.assertEqual(r.packet.wireHash,wire);
    Test.assert(r.packet.validation==1794551192l);Test.assert(r.packet.stale);
    Test.assertEqual(s.read("sf.sync.status")["code"],304);
    log.debug("actual 304 response handler keeps accepted record validation and stale threshold; injected finish boundary");return true;
}

(:test,:typecheck(false)) class RefreshViewClock extends WatchClock {
    var now=1794551202;
    function utcSeconds() as Number {return now;}
    function localTimeText() as String {return "08:00";}
}
(:test,:typecheck(false)) function refreshOfflineView(log){
    var data=refreshInputs();var store=new RefreshFaultStore(null);refreshSeed(store,data);
    var cache=refreshCache(store);Test.assert(cache.accept(refreshPacket("initial"),1794551202l));
    var clock=new RefreshViewClock();var view=new SpaceFoxView(clock,new ScheduleState(null,"empty"));
    view.setPacket(cache.packet);var image=Graphics.createBufferedBitmap({:width=>390,:height=>390}).get();
    view.onLayout(image.getDc());var loads=view.renderer.resourceLoads;var reads=store.reads;var writes=store.writes;
    view.onUpdate(image.getDc());Test.assertEqual(view.snapshot().countdown,"T- 16:18:18");
    view.onEnterSleep();clock.now+=7200;view.onExitSleep();view.onUpdate(image.getDc());
    Test.assertEqual(view.snapshot().countdown,"T- 14:18:18");Test.assertEqual(view.renderer.resourceLoads,loads);
    Test.assertEqual(store.reads,reads);Test.assertEqual(store.writes,writes);
    Test.assertEqual(view.context.launchId,"ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b");
    log.debug("current parsed packet, real buffered Graphics, two-hour logical sleep/wake: clock-derived countdown; no cache-adapter I/O or renderer resource reload");return true;
}

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
 Test.assert(feedScene(a,1794551202l).point==null);var c=refreshCache(s);Test.assert(c.accept(refreshPacket("initial"),1794551202l));
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
