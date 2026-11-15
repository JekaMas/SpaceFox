"""Read TTF cmap/hmtx for the two version digits; no SDK execution."""
import hashlib
import json
import struct
import sys
from pathlib import Path

p=Path(sys.argv[1]);data=p.read_bytes();u16=lambda o:struct.unpack_from('>H',data,o)[0];u32=lambda o:struct.unpack_from('>I',data,o)[0]
tables={}
for i in range(u16(4)):
 off=12+16*i;tag=data[off:off+4].decode('ascii');tables[tag]=(u32(off+8),u32(off+12))
cmap=tables['cmap'][0]; offsets=[]
for i in range(u16(cmap+2)):
 r=cmap+4+8*i;platform=u16(r);encoding=u16(r+2);off=cmap+u32(r+4)
 if u16(off)==4 and platform in (0,3):offsets.append((platform==3 and encoding==1,off))
if not offsets:raise ValueError('no Unicode BMP format 4 cmap')
base=max(offsets)[1];count=u16(base+6)//2;end=base+14;start=end+2*count+2;delta=start+2*count;rangeoff=delta+2*count

def glyph(code):
 for i in range(count):
  if u16(start+2*i)<=code<=u16(end+2*i):
   d=u16(delta+2*i);r=u16(rangeoff+2*i)
   if r==0:return (code+d)&0xffff
   at=rangeoff+2*i+r+2*(code-u16(start+2*i));g=u16(at)
   return (g+d)&0xffff if g else 0
 raise ValueError('glyph absent')
num=u16(tables['hhea'][0]+34);hmtx=tables['hmtx'][0]; advances={}
for char in '34':
 g=glyph(ord(char));assert g;advances[char]=u16(hmtx+4*min(g,num-1))
print(json.dumps({'font':'Roboto-Regular.ttf','sha256':hashlib.sha256(data).hexdigest(),'unitsPerEm':u16(tables['head'][0]+18),'glyphAdvance':advances,'boundary':'TTF horizontal advance only; no physical or new native header image.'},indent=2))
