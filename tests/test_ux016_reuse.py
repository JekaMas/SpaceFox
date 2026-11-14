"""Reconcile retained native lifecycle and data receipts against current owners."""
import hashlib,json,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; E=ROOT/'openspec/changes/spacefox-watchface/evidence/ux01-016'
class RetainedNativeProof(unittest.TestCase):
 def test_aod_paint_and_cadence_inputs(self):
  old=json.loads((E/'lifecycle-build.json').read_text());new=json.loads((E/'settings-build.json').read_text())
  for name in ('watchface/source/LocalePresentation.mc','watchface/source/WatchClock.mc','watchface/source/Fitness.mc'):
   self.assertEqual(old['productionSources'][name],new['productionSources'][name],name)
  for name in ('watchface/resources/fonts/Aod40.fnt','watchface/resources/fonts/Aod40.png'):
   self.assertEqual(old['productionResources'][name],new['productionResources'][name],name)
  original=(E/'lifecycle-renderer.mc.txt').read_text();current=(ROOT/'watchface/source/SceneRenderer.mc').read_text()
  self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),old['productionSources']['watchface/source/SceneRenderer.mc'])
  self.assertEqual(original.split('module SceneAod {',1)[1],current.split('module SceneAod {',1)[1])
  self.assert_view_delta('lifecycle-view.mc.txt',old,allow_active_date=True)
 def test_network_restore_owner_delta_only_low_battery(self):
  old=json.loads((E/'network-final-build.json').read_text());self.assert_view_delta('network-view.mc.txt',old)
 def assert_view_delta(self,name,build,allow_active_date=False):
  original=(E/name).read_text();self.assertEqual(hashlib.sha256(original.encode()).hexdigest(),build['productionSources']['watchface/source/SpaceFoxView.mc'])
  current=(ROOT/'watchface/source/SpaceFoxView.mc').read_text()
  current=current.replace('        // One inexpensive system battery read per permitted LOW snapshot.\n        // Do not start the active health sampler or any timer in LOW.\n        if(!_active){try{values["battery"]=fitness.number(System.getSystemStats().battery,100);}catch(e){values["battery"]=null;}}\n','')
  current=current.replace('// No network, storage, health sampling, parser or resource construction here.','// No network, storage, sensor call, parser or resource construction here.')
  if allow_active_date:
   current=current.replace('        if(snapshot.localCalendar!=null){dc.setColor(0xD4DFEB,Graphics.COLOR_TRANSPARENT);dc.drawText(195,95,presentation.calendarFont as Graphics.FontType,presentation.calendar(snapshot.localCalendar as Array<Number>),Graphics.TEXT_JUSTIFY_CENTER);}\n        dc.setColor(settings.clockColor,Graphics.COLOR_TRANSPARENT);dc.drawText(195,109,','        dc.drawText(195,109,')
  self.assertEqual(original,current)
if __name__=='__main__':unittest.main()
