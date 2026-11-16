import collections,json,os,sys,time
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path.cwd()))
from tools import release,build_watchface
root=Path.cwd(); rows=[]
for label,fn in [('source_state',lambda: release.source_state(root)),('toolchain',lambda: build_watchface.discover_toolchain(root))]:
 counts=collections.Counter(); sizes=collections.Counter(); processes=[]
 rb,rt,run=Path.read_bytes,Path.read_text,build_watchface.run
 def readb(p,*a,**k):
  data=rb(p,*a,**k);counts[str(p)]+=1;sizes[str(p)]+=len(data);return data
 def readt(p,*a,**k):
  data=rt(p,*a,**k);counts[str(p)]+=1;sizes[str(p)]+=len(data.encode());return data
 def execute(argv,*a,**k):
  processes.append(argv[-1]);return run(argv,*a,**k)
 start=time.monotonic()
 with patch.object(Path,'read_bytes',readb),patch.object(Path,'read_text',readt),patch.object(build_watchface,'run',execute):result=fn()
 rows.append(dict(owner=label,seconds=time.monotonic()-start,reads=sum(counts.values()),bytes=sum(sizes.values()),uniqueFiles=len(counts),duplicateReads=sum(n-1 for n in counts.values()),maxReads=max(counts.values()),profiles=len(result['lock']['profiles']) if label=='toolchain' else None,selected=len(result['inputs']) if label=='source_state' else None,processes=processes,duplicates={k:n for k,n in counts.items() if n>1}))
print(json.dumps(rows,indent=2))
