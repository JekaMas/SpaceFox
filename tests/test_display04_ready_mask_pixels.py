"""Actual decoded selected READY operation masks, not physical/perf proof."""
import hashlib,json,unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image
from tools.native_element_isolation import isolate
from tools.native_element_masks import frame_id,dual_background_support,validate
from tests import test_display04_native_mask_pixels as pending
from tests.test_display04_pending_pixels import pending_source_matches

ROOT=Path(__file__).resolve().parents[1]
E=pending.E/'ready-mask-en390'
IDS=('none','map','art','flag','point','header_rocket','header_separator','header_operator','purpose','footer','countdown')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def ready_capture(folder,size,ids=IDS,language='en',mode='active'):
 e=pending.E/folder
 pre=json.loads((e/'ready-precompile.json').read_text());build=json.loads((e/'ready-build.json').read_text())
 if sha(e/'ready-generator.py')!=pre['readyProbeSha256'] or sha(e/'ready-template.mc')!=pre['readyTemplateSha256']:
  raise ValueError('READY test source changed')
 if sha(e/'MaskObserver.prg')!=build['packageSha256'] or pre['selectionSha256']!=build['readySelection']:
  raise ValueError('READY executable identity differs')
 for name,digest in pre['sourceInputs'].items():
  if not pending_source_matches(name,digest):raise ValueError('READY source owner changed: '+name)
 for name,digest in pre['capturedClosure'].items():
  if sha(ROOT/name)!=digest:raise ValueError('READY captured object changed: '+name)
 for name,digest in pre['generatedInputs'].items():
  if sha(e/'precompile-generated'/name)!=digest:raise ValueError('READY generated input changed: '+name)
 for name,digest in pre['generatedResources'].items():
  if sha(e/'precompile-generated/resources'/name)!=digest:raise ValueError('READY generated resource changed: '+name)
 source=(ROOT/'watchface/source/SpaceFoxView.mc').read_text();start=source.index('    function bodyBatteryChanged(');end=source.index('    function stopFitness()',start)
 if hashlib.sha256(source[start:end].encode()).hexdigest()!=pre['omittedHealthCallbackSha256']:
  raise ValueError('original health callback differs')
 transformed=source[:start]+'    function bodyBatteryChanged(id as Object) as Void {}\n'+source[end:]
 if transformed!=(e/'precompile-generated/source/SpaceFoxView.mc').read_text() or sha(ROOT/'watchface/source/BodyBatterySource.mc')!=pre['omittedHealthAdapterSha256']:
  raise ValueError('READY test changes extend beyond unused health surface')
 if (e/'precompile-generated/source/SceneRenderer.mc').read_text()!=isolate((ROOT/'watchface/source/SceneRenderer.mc').read_text()):
  raise ValueError('READY native draw isolation differs')
 tree=ET.parse(e/'precompile-generated/manifest.xml');app=tree.getroot().find('{http://www.garmin.com/xml/connectiq}application')
 perms=app.find('{http://www.garmin.com/xml/connectiq}permissions')
 if app.get('type')!='watch-app' or any(p.get('id')=='ComplicationSubscriber' for p in perms):raise ValueError('READY test allowance differs')
 profile=json.loads((e/'profile-boundary.json').read_text());lock=json.loads((ROOT/'watchface/toolchain-lock.json').read_text())
 if profile['compilerProfileSha256']!=lock['profiles'][profile['device']]['files_sha256']['compiler.json'] or profile['simulatorProfileSha256']!=lock['profiles'][profile['device']]['files_sha256']['simulator.json'] or profile['watchAppDeclaredBytes']!=786432 or profile['watchFaceDeclaredBytes']!=131072 or profile['graphicsResourcePoolDeclaredBytes']!=(2097152 if size==390 else 3145728):
  raise ValueError('READY profile boundary differs')
 log=(e/'native.log').read_text();expected='D04_READY_BUILD_DONE selection='+pre['selectionSha256']+' map=true rocket=true flag=true position=true'
 if expected not in log or 'D04_READY_BUILD_ERROR' in log or 'Out Of Memory' in log:raise ValueError('actual READY completion not observed')
 if build['selectorIds']!=list(ids) or build['language']!=language or build['mode']!=mode or build['frozenAnimationPhase']!='0':raise ValueError('READY capture context differs')
 manifest=json.loads((e/'manifest.json').read_text())
 if manifest['missingSelectionIds'] or {int(k) for k in manifest['framesById']}!=set(range(2*len(ids))):raise ValueError('READY mask inventory incomplete')
 frames={}
 for key,names in manifest['framesById'].items():
  p=e/names[0]
  if sha(p)!=manifest['sha256'][p.name]:raise ValueError('READY frame changed')
  image=Image.open(p).convert('RGB')
  if image.size!=(size,size) or frame_id(image)!=int(key):raise ValueError('READY barcode differs')
  frames[int(key)]=image
 images={name:dual_background_support(frames[2*i],frames[2*i+1],frames[0],frames[1]) for i,name in enumerate(ids[1:],1)}
 source_regions=pending.REGIONS if mode=='active' else pending.LOW_REGIONS
 regions={name:(source_regions[name] if size==390 else pending.scaled(source_regions[name])) for name in images if name!='flag'}
 if 'flag' in images:regions['flag']=(72,317,318,348) if size==390 else pending.scaled((72,317,318,348))
 return images,regions

class NativeReadyEn390ChangedMasksTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.masks,cls.regions=ready_capture('ready-mask-en390',390)

 def test_decoded_changed_roles_ink_and_overlap(self):
  counts=validate(self.masks,self.regions,390,0,background={'map'})
  self.assertEqual(set(counts),set(IDS)-{'none'});self.assertTrue(all(counts.values()))

 def test_actual_flag_overlap_and_boundary_negatives(self):
  flag=self.masks['flag'].copy();footer=self.masks['footer'].copy();flag.putpixel((110,330),255);footer.putpixel((110,330),255)
  with self.assertRaisesRegex(ValueError,'foreground overlap'):
   validate({'flag':flag,'footer':footer},{'flag':self.regions['flag'],'footer':self.regions['footer']},390,0)
  flag=self.masks['flag'].copy();flag.putpixel((71,330),255)
  with self.assertRaisesRegex(ValueError,'region overflow: flag'):
   validate({'flag':flag},{'flag':self.regions['flag']},390,0)

class NativeReadyEn390FullCompositionTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from tests import test_display04_operation_trace as trace
  trace.verify_text_trace();trace.verify_font_and_mask_inputs()
  a=trace.operations(trace.bound('ready-trace-390','tests/fixtures/display04_ready_operation_trace/ReadyTrace.mc'))
  b=trace.operations(trace.bound('ready-trace-454','tests/fixtures/display04_ready_operation_trace/ReadyTrace.mc'))
  if a!=b:raise ValueError('READY logical text trace differs by native profile')
  prior=trace.operations(trace.bound('trace-pending-390','tests/fixtures/display04_operation_trace/Trace.mc'))
  unchanged={'date','clock','field_0','field_1','field_2','field_3','icon_0','icon_1','icon_2','icon_3'}
  if any(a[0][name]!=prior[0][name] for name in unchanged):raise ValueError('READY operand differs from pending trace')
  # The real READY feed and catalog used by the operation trace are the exact
  # same generated resource bytes admitted by the native mask observer.
  trace_dir=pending.E/'ready-trace-390/resources';capture=E/'precompile-generated/resources'
  for name in ('D04Feed.json','D04Catalog.json'):
   if (trace_dir/name).read_bytes()!=(capture/name).read_bytes():raise ValueError('READY trace fixture differs: '+name)
  NativeReadyEn390ChangedMasksTest.setUpClass();pending.NativePendingEn390MasksTest.setUpClass()
  cls.images=dict(NativeReadyEn390ChangedMasksTest.masks)
  cls.images.update({name:pending.NativePendingEn390MasksTest.masks[name] for name in unchanged})
  cls.regions=dict(NativeReadyEn390ChangedMasksTest.regions)
  cls.regions.update({name:pending.REGIONS[name] for name in unchanged})
  # The only foreground clip belongs to rocket animation and is cleared before
  # the later flag, footer, date, clock and fields execute.
  source=(ROOT/'watchface/source/NativeVisualRenderer.mc').read_text()
  if 'dc.setClip(22,118-ascent,54,124);dc.drawBitmap2(frameX,frameY,bitmap,drawOptions);dc.clearClip();' not in source:
   raise ValueError('rocket clip ownership differs')

 def test_ready_full_composition_actual_ink_and_regions(self):
  counts=validate(self.images,self.regions,390,0,background={'map'})
  self.assertEqual(len(counts),20);self.assertTrue(all(counts.values()))

class NativeReadyEn454FullCompositionTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from tests import test_display04_operation_trace as trace
  trace.verify_text_trace();trace.verify_font_and_mask_inputs()
  ready=trace.operations(trace.bound('ready-trace-454','tests/fixtures/display04_ready_operation_trace/ReadyTrace.mc'))
  prior=trace.operations(trace.bound('trace-pending-454','tests/fixtures/display04_operation_trace/Trace.mc'))
  unchanged={'date','clock','field_0','field_1','field_2','field_3','icon_0','icon_1','icon_2','icon_3'}
  if any(ready[0][name]!=prior[0][name] for name in unchanged):raise ValueError('454 READY operand differs from pending trace')
  trace_dir=pending.E/'ready-trace-454/resources';capture=pending.E/'ready-mask-en454/precompile-generated/resources'
  for name in ('D04Feed.json','D04Catalog.json'):
   if (trace_dir/name).read_bytes()!=(capture/name).read_bytes():raise ValueError('454 READY trace fixture differs: '+name)
  cls.images,cls.regions=ready_capture('ready-mask-en454',454)
  trace.PendingChangedMaskCompositionTest.setUpClass()
  prior_masks=trace.PendingChangedMaskCompositionTest.combined('subset-en454','en',454,pending.NativePendingRu454MasksTest)
  cls.images.update({name:prior_masks[name] for name in unchanged});cls.regions.update({name:pending.scaled(pending.REGIONS[name]) for name in unchanged})
  source=(ROOT/'watchface/source/NativeVisualRenderer.mc').read_text()
  if 'dc.setClip(22,118-ascent,54,124);dc.drawBitmap2(frameX,frameY,bitmap,drawOptions);dc.clearClip();' not in source:
   raise ValueError('454 rocket clip ownership differs')

 def test_ready_454_full_composition_actual_ink_and_regions(self):
  counts=validate(self.images,self.regions,454,0,background={'map'})
  self.assertEqual(len(counts),20);self.assertTrue(all(counts.values()))

class NativeReadyRuFullCompositionTest(unittest.TestCase):
 @staticmethod
 def compose(size):
  from tests import test_display04_operation_trace as trace
  name='ready-asset-trace-'+str(size);log=trace.bound(name,'tests/fixtures/display04_ready_asset_trace/ReadyAssetTrace.mc')
  pre=json.loads((pending.E/name/'precompile.json').read_text())
  if pre['retainedReadyPrecompileSha256']!=sha(pending.E/'ready-mask-en390/ready-precompile.json'):
   raise ValueError('READY asset trace source closure changed')
  expected='ddef3be6db53150c8c9b4b1712c758cde77d2a2137a981cfcf5a3876aa014d0c'
  if pre['capturedSelection']!=expected:raise ValueError('READY selection differs')
  asset_rows=[line[line.index('D04_READY_ASSETS|'):] for line in log.splitlines() if 'D04_READY_ASSETS|' in line]
  if len(asset_rows)!=2 or asset_rows[0].replace('D04_READY_ASSETS|0|','D04_READY_ASSETS|x|')!=asset_rows[1].replace('D04_READY_ASSETS|1|','D04_READY_ASSETS|x|'):
   raise ValueError('READY decoded asset identity differs across locale')
  if 'selection='+expected+'|map=390x390|rocket=54x124|flag=20x12|phase=0|position=true' not in asset_rows[0]:raise ValueError('READY assets incomplete')
  real=trace.operations(log.replace('D04_READY_TRACE_','D04_TRACE_'))
  # The only actual text/icon differences are purpose, localized date and step
  # grouping. Those three must exactly match the native RU pending fixture.
  changed={'purpose','date','field_0'}
  if {n for n in trace.IDS if real[0][n]!=real[1][n]}!=changed:raise ValueError('READY locale operation delta differs')
  prior=trace.operations(trace.bound('trace-pending-'+str(size),'tests/fixtures/display04_operation_trace/Trace.mc'))
  if any(real[1][name]!=prior[1][name] for name in changed):raise ValueError('READY RU operation differs from pending source')
  if size==390:
   NativeReadyEn390FullCompositionTest.setUpClass();images=dict(NativeReadyEn390FullCompositionTest.images);regions=dict(NativeReadyEn390FullCompositionTest.regions)
   trace.PendingChangedMaskCompositionTest.setUpClass();ru=trace.PendingChangedMaskCompositionTest.combined('subset-ru390','ru',390,pending.NativePendingEn390MasksTest)
  else:
   NativeReadyEn454FullCompositionTest.setUpClass();images=dict(NativeReadyEn454FullCompositionTest.images);regions=dict(NativeReadyEn454FullCompositionTest.regions)
   pending.NativePendingRu454MasksTest.setUpClass();ru=pending.NativePendingRu454MasksTest.masks
  images.update({n:ru[n] for n in changed});return images,regions

 def test_ru390_ready_composition(self):
  images,regions=self.compose(390);counts=validate(images,regions,390,0,background={'map'});self.assertEqual(len(counts),20);self.assertTrue(all(counts.values()))

 def test_ru454_ready_composition(self):
  images,regions=self.compose(454);counts=validate(images,regions,454,0,background={'map'});self.assertEqual(len(counts),20);self.assertTrue(all(counts.values()))

class NativeReadyEnLowCompositionTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from tests import test_display04_operation_trace as trace
  cls.logs={}
  for size in (390,454):
   log=trace.bound('ready-low-trace-fixed-'+str(size),'tests/fixtures/display04_ready_low_trace/ReadyLowTrace.mc')
   rows=[line[line.index('D04_READY_LOW|'):] for line in log.splitlines() if 'D04_READY_LOW|' in line]
   if len(rows)!=2 or not all('|bundled=true|' in r and '|point=335,165|minutePhase=1|clock=08:38|count=T- 04:29|' in r for r in rows):
    raise ValueError('READY LOW native resource/phase trace differs')
   cls.logs[size]=rows
  expected='aodMinute=null;updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);MaskObserver.barcode(dc);'
  originals=[]
  for folder in ('ready-low-en390','ready-low-en390-clockdate','ready-low-en454-all'):
   source=(pending.E/folder/'precompile-generated/observer/PointObserver.mc').read_text()
   if expected not in source or 'function utcSeconds(){return 1794576343;}' not in source:raise ValueError('READY LOW snapshot/phase differs')
   originals.append(source)
  if len(set(originals))!=1:raise ValueError('READY LOW observers differ beyond selector')

 def test_en390_ready_low_full_visible_composition(self):
  a,regions=ready_capture('ready-low-en390',390,('none','map','point','countdown','battery'),mode='low')
  b,more=ready_capture('ready-low-en390-clockdate',390,('none','date','clock'),mode='low')
  a.update(b);regions.update(more);counts=validate(a,regions,390,0,background={'map'});self.assertEqual(set(counts),set(pending.LOW_REGIONS));self.assertTrue(all(counts.values()))

 def test_en454_ready_low_full_visible_composition(self):
  a,regions=ready_capture('ready-low-en454-all',454,('none','map','point','date','clock','countdown','battery'),mode='low')
  counts=validate(a,regions,454,0,background={'map'});self.assertEqual(set(counts),set(pending.LOW_REGIONS));self.assertTrue(all(counts.values()))

class NativeReadyRuLowCompositionTest(unittest.TestCase):
 @staticmethod
 def compose(size):
  from tests import test_display04_operation_trace as trace
  log=trace.bound('ready-low-trace-fixed-'+str(size),'tests/fixtures/display04_ready_low_trace/ReadyLowTrace.mc')
  rows=[line[line.index('D04_READY_LOW|'):] for line in log.splitlines() if 'D04_READY_LOW|' in line]
  if len(rows)!=2:raise ValueError('READY LOW native trace missing locale')
  def invariant(row):
   fields=row.split('|');return [v for v in fields[2:] if not v.startswith('date=')]
  if invariant(rows[0])!=invariant(rows[1]) or '|minutePhase=1|clock=08:38|count=T- 04:29|' not in rows[0]:
   raise ValueError('READY LOW non-date operation differs by locale')
  if size==390:
   values,regions=ready_capture('ready-low-en390',390,('none','map','point','countdown','battery'),mode='low')
   common,extra=ready_capture('ready-low-en390-clockdate',390,('none','date','clock'),mode='low');values.update(common);regions.update(extra)
   new,more=ready_capture('ready-low-ru390-datebattery',390,('none','date','battery'),language='ru',mode='low')
   base_folder='ready-low-en390';ru_folder='ready-low-ru390-datebattery'
  else:
   values,regions=ready_capture('ready-low-en454-all',454,('none','map','point','date','clock','countdown','battery'),mode='low')
   new,more=ready_capture('ready-low-ru454-datebattery',454,('none','date','battery'),language='ru',mode='low')
   base_folder='ready-low-en454-all';ru_folder='ready-low-ru454-datebattery'
  en=(pending.E/base_folder/'precompile-generated/observer/PointObserver.mc').read_text();ru=(pending.E/ru_folder/'precompile-generated/observer/PointObserver.mc').read_text().replace('{"Language"=>1}','{"Language"=>0}')
  if en!=ru:raise ValueError('READY LOW observer differs beyond locale and selector')
  values.update(new);regions.update(more);return values,regions

 def test_ru390_ready_low(self):
  images,regions=self.compose(390);counts=validate(images,regions,390,0,background={'map'});self.assertEqual(set(counts),set(pending.LOW_REGIONS));self.assertTrue(all(counts.values()))

 def test_ru454_ready_low(self):
  images,regions=self.compose(454);counts=validate(images,regions,454,0,background={'map'});self.assertEqual(set(counts),set(pending.LOW_REGIONS));self.assertTrue(all(counts.values()))
