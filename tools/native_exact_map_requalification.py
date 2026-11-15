"""Source-bound DISPLAY03 full-map delta; reconstruct the previous proof."""
import hashlib,json,shutil,struct,tempfile,zlib
from pathlib import Path

def png(raw):
 if raw[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError('PNG signature')
 at=8;data=bytearray();w=h=None
 while at<len(raw):
  n=struct.unpack('>I',raw[at:at+4])[0];k=raw[at+4:at+8];b=raw[at+8:at+8+n]
  if zlib.crc32(k+b)&0xffffffff!=struct.unpack('>I',raw[at+8+n:at+12+n])[0]:raise ValueError('PNG CRC')
  if k==b'IHDR':
   w,h,depth,color,c,f,i=struct.unpack('>IIBBBBB',b)
   if w>454 or h>454 or depth!=8 or color not in (2,6) or (c,f,i)!=(0,0,0):raise ValueError('PNG format')
   channels=3 if color==2 else 4
  elif k==b'IDAT':data.extend(b)
  elif k==b'IEND':break
  at+=n+12
 if w is None or len(data)>1048576:raise ValueError('PNG bound')
 stride=w*channels;z=zlib.decompressobj();scan=z.decompress(data,(stride+1)*h+1)
 if not z.eof or z.unconsumed_tail or len(scan)!=(stride+1)*h:raise ValueError('PNG inflate')
 pixels=[];previous=bytearray(stride)
 for y in range(h):
  mode=scan[y*(stride+1)];row=bytearray(scan[y*(stride+1)+1:(y+1)*(stride+1)])
  if mode>4:raise ValueError('PNG filter')
  for x in range(stride):
   a=row[x-channels] if x>=channels else 0;b=previous[x];c=previous[x-channels] if x>=channels else 0
   if mode==1:d=a
   elif mode==2:d=b
   elif mode==3:d=(a+b)//2
   elif mode==4:
    t=a+b-c;pa=abs(t-a);pb=abs(t-b);pc=abs(t-c);d=a if pa<=pb and pa<=pc else b if pb<=pc else c
   else:d=0
   row[x]=(row[x]+d)&255
  pixels.extend(tuple(row[x:x+3]) for x in range(0,stride,channels));previous=row
 return w,h,pixels

def validate(root,catalog):
 from tools.native_display03_probe import inputs
 from tools.native_low_map_requalification import validate as previous
 from tools.generate_native_version import validate as validate_version
 from tools.run_native_tests import parse_output
 root=Path(root).resolve();proof=catalog['supportPolicy']['softwareQualificationProof']
 def read(item):
  p=Path(item['path'])
  if p.is_absolute() or '..' in p.parts:raise ValueError('invalid exact map proof path')
  raw=(root/p).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('exact map proof changed: '+str(p))
  return raw
 record=json.loads(read(proof['exactMapDeltaProof']));old=json.loads(read(record['priorCatalog']));oldproof=old['supportPolicy']['softwareQualificationProof']
 if record['scope']!='display03-exact-active-map' or record['status']!='passed':raise ValueError('exact map proof incomplete')
 if {k:v for k,v in proof.items() if k!='exactMapDeltaProof'}!=oldproof:raise ValueError('prior proof changed')
 comparable=json.loads(json.dumps(catalog));comparable['supportPolicy']['softwareQualificationProof']=oldproof
 if comparable!=old:raise ValueError('unrelated catalog change')
 if record['nativeInputs']!=inputs(root):raise ValueError('exact map native closure changed')
 for name,digest in record['supportInputs'].items():
  if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('exact map support changed: '+name)
 build=json.loads(read(record['decodedBuild']))
 for name,digest in {**build['productionSources'],**build['productionResources']}.items():
  if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('decoded build source changed: '+name)
 if hashlib.sha256(read(record['decodedProbe'])).hexdigest()!=build['probeSha256']:raise ValueError('decoded probe changed')
 for name,digest in build['probeResources'].items():
  if hashlib.sha256((root/record['decodedResources']/name).read_bytes()).hexdigest()!=digest:raise ValueError('decoded fixture changed')
 log=read(record['decodedLog']).decode()
 if 'DECODED_OUTLINE_READY' not in log or 'READY_FULL_BUNDLED=true selected=true point=335,165' not in log or 'Error:' in log or 'Watchdog' in log:raise ValueError('covered READY timer path failed')
 extra=json.loads(read(record['extraReceipt']));out=read(record['extraLog']).decode()
 if parse_output(out,extra['rawExit'],('exactExtraIdentity',))['status']!='passed':raise ValueError('extra point test failed')
 for n in record['extraOwnerInputs']:
  if extra['inputHashes'][n]!=hashlib.sha256((root/n).read_bytes()).hexdigest():raise ValueError('extra selection owner changed: '+n)
 for name,item in record['screenshots'].items():
  w,h,p=png(read(item)); expected=454 if name=='large' else 390
  if (w,h)!=(expected,expected):raise ValueError('frame dimensions changed')
  if name!='active':
   limit=16188 if expected==454 else 11945;lit=sum(any(q) for q in p)
   if lit>=limit or lit!=record['lit'][name]:raise ValueError('LOW lit-pixel bound failed: '+name)
 for k in ('enPoint','ruPoint','largePoint','activePoint'):
  if 'EXACT_POINT active=335,165 low=335,165 activePin=true lowPin=true' not in read(record[k]).decode():raise ValueError('same point observation missing')
 # 72 actual bundled bitmaps, every phase, fixed foreground exclusion. Counts
 # bound only the observed RU foreground (plus 100px measurement margin).
 rect=((35,132,315,171),(20,180,370,288),(40,288,350,327),(125,327,265,370));maximum=0
 for name in [f'AodMap{i}' for i in range(54)]+[f'AodExtra{i}' for i in range(18)]:
  w,h,px=png((root/'watchface/resources/drawables'/f'{name}.png').read_bytes())
  if (w,h)!=(390,390):raise ValueError('map canvas differs')
  counts=[0,0,0,0];total=0
  for i,v in enumerate(px):
   if not any(v):continue
   x=i%390;y=i//390
   if any(x0<=x<x1 and y0<=y<y1 for x0,y0,x1,y1 in rect):continue
   counts[(y%2)*2+x%2]+=1;total+=1
  maximum=max(maximum,max(total-c for c in counts))
 if maximum!=record['maxMapLit'] or maximum+record['sampleForegroundUpper']>=11945:raise ValueError('sampled foreground budget failed')
 validate_version(root)
 with tempfile.TemporaryDirectory(prefix='spacefox-exact-map-prior-') as d:
  target=Path(d)
  for folder in ('watchface','locales','tools','tests'):shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
  for folder in ('openspec','corpus','assets','catalog','schemas'):(target/folder).symlink_to(root/folder,target_is_directory=True)
  for name,item in record['priorSnapshots'].items():
   p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(read(item))
  for name in record['priorAbsent']:
   p=Path(name)
   if p.is_absolute() or '..' in p.parts:raise ValueError('invalid previous absent path')
   (target/p).unlink()
  if previous(target,old)!=old['supportPolicy']['softwareQualifiedLocales']:raise ValueError('prior LOW proof did not reconstruct')
 return catalog['supportPolicy']['softwareQualifiedLocales']
