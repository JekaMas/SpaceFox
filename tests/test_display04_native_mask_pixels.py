"""Native RU/454 pending ACTIVE operation masks, scoped to visible pixels.

The barcode strip and intentionally clipped map backdrop are explicit. This
suite does not prove preclip pixels, READY or another language/device.
"""
import hashlib
import json
import math
from pathlib import Path
import unittest
from PIL import Image
from tools.native_display04_mask_probe import IDS
from tools.native_element_masks import frame_id, dual_background_support, validate
from tests.test_display04_pending_pixels import check_capture_inputs, pending_source_matches

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'openspec/changes/spacefox-watchface/evidence/display04-whole-quality'
# Independent logical 390px intent bands, before scaling to the target face.
# Broad areas constrain each semantic role; actual ink intersection is checked
# independently, including adjacent same-color operations.
REGIONS={
 'map':(0,0,390,390),'art':(20,110,80,242),'point':(315,145,350,180),
 # Variable-width rocket and operator share the centered 238px title budget;
 # their actual ink, including the separator, must still be pairwise disjoint.
 'header_rocket':(74,40,316,70),'header_separator':(74,40,316,70),
 'header_operator':(74,40,316,70),'purpose':(50,70,340,90),
 # Bands derive from the accepted centered fit budgets and fixed row origins,
 # including contour/font boxes. Their shared space is checked by actual ink
 # pairwise intersection, not by assuming font-box whitespace is empty.
 'footer':(72,317,318,348),'date':(93,93,297,134),
 'clock':(68,107,322,227),'countdown':(56,200,334,250),
 'field_0':(50,238,186,294),'field_1':(204,238,338,294),
 'field_2':(50,276,204,332),'field_3':(204,276,338,332),
 'icon_0':(22,244,51,278),'icon_1':(174,244,306,278),
 'icon_2':(22,281,63,316),'icon_3':(174,281,306,316),
}
ABSENT={'flame','flag','stale','battery'}

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def scaled(rect):
    x0,y0,x1,y1=rect;s=454/390
    return (math.floor(x0*s),math.floor(y0*s),math.ceil(x1*s),math.ceil(y1*s))

class NativePendingRu454MasksTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    old=E/'mask-active-ru454';target=E/'mask-active-ru454-target33'
    original=json.loads((old/'batch-build.json').read_text())
    current=json.loads((target/'batch-build.json').read_text())
    check_capture_inputs(original,allow_historical_active=True)
    check_capture_inputs(current)
    cls.assert_bound(old,original,'exact-precompile.json','exact-rebuild-result.json')
    pre=json.loads((target/'batch-precompile.json').read_text())
    for name,sha in pre['sourceInputs'].items():
        if not pending_source_matches(name,sha):raise ValueError('target source input changed: '+name)
    if 'D04_MASK field_0/white' not in (target/'native.log').read_text():raise ValueError('target native selector was not observed')
    for name,sha in pre['generatedInputs'].items():
        if digest(target/'precompile-generated'/name)!=sha:raise ValueError('target generated input changed: '+name)
    if current['element']!='timed batch with per-frame ID barcode' or current['frozenAnimationPhase']!='0':raise ValueError('target context differs')
    if original['frozenAnimationPhase']!='0' or original['language']!='ru' or original['mode']!='active':raise ValueError('original context differs')
    old_observer=old/'precompile-generated/observer/PointObserver.mc';new_observer=target/'precompile-generated/observer/PointObserver.mc'
    if old_observer.read_bytes()!=new_observer.read_bytes():raise ValueError('observer snapshot changed')
    def active(source):
        source=source.read_text();return source[source.index('    function maskText('):source.index('    function metricText(')]
    if active(old/'precompile-generated/source/SceneRenderer.mc')!=active(target/'precompile-generated/source/SceneRenderer.mc'):
        raise ValueError('ACTIVE operation source changed')
    manifest=json.loads((old/'manifest.json').read_text());frames={}
    for key,names in manifest['framesById'].items():
        image_path=old/names[0]
        if digest(image_path)!=manifest['sha256'][image_path.name]:raise ValueError('captured frame changed')
        image=Image.open(image_path).convert('RGB')
        if frame_id(image)!=int(key):raise ValueError('barcode identity changed')
        frames[int(key)]=image
    capture=json.loads((target/'capture.json').read_text());path=target/capture['file']
    if digest(path)!=capture['sha256']:raise ValueError('target frame changed')
    image=Image.open(path).convert('RGB')
    if frame_id(image)!=33:raise ValueError('target barcode differs')
    frames[33]=image
    if set(frames)!=set(range(48)):raise ValueError('incomplete selector/background inventory')
    if set(IDS)!=set(REGIONS)|ABSENT:raise ValueError('operation inventory differs')
    masks={name:dual_background_support(frames[2*i],frames[2*i+1],frames[0],frames[1]) for i,name in enumerate(IDS,1)}
    for name in ABSENT:
        if masks[name].getbbox() is not None:raise ValueError('unexpected pending element: '+name)
    cls.masks={name:masks[name] for name in REGIONS}
    cls.regions={name:scaled(rect) for name,rect in REGIONS.items()}

 @staticmethod
 def assert_bound(evidence,build,pre_name,result_name):
    pre=json.loads((evidence/pre_name).read_text());result=json.loads((evidence/result_name).read_text())
    if result['exitCode']!=0 or not result['byteIdentical'] or not result['inputsUnchangedDuringCompile'] or result['capturedPrgSha256']!=build['packageSha256'] or result['rebuiltPrgSha256']!=build['packageSha256']:
        raise ValueError('original captured program rebuild differs')
    for name,sha in pre['commonOriginalInputs'].items():
        if not pending_source_matches(name,sha):raise ValueError('original common input changed: '+name)
    for name,sha in pre['generatedInputs'].items():
        if digest(evidence/'precompile-generated'/name)!=sha:raise ValueError('original generated input changed: '+name)

 def test_actual_visible_alpha_regions_and_pairwise_overlap(self):
    counts=validate(self.masks,self.regions,454,0,background={'map'})
    self.assertTrue(all(counts[name]>0 for name in REGIONS))

 def test_actual_mask_one_pixel_overflow_and_overlap_fail(self):
    name='clock';image=self.masks[name].copy();x0,y0,x1,y1=self.regions[name]
    image.putpixel((x0-1,180),255)
    with self.assertRaisesRegex(ValueError,'region overflow: clock'):
        validate({name:image},{name:self.regions[name]},454,0)
    date=self.masks['date'].copy();clock=self.masks['clock'].copy();date.putpixel((227,145),255);clock.putpixel((227,145),255)
    with self.assertRaisesRegex(ValueError,'foreground overlap'):
        validate({'date':date,'clock':clock},{'date':self.regions['date'],'clock':self.regions['clock']},454,0)


LOW_REGIONS={
 'map':(0,0,390,390), 'point':(315,145,350,180),
 'date':(90,89,300,130), 'clock':(60,140,325,247),
 'countdown':(80,246,310,286), 'battery':(120,295,270,339),
}

class NativePendingRu454LowMasksTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    evidence=E/'mask-low-ru454'
    build=json.loads((evidence/'batch-build.json').read_text())
    pre=json.loads((evidence/'batch-precompile.json').read_text())
    check_capture_inputs(build)
    for name,sha in pre['sourceInputs'].items():
        if not pending_source_matches(name,sha):raise ValueError('LOW source input changed: '+name)
    for name,sha in pre['generatedInputs'].items():
        if digest(evidence/'precompile-generated'/name)!=sha:raise ValueError('LOW generated input changed: '+name)
    ids=['none','map','point','date','clock','countdown','stale','battery']
    if build['selectorIds']!=ids or build['language']!='ru' or build['mode']!='low':raise ValueError('LOW context differs')
    manifest=json.loads((evidence/'manifest.json').read_text())
    if manifest['missingSelectionIds'] or {int(k) for k in manifest['framesById']}!=set(range(16)):
        raise ValueError('incomplete LOW masks')
    frames={}
    for identity,names in manifest['framesById'].items():
        path=evidence/names[0]
        if digest(path)!=manifest['sha256'][path.name]:raise ValueError('LOW frame changed')
        image=Image.open(path).convert('RGB')
        if frame_id(image)!=int(identity):raise ValueError('LOW barcode differs')
        frames[int(identity)]=image
    masks={name:dual_background_support(frames[2*i],frames[2*i+1],frames[0],frames[1]) for i,name in enumerate(ids[1:],1)}
    if masks['stale'].getbbox() is not None:raise ValueError('unexpected stale underline')
    # The actual LOW draw owner routes no configurable-field values or icons.
    source=(ROOT/'watchface/source/SceneRenderer.mc').read_text().split('module SceneAod {',1)[1]
    if 'metricText(' in source or 'icon(' in source or 'settings.slots' in source:
        raise ValueError('LOW acquired configurable fields')
    cls.masks={name:masks[name] for name in LOW_REGIONS}
    cls.regions={name:scaled(rect) for name,rect in LOW_REGIONS.items()}

 def test_low_visible_alpha_regions_and_pairwise_overlap(self):
    counts=validate(self.masks,self.regions,454,0,background={'map'})
    self.assertTrue(all(counts[name]>0 for name in LOW_REGIONS))

 def test_low_actual_mask_one_pixel_overflow_fails(self):
    image=self.masks['clock'].copy();x0,y0,x1,y1=self.regions['clock'];image.putpixel((x0-1,200),255)
    with self.assertRaisesRegex(ValueError,'region overflow: clock'):
        validate({'clock':image},{'clock':self.regions['clock']},454,0)


class NativePendingEn390MasksTest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    evidence=E/'mask-active-en390';build=json.loads((evidence/'batch-build.json').read_text());pre=json.loads((evidence/'batch-precompile.json').read_text())
    check_capture_inputs(build)
    for name,sha in pre['sourceInputs'].items():
        if digest(ROOT/name)!=sha:raise ValueError('EN/390 source changed: '+name)
    for name,sha in pre['generatedInputs'].items():
        if digest(evidence/'precompile-generated'/name)!=sha:raise ValueError('EN/390 generated input changed: '+name)
    if build['language']!='en' or build['mode']!='active' or build['frozenAnimationPhase']!='0':raise ValueError('EN/390 context differs')
    manifest=json.loads((evidence/'manifest.json').read_text())
    if manifest['missingSelectionIds'] or {int(k) for k in manifest['framesById']}!=set(range(48)):raise ValueError('EN/390 masks incomplete')
    frames={}
    for identity,names in manifest['framesById'].items():
        path=evidence/names[0]
        if digest(path)!=manifest['sha256'][path.name]:raise ValueError('EN/390 frame changed')
        image=Image.open(path).convert('RGB')
        if frame_id(image)!=int(identity):raise ValueError('EN/390 barcode differs')
        frames[int(identity)]=image
    masks={name:dual_background_support(frames[2*i],frames[2*i+1],frames[0],frames[1]) for i,name in enumerate(IDS,1)}
    for name in ABSENT:
        if masks[name].getbbox() is not None:raise ValueError('unexpected EN/390 pending element: '+name)
    cls.masks={name:masks[name] for name in REGIONS}

 def test_visible_alpha_regions_and_pairwise_overlap(self):
    counts=validate(self.masks,REGIONS,390,0,background={'map'})
    self.assertTrue(all(counts[name]>0 for name in REGIONS))

 def test_one_pixel_overflow_on_actual_mask_is_rejected(self):
    image=self.masks['clock'].copy();x0,y0,x1,y1=REGIONS['clock'];image.putpixel((x0-1,160),255)
    with self.assertRaisesRegex(ValueError,'region overflow: clock'):
        validate({'clock':image},{'clock':REGIONS['clock']},390,0)
