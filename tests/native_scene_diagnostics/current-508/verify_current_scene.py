#!/usr/bin/env python3
"""Check fixed unobscured selected-map and opaque-role pixels in an SDK capture."""
import argparse
import gzip
import hashlib
from pathlib import Path

PINS = {'map':'b166d43ce4b6b0bb659656eb3b98bf62683c7fbb5443c3bfaba1f543c2537ccd',
        'rocket':'15395365f81866ada8f35c360baa648fb7621b9a0e15052c2dfe5562ae8eacba',
        'siteCountry':'c8b74ae2cd882dfb43d120675b2c3cca57e8d69584f9ab902ba1b6d1c63f1fa9'}

def check(image, refs):
    def pixel(x, y):
        i=((y+256)*1200+x+87)*3
        return image[i:i+3]
    def within(a, b):
        return max(abs(a[k]-b[k]) for k in range(3))<=8
    count=0
    for y in range(78,105):
        for x in range(270,365):
            if (x-195)**2+(y-195)**2>194**2:continue
            i=(y*390+x)*3
            if not within(pixel(x,y),refs['map'][i:i+3]):return False
            count+=1
    if count!=2400:return False
    for role,w,h,x0,y0 in [('rocket',54,124,22,118),('siteCountry',20,12,118,325)]:
        ref=refs[role];n=0
        for y in range(h):
            for x in range(w):
                i=(y*w+x)*4
                if ref[i+3]!=255:continue
                if not within(pixel(x0+x,y0+y),ref[i:i+3]):return False
                n+=1
        if n!=({'rocket':542,'siteCountry':200}[role]):return False
    marker=pixel(335,165)
    return marker[0]>220 and marker[1]>170 and marker[2]<160

def main():
    p=argparse.ArgumentParser();p.add_argument('--public-root',required=True,type=Path);p.add_argument('--ppm',required=True,type=Path);a=p.parse_args()
    raw=a.ppm.read_bytes();raw=gzip.decompress(raw) if a.ppm.suffix=='.gz' else raw;head=raw.split(b'\n',3)
    assert head[:3]==[b'P6',b'1200 1200',b'255'] and len(head[3])==1200*1200*3
    refs={}
    for name,digest in PINS.items():
        value=gzip.decompress((a.public_root/'tests/fixtures/sfr1m-current'/f'{name}.rgba.gz').read_bytes())
        assert hashlib.sha256(value).hexdigest()==digest
        refs[name]=value
    assert check(head[3],refs),'current selected scene pixels differ'
    bad=bytearray(head[3]);i=((90+256)*1200+300+87)*3;bad[i]=255-bad[i]
    assert not check(bad,refs),'map pixel corruption escaped'
    print('PASS selected SDK scene: 2400 unobscured map pixels, 542 rocket pixels, 200 flag pixels, marker center; map corruption refused; not whole-map or independent-art proof')

if __name__=='__main__':main()
