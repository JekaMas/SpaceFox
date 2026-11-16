import Toybox.Application;
import Toybox.Lang;
import Toybox.WatchUi;
import Toybox.System;
import Toybox.Background;
import Toybox.Time;
import Toybox.Test;
(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}
(:typecheck(false)) class TestStore { var data;var values={};var reads=0;var writes=0;function initialize(d){data=d;}function read(key){reads+=1;return key.equals("sf.obj."+data["catalogDigest"])?data["catalog"]:values[key];}function write(key,value){writes+=1;values[key]=value;}function remove(key){values.remove(key);} }
(:test,:typecheck(false)) function ascentAdmissionPositive(log){var data=WatchUi.loadResource(Rez.JsonData.FinalPackets);var p=new NativeBridgeFeed(data["ascentGood"],1794576345,new TestStore(data));Test.assertEqual(p.document["launch"]["ascent_end"]["end_utc"],1794585343);Test.assertEqual(p.launchId(),"ll2:launch:ef9850ad-1096-425b-9d27-f7bbd186e61a");var store=new TestStore(data);var cache=new NativeCache("https://fixture.invalid/ascent",store);Test.assert(cache.accept(data["exact"],1794576345));var originalHash=cache.packet.recordHash;Test.assert(cache.accept(data["ascentGood"],1794576345));Test.assertEqual(cache.packet.recordHash,originalHash);var reopened=new NativeCache("https://fixture.invalid/ascent",store);Test.assert(reopened.load(1794576345)!=null);Test.assertEqual(reopened.packet.launchId(),p.launchId());Test.assertEqual(reopened.packet.validation,1794576343);Test.assert(!reopened.accept(data["ascentBadTarget"],1794576345));Test.assertEqual(reopened.packet.launchId(),p.launchId());return true;}
(:test,:typecheck(false)) function ascentAdmissionNegative(log){var data=WatchUi.loadResource(Rez.JsonData.FinalPackets);var names=["ascentBadId","ascentBadTarget","ascentBadEnd","ascentBadUrl","ascentBadFuture"];for(var i=0;i<names.size();i+=1){var rejected=false;try{new NativeBridgeFeed(data[names[i]],1794576345,new TestStore(data));}catch(e){rejected=true;}Test.assert(rejected);}return true;}
