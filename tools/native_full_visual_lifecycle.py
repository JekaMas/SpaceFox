#!/usr/bin/env python3
"""One ordinary lifecycle observer over the real persisted complete scene.

UI supplies actual Simulator LOW/HIGH/OFF/hide/show events. The finite observer
reads state; it never simulates a power mode or starts animation itself.
The optional initial hold skips only the first diagnostic reload until an actual
LOW event. This provides a deterministic setup for actual HIGH-to-LOW partial
build cancellation; it is not used for timing or normal startup claims.
"""
import argparse
from pathlib import Path
import sys
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import IMPORTS,build_probe,literal

def source(url,hold_initial=False):
    return IMPORTS+'import Toybox.Timer;\n'+'''
(:background,:typecheck(false)) class SfrLifeQuiet extends FeedService {function onTemporalEvent() as Void {System.println("SFR_LIFE_QUIET calls=0 owner="+NativeMetrics.ownerTag);Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var observer=null;var last="";var checks=0;var completed=null;var holdInitial='''+literal(hold_initial)+''';
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;NativeMetrics.traceStores=false;}
 function getServiceDelegate() as [System.ServiceDelegate]{return [new SfrLifeQuiet()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView() as [Views] or [Views,InputDelegates]{Application.Properties.setValue("FeedBaseUrl",'''+literal(url)+''');var result=SpaceFoxApp.getInitialView();view.pendingLoader=method(:beginLife);return result;}
 (:typecheck(disableBackgroundCheck)) function beginLife() as Void {if(!holdInitial){SpaceFoxApp.reloadFeed();}else{Background.deleteTemporalEvent();System.println("SFR_LIFECYCLE diagnosticInitialHold=true owner="+NativeMetrics.ownerTag);}startPulse();}
 (:typecheck(disableBackgroundCheck)) function startPulse() as Void {if(System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){return;}checks=0;last="";if(observer==null){observer=new Timer.Timer();}observer.start(method(:pulse),50,true);}
 (:typecheck(disableBackgroundCheck)) function report(label) as Void {if(view==null){return;}if(completed==null&&view.downloaded!=null){completed=view.downloaded;}System.println("SFR_LIFECYCLE event="+label+" mode="+System.getDisplayMode()+" buildTimer="+(view.sfrTimer!=null)+" build="+(view.sfrBuild!=null)+" requested="+view.sfrRequested+" bitmap="+(view.downloaded!=null)+" sameBitmap="+(completed!=null&&completed==view.downloaded)+" animation="+view.animationRunning+" progress="+view.animationProgress+" fitnessTimer="+(view.fitnessTimer!=null)+" reads="+feed.store.reads+" writes="+feed.store.writes+" ms="+System.getTimer()+" owner="+NativeMetrics.ownerTag);}
 (:typecheck(disableBackgroundCheck)) function pulse() as Void {checks+=1;var key="state|"+(view.sfrTimer!=null)+"|"+(view.sfrBuild!=null)+"|"+view.sfrRequested+"|"+(view.downloaded!=null)+"|"+view.animationRunning+"|"+(view.fitnessTimer!=null);if(!key.equals(last)){last=key;report("state");}if(checks>=600){observer.stop();observer=null;report("observer-finite-end");}}
 (:typecheck(disableBackgroundCheck)) function onDisplayModeChanged() as Void {if(System.getDisplayMode()!=System.DISPLAY_MODE_HIGH_POWER){holdInitial=false;}SpaceFoxApp.onDisplayModeChanged();report("display");if(System.getDisplayMode()==System.DISPLAY_MODE_HIGH_POWER){startPulse();}else if(observer!=null){observer.stop();observer=null;}}
 (:typecheck(disableBackgroundCheck)) function onBackgroundData(data as Application.PersistableType) as Void {if(holdInitial){Background.deleteTemporalEvent();return;}SpaceFoxApp.onBackgroundData(data);if(view!=null){report("background");}}
}
'''

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--hold-initial',action='store_true');a=p.parse_args();r=build_probe(a.output,source(a.url,a.hold_initial),group='current');print(r['exitCode']);sys.exit(r['exitCode'])
