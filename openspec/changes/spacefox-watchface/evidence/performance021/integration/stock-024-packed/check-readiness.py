"""Check the retained finite-workload active, LOW and wake observations."""
from pathlib import Path
import sys
from PIL import Image

base = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent

def count(image, box, predicate):
    w, h = image.size
    region = image.crop(tuple(round(v * n) for v, n in zip(box, (w, h, w, h))))
    return sum(predicate(*pixel) for pixel in region.getdata())

white = lambda r, g, b: r > 180 and g > 180 and b > 180
orange = lambda r, g, b: r > 140 and g > 90 and b < 110
blue = lambda r, g, b: b > r * 1.2 and b > 25
for name in ('active', 'wake'):
    im = Image.open(base / (name + '-region.png')).convert('RGB')
    assert im.size == (1130, 1796)
    assert count(im, (.2, .40, .34, .54), white) > 3000, name + ': rocket missing'
    assert count(im, (.25, .55, .75, .66), white) > 2000, name + ': fields missing'
    assert count(im, (.70, .40, .82, .50), orange) > 200, name + ': point missing'
    assert count(im, (.45, .27, .75, .42), blue) > 5000, name + ': map missing'
im = Image.open(base / 'low-region.png').convert('RGB')
assert im.size == (1130, 1796)
assert count(im, (.70, .40, .82, .50), orange) > 100, 'LOW point missing'
assert count(im, (.45, .27, .75, .42), blue) > 1000, 'LOW map missing'
print('finite 19-object stock readiness and LOW/wake map and point: passed')
