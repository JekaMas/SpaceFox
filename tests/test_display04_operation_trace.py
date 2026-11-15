"""Source-bound *partial* native operation reuse for pending EN/RU scenes.

A matched text/icon operation is a reuse candidate at the same device size. It
is not complete visible-alpha, bitmap, LOW, READY, preclip or release evidence.
"""
import json,unittest
from functools import lru_cache
from pathlib import Path
from tools.run_native_tests import parse_output
from tests import test_display04_native_mask_pixels as masks
E=masks.E
digest=masks.digest
from tests.test_display04_pending_pixels import pending_source_matches

ROOT=Path(__file__).resolve().parents[1]
IDS=('header_rocket','header_separator','header_operator','purpose','footer','date','clock','countdown',
     'icon_0','field_0','icon_1','field_1','icon_2','field_2','icon_3','field_3')
REUSABLE={'header_rocket','header_separator','header_operator','footer','clock','countdown',
          'icon_0','icon_1','field_1','icon_2','field_2','icon_3','field_3'}

def bound(folder,test):
 d=E/folder;pre=json.loads((d/'precompile.json').read_text());rec=json.loads((d/'receipt.json').read_text())
 if digest(ROOT/test)!=pre['testInput']:raise ValueError('trace source changed')
 for path,sha in pre['inputs'].items():
  if not pending_source_matches(path,sha):raise ValueError('trace owner changed: '+path)
 for path,sha in pre['generated'].items():
  if digest(d/path)!=sha:raise ValueError('generated trace input changed: '+path)
 if digest(d/'Trace.prg')!=rec['packageSha256']:raise ValueError('trace binary changed')
 log=(d/'native.log').read_text();name=rec['test']['expected_tests'][0]
 if parse_output(log,rec['rawExit'],(name,))['status']!='passed':raise ValueError('native trace failed')
 return log

def operations(log):
 result={0:[],1:[]}
 for line in log.splitlines():
  if 'D04_TRACE_' not in line:continue
  fields=line[line.index('D04_TRACE_'):].split('|');language=int(fields.pop(1));result[language].append(fields)
 if any(len(rows)!=len(IDS) for rows in result.values()):raise ValueError('native trace inventory differs')
 return {language:dict(zip(IDS,rows)) for language,rows in result.items()}

@lru_cache(maxsize=1)
def verify_text_trace():
 self=unittest.TestCase()
 a=operations(bound('trace-pending-390','tests/fixtures/display04_operation_trace/Trace.mc'))
 b=operations(bound('trace-pending-454','tests/fixtures/display04_operation_trace/Trace.mc'))
 self.assertEqual(a,b) # Native trace is logical 390 on each profile, not scaled pixels.
 for rows in (a,b):
  self.assertEqual({name for name in IDS if rows[0][name]==rows[1][name]},REUSABLE)
  self.assertEqual(rows[0]['clock'][-1],'08:38')
  self.assertEqual(rows[0]['purpose'][-1],'Communications')
  self.assertEqual(rows[1]['purpose'][-1],'Связь')
 scale=bound('scale-view-454','tests/fixtures/display04_scale_trace/TraceScale.mc')
 self.assertIn('target=454x454|buffer=390x390|draw=390x390|end=454.000000,454.000000|filter=0',scale)
 return True

@lru_cache(maxsize=1)
def verify_font_and_mask_inputs():
 self=unittest.TestCase()
 log=bound('font-trace-390-corrected','tests/fixtures/display04_font_trace/TraceFonts.mc')
 for locale,index in [('en',0),('ru',1)]:
  self.assertIn(f'D04_FONT|{index}|locale={locale}|face=RobotoRegular|labelVector=true|smallVector=true|countVector=true',log)
  self.assertEqual(json.loads((ROOT/f'watchface/resources/json/Locale{index}.json').read_text())['face'],'RobotoRegular')
 fonts=json.loads((ROOT/'openspec/changes/spacefox-watchface/evidence/language-settings-whole/basic-five-finite/fonts.json').read_text())
 self.assertEqual(fonts['fonts']['RobotoRegular']['sha256'],'31d218ca177e4c2191134f9c14fb43027f8a38622476db14038fd8ff186f875e')
 # Full source and screenshot bindings, including the historically unchanged
 # pending ACTIVE bodies, are checked by these established capture readers.
 masks.NativePendingEn390MasksTest.setUpClass();masks.NativePendingRu454MasksTest.setUpClass()
 return True

class PendingOperationTraceTest(unittest.TestCase):
 def test_source_bound_language_inputs_and_454_transform(self):
  self.assertTrue(verify_text_trace())

 def test_native_font_identity_and_matching_mask_sources(self):
  self.assertTrue(verify_font_and_mask_inputs())

class PendingChangedMaskCompositionTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  # The composition must refuse reuse even when selected alone, rather than
  # relying on a different unittest method having run earlier.
  verify_text_trace();verify_font_and_mask_inputs()
 @staticmethod
 def combined(folder,language,size,base_class):
  from PIL import Image
  from tools.native_element_masks import frame_id,dual_background_support
  from tests.test_display04_pending_pixels import check_capture_inputs
  d=E/folder;pre=json.loads((d/'subset-precompile.json').read_text());build=json.loads((d/'subset-build.json').read_text())
  check_capture_inputs(build)
  if build['language']!=language or build['mode']!='active' or build['frozenAnimationPhase']!='0' or build['selectorIds']!=['none','purpose','date','field_0']:
   raise ValueError('subset context differs')
  if pre['subsetProbeSha256']!=digest(ROOT/'tools/native_display04_subset_mask_probe.py') or digest(d/'MaskObserver.prg')!=build['packageSha256']:
   raise ValueError('subset build identity changed')
  for name,sha in pre['sourceInputs'].items():
   if not pending_source_matches(name,sha):raise ValueError('subset source changed: '+name)
  for name,sha in pre['generatedInputs'].items():
   if digest(d/'precompile-generated'/name)!=sha:raise ValueError('subset generated source changed: '+name)
  manifest=json.loads((d/'manifest.json').read_text());frames={}
  if manifest['missingSelectionIds'] or {int(k) for k in manifest['framesById']}!=set(range(8)):raise ValueError('subset frames incomplete')
  for key,values in manifest['framesById'].items():
   p=d/values[0]
   if digest(p)!=manifest['sha256'][p.name]:raise ValueError('subset frame changed')
   image=Image.open(p).convert('RGB')
   if image.size!=(size,size) or frame_id(image)!=int(key):raise ValueError('subset barcode or size differs')
   frames[int(key)]=image
  # Real native isolated alpha is paired against the actual empty black/white
  # baselines from this same observer. The other IDs reuse same-profile masks
  # only after the native semantic operation trace and font checks above.
  subset={name:dual_background_support(frames[i*2],frames[i*2+1],frames[0],frames[1]) for i,name in enumerate(build['selectorIds'][1:],1)}
  trace_name='bitmap-trace-390' if size==390 else 'bitmap-trace-454'
  bitmap_log=bound(trace_name,'tests/fixtures/display04_bitmap_trace/TraceBitmap.mc')
  rows=[line[line.index('D04_BITMAP|'):] for line in bitmap_log.splitlines() if 'D04_BITMAP|' in line]
  if len(rows)!=2 or rows[0].replace('D04_BITMAP|0|','D04_BITMAP|x|')!=rows[1].replace('D04_BITMAP|1|','D04_BITMAP|x|'):
   raise ValueError('native bitmap resources or arguments differ across locales')
  if '|pin=335,165|filter=1|phase=0|downloaded=false|stale=false' not in rows[0]:raise ValueError('pending bitmap context differs')
  source=(ROOT/'watchface/source/SceneRenderer.mc').read_text()
  for condition in ('if (progress > 0 && progress < 1)', 'var flag=rich==null?null:rich.siteCountryBitmap;', 'if ((current.stale || context != null && context.stale))'):
   if condition not in source:raise ValueError('conditional operation changed')
  base_class.setUpClass();return {name:base_class.masks[name] for name in REUSABLE|{'map','art','point'}}|subset

 def test_ru390_changed_text_and_reused_operations(self):
  from tools.native_element_masks import validate
  masks_by_id=self.combined('subset-ru390','ru',390,masks.NativePendingEn390MasksTest)
  regions={name:masks.REGIONS[name] for name in masks_by_id};counts=validate(masks_by_id,regions,390,0,background={'map'})
  self.assertEqual(set(counts),REUSABLE|{'purpose','date','field_0','map','art','point'});self.assertTrue(all(counts.values()))

 def test_en454_changed_text_and_reused_operations(self):
  from tools.native_element_masks import validate
  masks_by_id=self.combined('subset-en454','en',454,masks.NativePendingRu454MasksTest)
  regions={name:masks.scaled(masks.REGIONS[name]) for name in masks_by_id};counts=validate(masks_by_id,regions,454,0,background={'map'})
  self.assertEqual(set(counts),REUSABLE|{'purpose','date','field_0','map','art','point'});self.assertTrue(all(counts.values()))

class PendingLowMaskCompositionTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  verify_text_trace();verify_font_and_mask_inputs()
  cls.renderer=None;cls.observer=None;cls.mask_source=None

 @classmethod
 def subset(cls,folder,language,size,expected_ids,missing=()):
  import re
  from PIL import Image
  from tools.native_element_masks import frame_id,dual_background_support
  from tests.test_display04_pending_pixels import check_capture_inputs
  d=E/folder;pre=json.loads((d/'subset-precompile.json').read_text());build=json.loads((d/'subset-build.json').read_text())
  check_capture_inputs(build)
  if build['language']!=language or build['mode']!='low' or build['frozenAnimationPhase']!='0' or build['selectorIds']!=expected_ids:
   raise ValueError('LOW subset context differs')
  if pre['subsetProbeSha256']!=digest(ROOT/'tools/native_display04_subset_mask_probe.py') or digest(d/'MaskObserver.prg')!=build['packageSha256']:
   raise ValueError('LOW subset build identity changed')
  for name,sha in pre['sourceInputs'].items():
   if not pending_source_matches(name,sha):raise ValueError('LOW source changed: '+name)
  for name,sha in pre['generatedInputs'].items():
   if digest(d/'precompile-generated'/name)!=sha:raise ValueError('LOW generated input changed: '+name)
  renderer=(d/'precompile-generated/source/SceneRenderer.mc').read_bytes()
  observer=(d/'precompile-generated/observer/PointObserver.mc').read_text().replace('{"Language"=>1}','{"Language"=>0}')
  mask=(d/'precompile-generated/source/MaskObserver.mc').read_text()
  mask=re.sub(r'var ids=\[[^\]]+\];','var ids=<selector>;',mask)
  mask=re.sub(r'System.getTimer\(\)/\d+','System.getTimer()/<stage>',mask)
  if cls.renderer is None:cls.renderer,cls.observer,cls.mask_source=renderer,observer,mask
  elif (renderer,observer,mask)!=(cls.renderer,cls.observer,cls.mask_source):raise ValueError('LOW isolation path changed beyond selector or locale')
  if 'return 1794551202;' not in observer or 'stopAnimation();animationProgress=0;' not in observer or 'aodMinute=null;updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);' not in observer:
   raise ValueError('LOW snapshot/phase not frozen')
  manifest=json.loads((d/'manifest.json').read_text());frames={}
  if manifest['missingSelectionIds']!=list(missing):raise ValueError('LOW missing-selector record differs')
  for key,values in manifest['framesById'].items():
   p=d/values[0]
   if digest(p)!=manifest['sha256'][p.name]:raise ValueError('LOW subset frame changed')
   image=Image.open(p).convert('RGB')
   if image.size!=(size,size) or frame_id(image)!=int(key):raise ValueError('LOW subset barcode or size differs')
   frames[int(key)]=image
  wanted=set(range(len(expected_ids)*2))-set(missing)
  if set(frames)!=wanted:raise ValueError('LOW subset inventory differs')
  result={}
  for index,name in enumerate(expected_ids[1:],1):
   if 2*index in frames and 2*index+1 in frames:
    result[name]=dual_background_support(frames[2*index],frames[2*index+1],frames[0],frames[1])
  return result

 @classmethod
 def baseline390(cls):
  ids=['none','map','point','date','clock','countdown','stale','battery']
  values=cls.subset('low-en390','en',390,ids,missing=(2,))
  target=cls.subset('low-en390-map','en',390,['none','map'])
  values['map']=target['map']
  if values.pop('stale').getbbox() is not None:raise ValueError('unexpected LOW stale status')
  return values

 @staticmethod
 def verify(values,size):
  from tools.native_element_masks import validate
  regions={n:(masks.LOW_REGIONS[n] if size==390 else masks.scaled(masks.LOW_REGIONS[n])) for n in values}
  counts=validate(values,regions,size,0,background={'map'})
  if set(counts)!=set(masks.LOW_REGIONS) or not all(counts.values()):raise ValueError('LOW foreground inventory differs')
  return counts

 def test_en390_pending_low(self):
  self.verify(self.baseline390(),390)

 def test_ru390_pending_low(self):
  values=self.baseline390();values['date']=self.subset('low-ru390-date','ru',390,['none','date'])['date'];values['battery']=self.subset('low-ru390-battery','ru',390,['none','battery'])['battery'];self.verify(values,390)

 def test_en454_pending_low(self):
  # Establish exact test-only operation source/clock/phase equivalence with the
  # actual RU/454 baseline before reusing its same-profile non-date masks.
  self.subset('low-en454-date','en',454,['none','date'])
  original=E/'mask-low-ru454'
  if (original/'precompile-generated/source/SceneRenderer.mc').read_bytes()!=self.renderer:raise ValueError('prior LOW renderer differs')
  observer=(original/'precompile-generated/observer/PointObserver.mc').read_text().replace('{"Language"=>1}','{"Language"=>0}')
  if observer!=self.observer:raise ValueError('prior LOW observer differs')
  import re
  prior_mask=(original/'precompile-generated/source/MaskObserver.mc').read_text()
  prior_mask=re.sub(r'var ids=\[[^\]]+\];','var ids=<selector>;',prior_mask)
  prior_mask=re.sub(r'System.getTimer\(\)/\d+','System.getTimer()/<stage>',prior_mask)
  if prior_mask!=self.mask_source:raise ValueError('prior LOW selector changed beyond ID and stage')
  masks.NativePendingRu454LowMasksTest.setUpClass();values=dict(masks.NativePendingRu454LowMasksTest.masks)
  values['date']=self.subset('low-en454-date','en',454,['none','date'])['date'];values['battery']=self.subset('low-en454-battery','en',454,['none','battery'])['battery'];self.verify(values,454)
