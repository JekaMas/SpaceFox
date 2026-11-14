"""No-feed settings callback, retained properties and real maintenance render."""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import argparse
from tools.native_full_visual_runtime import IMPORTS,GROUPS,build_probe

def source():
 return IMPORTS+'''import Toybox.Graphics;
(:typecheck(false)) class NodataFitness extends Fitness {function sample(now as Number or Long) as Dictionary<String,Number or Null>{return {"steps"=>12345,"energy"=>68,"heart"=>72,"stress"=>47,"calories"=>2345,"battery"=>82};}}
(:typecheck(false)) class NodataProxy extends WatchUi.WatchFace {
 var app;function initialize(a){WatchFace.initialize();app=a;}
 function onLayout(dc){app.view.onLayout(dc);}
 function onShow(){app.view.onShow();}
 function onHide(){app.view.onHide();}
 function onUpdate(dc){app.view.onUpdate(dc);System.println("UX_NODATA_DRAW maintenance="+app.view.visualMaintenance+" field4="+app.view.settings.slots[3]+" color="+app.view.settings.fieldColors[3]+" context="+(app.view.context!=null)+" countdown="+app.view.snapshot().countdown);}
}
(:background,:typecheck(false)) class NodataQuiet extends FeedService {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var maintenanceEntered=false;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;}
 function getServiceDelegate(){return [new NodataQuiet()];}
 function getInitialView(){
  var first=Application.Storage.getValue("ux.configured2")!=true;Application.Properties.setValue("FeedBaseUrl","");
  view=new SpaceFoxView(new WatchClock(),new ScheduleState(null,"empty"));view.fitness=new NodataFitness();
  if(first){Application.Properties.setValue("Field4",5);Application.Properties.setValue("Field4Color",3);onSettingsChanged();Application.Storage.setValue("ux.configured2",true);}
  else{view.setSettings(new SceneSettings(null).load());}
  view.syncDisplayMode(System.getDisplayMode());Background.deleteTemporalEvent();
  System.println("UX_NODATA_START first="+first+" propertyType="+(Application.Properties.getValue("Field4") instanceof Number)+" property="+Application.Properties.getValue("Field4")+" role="+view.settings.slots[3]+" color="+view.settings.fieldColors[3]);
  return [new NodataProxy(self)];
 }
 function onDisplayModeChanged(){SpaceFoxApp.onDisplayModeChanged();if(System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){if(!maintenanceEntered&&view.renderer!=null){maintenanceEntered=true;view.maintenanceTimeFont=view.renderer.fonts["time"];view.maintenanceMetricFont=view.renderer.fonts["metric"];view.maintenanceIcons=view.renderer.icons;view.visualMaintenance=true;view.releaseRenderer();WatchUi.requestUpdate();}}}
}
'''

def build(out,baseline=False):
 GROUPS['ux-nodata']=('6a160f1e038a4e89a82b70f659e01021' if baseline else '6a160f1e038a4e89a82b70f659e01022','SpaceFoxUxNodataB016.prg' if baseline else 'SpaceFoxUxNodataC016.prg')
 with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
  return build_probe(out,source(),group='ux-nodata')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--baseline',action='store_true');a=p.parse_args();raise SystemExit(build(a.output,a.baseline)['exitCode'])
