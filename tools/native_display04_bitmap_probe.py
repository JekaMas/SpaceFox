#!/usr/bin/env python3
"""Build/run a source-bound native pending text/icon operation trace.

This is a partial trace, not an element-mask, bitmap, LOW, READY, preclip,
memory or release qualification. Caller owns and restores the SDK lane.
"""
import hashlib,json,subprocess,sys
from pathlib import Path
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.build_watchface import discover
from tools.native_display03_probe import inputs
from tools.run_native_tests import parse_output

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run(out,device):
 out=Path(out).resolve();out.mkdir(parents=True,exist_ok=False);ctx=discover();before=inputs()
 test=ROOT/'tests/fixtures/display04_bitmap_trace/TraceBitmap.mc';testhash=sha(test)
 ET.register_namespace('iq','http://www.garmin.com/xml/connectiq');tree=ET.parse(ROOT/'watchface/manifest.xml')
 tree.getroot().find('{http://www.garmin.com/xml/connectiq}application').set('id','c74f63410cce4584b2d9408d7e8e4e92');tree.write(out/'manifest.xml',encoding='utf-8',xml_declaration=True)
 fixture=json.loads((ROOT/'tests/fixtures/watch_refresh_cache/packets.json').read_text());rows={'D04Catalog':fixture['catalogs']['initial'],'D04Feed':{'raw':fixture['packets']['initial']}}
 res=out/'resources';res.mkdir()
 for name,value in rows.items():(res/(name+'.json')).write_text(json.dumps(value,ensure_ascii=False,separators=(',',':')))
 (res/'data.xml').write_text('<resources>'+''.join('<jsonData id="'+name+'" filename="'+name+'.json"/>' for name in rows)+'</resources>')
 jungle=out/'trace.jungle';jungle.write_text('project.manifest = '+str(out/'manifest.xml')+'\nbase.sourcePath = '+str(ROOT/'watchface/source')+';'+str(test.parent)+'\nbase.resourcePath = '+str(ROOT/'watchface/resources')+';'+str(res)+'\nbase.lang.rus = '+str(ROOT/'watchface/resources-rus')+'\n')
 package=out/'Trace.prg';cmd=[str(ctx['java']),'-Dfile.encoding=UTF-8','-jar',str(ctx['compiler']),'-f',str(jungle),'-d',device,'-o',str(package),'-y',str(ctx['key']),'-l','3','-O','2','-w','--unit-test']
 generated={str(q.relative_to(out)):sha(q) for q in [out/'manifest.xml',jungle,*sorted(res.glob('*'))]}
 (out/'precompile.json').write_text(json.dumps({'inputs':before,'testInput':testhash,'generated':generated,'compiler':cmd},indent=2)+'\n')
 compile=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'compile.log').write_text(compile.stdout)
 if compile.returncode:raise RuntimeError('compiler failed; see compile.log')
 if sha(test)!=testhash or before!=inputs() or any(sha(out/n)!=d for n,d in generated.items()):raise RuntimeError('input changed while compiling')
 launch=[str(ctx['java']),'-Dfile.encoding=UTF-8','-classpath',str(ctx['compiler']),'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux','-f',str(package),'-d',device,'-s',str(ctx['sdk']/'bin/shell'),'-t']
 with (out/'native.log').open('w') as log:proc=subprocess.run(launch,stdout=log,stderr=subprocess.STDOUT,text=True,timeout=120)
 result=parse_output((out/'native.log').read_text(),proc.returncode,('display04PendingBitmapTrace',))
 receipt={'status':result['status'],'test':result,'rawExit':proc.returncode,'packageSha256':sha(package),'launch':launch,'boundary':'pending EN/RU selected bitmap resource IDs, sizes, point and phase only; no READY, preclip, memory or release proof'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 if result['status']!='passed':raise RuntimeError('native trace failed')
 print(json.dumps(receipt))
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
