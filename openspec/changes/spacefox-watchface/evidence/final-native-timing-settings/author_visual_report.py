"""Read actual SDK exports/draw logs; no host countdown implementation.

Run with existing Python3.12/Pillow for artifact authoring. Portable validation
rechecks the serialized pixel OCR and unknown-marker connected components.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT))
from tests.test_basic_time_fields import geometry
from tools.native_timing_settings import STATES,EXPECTED
E=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def components(im):
 mask={(x,y) for y in range(202,235) for x in range(58,333)
       if (lambda c:c[0]>150 and c[1]>110 and c[2]<170)(im.getpixel((x,y))[:3])}
 groups=[]
 while mask:
  start=mask.pop();todo=[start];group=[start]
  while todo:
   x,y=todo.pop()
   for nxt in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
    if nxt in mask:mask.remove(nxt);todo.append(nxt);group.append(nxt)
  groups.append([min(x for x,y in group),min(y for x,y in group),max(x for x,y in group)+1,max(y for x,y in group)+1,len(group)])
 return sorted(groups)

def main():
 frames=E/'frames';raw=(E/'observer/run.log').read_text();rows={}
 for line in raw.splitlines():
  if not line.startswith('FINAL_TEXT|'):continue
  _,label,kind,x,y,width,height,color,text=line.split('|',8)
  rows.setdefault(label,[]).append(dict(kind=kind,x=float(x),y=float(y),width=float(width),height=float(height),color=int(color),text=text))
 proofs=[];pictures=[]
 for lang in ('en','ru'):
  for state in STATES:
   label=lang+'-'+state;source=frames/('held-'+label+'.png');im=Image.open(source).convert('RGB');assert im.size==(390,390)
   texts=rows[label];assert len(texts)==12
   basic='\n'.join('BASIC_TEXT|'+r['kind']+'|'+str(r['x'])+'|'+str(r['y'])+'|'+str(r['width'])+'|'+str(r['height'])+'|'+r['text'] for r in texts)
   boxes=geometry(basic)
   for r,b in zip(texts,boxes):
    r['conservativeBox']=b['box']
    for x in (b['box'][0],b['box'][2]):
     for y in (b['box'][1],b['box'][3]):assert (x-195)**2+(y-195)**2<=195**2,(label,r)
    left=max(0,int(r['x']-r['width']/2)-1);right=min(390,int(r['x']+r['width']/2)+2);top=int(r['y']);bottom=min(390,int(r['y']+r['height']))
    counter=Counter(im.crop((left,top,right,bottom)).getdata());wanted=tuple((r['color']>>shift)&255 for shift in (16,8,0))
    selected=min(counter,key=lambda c:sum((a-b)**2 for a,b in zip(c,wanted)))
    assert sum((a-b)**2 for a,b in zip(selected,wanted))<900,(label,r,selected)
    points=[(x,y) for y in range(top,bottom) for x in range(left,right) if im.getpixel((x,y))==selected]
    r['sdkQuantizedFillRgb']=selected;r['matchingColorPixelsWithinRoiBounds']=[min(x for x,y in points),min(y for x,y in points),max(x for x,y in points)+1,max(y for x,y in points)+1]
   for i,r in enumerate(texts):
    a=r['conservativeBox']
    for other in texts[i+1:]:
     b=other['conservativeBox'];assert not(a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]),(label,r,other)
   countdown=next(r for r in texts if r['y']==202);clock=next(r for r in texts if r['kind']=='time');assert countdown['text']==EXPECTED[state]
   expected_color=0xF3C37A if state in ('reschedule','unknown') else 0xCDB7FF if state=='appearance' else 0x7FE7C6
   assert countdown['color']==expected_color;assert clock['color']==(0x9AD5FF if state=='appearance' else 0x7FE7C6)
   dots=[(x,y) for y in range(235,240) for x in range(58,333) if max(im.getpixel((x,y)))>140]
   assert bool(dots)==(state in ('unknown','stale')),(label,len(dots))
   proof=dict(label=label,file=str(source.relative_to(E)),pngSha256=sha(source),texts=texts,underlineBrightPixels=len(dots),status='passed')
   if state=='unknown':
    groups=components(im);assert sum(g[2]-g[0]==7 and g[3]-g[1]==2 for g in groups)==6
    assert sum(g[2]-g[0]==3 and g[3]-g[1]==3 for g in groups)==4
    proof['unknownComponents']=groups;proof['manualPixelReadback']='--:--:--';proof['manualBoundary']='Exact six distinct horizontal dash strokes and four colon dots in actual native pixels; OCR yielded no text, no digit corrections applied.'
   proofs.append(proof);pictures.append((label,im))
 sheet=Image.new('RGB',(5*410,4*435),(18,22,30));draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
 for i,(label,im) in enumerate(pictures):
  x=(i%5)*410+10;y=(i//5)*435+34;sheet.paste(im,(x,y));draw.text((x,y-28),label,font=font,fill=(245,245,250))
 sheet.save(E/'contact-sheet.png')
 result=dict(status='passed',frameCount=20,geometryBoundary='All actual SDK draw widths/heights and retained bitmap glyph ink boxes fit circle and do not overlap. Matching-color pixel bounds are measured within each text ROI and may include other text of the same color; they are not isolated glyph ink bounds. Palette quantization reads actual exported PNGs and does not claim all antialiased ink or a physical panel. 1px black contour follows unchanged source draw loop and visual review.',frames=proofs)
 (E/'visual-report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 print('20 frames geometry/colors/independent dot state passed')
if __name__=='__main__':main()
