"""Preclip reconciliation of existing native argument/asset receipts.

These conservative square-viewport bounds complement the independently captured
circle/alpha masks. Map and rocket's declared animation clip are intentional.
"""
import hashlib,json,re,unittest
from pathlib import Path
from tests import test_display04_operation_trace as trace
from tools.native_element_isolation import PRIMITIVES,isolate
from tools.run_native_tests import parse_output
ROOT=Path(__file__).resolve().parents[1]

def inside(x0,y0,x1,y1):return 0<=x0<x1<=390 and 0<=y0<y1<=390

class NativePreclipEvidenceTest(unittest.TestCase):
 def test_actual_pending_and_ready_text_and_icon_boxes(self):
  # Native SDK font width/height and actual bitmap dimensions, before the
  # production draw; pad includes outline and one conservative rounding px.
  configs=[('trace-pending-390','tests/fixtures/display04_operation_trace/Trace.mc','D04_TRACE_'),('trace-pending-454','tests/fixtures/display04_operation_trace/Trace.mc','D04_TRACE_'),('ready-asset-trace-390','tests/fixtures/display04_ready_asset_trace/ReadyAssetTrace.mc','D04_READY_TRACE_'),('ready-asset-trace-454','tests/fixtures/display04_ready_asset_trace/ReadyAssetTrace.mc','D04_READY_TRACE_')]
  for folder,source,prefix in configs:
   log=trace.bound(folder,source);texts=icons=0
   for line in log.splitlines():
    if prefix+'TEXT|' in line:
     row=line[line.index(prefix+'TEXT|'):].split('|');x,y,w,h,contour=int(row[2]),int(row[3]),int(row[5]),int(row[6]),int(row[9]);pad=contour+1
     self.assertTrue(inside(x-w/2-pad,y-pad,x+w/2+pad,y+h+pad),(folder,row));texts+=1
    elif prefix+'ICON|' in line:
     row=line[line.index(prefix+'ICON|'):].split('|');x,y,w,h=map(int,row[3:7]);self.assertTrue(inside(x-1,y-1,x+w+1,y+h+1),(folder,row));icons+=1
   self.assertGreaterEqual(texts,24,folder);self.assertEqual(icons,8,folder)
  self.assertTrue(inside(194,0,196,1));self.assertFalse(inside(194,-1,196,1))

 def test_finite_long_site_text_and_circle_bound(self):
  d=trace.E/'preclip-fields/viewport-green';receipt=json.loads((d/'receipt.json').read_text());raw=(d/'native.log').read_text()
  self.assertEqual(hashlib.sha256((d/'Display02Tests.prg').read_bytes()).hexdigest(),receipt['packageSha256'])
  self.assertEqual(parse_output(raw,receipt['rawExit'],tuple(receipt['tests']['expected_tests']))['status'],'passed')
  for name in ('watchface/current-fields-tests/FieldsTests.mc','watchface/source/SceneRenderer.mc','watchface/source/LocalePresentation.mc'):
   self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),receipt['inputHashes'][name])
  for lang in (0,1):
   self.assertIn('FOOTER_CIRCLE language='+str(lang)+' case=0 width=239 height=22',raw)
   self.assertIn('FOOTER_CIRCLE language='+str(lang)+' case=1 width=242 height=22',raw)
  self.assertIn('currentFooterCircleBound',receipt['tests']['observed_tests'])

 def test_direct_bitmap_and_clip_ownership_for_retained_scene(self):
  source=(ROOT/'watchface/source/SceneRenderer.mc').read_text();found={}
  for name in re.findall(r'\bdc\.(clear\w*|draw\w+|fill\w+|setClip)\s*\(',source):found[name]=found.get(name,0)+1
  self.assertEqual(found,PRIMITIVES) # unknown primitives fail closed
  isolate(source) # verify each production call and its exact isolation route
  native=(ROOT/'watchface/source/NativeVisualRenderer.mc').read_text()
  self.assertIn('if(!frameIntersects(ascent)){return;}',native)
  self.assertIn('dc.setClip(22,118-ascent,54,124);dc.drawBitmap2(frameX,frameY,bitmap,drawOptions);dc.clearClip();',native)
  self.assertNotIn('setClip(',source);self.assertNotIn('clearClip(',source)
  for size in (390,454):
   pending=trace.bound('bitmap-trace-'+str(size),'tests/fixtures/display04_bitmap_trace/TraceBitmap.mc')
   self.assertIn('map=ResourceId,195x195|art=ResourceId,54x124|marker=ResourceId,28x28|pin=335,165',pending)
   selected=trace.bound('ready-asset-trace-'+str(size),'tests/fixtures/display04_ready_asset_trace/ReadyAssetTrace.mc')
   self.assertIn('map=390x390|rocket=54x124|flag=20x12|phase=0|position=true',selected)
   self.assertIn('|208|319|nameSmall|206|22|',selected)
   # Pin, flag, and unanimated art: source literals + actual SDK dimensions.
   self.assertTrue(inside(321,151,349,179))
   self.assertTrue(inside(22,118,76,242))
   self.assertTrue(inside(79,325,99,337)) # READY footer x=208, width=206, gap=26
  self.assertFalse(inside(-1,0,20,12))

 def test_low_direct_primitive_bounds_at_retained_actual_fixture(self):
  # Reuse original SDK date-width and actual LOW renderer traces: this does
  # not relabel other dates, battery values, or profiles as observed samples.
  e=trace.E/'retained-primary-date';receipt=json.loads((e/'receipt.json').read_text());log=(e/'native.log').read_text()
  expected=tuple(receipt['tests']['expected_tests'])
  self.assertEqual(parse_output(log,receipt['rawExit'],expected)['status'],'passed')
  self.assertEqual(hashlib.sha256((e/'Display02Tests.prg').read_bytes()).hexdigest(),receipt['packageSha256'])
  for name in ('watchface/source/LocalePresentation.mc','watchface/display03-tests/Display03Tests.mc','watchface/source/generated/SceneStrings.mc','watchface/resources/json/Locale0.json','watchface/resources/json/Locale1.json'):
   self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),receipt['inputHashes'][name])
  self.assertIn('PRIMARY_DATE locale=en text=Sun 15.11 width=177',log);self.assertIn('PRIMARY_DATE locale=ru text=Вс 15.11 width=155',log)
  for size in (390,454):
   low=trace.bound('ready-low-trace-fixed-'+str(size),'tests/fixtures/display04_ready_low_trace/ReadyLowTrace.mc')
   self.assertIn('date=Sun 15.11|aodFont=152|contextFont=47',low);self.assertIn('date=Вс 15.11|aodFont=152|contextFont=47',low)
   dimensions=trace.bound('low-dimensions-'+str(size),'tests/fixtures/display04_ready_low_trace/ReadyLowDimensions.mc')
   rows=[line[line.index('D04_LOW_BOUNDS|'):] for line in dimensions.splitlines() if 'D04_LOW_BOUNDS|' in line]
   self.assertEqual(len(rows),2)
   self.assertIn('viewport=390x390|phase=1|date=177,47|clock=240,152|count=143,47|battery=82,51|point=335,165',rows[0])
   self.assertIn('viewport=390x390|phase=1|date=155,47|clock=240,152|count=143,47|battery=82,51|point=335,165',rows[1])
  trace.verify_text_trace() # target 454, 390 logical buffer, point filter
  metric=trace.E/'battery-metrics-size51';pre=json.loads((metric/'battery-precompile.json').read_text());build=json.loads((metric/'battery-build.json').read_text());native=(metric/'native.log').read_text()
  self.assertEqual(hashlib.sha256((metric/'MaskObserver.prg').read_bytes()).hexdigest(),build['packageSha256'])
  for name in ('watchface/source/LocalePresentation.mc','watchface/source/SceneRenderer.mc','watchface/source/SpaceFoxView.mc'):
   self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),pre['sourceInputs'][name])
  self.assertIn('batteryFontIsContext=false batteryFontIsCalendar=false height=51 contextHeight=47 width=82 text=50% viewport=390x390',native)
  # AOD bitmap advance and 152px native line height: four 53px digits and
  # a 28px colon, with <=10px correction and +/-1px rest displacement.
  font=(ROOT/'watchface/resources/fonts/Aod40.fnt').read_text();adv=[]
  for ident in (48,56,58,51,56):
   line=next(v for v in font.splitlines() if v.startswith('char id='+str(ident)+' '));adv.append(int(re.search(r'\bxadvance=(\d+)',line)[1]))
  self.assertEqual(adv,[53,53,28,53,53]);self.assertTrue(inside(195-10-1-sum(adv)/2,121,195+10+1+sum(adv)/2,121+152))
  # Actual sampled date width <=177, actual battery 82, fitted countdown
  # <=300; all line heights and one-pixel displacements remain in viewport.
  for width,y,height in ((177,89,47),(300,246,47),(82,295,51)):
   self.assertTrue(inside(194-width/2-1,y-1,196+width/2+1,y+height+1))
  self.assertTrue(inside(328,158,342,172)) # actual source point (335,165), radius 7
  scene=(ROOT/'watchface/source/SceneRenderer.mc').read_text();view=(ROOT/'watchface/source/SpaceFoxView.mc').read_text()
  self.assertNotIn('setClip(',scene);self.assertNotIn('setClip(',view)
  self.assertIn('presentation.fit(dc,current.countdown,countFont,300)',scene)
  self.assertIn('dc.drawBitmap(-(phase%2),-(phase/2),restMask as Graphics.BitmapType);',view)
