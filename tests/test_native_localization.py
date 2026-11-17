"""Native resource/settings contracts, distinct from actual SDK render tests."""
import errno,gzip,hashlib,io,json,os,shutil,tarfile,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET
from tools.build_native_localization import generate,ROOT,resource_code
from tools.localization import load_locales,validate_locales
from tools.native_language_policy import software_locales
class NativeLocalizationResourcesTest(unittest.TestCase):
 def test_all36_and_settings_preserved(self):
  loaded=load_locales(ROOT);rows=loaded['catalog']['locales'];self.assertEqual(len(rows),36)
  settings=ET.parse(ROOT/'watchface/resources/settings/settings.xml')
  language=next(s for s in settings.getroot() if s.attrib['propertyKey']=='@Properties.Language')
  options={int(x.attrib['value']):x.text for x in language.find('settingConfig')};self.assertEqual(options,{0:'@Strings.Locale0',1:'@Strings.Locale1',2:'@Strings.Locale2',3:'@Strings.Locale3',4:'@Strings.Locale4',36:'@Strings.Auto'})
  self.assertEqual(rows[0]['id'],'en');self.assertEqual(rows[1]['id'],'ru')
  for i,r in enumerate(rows):
   native=json.loads((ROOT/f'watchface/resources/json/Locale{i}.json').read_text());self.assertEqual(native['locale'],r['id']);self.assertEqual(native['timeUnknown'],loaded['strings'][r['id']]['timeUnknown'])
   folder=ROOT/'watchface'/('resources' if i==0 else 'resources-'+resource_code(r));self.assertTrue((folder/'strings/strings.xml').is_file())
 def test_current_property_set_and_reminder_default(self):
  props=ET.parse(ROOT/'watchface/resources/settings/properties.xml').getroot()
  self.assertEqual({p.attrib['id'] for p in props}, {'Field1','Field2','Field3','Field4','Language','ClockColor','CountdownColor','Field1Color','Field2Color','Field3Color','Field4Color','FeedBaseUrl','LaunchReminders'})
  self.assertEqual(next(p.text for p in props if p.get('id')=='LaunchReminders'),'0')
 def test_generation_is_complete_and_repeatable(self):
  # Qualification is separately checked on the actual checkout; this test
  # supplies those observed modes to the isolated generator, not a fabricated
  # qualification or a historical source-tree reconstruction.
  catalog=load_locales(ROOT)['catalog'];qualified=software_locales(ROOT,catalog)
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);shutil.copytree(ROOT/'locales',root/'locales');shutil.copytree(ROOT/'watchface',root/'watchface')
   initial={str(p.relative_to(root)):p.read_bytes() for p in (root/'watchface').rglob('*') if p.is_file()}
   with patch('tools.build_native_localization.software_locales',return_value=qualified):
    generate(root)
    before={str(p.relative_to(root)):p.read_bytes() for p in (root/'watchface').rglob('*') if p.is_file()}
    self.assertEqual([name for name in sorted(set(initial)|set(before)) if initial.get(name)!=before.get(name)],[], 'first generation changed current watch inputs')
    generate(root)
   self.assertEqual(before,{str(p.relative_to(root)):p.read_bytes() for p in (root/'watchface').rglob('*') if p.is_file()})
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
