#!/usr/bin/env python3
"""Bounded real current HTTPS revalidation over the existing owned native cache."""
import argparse
import json
from pathlib import Path
from tools.native_full_visual_runtime import GROUPS, IMPORTS, build_probe


def source(base):
    return IMPORTS + 'import Toybox.Timer;\n' + '''
(:typecheck(false)) class HttpsProxy extends WatchUi.WatchFace {
 var app;function initialize(a){WatchFace.initialize();app=a;}
 function onLayout(dc){app.view.onLayout(dc);}function onShow(){app.view.onShow();app.begin();}function onHide(){app.view.onHide();}function onUpdate(dc){app.view.onUpdate(dc);}
}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var timer=null;var checks=0;var callbacks=0;var baselineCallbacks=0;var bitmap=null;var epoch=null;var generation=null;var seal=null;var beforeWrites=0;
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;}
 function ensure(ok,message){if(!ok){throw new Lang.InvalidValueException("CURRENT_HTTPS "+message);}}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){
 Application.Properties.setValue("FeedBaseUrl",''' + json.dumps(base) + ''');Application.Properties.setValue("Language",0);
 SpaceFoxApp.getInitialView();return [new HttpsProxy(self)];}
 (:typecheck(disableBackgroundCheck)) function begin(){if(timer!=null){return;}System.println("CURRENT_HTTPS BEGIN owner="+NativeMetrics.ownerTag);timer=new Timer.Timer();timer.start(method(:tick),100,false);}
 (:typecheck(disableBackgroundCheck)) function onBackgroundData(data as Application.PersistableType) as Void {callbacks+=1;SpaceFoxApp.onBackgroundData(data);}
 (:typecheck(disableBackgroundCheck)) function tick(){
 checks+=1;ensure(checks<1200,"bounded callback/scene timeout");ensure(System.getSystemStats().totalMemory==126784,"not ordinary heap");
 if(view.downloaded==null||view.sfrBuild!=null||view.sfrRequested){timer.start(method(:tick),100,false);return;}
 if(bitmap==null){bitmap=view.downloaded;epoch=feed.packet.validation;generation=feed.packet.document["publisher"]["generation"];seal=feed.store.read("sf.commit")["seal"];baselineCallbacks=callbacks;beforeWrites=feed.store.writes;
 // Manual client retry only: one public CDN read, never a provider request.
 Application.Storage.deleteValue("sf.attempt");System.println("CURRENT_HTTPS READY generation="+generation+" sourceEpoch="+epoch+" manualClientAttempt=true sameProductionService=true owner="+NativeMetrics.ownerTag);timer.start(method(:tick),100,false);return;}
 if(callbacks==baselineCallbacks){timer.start(method(:tick),100,false);return;}
 var current=feed.packet.document["publisher"]["generation"];var currentSeal=feed.store.read("sf.commit")["seal"];
 ensure(current>=generation&&feed.packet.validation>=epoch,"source authority regressed");ensure(view.downloaded==bitmap,"same current scene bitmap rebuilt");
 if(current==generation){ensure(feed.packet.validation==epoch&&currentSeal.equals(seal),"same generation refreshed source age/seal");}
 var snapshot=view.snapshot();ensure(snapshot.countdown.find("~")==0&&snapshot.remaining!=null,"actual minute countdown lost after callback");
 System.println("CURRENT_HTTPS COMPLETE beforeGeneration="+generation+" generation="+current+" beforeSourceEpoch="+epoch+" sourceEpoch="+feed.packet.validation+" sameBitmap=true sameSeal="+currentSeal.equals(seal)+" writes="+(feed.store.writes-beforeWrites)+" acceptedRawSha256="+feed.packet.wireHash+" launch="+feed.packet.launchId()+" display="+view.presentation.countdown(snapshot,true)+" callbacks="+(callbacks-baselineCallbacks)+" ordinaryBytes=126784 owner="+NativeMetrics.ownerTag);timer.stop();timer=null;
 }
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    GROUPS['https'] = ('5bf62b7a43d84afcb21e8d935670c104', 'SpaceFoxCurrentHttps20261113.prg')
    record = build_probe(args.output, source(args.base), group='https')
    print(json.dumps({key: record[key] for key in ('exitCode', 'ownerTag', 'packageSha256')}))
    return record['exitCode']


if __name__ == '__main__':
    raise SystemExit(main())
