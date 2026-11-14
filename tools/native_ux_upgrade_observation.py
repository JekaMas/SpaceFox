"""Build the fresh-UUID native update cadence fixture."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
import json
from tools.native_full_visual_runtime import IMPORTS, GROUPS, build_probe

def build(out):
    GROUPS['ux-upgrade']=('a224157df73349feb22c4475d9781b23','SpaceFoxUxUpgrade.prg')
    source=IMPORTS+'import Toybox.Graphics;\n'+ '(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}\n'+(Path(__file__).resolve().parents[1]/'watchface/ux-tests/UxUpgradeTests.mc').read_text()
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        result=build_probe(out,source,group='ux-upgrade',tests=True)
    result['expectedTests']=['uxUpgradeAttemptVersion','uxAssetErrorDetailsFit']
    (out/'build.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output)['exitCode'])
