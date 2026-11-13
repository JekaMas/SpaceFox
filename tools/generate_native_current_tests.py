#!/usr/bin/env python3
"""Current schema3/SFR1M native grammar, source-age and atomic cache cases.

The supplied bundle must come from the current producer. The source launch is
retained real metadata. Negative cases mutate schema/provenance only; the 8KiB
case repeats its actual mission name as a labeled transport density fixture.
Memory adapters in these direct cases do not prove ordinary persisted heap.
"""
import argparse,copy,hashlib,json,sys
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools import native_full_visual_runtime as runtime
from tools.native_current_runtime import selected_files
from tools.spacefox.catalog import canonical_bytes
EXPECTED=['currentEnvelope','currentWideRecovery','currentSourceAge','currentAtomicRecovery','currentSceneGrammar','currentMotionGrammar']
def source(profile):
 files,feed,route,_=selected_files(profile)
 root=json.loads(files[feed['visualSelection']['path']]);rocket=json.loads(files[root['roles']['rocket']['descriptor']['path']])
 def text(v):return runtime.literal(v.decode() if isinstance(v,bytes) else v)
 invalid=[]
 for key,value in [('schemaVersion',1),('schemaVersion',2),('schemaVersion',4),('rendererProfile','SFR1'),('rendererProfile','SFV1'),('compatibility',{}),('zzzLateRoot',True),('globeSelection',feed['visualSelection']),('globeTransfer',feed['nativeTransfer'])]:
  bad=copy.deepcopy(feed);bad[key]=value;invalid.append(canonical_bytes(bad).decode())
 wide=copy.deepcopy(feed);wide['launch']['mission_name']='';missing=8192-len(canonical_bytes(wide));name=feed['launch']['mission_name'] or feed['launch']['configuration_name'];wide['launch']['mission_name']=(name*(missing//len(name)+1))[:missing]
 if len(canonical_bytes(wide))!=8192:raise ValueError('density fixture requires ASCII source name')
 fresh=copy.deepcopy(wide);fresh['publisher']['generation']+=1;fresh['publisher']['selectionValidatedUtc']+=3600;fresh['launch']['source_validated_utc']+=3600
 changed=copy.deepcopy(fresh);changed['publisher']['generation']+=1;changed['launch']['mission_name']=feed['launch']['mission_name']
 roots=[]
 for key,value in [('schemaVersion',2),('rendererProfile','SFR1'),('layoutRevision','native-04-v1'),('layoutRevision','native-04-globe-motion-v1'),('zzzLateRoot',{})]:
  bad=copy.deepcopy(root);bad[key]=value;roots.append(canonical_bytes(bad).decode())
 bad=copy.deepcopy(root);bad['origins']['model']['ownerId']=root['operatorId'];roots.append(canonical_bytes(bad).decode())
 rasters=[]
 for key,value in [('sourceCanvas',[0,256]),('motionSource',None),('rendererProfile','SFR1'),('schemaVersion',1),('animation',[2000,[[0,0,0,256],[1000,0,0,256]]])]:
  bad=copy.deepcopy(rocket);bad[key]=value;raw=canonical_bytes(bad);digest=hashlib.sha256(raw).hexdigest();changed_root=copy.deepcopy(root);changed_root['roles']['rocket']['descriptor']={'path':'descriptors/'+digest+'.json','sha256':digest,'decodedBytes':len(raw)};rasters.append([raw.decode(),canonical_bytes(changed_root).decode()])
 now=feed['publisher']['selectionValidatedUtc'];put='currentPut(s,CurrentFixture.catalog());'
 return runtime.IMPORTS+'import Toybox.Test;\n'+'''
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}function getInitialView(){return [new WatchUi.WatchFace()];}}
(:typecheck(false)) class CurrentStore {var values={};var writes=0;var failAt=-1;function initialize(){}function read(key){return values[key];}function write(key,value){writes+=1;if(writes==failAt){throw new Lang.InvalidValueException("Controlled write interruption");}values[key]=value;}function remove(key){writes+=1;values.remove(key);}}
(:typecheck(false)) function currentPut(s,raw){var h=new NativeWireHash();h.put(raw);var digest=h.digest();var r={"path"=>"descriptors/"+digest+".json","sha256"=>digest,"decodedBytes"=>h.count};s.write("sf.obj."+r["sha256"],raw);return r;}
(:typecheck(false)) class CurrentFixture {
 static function feed(){return '''+text(files[route])+''';}
 static function wide(){return '''+text(canonical_bytes(wide))+''';}
 static function fresh(){return '''+text(canonical_bytes(fresh))+''';}
 static function changed(){return '''+text(canonical_bytes(changed))+''';}
 static function catalog(){return '''+text(files[feed['catalogPath']])+''';}
 static function root(){return '''+text(canonical_bytes(root))+''';}
 static function rocket(){return '''+text(canonical_bytes(rocket))+''';}
}
(:typecheck(false)) function currentCache(s){currentPut(s,CurrentFixture.catalog());return new NativeCache("https://current-native.invalid",s);}
(:typecheck(false)) function currentPacket(s){currentPut(s,CurrentFixture.catalog());return new NativeBridgeFeed(CurrentFixture.feed(),'''+str(now)+'''l,s);}
(:test,:typecheck(false)) function currentEnvelope(logger){var s=new CurrentStore();var c=currentCache(s);Test.assert(c.accept(CurrentFixture.feed(),'''+str(now)+'''l));var seal=c.commit["seal"];var bad='''+runtime.literal(invalid)+''';for(var i=0;i<bad.size();i+=1){var before=s.writes;Test.assertMessage(!c.accept(bad[i],'''+str(now)+'''l),"current envelope refusal"+i);Test.assert(before==s.writes&&c.commit["seal"].equals(seal));}logger.debug("CURRENT_ENVELOPE unknownVersions=3 oldProfiles=2 extraFields=4 noWrites=true");return true;}
(:test,:typecheck(false)) function currentWideRecovery(logger){var s=new CurrentStore();var c=currentCache(s);Test.assert(new NativeJson().byteSize(CurrentFixture.wide())==8192);Test.assert(c.accept(CurrentFixture.wide(),'''+str(now)+'''l));var seal=c.commit["seal"];var raw=c.commit["rawHash"];c=null;c=new NativeCache("https://current-native.invalid",s);Test.assert(c.load('''+str(now)+'''l)!=null&&c.commit["seal"].equals(seal));var t=new NativeTransfer(c.base,s);Test.assert(t.stage("feed",CurrentFixture.wide()+"x",null)==false);Test.assert(t.stage("feed",CurrentFixture.wide()+"!",null)==false);Test.assert(t.stage("feed",CurrentFixture.wide(),null));var incoming=new NativeIncoming(s,c.base);Test.assert(incoming.admitFeed(c,'''+str(now)+'''l));Test.assert(c.commit["seal"].equals(seal));Test.assert(c.accept(CurrentFixture.fresh(),'''+str(now+3600)+'''l));Test.assert(c.commit["rawHash"].equals(raw));c=null;c=new NativeCache("https://current-native.invalid",s);Test.assert(c.load('''+str(now+3600)+'''l)!=null&&c.packet.validation=='''+str(now+3600)+'''l);logger.debug("CURRENT_WIDE exact8192=true coldWarmReopen=true sourceOnlyRawReuse=true");return true;}
(:test,:typecheck(false)) function currentSourceAge(logger){var s=new CurrentStore();var c=currentCache(s);Test.assert(c.accept(CurrentFixture.feed(),'''+str(now)+'''l));var age=c.packet.validation;var cutoff=age+c.packet.document["refreshPolicy"]["normal_interval_seconds"]*c.packet.document["refreshPolicy"]["stale_cycles"];c.packet.advance(cutoff);Test.assert(c.packet.stale&&c.packet.validation==age);c.attempted('''+str(now)+'''l);Test.assert(!c.due('''+str(now)+'''l));Test.assert(c.due('''+str(now+7200)+'''l));Test.assert(!c.accept(CurrentFixture.feed().substring(0,20),'''+str(now+7200)+'''l));Test.assert(c.packet.validation==age);logger.debug("CURRENT_AGE failedNetworkDoesNotRenew=true staleFromSource=true cadence=true");return true;}
(:test,:typecheck(false)) function currentAtomicRecovery(logger){for(var fault=1;fault<=10;fault+=1){var s=new CurrentStore();var c=currentCache(s);Test.assert(c.accept(CurrentFixture.wide(),'''+str(now)+'''l));var seal=c.commit["seal"];s.failAt=s.writes+fault;var accepted=c.accept(CurrentFixture.changed(),'''+str(now+3600)+'''l);s.failAt=-1;if(!accepted){Test.assert(c.restoreAccepted('''+str(now+3600)+'''l,seal)!=null&&c.commit["seal"].equals(seal));}else{Test.assert(c.packet.document["publisher"]["generation"]==3);}var reopened=new NativeCache(c.base,s);Test.assert(reopened.load('''+str(now+3600)+'''l)!=null);}logger.debug("CURRENT_ATOMIC writeInterruptions=10 lastGoodRecoverable=true");return true;}
(:test,:typecheck(false)) function currentSceneGrammar(logger){var s=new CurrentStore();var p=currentPacket(s);currentPut(s,CurrentFixture.root());var b=new NativeSfrBuild(s,"https://current-native.invalid",p);Test.assert(b.scene["schemaVersion"]==3);var roots='''+runtime.literal(roots)+''';for(var i=0;i<roots.size();i+=1){s=new CurrentStore();p=currentPacket(s);p.bridge["selection"]=currentPut(s,roots[i]);var before=s.writes;var refused=false;try{new NativeSfrBuild(s,"https://current-native.invalid",p);}catch(e){refused=true;}Test.assertMessage(refused,"scene grammar"+i);Test.assert(s.writes==before&&s.read("sf.raster.active")==null);}logger.debug("CURRENT_SCENE rehashedSchemaProfileOriginNegatives=6 noActivation=true");return true;}
(:test,:typecheck(false)) function currentMotionGrammar(logger){var cases='''+runtime.literal(rasters)+''';for(var i=0;i<cases.size();i+=1){var s=new CurrentStore();var p=currentPacket(s);currentPut(s,cases[i][0]);p.bridge["selection"]=currentPut(s,cases[i][1]);var refused=false;try{var b=new NativeSfrBuild(s,"https://current-native.invalid",p);b.prepareRole("rocket");}catch(e){refused=true;}Test.assertMessage(refused,"raster grammar"+i);Test.assert(s.read("sf.raster.active")==null);}logger.debug("CURRENT_MOTION rehashedCanvasProvenanceTimelineNegatives=5 noActivation=true");return true;}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--profile',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--only',choices=EXPECTED);a=p.parse_args();native=source(a.profile);expected=EXPECTED
 if a.only:
  expected=[a.only]
  for name in EXPECTED:
   if name!=a.only:native=native.replace('(:test,:typecheck(false)) function '+name,'(:typecheck(false)) function '+name)
 r=runtime.build_probe(a.output,native,group='current',tests=True);r['expectedTests']=expected;(a.output/'build.json').write_text(json.dumps(r,indent=2)+'\n');print(r['exitCode']);return r['exitCode']
if __name__=='__main__':sys.exit(main())
