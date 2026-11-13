#!/usr/bin/env python3
"""Build isolated ordinary or seed-test SFR1 probes from production owners.

Every UUID has a distinct PRG basename. A seed intentionally replaces network
only; a plain observer excludes raw constants and uses ordinary126784B runtime.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

if __package__ in (None,''):sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.build_watchface import ROOT,NS,discover,validate_manifest,validate_api_policy,run

GROUPS={'current':('2bf62b7a43d84afcb21e8d935670c101','SpaceFoxCurrent20261113.prg')}

def build_probe(output,source,*,group,tests=False,source_files=None,probe_resources=None):
    out=output.resolve();out.mkdir(parents=True,exist_ok=True);c=discover();validate_api_policy(ROOT,c['lock']);tree=validate_manifest(ROOT,c['lock']);app=tree.getroot().find('iq:application',NS);app.set('id',GROUPS[group][0]);app.set('entry','SfrRuntimeApp');app.set('name','@Strings.SfrProbeName');tree.write(out/'manifest.xml')
    selected_sources=list((ROOT/'watchface/source').rglob('*.mc')) if source_files is None else [ROOT/p for p in source_files]
    production_sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in selected_sources}
    source_path=str(ROOT/'watchface/source')+';'+str(out)
    if source_files is not None:
        source_path=str(out)
        for p in selected_sources:
            selected=out/'selected-production'/p.name;selected.parent.mkdir(parents=True,exist_ok=True);selected.write_bytes(p.read_bytes())
    production_resources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'watchface').rglob('*')) if p.is_file() and any(part.startswith('resources') for part in p.relative_to(ROOT/'watchface').parts)}
    source_set=hashlib.sha256(json.dumps(production_sources,sort_keys=True).encode()).hexdigest()
    owner_tag=GROUPS[group][0]+'|'+out.name+'|'+source_set[:12]
    if not tests:
        initializer='SpaceFoxApp.initialize();' if 'SpaceFoxApp.initialize();' in source else 'AppBase.initialize();'
        if initializer not in source:raise ValueError('ordinary probe must initialize a declared application base')
        source=source.replace(initializer,initializer+'NativeMetrics.ownerTag='+json.dumps(owner_tag)+';System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);',1)
    resources=out/'probe-resources';resources.mkdir(exist_ok=True);(resources/'probe.xml').write_text('<resources><strings><string id="SfrProbeName">SFR-'+group+'</string></strings></resources>')
    for name,raw in (probe_resources or {}).items():
        target=resources/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    probe_resource_hashes={str(p.relative_to(resources)):hashlib.sha256(p.read_bytes()).hexdigest() for p in resources.rglob('*') if p.is_file()}
    (out/'Probe.mc').write_text(source)
    (out/'monkey.jungle').write_text('project.manifest = '+str(out/'manifest.xml')+'\nbase.sourcePath = '+source_path+'\nbase.resourcePath = '+str(ROOT/'watchface/resources')+';'+str(resources)+'\nbase.lang.rus = '+str(ROOT/'watchface/resources-rus')+'\n')
    package=out/GROUPS[group][1];command=[str(c['java']),'-Dfile.encoding=UTF-8','-jar',str(c['compiler']),'-f',str(out/'monkey.jungle'),'-d','fr165','-o',str(package),'-y',str(c['key']),*c['lock']['compiler_options']]
    if tests:command.append('--unit-test')
    result=run(command,out);(out/'compile.log').write_text(result.stdout)
    # Retain exact source bytes beside package/MIR/debug artifacts. The .txt
    # suffix prevents SDK source discovery from compiling these copies again.
    for relative,expected in production_sources.items():
        raw=(ROOT/relative).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=expected:raise RuntimeError('production source changed during compile: '+relative)
        snapshot=out/'production-snapshot'/(relative+'.txt');snapshot.parent.mkdir(parents=True,exist_ok=True);snapshot.write_bytes(raw)
    record=dict(schemaVersion=1,group=group,tests=tests,ownerTag=owner_tag,sourceSetSha256=source_set,sourceHead=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),sourceDirty=bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT)),command=command,exitCode=result.returncode,packageName=package.name,packageSha256=hashlib.sha256(package.read_bytes()).hexdigest() if package.exists() else None,productionSources=production_sources,productionResources=production_resources,probeResources=probe_resource_hashes,probeSha256=hashlib.sha256(source.encode()).hexdigest(),applicationUuid=GROUPS[group][0],productionSourceScope="all-native" if source_files is None else "explicit-setup-only-subset",proofBoundary=__doc__)
    (out/'build.json').write_text(json.dumps(record,indent=2)+'\n')
    return record

IMPORTS='import Toybox.Application;\nimport Toybox.Lang;\nimport Toybox.WatchUi;\nimport Toybox.System;\nimport Toybox.Background;\nimport Toybox.Time;\n'


def literal(value):
    if isinstance(value,dict):return '{'+','.join(json.dumps(k)+'=>'+literal(v) for k,v in value.items())+'}'
    if isinstance(value,list):return '['+','.join(literal(v) for v in value)+']'
    return json.dumps(value,ensure_ascii=False)

def observer_source(url,*,network=False,cleanup=False,phase=None,force_source=False):
    init='Application.Properties.setValue("FeedBaseUrl",'+json.dumps('' if cleanup else url)+');'
    if force_source:init+='Application.Storage.deleteValue("sf.attempt");System.println("SFR_CONTROL forceSourceAttempt=true");'
    if cleanup:init='var old=Background.getTemporalEventRegisteredTime();var before=sfrCleanupSnapshot();Application.Properties.setValue("FeedBaseUrl","");Background.deleteTemporalEvent();var after=sfrCleanupSnapshot();System.println("SFR_CLEANUP oldTemporal="+(old==null?"null":old.value())+" newTemporal="+(Background.getTemporalEventRegisteredTime()==null?"null":"present")+" blank="+configuredFeedUrl().equals("")+" acceptedBefore="+before+" acceptedAfter="+after+" preserved="+before.equals(after)+" owner="+NativeMetrics.ownerTag);return [new WatchUi.WatchFace()];'
    else:init+='var result=SpaceFoxApp.getInitialView();'+('' if network else 'Background.deleteTemporalEvent();')+'return result;'
    quiet='' if network else 'function getServiceDelegate() as [System.ServiceDelegate]{return [new SfrQuiet()];}'
    service='' if network else '(:background,:typecheck(false)) class SfrQuiet extends FeedService{function onTemporalEvent() as Void{Background.deleteTemporalEvent();Background.exit(null);}}'
    if network and phase:
        if phase not in ('a','wide','source','changed','rollback','nopoint','unknown','empty','coarse'):raise ValueError('fixed diagnostic phase only')
        quiet='function getServiceDelegate() as [System.ServiceDelegate]{return [new SfrControlledService()];}'
        service='(:background,:typecheck(false)) class SfrControlledService extends FeedService{function requestUrl(path as String) as String{var actual=path.equals("feed.json")?"versions/'+phase+'/feed.json":path;var url=FeedService.requestUrl(actual);System.println("SFR_CONTROL actualGet="+url+" owner="+NativeMetrics.ownerTag);return url;}}'
    helper=''
    if cleanup:helper='(:typecheck(false)) function sfrCleanupSnapshot(){var store=new NativeStore();var hash=new NativeCanonical();var keys=["sf.commit","sf.recovery","sf.pins"];for(var i=0;i<keys.size();i+=1){hash.quoted(keys[i]);hash.emit(store.read(keys[i]));}return hash.digest();}\n'
    if cleanup:
        operation=init.removesuffix('return [new WatchUi.WatchFace()];')
        helper+='(:typecheck(false)) function sfrQuiesce(){'+operation+'}\n'
        init='sfrQuiesce();return [new WatchUi.WatchFace()];'
    callback='(:typecheck(disableBackgroundCheck)) function onBackgroundData(data as Application.PersistableType) as Void {sfrQuiesce();}' if cleanup else ''
    return IMPORTS+helper+'(:background,:typecheck(false)) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();NativeMetrics.enabled=true;}(:typecheck(disableBackgroundCheck)) function getInitialView() as [Views] or [Views,InputDelegates]{'+init+'}\n'+quiet+callback+'}\n'+service

def main():
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['observer','network','cleanup','run']);p.add_argument('--group',choices=GROUPS,default='current');p.add_argument('--profile',type=Path);p.add_argument('--url');p.add_argument('--phase');p.add_argument('--force-source',action='store_true');p.add_argument('--output',type=Path,required=True);p.add_argument('--label',default='runtime');p.add_argument('--timeout',type=int,default=600);a=p.parse_args()
    if a.mode=='run':
        out=a.output.resolve();b=json.loads((out/'build.json').read_text())
        expected={**b['productionSources'],**b.get('productionResources',{})}
        changed=[name for name,digest in expected.items() if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=digest]
        if b['productionSourceScope']=='all-native' and set(b['productionSources'])!={str(p.relative_to(ROOT)) for p in (ROOT/'watchface/source').rglob('*.mc')}:changed.append('all-native source closure')
        changed += ['probe-resource/'+name for name,digest in b.get('probeResources',{}).items() if not (out/'probe-resources'/name).is_file() or hashlib.sha256((out/'probe-resources'/name).read_bytes()).hexdigest()!=digest]
        if changed:raise RuntimeError('Refusing stale native package: '+', '.join(changed[:8]))
        c=discover();command=[str(c['java']),'-Dfile.encoding=UTF-8','-classpath',str(c['compiler']),'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux','-f',str(out/b['packageName']),'-d','fr165','-s',str(c['sdk']/'bin/shell')]
        if b['tests']:command.append('-t')
        start=time.monotonic()
        with (out/(a.label+'.log')).open('w') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT);print('pid',child.pid,flush=True)
            try:code=child.wait(timeout=a.timeout);status='exited'
            except subprocess.TimeoutExpired:child.terminate();code=child.wait();status='timed-out-terminated'
        record=dict(command=command,exitCode=code,status=status,elapsedSeconds=time.monotonic()-start)
        raw=(out/(a.label+'.log')).read_text()
        record['vmOutputObserved']=bool(raw.strip())
        record['observation']='no-vm-output' if not raw.strip() else 'native-failure' if any(x in raw for x in ('Error:','Out Of Memory','Stack Overflow')) else 'observed-output-requires-case-assertions'
        if b['tests']:
            from tools.run_native_tests import parse_output
            record['framework']=parse_output((out/(a.label+'.log')).read_text(),code,tuple(b.get('expectedTests',('fullVisualSeed',))))
        (out/(a.label+'-execution.json')).write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record));return
    if not a.url:p.error('--url required for build modes')
    source=observer_source(a.url,network=a.mode=='network',cleanup=a.mode=='cleanup',phase=a.phase,force_source=a.force_source);r=build_probe(a.output,source,group=a.group,tests=False);print(json.dumps({k:r[k] for k in ('exitCode','packageName','packageSha256','tests')}));sys.exit(r['exitCode'])

if __name__=='__main__':main()
