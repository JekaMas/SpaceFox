"""Source-bound image study and byte-preserving producer optimization checks."""
import itertools
import json
from pathlib import Path
import subprocess
import struct
import zlib
import sys
import tempfile
import unittest

from tools import image_pipeline_research as study
from tools.spacefox import native_profile as native
from tests.test_sfr1m_offline_current import literal_decode


def original_row(row, previous, channels):
    """Frozen pre-change byte-slice implementation, checked against real rows."""
    width=len(row)//channels; x=0; out=bytearray()
    while x<width:
        copy=0
        while copy<128 and x+copy<width and row[(x+copy)*channels:(x+copy+1)*channels]==previous[(x+copy)*channels:(x+copy+1)*channels]: copy+=1
        run=1; color=row[x*channels:(x+1)*channels]
        while run<128 and x+run<width and row[(x+run)*channels:(x+run+1)*channels]==color: run+=1
        if copy and copy*4>=run: out.append(127+copy);x+=copy
        else: out.append(run-1);out.extend(color);x+=run
    return bytes(out)


def exhaustive_cost(a,b,c,x=0):
    if x==len(a):return (0,0)
    candidates=[]
    for n in range(1,len(a)-x+1):
        if all(p==a[x] for p in a[x:x+n]):
            z=exhaustive_cost(a,b,c,x+n);candidates.append((z[0]+1+c,z[1]+1))
        if a[x:x+n]==b[x:x+n]:
            z=exhaustive_cost(a,b,c,x+n);candidates.append((z[0]+1,z[1]+1))
    return min(candidates)


class ImagePipelineTest(unittest.TestCase):
    def test_corpus_positive(self):
        assets=[study.load(x) for x in study.inventory()]
        self.assertTrue({'current-map','current-rocket','current-flag'} <= {a['name'] for a in assets})
        self.assertEqual({'map','low','rocket','flag'}, {a['kind'] for a in assets})
        for a in assets:
            w=a['width'];h=a['height'];c=a['channels'];raw=a['pixels'];previous=bytes(w*c)
            for y in range(h):
                row=raw[y*w*c:(y+1)*w*c]
                self.assertEqual(native._row_tokens(row,previous,c), original_row(row,previous,c),a['name'])
                previous=row

    def test_corpus_negative(self):
        name,kind,split,path,w,h,c=study.CORPUS[0]
        with self.assertRaisesRegex(ValueError,'pixel length'):
            study.load((name,kind,split,path,w-1,h,c))
        with self.assertRaises((FileNotFoundError,ValueError)):
            study.load((name,kind,split,'missing.png',w,h,c))

    def test_invalid_positive(self):
        source=study.ROOT/'watchface/resources/drawables/art_flag-us.png'
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable,'-B',str(study.ROOT/'tools/image_pipeline_research.py'),'--pack-png',str(source),'--output',tmp],check=True)
            manifest=json.loads((Path(tmp)/'manifest.json').read_text())
            chunks=[(Path(tmp)/(r['sha256']+'.sfr')).read_bytes() for r in manifest['shards']]
            w,h,raw=native.png_pixels(source.read_bytes())
            self.assertEqual(literal_decode(chunks,w,h,4),raw)
            self.assertEqual(native.decode_raster(chunks,w,h,4),raw)
            self.assertEqual(manifest['pixel_sha256'],study.digest(raw))

    def test_invalid_negative(self):
        with self.assertRaises(ValueError):native.png_pixels(b'bad')
        with self.assertRaises(ValueError):study.pack(b'abc',2,2,3)
        source=study.ROOT/'watchface/resources/drawables/art_falcon-9.png'
        with tempfile.TemporaryDirectory() as tmp:
            result=subprocess.run([sys.executable,'-B',str(study.ROOT/'tools/image_pipeline_research.py'),'--pack-png',str(source),'--channels','3','--output',tmp],capture_output=True)
            self.assertNotEqual(result.returncode,0)
            self.assertFalse((Path(tmp)/'manifest.json').exists())
            # A prior successful output remains authoritative on bad input.
            manifest=Path(tmp)/'manifest.json'; manifest.write_bytes(b'prior manifest')
            original=(study.ROOT/'watchface/resources/drawables/art_flag-us.png').read_bytes()
            def chunk(kind, body):
                return struct.pack('>I',len(body))+kind+body+struct.pack('>I',zlib.crc32(kind+body)&0xffffffff)
            # Missing IEND, CRC corruption, truncated chunk, illegal tRNS and trailing bytes.
            ihdr_end=8+12+13
            rgb=(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))
                 +chunk(b'tRNS',b'\x00'*6)+chunk(b'IDAT',zlib.compress(b'\x00\x00\x00\x00'))+chunk(b'IEND',b''))
            # Optional suggested RGB palette is legal and must remain accepted.
            rgb_palette=(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,2,0,0,0))
                         +chunk(b'PLTE',b'\x00\x00\x00')+chunk(b'IDAT',zlib.compress(b'\x00\x00\x00\x00'))+chunk(b'IEND',b''))
            valid=Path(tmp)/'palette.png'; valid.write_bytes(rgb_palette)
            self.assertEqual(study.read_png(valid)[1],(1,1,b'\x00\x00\x00\xff'))
            cases=(rgb, original[:-12], original[:29]+bytes([original[29]^1])+original[30:],
                   original[:-1], original[:ihdr_end]+chunk(b'tRNS',b'\x00'*6)+original[ihdr_end:],
                   original+b'extra')
            for i, bad in enumerate(cases):
                path=Path(tmp)/f'bad-{i}.png';path.write_bytes(bad)
                result=subprocess.run([sys.executable,'-B',str(study.ROOT/'tools/image_pipeline_research.py'),'--pack-png',str(path),'--output',tmp],capture_output=True)
                self.assertNotEqual(result.returncode,0, i)
                self.assertEqual(manifest.read_bytes(),b'prior manifest')

    def test_lossless_positive(self):
        for record in study.CORPUS[:3]:
            a=study.load(record);w=a['width'];h=a['height'];c=a['channels'];px=a['pixels']
            chunks=native.encode_raster(px,w,h,c)
            self.assertEqual(chunks,study.pack(px,w,h,c))
            self.assertEqual(literal_decode(chunks,w,h,c),px)
        # Boundaries cover short alternatives and the 128-pixel token cap.
        for n in range(1,6):
            for left in itertools.product(range(2),repeat=n):
                for above in itertools.product(range(2),repeat=n):
                    for channels in (3,4):
                        row=b''.join(bytes([v])*channels for v in left)
                        previous=b''.join(bytes([v])*channels for v in above)
                        self.assertEqual(native._row_tokens(row,previous,channels),original_row(row,previous,channels))
        for n in (127,128,129,256,257,390):
            row=b''.join(bytes([0 if i<n//2 else 255])*3 for i in range(n))
            previous=b''.join(bytes([0 if i%3 else 255])*3 for i in range(n))
            self.assertEqual(native._row_tokens(row,previous,3),original_row(row,previous,3))
        # Known QOI stream vectors anchor the independent parser beyond round trips.
        self.assertEqual(study.qoi_encode(bytes([255,0,0,255]),4),bytes([254,255,0,0]))
        self.assertEqual(study.qoi_decode(bytes([254,255,0,0]),1,4),bytes([255,0,0,255]))
        # Exhaustive oracle is deliberately separate from the DP implementation.
        for n in range(1,5):
            for left in itertools.product(range(2),repeat=n):
                for above in itertools.product(range(2),repeat=n):
                    row=b''.join(bytes([v])*3 for v in left);previous=b''.join(bytes([v])*3 for v in above)
                    tokens=study.optimal_row(row,previous,3);i=0;count=0
                    while i<len(tokens):
                        t=tokens[i];i+=1 if t&128 else 4;count+=1
                    self.assertEqual((len(tokens),count),exhaustive_cost(left,above,3))

    def test_lossless_negative(self):
        a=study.load(study.CORPUS[1]);chunks=native.encode_raster(a['pixels'],a['width'],a['height'],4)
        self.assertNotEqual(study.digest(a['pixels']),study.digest(a['pixels'][:-1]+bytes([a['pixels'][-1]^1])))
        with self.assertRaises(ValueError):literal_decode(chunks[:-1],a['width'],a['height'],4)
        with self.assertRaises(ValueError):study.qoi_decode(bytes([254,255]),1,4)


if __name__=='__main__':unittest.main()
