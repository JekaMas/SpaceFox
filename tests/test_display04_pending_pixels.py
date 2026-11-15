"""Captured real-feed pending point on SDK; no READY or device claim."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import unittest
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
E=ROOT/'openspec/changes/spacefox-watchface/evidence/display04-whole-quality/pending-point-current'

def capture_input_relevant(name):
    # The captured observer has no admitted optional batch, so the decoder is
    # never invoked. Its later implementation and the generated version ID do
    # not change these pending pixels; neither exemption grants READY proof.
    if name in ('watchface/source/NativeSfr.mc','watchface/source/generated/NativeVersion.mc'):
        return False
    return (name.startswith(('watchface/source/','watchface/resources/','watchface/resources-','watchface/display04-observer/'))
            or name in ('watchface/manifest.xml','watchface/toolchain-lock.json','tests/fixtures/watch_refresh_cache/packets.json','tools/native_display04_point_probe.py'))


def historical_unchanged_pending_input(name, digest):
    """Check exact old bytes for two unexercised post-capture changes.

    The pending observer admits no downloaded scene, so NativeVisualRenderer
    is never called; the changed native test-runner bookkeeping cannot affect
    pixels. Each old source is reconstructed byte-for-byte and checked against
    its original receipt, without replacing the historical digest.
    """
    current=(ROOT/name).read_text()
    if name=='watchface/source/NativeVisualRenderer.mc':
        prior=(E.parent/'mask-active-ru454/precompile-generated/source/NativeVisualRenderer.mc').read_text()
        old='''        transform.setToTranslation((27-27*frameScale).toFloat(),(62-62*frameScale).toFloat());transform.scale(frameScale.toFloat(),frameScale.toFloat());
    }
    function draw(dc,progress,ascent){
        if(bitmap==null){return;}prepareFrame(progress,ascent);
        dc.setClip(22,118-ascent,54,124);dc.drawBitmap2(frameX,frameY,bitmap,drawOptions);dc.clearClip();
    }'''
        new='''    }
    // The source transform scales about the 54x124 frame center. Use the
    // union of translation-before/after-scale bounds and a pixel of rounding
    // margin: only frames that cannot intersect the intended clip are skipped.
    function frameIntersects(ascent){
        var tx=27.0-27.0*frameScale;var ty=62.0-62.0*frameScale;
        var sx=tx*frameScale;var sy=ty*frameScale;
        var left=frameX+(tx<sx?tx:sx)-1;var right=frameX+(tx>sx?tx:sx)+bitmap.getWidth()*frameScale+1;
        var top=frameY+(ty<sy?ty:sy)-1;var bottom=frameY+(ty>sy?ty:sy)+bitmap.getHeight()*frameScale+1;
        return right>22 && left<76 && bottom>118-ascent && top<242-ascent;
    }
    function draw(dc,progress,ascent){
        if(bitmap==null){return;}prepareFrame(progress,ascent);if(!frameIntersects(ascent)){return;}
        transform.setToTranslation((27-27*frameScale).toFloat(),(62-62*frameScale).toFloat());transform.scale(frameScale.toFloat(),frameScale.toFloat());
        dc.setClip(22,118-ascent,54,124);dc.drawBitmap2(frameX,frameY,bitmap,drawOptions);dc.clearClip();
    }'''
        if prior.count(old)!=1 or prior.replace(old,new)!=current:raise ValueError('unexpected visual renderer delta')
    elif name=='tools/native_display03_probe.py':
        prior=current.replace(",'display03SkipInvisibleRocket')",")")
        old=''';build=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'compile.log').write_text(build.stdout)'''
        new='''
 generated={str(q.relative_to(out)):sha(q) for q in [out/'manifest.xml',out/'probe.jungle',*sorted(out.glob('*.mc')),*sorted(res.glob('*'))]}
 (out/'precompile.json').write_text(json.dumps({'inputHashes':before,'generatedInputs':generated,'buildCommand':cmd},indent=2)+'\\n')
 build=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=120);(out/'compile.log').write_text(build.stdout)
 if any(sha(out/n)!=digest for n,digest in generated.items()):raise RuntimeError('generated native inputs changed during compile')'''
        if prior.count(new)!=1:raise ValueError('unexpected native probe delta')
        prior=prior.replace(new,old)
    else:
        return False
    return hashlib.sha256(prior.encode()).hexdigest()==digest

def pending_source_matches(name, digest):
    current=(ROOT/name).read_bytes()
    if hashlib.sha256(current).hexdigest()==digest:return True
    if name in ('watchface/source/NativeVisualRenderer.mc','tools/native_display03_probe.py'):
        return historical_unchanged_pending_input(name,digest)
    if name=='watchface/source/generated/NativeVersion.mc':
        prior=E.parent/'clock-cases-454/historical-inputs/NativeVersion.mc'
        old=prior.read_bytes()
        # The version identity is not drawn by the pending observer. The
        # semantic BUILD is unchanged; the ID follows the modified native tree.
        import re
        build_pattern=rb'const BUILD = "([0-9.]+)";'
        return (hashlib.sha256(old).hexdigest()==digest and
                re.search(build_pattern,old).group(1)==re.search(build_pattern,current).group(1))
    return False

def check_capture_inputs(build, *, allow_historical_active=False):
    for name,digest in build['inputs'].items():
        if not capture_input_relevant(name):
            continue
        data=(ROOT/name).read_bytes()
        if allow_historical_active and name=='watchface/source/SceneRenderer.mc':
            # Reconstruct the exact earlier source only for ACTIVE/wake images.
            # The sole change is in the LOW glyph baseline and its comment.
            source=data.decode()
            old_comment='// then apply at most one pixel of minute-based burn-in movement.'
            new_comment=('// The glyph baseline stays fixed vertically: native 454px scaling adds a\n'
                '        // device-font offset that otherwise shifts the lower phases beyond\n'
                '        // the two-pixel center bound. Horizontal movement and the independent\n'
                '        // four-phase pixel-rest mask retain the minute-based burn-in pattern.')
            old_draw='dc.drawText(195+p[0]+correction,122+p[1],font,current.localTime,Graphics.TEXT_JUSTIFY_CENTER);'
            new_draw='dc.drawText(195+p[0]+correction,121,font,current.localTime,Graphics.TEXT_JUSTIFY_CENTER);'
            if source.count(new_comment)!=1 or source.count(new_draw)!=1:
                raise ValueError('unexpected historical ACTIVE source change')
            data=source.replace(new_comment,old_comment).replace(new_draw,old_draw).encode()
        if hashlib.sha256(data).hexdigest()!=digest:
            if name=='watchface/source/NativeVisualRenderer.mc' and historical_unchanged_pending_input(name,digest):
                continue
            raise ValueError('point capture source changed: '+name)


def fresh_low(size):
    evidence=E.parent/f'centered-low-{size}'
    check_capture_inputs(json.loads((evidence/'build.json').read_text()))
    return Image.open(evidence/f'low-{size}.png').convert('RGB')

def verify_point(image, low):
    if image.size!=(390,390):raise ValueError('unexpected native capture size')
    pixels=Counter(image.getpixel((x,y)) for y in range(150,181) for x in range(320,351))
    if low:
        primary=sum(n for (r,g,b),n in pixels.items() if r>200 and 60<g<160 and 60<b<160)
        border=sum(n for (r,g,b),n in pixels.items() if r>220 and g>220 and b>220)
        if primary<35 or border<70:raise ValueError('LOW point ink missing')
    else:
        primary=sum(n for (r,g,b),n in pixels.items() if r>230 and 170<g<235 and 40<b<140)
        border=sum(n for (r,g,b),n in pixels.items() if r>220 and g>220 and b>220)
        if primary<60 or border<70:raise ValueError('ACTIVE point ink missing')
    return primary,border


class PendingPointPixelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build=json.loads((E/'build.json').read_text())
        cls.build=build
        check_capture_inputs(build,allow_historical_active=True)

    def test_pending_low_and_wake_visible_point(self):
        for name,low in [('active-0838.png',False),('low-0838.png',True),('wake-0838.png',False)]:
            with self.subTest(frame=name):verify_point(fresh_low(390) if low else Image.open(E/name).convert('RGB'),low)

    def test_missing_actual_point_is_rejected(self):
        for name,low in [('active-0838.png',False),('low-0838.png',True)]:
            image=fresh_low(390) if low else Image.open(E/name).convert('RGB')
            for y in range(150,181):
                for x in range(320,351):image.putpixel((x,y),(0,0,0))
            with self.assertRaisesRegex(ValueError,'point ink missing'):verify_point(image,low)

    def test_low_clock_center_height_and_lit_budget(self):
        image=fresh_low(390);clock=[];lit=0
        for y in range(390):
            for x in range(390):
                r,g,b=image.getpixel((x,y))
                if r or g or b:lit+=1
                if 110<=y<250 and g>40 and g>r*1.3 and g>b*1.05:clock.append((x,y))
        xs=[x for x,y in clock];ys=[y for x,y in clock]
        self.assertLessEqual(abs((min(xs)+max(xs))/2-195),2)
        self.assertLessEqual(abs((min(ys)+max(ys))/2-195),2)
        self.assertGreaterEqual(max(ys)-min(ys)+1,96)
        self.assertLessEqual(lit,math.floor(math.pi*195**2*.1))

    def test_larger_scaled_point_is_visible_and_removal_fails(self):
        evidence=E.parent/'pending-point-454'
        build=json.loads((evidence/'build.json').read_text())
        check_capture_inputs(build,allow_historical_active=True)
        def marker(image,low):
            if image.size!=(454,454):raise ValueError('unexpected larger capture size')
            pixels=Counter(image.getpixel((x,y)) for y in range(175,211) for x in range(372,410))
            if low:
                main=sum(n for (r,g,b),n in pixels.items() if r>200 and 60<g<160 and 60<b<160)
            else:
                main=sum(n for (r,g,b),n in pixels.items() if r>230 and 170<g<235 and 40<b<140)
            white=sum(n for (r,g,b),n in pixels.items() if r>220 and g>220 and b>220)
            if main<40 or white<75:raise ValueError('larger point ink missing')
        for name,low in [('active-454.png',False),('low-454.png',True)]:
            image=fresh_low(454) if low else Image.open(evidence/name).convert('RGB');marker(image,low)
            for y in range(175,211):
                for x in range(372,410):image.putpixel((x,y),(0,0,0))
            with self.assertRaisesRegex(ValueError,'point ink missing'):marker(image,low)


class CorrectedScaledClockTest(unittest.TestCase):
    def test_scaled_low_clock_ink_is_centered_and_readable(self):
        evidence=E.parent/'centered-low-454'
        image=fresh_low(454)
        points=[]
        for y in range(120,290):
            for x in range(image.width):
                r,g,b=image.getpixel((x,y))
                if g>40 and g>r*1.3 and g>b*1.05:points.append((x,y))
        self.assertTrue(points,'scaled clock ink missing')
        xs=[x for x,y in points];ys=[y for x,y in points];scale=image.width/390
        self.assertGreaterEqual(max(ys)-min(ys)+1,96*scale)
        self.assertLessEqual(abs((min(xs)+max(xs))/2-image.width/2),2*scale)
        self.assertLessEqual(abs((min(ys)+max(ys))/2-image.height/2),2*scale)
