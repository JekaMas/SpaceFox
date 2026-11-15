#!/usr/bin/env python3
"""Compile an isolated LOW battery draw with its actual native font metrics.

This is a test-only copy: the battery draw itself is unchanged. Its native
font handles, dimensions and sampled text are printed immediately before draw.
"""
import hashlib, json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.native_display04_subset_mask_probe import run, sha
from tools.native_display03_probe import inputs

def build(out, device):
 out=Path(out).resolve(); receipt=run(out,device,'en','low','battery','6000')
 p=out/'source/SceneRenderer.mc'; text=p.read_text()
 original='if(MaskObserver.visible("battery")){dc.drawText(195+p[0],295+p[1],presentation.aodBatteryFont as Graphics.FontType,current.battery,Graphics.TEXT_JUSTIFY_CENTER);}'
 changed='''if(MaskObserver.visible("battery")){
  System.println("D04_BATTERY_METRICS batteryFontIsContext="+(presentation.aodBatteryFont==presentation.aodContextFont)+" batteryFontIsCalendar="+(presentation.aodBatteryFont==presentation.calendarFont)+" height="+dc.getFontHeight(presentation.aodBatteryFont as Graphics.FontType)+" contextHeight="+dc.getFontHeight(presentation.aodContextFont as Graphics.FontType)+" width="+dc.getTextWidthInPixels(current.battery,presentation.aodBatteryFont as Graphics.FontType)+" text="+current.battery+" viewport="+dc.getWidth()+"x"+dc.getHeight()+" offset="+p[0]+","+p[1]);
  dc.drawText(195+p[0],295+p[1],presentation.aodBatteryFont as Graphics.FontType,current.battery,Graphics.TEXT_JUSTIFY_CENTER);}'''
 if text.count(original)!=1:raise ValueError('battery primitive changed')
 p.write_text('import Toybox.System;\n'+text.replace(original,changed)); pre=json.loads((out/'subset-precompile.json').read_text());pre['generatedInputs']['source/SceneRenderer.mc']=sha(p);pre['batteryProbeSha256']=sha(Path(__file__))
 (out/'battery-precompile.json').write_text(json.dumps(pre,indent=2)+'\n')
 result=subprocess.run(receipt['command'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'battery-compile.log').write_text(result.stdout)
 if result.returncode:raise RuntimeError('battery probe compile failed')
 if pre['sourceInputs']!=inputs() or any(sha(out/n)!=h for n,h in pre['generatedInputs'].items()):raise RuntimeError('inputs changed during compile')
 receipt['packageSha256']=sha(out/'MaskObserver.prg');receipt['batteryProbeSha256']=sha(Path(__file__));receipt['boundary']='actual battery font and native text metrics; isolated test-only source copy, not stock memory';(out/'battery-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return receipt['packageSha256']
if __name__=='__main__':print(build(*sys.argv[1:]))
