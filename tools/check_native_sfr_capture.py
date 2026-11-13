#!/usr/bin/env python3
"""Compare an actual390 SDK map capture with the frozen independent map PNG.

The explicit mask removes text/art/marker and the outer2px round boundary.
This proves the remaining pixels only; it is not a whole-composition oracle.
Pillow is an independent observation dependency, never a producer dependency.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

MASK=((321,151,349,179),(21,117,77,249),(170,21,243,41),
      (49,40,341,91),(60,113,325,202),(47,200,344,240),
      (49,239,344,317),(70,317,320,349))

def compare(capture,expected):
    actual=Image.open(capture).convert('RGB');source=Image.open(expected).convert('RGB')
    if actual.size!=(390,390) or source.size!=(390,390):raise ValueError('exact390x390 images required')
    checked=0;different=0;first=[]
    for y in range(390):
        for x in range(390):
            if (x-195)**2+(y-195)**2>193**2:continue
            if any(a<=x<c and b<=y<d for a,b,c,d in MASK):continue
            r,g,b=source.getpixel((x,y));want=((r>>3)*255//31,(g>>2)*255//63,(b>>3)*255//31)
            got=actual.getpixel((x,y));checked+=1
            if got!=want:
                different+=1
                if len(first)<20:first.append(dict(x=x,y=y,expected=want,actual=got))
    return dict(schemaVersion=1,capture=str(capture),captureSha256=hashlib.sha256(capture.read_bytes()).hexdigest(),expected=str(expected),expectedSha256=hashlib.sha256(expected.read_bytes()).hexdigest(),checkedPixels=checked,differences=different,firstDifferences=first,excludedRectangles=MASK,outerRadius=193,projection='RGB565 truncate/expand floor: (r>>3)*255//31,(g>>2)*255//63,(b>>3)*255//31',scope='Only unobscured map pixels; independent frozen source PNG, not producer decoder or full image equality.')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--capture',type=Path,required=True);p.add_argument('--expected',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();r=compare(a.capture,a.expected);a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ('checkedPixels','differences')}));raise SystemExit(0 if r['differences']==0 and r['checkedPixels']==30754 else 1)
