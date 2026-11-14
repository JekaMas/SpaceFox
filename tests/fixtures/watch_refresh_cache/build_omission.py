#!/usr/bin/env python3
"""Current producer trace: captured A omitted while another record advances."""
from dataclasses import replace
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from tests.test_schedule_producer_whole import captured_starship,NOW
from tools.spacefox.catalog import build_catalog,canonical_bytes
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState,Timing,TimePrecision,merge_schedule
from tools.spacefox.schedule import IdKind,StableId
from tools.spacefox.native_motion import build_artifact,validate_artifact
out=Path(__file__).resolve().parent
first=normalize_launch(captured_starship(),NOW)
a=replace(first,timing=Timing(TimePrecision.EXACT,exact_utc=1800007200),source_validated_utc=1800000000)
b=replace(a,launch_id=StableId(IdKind.LAUNCH,'ll2','00000000-0000-4000-8000-000000000005'),timing=Timing(TimePrecision.EXACT,exact_utc=1800010000),source_validated_utc=1800003600)
initial=merge_schedule(ScheduleState(),(a,),1800000000);later=merge_schedule(initial,(b,),1800003600);catalog=build_catalog(ROOT)
rows={}
for name,state,now,generation in [('initial',initial,1800000000,1),('omitted',later,1800003600,2)]:
 files,_=build_artifact(state,catalog,now,publisher={'instance':'a'*64,'generation':generation,'selectionValidatedUtc':now},root=ROOT);feed=validate_artifact(files)
 rows[name]={'raw':files['feed.json'].decode(),'catalog':files[feed['catalogPath']].decode(),'catalogDigest':feed['catalogDigest']}
 if feed['launch']['launch_id']!='ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b' or feed['launch']['source_validated_utc']!=1800000000:raise ValueError('omission selected record/age changed')
raw=canonical_bytes(rows);(out/'omission.json').write_bytes(raw)
print(json.dumps({'bundleSha256':hashlib.sha256(raw).hexdigest(),'aValidation':1800000000,'laterPublisherValidation':1800003600,'originalStatus':'pending','technicalMutation':'record B identity/time only; captured display strings preserved'}))
