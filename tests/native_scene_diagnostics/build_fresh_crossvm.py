"""Ordinary SDK Storage source-only update, then no-push process reopen."""
import copy, hashlib, json, sys, uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0] = ['/task', '/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools.native_current_runtime import selected_files
from tools.spacefox.catalog import canonical_bytes

root = Path('/task')
out = root / 'output/fresh-crossvm'
out.mkdir(parents=True, exist_ok=True)
files, feed, route, _ = selected_files(root / 'profile-a')
fresh = copy.deepcopy(feed)
fresh['publisher']['generation'] += 1
fresh['publisher']['selectionValidatedUtc'] += 3600
fresh['launch']['source_validated_utc'] += 3600
resources = {
    'Feed.json': json.dumps({'raw': files[route].decode()}, ensure_ascii=False, separators=(',', ':')).encode(),
    'Fresh.json': json.dumps({'raw': canonical_bytes(fresh).decode()}, ensure_ascii=False, separators=(',', ':')).encode(),
    'Catalog.json': json.dumps({'raw': files[feed['catalogPath']].decode(), 'digest': feed['catalogDigest']}, separators=(',', ':')).encode(),
    'inputs.xml': b'<resources><jsonData id="Feed" filename="Feed.json"/><jsonData id="Fresh" filename="Fresh.json"/><jsonData id="Catalog" filename="Catalog.json"/></resources>',
}
identity = uuid.uuid4().hex
runtime.GROUPS['fresh-crossvm'] = (identity, 'CF8.prg')
source = '''import Toybox.Application;import Toybox.Lang;import Toybox.System;import Toybox.WatchUi;
(:background) module NativeMetrics {var ownerTag as String="";}
(:typecheck(false)) class FreshCrossView extends WatchUi.WatchFace {
 var owner;function initialize(a){WatchFace.initialize();owner=a;}
 function onUpdate(dc){owner.step();}
}
(:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 var s=null;var c=null;var phase=0;var raw=null;var finished=false;
 function initialize(){AppBase.initialize();}
 function ensure(ok,msg){if(!ok){System.println("FRESH_CROSS_FAIL "+msg);throw new Lang.InvalidValueException(msg);}}
 function getInitialView(){return [new FreshCrossView(self)];}
 function step(){
  if(finished){return;}
  if(s==null){s=new NativeStore();c=new NativeCache("https://crossvm.invalid",s);}
  var stage=Application.Storage.getValue("sf.cross.stage");
  if(stage==null){
   if(phase==0){var catalog=WatchUi.loadResource(Rez.JsonData.Catalog);s.write("sf.obj."+catalog["digest"],catalog["raw"]);
    ensure(c.accept(WatchUi.loadResource(Rez.JsonData.Feed)["raw"],1794551192l),"accept A");raw=c.commit["rawHash"];phase=1;WatchUi.requestUpdate();return;}
   ensure(c.accept(WatchUi.loadResource(Rez.JsonData.Fresh)["raw"],1794554792l),"accept fresh B");
   ensure(c.packet.validation==1794554792l && c.commit["rawHash"].equals(raw) && raw.equals("RAW_EXPECTED") && c.packet.document["publisher"]["generation"]==2,"source only and raw reuse");
   var slot=c.commit["slot"];var header=s.read("sf.feed."+slot);var seal=c.commit["seal"];
   ensure(header instanceof Dictionary && header["chunks"]>0 && header["rawHash"].equals(raw),"committed header");
   Application.Storage.setValue("sf.cross.seal",seal);Application.Storage.setValue("sf.cross.stage",1);
   System.println("FRESH_CROSS_WRITE age=1794554792 generation=2 slot="+slot+" chunks="+header["chunks"]+" seal="+seal+" raw="+raw+" sameRaw=true stage=1");finished=true;System.exit();return;
  }
  ensure(stage==1,"stage");var before=s.writes;ensure(c.load(1794554792l)!=null,"reopen");
  var slot=c.commit["slot"];var header=s.read("sf.feed."+slot);var seal=Application.Storage.getValue("sf.cross.seal");
  ensure(c.packet.validation==1794554792l && c.commit["rawHash"].equals("RAW_EXPECTED") && c.packet.document["publisher"]["generation"]==2 && c.commit["seal"].equals(seal) && header instanceof Dictionary && header["chunks"]>0 && header["rawHash"].equals("RAW_EXPECTED") && s.writes==before,"age, raw, seal, header, generation or writes on reopen");
  System.println("FRESH_CROSS_REOPEN age=1794554792 generation=2 slot="+slot+" chunks="+header["chunks"]+" seal="+seal+" raw="+c.commit["rawHash"]+" zeroWrites=true");finished=true;System.exit();
 }
}'''.replace('RAW_EXPECTED', hashlib.sha256(files[route]).hexdigest())
with patch.object(runtime, 'discover', lambda: linux_probe.context), \
     patch.object(runtime.subprocess, 'check_output', linux_probe.git_info), \
     patch.object(runtime, 'validate_manifest', lambda r, l: ET.parse(r / 'watchface/manifest.xml')):
    result = runtime.build_probe(out, source, group='fresh-crossvm', tests=False, probe_resources=resources)
result.update({'sourceBinding': 'compare productionSources and productionResources to the checkout',
               'admission': 'diagnostic only'})
(out / 'build.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'exit': result['exitCode'], 'uuid': identity}))
sys.exit(result['exitCode'])
