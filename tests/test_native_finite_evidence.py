"""Actual finite receipt admission and rehashed causal corruption refusals."""
import copy,hashlib,json,shutil,tempfile,unittest
from pathlib import Path
from tools.native_language_policy import input_paths,software_locales
from tools.language_support import language_qualification_status
ROOT=Path(__file__).resolve().parents[1]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
class NativeFiniteEvidenceTest(unittest.TestCase):
 def test_actual_finite_primary_software_receipt_admits_without_human_flags(self):
  catalog=json.loads((ROOT/'locales/catalog.json').read_text());self.assertEqual(software_locales(ROOT),catalog['supportPolicy']['primaryLocales']);status=language_qualification_status();self.assertTrue(status['languageQualityReady']);self.assertEqual({},status['missingPrimaryQualification']);self.assertTrue(all(row['nativeQualified'] is False for row in catalog['locales']));self.assertEqual(status['externalReviewStatus'],{'nativeSpeakerReview':'unobserved','physicalDeviceReview':'unobserved'})
 def test_rehashed_native_log_probe_sdk_and_corpus_corruptions_refuse(self):
  with tempfile.TemporaryDirectory(prefix='spacefox-finite-negative-') as temp:
   root=Path(temp);catalog=json.loads((ROOT/'locales/catalog.json').read_text());proof=catalog['supportPolicy']['softwareQualificationProof'];receipt_path=Path(proof['receiptPath']);base=receipt_path.parent
   shutil.copytree(ROOT/'watchface',root/'watchface');shutil.copytree(ROOT/'locales',root/'locales');shutil.copytree((ROOT/proof['corpusPath']).parent,(root/proof['corpusPath']).parent);shutil.copytree(ROOT/base,root/base)
   for name in input_paths(catalog):
    target=root/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,target)
   self.assertEqual(software_locales(root),catalog['supportPolicy']['primaryLocales'])
   original_receipt=(root/receipt_path).read_bytes();original_catalog=(root/'locales/catalog.json').read_bytes()
   cases=[
    ('ui rows',base/'ui/ui.log',lambda raw:raw.replace(b'FINITE_UI READY locale=ru ',b'FINITE_UI REMOVED locale=ru ',1)),
    ('common completion',base/'common/corpus.log',lambda raw:raw.replace(b'FINITE_CORPUS COMPLETE ',b'FINITE_CORPUS REMOVED ',1)),
    ('probe assertion',base/'ui/Probe.mc.txt',lambda raw:raw+b'\n// rehashed incompatible assertion program\n'),
    ('SDK target',base/'common/build.json',lambda raw:raw.replace(b'"fr165"',b'"fr265"',1)),
    ('font failure',base/'fonts.json',lambda raw:raw.replace(b'"status": "passed"',b'"status": "failed"',1)),
    ('overflow probe',base/'ui/Probe.mc.txt',lambda raw:raw.replace(b'fit(dc,raw,font,275)',b'fit(dc,raw,font,1)',1)),
   ]
   for label,relative,mutate in cases:
    path=root/relative;raw=path.read_bytes();changed=mutate(raw);self.assertNotEqual(raw,changed,label);path.write_bytes(changed);record=json.loads(original_receipt);record['observations'][str(relative)]=sha(path)
    build_backup=None
    if label in ('probe assertion','overflow probe'):
     build_path=root/base/'ui/build.json';build_backup=build_path.read_bytes();build=json.loads(build_backup);build['probeSha256']=sha(path);build_path.write_text(json.dumps(build));record['observations'][str(base/'ui/build.json')]=sha(build_path)
    (root/receipt_path).write_text(json.dumps(record));updated=copy.deepcopy(catalog);updated['supportPolicy']['softwareQualificationProof']['receiptSha256']=sha(root/receipt_path);(root/'locales/catalog.json').write_text(json.dumps(updated))
    with self.subTest(case=label),self.assertRaises(ValueError):software_locales(root)
    path.write_bytes(raw)
    if build_backup is not None:build_path.write_bytes(build_backup)
    (root/receipt_path).write_bytes(original_receipt);(root/'locales/catalog.json').write_bytes(original_catalog)
   path=root/proof['corpusPath'];raw=path.read_bytes();data=json.loads(raw);data['coverage']['terminalNext']='https://ll.thespacedevs.com/incomplete';path.write_text(json.dumps(data));digest=sha(path);record=json.loads(original_receipt);record['corpusSha256']=digest;(root/receipt_path).write_text(json.dumps(record));updated=copy.deepcopy(catalog);updated['supportPolicy']['softwareQualificationProof'].update(corpusSha256=digest,receiptSha256=sha(root/receipt_path));(root/'locales/catalog.json').write_text(json.dumps(updated))
   with self.assertRaises(ValueError):software_locales(root)
if __name__=='__main__':unittest.main()
