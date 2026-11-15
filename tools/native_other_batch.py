#!/usr/bin/env python3
"""Run maintained scene/incident/UX/localization test files independently.

The caller must own the exclusive SDK simulator lane and restore its state.
--compile-only does not launch the simulator. Historic results are not reused.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from xml.etree import ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.build_watchface import discover
from tools.run_native_tests import parse_output

FAMILIES=('scene-tests','incident-tests','ux-tests','localization-tests')
# Inventory is explicit so deleting a file or an assertion cannot look green.
EXPECTED={'watchface/incident-tests/DeliveryContinuityTests.mc': ['deliveryModeCallbacksAreIdempotent',
                                                         'deliveryRejectedResponseRetainsScene',
                                                         'deliveryPendingDeadlineDoesNotMove',
                                                         'deliverySceneEventsAndLateCompletion',
                                                         'deliveryVisualIdentityCases',
                                                         'deliveryVisualWaitsForMatchingBatch',
                                                         'deliveryRealRegisteredDeadline',
                                                         'deliveryDuplicateCallbackDoesNotInvalidateBuild'],
 'watchface/incident-tests/FirstInstallTests.mc': ['firstInstallDefaultsAndRetry',
                                                   'phoneTextTransportAndColors'],
 'watchface/localization-tests/LocaleTests.mc': ['localeSelectionPositive',
                                                 'localeSelectionNegative',
                                                 'localeFormatsPositive',
                                                 'localeFormatsNegative'],
 'watchface/scene-tests/NativeSceneTests.mc': ['sceneLayoutPositive',
                                               'sceneLayoutNegative',
                                               'sceneContextPositive',
                                               'sceneContextNegative',
                                               'sceneSettingsPositive',
                                               'sceneSettingsNegative',
                                               'sceneRocketPositive',
                                               'sceneRocketNegative',
                                               'sceneGeographyPositive',
                                               'sceneGeographyNegative',
                                               'sceneCompositionPositive',
                                               'sceneCompositionNegative',
                                               'sceneStatusPositive',
                                               'sceneStatusNegative',
                                               'sceneAnimationPositive',
                                               'sceneAodPositive',
                                               'sceneAodNegative',
                                               'sceneMetricsPositive',
                                               'sceneMetricsNegative',
                                               'sceneFontsPositive',
                                               'sceneFontsNegative'],
 'watchface/ux-tests/Ux03Tests.mc': ['ux03MatchingFallback'],
 'watchface/ux-tests/UxLowGuardTests.mc': ['independentLowGuard'],
 'watchface/ux-tests/UxRestoreTests.mc': ['uxAcceptedSceneDuringRestore',
                                          'uxNewIdentityAfterRestore'],
 'watchface/ux-tests/UxSettingsTests.mc': ['uxSettingsCallbackAndReopen', 'uxCalendarCountdown'],
 'watchface/ux-tests/UxUpgradeTests.mc': ['uxUpgradeAttemptVersion']}

def inventory():
    rows=[]
    for family in FAMILIES:
        files=sorted((ROOT/'watchface'/family).glob('*.mc'))
        if not files:raise ValueError('empty native family: '+family)
        for path in files:
            names=re.findall(r'\(:test[^\n]*\)\s*function\s+(\w+)',path.read_text())
            if not names or len(names)!=len(set(names)):raise ValueError('missing/duplicate tests: '+str(path))
            rows.append({'source':str(path.relative_to(ROOT)), 'tests':names})
    actual={row['source']:row['tests'] for row in rows}
    if actual!=EXPECTED:raise ValueError('native family/test inventory differs: '+repr(actual))
    return rows

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def inputs(source):
    paths=[p for p in (ROOT/'watchface/source').rglob('*.mc') if p.is_file()]
    paths += [p for p in (ROOT/'watchface/resources').rglob('*') if p.is_file()]
    paths += [p for d in ROOT.glob('watchface/resources-*') for p in d.rglob('*') if p.is_file()]
    paths += [source,ROOT/'watchface/manifest.xml',ROOT/'watchface/toolchain-lock.json',
              ROOT/'locales/catalog.json',ROOT/'tests/fixtures/watch_refresh_cache/packets.json',ROOT/'tools/build_watchface.py',ROOT/'tools/run_native_tests.py',Path(__file__)]
    return {str(path.relative_to(ROOT)):sha(path) for path in sorted(paths)}

def run(row,out,ctx,compile_only):
    out.mkdir(parents=True,exist_ok=False)
    sources=out/'tests';sources.mkdir()
    src=ROOT/row['source'];before=inputs(src);body=src.read_text()
    # Historical UX low guard is a source fragment intentionally included by an
    # earlier probe, so supply its imports here without changing its test body.
    if src.name=='UxLowGuardTests.mc':body='import Toybox.Graphics;import Toybox.Test;import Toybox.System;\n'+body
    (sources/src.name).write_text(body)
    tree=ET.parse(ROOT/'watchface/manifest.xml');tree.getroot().find('{http://www.garmin.com/xml/connectiq}application').set('id','5bb6fca4fe174f9da6bfdc2ac6d70b59')
    ET.register_namespace('iq','http://www.garmin.com/xml/connectiq');tree.write(out/'manifest.xml',encoding='utf-8',xml_declaration=True)
    fixture=json.loads((ROOT/'tests/fixtures/watch_refresh_cache/packets.json').read_text());rows={'DisplayCatalog':fixture['catalogs']['initial'],'DisplayInitial':{'raw':fixture['packets']['initial']},'DisplayMoved':{'raw':fixture['packets']['moved']}}
    res=out/'resources';res.mkdir()
    for name,value in rows.items():(res/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')))
    (res/'data.xml').write_text('<resources>'+''.join('<jsonData id="'+name+'" filename="'+name+'.json"/>' for name in rows)+'</resources>')
    j='project.manifest = '+str(out/'manifest.xml')+'\nbase.sourcePath = '+str(ROOT/'watchface/source')+';'+str(sources)+'\nbase.resourcePath = '+str(ROOT/'watchface/resources')+';'+str(res)+'\n'
    for locale in json.loads((ROOT/'locales/catalog.json').read_text())['locales']:
        if locale['id']=='en':continue
        code={'chs':'zhs','cht':'zht'}.get(locale['garmin'],locale['garmin']);j+='base.lang.'+code+' = '+str(ROOT/'watchface'/('resources-'+code))+'\n'
    jungle=out/'probe.jungle';jungle.write_text(j);package=out/'test.prg'
    command=[str(ctx['java']),'-Dfile.encoding=UTF-8','-jar',str(ctx['compiler']),'-f',str(jungle),'-d','fr165m','-o',str(package),'-y',str(ctx['key']),'-l','3','-O','2','-w','--unit-test']
    build=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'compile.log').write_text(build.stdout)
    result={'source':row['source'],'tests':row['tests'],'compileExit':build.returncode,'inputHashes':before,'compiledOnly':compile_only}
    if build.returncode:
        (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');raise RuntimeError('compile failed: '+row['source'])
    result['packageSha256']=sha(package)
    if not compile_only:
        launch=[str(ctx['java']),'-Dfile.encoding=UTF-8','-classpath',str(ctx['compiler']),'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux','-f',str(package),'-d','fr165m','-s',str(ctx['sdk']/'bin/shell'),'-t']
        with (out/'native.log').open('w') as log:
            try:test=subprocess.run(launch,text=True,stdout=log,stderr=subprocess.STDOUT,timeout=120)
            except subprocess.TimeoutExpired:
                (out/'timeout.json').write_text(json.dumps({'launchCommand':launch,'timeoutSeconds':120,'inputHashes':before,'packageSha256':sha(package)},indent=2)+'\n')
                raise
        result['native']=parse_output((out/'native.log').read_text(),test.returncode,tuple(row['tests']))
        if result['native']['status']!='passed':
            (out/'result.json').write_text(json.dumps(result,indent=2)+'\n');raise RuntimeError('native tests failed: '+row['source'])
    if inputs(src)!=before:raise RuntimeError('native inputs changed during run: '+row['source'])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--inventory',action='store_true');parser.add_argument('--compile-only',action='store_true');parser.add_argument('--source',action='append');parser.add_argument('--output',type=Path);parser.add_argument('--isolated-simulator',type=Path,help='launch and stop an owned simulator for each suite; caller owns the exclusive lane');args=parser.parse_args()
    rows=inventory()
    if args.inventory:
        print(json.dumps({'families':rows,'declaredTests':sum(len(row['tests']) for row in rows)},indent=2));return
    if args.output is None:parser.error('--output required')
    if args.source:
        selected=set(args.source);known={row['source'] for row in rows}
        if not selected<=known:parser.error('unknown source selector')
        rows=[row for row in rows if row['source'] in selected]
    ctx=discover();args.output.mkdir(parents=True,exist_ok=True);failures=[]
    for row in rows:
        simulator=None
        try:
            if args.isolated_simulator and not args.compile_only:
                simulator=subprocess.Popen([str(args.isolated_simulator)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(3)
                if simulator.poll() is not None:raise RuntimeError('owned simulator exited before suite')
            run(row,args.output/Path(row['source']).stem,ctx,args.compile_only);print('COMPILED' if args.compile_only else 'PASS',row['source'],flush=True)
        except Exception as error:failures.append(str(error));print('FAIL',error,flush=True)
        finally:
            if simulator is not None and simulator.poll() is None:
                simulator.terminate()
                try:simulator.wait(timeout=10)
                except subprocess.TimeoutExpired:simulator.kill();simulator.wait()
    print(json.dumps({'files':len(rows),'failures':failures,'compiledOnly':args.compile_only},indent=2))
    if failures:raise SystemExit(1)

if __name__=='__main__':main()
