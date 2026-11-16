"""Real-capture serialization experiments, not a watch performance result."""
import json, statistics, time
from pathlib import Path
R=Path(__file__).resolve().parents[5]
f=R/'tests/fixtures/fr165-runtime-20261116/feed.txt'
d=json.loads(f.read_text()); cats=R/'tests/fixtures/fr165-runtime-20261116/objects'/d['catalogPath']; cat=json.loads(cats.read_text())
# Preserve all information consumed by the current SceneContext projection,
# refresh policy, identifiers and independent optional visual source. Candidate
# work is exploratory: endpoint and production integration are not implemented.
fields=('launch_id','configuration_id','configuration_name','operator_id','operator_name','operator_abbrev','mission_purpose','site_id','site_location_name','site_name','country_code','country_name','source_status_id','source_validated_utc','rescheduled','stale','status','timing','ascent_end','sitePosition')
def row(x,selected=False):
 if x is None:return None
 y={k:x.get(k) for k in fields}
 if selected:
  site=cat['entries'].get(x['site_id'],{});y['sitePosition']=site.get('position')
 return y
obj={'refreshPolicy':d['refreshPolicy'],'publisher':d['publisher'],'nativeTransfer':d['nativeTransfer'],'visualSelection':d['visualSelection'],'launch':row(d['launch'],True),'upcoming':[row(x) for x in d['upcoming']]}
# Dictionary-to-positional transformation is invertible for the same projected fields.
def packedrow(x):return None if x is None else [x[k] for k in fields]
arr=[obj['refreshPolicy'],obj['publisher'],obj['nativeTransfer'],obj['visualSelection'],packedrow(obj['launch']),[packedrow(x) for x in obj['upcoming']]]
def enc(x):return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
raw=f.read_bytes(); objects=enc(obj);arrays=enc(arr)
def unpack(a):return dict(zip(fields,a)) if a is not None else None
z=json.loads(arrays);assert unpack(z[4])==obj['launch'] and [unpack(x) for x in z[5]]==obj['upcoming']
results={}
for name,data in [('current',raw),('projected-object',objects),('projected-array',arrays)]:
 samples=[]
 for _ in range(7):
  t=time.perf_counter_ns()
  for i in range(1000):
   x=json.loads(data)
   if name=='projected-array':x=[unpack(x[4]),*[unpack(a) for a in x[5]]]
   elif name=='projected-object':x=[x['launch'],*x['upcoming']]
   else:x=[x['launch'],*x['upcoming']]
  samples.append((time.perf_counter_ns()-t)/1000000/1000)
 results[name]={'utf8Bytes':len(data),'hostJsonDecodeAndSelectMsMedian':round(statistics.median(samples),4),'samplesMs':samples}
print(json.dumps({'fixture':str(f.relative_to(R)),'scope':'host Python json decode+field selection only; excludes publisher, SDK parsing, admission, HTTP, persistence and UI; not an end-to-end comparison','results':results},indent=2))
