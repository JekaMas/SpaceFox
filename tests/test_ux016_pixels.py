"""Acceptance measurements from unscaled 390x390 native SDK screen captures.

Set SPACEFOX_UX_ACTIVE_FRAME and SPACEFOX_UX_AOD_FRAME to repaired captures to
run the identical assertions against the repaired package. Baseline is retained.
Pixel colors are display-quantized exact paint colors, not font line metrics.
"""
import os
from pathlib import Path
import unittest
from tools.spacefox.native_profile import png_pixels

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'openspec/changes/spacefox-watchface/evidence'
ACTIVE=Path(os.environ.get('SPACEFOX_UX_ACTIVE_FRAME',str(EVIDENCE/'ux01-016/active-en.png')))
AOD=Path(os.environ.get('SPACEFOX_UX_AOD_FRAME',str(EVIDENCE/'ux01-016/aod-en.png')))

def pixels(path,box,criterion):
    w,h,raw=png_pixels(path.read_bytes())
    if (w,h)!=(390,390): raise AssertionError(f'not unscaled native capture: {w}x{h}')
    return [(x,y) for y in range(box[1],box[3]) for x in range(box[0],box[2]) if criterion(tuple(raw[(y*w+x)*4:(y*w+x)*4+3]))]

def bounds(points):
    if not points: raise AssertionError('expected ink absent')
    xs,ys=zip(*points);return min(xs),min(ys),max(xs),max(ys)

class NativeUxPixels(unittest.TestCase):
    def test_ux01_active_clock_ink(self):
        b=bounds(pixels(ACTIVE,(70,110,320,202),lambda p:p==(123,230,197)))
        self.assertGreaterEqual(b[3]-b[1]+1,72, f'clock ink bbox {b}')
    def test_ux01_active_countdown_ink(self):
        b=bounds(pixels(ACTIVE,(90,207,300,240),lambda p:p in ((123,230,197),(246,194,123))))
        self.assertGreaterEqual(b[3]-b[1]+1,28, f'countdown ink bbox {b}')
    def test_ux01_active_field_ink(self):
        b=bounds(pixels(ACTIVE,(280,240,345,283),lambda p:p==(246,250,255)))
        self.assertGreaterEqual(b[3]-b[1]+1,32, f'field ink bbox {b}')
    def test_ux01_no_standalone_battery(self):
        found=sum(len(pixels(ACTIVE,box,lambda p:p==(180,194,205))) for box in ((28,98,48,112),(170,24,190,40)))
        self.assertEqual(found,0, f'standalone battery icon ink: {found} pixels')
    def aod_clock(self):
        # Metadata antialiasing can also produce the clock's gray. Segment
        # occupied rows and measure only the tallest connected row band.
        points=pixels(AOD,(0,0,390,390),lambda p:p in ((115,117,115),(139,137,139)))
        rows=sorted({y for _,y in points}); bands=[]
        for y in rows:
            if not bands or y>bands[-1][-1]+1: bands.append([y])
            else: bands[-1].append(y)
        if not bands: raise AssertionError('clock ink absent')
        band=max(bands,key=len)
        return bounds([(x,y) for x,y in points if band[0]<=y<=band[-1]])
    def test_ux01_aod_time_ink_and_center(self):
        b=self.aod_clock()
        self.assertGreaterEqual(b[3]-b[1]+1,84, f'AOD clock ink bbox {b}')
        self.assertLessEqual(abs((b[0]+b[2])/2-195),2, f'AOD clock ink bbox {b}')
        self.assertLessEqual(abs((b[1]+b[3])/2-195),2, f'AOD clock ink bbox {b}')
    def test_ux01_aod_visible_context(self):
        bright=lambda p:min(p)>=140 and max(p)-min(p)<=5
        for name,box in [('date and weekday',(60,80,330,135)),('battery',(60,280,330,320))]:
            b=bounds(pixels(AOD,box,bright))
            self.assertGreaterEqual(b[3]-b[1]+1,20 if name=='battery' else 18,f'{name} ink bbox {b}')
        b=bounds(pixels(AOD,(60,240,330,280),lambda p:p[1]>p[0] and p[2]>p[0]))
        self.assertGreaterEqual(b[3]-b[1]+1,22,f'countdown ink bbox {b}')
    def test_ux01_aod_lit_pixel_limit(self):
        self.assertLess(len(pixels(AOD,(0,0,390,390),lambda p:any(p))),11945)

if __name__=='__main__':unittest.main()
