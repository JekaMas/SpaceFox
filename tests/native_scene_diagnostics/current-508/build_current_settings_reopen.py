"""Build same-UUID settings seed/reopen observer; no network or device claim."""
import json,sys,uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe,current_runtime as runtime
out=Path('/task/output/settings-reopen');out.mkdir(parents=True,exist_ok=True)
source=Path('/task/source/tests/native_scene_diagnostics/current-508/CurrentSettingsReopen.mc').read_text()
runtime.GROUPS['settings-reopen']=(uuid.uuid4().hex,'USR.prg')
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 result=runtime.build_probe(out,source,group='settings-reopen',tests=False)
result.update({'actualBase':'14b019f1','admission':'diagnostic only','boundary':'Same private simulator installed package; controlled Properties; no physical restart claim'})
(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'exit':result['exitCode'],'uuid':result['applicationUuid']}));sys.exit(result['exitCode'])
