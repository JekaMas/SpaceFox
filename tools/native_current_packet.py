#!/usr/bin/env python3
"""Build current-only local SDK diagnostic packet from a retained real launch.

Historical source facts retain their source epoch. Exact8KiB is an explicit
transport-density fixture. Controlled timing/no-position/unknown-schema cases
are labeled mutations and do not claim to be additional real launch records.
"""
import argparse,copy,hashlib,json,sys
from dataclasses import replace
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.spacefox.catalog import build_catalog,canonical_bytes
from tools.spacefox.native_motion import build_artifact,validate_artifact
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import AcceptedLaunch,ScheduleState,Timing,TimePrecision
ROOT=Path(__file__).resolve().parents[1]
NOW=1794355200

def build(out):
 out.mkdir(parents=True,exist_ok=True);fixture=ROOT/'tests/fixtures/provider/detail-efficiency/upcoming-projection.json';rows=json.loads(fixture.read_text());record=normalize_launch(rows[0],NOW);catalog=build_catalog(ROOT);pack={};receipts=[]
 def artifact(name,entry,generation,epoch):
  state=ScheduleState(() if entry is None else (AcceptedLaunch(entry),),epoch)
  files,_=build_artifact(state,catalog,epoch,publisher={'instance':'1'*64,'generation':generation,'selectionValidatedUtc':epoch},root=ROOT);validate_artifact(files);pack[name]=files
  for path,raw in files.items():
   if path=='feed.json':p=out/('feed.json' if name=='a' else 'versions/'+name+'/feed.json')
   else:p=out/path
   p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
  receipts.append({'phase':name,'generation':generation,'feedBytes':len(files['feed.json']),'feedSha256':hashlib.sha256(files['feed.json']).hexdigest()})
  return json.loads(files['feed.json'])
 artifact('a',record,1,NOW)
 wide=replace(record,mission_name=None,source_validated_utc=NOW+1800);feed=json.loads(pack['a']['feed.json']);feed['launch']['mission_name']=None
 missing=8192-len(canonical_bytes(feed))+2;actual=record.mission_name or record.configuration_name
 wide=replace(record,mission_name=(actual*(missing//len(actual)+1))[:missing]);artifact('wide',wide,2,NOW+1800)
 source=replace(wide,source_validated_utc=NOW+3600);artifact('source',source,3,NOW+3600)
 changed=replace(record,source_validated_utc=NOW+7200);artifact('changed',changed,4,NOW+7200)
 artifact('empty',None,8,NOW+14400)
 for name,phase,key,value in [('rollback','a',None,None),('unknown','changed','schemaVersion',4),('unknownprofile','changed','rendererProfile','SFR1')]:
  feed=json.loads(pack[phase]['feed.json'])
  if key:feed[key]=value
  p=out/'versions'/name/'feed.json';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(canonical_bytes(feed))
 (out/'packet.json').write_text(json.dumps({'schemaVersion':1,'fixture':str(fixture.relative_to(ROOT)),'fixtureSha256':hashlib.sha256(fixture.read_bytes()).hexdigest(),'phases':receipts,'proofBoundary':__doc__},indent=2)+'\n')
 return receipts
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();print(json.dumps(build(a.output)))
