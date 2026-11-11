# SPDX-License-Identifier: MIT
import gzip,json,sys,math
from pathlib import Path
campaign=json.loads(gzip.decompress(Path(sys.argv[1]).read_bytes()));records={(r['candidate'],r['scene']):r for g in campaign['controls'] if g['name']=='authorNative' for r in g['records']};rows=[];max_error=0
EPS=5e-4

def compare(a,b,where=''):
 global max_error
 if isinstance(a,(int,float)) and isinstance(b,(int,float)):
  d=abs(a-b);max_error=max(max_error,d)
  return [] if math.isfinite(d) and d<=EPS else [where+':numeric mismatch']
 if isinstance(a,dict) and isinstance(b,dict):
  keys=(set(a)|set(b))-{'method'}
  if a.get('display')==b.get('display')=='contents' and a.get('w')==b.get('w')==0 and a.get('h')==b.get('h')==0:keys-= {'x','y'}
  return [p for k in keys for p in compare(a.get(k),b.get(k),where+'/'+k)]
 if isinstance(a,list) and isinstance(b,list):
  if len(a)!=len(b):return [where+':list length']
  return [p for i,(x,y) in enumerate(zip(a,b)) for p in compare(x,y,where+'/'+str(i))]
 return [] if a==b else [where+':value mismatch']
for p in sorted(Path(sys.argv[2]).glob('*.json')):
 meta=json.loads(p.read_text())
 for t in meta['trials']:
  if not t['on']:continue
  r=records[(t['candidate'],t['scene'])];errors=compare(r['observation']['marker']['snapshot'],t['snapshot'])
  rows.append({'metadata':p.name,'candidate':t['candidate'],'size':t['size'],'errors':errors})
report={'method':'Independent source/native snapshot closure; compare actual live leaves/computed paint/transforms/clip/foreground, not candidate recipe. Numeric epsilon5e-4native390units allows observed CSSOM Float32 bbox serialization only; no image resampling or coordinate shift applied.','onSnapshots':len(rows),'numericEpsilon':EPS,'precisionBasis':'CSSOM Float32 at1200CSSpx hasULP0.0001220703; subtract/normalize up to2x gives a conservative0.0005native390 bound. No style/shape/source point tolerance; only numerical fields, display:contents zeroarea x/y ignored as nonpainted.','maxNumericDifference':max_error,'mismatches':[r for r in rows if r['errors']],'passed':all(not r['errors'] for r in rows)};Path(sys.argv[3]).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='mismatches'}|{'mismatchesCount':len(report['mismatches']),'examples':report['mismatches'][:1]},indent=2))
