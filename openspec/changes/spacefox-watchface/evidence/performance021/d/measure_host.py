#!/usr/bin/env python3
"""One offline resource measurement; retained real fixture, no HTTP/Git/deploy."""
import cProfile
import hashlib
import json
from pathlib import Path
import pstats
import resource
import subprocess
import sys
import time
import tracemalloc

ROOT = Path.cwd()
sys.path.insert(0,str(ROOT))
from tests.test_current_motion_publisher import captured_starship, NOW
from tools.spacefox.catalog import build_catalog
from tools.spacefox.native_motion import build_artifact, validate_artifact
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, merge_schedule

report={'boundary':'Single offline retained-real-Starship sample; Python3.14 on macOS, not Ubuntu CI, not watch; tracemalloc overhead included; no external service or Git remote calls', 'python':sys.version,'phases':[]}
original_popen=subprocess.Popen
calls=[]
class ObservedPopen(original_popen):
    def __init__(self,args,*a,**kw):
        if not isinstance(args,list) or Path(str(args[0])).name not in ('node','rsvg-convert'):
            raise RuntimeError('unexpected subprocess in offline measurement')
        calls.append({'program':Path(str(args[0])).name})
        super().__init__(args,*a,**kw)
subprocess.Popen=ObservedPopen
tracemalloc.start()
def phase(name,fn):
    tracemalloc.reset_peak();before=tracemalloc.get_traced_memory()[0];start=time.perf_counter();c=len(calls)
    profile=cProfile.Profile();profile.enable()
    try:result=fn()
    finally:
        profile.disable();current,peak=tracemalloc.get_traced_memory()
        stats=pstats.Stats(profile)
        hot=sorted(stats.stats.items(),key=lambda x:x[1][3],reverse=True)[:15]
        report['phases'].append({'phase':name,'seconds':time.perf_counter()-start,'python_traced_before':before,'python_traced_current':current,'python_traced_peak':peak,'peak_over_before':peak-before,'process_peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'subprocesses':calls[c:],'top_cumulative':[{'file':Path(k[0]).name,'line':k[1],'function':k[2],'calls':v[1],'cumulative_seconds':v[3]} for k,v in hot]})
    return result
catalog=phase('catalog_build',lambda:build_catalog(ROOT))
record=normalize_launch(captured_starship(),NOW)
state=merge_schedule(ScheduleState(),(record,),NOW)
files,digest=phase('native_artifact_build',lambda:build_artifact(state,catalog,NOW,publisher={'instance':'a'*64,'generation':1,'selectionValidatedUtc':NOW},root=ROOT))
phase('repeat_same_artifact_validation',lambda:validate_artifact(files))
report.update(artifact_files=len(files),artifact_bytes=sum(map(len,files.values())),feed_bytes=len(files['feed.json']),feed_sha256=hashlib.sha256(files['feed.json']).hexdigest(),catalog_digest=digest)
output=Path(__file__).with_name('HOST-MEASUREMENT-FINAL.json');output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'output':str(output.relative_to(ROOT)),'artifact_files':len(files),'artifact_bytes':report['artifact_bytes'],'phases':[{k:p[k] for k in ('phase','seconds','python_traced_peak','process_peak_rss_bytes_macos')} for p in report['phases']]},indent=2))
