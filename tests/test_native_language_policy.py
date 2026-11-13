"""Admission-mechanism tests; fabricated receipts here confer no SDK qualification."""
import copy,hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from tools.native_language_policy import OWNERS,input_paths,software_locales,_validate_bound_files
ROOT=Path(__file__).resolve().parents[1]
class NativeSoftwareAdmissionTest(unittest.TestCase):
 def setUp(self):self.catalog=json.loads((ROOT/'locales/catalog.json').read_text())
 def test_self_asserted_receipt_and_incomplete_corpus_cannot_admit(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);c=copy.deepcopy(self.catalog);policy=c['supportPolicy'];policy['softwareQualifiedLocales']=['ru']
   sources={}
   for name in input_paths(c):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());sources[name]=hashlib.sha256(p.read_bytes()).hexdigest()
   (root/'watchface/source/generated/SceneStrings.mc').write_bytes((ROOT/'watchface/source/generated/SceneStrings.mc').read_bytes())
   corpus=root/'corpus.json';corpus.write_text('{"testOnly":true}');corpus_sha=hashlib.sha256(corpus.read_bytes()).hexdigest()
   receipt=root/'receipt.json';receipt.write_text(json.dumps({'status':'passed','qualifiedLocales':['ru'],'corpusSha256':corpus_sha,'productionSources':sources}))
   policy['softwareQualificationProof']={'schemaVersion':1,'corpusPath':'corpus.json','corpusSha256':corpus_sha,'receiptPath':'receipt.json','receiptSha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'productionSources':sources,'scope':'finite-primary-software','physicalDeviceObserved':False,'nativeSpeakerReviewed':False}
   with self.assertRaises(ValueError):software_locales(root,c)
 def test_pending_build_refuses_generated_availability_bypass(self):
  from tools.build_watchface import BuildBlocked,validate_manifest
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);shutil.copytree(ROOT/'watchface',root/'watchface');shutil.copytree(ROOT/'locales',root/'locales')
   from tools.build_native_localization import scene_strings
   import xml.etree.ElementTree as ET
   catalog_path=root/'locales/catalog.json';pending=json.loads(catalog_path.read_text());pending['supportPolicy']['softwareQualifiedLocales']=[];pending['supportPolicy']['softwareQualificationProof']=None;catalog_path.write_text(json.dumps(pending))
   generated=root/'watchface/source/generated/SceneStrings.mc';generated.write_text(scene_strings(pending['locales'],[]))
   manifest=root/'watchface/manifest.xml';tree=ET.parse(manifest);ns={'iq':'http://www.garmin.com/xml/connectiq'};languages=tree.find('.//iq:languages',ns);languages.clear();ET.SubElement(languages,'{'+ns['iq']+'}language').text='eng';tree.write(manifest)
   lock=json.loads((root/'watchface/toolchain-lock.json').read_text());validate_manifest(root,lock)
   p=root/'watchface/source/generated/SceneStrings.mc';original=p.read_text();changed=original.replace('return index==0;','return index==0||index==1;');self.assertNotEqual(original,changed);p.write_text(changed)
   with self.assertRaisesRegex(BuildBlocked,'generated locale'):validate_manifest(root,lock)
 def test_runtime_grapheme_and_locale_resource_binding_drift_refuse(self):
  # These are actual resource dependencies of LocaleGraphemes.load and
  # SceneStrings.resource, independent of the policy helper's inventory.
  bindings=('watchface/resources/json/GraphemeProperties.json',
            'watchface/resources/json/graphemes.xml',
            'watchface/resources/json/locales.xml',
            'watchface/resources/fonts/fonts.xml',
            'watchface/resources/fonts/Aod40.fnt',
            'watchface/resources/fonts/Aod40.png',
            'watchface/resources/fonts/Battery13.fnt',
            'watchface/resources/fonts/Battery13.png',
            'watchface/resources/fonts/Metric32.fnt',
            'watchface/resources/fonts/Metric32.png',
            'watchface/resources/fonts/Time80.fnt',
            'watchface/resources/fonts/Time80.png')
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);c=copy.deepcopy(self.catalog);policy=c['supportPolicy'];policy['softwareQualifiedLocales']=['ru']
   for name in set(input_paths(c))|set(bindings):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes())
   generated=root/'watchface/source/generated/SceneStrings.mc';generated.write_bytes((ROOT/'watchface/source/generated/SceneStrings.mc').read_bytes())
   sources={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in input_paths(c)}
   corpus=root/'corpus.json';corpus.write_text('{"testOnly":true}');corpus_sha=hashlib.sha256(corpus.read_bytes()).hexdigest()
   record={'status':'passed','qualifiedLocales':['ru'],'corpusSha256':corpus_sha,'productionSources':sources}
   receipt=root/'receipt.json';receipt.write_text(json.dumps(record));policy['softwareQualificationProof']={'schemaVersion':1,'corpusPath':'corpus.json','corpusSha256':corpus_sha,'receiptPath':'receipt.json','receiptSha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'productionSources':sources,'scope':'finite-primary-software','physicalDeviceObserved':False,'nativeSpeakerReviewed':False}
   self.assertEqual(_validate_bound_files(root,c),['ru'])
   original=generated.read_text();generated.write_text(original.replace('en|ru|','ru|en|'))
   with self.assertRaisesRegex(ValueError,'generated locale'):_validate_bound_files(root,c)
   generated.write_text(original)
   self.assertTrue(set(bindings)<=set(sources))
   for name in bindings:
    p=root/name;raw=p.read_bytes();p.write_bytes(raw+b' ')
    with self.subTest(path=name),self.assertRaises(ValueError):_validate_bound_files(root,c)
    p.write_bytes(raw)
   # A new page path is technical resource metadata; its bytes are the actual
   # existing atlas, not an invented display case. Follow it transitively.
   font=root/'watchface/resources/fonts/Time80.fnt';font.write_text(font.read_text().replace('Time80.png','ProofFontPage.png'))
   page=root/'watchface/resources/fonts/ProofFontPage.png';page.write_bytes((root/'watchface/resources/fonts/Time80.png').read_bytes())
   self.assertIn('watchface/resources/fonts/ProofFontPage.png',input_paths(c,root))
   self.assertNotIn('watchface/resources/fonts/Time80.png',input_paths(c,root))
   proof=policy['softwareQualificationProof']
   def refresh_receipt():
    receipt.write_text(json.dumps(record));proof['receiptSha256']=hashlib.sha256(receipt.read_bytes()).hexdigest()
   sources['watchface/resources/fonts/Time80.fnt']=hashlib.sha256(font.read_bytes()).hexdigest();refresh_receipt()
   # Rehashing the changed binding alone cannot disguise an unlisted page.
   with self.assertRaises(ValueError):_validate_bound_files(root,c)
   sources={name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in input_paths(c,root)}
   proof['productionSources']=sources;record['productionSources']=sources;refresh_receipt()
   self.assertEqual(_validate_bound_files(root,c),['ru'])
   page.write_bytes(page.read_bytes()+b' ')
   with self.assertRaises(ValueError):_validate_bound_files(root,c)
 def test_pending_does_not_enable_primary_membership(self):
  c=copy.deepcopy(self.catalog);c['supportPolicy']['softwareQualifiedLocales']=[];c['supportPolicy']['softwareQualificationProof']=None
  self.assertEqual(software_locales(ROOT,c),[])
  for invalid in [['en','en'],['sk'],['unsupported'],True]:
   c['supportPolicy']['softwareQualifiedLocales']=invalid
   with self.assertRaises(ValueError):software_locales(ROOT,c)
 def test_bound_receipt_and_each_source_drift_refuse(self):
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp);c=copy.deepcopy(self.catalog);policy=c['supportPolicy'];policy['softwareQualifiedLocales']=['en','ru'];sources={}
   for name in input_paths(c):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());sources[name]=hashlib.sha256(p.read_bytes()).hexdigest()
   (root/'watchface/source/generated/SceneStrings.mc').write_bytes((ROOT/'watchface/source/generated/SceneStrings.mc').read_bytes())
   corpus=root/'corpus.json';corpus.write_text('{"testOnly":true}');corpus_sha=hashlib.sha256(corpus.read_bytes()).hexdigest()
   record={'status':'passed','qualifiedLocales':['en','ru'],'corpusSha256':corpus_sha,'productionSources':sources}
   receipt=root/'receipt.json';receipt.write_text(json.dumps(record));proof={'schemaVersion':1,'corpusPath':'corpus.json','corpusSha256':corpus_sha,'receiptPath':'receipt.json','receiptSha256':hashlib.sha256(receipt.read_bytes()).hexdigest(),'productionSources':sources,'scope':'finite-primary-software','physicalDeviceObserved':False,'nativeSpeakerReviewed':False};policy['softwareQualificationProof']=proof
   self.assertEqual(_validate_bound_files(root,c),['en','ru'])
   for name in [*input_paths(c),'corpus.json','receipt.json']:
    p=root/name;raw=p.read_bytes();p.write_bytes(raw+b'changed')
    with self.subTest(path=name),self.assertRaises(ValueError):_validate_bound_files(root,c)
    p.write_bytes(raw)
   for key,value in [('physicalDeviceObserved',True),('nativeSpeakerReviewed',True),('schemaVersion',2),('receiptPath','../escape')]:
    original=proof[key];proof[key]=value
    with self.subTest(field=key),self.assertRaises(ValueError):_validate_bound_files(root,c)
    proof[key]=original
if __name__=='__main__':unittest.main()
