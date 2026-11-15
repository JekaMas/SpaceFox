"""Current public producer controls joined with source-bound SDK observations.

The SDK receipts are retained observations, not re-executed by this host test.
The exact probe sources/build inputs are separately checked by verify_binding.
Original SDK executions retain their recorded source/toolchain boundaries.
Public host replay never requires an installed SDK or private Git ancestry.
"""
import copy
import json
from pathlib import Path
import subprocess
import sys
from tests.public_proof_inputs import recorded_input
from tests.public_proof_inputs import verify_current_closure as verify_current
import unittest

PUBLIC=Path(__file__).resolve().parents[1]
EVIDENCE=PUBLIC/'openspec/changes/spacefox-watchface/evidence/current-native-scene-whole'
from tools.spacefox.catalog import canonical_bytes
from tools.spacefox.native_motion import validate_artifact

def files(label):
 root=EVIDENCE/('profile-'+label)
 return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}

def call(tool,*args):
 subprocess.run([sys.executable,'-B',str(EVIDENCE/tool),*map(str,args)],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)

def require(path,*markers):
 text=(EVIDENCE/path).read_text()
 for marker in markers:
  if marker not in text:raise AssertionError(f'{path}: missing {marker}')
 return text

def rejected(candidate,expected):
 try:validate_artifact(candidate)
 except ValueError as error:return expected in str(error)
 return False

class CurrentNativeSceneWhole(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  verify_current()
  # Check original probe/source/resource bytes, not today's installed toolchain.
  # Current applicability uses separately accepted parser/cache/UI seams.
  from tests.test_current_data_convergence import CurrentDataConvergenceTest
  CurrentDataConvergenceTest.setUpClass()
  for name in ('batch-source-age','real-view','current-map','fallback-draw','life-seed','life-observe'):
   folder=EVIDENCE/'current-main-508'/name
   build=json.loads((folder/'build.json').read_text())
   if build['exitCode']!=0:raise AssertionError('retained compile failed: '+name)
   import hashlib
   sha=lambda data:hashlib.sha256(data).hexdigest()
   for field in ('productionSources','productionResources'):
    for path,digest in build[field].items():
     if sha(recorded_input(path,digest))!=digest:raise AssertionError('retained source changed: '+path)
   if sha((folder/'Probe.mc').read_bytes())!=build['probeSha256']:raise AssertionError('retained probe changed: '+name)
   for path,digest in build['probeResources'].items():
    if sha((folder/'probe-resources'/path).read_bytes())!=digest:raise AssertionError('retained resource changed: '+path)
  cls.a=files('a');cls.b=files('b')
  cls.feed_a=validate_artifact(cls.a);cls.feed_b=validate_artifact(cls.b)

 def test_p1_selected_scene_positive(self):
  self.assertEqual(self.feed_a['launch']['launch_id'],'ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b')
  self.assertEqual((self.feed_a['publisher']['generation'],self.feed_b['publisher']['generation']),(1,2))
  subprocess.run([sys.executable,'-B',str(PUBLIC/'tests/native_scene_diagnostics/current-508/verify_current_scene.py'),'--public-root',str(PUBLIC),'--ppm',str(EVIDENCE/'current-main-508/current-map/screen.ppm.gz')],check=True,capture_output=True)
  require('current-main-508/current-map/run.log','CURRENT_SELECTED_DRAW complete=true','point=true')
  require('current-main-508/batch-source-age/run-retry.log','BATCH_COMPLETE fetched=18','exactSelectedOnly=true')

 def test_p1_corrupt_scene_negative(self):
  scene=json.loads(self.a[self.feed_a['visualSelection']['path']]);desc=json.loads(self.a[scene['roles']['rocket']['descriptor']['path']]);path=desc['shards'][0]['path'];bad=self.a.copy();bad[path]=bad[path]+b'!';bad[path+'.txt']=bad[path]
  self.assertTrue(rejected(bad,'raster shard bytes'),'actual current producer must reject corrupted selected object')
  require('grammar/run.log','currentSceneGrammar                 PASS','currentMotionGrammar                PASS','failed=0, errors=0')

 def test_p2_source_update_positive(self):
  candidate=self.a.copy();feed=copy.deepcopy(self.feed_a);feed['publisher']['generation']+=1;candidate['feed.json']=canonical_bytes(feed);candidate['feed.json.txt']=candidate['feed.json']
  actual=validate_artifact(candidate);self.assertEqual(actual['launch']['source_validated_utc'],self.feed_a['launch']['source_validated_utc'])
  self.assertEqual(actual['visualSelection'],self.feed_a['visualSelection'])
  require('current-main-508/batch-source-age/run-retry.log','SOURCE_ONLY_CALLBACK generation=2 optionalGets=0','SOURCE_AGE_COMPLETE generation=2 sourceValidation=1794551192 unchanged=true')
  require('feed-controls/run.log','CURRENT_WIDE exact8192=true coldWarmReopen=true sourceOnlyRawReuse=true','currentWideRecovery                 PASS','currentSourceAge                    PASS','failed=0, errors=0')
  require('current-main-508/current-redraw/native.log','displayDrawDefersResume             PASS','DRAW_RESUME deferred=true rendererLoadsStable=true callbackResumesOnce=true','failed=0, errors=0')

 def test_p2_lifecycle_negative(self):
  candidate=self.a.copy();feed=copy.deepcopy(self.feed_a);feed['publisher']['selectionValidatedUtc']=feed['launch']['source_validated_utc']-1;candidate['feed.json']=canonical_bytes(feed);candidate['feed.json.txt']=candidate['feed.json']
  self.assertTrue(rejected(candidate,'selection validation precedes selected source'),'publisher epoch cannot predate the selected source')
  text=require('current-main-508/life-observe/inflight.log','event=display mode=1 buildTimer=false build=false requested=false','event=display mode=2 buildTimer=false build=false requested=false','bitmap=true')
  self.assertIn('buildTimer=true build=true requested=true',text)
  require('current-main-508/life-observe/inflight.log','HIDE_BEFORE timer=true build=true pending=true','HIDE_AFTER timer=false build=false pending=false animation=false fitness=false','bitmap=true')

 def test_p3_recovery_positive(self):
  self.assertNotEqual(self.feed_a['visualSelection']['sha256'],self.feed_b['visualSelection']['sha256'])
  require('current-main-508/real-view/run.log','actualOldBitmapCleared=true','retryB=true recoveryA=true')
  require('current-main-508/fallback-draw/run.log','FALLBACK_DRAW Bcontext=true Bpoint=26.99677 matchingProjection=false marker=false oldRaster=false')
  self.assertTrue((EVIDENCE/'current-main-508/fallback-draw/screen.png').is_file())
  require('full-clean/run.log','CLEAN removed=329 ownFillerOnly=true','COMPLETE cleaned=true')
  require('full-positive/run.log','FULL_POSITIVE_COMPLETE acceptedB=true floor=2')
  require('current-main-508/life-observe/repeat-reopen.log','push=false','bitmap=true','writes=0')
  digest=lambda stage:[line.split()[0] for line in (EVIDENCE/'current-main-508/life-observe'/stage).read_text().splitlines()]
  for stage in ('repeat-after-stop.sha256','repeat-after-reopen.sha256'):
   self.assertEqual(digest(stage),digest('repeat-before.sha256'))

 def test_p3_refusal_negative(self):
  candidate=self.a.copy();feed=copy.deepcopy(self.feed_a);feed['visualSelection']['path']='https://invalid.example/not-immutable';candidate['feed.json']=canonical_bytes(feed);candidate['feed.json.txt']=candidate['feed.json']
  self.assertTrue(rejected(candidate,'immutable path/digest mismatch'),'untrusted selected endpoint must be refused')
  require('callback-skew/run.log','NEG_COMPLETE corruptRejected=true missingRefused=true priorPointerPreserved=true','http200CallbackRefused=true')
  require('feed-controls/run.log','CURRENT_ATOMIC writeInterruptions=10 lastGoodRecoverable=true','currentAtomicRecovery               PASS')
  require('late-current/run.log','currentLateProvenanceAndEndpoints   PASS','failed=0, errors=0')
  require('race-current/run.log','ROOT_RACE_COMPLETE mutationReached=true incomingRefused=true oldSealAndFloor=true durableReopen=true')
  require('raster-fault/run.log','RASTER_FAULT_COMPLETE recoveryWriteAndActiveWriteInjected=true oldPointerPreserved=true retryB=true recoveryA=true')
  require('full-fill/run.log','QUOTA exception=Lang.StorageFullException tier=1','COMPLETE full=true')
  require('full-reject/run.log','FULL_REJECTION_COMPLETE oldSealFloorAge=true acceptedB=false')
  require('full-reject/Probe.mc','cache.failureReason.equals("persist")')
  require('unresolved/run.log','refreshUnresolvedScene              PASS','moreGenericRenderer                 PASS')

if __name__=='__main__':unittest.main()
