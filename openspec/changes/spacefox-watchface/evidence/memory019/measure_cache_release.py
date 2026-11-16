#!/usr/bin/env python3
"""Offline release trace of the existing host geography LRU, not a product fix."""
import gc
import hashlib
import json
from pathlib import Path
import resource
import sys
import time
import tracemalloc
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT))
from tools.spacefox.geographic_context import load_source,_load_source_cached
recipe=json.loads((ROOT/'catalog/source.json').read_text())
index=json.loads((ROOT/recipe['visualBridge']['path']).read_text())
tracemalloc.start();start=time.perf_counter();rows=[]
def mark(name):
 gc.collect();current,peak=tracemalloc.get_traced_memory()
 rows.append({'phase':name,'python_traced_current':current,'python_traced_peak':peak,'process_peak_rss_bytes_macos':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'cache':_load_source_cached.cache_info()._asdict()})
mark('before')
value=load_source(ROOT,index['regional']);mark('loaded')
summary={'records':len(value['records']),'original_vertices':sum(len(r['points'])for r in value['records']),'supplement_rings':len(value['supplements'])}
del value;mark('caller_reference_dropped')
_load_source_cached.cache_clear();mark('cache_cleared')
r={'boundary':'One offline geography cache lifecycle. cache_clear used only inside this diagnostic process. CPython traced objects and high-water RSS are different; not a watch or physical-power measurement','python':sys.version,'base':'943f320c33b253b913eb8276d1c09b65d51a6c8a','seconds':time.perf_counter()-start,'source_pin':index['regional'],'summary':summary,'phases':rows}
Path(__file__).with_name('CACHE-RELEASE-MEASUREMENT.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
