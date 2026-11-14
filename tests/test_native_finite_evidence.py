"""Actual finite receipt admission and rehashed causal corruption refusals."""
import copy,hashlib,json,re,shutil,tempfile,unittest
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
   if 'sourceDeltaProof' in proof:
    folder=Path(proof['sourceDeltaProof']['path']).parent
    shutil.copytree(ROOT/folder,root/folder,dirs_exist_ok=True)
   self.assertEqual(software_locales(root),catalog['supportPolicy']['primaryLocales'])
   original_receipt=(root/receipt_path).read_bytes();original_catalog=(root/'locales/catalog.json').read_bytes()
   delta_path=root/proof['sourceDeltaProof']['path'] if 'sourceDeltaProof' in proof else None
   original_delta=delta_path.read_bytes() if delta_path else None
   original_proof_path=root/json.loads(original_delta)['originalProof']['path'] if delta_path else None
   original_proof=original_proof_path.read_bytes() if delta_path else None
   def bind_updated(updated):
    if delta_path:
     historical=json.loads(original_proof); current=updated['supportPolicy']['softwareQualificationProof']
     for key in historical:
      if key!='productionSources':historical[key]=current[key]
     original_proof_path.write_text(json.dumps(historical)); delta_record=json.loads(original_delta)
     delta_record['originalProof']['sha256']=sha(original_proof_path);delta_path.write_text(json.dumps(delta_record))
     current['sourceDeltaProof']['sha256']=sha(delta_path)
    (root/'locales/catalog.json').write_text(json.dumps(updated))
   def restore_bindings():
    if delta_path:original_proof_path.write_bytes(original_proof);delta_path.write_bytes(original_delta)
    (root/'locales/catalog.json').write_bytes(original_catalog)
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
    (root/receipt_path).write_text(json.dumps(record));updated=copy.deepcopy(catalog);updated['supportPolicy']['softwareQualificationProof']['receiptSha256']=sha(root/receipt_path);bind_updated(updated)
    with self.subTest(case=label),self.assertRaises(ValueError):software_locales(root)
    path.write_bytes(raw)
    if build_backup is not None:build_path.write_bytes(build_backup)
    (root/receipt_path).write_bytes(original_receipt);restore_bindings()
   if delta_path:
    delta_record=json.loads(original_delta); evidence=root/delta_record['nativeEvidence']
    log=evidence/'unit/native-tests.log';raw=log.read_bytes();changed=re.sub(rb'(finalTimingPositive\s+)PASS',rb'\g<1>FAIL',raw,count=1);self.assertNotEqual(raw,changed);log.write_bytes(changed)
    native=evidence/'native-result.json';native_raw=native.read_bytes();native_record=json.loads(native_raw);native_record['files']['unit/native-tests.log']=sha(log);native.write_text(json.dumps(native_record))
    delta_record['nativeResultSha256']=sha(native);delta_path.write_text(json.dumps(delta_record));updated=copy.deepcopy(catalog);updated['supportPolicy']['softwareQualificationProof']['sourceDeltaProof']['sha256']=sha(delta_path);(root/'locales/catalog.json').write_text(json.dumps(updated))
    with self.assertRaisesRegex(ValueError,'native unit framework receipt failed'):software_locales(root)
    log.write_bytes(raw);native.write_bytes(native_raw);restore_bindings()
   if delta_path:
    delta_record=json.loads(original_delta); ascent=root/delta_record['ascentProof']['directory']
    log=ascent/'native-tests.log';raw=log.read_bytes();changed=re.sub(rb'(ascentAdmissionPositive\s+)PASS',rb'\g<1>FAIL',raw,count=1);self.assertNotEqual(raw,changed);log.write_bytes(changed)
    delta_record['ascentProof']['files']['native-tests.log']=sha(log);delta_path.write_text(json.dumps(delta_record));updated=copy.deepcopy(catalog);updated['supportPolicy']['softwareQualificationProof']['sourceDeltaProof']['sha256']=sha(delta_path);(root/'locales/catalog.json').write_text(json.dumps(updated))
    with self.assertRaisesRegex(ValueError,'current ascent native framework receipt failed'):software_locales(root)
    log.write_bytes(raw);restore_bindings()
   path=root/proof['corpusPath'];raw=path.read_bytes();data=json.loads(raw);data['coverage']['terminalNext']='https://ll.thespacedevs.com/incomplete';path.write_text(json.dumps(data));digest=sha(path);record=json.loads(original_receipt);record['corpusSha256']=digest;(root/receipt_path).write_text(json.dumps(record));updated=copy.deepcopy(catalog);updated['supportPolicy']['softwareQualificationProof'].update(corpusSha256=digest,receiptSha256=sha(root/receipt_path));bind_updated(updated)
   with self.assertRaises(ValueError):software_locales(root)
if __name__=='__main__':unittest.main()
