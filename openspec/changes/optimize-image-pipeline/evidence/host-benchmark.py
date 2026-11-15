import gzip,time,statistics,json,hashlib,sys
from pathlib import Path
sys.path.insert(0,'.')
from tools.spacefox.native_profile import encode_raster
from tests.test_current_motion_publisher import ROOT,NOW,captured_starship
from tools.spacefox.catalog import build_catalog
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState,merge_schedule
from tools.spacefox.native_motion import build_artifact
out={}
for name,w,h,c in [('map',390,390,3),('rocket',54,124,4),('siteCountry',20,12,4)]:
 raw=gzip.decompress(Path('tests/fixtures/sfr1m-current/'+name+'.rgba.gz').read_bytes()); times=[]; result=None
 for _ in range(9):
  start=time.perf_counter_ns(); chunks=encode_raster(raw,w,h,c);times.append((time.perf_counter_ns()-start)/1e6)
  digest=hashlib.sha256(b''.join(chunks)).hexdigest()
  if result is not None and digest!=result:raise ValueError('nondeterministic')
  result=digest
 out[name]={'full_encoder_ms':times,'median_ms':statistics.median(times),'shards':len(chunks),'wire_bytes':sum(map(len,chunks)),'joined_sha256':result}
r=normalize_launch(captured_starship(),NOW);state=merge_schedule(ScheduleState(),(r,),NOW);catalog=build_catalog(ROOT); times=[];hashes=[]
for _ in range(3):
 start=time.perf_counter_ns(); files,_=build_artifact(state,catalog,NOW,publisher=dict(instance='a'*64,generation=1,selectionValidatedUtc=NOW),root=ROOT);times.append((time.perf_counter_ns()-start)/1e6)
 h=hashlib.sha256()
 for key in sorted(files):h.update(key.encode()+b'\0'+hashlib.sha256(files[key]).digest())
 hashes.append(h.hexdigest())
if len(set(hashes))!=1:raise ValueError('package nondeterministic')
out['package']={'build_ms':times,'median_ms':statistics.median(times),'file_count':len(files),'closure_sha256':hashes[0]}
print(json.dumps(out,indent=2))
