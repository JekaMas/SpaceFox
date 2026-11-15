import json,re,sys
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime,watch_refresh_cache_probe as probe
out=Path('/task/output/unresolved');out.mkdir(parents=True,exist_ok=True);original=probe.build_probe
extra=(probe.FIXTURE/'AdditionalAssertions.mc').read_text();start=extra.index('(:test,:typecheck(false)) function moreGenericRenderer');end=extra.index('(:test,:typecheck(false)) function moreNonfinitePosition',start);extra=extra[start:end]
def selected(output,source,**kw):
 source=re.sub(r'\(:test,:typecheck\(false\)\) function (?!refreshUnresolvedScene\b)',r'(:typecheck(false)) function ',source)
 source+=extra
 return original(output,source,**kw)
with patch.object(probe,'build_probe',selected),patch.object(probe,'discover',lambda:linux_probe.context),patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info):
 r=probe.build(out,diagnostic_unqualified=True)
r['expectedTests']=['refreshUnresolvedScene','moreGenericRenderer'];r['actualBase']='854a5a30a5bb021d2bac3e2f799b4f6401f269af';(out/'build.json').write_text(json.dumps(r,indent=2)+'\n');print('exit',r['exitCode']);sys.exit(r['exitCode'])
