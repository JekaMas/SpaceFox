"""Controlled same-content LOW phases through actual SDK callbacks."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.native_ux_visual_observation import source

def build(out,device):
    GROUPS['ux02-phases']=('b110aeb8c913430ab84ee3fca4330d91','SpaceFoxUx02Phases.prg')
    program=source().replace('class SfrRuntimeApp extends SpaceFoxApp {','class SfrRuntimeApp extends SpaceFoxApp {var phaseClock;var transitions=0;')
    program=program.replace('var clock=new UxClock();','var clock=new UxClock();phaseClock=clock;')
    program=program.replace('function onDisplayModeChanged(){SpaceFoxApp.onDisplayModeChanged();','function onDisplayModeChanged(){if(System.getDisplayMode()==System.DISPLAY_MODE_LOW_POWER){phaseClock.now=1794540000l+transitions*60;System.println("UX_PHASE phase="+(phaseClock.now/60)%4);transitions+=1;}SpaceFoxApp.onDisplayModeChanged();')
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,program,group='ux02-phases',device=device)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--device',default='fr165m');a=p.parse_args();raise SystemExit(build(a.output,a.device)['exitCode'])
