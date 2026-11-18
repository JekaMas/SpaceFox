"""Compare only the simulator rocket region; inputs are X11 RGB8 screenshots."""
from pathlib import Path
import struct, sys, zlib


def crop(path):
    data=Path(path).read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':raise ValueError('PNG signature')
    at=8; pieces=[]; size=None
    while at<len(data):
        n=struct.unpack_from('>I',data,at)[0]; kind=data[at+4:at+8]; body=data[at+8:at+8+n]
        if zlib.crc32(kind+body)&0xffffffff != struct.unpack_from('>I',data,at+8+n)[0]:raise ValueError('PNG CRC')
        if kind==b'IHDR':size=struct.unpack('>IIBBBBB',body)
        if kind==b'IDAT':pieces.append(body)
        at+=12+n
        if kind==b'IEND':break
    if size!=(1024,768,8,2,0,0,0):raise ValueError('unexpected screenshot format')
    raw=zlib.decompress(b''.join(pieces));stride=1+1024*3
    if len(raw)!=768*stride:raise ValueError('unexpected screenshot length')
    result=[]
    for y in range(420,485):
        row=raw[y*stride:(y+1)*stride]
        if row[0]!=0:raise ValueError('unexpected screenshot filter')
        for x in range(133,139):result.append(row[1+3*x:1+3*x+3])
    return result

frames=[crop(p) for p in sys.argv[1:]]
if len(frames)!=3:raise ValueError('three screenshots required')
for a,b in ((0,1),(1,2),(0,2)):
    count=sum(x!=y for x,y in zip(frames[a],frames[b]))
    print(f'{86+a} vs {86+b}: changed RGB pixels in rocket crop = {count}')
    if count==0:raise AssertionError('remote change not visible in rocket region')
