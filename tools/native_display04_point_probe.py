#!/usr/bin/env python3
"""Compile a test-key, offline captured-feed point observer; no simulator launch."""
import hashlib,json,subprocess,sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.build_watchface import discover
from tools.native_display03_probe import inputs

def build(out,device='fr165m'):
    out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);ctx=discover();before=inputs()
    paths=[ROOT/'watchface/display04-observer/PointObserver.mc',Path(__file__)]
    extra={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    tree=ET.parse(ROOT/'watchface/manifest.xml');app=tree.getroot().find('{http://www.garmin.com/xml/connectiq}application');app.set('id','72d83a2963c24fa1938bd49af9527d61');app.set('entry','Display04PointApp')
    ET.register_namespace('iq','http://www.garmin.com/xml/connectiq');tree.write(out/'manifest.xml',encoding='utf-8',xml_declaration=True)
    fixture=json.loads((ROOT/'tests/fixtures/watch_refresh_cache/packets.json').read_text());rows={'D04Catalog':fixture['catalogs']['initial'],'D04Feed':{'raw':fixture['packets']['initial']}}
    res=out/'resources';res.mkdir()
    for name,value in rows.items():(res/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')))
    (res/'data.xml').write_text('<resources>'+''.join('<jsonData id="'+name+'" filename="'+name+'.json"/>' for name in rows)+'</resources>')
    observer=out/'observer';observer.mkdir();(observer/'PointObserver.mc').write_bytes(paths[0].read_bytes());(observer/'CurrentJobs.mc').write_bytes((ROOT/'tests/native-runtime/CurrentJobs.mc').read_bytes())
    jungle=out/'probe.jungle';jungle.write_text('project.manifest = '+str(out/'manifest.xml')+'\nbase.sourcePath = '+str(ROOT/'watchface/source')+';'+str(observer)+'\nbase.resourcePath = '+str(ROOT/'watchface/resources')+';'+str(res)+'\nbase.lang.rus = '+str(ROOT/'watchface/resources-rus')+'\n')
    package=out/'PointObserver.prg';cmd=[str(ctx['java']),'-Dfile.encoding=UTF-8','-jar',str(ctx['compiler']),'-f',str(jungle),'-d',device,'-o',str(package),'-y',str(ctx['key']),'-l','3','-O','2','-w']
    r=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'compile.log').write_text(r.stdout)
    if r.returncode:raise RuntimeError('point observer compile failed')
    if before!=inputs() or any(hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=h for n,h in extra.items()):raise RuntimeError('source changed during point build')
    receipt={'status':'compiled, not executed','device':device,'command':cmd,'packageSha256':hashlib.sha256(package.read_bytes()).hexdigest(),'inputs':before|extra,'boundary':'test-key offline in-memory accepted real feed; no physical/phone/READY proof'}
    (out/'build.json').write_text(json.dumps(receipt,indent=2)+'\n');return receipt

if __name__=='__main__':
    result=build(sys.argv[1],sys.argv[2] if len(sys.argv)>2 else 'fr165m');print(json.dumps({'status':result['status'],'packageSha256':result['packageSha256']}))
