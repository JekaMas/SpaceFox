#!/usr/bin/env python3
"""Ordinary current-scene clock and four-field settings observation.

The app samples the real Simulator clock/fitness APIs and calls production
settings callbacks. It never supplies invented health values or a test clock.
"""
import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.native_current_runtime import PACKET, observe
from tools.native_full_visual_runtime import GROUPS, build_probe


def source(url):
    raw = observe(url)
    raw = raw.replace('var phase=0;', 'var phase=0;var firstUtc=null;var settingPhase=0;')
    raw = raw.replace('\n observer.stop();observer=null;\n', '\n firstUtc=Time.now().value();observer.start(method(:settingsPulse),1100,false);\n', 1)
    methods = '''
 (:typecheck(disableBackgroundCheck)) function settingsPulse(){
 var names=["steps","energy","heart","stress","calories","battery"];
 var selected=[];for(var i=0;i<4;i+=1){var index=(settingPhase+i)%6;Application.Properties.setValue("Field"+(i+1),index);selected.add(names[index]);}
 SpaceFoxApp.onSettingsChanged();Background.deleteTemporalEvent();
 var loaded=new SceneSettings(null).load();for(var j=0;j<4;j+=1){ensure(view.settings.slots[j].equals(selected[j])&&loaded.slots[j].equals(selected[j]),"four field property/load/callback mismatch");var value=view.fitness.display(view.values,selected[j]);ensure(value instanceof String,"metric unavailable formatting failed");}
 ensure(view.downloaded==rich&&feed.packet.validation==age&&feed.store.read("sf.commit")["seal"].equals(seal),"settings changed scene/source");
 ensure(view.sfrBuild==null&&!view.sfrRequested,"field settings rebuilt scene");
 var now=Time.now().value();var snapshot=view.snapshot();var clock=System.getClockTime();var hour=clock.hour;var expected=hour.format("%02d")+":"+clock.min.format("%02d");
 ensure(snapshot.localTime.equals(expected),"current native clock mismatch");ensure(now>firstUtc,"native clock did not advance");ensure(snapshot.remaining==null||snapshot.remaining>=0,"negative countdown");
 System.println("CURRENT_MAIN_FIELDS phase="+settingPhase+" slots="+selected+" local="+snapshot.localTime+" utc="+now+" countdown="+snapshot.countdown+" sameBitmap=true sameSource=true persistentProperties=true realFitnessApi=true ordinaryBytes="+System.getSystemStats().totalMemory+" owner="+NativeMetrics.ownerTag);
 WatchUi.requestUpdate();settingPhase+=1;if(settingPhase<6){observer.start(method(:settingsPulse),1100,false);}else{observer.stop();observer=null;System.println("CURRENT_MAIN_COMPLETE fields=4 roles=6 nativeClockAdvancing=true settingsCallbacks=6 sameBitmap=true sameSource=true owner="+NativeMetrics.ownerTag);}
 }
'''
    at = raw.rfind('\n}\n')
    return raw[:at]+methods+raw[at:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--identity', type=Path, default=PACKET/'identity.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    identity = json.loads(args.identity.read_text())
    GROUPS['main'] = (identity['uuid'], identity['basename'])
    record = build_probe(args.output, source(identity['url']), group='main')
    print(json.dumps({key: record[key] for key in ('exitCode', 'packageName', 'packageSha256')}))
    return record['exitCode']


if __name__ == '__main__':
    raise SystemExit(main())
