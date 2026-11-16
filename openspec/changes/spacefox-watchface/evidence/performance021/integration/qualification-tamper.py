import json,os,shutil,tempfile
from pathlib import Path
from tools.native_integration022_qualification import ROOTS,validate
root=Path.cwd(); catalog=json.loads((root/'locales/catalog.json').read_text()); ref=catalog['supportPolicy']['softwareQualificationProof']['integration022Proof']; record=json.loads((root/ref['path']).read_text())
with tempfile.TemporaryDirectory(prefix='spacefox-022-tamper-') as td:
 t=Path(td)
 for p in root.iterdir():
  if p.is_file() and not p.is_symlink(): os.link(p,t/p.name)
 for n in ROOTS:
  if (root/n).is_dir(): shutil.copytree(root/n,t/n,copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 def damaged(name,expect):
  path=t/name; data=path.read_bytes(); path.unlink(); path.write_bytes(data+b'\nTAMPER\n')
  try:
   try: validate(t,catalog)
   except ValueError as e:
    assert expect in str(e),(name,str(e));print('PASS',name,str(e))
   else: raise AssertionError('accepted tampering: '+name)
  finally: path.unlink();shutil.copyfile(root/name,path)
 damaged('watchface/source/SpaceFoxApp.mc','watch input closure changed')
 damaged(record['evidence']['batchCorruption']['path'],'combined qualification input changed')
 damaged(next(iter(record['historical']['performance']['restore'].values()))['path'],'combined qualification input changed')
 bad=json.loads(json.dumps(catalog)); bad['supportPolicy']['primaryLocales'].append('xx')
 try: validate(t,bad)
 except ValueError as e:
  assert 'locale policy changed' in str(e); print('PASS changed catalog policy',str(e))
 else: raise AssertionError('accepted catalog tampering')
