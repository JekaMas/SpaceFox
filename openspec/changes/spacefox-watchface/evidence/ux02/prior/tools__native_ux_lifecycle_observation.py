"""Real system display mode and clock; observer logs, never drives redraw."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.native_ux_visual_observation import source

def build(out):
    GROUPS['ux-life']=('6a160f1e038a4e89a82b70f659e01018','SpaceFoxUxLife016.prg')
    program=('import Toybox.Graphics;\n'+source()).replace('(:background,:typecheck(false)) class UxQuiet', '''(:typecheck(false)) class UxObservedView extends SpaceFoxView {
 function initialize(clock,schedule){SpaceFoxView.initialize(clock,schedule);}
 function onUpdate(dc as Graphics.Dc) as Void {System.println("UX_TICK mode="+System.getDisplayMode()+" now="+Time.now().value()+" previous="+aodMinute);SpaceFoxView.onUpdate(dc);}
}
(:background,:typecheck(false)) class UxQuiet''').replace('var clock=new UxClock();view=new SpaceFoxView(clock,new ScheduleState(clock.now+176523l,"minute"));','var clock=new WatchClock();view=new UxObservedView(clock,new ScheduleState(clock.utcSeconds().toLong()+176523l,"minute"));')
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,program,group='ux-life')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output)['exitCode'])
