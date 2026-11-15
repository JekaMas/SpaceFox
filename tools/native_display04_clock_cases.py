#!/usr/bin/env python3
"""Compile native LOW clock extrema from the real renderer and AOD font.

Observer supplies valid times and phases, forces LOW callbacks, isolates only
clock draw, and labels each actual frame outside the face's clock region. It
makes no cadence, resource, device, or whole-scene claim.
"""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.native_display04_mask_probe import build
from tools.native_display03_probe import inputs

TIMES=('00:00','17:57','08:38')
def build_cases(out,device):
 out=Path(out).resolve();before=inputs();build(out,device,'clock',False)
 code='''import Toybox.Graphics;
import Toybox.Lang;
import Toybox.System;
(:typecheck(false)) module MaskObserver {
 var cases=%s;var current=0;
 function sample(){current=((System.getTimer()/8000)%%12).toNumber();}
 function clock(){return cases[current/4];}
 function utc(){return 1794551040+(current%%4)*60;}
 function visible(id){return id.equals("clock");}
 function clear(dc){dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();}
 function barcode(dc){var x=(dc.getWidth()-48)/2;dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.fillRectangle(x-2,8,52,10);dc.setColor(Graphics.COLOR_WHITE,Graphics.COLOR_TRANSPARENT);dc.fillRectangle(x,10,4,6);dc.fillRectangle(x+40,10,4,6);for(var bit=0;bit<6;bit+=1){if((current & (1<<bit))!=0){dc.fillRectangle(x+5+bit*5,10,4,6);}}}
}
'''%json.dumps(TIMES,separators=(',',':'))
 (out/'source/MaskObserver.mc').write_text(code)
 p=out/'observer/PointObserver.mc';s=p.read_text()
 for old,new in [('return 1794551202+(System.getTimer()/1000);','return MaskObserver.utc();'),('return "08:38";','return MaskObserver.clock();'),('SpaceFoxView.onUpdate(dc);','MaskObserver.sample();aodMinute=null;updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);MaskObserver.barcode(dc);')]:
  if s.count(old)!=1:raise ValueError('observer source changed '+old)
  s=s.replace(old,new)
 p.write_text(s);receipt=json.loads((out/'build.json').read_text());cmd=receipt['command']
 generated={str(q.relative_to(out)):hashlib.sha256(q.read_bytes()).hexdigest() for q in (p,out/'source/MaskObserver.mc',out/'source/SceneRenderer.mc',out/'manifest.xml',out/'probe.jungle')}
 (out/'cases-precompile.json').write_text(json.dumps({'productionInputs':before,'generatedInputs':generated,'caseOwnerSha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'command':cmd},indent=2)+'\n')
 r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
 if any(hashlib.sha256((out/name).read_bytes()).hexdigest()!=digest for name,digest in generated.items()):raise RuntimeError('generated input changed during compile')
 (out/'cases-compile.log').write_text(r.stdout)
 if r.returncode:raise RuntimeError('clock case compile failed')
 if before!=inputs():raise RuntimeError('source changed during clock case build')
 receipt.update(status='compiled, not executed',cases=list(TIMES),phases=[0,1,2,3],programSha256=hashlib.sha256((out/'MaskObserver.prg').read_bytes()).hexdigest(),caseOwnerSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),boundary='test-only native LOW glyph/extrema observer; forced callbacks, barcode excluded; no cadence/device/full-scene claim')
 (out/'cases-build.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':print(json.dumps({'status':build_cases(sys.argv[1],sys.argv[2])['status']}))
