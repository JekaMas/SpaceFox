"""Native ink-height witnesses; a colored fill is separate from dark contour."""
import json,re,unittest
from pathlib import Path
from PIL import Image,ImageChops
from tests import test_display04_native_mask_pixels as masks

ROOT=Path(__file__).resolve().parents[1]
E=masks.E

def colored_black_frame(folder,selector):
 d=E/folder;m=json.loads((d/'manifest.json').read_text())
 def image(identity):
  path=d/m['framesById'][str(identity)][0]
  if masks.digest(path)!=m['sha256'][path.name]:raise ValueError('typography frame changed')
  return Image.open(path).convert('RGB')
 image_black=image(selector);empty_black=image(0);diff=ImageChops.difference(image_black,empty_black).convert('L');x=(diff.width-48)//2
 for y in range(8,18):
  for z in range(x-2,x+50):diff.putpixel((z,y),0)
 return diff

def height(image):
 box=image.getbbox()
 if box is None:raise ValueError('missing actual colored ink')
 return box[3]-box[1]

class NativeTypographyBoundsTest(unittest.TestCase):
 def test_available_numeric_components_and_unavailable_dashes(self):
  masks.NativePendingEn390MasksTest.setUpClass();masks.NativePendingRu454MasksTest.setUpClass()
  for folder,size in [('mask-active-en390',390),('mask-active-ru454',454)]:
   image=colored_black_frame(folder,32);columns=[x for x in range(image.width) if any(image.getpixel((x,y)) for y in range(230,image.height-50))];runs=[]
   for x in columns:
    if not runs or x>runs[-1][-1]+1:runs.append([x])
    else:runs[-1].append(x)
   heights=[]
   for run in runs:
    ys=[y for x in run for y in range(230,image.height-50) if image.getpixel((x,y))]
    heights.append(max(ys)-min(ys)+1)
   # EN has one separate punctuation component; RU uses a space. The five
   # numeric glyphs are checked individually, never by their union bbox.
   numeric=[v for v in heights if v>=28]
   self.assertEqual(len(numeric),5);self.assertTrue(all(v>=32*size/390 for v in numeric))
   for slot in (1,2,3):
    dash=colored_black_frame(folder,32+2*slot);self.assertLess(height(dash),20)

 def test_metric_digits_share_one_source_font_in_all_four_slots(self):
  # Source-atlas bounds complement, but do not replace, the actual five-digit
  # native samples above. All roles use this same loaded font and draw loop.
  root=ROOT/'watchface/resources/fonts';atlas=Image.open(root/'Metric32.png').convert('L')
  rows=(root/'Metric32.fnt').read_text().splitlines();digits={}
  for row in rows:
   fields={k:int(v) for k,v in re.findall(r'(id|x|y|width|height)=([0-9]+)',row)}
   if 48<=fields.get('id',0)<=57:
    x,y,w,h=(fields[k] for k in ('x','y','width','height'));box=atlas.crop((x,y,x+w,y+h)).getbbox()
    self.assertIsNotNone(box);digits[fields['id']]=box[3]-box[1]
  self.assertEqual(set(digits),set(range(48,58)));self.assertTrue(all(h>=32 for h in digits.values()))
  source=(ROOT/'watchface/source/SceneRenderer.mc').read_text()
  self.assertIn('fonts["metric"] = load(Rez.Fonts.Metric32)',source)
  loop=source.split('for (var i = 0; i < 4; i += 1) {',1)[1].split('if(selectedMap)',1)[0]
  self.assertIn('text(dc,left+width/2,y,fonts["metric"] as Graphics.FontType,label,settings.fieldColors[i],128,1);',loop)
