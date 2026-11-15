#!/usr/bin/env python3
"""Compile a test-key FR165M observer of natural WatchFace callbacks.

The proxy forwards only callbacks delivered by Garmin, with no synthetic draw,
clock or cache. It logs before/after the production renderer; its timing does not
measure a physical gesture, display scanout or Store build.
"""
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
import sys
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import GROUPS, IMPORTS, build_probe
GROUPS['display03']=('6195ca66a7024e309b9d292738f0d6ab','Display03Runtime.prg')

def source():
 return IMPORTS+'''(:background) module NativeMetrics { var ownerTag as String=""; }
(:typecheck(false)) class Display03Proxy extends WatchUi.WatchFace {
 var app;var wakeAt=null;function initialize(a){WatchFace.initialize();app=a;}
 function onLayout(dc){app.view.onLayout(dc);}
 function onShow(){System.println("D03_SHOW ms="+System.getTimer()+" display="+System.getDisplayMode());app.view.onShow();}
 function onHide(){app.view.onHide();}
 function onEnterSleep(){System.println("D03_SLEEP ms="+System.getTimer()+" display="+System.getDisplayMode());app.view.onEnterSleep();}
 function onExitSleep(){wakeAt=System.getTimer();System.println("D03_WAKE ms="+wakeAt+" display="+System.getDisplayMode());app.view.onExitSleep();}
 function onUpdate(dc){
   var started=System.getTimer();app.view.onUpdate(dc);var ended=System.getTimer();var v=app.view;
   var s=v.snapshot();System.println("D03_FRAME begin="+started+" end="+ended+" utc="+Time.now().value()+" display="+System.getDisplayMode()+" mode="+v.displayMode()+" countdown="+s.countdown+" low="+s.lowCountdown+" launch="+(v.context==null?"none":v.context.launchId)+" map="+(v.renderer!=null&&v.renderer.aodMap!=null)+" point="+(v.renderer!=null&&v.renderer.pin)+" ready="+(v.downloaded!=null)+" wake="+(wakeAt==null?-1:wakeAt));
   if(v.displayMode()==v.NOT_LOW){wakeAt=null;}
 }
}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 function initialize(){SpaceFoxApp.initialize();}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){SpaceFoxApp.getInitialView();return [new Display03Proxy(self)];}
 (:typecheck(disableBackgroundCheck)) function reloadFeed(){System.println("D03_RELOAD_BEGIN ms="+System.getTimer());SpaceFoxApp.reloadFeed();System.println("D03_RELOAD_END ms="+System.getTimer());}
 (:typecheck(disableBackgroundCheck)) function onDisplayModeChanged(){System.println("D03_DISPLAY ms="+System.getTimer()+" mode="+System.getDisplayMode());SpaceFoxApp.onDisplayModeChanged();}
}
'''
if __name__=='__main__':
 with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
  result=build_probe(Path(sys.argv[1]),source(),group='display03',device='fr165m')
 print('build exit',result['exitCode']);sys.exit(result['exitCode'])
