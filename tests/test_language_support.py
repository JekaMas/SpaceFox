"""One software admission state for status, runtime and generated manifest."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from tools.language_support import ROOT,language_qualification_status
from tools.native_language_policy import OWNERS,input_paths,software_locales
PRIMARY=set('en ru de fr es'.split())
BEST_EFFORT=set('it pt nl pl uk cs sk hu ro bg hr sl el tr da sv nb fi et lv lt zh-Hans zh-Hant ja ko ar he th id ms vi'.split())
class LanguageSupportTest(unittest.TestCase):
 def test_primary_scope_and_retained_inventory(self):
  result=language_qualification_status();self.assertEqual(PRIMARY,set(result['primaryLocales']));self.assertEqual(BEST_EFFORT,set(result['bestEffortLocales']))
  qualified=set(software_locales(ROOT));self.assertEqual(qualified,set(result['qualifiedSoftwareLocales']));self.assertEqual(PRIMARY-qualified,set(result['missingPrimaryQualification']));self.assertEqual(qualified==PRIMARY,result['languageQualityReady'])
  for locale in PRIMARY|BEST_EFFORT:self.assertTrue((ROOT/'locales'/(locale+'.json')).is_file())
  catalog=json.loads((ROOT/'locales/catalog.json').read_text());self.assertEqual(36,len(catalog['locales']));self.assertTrue(all(row['reviewStatus']=='draft' and row['nativeQualified'] is False for row in catalog['locales']))
  self.assertEqual({'nativeSpeakerReview':'unobserved','physicalDeviceReview':'unobserved'},result['externalReviewStatus'])
  with self.assertRaises(TypeError):language_qualification_status(observations={locale:{'fr165GlyphLayoutReview':True} for locale in PRIMARY})
 def test_bound_software_state_cannot_disagree_with_status(self):
  # Controlled receipt below tests policy wiring only; it is never an SDK receipt.
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);catalog=json.loads((ROOT/'locales/catalog.json').read_text());policy=catalog['supportPolicy'];qualified=policy['primaryLocales'];policy['softwareQualifiedLocales']=qualified;sources={}
   for name in input_paths(catalog):
    p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((ROOT/name).read_bytes());sources[name]=hashlib.sha256(p.read_bytes()).hexdigest()
   (root/'watchface/source/generated/SceneStrings.mc').write_bytes((ROOT/'watchface/source/generated/SceneStrings.mc').read_bytes())
   p=root/'corpus.json';p.write_text('{"policyTestOnly":true}');corpus=hashlib.sha256(p.read_bytes()).hexdigest()
   receipt={'status':'passed','qualifiedLocales':qualified,'corpusSha256':corpus,'productionSources':sources};p=root/'receipt.json';p.write_text(json.dumps(receipt));receipt_sha=hashlib.sha256(p.read_bytes()).hexdigest()
   policy['softwareQualificationProof']={'schemaVersion':1,'corpusPath':'corpus.json','corpusSha256':corpus,'receiptPath':'receipt.json','receiptSha256':receipt_sha,'productionSources':sources,'scope':'finite-primary-software','physicalDeviceObserved':False,'nativeSpeakerReviewed':False}
   (root/'locales').mkdir(exist_ok=True);path=root/'locales/catalog.json';path.write_text(json.dumps(catalog))
   with self.assertRaises(ValueError):language_qualification_status(root)
   (root/'corpus.json').write_text('changed')
   with self.assertRaises(ValueError):language_qualification_status(root)
 def test_corrupt_partition_refuses(self):
  original=json.loads((ROOT/'locales/catalog.json').read_text())
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'locales').mkdir(exist_ok=True);path=root/'locales/catalog.json'
   for primary in [original['supportPolicy']['primaryLocales']+['hi'],original['supportPolicy']['primaryLocales']+['en'],[v for v in original['supportPolicy']['primaryLocales'] if v!='en']]:
    catalog=copy.deepcopy(original);catalog['supportPolicy']['primaryLocales']=primary;path.write_text(json.dumps(catalog))
    with self.assertRaises(ValueError):language_qualification_status(root)
 def test_finite_corpus_policy_cannot_expand_or_mix_external_gate(self):
  original=json.loads((ROOT/'locales/catalog.json').read_text())
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);(root/'locales').mkdir();path=root/'locales/catalog.json'
   mutations=[('displayCorpus',dict(original['supportPolicy']['displayCorpus'],inventedDisplayText=True)),
              ('qualificationCriteria',['nativeSpeakerReview']),('separateEvidenceCriteria',[])]
   for key,value in mutations:
    catalog=copy.deepcopy(original);catalog['supportPolicy'][key]=value;path.write_text(json.dumps(catalog))
    with self.subTest(field=key),self.assertRaises(ValueError):language_qualification_status(root)
if __name__=='__main__':unittest.main()
