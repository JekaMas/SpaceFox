"""Actual AOD atlas ink projected into the declared 390px circular display."""
from pathlib import Path
import re
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def glyphs(name='Aod40'):
    atlas=Image.open(ROOT/f'watchface/resources/fonts/{name}.png').convert('L')
    rows=(ROOT/f'watchface/resources/fonts/{name}.fnt').read_text().splitlines()
    result={}
    for row in rows:
        if not row.startswith('char id='): continue
        f={k:int(v) for k,v in re.findall(r'(id|x|y|width|height|xoffset|yoffset|xadvance)=(-?\d+)',row)}
        pts={(x+f['xoffset'],y+f['yoffset']) for y in range(f['height']) for x in range(f['width']) if atlas.getpixel((f['x']+x,f['y']+y))>20}
        result[chr(f['id'])]=(f['xadvance'],pts)
    return result


def clock_ink(text, x, y, phase, data):
    width=sum(data[c][0] for c in text)
    cursor=x-width//2;points=set()
    for c in text:
        advance, glyph=data[c]
        points.update((cursor+gx+phase[0],y+gy+phase[1]) for gx,gy in glyph)
        cursor+=advance
    return points


def validate_circle(points):
    if any((x-194.5)**2+(y-194.5)**2>194.5**2 for x,y in points):
        raise ValueError('clock ink outside circular display')


class Display04LowGeometryTest(unittest.TestCase):
    def test_committed_clock_baseline_is_vertically_centered(self):
        source=(ROOT/'watchface/source/SceneRenderer.mc').read_text()
        m=re.search(r'dc\.drawText\(195\+p\[0\]\+correction,(\d+),font,current\.localTime',source)
        self.assertIsNotNone(m)
        points=clock_ink('08:08',195,int(m.group(1)),(0,0),glyphs())
        center=(min(y for _,y in points)+max(y for _,y in points))/2
        self.assertLessEqual(abs(center-195),2, f'ink center {center}')

    def test_centered_clock_avoids_fixed_projected_pin(self):
        # 08:08 was a real collision with the original-width atlas when moved
        # to the centered baseline, at (335,158); the repair must clear it.
        data=glyphs();points=clock_ink('08:08',195,121,(0,0),data)
        pin={(x,y) for x in range(328,343) for y in range(158,173) if (x-335)**2+(y-165)**2<=49}
        self.assertFalse(points & pin, f'pin overlaps clock at {sorted(points & pin)[:5]}')

    def test_all_valid_times_rest_phases_and_projected_pin(self):
        data=glyphs()
        source=(ROOT/'watchface/source/SceneRenderer.mc').read_text()
        baseline=int(re.search(r'dc\.drawText\(195\+p\[0\]\+correction,(\d+),font,current\.localTime',source).group(1))
        left=[int(x) for x in re.search(r'var leftEdges=\[([^]]+)\]',source).group(1).split(',')]
        right=[int(x) for x in re.search(r'var rightEdges=\[([^]]+)\]',source).group(1).split(',')]
        advance=int(re.search(r'\((\d+)-leftEdges\[first',source).group(1))
        pin={(x,y) for x in range(327,344) for y in range(157,174)
             if (x-335)**2+(y-165)**2<=64}
        for hour in range(24):
            for minute in range(60):
                value=f'{hour:02d}:{minute:02d}'
                correction=int((advance-left[int(value[0])]-right[int(value[-1])])/2)
                points=clock_ink(value,195+correction,baseline,(0,0),data)
                for phase,(dx,dy) in enumerate(((-1,-1),(1,-1),(-1,1),(1,1))):
                    rest={(x+dx,y) for x,y in points if not ((x+dx)%2==phase%2 and y%2==phase//2)}
                    xs=[x for x,y in rest];ys=[y for x,y in rest]
                    self.assertGreaterEqual(max(ys)-min(ys)+1,96,(value,phase))
                    self.assertLessEqual(abs((min(xs)+max(xs))/2-195),2,(value,phase,'x'))
                    self.assertLessEqual(abs((min(ys)+max(ys))/2-195),2,(value,phase,'y'))
                    self.assertFalse(rest & pin,(value,phase,'pin'))
                    validate_circle(rest)

    def test_circle_detector_rejects_one_pixel_boundary_violation(self):
        validate_circle({(195,1)})
        with self.assertRaisesRegex(ValueError, 'outside circular display'):
            validate_circle({(195,0)})


class Display04ActivePointGeometryTest(unittest.TestCase):
    def test_every_clock_time_avoids_real_marker_ink(self):
        # Actual bitmap-font pixels and alpha, rendered separately so matching
        # colors cannot hide collisions. SDK drawing/scale remains a later gate.
        data=glyphs('Time80')
        marker=Image.open(ROOT/'watchface/resources/drawables/LaunchMarker.png').convert('RGBA')
        pin={(321+x,151+y) for y in range(marker.height) for x in range(marker.width) if marker.getpixel((x,y))[3]>0}
        for hour in range(24):
            for minute in range(60):
                text=f'{hour:02d}:{minute:02d}'
                ink=clock_ink(text,195,109,(0,0),data)
                contour={(x+dx,y+dy) for x,y in ink for dx in (-1,0,1) for dy in (-1,0,1)}
                for dx in (-1,0,1):
                    for dy in (-1,0,1):
                        self.assertFalse(contour & {(x+dx,y+dy) for x,y in pin}, (text,dx,dy))
                if text=='08:38':
                    self.assertTrue(pin)
                    self.assertGreaterEqual(min(x for x,y in pin)-max(x for x,y in contour),1)


class NativeScaledLowClockExtremaTest(unittest.TestCase):
    def test_native_454_extrema_cover_all_phases_and_fit(self):
        import hashlib
        import json
        evidence=ROOT/'openspec/changes/spacefox-watchface/evidence/display04-whole-quality/clock-cases-454'
        manifest=json.loads((evidence/'manifest.json').read_text())
        pre=json.loads((evidence/'exact-precompile.json').read_text())
        rebuilt=json.loads((evidence/'exact-rebuild-result.json').read_text())
        self.assertEqual(rebuilt['exitCode'],0)
        self.assertTrue(rebuilt['byteIdentical'])
        self.assertTrue(rebuilt['inputsUnchangedDuringCompile'])
        self.assertEqual(pre['capturedPrgSha256'],rebuilt['rebuiltPrgSha256'])
        self.assertEqual(pre['capturedPrgSha256'],json.loads((evidence/'cases-build.json').read_text())['programSha256'])
        from tests.test_display04_pending_pixels import pending_source_matches
        for name,digest in pre['sourceInputs'].items():
            self.assertTrue(pending_source_matches(name,digest),name)
        for name,digest in pre['generatedInputs'].items():
            self.assertEqual(hashlib.sha256((evidence/'precompile-generated'/name).read_bytes()).hexdigest(),digest,name)
        self.assertEqual(manifest['missingIds'],[])
        self.assertEqual({int(k) for k in manifest['framesById']},set(range(12)))
        for identity,files in manifest['framesById'].items():
            with self.subTest(case=int(identity)):
                image_path=evidence/files[0]
                self.assertEqual(hashlib.sha256(image_path.read_bytes()).hexdigest(),manifest['sha256'][image_path.name])
                image=Image.open(image_path).convert('RGB');self.assertEqual(image.size,(454,454))
                start=(image.width-48)//2
                self.assertGreater(image.getpixel((start+2,12))[0],200)
                self.assertGreater(image.getpixel((start+42,12))[0],200)
                actual=sum((image.getpixel((start+7+5*bit,12))[0]>200)<<bit for bit in range(6))
                self.assertEqual(actual,int(identity))
                points=[]
                for y in range(120,290):
                    for x in range(image.width):
                        red,green,blue=image.getpixel((x,y))
                        if green>40 and green>red*1.3 and green>blue*1.05:
                            points.append((x,y))
                self.assertTrue(points)
                xs=[x for x,y in points];ys=[y for x,y in points]
                self.assertLessEqual(abs((min(xs)+max(xs))/2-227),2*454/390)
                self.assertLessEqual(abs((min(ys)+max(ys))/2-227),2*454/390)
                self.assertGreaterEqual(max(ys)-min(ys)+1,96*454/390)
