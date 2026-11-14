"""Reconcile bounded UX03 pixels and fallback with unchanged UX02 evidence."""
import hashlib,json,shutil,tempfile
from pathlib import Path
BASE='openspec/changes/spacefox-watchface/evidence/ux03/'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def validate(root,catalog):
 from tools.native_ux02_requalification import validate as prior_validate
 from tools.run_native_tests import parse_output
 root=Path(root).resolve();proof=catalog['supportPolicy']['softwareQualificationProof']
 def checked(path,sha256):
  p=Path(path)
  if p.is_absolute() or '..' in p.parts or not (root/p).is_file() or digest(root/p)!=sha256:raise ValueError('UX03 proof input changed: '+path)
  return root/p
 record=json.loads(checked(**proof['ux03DeltaProof']).read_text())
 if record.get('scope')!='native-ux03-en-ru-fr165m-fr965' or record.get('status')!='passed':raise ValueError('UX03 proof incomplete')
 old=json.loads(checked(**record['priorCatalog']).read_text());oldproof=old['supportPolicy']['softwareQualificationProof']
 if {k:v for k,v in proof.items() if k!='ux03DeltaProof'}!=oldproof:raise ValueError('prior locale proof changed')
 comparable=json.loads(json.dumps(catalog));comparable['supportPolicy']['softwareQualificationProof']=oldproof
 if comparable!=old:raise ValueError('catalog outside UX03 proof changed')
 for name,sha in record['sources'].items():checked(name,sha)
 for name,sha in record['evidence'].items():checked(name,sha)
 expected={str(p.relative_to(root)) for p in (root/'watchface/source').rglob('*.mc')}
 if not expected<=set(record['sources']):raise ValueError('UX03 native closure incomplete')
 for name in ('unit','stale390','stale454'):
  build=json.loads((root/BASE/(name+'-build.json')).read_text())
  if build['exitCode']!=0 or build['probeSha256']!=digest(root/BASE/(name+'-probe.mc.txt')):raise ValueError('UX03 SDK build or probe differs: '+name)
  for source,sha in {**build['productionSources'],**build['productionResources']}.items():
   if record['sources'].get(source)!=sha:raise ValueError('UX03 SDK source differs: '+source)
 if parse_output((root/BASE/'unit-final.log').read_text(),1,('ux03MatchingFallback',))['status']!='passed':raise ValueError('UX03 native test failed')
 pixels=(root/BASE/'pixels.log').read_text()
 for name in ('test_low_selected_colors_and_lit_budget','test_stale_ink_marker_fields_and_gutters'):
  if name not in pixels or '\nOK\n' not in pixels:raise ValueError('UX03 pixels missing')
 with tempfile.TemporaryDirectory(prefix='spacefox-ux03-prior-') as d:
  target=Path(d)
  for folder in ('watchface','locales','tools','tests'):shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
  for folder in ('openspec','corpus','assets','catalog','schemas'):(target/folder).symlink_to(root/folder,target_is_directory=True)
  for name,item in record['priorSnapshots'].items():
   dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(checked(**item),dst)
  (target/'locales/catalog.json').write_text(json.dumps(old,indent=2)+'\n')
  if prior_validate(target,old)!=old['supportPolicy']['softwareQualifiedLocales']:raise ValueError('retained UX02 proof failed')
 return catalog['supportPolicy']['softwareQualifiedLocales']
