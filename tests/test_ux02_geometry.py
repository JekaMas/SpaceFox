"""Geometry measured from unscaled SDK screen captures, not font requests."""
import math
import unittest
from pathlib import Path
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'openspec/changes/spacefox-watchface/evidence/ux02'
FRAMES=['ux02-fr165m-low.png','ux02-time-1111.png','ux02-time-0000.png','ux02-time-2359.png','ux02-fr965-point-low.png']

def measure(name):
    image=Image.open(E/name).convert('RGB');w,h=image.size;raw=image.tobytes()
    assert w==h and w in (390,454), (name,w,h)
    points=[(x,y,tuple(raw[(y*w+x)*3:(y*w+x)*3+3])) for y in range(h) for x in range(w) if any(raw[(y*w+x)*3:(y*w+x)*3+3])]
    rows=sorted({y for x,y,c in points}); bands=[]
    for y in rows:
        if not bands or y>bands[-1][-1]+1: bands.append([])
        bands[-1].append(y)
    boxes=[]
    for band in bands:
        selected=[(x,y) for x,y,c in points if band[0]<=y<=band[-1]]
        xs,ys=zip(*selected); boxes.append((min(xs),min(ys),max(xs),max(ys)))
    return w,points,boxes

class Ux02Geometry(unittest.TestCase):
    def test_real_time_variants_have_gutters_center_and_budget(self):
        for name in FRAMES:
            with self.subTest(frame=name):
                w,points,boxes=measure(name)
                self.assertEqual(len(boxes),4,boxes)
                date,clock,count,battery=boxes
                scale=w/390
                for box,floor in zip(boxes,(28,96,28,32)):
                    self.assertGreaterEqual(box[3]-box[1]+1,math.floor(floor*scale),box)
                self.assertLessEqual(abs((clock[0]+clock[2])/2-w/2),2*scale,clock)
                self.assertLessEqual(abs((clock[1]+clock[3])/2-w/2),2*scale,clock)
                self.assertTrue(all(next_[1]-prior[3]-1>=4 for prior,next_ in zip(boxes,boxes[1:])),boxes)
                self.assertLessEqual(len(points),math.floor(math.pi*(w/2)**2*.1))
                self.assertTrue(all((x-w/2)**2+(y-w/2)**2 < (w/2-4)**2 for x,y,c in points))
                self.assertTrue(any(c==(123,230,197) and date[1]<=y<=battery[3] for x,y,c in points))
                self.assertTrue(any(c==(213,222,238) and date[1]<=y<=date[3] for x,y,c in points))
class Ux02CountdownCorpus(unittest.TestCase):
    def test_finite_real_countdowns_fit_and_preserve_gutters(self):
        for name in ("ux02-ru-count-396h-v2.png", "ux02-ru-count-minus59.png", "ux02-ru-count-plus59.png", "ux02-ru-count-unknown.png"):
            with self.subTest(frame=name):
                w, points, boxes = measure(name)
                date, clock, battery = boxes[0], boxes[1], boxes[-1]
                countdown = boxes[2:-1]
                self.assertTrue(countdown)
                self.assertGreaterEqual(countdown[0][1]-clock[3]-1, 4)
                self.assertGreaterEqual(battery[1]-countdown[-1][3]-1, 4)
                self.assertLessEqual(len(points), math.floor(math.pi*(w/2)**2*.1))
                self.assertTrue(all((x-w/2)**2+(y-w/2)**2 < (w/2-4)**2 for x,y,c in points))
                if "unknown" not in name:
                    self.assertGreaterEqual(countdown[-1][3]-countdown[0][1]+1, 28)

class Ux02Statuses(unittest.TestCase):
    def test_status_color_gaps_and_budget(self):
        for width in (390,454):
            for state in ('stale','reschedule','both'):
                name=f'ux02-status-{state}-{width}-v3.png'
                with self.subTest(frame=name):
                    w,points,boxes=measure(name)
                    self.assertEqual(w,width)
                    self.assertEqual(len(boxes),5 if state!='reschedule' else 4,boxes)
                    date,clock,count=boxes[:3];battery=boxes[-1]
                    self.assertLessEqual(len(points),math.floor(math.pi*(w/2)**2*.1))
                    expected=(156,214,255) if state=='stale' else ((246,194,123) if w==390 else (246,198,123))
                    self.assertTrue(any(c==expected and count[1]<=y<=count[3] for x,y,c in points))
                    self.assertTrue(any(c==(205,182,255) and clock[1]<=y<=clock[3] for x,y,c in points))
                    if state!='reschedule':
                        underline=boxes[3]
                        self.assertGreaterEqual(underline[1]-count[3]-1,2,boxes)
                        self.assertGreaterEqual(battery[1]-underline[3]-1,2,boxes)
                        self.assertTrue(any(c==expected and underline[1]<=y<=underline[3] for x,y,c in points))
                    else:self.assertGreaterEqual(battery[1]-count[3]-1,2,boxes)

if __name__=='__main__':unittest.main()
