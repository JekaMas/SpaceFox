# SPDX-License-Identifier: MIT
"""Preregistered final60 exact native crops; no output-driven scene selection."""
import argparse,hashlib,json,random,shutil,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('native');p.add_argument('inputs');p.add_argument('selection');p.add_argument('output');a=p.parse_args();out=Path(a.output);out.mkdir(parents=True,exist_ok=True);scenes=json.load(open(a.inputs))['scenes'];ids=json.load(open(a.selection))['candidateIds'];assert len(ids)==5
active=[next(s for s in scenes if s['language']==lang and s['fixture']['point'] is not None)for lang in ['ru','en']];nil=next(s for s in scenes if s['fixture']['point'] is None);chosen=[(active[0],True,'active'),(active[1],True,'active'),(nil,True,'genuine-null'),(active[0],False,'map-present-marker-hidden')];lookup={}
for file in sorted(Path(a.native).glob('*.json')):
 b=json.loads(file.read_text())
 for t in b['trials']:
  if t['rep']==1:lookup[t['candidate'],t['scene'],t['size'],t['on']]={**t,'rawFile':str(file.with_suffix('.jpg').resolve()),'rawSha256':hashlib.sha256(file.with_suffix('.jpg').read_bytes()).hexdigest()}
trials=[]
for c in ids:
 for size in [390,222,195]:
  for scene,on,kind in chosen:
   t=lookup[c,scene['id'],size,on];r=t['faceRect'];assert all(abs(r[k]-round(r[k]))<.001 for k in ['x','y','w','h'])and abs(r['w']-size)<.001 and abs(r['h']-size)<.001
   imageId='image-'+hashlib.sha256((c+scene['id']+str(size)+kind).encode()).hexdigest()[:12];dst=out/(imageId+'.png');subprocess.run(['/usr/bin/sips','-s','format','png','--cropToHeightWidth',str(size),str(size),'--cropOffset',str(round(r['y'])),str(round(r['x'])),t['rawFile'],'--out',str(dst)],check=True,capture_output=True)
   trials.append({**t,'imageId':imageId,'image':{'file':str(dst.resolve()),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()},'expectedVisible':kind=='active','kind':kind})
assert len(trials)==60;truth={'profile':'final','selectionRule':'FirstnonnullRU+EN,firstnull,hiddenfirstnonnullRU,inbankorder','trials':trials};(out/'truth.json').write_text(json.dumps(truth,ensure_ascii=False,indent=2));(out/'candidate-ids.json').write_text(json.dumps({'candidateIds':ids}));byid={t['imageId']:t for t in trials}
for n,seed in [('a',9921),('b',2217)]:
 dest=out/('observer-'+n);dest.mkdir(exist_ok=True);order=[t['imageId']for t in trials];rng=random.Random(seed)
 for attempt in range(10000):
  rng.shuffle(order)
  if all((byid[x]['candidate'],byid[x]['scene'])!=(byid[y]['candidate'],byid[y]['scene'])for x,y in zip(order,order[1:])):break
 else:raise RuntimeError('order could not avoid adjacent repeats')
 for t in trials:shutil.copy2(out/(t['imageId']+'.png'),dest/(t['imageId']+'.png'))
 (dest/'order.json').write_text(json.dumps(order))
print('60unique exactnativeimages; two shuffled observer packets,120plannedresponses; nohumanlatencyclaim')
