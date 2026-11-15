#!/usr/bin/env python3
"""Compile a native READY mask observer over a retained real content closure.

The generated test-only resource store exposes the *original*, hash-checked
feed, catalog, selection, transfer, descriptors and raster shards. Production
NativeCache, NativeSfrBuild, NativeSfrDecoder and native renderer remain in the
execution path. No network, user health, release signing or stock-memory claim.
Caller owns simulator state, screenshot capture and acceptance.
"""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.native_display04_subset_mask_probe import run as subset
from tools.native_display03_probe import inputs

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def build(out,device,language,names,period='6000'):
 out=Path(out).resolve();receipt=subset(out,device,language,'active',names,period)
 artifact=ROOT/'openspec/changes/spacefox-watchface/evidence/site-flag-visual-batch/native-artifact'
 feed=artifact/'feed.json';f=json.loads(feed.read_text());transfer=artifact/f['nativeTransfer']['path'];index=json.loads(transfer.read_text())
 refs={tuple(f['nativeTransfer'][k] for k in ('sha256','decodedBytes'))}
 refs.update((row[1],row[2]) for row in index['objects'])
 resources=out/'resources';branches=[];resource_paths=[]
 all_files={p.stem:p for p in artifact.rglob('*') if p.is_file() and len(p.stem)==64}
 closure={}
 for i,(digest,length) in enumerate(sorted(refs)):
  path=all_files.get(digest)
  if path is None or sha(path)!=digest or path.stat().st_size!=length:raise ValueError('captured READY object mismatch: '+digest)
  name='D04ReadyObject'+str(i);target=resources/(name+'.json');target.write_text(json.dumps({'raw':path.read_text()},ensure_ascii=False,separators=(',',':')))
  resource_paths.append(target);branches.append('if(key.equals("sf.obj.'+digest+'")){return WatchUi.loadResource(Rez.JsonData.'+name+')["raw"];}')
  closure[str(path.relative_to(ROOT))]=digest
 catalog=artifact/f['catalogPath']
 if sha(catalog)!=f['catalogDigest']:raise ValueError('captured catalog mismatch')
 (resources/'D04Catalog.json').write_text(json.dumps({'catalogDigest':f['catalogDigest'],'catalog':catalog.read_text()},ensure_ascii=False,separators=(',',':')))
 (resources/'D04Feed.json').write_text(json.dumps({'raw':feed.read_text()},ensure_ascii=False,separators=(',',':')))
 xml=resources/'data.xml';xml.write_text('<resources>'+''.join('<jsonData id="'+p.stem+'" filename="'+p.name+'"/>' for p in [resources/'D04Catalog.json',resources/'D04Feed.json',*resource_paths])+'</resources>')
 observer=out/'observer/PointObserver.mc';template=(ROOT/'tests/fixtures/display04_ready_mask/ReadyObserver.mc').read_text()
 if template.count('/* ASSET_BRANCHES */')!=1:raise ValueError('READY store template differs')
 observer.write_text(template.replace('/* ASSET_BRANCHES */',''.join(branches)).replace('{"Language"=>0}','{"Language"=>'+('1' if language=='ru' else '0')+'}'))
 pre=json.loads((out/'subset-precompile.json').read_text());pre['generatedInputs']['observer/PointObserver.mc']=sha(observer)
 pre['generatedResources']={p.name:sha(p) for p in sorted(resources.glob('*'))}
 pre['readyProbeSha256']=sha(Path(__file__));pre['readyTemplateSha256']=sha(ROOT/'tests/fixtures/display04_ready_mask/ReadyObserver.mc');pre['capturedClosure']=closure
 pre['feedSha256']=sha(feed);pre['catalogSha256']=sha(catalog);pre['selectionSha256']=f['visualSelection']['sha256'];pre['transferSha256']=f['nativeTransfer']['sha256']
 (out/'ready-precompile.json').write_text(json.dumps(pre,indent=2)+'\n')
 run=subprocess.run(receipt['command'],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'ready-compile.log').write_text(run.stdout)
 if run.returncode:raise RuntimeError('READY observer compiler failed')
 if pre['sourceInputs']!=inputs() or any(sha(out/n)!=h for n,h in pre['generatedInputs'].items()) or any(sha(resources/n)!=h for n,h in pre['generatedResources'].items()):raise RuntimeError('READY inputs changed during compile')
 receipt.update({'packageSha256':sha(out/'MaskObserver.prg'),'readyProbeSha256':sha(Path(__file__)),'observerSha256':sha(observer),'readySelection':pre['selectionSha256'],'boundary':'test-only resource-store observer; production cache/build/decoder and actual native renderer; no stock-memory or physical proof'})
 (out/'ready-build.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt
if __name__=='__main__':
 result=build(*sys.argv[1:]);print(json.dumps({'status':result['status'],'packageSha256':result['packageSha256'],'selection':result['readySelection']}))
