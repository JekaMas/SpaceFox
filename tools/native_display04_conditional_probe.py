#!/usr/bin/env python3
"""Compile bounded real-feed-derived stale+structured-Hold geometry observer.

A source fixture is technically mutated only to provider-documented status ID 5
and stale=true; no provider request or inferred Hold. Actual cache, builder,
decoder and rendering execute. Watch-app allowance is geometry only.
"""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.native_display04_ready_mask_probe import build
from tools.native_display03_probe import inputs

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(out,device,period='6000'):
 out=Path(out).resolve();receipt=build(out,device,'en','art,flame,countdown,stale',period,'active')
 r=out/'resources/D04Feed.json';wrapper=json.loads(r.read_text());raw=wrapper['raw']
 changes=[('"source_status_id":1','"source_status_id":5'),('"source_status_name":"Go for Launch"','"source_status_name":null'),('"stale":false','"stale":true')]
 for old,new in changes:
  if raw.count(old)!=1:raise ValueError('captured fixture mutation ambiguous: '+old)
  raw=raw.replace(old,new)
 wrapper['raw']=raw;r.write_text(json.dumps(wrapper,ensure_ascii=False,separators=(',',':')))
 obs=out/'observer/PointObserver.mc';source=obs.read_text();needle='System.println("D04_READY_ACCEPTED realFeed=true");return [new D04ReadyWrapper(view)];';replacement='System.println("D04_CONDITIONAL hold="+view.context.sourceHold+" stale="+view.context.stale);'+needle
 if source.count(needle)!=1:raise ValueError('conditional view setup differs')
 source=source.replace(needle,replacement)
 old='''  stopAnimation();animationProgress=0;MaskObserver.sample();var selection=MaskObserver.selected()+(MaskObserver.white()?"/white":"/black");
  if(!selection.equals(lastMask)){System.println("D04_READY_MASK "+selection);lastMask=selection;}
  SpaceFoxView.onUpdate(dc);MaskObserver.barcode(dc);'''
 new='''  stopAnimation();MaskObserver.sample();var choice=MaskObserver.selected();var selection=choice+(MaskObserver.white()?"/white":"/black");
  if(!selection.equals(lastMask)){System.println("D04_READY_MASK "+selection);lastMask=selection;}
  if(choice.substring(0,4).equals("low_")){animationProgress=0;aodMinute=null;updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);}
  else{animationProgress=0.5;updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);}
  MaskObserver.barcode(dc);'''
 if source.count(old)!=1:raise ValueError('conditional draw wrapper differs')
 obs.write_text(source.replace(old,new));mask=out/'source/MaskObserver.mc';source=mask.read_text();oldids=receipt['selectorIds'];ids=['active_none','active_art','active_flame','active_countdown','active_stale','low_none','low_countdown','low_stale']
 old='var ids='+json.dumps(oldids,separators=(',',':'))+';';new='var ids='+json.dumps(ids,separators=(',',':'))+';'
 if source.count(old)!=1:raise ValueError('conditional selector differs')
 source=source.replace(old,new);old='function visible(id as String) as Boolean {return id.equals(selected());}';new='function visible(id as String) as Boolean {var name=selected();var cut=name.find("_");return cut!=null && id.equals(name.substring(cut+1,name.length()));}'
 if source.count(old)!=1:raise ValueError('conditional isolation routing differs')
 mask.write_text(source.replace(old,new));pre=json.loads((out/'ready-precompile.json').read_text());pre['generatedInputs']['observer/PointObserver.mc']=sha(obs);pre['generatedInputs']['source/MaskObserver.mc']=sha(mask);pre['generatedResources']['D04Feed.json']=sha(r);pre['conditionalProbeSha256']=sha(Path(__file__));pre['conditionalFeedSha256']=hashlib.sha256(raw.encode()).hexdigest();pre['conditionalChanges']=changes;pre['conditionalIds']=ids
 (out/'conditional-precompile.json').write_text(json.dumps(pre,indent=2)+'\n')
 p=subprocess.run(receipt['command'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'conditional-compile.log').write_text(p.stdout)
 if p.returncode:raise RuntimeError('conditional observer compile failed')
 if inputs()!=pre['sourceInputs'] or any(sha(out/n)!=h for n,h in pre['generatedInputs'].items()) or any(sha(out/'resources'/n)!=h for n,h in pre['generatedResources'].items()):raise RuntimeError('conditional inputs changed during compilation')
 receipt.update({'selectorIds':ids,'packageSha256':sha(out/'MaskObserver.prg'),'conditionalProbeSha256':sha(Path(__file__)),'boundary':'technical stale/status-ID-5 mutation of real feed; phase0.5 active and phase1 LOW; watch-app geometry only'})
 (out/'conditional-build.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
 result=run(*sys.argv[1:]);print(json.dumps({'status':result['status'],'packageSha256':result['packageSha256']}))
