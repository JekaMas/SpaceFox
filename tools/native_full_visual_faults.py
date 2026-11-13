#!/usr/bin/env python3
"""Ordinary SDK full-storage and pointer-race controls over real app Storage.

Only this disposable namespace's diagnostic filler/attempt/provisional-pointer
events are controlled. Accepted feeds/floors/immutable objects are never edited.
All source admission, raw validation, reconstruction and rendering run unchanged.
No raw fixture literal, host behavior model, reset or external write is used.
"""
import argparse
from pathlib import Path
import sys
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import build_probe,IMPORTS,literal

def source(url,mode):
    return IMPORTS+'import Toybox.Timer;\n'+'''
(:background,:typecheck(false)) function sfrFaultLog(message){System.println("SFR_FAULT "+message+" owner="+NativeMetrics.ownerTag);}
(:background,:typecheck(false)) class SfrFaultService extends FeedService {
 function requestUrl(path as String) as String {var actual=path.equals("feed.json")?"versions/source/feed.json":path;sfrFaultLog("actualGet="+FeedService.requestUrl(actual));return FeedService.requestUrl(actual);}
}
(:background,:typecheck(false)) class SfrFaultQuiet extends FeedService {function onTemporalEvent() as Void {Background.deleteTemporalEvent();Background.exit(null);}}
(:typecheck(false)) class SfrObservedStore extends NativeStore {function initialize(){NativeStore.initialize();}function write(key,value){try{NativeStore.write(key,value);}catch(e){sfrFaultLog("WRITE_REFUSAL key="+key+" storageFull="+(e instanceof Lang.StorageFullException));throw e;}}}
(:typecheck(false)) class SfrRaceStore extends NativeStore {
 var injected=false;
 function initialize(){NativeStore.initialize();}
 function read(key){var value=NativeStore.read(key);if(!injected&&key.find("sf.incoming.feed.")==0&&!key.equals("sf.incoming.feed.processed")){var marker=NativeStore.read("sf.incoming.feed");marker["sequence"]+=1;NativeStore.write("sf.incoming.feed",marker);injected=true;sfrFaultLog("ROOT_RACE sequence="+marker["sequence"]);}return value;}
}
(:extendedCode,:typecheck(false)) class SfrFaultControl {
 var app;var mode;var timer;var checks=0;var retried=false;var counter=0;var tier=0;var padding=null;var counts=[0,0,0,0,0];
 function initialize(owner,chosen){app=owner;mode=chosen;timer=new Timer.Timer();timer.start(method(:ready),100,false);}
 function snapshot(label){var c=Application.Storage.getValue("sf.commit");var p=Application.Storage.getValue(app.feed.pinKey);var a=Application.Storage.getValue("sf.raster.active");sfrFaultLog("SNAPSHOT label="+label+" generation="+c["publisher"]["generation"]+" validation="+c["validation"]+" selectionUtc="+c["publisher"]["selectionValidatedUtc"]+" seal="+c["seal"]+" floor="+p["generation"]+" floorUtc="+p["selectionValidatedUtc"]+" selection="+a["selectionHash"]+" bitmap="+(app.view.downloaded!=null));NativeMetrics.sample("fault-snapshot");}
 function ready(){checks+=1;if(app.view.sfrBuild!=null||app.view.sfrRequested){if(checks<300){timer.start(method(:ready),100,false);}else{sfrFaultLog("FAILED sceneTimeout");}return;}if(app.view.downloaded==null&&!mode.equals("inspect-corrupt")&&!mode.equals("restore")){sfrFaultLog("FAILED incompleteScene");return;}snapshot("ready-"+mode);if(mode.equals("retry")&&!retried){retried=true;var prior=app.view.downloaded;app.reloadFeed();sfrFaultLog("RETRY reusedBitmap="+(prior!=null&&prior==app.view.downloaded));snapshot("after-retry");timer.start(method(:ready),100,false);return;}if(mode.equals("inspect-corrupt")){sfrFaultLog("CORRUPT_REOPEN bitmap="+(app.view.downloaded!=null));timer.stop();timer=null;}else if(mode.equals("corrupt")){corrupt();}else if(mode.equals("restore")){restore();}else if(mode.equals("fill")){Application.Storage.setValue("sf.control.fill.max",4096);timer.start(method(:fill),50,false);}else if(mode.equals("clean")){timer.start(method(:clean),50,false);}else if(mode.equals("full")){app.feed.store=new SfrObservedStore();try{Application.Storage.setValue("sf.attempt",{"base"=>app.feed.base,"utc"=>Time.now().value().toLong()-7200});}catch(e){sfrFaultLog("fullAttemptRefused="+e.getErrorMessage());}sfrFaultLog("WAITING fullSource manualTemporal=true");}else if(mode.equals("race")){app.feed.store=new SfrRaceStore();Application.Storage.setValue("sf.attempt",{"base"=>app.feed.base,"utc"=>Time.now().value().toLong()-7200});sfrFaultLog("WAITING rootRace manualTemporal=true");}else{timer.stop();timer=null;sfrFaultLog("COMPLETE mode="+mode);}}
 function corrupt(){var active=Application.Storage.getValue("sf.raster.active");var chosen=null;for(var i=0;i<active["refs"].size();i+=1){var r=active["refs"][i];if(r[0]==1){chosen=r;break;}}if(chosen==null){sfrFaultLog("FAILED noRasterToCorrupt");return;}var key="sf.obj."+chosen[1];var raw=Application.Storage.getValue(key);var hash=new NativeWireHash();hash.put(raw);if(!hash.digest().equals(chosen[1])){sfrFaultLog("FAILED originalRasterInvalid");return;}Application.Storage.setValue("sf.control.corrupt",{"key"=>key,"sha256"=>chosen[1],"raw"=>raw});var altered=raw.substring(0,raw.length()-1)+"!";Application.Storage.setValue(key,altered);var h=new NativeWireHash();h.put(altered);sfrFaultLog("CORRUPTED key="+key+" original="+chosen[1]+" altered="+h.digest()+" bytes="+h.count+" ownOptionalOnly=true acceptedMetadataUntouched=true");snapshot("corrupt-before-reopen");timer.stop();timer=null;}
 function restore(){var backup=Application.Storage.getValue("sf.control.corrupt");if(!(backup instanceof Dictionary)){sfrFaultLog("FAILED noCorruptBackup");return;}var h=new NativeWireHash();h.put(backup["raw"]);if(!h.digest().equals(backup["sha256"])||!backup["key"].equals("sf.obj."+backup["sha256"])){sfrFaultLog("FAILED corruptBackupInvalid");return;}Application.Storage.setValue(backup["key"],backup["raw"]);Application.Storage.deleteValue("sf.control.corrupt");sfrFaultLog("RESTORED key="+backup["key"]+" sha256="+backup["sha256"]+" diagnosticWrite=1");mode="inspect";checks=0;app.view.assetTried=false;app.view.prepareVisual();timer.start(method(:ready),100,false);}
 function fill(){var sizes=[4096,512,64,8,1];var start=System.getTimer();var done=0;while(done<4&&System.getTimer()-start<8){if(counter>=4096){sfrFaultLog("FAILED fillerBoundNotQuota");timer.stop();timer=null;return;}if(padding==null){padding="F";while(padding.length()<sizes[tier]){padding+=padding;}}try{Application.Storage.setValue("sf.control.fill."+counter,padding);counter+=1;counts[tier]+=1;done+=1;if(counter%128==0){sfrFaultLog("FILL progressKeys="+counter+" logicalBytes="+(counts[0]*4096+counts[1]*512+counts[2]*64+counts[3]*8+counts[4]));}}catch(e){if(!(e instanceof Lang.StorageFullException)){sfrFaultLog("FAILED unexpectedFillerException="+e.getErrorMessage());timer.stop();timer=null;return;}sfrFaultLog("QUOTA exception=Lang.StorageFullException tier="+sizes[tier]+" successful="+counts[tier]+" totalKeys="+counter+" error="+e.getErrorMessage());tier+=1;padding=null;if(tier>=5){snapshot("full");try{Application.Storage.setValue("sf.attempt",{"base"=>app.feed.base,"utc"=>Time.now().value().toLong()-7200});}catch(error){sfrFaultLog("fullAttemptRefused="+error.getErrorMessage());}timer.stop();timer=null;sfrFaultLog("WAITING fullSource manualTemporal=true");return;}}}timer.start(method(:fill),50,false);}
 function clean(){var start=System.getTimer();var done=0;while(counter<4096&&done<4&&System.getTimer()-start<8){var key="sf.control.fill."+counter;if(Application.Storage.getValue(key)!=null){Application.Storage.deleteValue(key);}counter+=1;done+=1;}if(counter<4096){timer.start(method(:clean),50,false);}else{Application.Storage.deleteValue("sf.control.fill.max");snapshot("cleaned");timer.stop();timer=null;sfrFaultLog("COMPLETE cleanup=true ownFillerOnly=true");}}
}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var control=null;var mode='''+literal(mode)+''';
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;NativeMetrics.traceStores=true;}
 function getServiceDelegate() as [System.ServiceDelegate]{return mode.equals("inspect")||mode.equals("clean")||mode.equals("corrupt")||mode.equals("inspect-corrupt")||mode.equals("restore")?[new SfrFaultQuiet()]:[new SfrFaultService()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView() as [Views] or [Views,InputDelegates]{Application.Properties.setValue("FeedBaseUrl",'''+literal(url)+''');if(mode.equals("fill")||mode.equals("race")||mode.equals("full")){Application.Storage.setValue("sf.attempt",{"base"=>'''+literal(url)+''',"utc"=>Time.now().value().toLong()});}var result=SpaceFoxApp.getInitialView();view.pendingLoader=method(:startControl);return result;}
 (:typecheck(disableBackgroundCheck)) function startControl() as Void {view.prepareVisual();control=new SfrFaultControl(self,mode);}
 (:typecheck(disableBackgroundCheck)) function onBackgroundData(data as Application.PersistableType) as Void {if(view==null){SpaceFoxApp.onBackgroundData(data);return;}var prior=view.downloaded;SpaceFoxApp.onBackgroundData(data);sfrFaultLog("afterAdmission mode="+mode+" reusedBitmap="+(prior!=null&&prior==view.downloaded));if(control!=null){control.snapshot("after-"+mode);}}
}
'''

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--mode',required=True,choices=['full','fill','inspect','clean','race','retry','corrupt','inspect-corrupt','restore']);p.add_argument('--url',required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--group',default='current',choices=['current']);a=p.parse_args();r=build_probe(a.output,source(a.url,a.mode),group=a.group);print(r['exitCode']);sys.exit(r['exitCode'])
