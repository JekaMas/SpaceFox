"""Read actual simulator PNG controls, including the retained red frame."""
import struct
import unittest
import zlib
from pathlib import Path

E = Path(__file__).resolve().parents[1]/'openspec/changes/spacefox-watchface/evidence/devices020/stock'


def pixels(path):
    data=path.read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n': raise ValueError('not PNG')
    pos=8;compressed=bytearray();width=height=None
    while pos<len(data):
        size=struct.unpack_from('>I',data,pos)[0];kind=data[pos+4:pos+8];body=data[pos+8:pos+8+size]
        if zlib.crc32(kind+body)&0xffffffff != struct.unpack_from('>I',data,pos+8+size)[0]:raise ValueError('PNG CRC')
        if kind==b'IHDR':
            width,height,depth,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',body)
            if (width,height,depth,color,compression,filtering,interlace)!=(448,486,8,2,0,0,0):raise ValueError('unexpected image format')
        elif kind==b'IDAT':compressed.extend(body)
        elif kind==b'IEND':break
        pos+=size+12
    raw=zlib.decompress(compressed);stride=width*3;prev=bytearray(stride);rows=[];at=0
    for _ in range(height):
        mode=raw[at];at+=1;cur=bytearray(raw[at:at+stride]);at+=stride
        for x in range(stride):
            a=cur[x-3] if x>=3 else 0;b=prev[x];c=prev[x-3] if x>=3 else 0
            if mode==0:f=0
            elif mode==1:f=a
            elif mode==2:f=b
            elif mode==3:f=(a+b)//2
            elif mode==4:
                p=a+b-c;pa=abs(p-a);pb=abs(p-b);pc=abs(p-c);f=a if pa<=pb and pa<=pc else b if pb<=pc else c
            else:raise ValueError('PNG filter')
            cur[x]=(cur[x]+f)&255
        rows.append(cur);prev=cur
    return lambda x,y:tuple(rows[y][x*3:x*3+3])


class RectanglePixelTest(unittest.TestCase):
    def test_green_frames_have_black_letterbox(self):
        for name in ('venux1-en-active-green.png','venux1-en-low-green.png','venux1-ru-active-green.png','venux1-ru-low-green.png'):
            with self.subTest(name=name):
                p=pixels(E/name);self.assertEqual(p(224,4),(0,0,0));self.assertEqual(p(224,481),(0,0,0))

    def test_original_red_has_white_letterbox(self):
        p=pixels(E/'venux1-white-margins-red.png')
        self.assertEqual(p(224,4),(255,250,255));self.assertEqual(p(224,481),(255,250,255))


if __name__ == '__main__':unittest.main()
