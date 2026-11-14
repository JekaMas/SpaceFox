"""Check real SDK staged rejection and same accepted visual reconstruction."""
import re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class RejectedStagedFeed(unittest.TestCase):
 def test_accepted_scene_survives_rejected_candidate(self):
  text=(ROOT/'openspec/changes/spacefox-watchface/evidence/ux01-016/rejection-final.log').read_text()
  staged=re.search(r'UX_REJECT_STAGED retainedId=(\S+) target=(\d+) compactContext=true bitmapReleased=true',text)
  restored=re.search(r'UX_REJECT_RECOVERED id=(\S+) target=(\d+) selection=([0-9a-f]{64}) bitmap=true',text)
  self.assertIsNotNone(staged);self.assertIsNotNone(restored);self.assertEqual(staged.groups(),restored.groups()[:2]);self.assertNotIn('Encountered an app crash',text)
if __name__=='__main__':unittest.main()
