"""Observe actual LOW-mode draws and system battery without fixture values."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import IMPORTS, GROUPS, build_probe

def build(out):
 GROUPS['ux-battery']=('6a160f1e038a4e89a82b70f659e01024','SpaceFoxUxBattery016.prg')
 source=IMPORTS+'''import Toybox.Graphics;
(:typecheck(false)) class BatteryView extends SpaceFoxView {
 function initialize(){SpaceFoxView.initialize(new WatchClock(),new ScheduleState(null,"empty"));}
 function onUpdate(dc as Graphics.Dc) as Void {var before=aodMinute;SpaceFoxView.onUpdate(dc);if(System.getDisplayMode()==System.DISPLAY_MODE_LOW_POWER){System.println("UX_LOW_BATTERY mode="+System.getDisplayMode()+" now="+Time.now().value()+" before="+before+" after="+aodMinute+" system="+System.getSystemStats().battery+" displayed="+snapshot().battery+" timer="+(fitnessTimer!=null));}}
}
(:typecheck(false)) class BatteryProxy extends WatchUi.WatchFace {
 var app;var pending=false;function initialize(owner){WatchFace.initialize();app=owner;}
 function onLayout(dc){app.view.onLayout(dc);}function onShow(){app.view.onShow();}function onHide(){app.view.onHide();}
 function onUpdate(dc){if(pending){app.view.onLayout(dc);app.view.onShow();pending=false;}app.view.onUpdate(dc);}
}
(:background,:typecheck(false)) class BatteryQuiet extends FeedService {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var proxy=null;function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;}
 function getServiceDelegate(){return [new BatteryQuiet()];}
 function getInitialView(){Application.Properties.setValue("FeedBaseUrl","");view=new BatteryView();view.setSettings(new SceneSettings(null).load());view.syncDisplayMode(System.getDisplayMode());Background.deleteTemporalEvent();proxy=new BatteryProxy(self);return [proxy];}
 function onDisplayModeChanged(){if(System.getDisplayMode()==System.DISPLAY_MODE_LOW_POWER){view=new BatteryView();view.setSettings(new SceneSettings(null).load());view.syncDisplayMode(System.getDisplayMode());proxy.pending=true;WatchUi.requestUpdate();System.println("UX_LOW_COLD_FRESH mode="+System.getDisplayMode());}else{SpaceFoxApp.onDisplayModeChanged();}}
}
'''
 with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
  return build_probe(out,source,group='ux-battery')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();raise SystemExit(build(a.output)['exitCode'])
