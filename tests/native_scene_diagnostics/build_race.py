import json,sys,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools.native_current_runtime import selected_files
root=Path('/task');fa,a,_,_=selected_files(root/'profile-a');fb,b,_,_=selected_files(root/'profile-b');resources={};xml=['<resources>']
for name,value in [('FeedA',fa['feed.json']),('FeedB',fb['feed.json']),('CatalogA',fa[a['catalogPath']])]:
 resources[name+'.json']=json.dumps({'raw':value.decode()},ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>')
resources['objects.xml']=(''.join(xml)+'</resources>').encode();identity=uuid.uuid4().hex;runtime.GROUPS['race-current']=(identity,'RC1.prg')
app='''import Toybox.Application;import Toybox.Lang;import Toybox.WatchUi;import Toybox.System;
(:typecheck(false)) class RaceStore extends NativeStore {var enabled=false;var fired=false;function read(key){var v=NativeStore.read(key);if(enabled&&!fired&&key.find("sf.incoming.feed.")==0&&!key.equals("sf.incoming.feed.processed")){var m=NativeStore.read("sf.incoming.feed");m["sequence"]+=1;NativeStore.write("sf.incoming.feed",m);fired=true;}return v;}}
(:typecheck(false)) class RaceView extends WatchUi.WatchFace {var app;function initialize(a){WatchFace.initialize();app=a;}function onUpdate(dc){app.step();}}
(:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {var s;var c;var seal;var floor;var stage=0;function initialize(){AppBase.initialize();}function ensure(ok,msg){if(!ok){System.println("RACE_FAIL "+msg);throw new Lang.InvalidValueException(msg);}}function getInitialView(){s=new RaceStore();c=new NativeCache("https://race.invalid",s);return [new RaceView(self)];}function step(){if(stage==0){var i=new NativeImmutable(s);var raw=WatchUi.loadResource(Rez.JsonData.CatalogA)["raw"];var h=new NativeWireHash();h.put(raw);var digest=h.digest();ensure(i.put({"path"=>"wire3/catalogs/"+digest+".json","sha256"=>digest,"decodedBytes"=>h.count},raw),"catalog");}else if(stage==1){ensure(c.accept(WatchUi.loadResource(Rez.JsonData.FeedA)["raw"],1794551192l),"accept A");seal=c.commit["seal"];floor=s.read(c.pinKey)["generation"];}else if(stage==2){var t=new NativeTransfer(c.base,s);ensure(t.stage("feed",WatchUi.loadResource(Rez.JsonData.FeedB)["raw"],null),"stage B");}else if(stage==3){s.enabled=true;var incoming=new NativeIncoming(s,c.base);ensure(!incoming.admitFeed(c,1794551192l)&&s.fired,"race not refused");ensure(c.packet!=null&&c.commit["seal"].equals(seal)&&s.read(c.pinKey)["generation"]==floor,"floor/restore lost");s.enabled=false;}else if(stage==4){c=null;c=new NativeCache("https://race.invalid",s);ensure(c.load(1794551192l)!=null&&c.commit["seal"].equals(seal),"reopen");System.println("ROOT_RACE_COMPLETE mutationReached=true incomingRefused=true oldSealAndFloor=true durableReopen=true");stage=99;System.exit();return;}stage+=1;WatchUi.requestUpdate();}}
'''
out=root/'output/race-current';out.mkdir(parents=True,exist_ok=True)
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 r=runtime.build_probe(out,app,group='race-current',tests=False,probe_resources=resources)
r.update({'actualBase':'854a5a30a5bb021d2bac3e2f799b4f6401f269af','admission':'diagnostic only'});(out/'build.json').write_text(json.dumps(r,indent=2)+'\n');print('exit',r['exitCode'],'uuid',identity);sys.exit(r['exitCode'])
