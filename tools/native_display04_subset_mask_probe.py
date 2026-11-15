#!/usr/bin/env python3
"""Compile the existing barcoded native mask observer for a finite ID subset.

This changes only its test-only selector cycle; production primitives, source,
fixture, fonts, timer-frozen inputs and isolated operation bodies stay the same.
The caller owns simulator state, capture and semantic acceptance.
"""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.native_display04_batch_mask_probe import batch
from tools.native_display03_probe import inputs

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def run(out,device,language,mode,names,period='6000'):
 out=Path(out).resolve();receipt=batch(out,device,language,mode,'0','0',period)
 old=receipt['selectorIds'];wanted=names.split(',')
 if not wanted or len(wanted)!=len(set(wanted)) or any(x not in old[1:] for x in wanted):raise ValueError('unsupported or duplicate subset')
 selected=['none']+wanted;observer=out/'source/MaskObserver.mc';source=observer.read_text()
 before='var ids='+json.dumps(old,separators=(',',':'))+';';after='var ids='+json.dumps(selected,separators=(',',':'))+';'
 if source.count(before)!=1:raise ValueError('selector source changed')
 observer.write_text(source.replace(before,after));pre=json.loads((out/'batch-precompile.json').read_text());pre['generatedInputs']['source/MaskObserver.mc']=sha(observer)
 pre['subsetProbeSha256']=sha(Path(__file__));pre['subsetIds']=selected
 (out/'subset-precompile.json').write_text(json.dumps(pre,indent=2)+'\n')
 command=receipt['command'];run=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'subset-compile.log').write_text(run.stdout)
 if run.returncode:raise RuntimeError('subset compiler failed')
 if pre['sourceInputs']!=inputs() or any(sha(out/n)!=h for n,h in pre['generatedInputs'].items()):raise RuntimeError('input changed during compilation')
 receipt.update({'selectorIds':selected,'packageSha256':sha(out/'MaskObserver.prg'),'subsetProbeSha256':sha(Path(__file__)),'maskObserverSha256':sha(observer),'boundary':'test-only subset of pending actual primitives; barcode excluded, no READY, preclip or physical proof'})
 (out/'subset-build.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':print(json.dumps(run(*sys.argv[1:])))
