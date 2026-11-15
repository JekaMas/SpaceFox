import hashlib,json,sys,time,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools.native_current_runtime import selected_files
root=Path('/task');out=root/'output/animated-draw';out.mkdir(parents=True,exist_ok=True)
resources={};xml=['<resources>'];rs={};feeds={};scenes={}
for label in ('A','B'):
 files,feed,route,paths=selected_files(root/('profile-animated' if label=='A' else 'profile-b'));feeds[label]=feed;scenes[label]=json.loads(files[feed['visualSelection']['path']]);names=[]
 for i,path in enumerate(paths):
  name='Obj%s%d'%(label,i);raw=files[path];digest=hashlib.sha256(raw).hexdigest();value={'ref':{'path':path,'sha256':digest,'decodedBytes':len(raw)},'raw':raw.decode()}
  resources[name+'.json']=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>');names.append('Rez.JsonData.'+name)
 name='Feed'+label;resources[name+'.json']=json.dumps({'raw':files[route].decode()},ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>');rs[label]=names
resources['objects.xml']=(''.join(xml)+'</resources>').encode();nonce=uuid.uuid4().hex;identity=uuid.uuid4().hex;runtime.GROUPS['phases']=(identity,'CA2.prg');now=int(time.time());threshold=[now+105,now+180,now+255]
app='''// NativeMetrics probe-only adapter inclusion
import Toybox.Application;import Toybox.Lang;import Toybox.System;import Toybox.Time;import Toybox.WatchUi;
(:typecheck(false)) class PhasesView extends WatchUi.WatchFace {var app;function initialize(a){WatchFace.initialize();app=a;}function onUpdate(dc){app.step();}}
(:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 var store;var cache;var immutable;var stage;var pos=0;var objects;var build;var packet;var before;
 function initialize(){AppBase.initialize();}
 function ensure(ok,msg){if(!ok){System.println("CAT_FAIL "+msg);throw new Lang.InvalidValueException(msg);}}
 function getInitialView(){store=new NativeStore();cache=new NativeCache("https://catalog-local.invalid",store);immutable=new NativeImmutable(store);var nonce=Application.Storage.getValue("sf.ca.nonce");var now=Time.now().value().toLong();stage=nonce==null?0:Application.Storage.getValue("sf.ca.stage");System.println("CAT_OPEN stage="+stage+" nonce="+nonce+" epoch="+now);
 if(stage==0){ensure(nonce==null&&store.read("sf.commit")==null,"fresh namespace");objects=@@OBJA@@;}
 else {ensure(nonce instanceof String&&nonce.equals("@@NONCE@@"),"nonce missing");if(stage==20){ensure(cache.load(1794551192l)!=null&&cache.packet.document["publisher"]["generation"]==1,"load prior A before B");objects=@@OBJB@@;}}
 return [new PhasesView(self)];}
 function again(){WatchUi.requestUpdate();}
 function step(){
 if(stage==0||stage==20){if(pos<objects.size()){var value=WatchUi.loadResource(objects[pos]);ensure(immutable.put(value["ref"],value["raw"]),"object put "+pos);pos+=1;again();return;}var feed=WatchUi.loadResource(stage==0?Rez.JsonData.FeedA:Rez.JsonData.FeedB)["raw"];ensure(cache.accept(feed,1794551192l),"feed accept");packet=cache.packet;build=new NativeSfrBuild(store,"https://catalog-local.invalid",packet);stage=stage==0?1:21;again();return;}
 if(stage==10||stage==30){before=store.writes;ensure(cache.load(1794551192l)!=null,"reopen feed");packet=cache.packet;build=new NativeSfrBuild(store,"https://catalog-local.invalid",packet);stage=stage==10?11:31;again();return;}
 if(stage==1||stage==11||stage==21||stage==31){if(!build.step()){again();return;}var result=build.result;var isB=stage==21||stage==31;if(!isB){ensure(result.animations[0]==2000&&result.animations[1].size()==3&&result.animations[1][1][2]==-64&&result.animations[1][1][3]==288&&result.animations[1][2][2]==-128,"animated timeline");result.prepareFrame(0.5,0);ensure(result.duration()==2.0&&result.frameY>116.3&&result.frameY<116.4&&result.frameScale==1.125,"animated interpolation");var stats=System.getSystemStats();System.println("ANIMATED_FRAME_OK duration=2000 frameY="+result.frameY+" frameScale="+result.frameScale+" used="+stats.usedMemory+" total="+stats.totalMemory);}var expected=isB?"@@SEL_B@@":"@@SEL_A@@";var active=store.read("sf.raster.active");ensure(result.selectionHash.equals(expected)&&result.mapBitmap!=null&&result.bitmap!=null&&result.siteCountryBitmap!=null,"complete decoded selected scene");ensure(active["selectionHash"].equals(expected),"active pointer");ensure(packet.launchId().equals("ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b"),"identity");ensure(packet.document["publisher"]["generation"]==(isB?2:1),"generation");ensure(packet.bridge["site"]["position"]["latitude"].equals(isB?"26.99677":"25.99677"),"position");if(stage==11||stage==31){ensure(store.writes==before,"reopen writes");}if(stage==1){Application.Storage.setValue("sf.ca.nonce","@@NONCE@@");} Application.Storage.setValue("sf.ca.stage",stage==1?10:stage==11?20:stage==21?30:99);System.println("CAT_PHASE stage="+stage+" generation="+(isB?2:1)+" selected="+expected+" position="+packet.bridge["site"]["position"]["latitude"]+" fullScene=true reopenNoWrites="+(stage==11||stage==31));stage=99;System.exit();return;}
 }
}'''
repl={'@@T1@@':str(threshold[0]),'@@T2@@':str(threshold[1]),'@@T3@@':str(threshold[2]),'@@NONCE@@':nonce,'@@OBJA@@':'['+','.join(rs['A'])+']','@@OBJB@@':'['+','.join(rs['B'])+']','@@SEL_A@@':feeds['A']['visualSelection']['sha256'],'@@SEL_B@@':feeds['B']['visualSelection']['sha256']}
for a,b in repl.items():app=app.replace(a,b)
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 result=runtime.build_probe(out,app,group='phases',tests=False,probe_resources=resources)
result.update({'actualBase':'854a5a30a5bb021d2bac3e2f799b4f6401f269af','nonce':nonce,'threshold':threshold,'feeds':feeds,'admission':'diagnostic only'});(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'exit':result['exitCode'],'uuid':identity,'threshold':threshold}));sys.exit(result['exitCode'])
