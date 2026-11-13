#!/usr/bin/env python3
"""Ordinary persisted reopen timing with production metrics/trace disabled.

A separate50ms foreground observer reads only builder/view fields. Requested-to-
ready is a conservative upper bound including the initial fallback/Timer yield.
First-build/decoded-map observations have <=one50ms polling interval uncertainty.
No screenshot dialog, raw fixture constant, decode patch or HTTP substitution.
"""
import argparse
from pathlib import Path
import sys
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import IMPORTS,build_probe,literal

def source(url,live=False):
    result=IMPORTS+'import Toybox.Timer;\n'+'''
(:background,:typecheck(false)) class SfrTimingQuiet extends FeedService {function onTemporalEvent() as Void {System.println("SFR_TIMING_QUIET calls=0 owner="+NativeMetrics.ownerTag);Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var observer=null;var requested=0;var buildObserved=0;var mapObserved=0;var writesBefore=0;var checks=0;var lastMaintenance=null;var fullBitmap=null;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=false;NativeMetrics.traceStores=false;}
 function getServiceDelegate() as [System.ServiceDelegate]{return [new SfrTimingQuiet()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView() as [Views] or [Views,InputDelegates]{Application.Properties.setValue("FeedBaseUrl",'''+literal(url)+''');var result=SpaceFoxApp.getInitialView();view.pendingLoader=method(:startTiming);return result;}
 (:typecheck(disableBackgroundCheck)) function startTiming() as Void {if(view.downloaded!=null){System.println("SFR_TIMING FAILED alreadyWarm owner="+NativeMetrics.ownerTag);return;}requested=System.getTimer();writesBefore=feed.store.writes;SpaceFoxApp.reloadFeed();observer=new Timer.Timer();observer.start(method(:observeTiming),50,true);System.println("SFR_TIMING requested="+requested+" metrics=false trace=false observerMs=50 owner="+NativeMetrics.ownerTag);}
 (:typecheck(disableBackgroundCheck)) function observeTiming() as Void {
  checks+=1;var now=System.getTimer();if(view.visualMaintenance&&view.maintenanceSecond!=null&&view.maintenanceSecond!=lastMaintenance){lastMaintenance=view.maintenanceSecond;System.println("SFR_TIMING updateRequestedUtc="+lastMaintenance+" observed="+now+" owner="+NativeMetrics.ownerTag);}if(buildObserved==0&&view.sfrBuild!=null){buildObserved=now;System.println("SFR_TIMING buildObserved="+now+" owner="+NativeMetrics.ownerTag);}
  if(mapObserved==0&&view.sfrBuild!=null&&view.sfrBuild.result.mapBitmap!=null){mapObserved=now;System.println("SFR_TIMING decodedMapObserved="+now+" requestToMapUpperMs="+(now-requested)+" owner="+NativeMetrics.ownerTag);}
  if(buildObserved!=0&&view.sfrBuild==null&&!view.sfrRequested){observer.stop();observer=null;fullBitmap=view.downloaded;var valid=view.downloaded instanceof NativeSfrRenderer&&view.downloaded.mapBitmap!=null&&view.downloaded.selectionHash.equals(feed.packet.bridge["selection"]["sha256"]);System.println("SFR_TIMING fullObserved="+now+" requestToFullUpperMs="+(now-requested)+" observedBuildToFullMs="+(now-buildObserved)+" decodedMapObserved="+mapObserved+" complete="+valid+" generation="+feed.packet.document["publisher"]["generation"]+" storeWriteDelta="+(feed.store.writes-writesBefore)+" owner="+NativeMetrics.ownerTag);Background.deleteTemporalEvent();return;}
  if(checks>600){observer.stop();observer=null;System.println("SFR_TIMING FAILED timeout owner="+NativeMetrics.ownerTag);}
 }
 (:typecheck(disableBackgroundCheck)) function onDisplayModeChanged() as Void {SpaceFoxApp.onDisplayModeChanged();if(view!=null){System.println("SFR_TIMING_DISPLAY mode="+System.getDisplayMode()+" sameBitmap="+(fullBitmap!=null&&view.downloaded==fullBitmap)+" decoding="+(view.sfrBuild!=null||view.sfrRequested)+" animation="+view.animationRunning+" reads="+feed.store.reads+" writes="+feed.store.writes+" ms="+System.getTimer()+" owner="+NativeMetrics.ownerTag);}}
}
'''

    if not live:result=result.replace('if(view.visualMaintenance&&view.maintenanceSecond!=null&&view.maintenanceSecond!=lastMaintenance){lastMaintenance=view.maintenanceSecond;System.println("SFR_TIMING updateRequestedUtc="+lastMaintenance+" observed="+now+" owner="+NativeMetrics.ownerTag);}','')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--url',required=True);p.add_argument('--group',choices=['current'],default='current');p.add_argument('--output',type=Path,required=True);p.add_argument('--live',action='store_true');a=p.parse_args();r=build_probe(a.output,source(a.url,a.live),group=a.group);print(r['exitCode']);sys.exit(r['exitCode'])
