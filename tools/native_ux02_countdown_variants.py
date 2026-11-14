"""LOW Russian numeric cases, including the real latest minute-precision target."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.native_ux_visual_observation import source

def build(out):
    GROUPS['ux02-counts']=('b110aeb8c913430ab84ee3fca4330d8e','SpaceFoxUx02Counts.prg')
    # 2026-11-29T15:49Z, Cygnus CRS-2 NG-25, minute precision, from
    # retained real corpus; base 2026-11-13T03:20Z -> 396:29:00.
    program=source().replace('function utcSeconds(){return now;}', 'var index=-1;function utcSeconds(){return now+(index<1?0:index==1?1427281l:1427399l);}')
    program=program.replace('clock.now+176523l', 'clock.now+1427340l').replace('{"Field4"=>5,"Field4Color"=>3}', '{"Language"=>1,"Field4"=>5,"Field4Color"=>3}')
    program=program.replace('(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {', '(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {var uxClock=null;')
    program=program.replace('var clock=new UxClock();view=', 'var clock=new UxClock();uxClock=clock;view=')
    program=program.replace('function onDisplayModeChanged(){SpaceFoxApp.onDisplayModeChanged();', 'function onDisplayModeChanged(){if(System.getDisplayMode()==System.DISPLAY_MODE_LOW_POWER){uxClock.index+=1;if(uxClock.index==3){view.setContext(null);}System.println("UX02_COUNT index="+uxClock.index);}SpaceFoxApp.onDisplayModeChanged();')
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,program,group='ux02-counts',device='fr165m')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output)['exitCode'])
