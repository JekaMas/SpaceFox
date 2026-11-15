import copy,hashlib,json,sys,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools.native_current_runtime import selected_files
from tools.spacefox.catalog import canonical_bytes
root=Path('/task');out=root/'output/bounds';out.mkdir(parents=True,exist_ok=True)
files,feed,route,_=selected_files(root/'profile-a')
wide=copy.deepcopy(feed);wide['launch']['mission_name']='';missing=8192-len(canonical_bytes(wide));name=feed['launch']['mission_name'] or feed['launch']['configuration_name'];wide['launch']['mission_name']=(name*(missing//len(name)+1))[:missing];raw=canonical_bytes(wide);assert len(raw)==8192
resources={'Feed.json':json.dumps({'raw':raw.decode()},ensure_ascii=False,separators=(',',':')).encode(),'Catalog.json':json.dumps({'raw':files[feed['catalogPath']].decode(),'digest':feed['catalogDigest']},separators=(',',':')).encode(),'inputs.xml':b'<resources><jsonData id="Feed" filename="Feed.json"/><jsonData id="Catalog" filename="Catalog.json"/></resources>'}
identity=uuid.uuid4().hex;runtime.GROUPS['bounds']=(identity,'BF1.prg')
source='''import Toybox.Application;import Toybox.Lang;import Toybox.System;import Toybox.WatchUi;
(:background) module NativeMetrics {var ownerTag as String="";}
(:typecheck(false)) class BoundsView extends WatchUi.WatchFace {var owner;function initialize(a){WatchFace.initialize();owner=a;}function onUpdate(dc){owner.step();}}
(:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 var s=null;var c=null;var phase=0;var done=false;
 function initialize(){AppBase.initialize();}function ensure(ok,msg){if(!ok){System.println("BOUNDS_FAIL "+msg);throw new Lang.InvalidValueException(msg);}}
 function getInitialView(){return [new BoundsView(self)];}
 function step(){if(done){return;}if(s==null){s=new NativeStore();c=new NativeCache("https://bounds.invalid",s);}var stage=Application.Storage.getValue("sf.bounds.stage");
 if(stage==null){var cat=WatchUi.loadResource(Rez.JsonData.Catalog);s.write("sf.obj."+cat["digest"],cat["raw"]);cat=null;var raw=WatchUi.loadResource(Rez.JsonData.Feed)["raw"];var before=System.getSystemStats();System.println("BOUNDS_BEFORE total="+before.totalMemory+" used="+before.usedMemory+" rawBytes="+new NativeJson().byteSize(raw));ensure(c.accept(raw,NOWl),"accept wide");var after=System.getSystemStats();var seal=c.commit["seal"];ensure(c.commit["rawHash"].equals("HASH"),"hash");Application.Storage.setValue("sf.bounds.seal",seal);Application.Storage.setValue("sf.bounds.stage",1);System.println("BOUNDS_ACCEPT total="+after.totalMemory+" used="+after.usedMemory+" seal="+seal+" hash="+c.commit["rawHash"]+" slot="+c.commit["slot"]);done=true;System.exit();return;}
 var before=s.writes;ensure(c.load(NOWl)!=null,"reopen");ensure(c.commit["seal"].equals(Application.Storage.getValue("sf.bounds.seal"))&&c.commit["rawHash"].equals("HASH")&&s.writes==before,"reopen identity");var stats=System.getSystemStats();System.println("BOUNDS_REOPEN total="+stats.totalMemory+" used="+stats.usedMemory+" zeroWrites=true hash="+c.commit["rawHash"]);done=true;System.exit();}
}'''.replace('NOW',str(feed['publisher']['selectionValidatedUtc'])).replace('HASH',hashlib.sha256(raw).hexdigest())
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 result=runtime.build_probe(out,source,group='bounds',tests=False,probe_resources=resources)
result.update({'sourceBinding':'compare hashes against checkout','admission':'diagnostic only','rawBytes':len(raw),'rawSha256':hashlib.sha256(raw).hexdigest()});(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'exit':result['exitCode'],'uuid':identity}));sys.exit(result['exitCode'])
