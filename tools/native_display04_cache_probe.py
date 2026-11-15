#!/usr/bin/env python3
"""Compile isolated seed/control apps; caller exclusively owns simulator state."""
import hashlib,json,subprocess,sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.build_watchface import discover
from tools.native_display03_probe import inputs

def build(out):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);ctx=discover();before=inputs()
 source=ROOT/'watchface/display04-observer/CacheControl.mc';source_hash=hashlib.sha256(source.read_bytes()).hexdigest();res=out/'resources';res.mkdir()
 fixture=json.loads((ROOT/'tests/fixtures/watch_refresh_cache/packets.json').read_text());rows={'D04Catalog':fixture['catalogs']['initial'],'D04Feed':{'raw':fixture['packets']['initial']},'D04Moved':{'raw':fixture['packets']['moved']}}
 for name,value in rows.items():(res/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')))
 (res/'data.xml').write_text('<resources>'+''.join('<jsonData id="'+name+'" filename="'+name+'.json"/>' for name in rows)+'</resources>')
 isolated=out/'source';isolated.mkdir();(isolated/'CacheControl.mc').write_bytes(source.read_bytes());products={}
 for kind,entry in [('seed','D04SeedApp'),('control','D04ControlApp')]:
  tree=ET.parse(ROOT/'watchface/manifest.xml');app=tree.getroot().find('{http://www.garmin.com/xml/connectiq}application');app.set('id','b454857f273844c4aef9e7fbc9f409e3');app.set('entry',entry);manifest=out/(kind+'.xml');ET.register_namespace('iq','http://www.garmin.com/xml/connectiq');tree.write(manifest,encoding='utf-8',xml_declaration=True)
  jungle=out/(kind+'.jungle');jungle.write_text('project.manifest = '+str(manifest)+'\nbase.sourcePath = '+str(ROOT/'watchface/source')+';'+str(isolated)+'\nbase.resourcePath = '+str(ROOT/'watchface/resources')+';'+str(res)+'\nbase.lang.rus = '+str(ROOT/'watchface/resources-rus')+'\n')
  package=out/(kind+'.prg');cmd=[str(ctx['java']),'-Dfile.encoding=UTF-8','-jar',str(ctx['compiler']),'-f',str(jungle),'-d','fr165m','-o',str(package),'-y',str(ctx['key']),'-l','3','-O','2','-w'];r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/(kind+'-compile.log')).write_text(r.stdout)
  if r.returncode:raise RuntimeError(kind+' compile failed')
  products[kind]={'sha256':hashlib.sha256(package.read_bytes()).hexdigest(),'command':cmd}
 if before!=inputs() or hashlib.sha256(source.read_bytes()).hexdigest()!=source_hash:raise RuntimeError('inputs changed while compiling')
 (out/'build.json').write_text(json.dumps({'status':'compiled only','products':products,'inputs':before,'observerSha256':source_hash,'uuid':'b454857f273844c4aef9e7fbc9f409e3','boundary':'test-key persisted accepted fixture; quiet background; no physical behavior'},indent=2)+'\n')
 print('seed/control compiled; not executed')
if __name__=='__main__':build(sys.argv[1])
