"""Exercise native LOW status combinations after each real display transition."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.native_ux_visual_observation import source

def build(out,device):
    GROUPS['ux02-status']=('b110aeb8c913430ab84ee3fca4330d8f','SpaceFoxUx02Status.prg')
    program=source().replace('(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {','(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {var statusIndex=-1;')
    program=program.replace('{"Field4"=>5,"Field4Color"=>3}', '{"ClockColor"=>3,"CountdownColor"=>2,"Field4"=>5,"Field4Color"=>3}')
    program=program.replace('view.fitness=new UxFitness();', 'view.setContext(new SceneContext({"id"=>"status-test","target"=>clock.now+176523l,"precision"=>"minute"}));view.fitness=new UxFitness();')
    program=program.replace('function onDisplayModeChanged(){SpaceFoxApp.onDisplayModeChanged();','function onDisplayModeChanged(){if(System.getDisplayMode()==System.DISPLAY_MODE_LOW_POWER){statusIndex+=1;view.context.stale=statusIndex!=1;view.context.rescheduled=statusIndex!=0;System.println("UX02_STATUS index="+statusIndex+" stale="+view.context.stale+" rescheduled="+view.context.rescheduled);}SpaceFoxApp.onDisplayModeChanged();')
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,program,group='ux02-status',device=device)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--device',default='fr165m');a=p.parse_args();raise SystemExit(build(a.output,a.device)['exitCode'])
