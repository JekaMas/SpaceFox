"""Measurements on actual source-bound native captures, not font boxes."""
import math
import unittest
from pathlib import Path
from PIL import Image
E=Path(__file__).resolve().parents[1]/'openspec/changes/spacefox-watchface/evidence/ux03'

def points(im,rect,predicate):
    scale=im.width/390
    x0,y0,x1,y1=(round(v*scale) for v in rect)
    return [(x,y) for y in range(y0,y1) for x in range(x0,x1) if predicate(*im.getpixel((x,y)))]
def box(p):
    if not p: raise AssertionError('expected ink missing')
    return min(x for x,y in p),min(y for x,y in p),max(x for x,y in p),max(y for x,y in p)
def lavender(r,g,b):return r>180 and b>230 and r>g*1.05
def blue(r,g,b):return 140<=r<=165 and 200<=g<=220 and b>=245
def dot(r,g,b):return 110<=r<=170 and 170<=g<=225 and b>=200
def bright(r,g,b):return r>=170 and g>=160 and b>=190

class Ux03Pixels(unittest.TestCase):
 def test_stale_ink_marker_fields_and_gutters(self):
  for width,name in [(390,'active-stale-final-390.png'),(454,'active-stale-454.png')]:
   with self.subTest(width=width):
    im=Image.open(E/name).convert('RGB');self.assertEqual(im.size,(width,width));scale=width/390
    clock=box(points(im,(55,100,325,207),lavender));count=box(points(im,(70,205,320,239),blue));dots=box(points(im,(70,239,320,245),dot))
    self.assertGreaterEqual(count[1]-clock[3]-1,4)
    self.assertGreaterEqual(dots[1]-count[3]-1,2)
    upper=[box(points(im,r,bright)) for r in ((20,245,195,282),(195,245,370,282))]
    self.assertGreaterEqual(min(b[1] for b in upper)-dots[3]-1,4)
    lower=[box(points(im,r,bright)) for r in ((20,290,195,320),(195,282,370,320))]
    self.assertLess(upper[0][2],upper[1][0]);self.assertLess(lower[0][2],lower[1][0])
    # The actual English 12,345 comma reaches y289; the second row 72 starts
    # at y287 but its rightmost ink is x99 and the comma starts at x102.
    if width==390:
     comma=box(points(im,(100,282,110,290),bright));second=box(points(im,(50,287,100,320),bright));self.assertGreaterEqual(comma[0]-second[2]-1,2)
    yellow=points(im,(321,151,349,179),lambda r,g,b:r>=245 and 200<=g<=220 and 80<=b<=120)
    self.assertGreater(len(yellow),50*scale*scale)
    self.assertTrue(all((x-width/2)**2+(y-width/2)**2<(width/2)**2 for x,y in yellow))
 def test_low_selected_colors_and_lit_budget(self):
  for width,name in [(390,'low-stale-final-390.png'),(454,'low-stale-454.png')]:
   with self.subTest(width=width):
    im=Image.open(E/name).convert('RGB');pixels=list(im.getdata());lit=sum(any(c) for c in pixels)
    self.assertLessEqual(lit,math.floor(math.pi*(width/2)**2*.1))
    self.assertTrue(points(im,(40,140,350,245),lavender));self.assertTrue(points(im,(70,250,320,284),blue))
    self.assertTrue(points(im,(125,290,270,327),lambda r,g,b:r>=180 and g>=180 and b>=180))
if __name__=='__main__':unittest.main()
