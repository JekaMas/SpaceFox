# SPDX-License-Identifier: MIT
"""Reviewer-owned image localization scoring; not a human visual-search estimator."""
import argparse,hashlib,json,math
from collections import deque
from pathlib import Path
from audit_marker_raster import artifact,decoded,finite

def silhouette(base,t):
 a=t['visibleGlyphMask'];im=decoded(base,a);origin=a['origin']
 if im['ch']!=4 or len(origin)!=2 or any(not isinstance(v,int) for v in origin):raise ValueError('invalid visible glyph mask')
 w,h=im['w'],im['h'];ink={(x,y) for y,row in enumerate(im['rows']) for x in range(w) if row[x*4+3]/255>.05}
 if not ink:raise ValueError('positive truth has no glyph support')
 # Fill enclosed interior so a correctly chosen outline center is not called a miss.
 outside=set();q=deque((x,y) for y in range(h) for x in range(w) if (x in (0,w-1) or y in (0,h-1)) and (x,y) not in ink)
 while q:
  x,y=q.popleft()
  if (x,y) in outside:continue
  outside.add((x,y))
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<w and 0<=yy<h and (xx,yy) not in ink and (xx,yy) not in outside:q.append((xx,yy))
 return [(origin[0]+x+.5,origin[1]+y+.5) for y in range(h) for x in range(w) if (x,y) not in outside]

def score(truth,answers,base,frozen):
 ts=truth['trials'];aa=answers['answers'];expected={t['imageId']:t for t in ts};received={a['imageId']:a for a in aa};errors=[]
 if len(ts)!=len(expected) or len(aa)!=len(received) or set(expected)!=set(received):errors.append('missing/duplicate/unknown image response')
 frozen_ids=frozen.get('candidateIds')
 if not isinstance(frozen_ids,list) or not frozen_ids or len(set(frozen_ids))!=len(frozen_ids):raise ValueError('invalid frozen blind candidate set')
 if {t.get('candidate') for t in ts}!=set(frozen_ids):errors.append('frozen blind candidate coverage')
 for t in ts:
  if t.get('kind') not in ('active','genuine-null','map-present-marker-hidden') or t.get('expectedVisible')!=(t.get('kind')=='active'):errors.append('invalid blind trial truth kind')
 if truth.get('profile')=='final':
  if len(frozen_ids)!=5 or len(ts)!=60:errors.append('final60 coverage')
  for c in frozen_ids:
   for n in (390,222,195):
    rows=[t for t in ts if t.get('candidate')==c and t.get('size')==n]
    if len(rows)!=4 or sum(t['kind']=='active' for t in rows)!=2 or sum(t['kind']=='genuine-null' for t in rows)!=1 or sum(t['kind']=='map-present-marker-hidden' for t in rows)!=1:errors.append('final candidate/size/kind coverage')
    if len({t.get('scene') for t in rows if t['kind']=='active'})!=2:errors.append('duplicate positive scene')
 result=[]
 for ident,t in expected.items():
  artifact(base,t['image']);a=received.get(ident);r={'imageId':ident,'size':t['size'],'expectedVisible':t['expectedVisible'],'kind':t['kind'],'errors':[]}
  if not a:r['errors'].append('missing response');result.append(r);continue
  if a.get('status') not in ('located','none','unable') or a.get('confidence') not in ('low','medium','high') or a.get('classification') not in ('launch-site','decorative','other','uncertain','none'):r['errors'].append('invalid structured response')
  r['response']=a
  if a.get('status')=='located':
   if not finite(a.get('x')) or not finite(a.get('y')) or not 0<=a['x']<t['size'] or not 0<=a['y']<t['size']:r['errors'].append('invalid image pixel coordinate')
  elif a.get('x') is not None or a.get('y') is not None:r['errors'].append('ambiguous coordinate for none/unable')
  if t['expectedVisible']:
   if a.get('status')!='located':r['errors'].append('positive unable/not located')
   elif not r['errors']:
    if a.get('classification')!='launch-site':r['errors'].append('wrong semantic identity')
    pts=silhouette(base,t);scale=t['size']/390;tolerance=6*scale;anchor=t['anchor390'];d=min(math.hypot(a['x']-x,a['y']-y) for x,y in pts);anchorDistance=math.hypot(a['x']-anchor[0]*scale,a['y']-anchor[1]*scale);r.update(distanceToFilledSilhouette=d,distanceToAnchor=anchorDistance,tolerance=tolerance)
    if min(d,anchorDistance)>tolerance:r['errors'].append('wrong localized point')
  elif a.get('status')=='located':r['errors'].append('invented marker in negative image')
  elif a.get('status')=='unable':r['negativeUncertainty']=True
  r['passed']=not r['errors'];result.append(r)
 return {'method':'Independent per-image location/semantic check against withheld frozen truth; outline interiors accepted; no human latency/probability inference','errors':errors,'trials':result,'passed':bool(result) and not errors and all(x.get('passed') for x in result),'counts':{'images':len(result),'positive':sum(x['expectedVisible'] for x in result),'negative':sum(not x['expectedVisible'] for x in result),'negativeUnable':sum(x.get('negativeUncertainty',False) for x in result),'materialFailures':sum(bool(x['errors']) for x in result)}}

def main():
 p=argparse.ArgumentParser();p.add_argument('truth');p.add_argument('answers');p.add_argument('response_lock');p.add_argument('output');p.add_argument('--frozen-candidates',required=True);args=p.parse_args();truth=Path(args.truth);answers=Path(args.answers);lock=json.loads(Path(args.response_lock).read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
 if lock.get('answersSha256')!=sha(answers) or lock.get('truthSha256')!=sha(truth):raise ValueError('truth/answer lock mismatch')
 out=score(json.loads(truth.read_text()),json.loads(answers.read_text()),truth.parent,json.loads(Path(args.frozen_candidates).read_text()));out['lockVerified']=True;out['answersSha256']=sha(answers);out['truthSha256']=sha(truth);Path(args.output).write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'passed':out['passed'],'errors':out['errors'],'counts':out['counts']},indent=2))
if __name__=='__main__':main()
