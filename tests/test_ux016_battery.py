"""Assert actual SDK LOW draws tracked real battery without a fitness timer."""
import os,re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LOG=Path(os.environ.get('SPACEFOX_UX_BATTERY_LOG',ROOT/'openspec/changes/spacefox-watchface/evidence/ux01-016/battery-final.log'))
def observations():
 text=LOG.read_text()
 if 'UX_LOW_COLD_FRESH mode=1' not in text: raise AssertionError('fresh view was not created in real LOW mode')
 rows=[]
 for line in text.splitlines():
  m=re.search(r'UX_LOW_BATTERY mode=1 now=(\d+) before=(\w+) after=(\d+) system=([\d.]+) displayed=(\S+) timer=(\w+)',line)
  if m and (not rows or int(m[3])!=rows[-1][0]): rows.append((int(m[3]),int(float(m[4])),m[5],m[6]))
 return rows
class LowPowerBattery(unittest.TestCase):
 def test_initial_low_battery(self):
  rows=observations();self.assertTrue(rows,'no LOW draw observed');self.assertEqual(rows[0][2],str(rows[0][1])+'%');self.assertEqual(rows[0][3],'false')
 def test_next_minute_battery(self):
  rows=observations();self.assertGreaterEqual(len(rows),2,'no next permitted minute observed');self.assertNotEqual(rows[0][1],rows[1][1],'system battery did not change');self.assertEqual(rows[1][2],str(rows[1][1])+'%');self.assertEqual(rows[1][3],'false')
if __name__=='__main__':unittest.main()
