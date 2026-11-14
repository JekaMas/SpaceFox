"""SDK version handoff: isolated UUID with retained 0.1.5 production owners."""
import argparse, hashlib, json, subprocess
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from tools.build_watchface import discover, NS, ROOT
from tools.native_full_visual_runtime import IMPORTS, GROUPS, build_probe

UUID='e87c78f5319f4b3b9a000ad2a267e216'
OLD=Path('/Users/jekamas/.codex/tmp/spacefox-ux02-previous-source')
OLD_PROGRAM=IMPORTS+'''(:background,:typecheck(false)) class UxOldService extends FeedService {
 function request(path as String,callback as Method) as Void {System.println("HANDOFF_OLD request="+path);callback.invoke(-400,null);}
}
(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;}
 function getServiceDelegate(){return [new UxOldService()];}
 function getInitialView(){
  Application.Properties.setValue("FeedBaseUrl","https://jekamas.github.io/SpaceFox");
  Application.Properties.setValue("Field1",0);Application.Properties.setValue("Field2",1);Application.Properties.setValue("Field3",2);Application.Properties.setValue("Field4",5);
  Application.Properties.setValue("ClockColor",3);Application.Properties.setValue("CountdownColor",4);Application.Properties.setValue("Field4Color",3);
  var result=SpaceFoxApp.getInitialView();System.println("HANDOFF_OLD startup=0.1.5 settings=written");return result;
 }
}
'''
NEW_PROGRAM=IMPORTS+'''(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {
 function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;}
 function getInitialView(){
  var old=Application.Storage.getValue("sf.sync.status");var attempt=Application.Storage.getValue("sf.attempt");
  System.println("HANDOFF_NEW prior_status="+old+" attempt="+attempt+" field4="+Application.Properties.getValue("Field4")+" clock="+Application.Properties.getValue("ClockColor")+" countdown="+Application.Properties.getValue("CountdownColor")+" url="+Application.Properties.getValue("FeedBaseUrl"));
  var result=SpaceFoxApp.getInitialView();System.println("HANDOFF_NEW startup=0.1.6 view="+(view!=null));return result;
 }
 (:typecheck(disableBackgroundCheck)) function onBackgroundData(data as Application.PersistableType) as Void {
  SpaceFoxApp.onBackgroundData(data);System.println("HANDOFF_NEW after_background status="+Application.Storage.getValue("sf.sync.status")+" context="+(view!=null&&view.context!=null));
 }
}
'''
def old(out,force=False):
 out.mkdir(parents=True,exist_ok=True);ctx=discover();tree=ET.parse(OLD/'watchface/manifest.xml');app=tree.getroot().find('iq:application',NS);assert app.get('version')=='0.1.5';app.set('id',UUID);app.set('entry','SfrRuntimeApp');tree.write(out/'manifest.xml');program=OLD_PROGRAM.replace('var result=SpaceFoxApp.getInitialView();', 'Application.Storage.deleteValue("sf.attempt");var result=SpaceFoxApp.getInitialView();') if force else OLD_PROGRAM;(out/'Probe.mc').write_text(program)
 (out/'monkey.jungle').write_text('project.manifest = '+str(out/'manifest.xml')+'\nbase.sourcePath = '+str(OLD/'watchface/source')+';'+str(out)+'\nbase.resourcePath = '+str(OLD/'watchface/resources')+'\nbase.lang.rus = '+str(OLD/'watchface/resources-rus')+'\n')
 package=out/'SpaceFoxUxHandoffOld.prg';command=[str(ctx['java']),'-Dfile.encoding=UTF-8','-jar',str(ctx['compiler']),'-f',str(out/'monkey.jungle'),'-d','fr165m','-o',str(package),'-y',str(ctx['key']),*ctx['lock']['compiler_options']]
 r=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/'compile.log').write_text(r.stdout);sources={str(p.relative_to(OLD)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((OLD/'watchface').rglob('*')) if p.is_file()};record={'historicalSource':'18305ba295fc6e7895e1c0c30bea619bb96872d2','version':'0.1.5','applicationUuid':UUID,'device':'fr165m','command':command,'exitCode':r.returncode,'packageName':package.name,'packageSha256':hashlib.sha256(package.read_bytes()).hexdigest() if package.exists() else None,'sourceHashes':sources,'probeSha256':hashlib.sha256(program.encode()).hexdigest(),'forceEligibleAttempt':force};(out/'build.json').write_text(json.dumps(record,indent=2)+'\n');return r.returncode

def current(out,device="fr165m"):
 GROUPS['ux-handoff']=(UUID,'SpaceFoxUxHandoffNew.prg')
 with patch('tools.native_full_visual_runtime.validate_manifest',lambda root,lock:ET.parse(root/'watchface/manifest.xml')):
  return build_probe(out,NEW_PROGRAM,group='ux-handoff',device=device)['exitCode']
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['old','current']);p.add_argument('--output',type=Path,required=True);p.add_argument('--force-eligible',action='store_true');p.add_argument('--device',default='fr165m');a=p.parse_args();raise SystemExit(old(a.output.resolve(),a.force_eligible) if a.mode=='old' else current(a.output.resolve(),a.device))
