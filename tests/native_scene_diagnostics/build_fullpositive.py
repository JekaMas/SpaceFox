import json,sys
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime,native_current_runtime as current,native_full_visual_quota as quota
root=Path('/task');runtime.GROUPS['fullstore-current']=('afcb63403b834ed49f7fdc85a32bb319','CL1.prg');url='https://lifecycle.invalid'
files,feed,route,paths=current.selected_files(root/'profile-b')
prefill=current.seed(root/'profile-b',url,objects_only=True)
raw=runtime.literal(files[route].decode())
full=runtime.IMPORTS+'''\n(:typecheck(false)) class FullView extends WatchUi.WatchFace {var app;function initialize(a){WatchFace.initialize();app=a;}function onUpdate(dc){app.step();}}
(:background,:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {var store;var cache;var seal;var floor;var age;var stage=0;function initialize(){AppBase.initialize();}function ensure(ok,msg){if(!ok){System.println("FULL_FAIL "+msg);throw new Lang.InvalidValueException(msg);}}function getInitialView(){store=new NativeStore();cache=new NativeCache("https://lifecycle.invalid",store);return [new FullView(self)];}function step(){if(stage==0){ensure(cache.load(1794551192l)!=null,"load A");seal=cache.commit["seal"];floor=store.read(cache.pinKey)["generation"];age=cache.packet.validation;}else if(stage==1){var accepted=cache.accept('''+raw+''',1794554792l);ensure(accepted&&cache.packet.document["publisher"]["generation"]==2,"B not accepted after cleanup");}else if(stage==2){ensure(store.read(cache.pinKey)["generation"]==2,"B floor");System.println("FULL_POSITIVE_COMPLETE acceptedB=true floor=2");stage=99;System.exit();return;}stage+=1;WatchUi.requestUpdate();}}\n''' 
items=[('full-positive',full,False,None)]
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 for name,source,tests,files in items:
  out=root/'output'/name;out.mkdir(parents=True,exist_ok=True);r=runtime.build_probe(out,source,group='fullstore-current',tests=tests,source_files=files);r.update({'actualBase':'854a5a30a5bb021d2bac3e2f799b4f6401f269af','admission':'diagnostic only'});(out/'build.json').write_text(json.dumps(r,indent=2)+'\n');print(name,r['exitCode'],flush=True)
  if r['exitCode']:sys.exit(r['exitCode'])
