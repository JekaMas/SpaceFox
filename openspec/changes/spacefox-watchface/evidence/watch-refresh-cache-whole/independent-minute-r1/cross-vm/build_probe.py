"""Build a single ordinary AppBase, current captured MIN persistence witness.

Only source-validation/publisher epochs change; the producer packet identities,
nominal target and immutable catalog remain captured inputs. No network runs.
"""
import hashlib,json,sys,uuid,time
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
sys.path[:0]=['/task','/task/source']
import linux_probe
from tools import native_full_visual_runtime as runtime
from tools.spacefox.wire import validate_current_feed
root=Path('/task/source');fixtures=root/'tests/fixtures/watch_refresh_cache';out=Path('/task/output/cross-vm');out.mkdir(parents=True,exist_ok=True)
source=json.loads((fixtures/'packets.json').read_bytes());packets={}
for label,original,epoch in (('A','initial',1794603899),('B','moved',1794603900),('Newer','refresh',1794612901),('BadInstance','refresh',1794612901)):
 doc=json.loads(source['packets'][original]);doc['launch']['source_validated_utc']=epoch;doc['publisher']['selectionValidatedUtc']=epoch
 if label=='BadInstance':doc['publisher']['instance']='b'*64
 raw=json.dumps(doc,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();parsed=validate_current_feed(raw,now=epoch)
 assert parsed['launch']['timing']['source_precision_id']==1 and parsed['launch']['timing']['exact_utc'] is None
 packets[label]=raw.decode()
cat=source['catalogs']['initial'];assert cat==source['catalogs']['moved']==source['catalogs']['refresh']
nonce=uuid.uuid4().hex;identity=uuid.uuid4().hex;wire=hashlib.sha256(packets['B'].encode()).hexdigest();runtime.GROUPS['cross-vm']=(identity,'C7.prg')
boundary=int(time.time())+90;boundary2=boundary+80;app=(fixtures/'CrossVmApp.mc').read_text().replace('@@NONCE@@',nonce).replace('@@HASH_B@@',wire).replace('@@BOUNDARY@@',str(boundary)).replace('@@BOUNDARY2@@',str(boundary2))
rows={'CrossCatalog':{'digest':cat['catalogDigest'],'raw':cat['catalog']},**{'Cross'+key:{'raw':value} for key,value in packets.items()}}
resources={};xml=['<resources>']
for name,value in rows.items():
 raw=json.dumps(value,ensure_ascii=False,separators=(',',':')).encode();resources[name+'.json']=raw;xml.append('<jsonData id="'+name+'" filename="'+name+'.json"/>')
resources['crossvm.xml']=''.join(xml).encode()+b'</resources>'
with patch.object(runtime,'discover',lambda:linux_probe.context),patch.object(runtime.subprocess,'check_output',linux_probe.git_info),patch.object(runtime,'validate_manifest',lambda r,l:ET.parse(r/'watchface/manifest.xml')):
 result=runtime.build_probe(out,app,group='cross-vm',tests=False,probe_resources=resources)
result['admissionValidation']='bypassed-diagnostic-only';result['boundary']='ordinary AppBase and actual SDK Storage; controlled source packets/time; no phone, physical, natural OS or release proof'
result['inputSha256']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (fixtures/'CrossVmApp.mc',fixtures/'packets.json',Path(__file__).resolve()) if p.is_relative_to(root)}
result['nonce']=nonce;result['phaseBoundaryEpoch']=boundary;result['mutationBoundaryEpoch']=boundary2;result['packetSha256']={k:hashlib.sha256(v.encode()).hexdigest() for k,v in packets.items()};result['expected']={'launchId':'ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b','Avalidation':1794603899,'Bvalidation':1794603900,'Btarget':1794611100,'wake':1794612901,'newValidation':1794612901,'Bwire':wire}
(out/'build.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'exitCode':result['exitCode'],'uuid':identity,'nonce':nonce,'Bwire':wire}));raise SystemExit(result['exitCode'])
