import hashlib,json,sys,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools.native_current_runtime import selected_files
root=Path('/task');files,feed,_,paths=selected_files(root/'profile-a');resources={};xml=['<resources>'];ids=[]
for i,path in enumerate(paths):
 raw=files[path];name='Obj'+str(i);ref={'path':path,'sha256':hashlib.sha256(raw).hexdigest(),'decodedBytes':len(raw)};resources[name+'.json']=json.dumps({'ref':ref,'raw':raw.decode()},ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>');ids.append('Rez.JsonData.'+name)
resources['Feed.json']=json.dumps({'raw':files['feed.json'].decode()},ensure_ascii=False,separators=(',',':')).encode();xml.append('<jsonData id="Feed" filename="Feed.json"/>');resources['objects.xml']=(''.join(xml)+'</resources>').encode()
id=uuid.uuid4().hex;runtime.GROUPS['map-only']=(id,'CM1.prg')
app='''import Toybox.Application;import Toybox.Graphics;import Toybox.Lang;import Toybox.WatchUi;import Toybox.System;
(:typecheck(false)) class MapView extends WatchUi.WatchFace {var app;function initialize(a){WatchFace.initialize();app=a;}function onUpdate(dc){app.step(dc);}}
(:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {var s;var cache;var immutable;var objects=@@OBJECTS@@;var pos=0;var phase=0;var build;var map;var announced=false;function initialize(){AppBase.initialize();}function ensure(ok,msg){if(!ok){System.println("MAP_FAIL "+msg);throw new Lang.InvalidValueException(msg);}}function getInitialView(){s=new NativeStore();cache=new NativeCache("https://map.invalid",s);immutable=new NativeImmutable(s);ensure(s.read("sf.commit")==null,"fresh");return [new MapView(self)];}function step(dc){if(phase==0){if(pos<objects.size()){var v=WatchUi.loadResource(objects[pos]);ensure(immutable.put(v["ref"],v["raw"]),"seed");pos+=1;}else{ensure(cache.accept(WatchUi.loadResource(Rez.JsonData.Feed)["raw"],1794551192l),"accept");build=new NativeSfrBuild(s,cache.base,cache.packet);phase=1;}WatchUi.requestUpdate();return;}if(phase==1){if(!build.step()){WatchUi.requestUpdate();return;}ensure(build.result.selectionHash.equals("@@SELECTION@@")&&build.result.mapBitmap!=null,"selected map");map=build.result.mapBitmap;build=null;phase=2;}if(phase==2){dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();dc.drawBitmap(0,0,map);if(!announced){announced=true;System.println("MAP_ONLY_READY selection=@@SELECTION@@ width=390 height=390");}}}}
'''.replace('@@OBJECTS@@','['+','.join(ids)+']').replace('@@SELECTION@@',feed['visualSelection']['sha256'])
out=root/'output/map-only';out.mkdir(parents=True,exist_ok=True)
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 r=runtime.build_probe(out,app,group='map-only',tests=False,probe_resources=resources)
r.update({'actualBase':'854a5a30a5bb021d2bac3e2f799b4f6401f269af','admission':'diagnostic only'});(out/'build.json').write_text(json.dumps(r,indent=2)+'\n');print('exit',r['exitCode'],'uuid',id);sys.exit(r['exitCode'])
