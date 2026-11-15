#!/usr/bin/env python3
"""Freeze current DISPLAY04 software proof after actual observations exist.

No native run is performed here. Historical bytes are copied from the fixed
starting HEAD and old receipts remain immutable.
"""
import base64,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.native_display03_probe import inputs
from tools.native_display04_requalification import HOST_MODULES,evidence_inputs,support_inputs

def sha(b):return hashlib.sha256(b).hexdigest()
def item(path):
 data=path.read_bytes();return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(data)}
def main():
 catalog_path=ROOT/'locales/catalog.json';catalog=json.loads(catalog_path.read_text());old=catalog['supportPolicy']['softwareQualificationProof']
 if 'display04DeltaProof' in old:raise ValueError('current proof already exists')
 evidence=ROOT/'openspec/changes/spacefox-watchface/evidence/display04-whole-quality';target=evidence/'admission';target.mkdir(exist_ok=True);snapshot=target/'prior-bytes';snapshot.mkdir(exist_ok=True)
 def store(raw):
  data=base64.b64encode(raw);p=snapshot/(sha(data)+'.b64')
  if not p.exists():p.write_bytes(data)
  return {**item(p),'encoding':'base64'}
 prior_catalog=store(catalog_path.read_bytes())
 def names(args):return subprocess.check_output(['git',*args,'--','watchface','locales','tools','tests'],cwd=ROOT).decode().split('\0')[:-1]
 changed=names(['diff','--name-only','-z','HEAD']);untracked=names(['ls-files','--others','--exclude-standard','-z']);snapshots={}
 for name in changed:
  if name=='locales/catalog.json':continue
  result=subprocess.run(['git','show','HEAD:'+name],cwd=ROOT,capture_output=True)
  if result.returncode:
   untracked.append(name) # staged new file was absent from starting HEAD
   continue
  snapshots[name]=store(result.stdout)
 def row(folder,program,precompile=True):
  d=evidence/folder
  result={'receipt':item(d/'receipt.json'),'log':item(d/'native.log'),'program':item(d/program)}
  if precompile:result['precompile']=item(d/'precompile.json')
  return result
 fields=evidence/'final-current-native/current_fields_probe/receipt.json';r=json.loads(fields.read_text())
 host=target/'host.log'
 if not host.is_file():raise ValueError('actual host result required')
 record={'scope':'display04-current-primary-software','priorCatalog':prior_catalog,'priorSnapshots':snapshots,
  'priorAbsent':sorted(untracked),'nativeInputs':inputs(),'supportInputs':support_inputs(ROOT),'evidenceInputs':evidence_inputs(ROOT),
  'fieldsTests':r['tests']['expected_tests'],'nativeEvidence':{'display03':row('retained-display03-native','Display02Tests.prg',False),
  'rocketGuard':row('rocket-clipping/green','Display02Tests.prg'),
  'currentFields':row('final-current-native/current_fields_probe','Display02Tests.prg')},
  'display03HistoricalInputs':{name:item(evidence/'retained-display03-native/historical-inputs'/name) for name in ('watchface/source/SceneRenderer.mc','watchface/source/NativeVisualRenderer.mc','watchface/source/generated/NativeVersion.mc','tools/native_display03_probe.py')},
  'hostEvidence':{'modules':list(HOST_MODULES),'log':item(host)}}
 out=target/'proof.json';out.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
 old['display04DeltaProof']=item(out);catalog_path.write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n')
 print('Created current proof from observed native/host records; validation still required.')
if __name__=='__main__':main()
