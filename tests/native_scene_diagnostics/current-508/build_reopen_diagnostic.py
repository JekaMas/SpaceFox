import json,sys
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe,current_runtime as runtime
runtime.GROUPS['reopen-diagnostic']=('b1a6edd46c264da991b8520129eb6731','CL1.prg')
source='''import Toybox.Application;import Toybox.Lang;import Toybox.System;import Toybox.Time;import Toybox.WatchUi;
(:typecheck(false)) class ProbeView extends WatchUi.WatchFace {var app;function initialize(a){WatchFace.initialize();app=a;}function onUpdate(dc){app.step();}}
(:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {var stepNum=0;var store;var cache;var marker;function initialize(){AppBase.initialize();}function getInitialView(){store=new NativeStore();cache=new NativeCache("https://lifecycle.invalid",store);return [new ProbeView(self)];}function step(){if(stepNum==0){marker=store.read("sf.commit");System.println("DIAG commit="+(marker!=null)+" base="+cache.base+" used="+System.getSystemStats().usedMemory);stepNum++;WatchUi.requestUpdate();return;}if(stepNum==1){try{var p=cache.checkedProjection(marker,Time.now().value().toLong());System.println("DIAG projection="+(p!=null)+" raw="+cache.verifyRaw(marker)+" used="+System.getSystemStats().usedMemory);}catch(e){System.println("DIAG projection exception="+e.getErrorMessage());}stepNum++;WatchUi.requestUpdate();return;}if(stepNum==2){try{var p=cache.readCommit(marker,Time.now().value().toLong());System.println("DIAG readCommit="+(p!=null)+" used="+System.getSystemStats().usedMemory);}catch(e){System.println("DIAG readCommit exception="+e.getErrorMessage());}stepNum++;System.exit();}}}
'''
out=Path('/task/output/reopen-diagnostic');out.mkdir(parents=True,exist_ok=True)
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 r=runtime.build_probe(out,source,group='reopen-diagnostic',tests=False)
r['actualBase']='508679499bb34926207d695ced00b7890be7530d';(out/'build.json').write_text(json.dumps(r,indent=2)+'\n');print('exit',r['exitCode']);sys.exit(r['exitCode'])
