"""Native resource/settings contracts, distinct from actual SDK render tests."""
import errno,gzip,hashlib,io,json,os,shutil,tarfile,tempfile,unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from tools.build_native_localization import generate,ROOT,resource_code
from tools.localization import load_locales,validate_locales
from tools.native_language_policy import software_locales
class NativeLocalizationResourcesTest(unittest.TestCase):
 def test_all36_and_settings_preserved(self):
  loaded=load_locales(ROOT);rows=loaded['catalog']['locales'];self.assertEqual(len(rows),36)
  settings=ET.parse(ROOT/'watchface/resources/settings/settings.xml');props=ET.parse(ROOT/'watchface/resources/settings/properties.xml')
  self.assertEqual({p.attrib['id'] for p in props.getroot()}, {'Field1','Field2','Field3','Field4','Language','ClockColor','CountdownColor','Field1Color','Field2Color','Field3Color','Field4Color','FeedBaseUrl'})
  language=next(s for s in settings.getroot() if s.attrib['propertyKey']=='@Properties.Language')
  options={int(x.attrib['value']):x.text for x in language.find('settingConfig')};self.assertEqual(options,{0:'@Strings.Locale0',1:'@Strings.Locale1',2:'@Strings.Locale2',3:'@Strings.Locale3',4:'@Strings.Locale4',36:'@Strings.Auto'})
  self.assertEqual(rows[0]['id'],'en');self.assertEqual(rows[1]['id'],'ru')
  for i,r in enumerate(rows):
   native=json.loads((ROOT/f'watchface/resources/json/Locale{i}.json').read_text());self.assertEqual(native['locale'],r['id']);self.assertEqual(native['timeUnknown'],loaded['strings'][r['id']]['timeUnknown'])
   folder=ROOT/'watchface'/('resources' if i==0 else 'resources-'+resource_code(r));self.assertTrue((folder/'strings/strings.xml').is_file())
 def test_generation_is_complete_and_repeatable(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);shutil.copytree(ROOT/'locales',root/'locales');shutil.copytree(ROOT/'watchface',root/'watchface')
   catalog=load_locales(ROOT)['catalog'];proof=catalog['supportPolicy']['softwareQualificationProof']
   if proof:
    for name,digest in proof['productionSources'].items():
     source=ROOT/name
     if not source.is_file():
      # These are historic proof inputs, removed from the current watch tree.
      # Authenticate their retained original Git snapshots; do not add unused
      # fonts back to the generated watch resources.
      self.assertIn(name,{'watchface/resources/fonts/Battery13.fnt','watchface/resources/fonts/Battery13.png'})
      archived=json.loads((ROOT/'tests/fixtures/public-proof-inputs/manifest.json').read_text())['inputs'][name+'@'+digest]
      self.assertEqual(archived['source'],name);self.assertEqual(archived['sha256'],digest)
      self.assertEqual(hashlib.sha256((ROOT/archived['path']).read_bytes()).hexdigest(),digest)
      self.assertNotIn('Battery13',(ROOT/'watchface/resources/fonts/fonts.xml').read_text())
      continue
     target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    corpus_dir=Path(proof['corpusPath']).parent;shutil.copytree(ROOT/corpus_dir,root/corpus_dir)
    receipt_dir=Path(proof['receiptPath']).parent;shutil.copytree(ROOT/receipt_dir,root/receipt_dir)
   if proof and 'uxDeltaProof' in proof:
    shutil.copytree(ROOT/'tools',root/'tools',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    shutil.copytree(ROOT/'tests',root/'tests',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
    for folder in ('assets','catalog','schemas'):
     if not (root/folder).exists():(root/folder).symlink_to(ROOT/folder,target_is_directory=True)
    (root/'release').mkdir(exist_ok=True)
    shutil.copyfile(ROOT/'release/native-admission-inputs.json',root/'release/native-admission-inputs.json')
    for name in json.loads((ROOT/'release/native-admission-inputs.json').read_text()):
     target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
     if not target.exists():shutil.copyfile(ROOT/name,target)
    ux=json.loads((ROOT/proof['uxDeltaProof']['path']).read_text())
    for name,digest in ux['sources'].items():
     target=root/name;target.parent.mkdir(parents=True,exist_ok=True)
     if not target.exists():
      source=ROOT/name
      if not source.is_file():
       # The active layered proof reconstructs the UX delta separately. Verify
       # the exact retained old source, but do not insert it into current output.
       self.assertIn(name,{'watchface/resources/fonts/Battery13.fnt','watchface/resources/fonts/Battery13.png','watchface/source/NativeMetrics.mc'})
       archived=json.loads((ROOT/'tests/fixtures/public-proof-inputs/manifest.json').read_text())['inputs'][name+'@'+digest]
       self.assertEqual(archived['source'],name);self.assertEqual(archived['sha256'],digest)
       self.assertEqual(hashlib.sha256((ROOT/archived['path']).read_bytes()).hexdigest(),digest)
      else:shutil.copyfile(source,target)
    if 'performance021Proof' in proof:
     # Materialize the authenticated retained parent closure, not the obsolete
     # assumption that all of its inputs are current productionSources.
     from tools.native_fields018_qualification import read as read_proof
     fields=json.loads(read_proof(ROOT,proof['fields018Proof']))
     parent=json.loads(gzip.decompress(read_proof(ROOT,fields['parentReceipt'])))
     with tarfile.open(fileobj=io.BytesIO(read_proof(ROOT,fields['parentDelta'])),mode='r:gz') as archive:
      delta={member.name for member in archive.getmembers()}
     outer=json.loads(read_proof(ROOT,proof['performance021Proof']))
     for name in parent['source_inputs_sha256']:
      relative=Path(name);self.assertFalse(relative.is_absolute() or '..' in relative.parts)
      if name in delta:continue
      target=root/relative
      if target.exists():continue
      source=ROOT/relative
      if not source.is_file():
       self.assertIn(name,outer['prior'])
       snapshot=outer['prior'][name];raw=(ROOT/snapshot['path']).read_bytes()
       self.assertEqual(hashlib.sha256(raw).hexdigest(),snapshot['sha256'])
       continue  # The outer validator installs this authenticated prior input.
      target.parent.mkdir(parents=True,exist_ok=True)
      try:os.link(source,target)
      except OSError as error:
       if error.errno!=errno.EXDEV:raise
       shutil.copyfile(source,target)
   elif proof and 'sourceDeltaProof' in proof:
    folder=Path(proof['sourceDeltaProof']['path']).parent;shutil.copytree(ROOT/folder,root/folder,dirs_exist_ok=True)
   initial={str(p.relative_to(root)):p.read_bytes() for p in (root/'watchface').rglob('*') if p.is_file()}
   generate(root)
   before={str(p.relative_to(root)):p.read_bytes() for p in (root/'watchface').rglob('*') if p.is_file()}
   self.assertEqual([name for name in sorted(set(initial)|set(before)) if initial.get(name)!=before.get(name)],[], 'first generation changed current watch inputs')
   generate(root);self.assertEqual(before,{str(p.relative_to(root)):p.read_bytes() for p in (root/'watchface').rglob('*') if p.is_file()})
   for name,raw in before.items():self.assertEqual(raw,(ROOT/name).read_bytes(),name)
 def test_missing_translation_or_placeholder_rejected(self):
  x=load_locales(ROOT);del x['strings']['ar']['timeUnknown']
  with self.assertRaises(ValueError):validate_locales(x['catalog'],x['strings'])
  x=load_locales(ROOT);x['strings']['he']['field']='שדה'
  with self.assertRaises(ValueError):validate_locales(x['catalog'],x['strings'])
 def test_release_excludes_unqualified_candidates(self):
  catalog=load_locales(ROOT)['catalog'];rows=catalog['locales'];qualified=software_locales(ROOT,catalog);expected=[resource_code(r) for r in rows if r['id']=='en' or r['id'] in qualified]
  ns={'iq':'http://www.garmin.com/xml/connectiq'};actual=[n.text for n in ET.parse(ROOT/'watchface/manifest.xml').findall('.//iq:language',ns)];self.assertEqual(actual,expected)
  self.assertEqual(resource_code({'garmin':'chs'}),'zhs');self.assertEqual(resource_code({'garmin':'cht'}),'zht')
if __name__=='__main__':unittest.main()
