"""Check independently isolated native element alpha masks.

Capture input must include an overscan border, so pixels outside the device
circle remain observable. Masks must be isolated by draw operation, not by
output color: differently named operations can use exactly the same color.
"""
from itertools import combinations
from PIL import Image, ImageChops


def frame_id(image):
    """Decode the test observer's embedded selector, not screenshot timing."""
    image=image.convert('RGB');width,height=image.size
    if width!=height or width not in (390,454):raise ValueError('unexpected frame dimensions')
    x=(width-48)//2
    if image.getpixel((x+2,12))[0]<200 or image.getpixel((x+42,12))[0]<200:
        raise ValueError('mask barcode sentinel missing')
    return sum((image.getpixel((x+7+5*bit,12))[0]>200)<<bit for bit in range(6))


def dual_background_support(black,white,empty_black,empty_white):
    """Native visible alpha support from paired black/white compositing.

    Subtract each output channel's black-to-white span from its corresponding
    empty-frame span. The maximum positive channel deficit records visible
    source coverage even for black or white ink. This is 16-bit SDK output:
    intensities are quantized, and clipped/offscreen pixels cannot be inferred.
    The test-only barcode rectangle is deliberately removed.
    """
    images=[im.convert('RGB') for im in (black,white,empty_black,empty_white)]
    if len({im.size for im in images})!=1:raise ValueError('mask pair size differs')
    output=Image.new('L',images[0].size)
    for b,w,eb,ew in zip(*(im.split() for im in images)):
        reference=ImageChops.subtract(ew,eb)
        observed=ImageChops.subtract(w,b)
        output=ImageChops.lighter(output,ImageChops.subtract(reference,observed))
    x=(output.width-48)//2
    for y in range(8,18):
        for z in range(x-2,x+50):output.putpixel((z,y),0)
    return output

def validate(masks, regions, diameter, overscan, *, background=(), allowed_pairs=()):
    """Return ink counts or raise with the first empty, overflowing, overlapping ink.

    ``regions`` are independent intended rectangles in device coordinates,
    with right/bottom exclusive. Background masks may intentionally clip the
    round face and are excluded from foreground overlap checks.
    """
    if set(masks) != set(regions) or not masks:
        raise ValueError('element inventory differs')
    side = diameter + 2 * overscan
    center = overscan + diameter / 2
    radius2 = (diameter / 2) ** 2
    backgrounds = set(background)
    pairs = {frozenset(pair) for pair in allowed_pairs}
    ink = {}
    for name, source in masks.items():
        image = source if isinstance(source, Image.Image) else Image.open(source)
        if image.size != (side, side) or image.mode not in ('L', 'RGBA'):
            raise ValueError('invalid overscan alpha mask: ' + name)
        alpha = image if image.mode == 'L' else image.getchannel('A')
        x0, y0, x1, y1 = regions[name]
        if not (x0 < x1 and y0 < y1):
            raise ValueError('empty intended region: ' + name)
        points = set()
        for y in range(side):
            for x in range(side):
                if not alpha.getpixel((x, y)):
                    continue
                points.add((x, y))
                if name not in backgrounds:
                    dx, dy = x + .5 - center, y + .5 - center
                    if dx * dx + dy * dy > radius2:
                        raise ValueError('circle overflow: ' + name)
                    if not (x0 <= x - overscan < x1 and y0 <= y - overscan < y1):
                        raise ValueError('region overflow: ' + name)
        if not points:
            raise ValueError('missing element: ' + name)
        ink[name] = points
    for a, b in combinations(sorted(set(masks) - backgrounds), 2):
        if frozenset((a, b)) not in pairs and ink[a] & ink[b]:
            raise ValueError('foreground overlap: ' + a + ' / ' + b)
    return {name: len(points) for name, points in ink.items()}
