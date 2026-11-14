"""Narrow source boundaries for retaining UX01 native rejection/cadence receipts."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'openspec/changes/spacefox-watchface/evidence/ux01-016'
P=ROOT/'openspec/changes/spacefox-watchface/evidence/ux02/prior'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
class RetainedRecovery(unittest.TestCase):
 def test_callback_admission_and_resume_owners_retained(self):
  build=json.loads((E/'identity-build.json').read_text())
  for name in ('NativeIncoming','NativeForegroundApp','NativeForegroundCache','NativeCache','NativeImmutable','NativeFeed','FeedService','NativeSfr'):
   path=f'watchface/source/{name}.mc'; checked = ROOT/path if name != 'NativeImmutable' else ROOT/'openspec/changes/spacefox-watchface/evidence/release-cache-port/prior/NativeImmutable.mc'; self.assertEqual(sha(checked),build['productionSources'][path],path)
  cache=json.loads((ROOT/'openspec/changes/spacefox-watchface/evidence/release-cache-port/cache-port-proof.json').read_text()); self.assertEqual(sha(ROOT/'watchface/source/NativeImmutable.mc'),cache['sources']['watchface/source/NativeImmutable.mc']['sha256'])
  old=P/'watchface__source__SpaceFoxView.mc';self.assertEqual(sha(old),build['productionSources']['watchface/source/SpaceFoxView.mc'])
  original=old.read_text();current=(ROOT/'watchface/source/SpaceFoxView.mc').read_text()
  # All rejection, reset, timer, visibility and wake owner bodies outside the
  # explicitly changed layout/paint interval are byte-for-byte unchanged.
  self.assertEqual(original.split('    function onLayout(',1)[0].split('    function syncDisplayMode(',1)[1],current.split('    function onLayout(',1)[0].split('    function syncDisplayMode(',1)[1])
  self.assertEqual(original.split('    function stopAnimation(',1)[1],current.split('    function stopAnimation(',1)[1])
  # The moved drawScene body differs only in passing settings to LOW painting.
  oldbody=original.split('    function onUpdate(dc as Graphics.Dc) as Void {',1)[1].split('    // Resident built-in fonts',1)[0]
  newbody=current.split('    function drawScene(dc as Graphics.Dc) as Void {',1)[1].split('    // Resident built-in fonts',1)[0].replace('drawing.aod(dc,current,minute,settings)','drawing.aod(dc,current,minute)')
  self.assertEqual(oldbody,newbody)
  transfer=P/'watchface__source__NativeTransfer.mc';self.assertEqual(sha(transfer),build['productionSources']['watchface/source/NativeTransfer.mc'])
  old=transfer.read_text();new=(ROOT/'watchface/source/NativeTransfer.mc').read_text()
  new=new.replace('&&attempt["build"] instanceof String&&attempt["build"].equals(NativeVersion.BUILD)','').replace(',"build"=>NativeVersion.BUILD','')
  self.assertEqual(old,new)
if __name__=='__main__':unittest.main()
