"""Build an isolated SDK test using real settings storage and app callback."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse, json
from tools.native_full_visual_runtime import IMPORTS, GROUPS, build_probe

def build(out):
    GROUPS['ux-settings']=('6a160f1e038a4e89a82b70f659e01016','SpaceFoxUxSettings016.prg')
    source=IMPORTS+'(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}\n'+(Path(__file__).resolve().parents[1]/'watchface/ux-tests/UxSettingsTests.mc').read_text()
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        result=build_probe(out,source,group='ux-settings',tests=True)
    result['expectedTests']=['uxSettingsCallbackAndReopen','uxCalendarCountdown','uxBackgroundVersionDiagnostic']
    (out/'build.json').write_text(json.dumps(result,indent=2)+'\n')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output)['exitCode'])
