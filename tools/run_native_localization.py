#!/usr/bin/env python3
"""Isolated, exact-source native locale cohort. Launch requires simulator lease."""
import argparse,hashlib,json,os,subprocess,sys,uuid
from pathlib import Path
if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.build_watchface import ROOT,NS,discover,validate_manifest,run

def build(out,source=None,tests=True,include_scene=False):
 out=out.resolve();out.mkdir(parents=True,exist_ok=True);c=discover();tree=validate_manifest(ROOT,c['lock']);app=tree.find('iq:application',NS);uid=uuid.uuid4().hex;app.set('id',uid);app.set('entry','LocaleCohortApp');tree.write(out/'manifest.xml')
 src=source or 'import Toybox.Application;import Toybox.WatchUi; class LocaleCohortApp extends Application.AppBase { function initialize(){AppBase.initialize();} (:typecheck(disableBackgroundCheck)) function getInitialView(){return [new WatchUi.WatchFace()];}}'
 (out/'Cohort.mc').write_text(src)
 sourcepaths=[str(ROOT/'watchface/source'),str(out)]
 if tests:sourcepaths.append(str(ROOT/'watchface/localization-tests'))
 if include_scene:sourcepaths.append(str(ROOT/'watchface/scene-tests'))
 (out/'monkey.jungle').write_text('project.manifest = '+str(out/'manifest.xml')+'\nbase.sourcePath = '+';'.join(sourcepaths)+'\nbase.resourcePath = '+str(ROOT/'watchface/resources')+'\n')
 package=out/('LocaleCohort'+uid[:10]+'.prg');cmd=[str(c['java']),'-Dfile.encoding=UTF-8','-jar',str(c['compiler']),'-f',str(out/'monkey.jungle'),'-d','fr165','-o',str(package),'-y',str(c['key']),*c['lock']['compiler_options']]+(['--unit-test'] if tests else [])
 result=run(cmd,out);(out/'compile.log').write_text(result.stdout)
 sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for folder in ['watchface/source','watchface/localization-tests','watchface/resources']+(['watchface/scene-tests'] if include_scene else []) for p in (ROOT/folder).rglob('*') if p.is_file()}
 record=dict(uuid=uid,package=str(package),tests=tests,compileExit=result.returncode,sourceHead=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),sourceHashes=sources,sourceDirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)),command=cmd)
 (out/'build.json').write_text(json.dumps(record,indent=2)+'\n');print('compile',result.returncode,package.name);return result.returncode

def execute(out,only=None):
 r=json.loads((out/'build.json').read_text())
 changed=[name for name,digest in r['sourceHashes'].items() if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
 if changed:raise RuntimeError('Refusing stale compiled native cohort: '+', '.join(changed[:8]))
 c=discover();cmd=[str(c['java']),'-Dfile.encoding=UTF-8','-classpath',str(c['compiler']),'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux','-f',r['package'],'-d','fr165','-s',str(c['sdk']/'bin/shell')]+(['-t'] if r['tests'] else [])
 if only:cmd.append(only)
 label='runtime' if only is None else only
 proc=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=300);(out/(label+'.log')).write_text(proc.stdout);record=dict(rawExit=proc.returncode,command=cmd)
 if r['tests']:
  from tools.run_native_tests import parse_output
  record['framework']=parse_output(proc.stdout,proc.returncode,(only,) if only else ('localeSelectionPositive','localeSelectionNegative','localeFormatsPositive','localeFormatsNegative'))
 (out/(label+'-execution.json')).write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record))
 if record.get('framework',{}).get('status')=='passed':
  for name in record['framework']['expected_tests']:print('native::'+name)
  return 0
 return proc.returncode or 1
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('mode',choices=['build','run','check']);p.add_argument('--output',type=Path,required=True);p.add_argument('--only');p.add_argument('--include-scene',action='store_true');a=p.parse_args()
 if a.mode=='check':
  out=a.output/uuid.uuid4().hex
  code=build(out,include_scene=a.include_scene)
  sys.exit(code if code else execute(out,a.only))
 sys.exit(build(a.output,include_scene=a.include_scene) if a.mode=='build' else execute(a.output,a.only))
