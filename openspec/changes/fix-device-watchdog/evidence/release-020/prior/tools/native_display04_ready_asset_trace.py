#!/usr/bin/env python3
"""Run native unit trace on both locales using the real selected SFR closure.

The unit allowance is separate from watch-face heap; the test invokes the
unchanged production cache, full native builder/decoder and drawing owner.
Caller owns simulator lane and restoration.
"""
import hashlib,json,shutil,subprocess,sys
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
 template=ROOT/'tests/fixtures/display04_ready_asset_trace/ReadyAssetTrace.mc';template_hash=sha(template)
 previous=ROOT/'openspec/changes/spacefox-watchface/evidence/display04-whole-quality/ready-mask-en390'
 pre=json.loads((previous/'ready-precompile.json').read_text());observed=(previous/'precompile-generated/observer/PointObserver.mc').read_text()
 start=observed.index('if(data.hasKey(key)){return data[key];}')+len('if(data.hasKey(key)){return data[key];}');end=observed.index('return null;',start)
 branches=observed[start:end];source=template.read_text();assert source.count('/* ASSET_BRANCHES */')==1
 generated=out/'observer';generated.mkdir();(generated/'ReadyAssetTrace.mc').write_text(source.replace('/* ASSET_BRANCHES */',branches))
 resources=out/'resources';shutil.copytree(previous/'precompile-generated/resources',resources)
 for n,h in pre['generatedResources'].items():
  if sha(resources/n)!=h:raise ValueError('retained READY resource changed: '+n)
 ET.register_namespace('iq','http://www.garmin.com/xml/connectiq');tree=ET.parse(ROOT/'watchface/manifest.xml');tree.getroot().find('{http://www.garmin.com/xml/connectiq}application').set('id','5bb6fca4fe174f9da6bfdc2ac6d70b59');tree.write(out/'manifest.xml',encoding='utf-8',xml_declaration=True)
 jungle=out/'trace.jungle';jungle.write_text('project.manifest = '+str(out/'manifest.xml')+'\nbase.sourcePath = '+str(ROOT/'watchface/source')+';'+str(generated)+'\nbase.resourcePath = '+str(ROOT/'watchface/resources')+';'+str(resources)+'\nbase.lang.rus = '+str(ROOT/'watchface/resources-rus')+'\n')
 package=out/'Trace.prg';cmd=[str(ctx['java']),'-Dfile.encoding=UTF-8','-jar',str(ctx['compiler']),'-f',str(jungle),'-d',device,'-o',str(package),'-y',str(ctx['key']),'-l','3','-O','2','-w','--unit-test']
 files=[out/'manifest.xml',jungle,generated/'ReadyAssetTrace.mc',*sorted(resources.glob('*'))];gen={str(q.relative_to(out)):sha(q) for q in files}
 (out/'precompile.json').write_text(json.dumps({'inputs':before,'testInput':template_hash,'generated':gen,'compiler':cmd,'capturedSelection':pre['selectionSha256'],'retainedReadyPrecompileSha256':sha(previous/'ready-precompile.json')},indent=2)+'\n')
 compile=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'compile.log').write_text(compile.stdout)
 if compile.returncode:raise RuntimeError('asset trace compile failed')
 if sha(template)!=template_hash or before!=inputs() or any(sha(out/n)!=h for n,h in gen.items()):raise RuntimeError('asset trace inputs changed')
 launch=[str(ctx['java']),'-Dfile.encoding=UTF-8','-classpath',str(ctx['compiler']),'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux','-f',str(package),'-d',device,'-s',str(ctx['sdk']/'bin/shell'),'-t']
 with (out/'native.log').open('w') as log:proc=subprocess.run(launch,stdout=log,stderr=subprocess.STDOUT,text=True,timeout=180)
 result=parse_output((out/'native.log').read_text(),proc.returncode,('display04RealReadyAssetTrace',));receipt={'status':result['status'],'test':result,'rawExit':proc.returncode,'packageSha256':sha(package),'launch':launch,'boundary':'unit allowance; real production selection/build/decoder and actual EN/RU draw calls, no physical or stock-memory proof'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
 if result['status']!='passed':raise RuntimeError('native READY asset trace failed')
 print(json.dumps(receipt))
if __name__=='__main__':run(sys.argv[1],sys.argv[2])
