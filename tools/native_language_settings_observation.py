#!/usr/bin/env python3
"""Ordinary simulator settings observer; one captured DAY launch and test telemetry."""
import json
from pathlib import Path
import sys
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import GROUPS, build_probe, IMPORTS

SOURCE = IMPORTS + '''import Toybox.Timer;
(:background,:typecheck(false)) class LanguageQuiet extends System.ServiceDelegate {function onTemporalEvent(){Background.deleteTemporalEvent();Background.exit(null);}}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 var observer=null; var previous="";
 function initialize(){SpaceFoxApp.initialize();}
 function getServiceDelegate(){return [new LanguageQuiet()];}
 (:typecheck(disableBackgroundCheck)) function getInitialView(){
  if(Application.Storage.getValue("language-probe-init")==null){Application.Properties.setValue("Language",36);Application.Properties.setValue("Field1",0);Application.Properties.setValue("Field2",4);Application.Properties.setValue("Field3",2);Application.Properties.setValue("Field4",3);Application.Properties.setValue("FeedBaseUrl","");Application.Storage.setValue("language-probe-init",true);}
  var result=SpaceFoxApp.getInitialView();view.pendingLoader=method(:begin);return result;
 }
 (:typecheck(disableBackgroundCheck)) function begin(){
  Background.deleteTemporalEvent();view.setContext(new SceneContext({"id"=>"7bdc412b-c965-4517-a131-f57a01189803","rocket"=>"Ariane 64 Block 2","date"=>"2026-11-23","precision"=>"date"}));
  if(observer==null){observer=new Timer.Timer();}observer.start(method(:tick),2000,true);
 }
 (:typecheck(disableBackgroundCheck)) function tick(){
  var sys=System.getDeviceSettings();var current=view.snapshot();var c=System.getClockTime();var h=c.hour;var expected=h.format("%02d")+":"+c.min.format("%02d");
  if(!current.localTime.equals(expected)){throw new Lang.InvalidValueException("clock disagrees with simulator setting");}
  view.values={"steps"=>12345,"calories"=>12345,"heart"=>72,"stress"=>47,"energy"=>68,"battery"=>82};var s=view.settings;var p=view.presentation;var key=sys.systemLanguage+":"+s.language;
  if(!key.equals(previous)){previous=key;System.println("LANGUAGE_SETTINGS fixed24=true system="+sys.systemLanguage+" locale="+s.language+" presentation="+p.locale+" auto="+s.autoLanguage+" persisted="+Application.Properties.getValue("Language")+" clock="+current.localTime+" date="+p.countdown(current,true)+" fields="+s.slots+" testTelemetrySteps="+p.metric(view.fitness,view.values,"steps")+" owner="+NativeMetrics.ownerTag);}
  WatchUi.requestUpdate();
 }
}
'''
if __name__ == '__main__':
    out = Path(sys.argv[1]); GROUPS['language-settings'] = ('6af62b7a43d84afcb21e8d935670c105', 'LanguageSettingsObservation.prg')
    source = SOURCE
    if len(sys.argv) > 2 and sys.argv[2] == 'unknown':
        source = source.replace('7bdc412b-c965-4517-a131-f57a01189803', '3cdb9dee-b5cb-406c-bbd1-06a219930fb7').replace('Ariane 64 Block 2', 'Falcon 9 Block 5').replace('"date"=>"2026-11-23","precision"=>"date"', '"precision"=>"unknown"')
    if len(sys.argv) > 2 and sys.argv[2] == 'minute':
        source = source.replace('7bdc412b-c965-4517-a131-f57a01189803', '0f867f0c-5422-4d44-93b8-d7faaae7019b').replace('Ariane 64 Block 2', 'Starship V3').replace('"date"=>"2026-11-23","precision"=>"date"', '"target"=>1794609900,"precision"=>"minute"')
    if len(sys.argv) > 2 and sys.argv[2] == 'exact':
        source = source.replace('(:background,:typecheck(false)) class SfrRuntimeApp', 'class ProbeClock extends WatchClock {function utcSeconds() as Number{return 1789565449;}}\n(:background,:typecheck(false)) class SfrRuntimeApp')
        source = source.replace('var result=SpaceFoxApp.getInitialView();', 'view=new SpaceFoxView(new ProbeClock(),new ScheduleState(null,"empty"));view.setSettings(new SceneSettings(null).load());var result=[view];')
        source = source.replace('7bdc412b-c965-4517-a131-f57a01189803', 'd793ba47-faf5-4bab-a386-39a9ccc49c90').replace('Ariane 64 Block 2', 'Soyuz 2.1b').replace('"date"=>"2026-11-23","precision"=>"date"', '"target"=>1789565634,"precision"=>"exact"')
    if 'diagnostic' in sys.argv[2:]:
        source = source.replace('Background.deleteTemporalEvent();view.setContext(', 'Background.deleteTemporalEvent();view.presentation.qualificationMode=true;view.presentation.prepare(view.settings.language);view.setContext(')
    result = build_probe(out, source, group='language-settings')
    print(json.dumps({k: result[k] for k in ('exitCode','packageName','packageSha256')}))
    raise SystemExit(result['exitCode'])
