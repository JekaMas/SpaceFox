#!/usr/bin/env python3
"""Ordinary native current-protocol network callback observer.

Loopback changes requestUrl only. Production transport/cache/admission/scene
owners and FR165 ordinary heaps execute normally; this does not prove public
HTTPS/TLS delivery. Each phase is triggered by the Simulator temporal-event UI.
"""
import argparse,json,sys
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import build_probe,IMPORTS,literal,GROUPS
PHASES=['a','wide','warm','source','changed','rollback','unknown','unknownprofile','empty']
GENERATIONS=[1,2,2,3,4,4,4,4,8]
def source(base,loopback):
 return IMPORTS+'import Toybox.Timer;\n'+'''
(:background,:typecheck(false)) function currentPhase(){var index=Application.Storage.getValue("sf.control.index");if(!(index instanceof Number)||index<0||index>8){index=0;}return '''+literal(PHASES)+'''[index];}
(:background,:typecheck(false)) function currentLog(text){System.println("CURRENT_NETWORK "+text+" owner="+NativeMetrics.ownerTag);}
(:background,:typecheck(false)) class CurrentService extends FeedService {
 function requestUrl(path as String) as String {var phase=currentPhase();var actual=path.equals("feed.json")&&!phase.equals("a")?"versions/"+phase+"/feed.json":path;var url='''+literal(loopback)+'''+"/"+actual;currentLog("phase="+phase+" url="+url);return url;}
}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var timer=null;var checks=0;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;}
 function getServiceDelegate(){return [new CurrentService()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){Application.Properties.setValue("FeedBaseUrl",'''+literal(base)+''');if(Application.Storage.getValue("sf.control.index")==null){Application.Storage.setValue("sf.control.index",0);}var result=SpaceFoxApp.getInitialView();return result;}
 (:typecheck(disableBackgroundCheck)) function onBackgroundData(data as Application.PersistableType) as Void {var prior=view==null?null:view.downloaded;SpaceFoxApp.onBackgroundData(data);currentLog("phase="+currentPhase()+" afterAdmission reusedBitmap="+(prior!=null&&prior==view.downloaded)+" hasBitmap="+(view.downloaded!=null));checks=0;if(timer==null){timer=new Timer.Timer();}timer.start(method(:ready),100,false);}
 (:typecheck(disableBackgroundCheck)) function ready(){checks+=1;if(restorePending||view.sfrBuild!=null||view.sfrRequested){if(checks<400){timer.start(method(:ready),100,false);}else{currentLog("FAILED incompleteDecode");}return;}var index=Application.Storage.getValue("sf.control.index");var actual=feed.packet==null?0:feed.packet.document["publisher"]["generation"];var expected='''+literal(GENERATIONS)+'''[index];if(actual!=expected){currentLog("FAILED generation="+actual+" expected="+expected);return;}if(!currentPhase().equals("empty")&&view.downloaded==null){currentLog("FAILED bitmapMissing");return;}if(currentPhase().equals("empty")&&(view.context!=null||view.downloaded!=null)){currentLog("FAILED emptySceneRetained");return;}currentLog("READY phase="+currentPhase()+" generation="+actual+" bitmap="+(view.downloaded!=null)+" stale="+feed.packet.stale+" validation="+feed.packet.validation+" rescheduled="+feed.packet.rescheduled+" reads="+feed.store.reads+" writes="+feed.store.writes);NativeMetrics.sample("current-ready");if(index<8){index+=1;Application.Storage.setValue("sf.control.index",index);if(!currentPhase().equals("warm")){Application.Storage.deleteValue("sf.attempt");}currentLog("WAITING phase="+currentPhase()+" actualSimulatorTemporalRequired=true");}else{Background.deleteTemporalEvent();currentLog("COMPLETE phases=9 currentOnly=true temporal=false");}}
}
'''
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--base',default='https://current-native.invalid');p.add_argument('--loopback',default='http://127.0.0.1:18791');p.add_argument('--output',type=Path,required=True);a=p.parse_args();GROUPS['current-network']=('3bf62b7a43d84afcb21e8d935670c102','SpaceFoxCurrentNetwork20261113.prg');r=build_probe(a.output,source(a.base,a.loopback),group='current-network');print(r['exitCode']);sys.exit(r['exitCode'])
