#!/usr/bin/env python3
"""Focused test-key SDK execution; caller owns simulator lease and restoration.

This diagnostic bypasses release admission only to produce its input evidence.
It never signs a release or claims device/Store qualification.
"""
import hashlib, json, subprocess, sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from tools.build_watchface import discover
from tools.run_native_tests import parse_output
NAMES=('currentLowRecovery',)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inputs():
 paths=[p for p in (ROOT/'watchface/source').rglob('*.mc') if p.is_file()]
 paths += [p for p in (ROOT/'watchface/resources').rglob('*') if p.is_file()]
 paths += [p for d in ROOT.glob('watchface/resources-*') for p in d.rglob('*') if p.is_file()]
 paths += [ROOT/'watchface/manifest.xml',ROOT/'watchface/toolchain-lock.json',ROOT/'watchface/current-recovery-tests/RecoveryTests.mc',ROOT/'tests/fixtures/watch_refresh_cache/packets.json']
 return {str(p.relative_to(ROOT)):sha(p) for p in sorted(paths)}
def run(out):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=True);ctx=discover();before=inputs()
 ET.register_namespace('iq','http://www.garmin.com/xml/connectiq');tree=ET.parse(ROOT/'watchface/manifest.xml');tree.getroot().find('{http://www.garmin.com/xml/connectiq}application').set('id','5bb6fca4fe174f9da6bfdc2ac6d70b59');tree.write(out/'manifest.xml',encoding='utf-8',xml_declaration=True)
 fixture=json.loads((ROOT/'tests/fixtures/watch_refresh_cache/packets.json').read_text());rows={'DisplayCatalog':fixture['catalogs']['initial'],'DisplayInitial':{'raw':fixture['packets']['initial']},'DisplayMoved':{'raw':fixture['packets']['moved']}}
 stale=json.loads(fixture['packets']['initial']);stale['publisher']['generation']=3;rows['DisplayStale']={'raw':json.dumps(stale,ensure_ascii=False,separators=(',',':'))}
 res=out/'resources';res.mkdir(exist_ok=True)
 for name,value in rows.items():(res/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')))
 (res/'data.xml').write_text('<resources>'+''.join('<jsonData id="'+name+'" filename="'+name+'.json"/>' for name in rows)+'</resources>')
 catalog=json.loads((ROOT/'locales/catalog.json').read_text());j='project.manifest = '+str(out/'manifest.xml')+'\nbase.sourcePath = '+str(ROOT/'watchface/source')+';'+str(ROOT/'watchface/current-recovery-tests')+'\nbase.resourcePath = '+str(ROOT/'watchface/resources')+';'+str(res)+'\n'
 for row in catalog['locales']:
  if row['id']=='en':continue
  code={'chs':'zhs','cht':'zht'}.get(row['garmin'],row['garmin']);j+='base.lang.'+code+' = '+str(ROOT/'watchface'/('resources-'+code))+'\n'
 (out/'probe.jungle').write_text(j);package=out/'Display02Tests.prg';cmd=[str(ctx['java']),'-Dfile.encoding=UTF-8','-jar',str(ctx['compiler']),'-f',str(out/'probe.jungle'),'-d','fr165','-o',str(package),'-y',str(ctx['key']),'-l','3','-O','2','-w','--unit-test'];build=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'compile.log').write_text(build.stdout)
 if build.returncode:raise RuntimeError('SDK compile failed')
 launch=[str(ctx['java']),'-Dfile.encoding=UTF-8','-classpath',str(ctx['compiler']),'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux','-f',str(package),'-d','fr165','-s',str(ctx['sdk']/'bin/shell'),'-t']
 with (out/'native.log').open('w') as log:
  try:test=subprocess.run(launch,text=True,stdout=log,stderr=subprocess.STDOUT,timeout=120)
  except subprocess.TimeoutExpired:
   (out/'timeout.json').write_text(json.dumps({'timeoutSeconds':120,'launchCommand':launch,'inputHashes':before,'packageSha256':sha(package)},indent=2)+'\n')
   raise
 result=parse_output((out/'native.log').read_text(),test.returncode,NAMES)
 if inputs()!=before:raise RuntimeError('native source changed during test')
 receipt={'status':result['status'],'buildCommand':cmd,'launchCommand':launch,'rawExit':test.returncode,'tests':result,'inputHashes':before,'packageSha256':sha(package),'testKeyBoundary':'disposable SDK test key','admission':'diagnostic bypass; current proof checked separately'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 if result['status']!='passed':raise RuntimeError('SDK tests incomplete or failed')
 print('PASS '+str(len(NAMES))+' source-bound tests; raw launcher exit '+str(test.returncode))
if __name__=='__main__':run(sys.argv[1])
