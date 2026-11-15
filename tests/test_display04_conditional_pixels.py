"""Actual READY Hold/stale and ascent-conditional native alpha witnesses."""
import hashlib,json,unittest
from pathlib import Path
from PIL import Image
from tools.native_element_masks import dual_background_support,frame_id,validate
from tests import test_display04_native_mask_pixels as pending
from tests import test_display04_ready_mask_pixels as ready
from tests.test_display04_pending_pixels import pending_source_matches
ROOT=Path(__file__).resolve().parents[1]; E=pending.E

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def capture(size):
 d=E/('conditional-'+str(size));pre=json.loads((d/'conditional-precompile.json').read_text());build=json.loads((d/'conditional-build.json').read_text());manifest=json.loads((d/'manifest.json').read_text())
 if sha(d/'conditional-generator.py')!=pre['conditionalProbeSha256'] or sha(d/'ready-generator.py')!=pre['readyProbeSha256'] or sha(d/'ready-template.mc')!=pre['readyTemplateSha256']:raise ValueError('conditional generator changed')
 if sha(d/'MaskObserver.prg')!=build['packageSha256']:raise ValueError('conditional executable changed')
 for name,h in pre['sourceInputs'].items():
  if not pending_source_matches(name,h):raise ValueError('conditional source differs: '+name)
 for name,h in pre['capturedClosure'].items():
  if sha(ROOT/name)!=h:raise ValueError('conditional asset differs: '+name)
 for name,h in pre['generatedInputs'].items():
  if sha(d/'precompile-generated'/name)!=h:raise ValueError('conditional generated source differs: '+name)
 for name,h in pre['generatedResources'].items():
  if sha(d/'precompile-generated/resources'/name)!=h:raise ValueError('conditional resource differs: '+name)
 original=json.loads((E/'ready-mask-en390/precompile-generated/resources/D04Feed.json').read_text())['raw']
 changes=[('"source_status_id":1','"source_status_id":5'),('"source_status_name":"Go for Launch"','"source_status_name":null'),('"stale":false','"stale":true')]
 if pre['conditionalChanges']!=[list(x) for x in changes]:raise ValueError('conditional mutations differ')
 for a,b in changes:
  if original.count(a)!=1:raise ValueError('fixture mutation is ambiguous')
  original=original.replace(a,b)
 if json.loads((d/'precompile-generated/resources/D04Feed.json').read_text())['raw']!=original:raise ValueError('conditional feed differs beyond mutations')
 log=(d/'native.log').read_text()
 if 'D04_CONDITIONAL hold=true stale=true' not in log or ('D04_READY_BUILD_DONE selection='+pre['selectionSha256']+' map=true rocket=true flag=true position=true') not in log:raise ValueError('conditional native scene did not finish')
 ids=['active_none','active_art','active_flame','active_countdown','active_stale','low_none','low_countdown','low_stale']
 if build['selectorIds']!=ids or pre['conditionalIds']!=ids:raise ValueError('conditional selector differs')
 # The READY observer and conditional observer differ only in the explicit
 # mode/phase/selector routing and the diagnostic print. Their fixed clock,
 # settings, fixture, decoder and drawing owner remain identical.
 obs=(d/'precompile-generated/observer/PointObserver.mc').read_text()
 old='''  stopAnimation();MaskObserver.sample();var choice=MaskObserver.selected();var selection=choice+(MaskObserver.white()?"/white":"/black");
  if(!selection.equals(lastMask)){System.println("D04_READY_MASK "+selection);lastMask=selection;}
  if(choice.substring(0,4).equals("low_")){animationProgress=0;aodMinute=null;updateForDisplayMode(dc,System.DISPLAY_MODE_LOW_POWER);}
  else{animationProgress=0.5;updateForDisplayMode(dc,System.DISPLAY_MODE_HIGH_POWER);}
  MaskObserver.barcode(dc);'''
 normal='''  stopAnimation();animationProgress=0;MaskObserver.sample();var selection=MaskObserver.selected()+(MaskObserver.white()?"/white":"/black");
  if(!selection.equals(lastMask)){System.println("D04_READY_MASK "+selection);lastMask=selection;}
  SpaceFoxView.onUpdate(dc);MaskObserver.barcode(dc);'''
 diag='System.println("D04_CONDITIONAL hold="+view.context.sourceHold+" stale="+view.context.stale);'
 if obs.count(old)!=1 or obs.count(diag)!=1:raise ValueError('conditional observer routing changed')
 obs=obs.replace(old,normal).replace(diag,'')
 if obs!=(E/('ready-mask-en'+str(size))/'precompile-generated/observer/PointObserver.mc').read_text():raise ValueError('conditional unchanged inputs differ')
 frames={}
 for key,names in manifest['framesById'].items():
  p=d/names[0]
  if sha(p)!=manifest['sha256'][p.name]:raise ValueError('conditional frame changed')
  image=Image.open(p).convert('RGB')
  if image.size!=(size,size) or frame_id(image)!=int(key):raise ValueError('conditional barcode differs')
  frames[int(key)]=image
 if size==390 and set(frames)==set(range(16))-{10}:
  # Active clear is all black. LOW adds only black/transparent rest pixels,
  # so its missing black baseline is exactly identical outside the barcode.
  black=frames[0].copy();x=(size-48)//2
  for y in range(8,18):
   for xx in range(x-2,x+50):black.putpixel((xx,y),(0,0,0))
  if black.getbbox() is not None:raise ValueError('black baseline is not black')
  mask=Image.open(ROOT/'watchface/resources/drawables/AodRestMask.png').convert('RGBA')
  if not set(mask.getdata())<={(0,0,0,0),(0,0,0,255)}:raise ValueError('rest mask is not black/transparent')
  source=(ROOT/'watchface/source/SpaceFoxView.mc').read_text()
  if 'dc.drawBitmap(-(phase%2),-(phase/2),restMask as Graphics.BitmapType);' not in source:raise ValueError('rest-mask draw changed')
  frames[10]=frames[0]
 if set(frames)!=set(range(16)):raise ValueError('conditional frame inventory incomplete')
 active={ids[i]:dual_background_support(frames[2*i],frames[2*i+1],frames[0],frames[1]) for i in range(1,5)}
 low={ids[i]:dual_background_support(frames[2*i],frames[2*i+1],frames[10],frames[11]) for i in (6,7)}
 # Garmin simulator RGB565 quantizes #FF6B6B to this actual color.
 for n in (6,8,12,14):
  if (255,105,106) not in frames[n].getdata():raise ValueError('actual coral pixels absent')
 return active,low

class ConditionalNativePixelsTest(unittest.TestCase):
 def check_profile(self,size):
  active,low=capture(size)
  regions={'active_art':pending.REGIONS['art'],'active_flame':(40,232,58,250),'active_countdown':pending.REGIONS['countdown'],'active_stale':(56,238,334,245)}
  lowregions={'low_countdown':pending.LOW_REGIONS['countdown'],'low_stale':(80,282,310,290)}
  if size==454:regions={k:pending.scaled(v) for k,v in regions.items()};lowregions={k:pending.scaled(v) for k,v in lowregions.items()}
  self.assertEqual(len(validate(active,regions,size,0)),4)
  self.assertEqual(len(validate(low,lowregions,size,0)),2)
  # Reuse only the matching real-READY operations. Source fixture changes are
  # status/staleness alone; progress changes only art/flame in this renderer.
  if size==390:
   ready.NativeReadyEn390FullCompositionTest.setUpClass();base=dict(ready.NativeReadyEn390FullCompositionTest.images);bounds=dict(ready.NativeReadyEn390FullCompositionTest.regions)
   lowbase,lowbounds=ready.ready_capture('ready-low-en390',390,('none','map','point','countdown','battery'),mode='low')
   rest,extra=ready.ready_capture('ready-low-en390-clockdate',390,('none','date','clock'),mode='low');lowbase.update(rest);lowbounds.update(extra)
  else:
   ready.NativeReadyEn454FullCompositionTest.setUpClass();base=dict(ready.NativeReadyEn454FullCompositionTest.images);bounds=dict(ready.NativeReadyEn454FullCompositionTest.regions)
   lowbase,lowbounds=ready.ready_capture('ready-low-en454-all',454,('none','map','point','date','clock','countdown','battery'),mode='low')
  base['art']=active['active_art'];base['countdown']=active['active_countdown'];base['flame']=active['active_flame'];base['stale']=active['active_stale']
  bounds['flame']=regions['active_flame'];bounds['stale']=regions['active_stale']
  self.assertEqual(len(validate(base,bounds,size,0,background={'map'})),22)
  lowbase['countdown']=low['low_countdown'];lowbase['stale']=low['low_stale'];lowbounds['stale']=lowregions['low_stale']
  self.assertEqual(len(validate(lowbase,lowbounds,size,0,background={'map'})),7)
 def test_390_actual_hold_stale_flame(self):self.check_profile(390)
 def test_454_actual_hold_stale_flame(self):self.check_profile(454)
