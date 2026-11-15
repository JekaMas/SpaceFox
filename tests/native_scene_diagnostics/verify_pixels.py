#!/usr/bin/env python3
"""Bounded native screenshot vs independent frozen raw selected SFR1M pixels."""
import argparse,gzip,hashlib,json,struct,zlib
from pathlib import Path
HERE=Path(__file__).resolve().parent
PINS={"map":"b166d43ce4b6b0bb659656eb3b98bf62683c7fbb5443c3bfaba1f543c2537ccd","rocket":"15395365f81866ada8f35c360baa648fb7621b9a0e15052c2dfe5562ae8eacba","siteCountry":"c8b74ae2cd882dfb43d120675b2c3cca57e8d69584f9ab902ba1b6d1c63f1fa9"}

def png_rgb(path):
 data=path.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';pos=8;parts=[];w=h=None
 while pos<len(data):
  size=struct.unpack_from('>I',data,pos)[0];kind=data[pos+4:pos+8];body=data[pos+8:pos+8+size];pos+=12+size
  if kind==b'IHDR':w,h,depth,color,comp,filt,interlace=struct.unpack('>IIBBBBB',body);assert (depth,color,comp,filt,interlace)==(8,2,0,0,0)
  elif kind==b'IDAT':parts.append(body)
  elif kind==b'IEND':break
 packed=zlib.decompress(b''.join(parts));stride=w*3;out=bytearray(w*h*3);prev=bytearray(stride)
 for y in range(h):
  row=bytearray(packed[y*(stride+1)+1:(y+1)*(stride+1)]);ft=packed[y*(stride+1)]
  for x in range(stride):
   left=row[x-3] if x>=3 else 0;up=prev[x];ul=prev[x-3] if x>=3 else 0
   if ft==1:v=left
   elif ft==2:v=up
   elif ft==3:v=(left+up)//2
   elif ft==4:
    p=left+up-ul;pa=abs(p-left);pb=abs(p-up);pc=abs(p-ul);v=left if pa<=pb and pa<=pc else up if pb<=pc else ul
   else:assert ft==0;v=0
   row[x]=(row[x]+v)&255
  out[y*stride:(y+1)*stride]=row;prev=row
 return w,h,bytes(out)

def evaluate(w,h,img,public):
 assert (w,h)==(1200,1200);ox,oy=87,256
 def rgb(x,y):return img[((oy+y)*w+ox+x)*3:((oy+y)*w+ox+x)*3+3]
 def frozen(role):
  raw=gzip.decompress((public/'tests/fixtures/sfr1m-current'/f'{role}.rgba.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()==PINS[role];return raw
 # Scene coordinates are fixed by the renderer; only fully opaque pixels are
 # compared, avoiding alpha-blending assumptions. 8 covers RGB565 quantization.
 metrics={}
 for role,ww,hh,x0,y0 in [('rocket',54,124,22,118),('siteCountry',20,12,118,325)]:
  ref=frozen(role);n=matched=0
  for y in range(hh):
   for x in range(ww):
    i=(y*ww+x)*4
    if ref[i+3]!=255:continue
    target=rgb(x0+x,y0+y);n+=1;matched+=max(abs(ref[i+k]-target[k]) for k in range(3))<=8
  metrics[role]=(matched,n)
  if matched!=n or n<100:return False,metrics
 ref=frozen('map');n=matched=0
 # Composed map ROI is reported only; foreground ink overlaps these pixels.
 for y in range(45,115):
  for x in range(250,345):
   i=(y*390+x)*3
   if max(ref[i:i+3])<20:continue
   target=rgb(x,y);n+=1;matched+=max(abs(ref[i+k]-target[k]) for k in range(3))<=8
 metrics['map']=(matched,n)
 # The actual selected site marker has its yellow center at literal 335,165.
 marker=rgb(335,165);metrics['marker']=list(marker)
 return marker[0]>220 and marker[1]>170 and marker[2]<160,metrics

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--public-root',type=Path,required=True);parser.add_argument('--scene',type=Path,required=True);parser.add_argument('--map',type=Path,required=True);parser.add_argument('--new-captures',action='store_true',help='compare a fresh capture without asserting historical screenshot hashes');args=parser.parse_args();public=args.public_root
 feed=json.loads((HERE/'profile-a/feed.json').read_bytes());scene=json.loads((HERE/'profile-a'/feed['visualSelection']['path']).read_bytes());assert feed['launch']['launch_id']=='ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b' and scene['marker']['anchor']==[335,165]
 for role in PINS:
  desc=json.loads((HERE/'profile-a'/scene['roles'][role]['descriptor']['path']).read_bytes());assert desc['pixelSha256']==PINS[role]
 path=args.scene
 if not args.new_captures:assert hashlib.sha256(path.read_bytes()).hexdigest()=='e5a31d4798bdffce14947c9d68f3774aafaa8a914adc29e0d56e60c35b9eac14'
 w,h,img=png_rgb(path);ok,metrics=evaluate(w,h,img,public);assert ok,metrics
 # The role-only capture has no clock, labels, marker or foreground overlays.
 # Radius 194 excludes the outermost device bezel/antialias ring on the 390px circle.
 map_path=args.map
 if not args.new_captures:assert hashlib.sha256(map_path.read_bytes()).hexdigest()=='eed9f56223bca3fadb6e0fc887c40e021b3397be08dad5e62d1f42d0bf0869a9'
 mw,mh,map_img=png_rgb(map_path);assert (mw,mh)==(1200,1200);raw=gzip.decompress((public/'tests/fixtures/sfr1m-current/map.rgba.gz').read_bytes());assert hashlib.sha256(raw).hexdigest()==PINS['map'];count=0;worst=0
 def map_check(pixels):
  count=0;worst=0
  for y in range(390):
   for x in range(390):
    if (x-195)**2+(y-195)**2>194**2:continue
    i=(y*390+x)*3;j=((256+y)*mw+87+x)*3;err=max(abs(raw[i+k]-pixels[j+k]) for k in range(3));count+=1;worst=max(worst,err)
    if err>8:return False,count,worst
  return True,count,worst
 ok,count,worst=map_check(map_img);assert ok and count==118213;metrics['mapRoleOnly']={'matched':count,'total':count,'maxChannelDifference':worst,'radius':194}
 altered=bytearray(map_img);offset=((256+195)*mw+87+195)*3;altered[offset]=255-raw[(195*390+195)*3];assert not map_check(altered)[0]
 # A blank/corrupt capture must not be admitted by the same comparison.
 bad,_=evaluate(w,h,bytes(len(img)),public);assert not bad
 print(json.dumps({'captureSha256':hashlib.sha256(path.read_bytes()).hexdigest(),'origin':[87,256],'metrics':metrics,'blankNegativeRejected':True,'boundary':'SDK screenshot vs literal frozen renderer reference; not physical or independent art accuracy'},sort_keys=True))
if __name__=='__main__':main()
