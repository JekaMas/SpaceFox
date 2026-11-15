"""Examine all ten actual digit inks under the four pixel-rest parities."""
from pathlib import Path
import re, unittest
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
class Display02AodFontTest(unittest.TestCase):
 def test_each_digit_rest_phase_and_centering(self):
  fnt=(ROOT/'watchface/resources/fonts/Aod40.fnt').read_text();img=Image.open(ROOT/'watchface/resources/fonts/Aod40.png').convert('L');edges=[]
  for digit in range(10):
   row=next(line for line in fnt.splitlines() if line.startswith('char id='+str(48+digit)+' '))
   fields={k:int(v) for k,v in re.findall(r'(x|y|width|height|xadvance)=(-?\d+)',row)};x,y,w,h=(fields[k] for k in ('x','y','width','height'));lit=[(a,b) for a in range(w) for b in range(h) if img.getpixel((x+a,y+b))>20];self.assertTrue(lit)
   for dx in range(2):
    for dy in range(2):
     remaining=[(a,b) for a,b in lit if not(a%2==dx and b%2==dy)];self.assertGreaterEqual(max(b for a,b in remaining)-min(b for a,b in remaining)+1,96,(digit,dx,dy))
   strong=[a for a,b in lit if img.getpixel((x+a,y+b))>=128];edges.append((min(strong),max(strong)+1,fields['xadvance']))
  left=[5,9,4,4,4,5,5,4,5,5];right=[48,37,49,48,50,48,49,49,48,48]
  self.assertEqual([(a,b) for a,b,_ in edges],list(zip(left,right)))
  for first in range(10):
   for last in range(10):
    correction=int((54-left[first]-right[last])/2);ink_center=(left[first]+right[last]-edges[first][2])/2+correction
    self.assertLessEqual(abs(ink_center),2,(first,last))
