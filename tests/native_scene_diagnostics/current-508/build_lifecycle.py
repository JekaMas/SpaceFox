import json,sys,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
import current_runtime as runtime
from tools import native_current_runtime as current
from tools import native_full_visual_lifecycle as lifecycle
root=Path('/task'); ident=uuid.uuid4().hex;runtime.GROUPS['life-current']=(ident,'CL1.prg');url='https://lifecycle.invalid'
files,feed,route,paths=current.selected_files(root/'profile-a')
seed=current.seed(root/'profile-a',url)
needle='var t=new NativeTransfer('
replace='var batch=new NativeBatch(store,'+json.dumps(url)+');if(!batch.begin('+runtime.literal(files[route].decode())+')||batch.next()!=null){throw new Lang.InvalidValueException("seed batch not ready");}var t=new NativeTransfer('
assert needle in seed; seed=seed.replace(needle,replace)
source=lifecycle.source(url).replace('view.sfrRequested','view.sceneLifecycle.pending()')
source=source.replace('NativeMetrics.enabled=true;NativeMetrics.traceStores=false;','').replace('+NativeMetrics.ownerTag','+"current"')
source=source.replace('return result;}\n (:typecheck(disableBackgroundCheck)) function beginLife()', 'return [new DrawProxy(self)];}\n (:typecheck(disableBackgroundCheck)) function beginLife()')
source += '''\n(:typecheck(false)) class DrawProxy extends WatchUi.WatchFace {var app;function initialize(a){WatchFace.initialize();app=a;}function onLayout(dc){app.view.onLayout(dc);}function onShow(){app.view.onShow();}function onUpdate(dc){app.view.onUpdate(dc);}function onHide(){var v=app.view;System.println("HIDE_BEFORE timer="+(v.sfrTimer!=null)+" build="+(v.sfrBuild!=null)+" pending="+v.sceneLifecycle.pending());v.onHide();System.println("HIDE_AFTER timer="+(v.sfrTimer!=null)+" build="+(v.sfrBuild!=null)+" pending="+v.sceneLifecycle.pending()+" animation="+v.animationRunning+" fitness="+(v.fitnessTimer!=null));}}\n'''

with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 for name,body,tests in [('life-seed',seed,True),('life-observe',source,False)]:
  out=root/'output'/name;out.mkdir(parents=True,exist_ok=True);result=runtime.build_probe(out,body,group='life-current',tests=tests);result['actualBase']='508679499bb34926207d695ced00b7890be7530d';result['admission']='diagnostic only';(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(name,result['exitCode'],flush=True)
  if result['exitCode']:sys.exit(result['exitCode'])
print('uuid',ident)
