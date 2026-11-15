#!/usr/bin/env python3
"""Test-only batch: native battery sizes, four rest phases and unmasked control."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.native_display04_battery_probe import build
from tools.native_display03_probe import inputs

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(out,device):
 out=Path(out).resolve();build(out,device)
 mask=out/'source/MaskObserver.mc';s=mask.read_text()
 old='function sample() as Void {current=(((System.getTimer()/6000)+0)%(2*ids.size())).toNumber();}'
 new='function sample() as Void {current=((System.getTimer()/6000)%14).toNumber();}'
 assert s.count(old)==1;s=s.replace(old,new)
 s=s.replace('function white() as Boolean {return (current%2)==1;}','function white() as Boolean {return false;}')
 s=s.replace('function selected() as String {return ids[(current/2)%ids.size()];}','function selected() as String {return current==0?"none":"battery";}');mask.write_text(s)
 observer=out/'observer/PointObserver.mc';s=observer.read_text()
 s=s.replace('function utcSeconds(){return 1794551202;}','function utcSeconds(){var k=MaskObserver.current;var phase=k==0?0:(k==13?2:(k-1)%4);return 1794551082+phase*60;}')
 s=s.replace('var announced=false;var lastMask="";', 'var announced=false;var lastMask="";var lastProbe=-1;')
 marker='MaskObserver.sample();var currentMask='
 inject='''MaskObserver.sample();var probe=MaskObserver.current;
  if(probe!=lastProbe && probe>0){var size=probe==13?53:(53+2*((probe-1)/4));presentation.aodBatteryFont=Graphics.getVectorFont({:face=>"RobotoRegular",:size=>size});lastProbe=probe;System.println("D04_SWEEP id="+probe+" requested="+size);}
  var currentMask='''
 assert s.count(marker)==1;s=s.replace(marker,inject)
 marker=' function onUpdate(dc){';assert s.count(marker)==1
 s=s.replace(marker,' function applyPixelRest(dc as Graphics.Dc) as Void {if(MaskObserver.current!=13){SpaceFoxView.applyPixelRest(dc);}}\n'+marker)
 observer.write_text(s)
 pre=json.loads((out/'battery-precompile.json').read_text())
 for n in ('source/MaskObserver.mc','observer/PointObserver.mc'):pre['generatedInputs'][n]=sha(out/n)
 pre['sweepProbeSha256']=sha(Path(__file__));pre['stages']={'0':'black baseline','1-4':'size53 phase0..3','5-8':'size55 phase0..3','9-12':'size57 phase0..3','13':'size53 phase2 unmasked'}
 (out/'sweep-precompile.json').write_text(json.dumps(pre,indent=2)+'\n')
 receipt=json.loads((out/'battery-build.json').read_text());result=subprocess.run(receipt['command'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'sweep-compile.log').write_text(result.stdout)
 if result.returncode:raise RuntimeError('sweep compile failed')
 if pre['sourceInputs']!=inputs() or any(sha(out/n)!=h for n,h in pre['generatedInputs'].items()):raise RuntimeError('sweep inputs changed')
 receipt['packageSha256']=sha(out/'MaskObserver.prg');receipt['sweepProbeSha256']=sha(Path(__file__));receipt['boundary']='test-only actual native font candidates, colored black-background ink; not resource or lifecycle proof';(out/'sweep-build.json').write_text(json.dumps(receipt,indent=2)+'\n')
 return receipt['packageSha256']
if __name__=='__main__':print(run(*sys.argv[1:]))
