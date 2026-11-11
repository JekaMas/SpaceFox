# SPDX-License-Identifier: MIT
"""Independent actual diagnostic-PNG spatial alpha survival; no producer metrics used."""
import hashlib,json,sys,math
from pathlib import Path
from png_decoder_source import decode_png
CACHE={}
def pixels(base,a):
 p=(base/a['file']).resolve();b=p.read_bytes();h=hashlib.sha256(b).hexdigest()
 if h!=a['sha256']:raise ValueError('mask hash mismatch')
 if h in CACHE:return CACHE[h]
 w,ht,ch,rows=decode_png(b)
 if ch!=4:raise ValueError('mask alpha channel absent')
 v={(x,y):row[x*4+3] for y,row in enumerate(rows) for x in range(w) if row[x*4+3]};CACHE[h]=(w,ht,v);return CACHE[h]
def run(manifest):
 base=manifest.parent;j=json.loads(manifest.read_text());rr=[]
 for t in j['trials']:
  if t['sourcePoint'] is None:continue
  parts=[];errors=[]
  for part,minimum in [('glyph',.95),('core',.98),('halo',.95)]:
   try:
    a=t['masks'][part];b=t['visibleMasks'][part]
    if a['origin']!=b['origin']:raise ValueError('raw/visible raster phases differ')
    w,h,R=pixels(base,a);ww,hh,V=pixels(base,b)
    if (w,h)!=(ww,hh):raise ValueError('mask dimensions differ')
    raw=sum(R.values());visible=sum(V.values());intersection=sum(min(a,V.get(k,0)) for k,a in R.items());survival=intersection/raw if raw else 0;positive=sum(max(0,a-R.get(k,0)) for k,a in V.items());outside=sum(1 for (x,y),a in V.items() if a>R.get((x,y),0) and not any((xx,yy) in R for yy in range(y-1,y+2) for xx in range(x-1,x+2)))
    if survival+1e-9<minimum:errors.append('actual PNG survival:'+part)
    if positive>255 or outside:errors.append('AA redistribution outside bounded fringe:'+part)
    reported=t.get('reported',{}).get('parts',{}).get(part,{})
    if abs(reported.get('rawArea',float('inf'))-raw/255)>1e-7 or abs(reported.get('visibleArea',float('inf'))-visible/255)>1e-7:errors.append('reported alpha area contradiction:'+part)
    parts.append({'part':part,'rawArea':raw/255,'visibleArea':visible/255,'spatialIntersectionArea':intersection/255,'spatialSurvival':survival,'positiveRedistribution':positive/255,'offRawNeighborhoodPixels':outside})
   except Exception as e:errors.append(type(e).__name__+':'+str(e))
  rr.append({'candidate':t['candidate'],'scene':t['scene'],'size':t['size'],'errors':errors,'parts':parts})
 return {'method':'Independent CRC/hash PNG alpha-byte counts and same-pixel intersection/retention; positive AA redistribution never compensates lost source paint; one capture-pixel aggregate positive/fringe guard and no outside1px-source-neighborhood growth','manifest':str(manifest),'trials':rr,'maskFilesDecoded':len(CACHE),'failedTrials':sum(bool(x['errors']) for x in rr),'boundary':'These are source-bound diagnostic PNGs, not native screenshots or human noticeability evidence.'}
if __name__=='__main__':
 report=run(Path(sys.argv[1]).resolve());Path(sys.argv[2]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='trials'},indent=2))
