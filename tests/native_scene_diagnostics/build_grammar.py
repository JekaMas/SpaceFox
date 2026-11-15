import json,sys,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools import generate_native_current_tests as gen
out=Path('/task/output/grammar');out.mkdir(parents=True,exist_ok=True);identity=uuid.uuid4().hex;runtime.GROUPS['grammar']=(identity,'CA5.prg');source=gen.source(Path('/task/profile-a'));chosen=('currentSceneGrammar','currentMotionGrammar')
for name in gen.EXPECTED:
 if name not in chosen:source=source.replace('(:test,:typecheck(false)) function '+name,'(:typecheck(false)) function '+name)
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 result=runtime.build_probe(out,source,group='grammar',tests=True)
result.update({'actualBase':'854a5a30a5bb021d2bac3e2f799b4f6401f269af','expectedTests':chosen,'admission':'diagnostic only'});(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'exit':result['exitCode'],'uuid':identity}));sys.exit(result['exitCode'])
