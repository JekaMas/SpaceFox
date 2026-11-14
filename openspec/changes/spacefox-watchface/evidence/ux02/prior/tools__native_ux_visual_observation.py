"""Build a finite ordinary native screen observer without network or forged display mode."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import IMPORTS, GROUPS, build_probe

def source():
    return IMPORTS+'''import Toybox.Timer;
(:typecheck(false)) class UxClock extends WatchClock {var now=1794540000l;function utcSeconds(){return now;}function localTimeText(){return "08:08";}}
(:typecheck(false)) class UxFitness extends Fitness {
 function sample(now as Number or Long) as Dictionary<String, Number or Null> {return {"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"calories"=>2345,"battery"=>82};}
}
(:background,:typecheck(false)) class UxQuiet extends FeedService {function onTemporalEvent() as Void {Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;}
 function getServiceDelegate(){return [new UxQuiet()];}
 function getInitialView(){
  var clock=new UxClock();view=new SpaceFoxView(clock,new ScheduleState(clock.now+176523l,"minute"));view.fitness=new UxFitness();view.setSettings(new SceneSettings({"Field4"=>5,"Field4Color"=>3}));
  view.values={"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"calories"=>2345,"battery"=>82};
  view.syncDisplayMode(System.getDisplayMode());Background.deleteTemporalEvent();
  System.println("UX_VISUAL initial mode="+System.getDisplayMode());return [view];
 }
 function onDisplayModeChanged(){SpaceFoxApp.onDisplayModeChanged();System.println("UX_VISUAL mode="+System.getDisplayMode());}
}
'''

def build(out):
    GROUPS['ux-visual']=('6a160f1e038a4e89a82b70f659e01017','SpaceFoxUxVisual016.prg')
    with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
        return build_probe(out,source(),group='ux-visual')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output)['exitCode'])
