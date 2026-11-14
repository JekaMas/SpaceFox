"""100 percent battery in each actual active field on real display transitions."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.native_ux_visual_observation import source

def build(out):
    GROUPS['ux02-slots']=('b110aeb8c913430ab84ee3fca4330d90','SpaceFoxUx02Slots.prg')
    program=source().replace('"battery"=>82', '"battery"=>100')
    program=program.replace('(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {', '(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {var slot=-1;function assignSlot(){var d={};for(var i=1;i<=4;i+=1){d["Field"+i]=i-1;}d["Field"+(slot+1)]=5;if(slot==2){d["Field4"]=0;}d["Field"+(slot+1)+"Color"]=3;view.setSettings(new SceneSettings(d));System.println("UX02_SLOT slot="+(slot+1)+" battery=100");}')
    program=program.replace('function onDisplayModeChanged(){SpaceFoxApp.onDisplayModeChanged();','function onDisplayModeChanged(){if(System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){slot=(slot+1)%4;assignSlot();}SpaceFoxApp.onDisplayModeChanged();')
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,program,group='ux02-slots',device='fr165m')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output)['exitCode'])
