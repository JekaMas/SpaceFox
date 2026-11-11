# SPDX-License-Identifier: MIT
"""Negative artifact mutations around an observed healthy native trial; not live-DOM/product evidence."""
import copy,json,hashlib,math
from pathlib import Path
from audit_marker_raster import audit_trial,artifact
from png_decoder_source import decode_png
from export_assets import png
R=Path(__file__).parent;B=R/'g1-adapted';M=json.loads((B/'native-manifest.json').read_text());healthy=next(t for t in M['trials'] if t['candidate']=='M1-11' and t['size']==390);prior=json.loads((R/'g1-native-independent-audit.json').read_text());baseline=next(t for t in prior['trials'] if t['id']==healthy['id']);assert baseline['passed'];oracle=json.loads((B/'native-hero-oracle.json').read_text())['expected'][0];D=R/'negative-artifacts';D.mkdir(exist_ok=True);results=[]
def save(data,suffix):
 p=D/(hashlib.sha256(data).hexdigest()+suffix);p.write_bytes(data);return{'file':str(p),'sha256':hashlib.sha256(data).hexdigest()}
def change_png(a,fn):
 _,blob=artifact(B,a);w,h,ch,rows=decode_png(blob);fn(w,h,ch,rows);return save(png(w,h,ch,rows),'.png')
def probe(name,fn,native=True,scene=oracle,source=healthy):
 t=copy.deepcopy(source);fn(t)
 try:
  v=audit_trial(B,t,scene,native_required=native);errors=v['errors'];rejected=bool(errors)
 except Exception as e:errors=[type(e).__name__+': '+str(e)];rejected=True
 results.append({'name':name,'scope':'artifact-only deliberately corrupted data/images derived from actual healthy capture; not a live-DOM intervention','rejected':rejected,'errors':errors})
probe('missing mandatory core reference',lambda t:t['masks'].pop('core'))
def edge(t):
 a=t['masks']['core'];new=change_png(a,lambda w,h,c,rows:rows[0].__setitem__(3,255));t['masks']['core']={**new,'origin':a['origin']}
probe('reference self-edge clipping',edge)
def cover(t):
 b=next(b for b in t['geometry']['occluders'] if b['role']=='field-row');x,y=t['geometry']['anchor'];b.update(x=x-40,y=y-40,w=80,h=80,background='rgb(5, 10, 17)',display='block',visibility='visible',opacity=1)
probe('opaque foreground covers complete glyph',cover)
probe('additional real rectangular geo clip removes core',lambda t:t['geometry']['clips'].append({'role':'nested-geo','kind':'rect','x':0,'y':0,'w':10,'h':10}))
probe('additional watch/circle clip removes marker',lambda t:t['geometry']['clips'].append({'role':'nested-watch','kind':'circle','cx':195,'cy':195,'r':10}))
def tiny(t):
 a=t['masks']['core']
 def f(w,h,c,rows):
  for row in rows:
   for x in range(w):row[x*c+3]=0
  rows[100][305*c+3]=255
 t['masks']['core']={**change_png(a,f),'origin':a['origin']}
probe('tiny core',tiny)
probe('native ON substituted with low-contrast HIDE images',lambda t:t['capture'].__setitem__('on',copy.deepcopy(t['capture']['hide'])))
def shift(t):
 for a in t['capture']['on']:
  new=change_png(a,lambda w,h,c,rows:[row.__setitem__(slice(None),bytes([0]*c)+row[:-c]) for row in rows]);a.update(new)
probe('ON face pixel content shifted one physical pixel',shift)
def nonmarker(t):
 a=t['capture']['nonMarkerOn'];value=json.loads(artifact(B,a)[1]);value[0]['text']='corrupted non-marker text';t['capture']['nonMarkerOn']=save(json.dumps(value).encode(),'.json')
probe('non-marker descriptor changed',nonmarker)
probe('mandatory occluder channel absent',lambda t:t['geometry'].pop('occluders'))
probe('NaN anchor',lambda t:t['geometry']['anchor'].__setitem__(0,float('nan')))
probe('missing raster artifact',lambda t:t['masks']['core'].__setitem__('file','objects/missing-file.png'))
geo=json.loads((B/'geometry-manifest.json').read_text());null=next(t for t in geo['trials'] if t['sourcePoint'] is None);expected={'sceneId':null['scene'],'sourcePoint':None}
def invent(t):t['geometry']['anchor']=healthy['geometry']['anchor'];t['masks']=healthy['masks'];t['markerReferenceSvg']=healthy['markerReferenceSvg']
probe('invented marker in actual no-coordinate scene',invent,native=False,scene=expected,source=null)
report={'method':'Independent checker negative discrimination; actual healthy baseline reused from retained G1 native audit. All interventions artifact-only, not new live/browser observations.','healthyBaseline':{'receipt':'g1-native-independent-audit.json','trial':baseline['id'],'passed':baseline['passed']},'results':results,'allMutantsRejected':all(x['rejected'] for x in results)};(R/'independent-checker-negative-probes.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
