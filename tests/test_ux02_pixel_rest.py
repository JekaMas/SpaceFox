"""Independent pixel-set oracle on four actual SDK LOW captures per device."""
import math
import os
import unittest
from pathlib import Path
from PIL import Image
E=Path(__file__).resolve().parents[1]/'openspec/changes/spacefox-watchface/evidence/ux02'
class PixelRest(unittest.TestCase):
    def test_mask_only_removes_pixels_without_changing_rgb(self):
        for phase in range(4):
            before=Image.open(E/f'phase-old-{phase}.png').convert('RGB')
            after=Image.open(E/f'phase-checker-{phase}.png').convert('RGB')
            self.assertEqual(before.size,after.size)
            for old,new in zip(before.get_flattened_data(),after.get_flattened_data()):
                self.assertTrue(new==(0,0,0) or new==old,(phase,old,new))

    def test_four_phases_fit_and_every_pixel_rests(self):
        cases=((390,'phase-old-'),) if os.getenv('UX02_PHASE_BASELINE')=='1' else ((390,'phase-checker-'),(454,'phase-checker-454-'))
        for size,prefix in cases:
            phases=[]
            for phase in range(4):
                image=Image.open(E/f'{prefix}{phase}.png').convert('RGB')
                self.assertEqual(image.size,(size,size))
                pixels=image.load()
                lit={(x,y) for y in range(size) for x in range(size) if any(pixels[x,y])}
                self.assertLessEqual(len(lit),math.floor(math.pi*(size/2)**2*.1))
                self.assertTrue(all((x-size/2)**2+(y-size/2)**2 < (size/2-4)**2 for x,y in lit))
                scale=size/390
                ranges=((95,140,28),(140,250,96),(250,290,28),(290,330,32))
                boxes=[]
                for lo,hi,floor in ranges:
                    part={(x,y) for x,y in lit if math.floor(lo*scale)<=y<math.ceil(hi*scale)}
                    self.assertTrue(part,(size,phase,lo))
                    ys=[y for x,y in part];boxes.append((min(ys),max(ys)))
                    self.assertGreaterEqual(max(ys)-min(ys)+1,math.floor(floor*scale),(size,phase,lo))
                self.assertTrue(all(b[0]-a[1]-1>=4 for a,b in zip(boxes,boxes[1:])),(size,phase,boxes))
                phases.append(lit)
            self.assertEqual(len(set.intersection(*phases)),0,(size,'continuously lit pixels'))
if __name__=='__main__':unittest.main()
