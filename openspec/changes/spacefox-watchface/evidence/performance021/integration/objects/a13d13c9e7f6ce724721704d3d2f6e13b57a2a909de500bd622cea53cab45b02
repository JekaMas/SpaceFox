#!/usr/bin/env python3
"""Compile one offline test-only operation mask using the real native renderer.

A compiled mask is not a visual result: runtime capture, black/white alpha
reconstruction, independent intended-region checking and input binding remain
necessary. This probe never contacts a provider or launches the simulator.
"""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_watchface import discover
from tools.native_display03_probe import inputs
from tools.native_element_isolation import isolate

IDS = ('map','art','flame','flag','point','header_rocket','header_separator',
       'header_operator','purpose','footer','date','clock','countdown','stale',
       'battery',*(f'field_{i}' for i in range(4)),*(f'icon_{i}' for i in range(4)))


def build(out, device, element, white):
    if element not in IDS or white not in (False, True):
        raise ValueError('unsupported mask selection')
    out = Path(out).resolve(); out.mkdir(parents=True, exist_ok=False)
    before = inputs(); context = discover()
    source = out/'source'; shutil.copytree(ROOT/'watchface/source', source)
    renderer = source/'SceneRenderer.mc'; renderer.write_text(isolate(renderer.read_text()))
    (source/'MaskObserver.mc').write_text('''import Toybox.Graphics;
import Toybox.Lang;
module MaskObserver {
 function visible(id as String) as Boolean {return id.equals("%s");}
 function clear(dc as Graphics.Dc) as Void {dc.setColor(%s,%s);dc.clear();}
}
''' % (element, 'Graphics.COLOR_WHITE' if white else 'Graphics.COLOR_BLACK', 'Graphics.COLOR_WHITE' if white else 'Graphics.COLOR_BLACK'))
    observer = out/'observer'; observer.mkdir()
    original = ROOT/'watchface/display04-observer/PointObserver.mc'
    (observer/'PointObserver.mc').write_bytes(original.read_bytes())
    tree=ET.parse(ROOT/'watchface/manifest.xml'); app=tree.getroot().find('{http://www.garmin.com/xml/connectiq}application')
    app.set('id','32b83a2963c24fa1938bd49af9527a62'); app.set('entry','Display04PointApp')
    ET.register_namespace('iq','http://www.garmin.com/xml/connectiq')
    tree.write(out/'manifest.xml',encoding='utf-8',xml_declaration=True)
    fixture=json.loads((ROOT/'tests/fixtures/watch_refresh_cache/packets.json').read_text())
    rows={'D04Catalog':fixture['catalogs']['initial'],'D04Feed':{'raw':fixture['packets']['initial']}}
    res=out/'resources';res.mkdir()
    for name,value in rows.items(): (res/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')))
    (res/'data.xml').write_text('<resources>'+''.join('<jsonData id="'+name+'" filename="'+name+'.json"/>' for name in rows)+'</resources>')
    jungle=out/'probe.jungle'; jungle.write_text('project.manifest = '+str(out/'manifest.xml')+'\nbase.sourcePath = '+str(source)+';'+str(observer)+'\nbase.resourcePath = '+str(ROOT/'watchface/resources')+';'+str(res)+'\nbase.lang.rus = '+str(ROOT/'watchface/resources-rus')+'\n')
    package=out/'MaskObserver.prg'
    command=[str(context['java']),'-Dfile.encoding=UTF-8','-jar',str(context['compiler']),'-f',str(jungle),'-d',device,'-o',str(package),'-y',str(context['key']),'-l','3','-O','2','-w']
    run=subprocess.run(command,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120)
    (out/'compile.log').write_text(run.stdout)
    if run.returncode: raise RuntimeError('mask observer compile failed: '+str(out/'compile.log'))
    if before != inputs(): raise RuntimeError('source changed during mask build')
    extra={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),ROOT/'tools/native_element_isolation.py',original)}
    receipt={'status':'compiled, not executed','device':device,'element':element,'whiteBackground':white,
             'command':command,'packageSha256':hashlib.sha256(package.read_bytes()).hexdigest(),
             'inputs':before|extra, 'transformedRendererSha256':hashlib.sha256(renderer.read_bytes()).hexdigest(),
             'boundary':'test-only pending observer; no runtime, READY, preclip, alpha or device proof'}
    (out/'build.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__ == '__main__':
    result=build(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4]=='white')
    print(json.dumps({'status':result['status'],'packageSha256':result['packageSha256']}))
