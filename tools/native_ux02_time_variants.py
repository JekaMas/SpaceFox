"""Native LOW time variants; each real LOW transition advances one clock value."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.native_ux_visual_observation import source

def build(out,device):
    GROUPS['ux02-times']=('b110aeb8c913430ab84ee3fca4330d8d','SpaceFoxUx02Times.prg')
    program=source().replace('function localTimeText(){return "08:08";}', 'var index=-1;function localTimeText(){return index<0?"08:08":["11:11","00:00","23:59"][index%3];}')
    program=program.replace('(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {', '(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {var uxClock=null;')
    program=program.replace('var clock=new UxClock();view=', 'var clock=new UxClock();uxClock=clock;view=')
    program=program.replace('function onDisplayModeChanged(){SpaceFoxApp.onDisplayModeChanged();', 'function onDisplayModeChanged(){if(System.getDisplayMode()==System.DISPLAY_MODE_LOW_POWER){uxClock.index+=1;System.println("UX02_TIME value="+uxClock.localTimeText());}SpaceFoxApp.onDisplayModeChanged();')
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,program,group='ux02-times',device=device)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--device',default='fr165m');a=p.parse_args();raise SystemExit(build(a.output,a.device)['exitCode'])
