"""Native resource/settings contracts, distinct from actual SDK render tests."""
import json,shutil,tempfile,unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from tools.build_native_localization import generate,ROOT,resource_code
from tools.localization import load_locales,validate_locales
from tools.native_language_policy import software_locales
class NativeLocalizationResourcesTest(unittest.TestCase):
 def test_all36_and_settings_preserved(self):
  loaded=load_locales(ROOT);rows=loaded['catalog']['locales'];self.assertEqual(len(rows),36)
  settings=ET.parse(ROOT/'watchface/resources/settings/settings.xml');props=ET.parse(ROOT/'watchface/resources/settings/properties.xml')
  self.assertEqual({p.attrib['id'] for p in props.getroot()}, {'Field1','Field2','Field3','Field4','Language','FeedBaseUrl'})
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
    for name in proof['productionSources']:
     target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
    corpus_dir=Path(proof['corpusPath']).parent;shutil.copytree(ROOT/corpus_dir,root/corpus_dir)
    receipt_dir=Path(proof['receiptPath']).parent;shutil.copytree(ROOT/receipt_dir,root/receipt_dir)
   generate(root)
   before={str(p.relative_to(root)):p.read_bytes() for p in (root/'watchface').rglob('*') if p.is_file()};generate(root);self.assertEqual(before,{str(p.relative_to(root)):p.read_bytes() for p in (root/'watchface').rglob('*') if p.is_file()})
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
