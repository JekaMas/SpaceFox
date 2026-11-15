"""Reconcile an ordinary SDK AppBase across an owned simulator restart.

The test reads retained actual runtime output and independently reconstructs
literal producer-derived packets. It does not launch a simulator or assert
paired-phone, physical watch, natural OS scheduling or clean power-loss behavior.
"""
import hashlib
import json
import re
import unittest
from tests.public_proof_inputs import recorded_input
from tests.public_proof_inputs import verify_current_closure as verify_current
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'openspec/changes/spacefox-watchface/evidence/watch-refresh-cache-whole/independent-minute-r1/cross-vm'
F=ROOT/'tests/fixtures/watch_refresh_cache'
sha=lambda raw:hashlib.sha256(raw).hexdigest()

class CrossVmPersistenceTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.build=json.loads((E/'build.json').read_text());cls.probe=(E/'Probe.mc').read_text();cls.expected=cls.build['expected']
 def test_source_bound_same_package_and_storage_restart(self):
  verify_current()
  b=self.build;self.assertEqual(b['exitCode'],0);self.assertEqual(b['packageName'],'C7.prg');self.assertTrue(b['sourceDirty'])
  self.assertEqual(b['admissionValidation'],'bypassed-diagnostic-only')
  for path,digest in {**b['productionSources'],**b['productionResources'],**b['inputSha256']}.items():self.assertEqual(sha(recorded_input(path,digest)),digest,path)
  nonce=b['nonce'];self.assertRegex(nonce,r'^[0-9a-f]{32}$');self.assertRegex(b['applicationUuid'],r'^[0-9a-f]{32}$')
  original=(F/'CrossVmApp.mc').read_text().replace('@@NONCE@@',nonce).replace('@@HASH_B@@',self.expected['Bwire']).replace('@@BOUNDARY@@',str(b['phaseBoundaryEpoch'])).replace('@@BOUNDARY2@@',str(b['mutationBoundaryEpoch']))
  original=original.replace('AppBase.initialize();','AppBase.initialize();NativeMetrics.ownerTag='+json.dumps(b['ownerTag'])+';System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);',1)
  self.assertEqual(self.probe,original);self.assertEqual(sha(self.probe.encode()),b['probeSha256'])
  captured=json.loads((F/'packets.json').read_bytes());packets={}
  for label,name,epoch in (('A','initial',1794603899),('B','moved',1794603900),('Newer','refresh',1794612901),('BadInstance','refresh',1794612901)):
   doc=json.loads(captured['packets'][name]);doc['launch']['source_validated_utc']=epoch;doc['publisher']['selectionValidatedUtc']=epoch
   if label=='BadInstance':doc['publisher']['instance']='b'*64
   raw=json.dumps(doc,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode();packets[label]=raw
   self.assertEqual(sha(raw),b['packetSha256'][label]);resource=json.dumps({'raw':raw.decode()},ensure_ascii=False,separators=(',',':')).encode()
   self.assertEqual(sha(resource),b['probeResources']['Cross'+label+'.json'])
   self.assertEqual((E/'probe-resources'/('Cross'+label+'.json')).read_bytes(),resource)
   self.assertEqual(doc['launch']['timing']['source_precision_id'],1);self.assertIsNone(doc['launch']['timing']['exact_utc'])
  self.assertEqual(sha(packets['B']),'c686f5e57622097a9184be9d0e8b3008a61bb421cbc273b194dbbc05d1964a14')
  self.assertEqual(self.expected,{'launchId':'ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b','Avalidation':1794603899,'Bvalidation':1794603900,'Btarget':1794611100,'wake':1794612901,'newValidation':1794612901,'Bwire':sha(packets['B'])})
  cat=captured['catalogs']['initial'];self.assertEqual(cat,captured['catalogs']['moved']);self.assertEqual(cat,captured['catalogs']['refresh'])
  catbytes=json.dumps({'digest':cat['catalogDigest'],'raw':cat['catalog']},ensure_ascii=False,separators=(',',':')).encode()
  self.assertEqual(sha(catbytes),b['probeResources']['CrossCatalog.json']);self.assertEqual((E/'probe-resources/CrossCatalog.json').read_bytes(),catbytes)
  self.assertEqual(sha(cat['catalog'].encode()),cat['catalogDigest'])
  def hashes(name):return {Path(line.split(None,1)[1]).name:line.split(None,1)[0] for line in (E/name).read_text().splitlines()}
  before=hashes('storage-C7-before-close.sha256');self.assertEqual(set(before),{'C7.DAT','C7.IDX','C7.PRG'})
  for name in ('storage-C7-after-close.sha256','storage-C7-after-stop.sha256','storage-C7-before-read.sha256','storage-C7-after-read.sha256'):
   self.assertEqual(before,hashes(name))
  for name in ('package-C7-phase1.sha256','package-C7-after-stop.sha256','package-C7-before-read.sha256','package-C7-after-read.sha256'):
   self.assertEqual(hashes(name),{'C7.prg':b['packageSha256']})
  def simulator_pid(name):
   lines=(E/name).read_text().splitlines();found=[line for line in lines if '/bin/simulator /task/' in line and 'sh -c' not in line]
   self.assertEqual(len(found),1,(name,lines));return int(found[0].split()[1])
  self.assertNotEqual(simulator_pid('process-C7-phase1.txt'),simulator_pid('process-C7-phase2.txt'))
  self.assertEqual((E/'process-C7-old-after-stop.txt').read_text().strip(),'')
  self.assertEqual((E/'simulator-C7-stop-code.txt').read_text().strip(),'143')
  env=json.loads((E/'environment.json').read_text());self.assertEqual(env['networkMode'],'none');self.assertFalse(env['portBindings']);self.assertEqual((E/'runtime-mount-C7.txt').read_text().strip(),'/task/simulator-data-C7')
  self.assertEqual(env['compilerSha256'],'082b2fd3f50578204e01d44313f43f2ce52a60dbfd6221f6b259b2687239de3f');self.assertEqual(env['builderSha256'],sha((E/'build_probe.py').read_bytes()))
  self.assertEqual((E/'phase1-C7.exit').read_text().strip(),'124')
  for n in ('phase2','phase3'):
   self.assertEqual((E/(n+'-C7.exit')).read_text().strip(),'0');self.assertFalse((E/(n+'-C7.stderr')).read_text())
  first=(E/'phase1-C7.stdout').read_text();second=(E/'phase2-C7.stdout').read_text();third=(E/'phase3-C7.stdout').read_text()
  self.assertEqual(first.count('CROSSVM_PHASE1 '),1)
  for out in (second,third):
   self.assertNotIn('CROSSVM_PHASE1 ',out);self.assertIn('OPEN_INSTALLED uuid=f80b3121-b554-46c9-9883-96a8690d6100 push=false',out)
  for out in (first,second,third):self.assertIn('SFR_PROBE owner='+b['ownerTag'],out);self.assertNotIn('CROSSVM_FAIL',out);self.assertNotIn('Error:',out)
  times=[]
  for out,stage,marker in ((first,0,'null'),(second,10,nonce),(third,20,nonce)):
   match=re.search(r'CROSSVM_OPEN nonce=(\S+) stage=(\d+) epoch=(\d+) uptime=(\d+)',out);self.assertIsNotNone(match);self.assertEqual(match.group(1),marker);self.assertEqual(int(match.group(2)),stage);times.append(int(match.group(3)))
  self.assertLess(times[0],b['phaseBoundaryEpoch']);self.assertLessEqual(b['phaseBoundaryEpoch'],times[1]);self.assertLess(times[1],b['mutationBoundaryEpoch']);self.assertLessEqual(b['mutationBoundaryEpoch'],times[2])
  self.assertIn('nonce='+nonce+' id='+self.expected['launchId']+' target=1794611100 validation=1794603900 rescheduled=true stale=false generation=2 origin=1794603900 wire='+self.expected['Bwire']+' seed=true',first)
  self.assertIn('nonce='+nonce+' id='+self.expected['launchId']+' target=1794611100 validation=1794603900 stale=true rescheduled=true generation=2 origin=1794603900 wire='+self.expected['Bwire']+' noReseed=true noWrites=true',second)
  self.assertIn('replayNoWrite=true oldRejected=true changedInstanceRejected=true newValidation=1794612901 newStale=false rescheduled=true newGeneration=3 origin=1794612901 noReseed=true',third)
  launcher=(E/'RunInstalled.java').read_text();self.assertIn('device.openApp(uuid,false)',launcher);self.assertNotIn('.pushPrg(',launcher)
 def test_negative_replay_floor_and_owned_cleanup(self):
  self.test_source_bound_same_package_and_storage_restart()
  missing=(E/'phase4-missing-C7.stdout').read_text();self.assertIn('CROSSVM_READER_REFUSED missingOrWrongNonce=true noWrites=true',missing);self.assertNotIn('CROSSVM_PHASE1 ',missing)
  self.assertIn('No such file or directory',(E/'storage-C7-before-missing.txt').read_text());self.assertIn('No such file or directory',(E/'storage-C7-after-missing.txt').read_text())
