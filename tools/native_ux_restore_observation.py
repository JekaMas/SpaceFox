"""Build the identical focused restore test in either baseline or current tree."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse,json
from tools.native_full_visual_runtime import IMPORTS,GROUPS,build_probe

def build(out,fixture):
    GROUPS['ux-restore']=('6a160f1e038a4e89a82b70f659e01020','SpaceFoxUxRestore016.prg')
    program=IMPORTS+'(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}\n'+fixture.read_text()
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        result=build_probe(out,program,group='ux-restore',tests=True)
    result['expectedTests']=['uxAcceptedSceneDuringRestore','uxNewIdentityAfterRestore']
    (out/'build.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--fixture',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output,a.fixture)['exitCode'])
