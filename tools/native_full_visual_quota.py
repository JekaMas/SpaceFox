#!/usr/bin/env python3
"""Fill only owned diagnostic keys in a blank ordinary namespace.

Setup deliberately excludes packet/bitmap/resource residency; it is not a full
scene heap or native admission result. A later ordinary reopen supplies that
separate boundary. Only Lang.StorageFullException qualifies the actual quota.
"""
import argparse
from pathlib import Path
import sys
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import IMPORTS,build_probe,literal

def source(mode):
 return IMPORTS+'import Toybox.Timer;\n'+'''
(:background,:typecheck(false)) class SfrQuotaQuiet extends System.ServiceDelegate {function onTemporalEvent() as Void {Background.deleteTemporalEvent();Background.exit(null);}}
(:typecheck(false)) class SfrQuotaView extends WatchUi.WatchFace {var app;function initialize(owner){WatchUi.WatchFace.initialize();app=owner;}function onShow(){app.startQuota();}}
(:background,:typecheck(false)) class SfrRuntimeApp extends Application.AppBase {
 var phase='''+literal(mode)+''';var timer=null;var counter=0;var tier=0;var padding=null;var counts=[0,0,0,0,0];var removed=0;
 function initialize(){AppBase.initialize();NativeMetrics.enabled=true;}
 function getServiceDelegate() as [System.ServiceDelegate]{return [new SfrQuotaQuiet()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView() as [Views] or [Views,InputDelegates]{Background.deleteTemporalEvent();snapshot("begin-"+phase);return [new SfrQuotaView(self)];}
 (:typecheck(disableBackgroundCheck)) function startQuota(){if(timer==null){timer=new Timer.Timer();timer.start(method(:tick),50,false);}}
 function log(message){System.println("SFR_QUOTA "+message+" owner="+NativeMetrics.ownerTag);}
 function snapshot(label){var c=Application.Storage.getValue("sf.commit");var index=Application.Storage.getValue("sf.pins");var p=Application.Storage.getValue(index[0]);log("SNAPSHOT label="+label+" generation="+c["publisher"]["generation"]+" validation="+c["validation"]+" seal="+c["seal"]+" floor="+p["generation"]+" floorUtc="+p["selectionValidatedUtc"]);NativeMetrics.sample("quota-snapshot");}
 (:typecheck(disableBackgroundCheck)) function onBackgroundData(data as Application.PersistableType) as Void {Background.deleteTemporalEvent();}
 function tick(){var start=System.getTimer();var done=0;if(phase.equals("clean")||phase.equals("fill")){while(counter<4096&&done<32&&System.getTimer()-start<8){var key="sf.control.fill."+counter;if(Application.Storage.getValue(key)!=null){Application.Storage.deleteValue(key);removed+=1;}counter+=1;done+=1;}if(counter<4096){timer.start(method(:tick),50,false);return;}Application.Storage.deleteValue("sf.control.fill.max");log("CLEAN removed="+removed+" ownFillerOnly=true");snapshot("cleaned");if(phase.equals("clean")){timer.stop();timer=null;log("COMPLETE cleaned=true");return;}phase="filling";counter=0;Application.Storage.setValue("sf.control.fill.max",4096);}
 var sizes=[32000,4096,512,64,1];start=System.getTimer();done=0;while(done<4&&System.getTimer()-start<8){if(counter>=4096){log("FAILED boundNotQuota");return;}if(padding==null){padding=new [sizes[tier]]b;}try{Application.Storage.setValue("sf.control.fill."+counter,padding);counter+=1;counts[tier]+=1;done+=1;if(counter%32==0){log("FILL keys="+counter+" logicalBytes="+(counts[0]*32000+counts[1]*4096+counts[2]*512+counts[3]*64+counts[4]));}}catch(e){if(!(e instanceof Lang.StorageFullException)){log("FAILED unexpected="+e.getErrorMessage());return;}log("QUOTA exception=Lang.StorageFullException tier="+sizes[tier]+" successful="+counts[tier]+" keys="+counter+" error="+e.getErrorMessage());tier+=1;padding=null;if(tier>=5){snapshot("filled");timer.stop();timer=null;log("COMPLETE full=true logicalBytes="+(counts[0]*32000+counts[1]*4096+counts[2]*512+counts[3]*64+counts[4])+" keys="+counter+" setupBlank=true");return;}}}timer.start(method(:tick),50,false);}
}
'''
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--mode',choices=['fill','clean'],required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=build_probe(a.output,source(a.mode),group='current',source_files=['watchface/source/NativeMetrics.mc']);print(r['exitCode']);sys.exit(r['exitCode'])
