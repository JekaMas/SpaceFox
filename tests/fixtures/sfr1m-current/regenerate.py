import gzip,json,hashlib
from pathlib import Path
from tests.test_current_motion_publisher import ROOT,NOW,captured_starship
from tools.spacefox.catalog import build_catalog
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState,merge_schedule
from tools.spacefox.native_motion import build_artifact
from tools.spacefox import native_profile as p
r=normalize_launch(captured_starship(),NOW);s=merge_schedule(ScheduleState(),(r,),NOW)
f,_=build_artifact(s,build_catalog(ROOT),NOW,publisher=dict(instance='a'*64,generation=1,selectionValidatedUtc=NOW),root=ROOT)
feed=json.loads(f['feed.json']);scene=json.loads(f[feed['visualSelection']['path']]);src=json.loads(f[scene['sourceSelection']['path']])
for role,b in scene['roles'].items():
 if b is None: continue
 d=json.loads(f[b['descriptor']['path']]); sr=src['roles']['geography' if role=='map' else role];sd=json.loads(f[sr['descriptor']['path']]);w,h=d['canvas'];
 if role=='map':
  px,_,_=p.rasterize(p._map_visuals(f,sd),w,h,opaque=True);px=bytes(x for i,x in enumerate(px) if i%4!=3)
  for step in (1,4,8,16):
   x=px if step==1 else bytes(min(255,((v+step//2)//step)*step) for v in px)
   if hashlib.sha256(x).hexdigest()==d['pixelSha256']:px=x;break
  else:raise ValueError('no map raw match')
 else:
  visual,_=p._asset(f,sr['descriptor']);px,_,_=p.rasterize([visual],w,h)
 assert hashlib.sha256(px).hexdigest()==d['pixelSha256']
 out=ROOT/'tests/fixtures/sfr1m-current'/f'{role}.rgba.gz';out.write_bytes(gzip.compress(px,mtime=0));print(role,len(px),hashlib.sha256(px).hexdigest(),hashlib.sha256(out.read_bytes()).hexdigest())
