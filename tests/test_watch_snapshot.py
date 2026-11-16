import json
import unittest
from pathlib import Path
from tools.spacefox.watch_snapshot import FIELDS,encode_snapshot,snapshot
ROOT=Path(__file__).resolve().parents[1]
def row(value):return dict(zip(FIELDS,value))
class CapturedSnapshot(unittest.TestCase):
 def test_coarse_real_capture(self):
  p=ROOT/'tests/fixtures/fr165-runtime-20261116/feed.txt';feed=json.loads(p.read_text());catalog=json.loads((p.parent/'objects'/feed['catalogPath']).read_text());out=snapshot(feed,catalog);selected=row(out[3])
  self.assertEqual(selected['id'],'ll2:launch:e0a11eb1-0bda-4872-b36b-140247fd5c60');self.assertEqual(selected['point'],['111.589567','38.863128']);self.assertEqual(selected['site'],'CN · Taiyuan Satellite Launch Center');self.assertEqual(selected['precision'],'window');self.assertIsNone(selected['target']);self.assertEqual(selected['displayTarget'],1795042200);self.assertFalse(selected['reminderEligible']);self.assertEqual(len(out[4]),2);self.assertEqual(out[6]['transfer'],feed['nativeTransfer']);self.assertEqual(out[6]['selection'],feed['visualSelection']);self.assertEqual(json.loads(encode_snapshot(feed,catalog))['data'],out)
 def test_exact_real_capture(self):
  p=ROOT/'tests/fixtures/trusted-json';feed=json.loads((p/'exact-feed.json').read_text());catalog=json.loads((p/'exact-catalog.json').read_text());s=row(snapshot(feed,catalog)[3]);self.assertEqual(s['target'],1794677550);self.assertEqual(s['precision'],'exact');self.assertEqual(s['retentionDeadline'],1794678450);self.assertTrue(s['reminderEligible']);self.assertIsNone(s['displayTarget'])
