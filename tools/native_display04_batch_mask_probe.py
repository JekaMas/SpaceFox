#!/usr/bin/env python3
"""Compile one changing-selector mask observer for a bounded capture batch.

Capture and semantic acceptance are separate from compilation. A timed selector draws a machine-readable ID in a reserved strip on every
frame; saved pixels, never dialog timing, establish the selected operation and
background. 'none' provides the baseline. LOW uses explicit test-only callbacks to expose each isolated draw;
its cadence is not representative of production.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.native_display04_mask_probe import build, IDS
from tools.native_display03_probe import inputs


def batch(out, device, language, mode, phase='0', start='0', period='8000'):
    if not start.isdigit() or int(start)>47 or not period.isdigit() or not 1000<=int(period)<=60000:
        raise ValueError('invalid batch selector timing')
    if phase not in ('0','0.5','1'):
        raise ValueError('unsupported animation phase')
    if language not in ('en','ru') or mode not in ('active','low'):
        raise ValueError('unsupported test context')
    selected_ids=['none']+(list(IDS) if mode=='active' else ['map','point','date','clock','countdown','stale','battery'])
    if int(start)>=2*len(selected_ids):raise ValueError('selector offset outside inventory')
    out=Path(out).resolve(); before=inputs(); build(out,device,'clock',False)
    code='''import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
(:typecheck(false)) module MaskObserver {
 var ids=%s;var current=0;
 function sample() as Void {current=(((System.getTimer()/%s)+%s)%%(2*ids.size())).toNumber();}
 function white() as Boolean {return (current%%2)==1;}
 function selected() as String {return ids[(current/2)%%ids.size()];}
 function barcode(dc as Graphics.Dc) as Void {
  var x=(dc.getWidth()-48)/2;dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.fillRectangle(x-2,8,52,10);
  dc.setColor(Graphics.COLOR_WHITE,Graphics.COLOR_TRANSPARENT);dc.fillRectangle(x,10,4,6);dc.fillRectangle(x+40,10,4,6);
  for(var bit=0;bit<6;bit+=1){if((current & (1<<bit))!=0){dc.fillRectangle(x+5+bit*5,10,4,6);}}
 }
 function visible(id as String) as Boolean {return id.equals(selected());}
 function clear(dc as Graphics.Dc) as Void {var color=white()?Graphics.COLOR_WHITE:Graphics.COLOR_BLACK;dc.setColor(color,color);dc.clear();}
}
''' % (json.dumps(selected_ids,separators=(',',':')),period,start)
    (out/'source/MaskObserver.mc').write_text(code)
    observer=out/'observer/PointObserver.mc';src=observer.read_text()
    src=src.replace('var announced=false;', 'var announced=false;var lastMask="";')
    call='SpaceFoxView.onUpdate(dc);'
    assert src.count(call)==1
    update=('aodMinute=null;updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);' if mode=='low' else call)
    src=src.replace(call,'''stopAnimation();animationProgress='''+phase+''';MaskObserver.sample();var currentMask=MaskObserver.selected()+(MaskObserver.white()?"/white":"/black");
  if(!currentMask.equals(lastMask)){System.println("D04_MASK "+currentMask);lastMask=currentMask;}
  '''+update+'MaskObserver.barcode(dc);')
    assert src.count('{"Language"=>0}')==1
    src=src.replace('{"Language"=>0}', '{"Language"=>'+('1' if language=='ru' else '0')+'}')
    src=src.replace('return 1794551202+(System.getTimer()/1000);','return 1794551202;')
    src=src.replace('function initialize(){AppBase.initialize();}', 'function initialize(){AppBase.initialize();} function onSettingsChanged(){WatchUi.requestUpdate();}')
    observer.write_text(src)
    receipt=json.loads((out/'build.json').read_text()); command=receipt['command']
    names=('observer/PointObserver.mc','source/MaskObserver.mc','source/SceneRenderer.mc','manifest.xml','probe.jungle')
    generated={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in names}
    (out/'batch-precompile.json').write_text(json.dumps({'sourceInputs':before,'generatedInputs':generated,'command':command},indent=2)+'\n')
    run=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
    if any(hashlib.sha256((out/n).read_bytes()).hexdigest()!=d for n,d in generated.items()):raise RuntimeError('generated source changed during batch build')
    (out/'batch-compile.log').write_text(run.stdout)
    if run.returncode: raise RuntimeError('batch compile failed: '+str(out/'batch-compile.log'))
    if before!=inputs():raise RuntimeError('source changed during batch build')
    receipt.update({'status':'compiled batch, not executed','element':'timed batch with per-frame ID barcode','language':language,'mode':mode,'frozenAnimationPhase':phase,'selectorIds':selected_ids,'initialSelectionOffset':int(start),'stageMs':int(period),
       'packageSha256':hashlib.sha256((out/'MaskObserver.prg').read_bytes()).hexdigest(),
       'batchOwnerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'observerSha256':hashlib.sha256(observer.read_bytes()).hexdigest(),
       'maskObserverSha256':hashlib.sha256((out/'source/MaskObserver.mc').read_bytes()).hexdigest(),
       'boundary':'test-only watchface observer; pending observer; metadata strip excluded from oracle; forced LOW cadence; no READY, preclip, alpha, stock-memory or device proof'})
    (out/'batch-build.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    r=batch(*sys.argv[1:]);print(json.dumps({'status':r['status'],'packageSha256':r['packageSha256']}))
