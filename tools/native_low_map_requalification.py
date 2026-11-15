"""Requalify only the DISPLAY03 LOW map delta against its retained predecessor."""
import hashlib,json,math,shutil,tempfile
from pathlib import Path

def validate(root,catalog):
 from tools.native_display03_probe import inputs
 from tools.native_display03_requalification import validate as previous
 from tools.run_native_tests import parse_output
 from tools.spacefox.native_profile import png_pixels
 from tools.generate_native_version import validate as validate_version
 root=Path(root).resolve();proof=catalog['supportPolicy']['softwareQualificationProof']
 def read(item):
  p=Path(item['path'])
  if p.is_absolute() or '..' in p.parts:raise ValueError('invalid LOW delta path')
  raw=(root/p).read_bytes()
  if hashlib.sha256(raw).hexdigest()!=item['sha256']:raise ValueError('LOW delta proof changed: '+str(p))
  return raw
 record=json.loads(read(proof['lowMapDeltaProof']))
 if record['scope']!='display03-low-map-geometry' or record['status']!='passed':raise ValueError('LOW geometry proof incomplete')
 old=json.loads(read(record['priorCatalog']));prior=old['supportPolicy']['softwareQualificationProof']
 if {k:v for k,v in proof.items() if k!='lowMapDeltaProof'}!=prior:raise ValueError('prior qualification changed')
 comparable=json.loads(json.dumps(catalog));comparable['supportPolicy']['softwareQualificationProof']=prior
 if comparable!=old:raise ValueError('catalog changed outside LOW proof')
 if record['nativeInputs']!=inputs(root):raise ValueError('LOW native source closure changed')
 for name,digest in record['supportInputs'].items():
  if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('LOW support changed: '+name)
 receipt=json.loads(read(record['nativeReceipt']));log=read(record['nativeLog']).decode()
 if receipt['inputHashes']!=record['nativeInputs'] or parse_output(log,receipt['rawExit'],('display03RealMapDecode',))['status']!='passed':raise ValueError('LOW decoder observation missing')
 build=json.loads(read(record['visualBuild']))
 # The controlled visual uses these exact production owners and assets. NativeVersion,
 # decoder and build manifest do not participate in this bundled-map drawing.
 for name in record['visualInputs']:
  actual=hashlib.sha256((root/name).read_bytes()).hexdigest()
  expected=build['productionSources'].get(name,build['productionResources'].get(name))
  if expected!=actual:raise ValueError('LOW visual source changed: '+name)
 decoded=json.loads(read(record['decodedBuild']))
 for name,digest in {**decoded['productionSources'],**decoded['productionResources']}.items():
  if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:raise ValueError('decoded visual source differs: '+name)
 if hashlib.sha256(read(record['decodedProbe'])).hexdigest()!=decoded['probeSha256']:raise ValueError('decoded visual probe differs')
 for name,digest in decoded['probeResources'].items():
  if hashlib.sha256((root/record['decodedResources']/name).read_bytes()).hexdigest()!=digest:raise ValueError('decoded fixture differs: '+name)
 if 'DECODED_OUTLINE_READY' not in read(record['decodedLog']).decode():raise ValueError('decoded outline was not ready')
 observations={}
 for lang,item in record['screenshots'].items():
  width,height,pixels=png_pixels(read(item))
  if (width,height)!=(390,390):raise ValueError('unexpected native LOW dimensions')
  def rgb(x,y):
   i=(y*390+x)*4;return pixels[i:i+3]
  outline=[(x,y) for y in range(100) for x in range(390) if (lambda p:p[2]>120 and p[2]>p[0] and p[1]>p[0])(rgb(x,y))]
  date=[(x,y) for y in range(100,140) for x in range(390) if min(rgb(x,y))>90]
  point=[(x,y) for y in range(68,83) for x in range(276,291) if (x-283)**2+(y-75)**2<=49 and max(rgb(x,y))>120]
  clock=[(x,y) for y in range(140,247) for x in range(390) if (lambda p:p[1]>80 and p[1]>p[0]*1.2)(rgb(x,y))]
  coral=sum(1 for x,y in point if (lambda p:p[0]>150 and p[0]>p[1]*1.2)(rgb(x,y)))
  if not outline or not date or not point or not clock or coral<20:raise ValueError('LOW visual region or point empty')
  bounds=lambda pts:[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]
  ob,pb,cb=bounds(outline),bounds(point),bounds(clock)
  def luminance(p):
   c=[v/255 for v in p];c=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c];return .2126*c[0]+.7152*c[1]+.0722*c[2]
  contrast=min((luminance(rgb(x,y))+.05)/.05 for x,y in outline)
  if contrast<4.5:raise ValueError('LOW outline contrast below 4.5:1')
  gap=min(math.hypot(x-u,y-v) for x,y in outline for u,v in date if abs(x-u)<30 and abs(y-v)<30)
  lit=sum(1 for i in range(0,len(pixels),4) if max(pixels[i:i+3])>0)
  if ob[2]-ob[0]+1<90 or pb[2]-pb[0]+1<12 or pb[3]-pb[1]+1<12 or cb[3]-cb[1]+1<96 or gap<8 or lit>=11945:raise ValueError('LOW geometry bound failed: '+lang)
  observations[lang]={'outlineBounds':ob,'pointBounds':pb,'clockBounds':cb,'clearance':round(gap,2),'lit':lit}
 if observations!=record['measurements'] or set(observations)!={'en','ru','decoded'}:raise ValueError('LOW measurements differ')
 validate_version(root)
 with tempfile.TemporaryDirectory(prefix='spacefox-low-map-prior-') as d:
  target=Path(d)
  for folder in ('watchface','locales','tools','tests'):shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
  for folder in ('openspec','corpus','assets','catalog','schemas'):(target/folder).symlink_to(root/folder,target_is_directory=True)
  for name,item in record['priorSnapshots'].items():
   p=target/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(read(item))
  if previous(target,old)!=old['supportPolicy']['softwareQualifiedLocales']:raise ValueError('prior DISPLAY03 admission did not reconstruct')
 return catalog['supportPolicy']['softwareQualifiedLocales']
