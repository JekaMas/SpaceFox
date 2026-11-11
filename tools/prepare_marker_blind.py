# SPDX-License-Identifier: MIT
"""Exact integer crops from retained native JPEGs; PNG retains JPEG ancestry."""
import argparse,concurrent.futures,hashlib,json,random,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('native');p.add_argument('out');p.add_argument('--size',type=int,required=True);p.add_argument('--catches',type=int,required=True);a=p.parse_args();root=Path(a.native);out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
trials=[];seen=set();hidden=[]
for meta in sorted(root.glob('*.json')):
 b=json.loads(meta.read_text())
 for t in b['trials']:
  if t['size']!=a.size or t['rep']!=1:continue
  key=t['candidate'],t['scene']
  row={**t,'rawFile':str(meta.with_suffix('.jpg').resolve()),'rawSha256':hashlib.sha256(meta.with_suffix('.jpg').read_bytes()).hexdigest()}
  if t['on'] and key not in seen:trials.append(row);seen.add(key)
  elif not t['on']:hidden.append(row)
trials+=hidden[:a.catches];random.Random(7340+a.size).shuffle(trials)
def crop(it):
 i,t=it;image='image-'+hashlib.sha256((str(i)+t['candidate']+t['scene']+str(t['on'])).encode()).hexdigest()[:10];rect=t['faceRect'];z=a.size;x,y=round(rect['x']),round(rect['y']);assert abs(rect['w']-z)<.001 and abs(rect['h']-z)<.001 and abs(rect['x']-x)<.001 and abs(rect['y']-y)<.001
 dst=out/(image+'.png');subprocess.run(['/usr/bin/sips','-s','format','png','--cropToHeightWidth',str(z),str(z),'--cropOffset',str(y),str(x),t['rawFile'],'--out',str(dst)],check=True,capture_output=True)
 return {**t,'imageId':image,'image':{'file':str(dst.resolve()),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest()},'kind':'active' if t['on'] and t['snapshot'] else 'genuine-null' if not t['snapshot'] else 'map-present-marker-hidden','expectedVisible':bool(t['on'] and t['snapshot'])}
with concurrent.futures.ThreadPoolExecutor(max_workers=6)as ex:rows=list(ex.map(crop,enumerate(trials)))
(out/'truth.json').write_text(json.dumps({'profile':'generation','trials':rows},ensure_ascii=False,indent=2));(out/'order.json').write_text(json.dumps([r['imageId'] for r in rows]));print(len(rows),'images')
