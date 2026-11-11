# SPDX-License-Identifier: MIT
"""Independent marker artifact audit. No SpaceFox renderer/evaluator imports.
Proposed adapter in raster-schema.md. No product observations have yet been evaluated.
"""
import argparse,hashlib,json,math,subprocess,tempfile
from pathlib import Path
from png_decoder_source import decode_png
SIZES=(390,222,195)
POLICY={'area390':{'glyph':60,'core':28,'halo':30},'survival':{'glyph':.95,'core':.98,'halo':.95},'clearance390':4,'coreEqDiameter390':6,'glyphMinMaxExtent390':12,'coreContrast':3,'coreContrastFraction':.9,'haloContrast':3,'haloContrastFraction':.5,'coreAlphaEligible':.75,'haloAlphaEligible':.25,'minEligible390':12,'minSignalDelta8bit':12,'noiseMultiplier':4,'paddingCapturePixels':16}

def finite(v):return isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v)
def check_rect(r):return all(finite(r.get(k)) for k in ('x','y','w','h')) and r['w']>=0 and r['h']>=0

def rgb_alpha(style):
 import re
 if not isinstance(style,str):raise ValueError('background color missing')
 n=[float(v) for v in re.findall(r'[\d.]+',style)]
 if len(n) not in (3,4) or not all(math.isfinite(v) for v in n) or any(not 0<=v<=255 for v in n[:3]):raise ValueError('invalid computed background')
 a=n[3] if len(n)==4 else 1
 if not 0<=a<=1:raise ValueError('invalid background alpha')
 return a

def luminance(p):
 rgb=[v/255 for v in p[:3]];rgb=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in rgb]
 return sum(v*w for v,w in zip(rgb,(.2126,.7152,.0722)))
def contrast(p,q):
 a,b=luminance(p),luminance(q);return(max(a,b)+.05)/(min(a,b)+.05)
def percentile(xs,p):
 if not xs:return 0
 ss=sorted(xs);return ss[min(len(ss)-1,max(0,math.ceil(len(ss)*p)-1))]
def bounds_distance(x,y,r):return math.hypot(max(r['x']-x,0,x-r['x']-r['w']),max(r['y']-y,0,y-r['y']-r['h']))

def artifact(base,a):
 if not isinstance(a,dict) or not isinstance(a.get('file'),str) or not isinstance(a.get('sha256'),str):raise ValueError('missing hashed artifact')
 p=(base/a['file']).resolve();b=p.read_bytes()
 if hashlib.sha256(b).hexdigest()!=a['sha256']:raise ValueError('artifact hash mismatch')
 return p,b

def decoded(base,a):
 p,b=artifact(base,a);ancestry='lossless-png'
 if b.startswith(b'\xff\xd8'):
  ancestry='native-jpeg decoded by macOS sips; JPEG uncertainty retained'
  with tempfile.TemporaryDirectory(prefix='marker-jpeg-',dir=str(Path(__file__).parent)) as d:
   out=Path(d)/'decoded.png';subprocess.run(['/usr/bin/sips','-s','format','png',str(p),'--out',str(out)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE);b=out.read_bytes()
 w,h,ch,rows=decode_png(b);pixels=[tuple(row[x*ch:x*ch+3]) for row in rows for x in range(w)]
 return {'w':w,'h':h,'ch':ch,'rows':rows,'pixels':pixels,'ancestry':ancestry}

def crop(base,c,size):
 im=decoded(base,c);r=c.get('faceRect',{})
 if not check_rect(r) or any(not isinstance(r[k],int) for k in ('x','y','w','h')) or r['w']!=size or r['h']!=size or r['x']<0 or r['y']<0 or r['x']+size>im['w'] or r['y']+size>im['h']:raise ValueError('invalid integer face crop/native size')
 return {'pixels':[im['pixels'][(r['y']+y)*im['w']+r['x']+x] for y in range(size) for x in range(size)],'ancestry':im['ancestry']}

_MASK_CACHE={}
def mask(base,a,size):
 if not isinstance(a,dict):raise ValueError('missing mandatory component reference')
 _,blob=artifact(base,a) # File existence/hash remain mandatory even on a decoded-content cache hit.
 key=(a.get('sha256'),tuple(a.get('origin',[])))
 if key in _MASK_CACHE:return _MASK_CACHE[key]
 w,h,ch,rows=decode_png(blob);im={'w':w,'h':h,'ch':ch,'rows':rows}
 if im['ch']!=4:raise ValueError('component reference must have alpha')
 origin=a.get('origin');w,h=im['w'],im['h']
 if not isinstance(origin,list) or len(origin)!=2 or any(not isinstance(v,int) for v in origin):raise ValueError('invalid reference origin')
 if w<5 or h<5:raise ValueError('reference too small')
 alphas=[[row[x*4+3]/255 for x in range(w)] for row in im['rows']]
 if any(alphas[y][x]>.001 for y in range(h) for x in range(w) if x<2 or y<2 or x>=w-2 or y>=h-2):raise ValueError('reference already clipped at own edge')
 points=[(origin[0]+x,origin[1]+y,alphas[y][x]) for y in range(h) for x in range(w) if alphas[y][x]>0]
 _MASK_CACHE[key]=points;return points

def audit_trial(base,t,expected,native_required=True):
 errors=[];metrics={};size=t.get('size');r={'id':t.get('id'),'candidate':t.get('candidate'),'scene':t.get('scene'),'size':size,'errors':errors,'metrics':metrics}
 if size not in SIZES:raise ValueError('unsupported actual size')
 if t.get('sourcePoint')!=expected['sourcePoint']:errors.append('source point mismatch')
 g=t.get('geometry',{});clips=g.get('clips');occ=g.get('occluders');protected=g.get('protected')
 if not isinstance(clips,list) or len(clips)<2 or sum(c.get('role')=='watch' and c.get('kind')=='circle' and c.get('cx')==195 and c.get('cy')==195 and c.get('r')==195 for c in clips)!=1:raise ValueError('missing actual clipping chain')
 for c in clips:
  if c.get('kind')=='circle':
   if not all(finite(c.get(k)) for k in ('cx','cy','r')) or c['r']<=0:raise ValueError('invalid circle clip')
  elif c.get('kind')!='rect' or not check_rect(c):raise ValueError('unsupported or invalid clip')
 if not isinstance(occ,list) or any(sum(x.get('role')==role for x in occ)!=1 for role in ('mission','field-row','count-group')):raise ValueError('missing actual foreground container channel')
 painted=[]
 for b in occ:
  if not check_rect(b) or not finite(b.get('opacity')) or not 0<=b['opacity']<=1 or not isinstance(b.get('display'),str) or not isinstance(b.get('visibility'),str):raise ValueError('invalid foreground measurement')
  a=rgb_alpha(b.get('background'))*b['opacity']
  if b['display'] not in ('none','contents') and b['visibility']=='visible' and b['w']>0 and b['h']>0 and a>0:painted.append((b,a))
 if not isinstance(protected,list) or len(protected)<15 or any(not check_rect(b) for b in protected):raise ValueError('missing full protected foreground paint')
 cap=t.get('capture',{});ons=[];offs=[]
 if native_required:
  cap=t.get('capture',{});onDesc=json.loads(artifact(base,cap.get('nonMarkerOn'))[1]);offDesc=json.loads(artifact(base,cap.get('nonMarkerHide'))[1])
  if onDesc!=offDesc:errors.append('counterpart changed non-marker descriptors')
  if cap.get('provenance') not in ('native-jpeg','actual-viewport-png'):errors.append('native actual image support unavailable')
  if len(cap.get('on',[]))<1 or len(cap.get('hide',[]))<2:raise ValueError('missing stable image replicas')
  ons=[crop(base,v,size) for v in cap['on']];offs=[crop(base,v,size) for v in cap['hide']];metrics['imageAncestry']=sorted(set(x['ancestry'] for x in ons+offs))
 sourcePoint=expected['sourcePoint'];scale=size/390
 if sourcePoint is None:
  if g.get('anchor') is not None or t.get('masks') is not None or t.get('markerReferenceSvg') is not None:errors.append('invented marker/reference for missing point')
  if native_required:
   maxdiff=max(max(abs(a-b) for a,b in zip(p,q)) for p,q in zip(ons[0]['pixels'],offs[0]['pixels']));noise=max(max(abs(a-b) for a,b in zip(p,q)) for p,q in zip(offs[0]['pixels'],offs[1]['pixels']));metrics.update(noMarkerMaxDelta=maxdiff,replicateMaxNoise=noise)
   if maxdiff>max(12,noise*4):errors.append('signal in no-marker image')
  return r
 if not isinstance(g.get('anchor'),list) or len(g['anchor'])!=2 or not all(finite(v) for v in g['anchor']):raise ValueError('invalid true site anchor')
 artifact(base,t.get('markerReferenceSvg'))
 components={name:mask(base,t.get('masks',{}).get(name),size) for name in ('glyph','core','halo')}
 full=components['glyph'];pixels={};survivals={};clearance=math.inf
 for name,pts in components.items():
  area=sum(a for x,y,a in pts);metrics[name+'AlphaArea']=area
  if area+1e-8<POLICY['area390'][name]*scale*scale:errors.append('tiny '+name)
  kept=0;eligible=[]
  for x,y,a in pts:
   X,Y=(x+.5)/scale,(y+.5)/scale;trans=1
   for c in clips:
    if c['kind']=='circle':
     margin=c['r']-max(math.hypot((x+dx)/scale-c['cx'],(y+dy)/scale-c['cy']) for dx in (0,1) for dy in (0,1))
     inside=math.hypot(X-c['cx'],Y-c['cy'])<=c['r']
    else:
     margin=min(x/scale-c['x'],y/scale-c['y'],c['x']+c['w']-(x+1)/scale,c['y']+c['h']-(y+1)/scale)
     inside=c['x']<=X<=c['x']+c['w'] and c['y']<=Y<=c['y']+c['h']
    if not inside:trans=0
    if name=='glyph' and a>.05:clearance=min(clearance,margin)
   for b,alpha in painted:
    if b['x']<=X<=b['x']+b['w'] and b['y']<=Y<=b['y']+b['h']:trans*=1-alpha
   kept+=a*trans
   if name=='glyph' and a>.05:
    for b in protected+[b for b,alpha in painted]:clearance=min(clearance,bounds_distance(X,Y,b)-.71/scale)
   cutoff=POLICY['coreAlphaEligible'] if name=='core' else POLICY['haloAlphaEligible']
   if name in ('core','halo') and a>=cutoff and trans>=.98 and 0<=x<size and 0<=y<size:eligible.append(y*size+x)
  survive=kept/area if area>0 else 0;survivals[name]=survive
  if survive+1e-8<POLICY['survival'][name]:errors.append('clipped/occluded '+name)
  pixels[name]=eligible
 metrics['survival']=survivals;metrics['fullGlyphConservativeClearance390']=clearance
 if clearance+1e-8<POLICY['clearance390']:errors.append('full glyph clearance')
 if 2*math.sqrt(metrics['coreAlphaArea']/math.pi)/scale+1e-8<POLICY['coreEqDiameter390']:errors.append('core equivalent diameter')
 xs=[x for x,y,a in full if a>.05];ys=[y for x,y,a in full if a>.05]
 extent=max(max(xs)-min(xs)+1,max(ys)-min(ys)+1)/scale;metrics['glyphMaxExtent390']=extent
 if extent+1e-8<POLICY['glyphMinMaxExtent390']:errors.append('glyph extent')
 if not native_required:
  metrics['nativeImageSupport']='not measured in this geometry-only artifact';return r
 pad=POLICY['paddingCapturePixels'];roi=(min(xs)-pad,min(ys)-pad,max(xs)+pad,max(ys)+pad)
 inside=lambda i:roi[0]<=i%size<=roi[2] and roi[1]<=i//size<=roi[3]
 deltas=lambda A,B:[max(abs(a-b) for a,b in zip(p,q)) for p,q in zip(A['pixels'],B['pixels'])]
 noise=deltas(offs[0],offs[1]);
 if len(ons)>1:noise=[max(a,b) for a,b in zip(noise,deltas(ons[0],ons[1]))]
 noise99=percentile([v for i,v in enumerate(noise) if inside(i)],.99);threshold=max(POLICY['minSignalDelta8bit'],POLICY['noiseMultiplier']*noise99);metrics.update(noise99_8bit=noise99,signalThreshold8bit=threshold)
 if threshold>128:errors.append('counterpart noise too high')
 change=deltas(ons[0],offs[0]);out=[i for i in range(size*size) if not inside(i) and math.hypot(i%size+.5-size/2,i//size+.5-size/2)<size/2];offRate=sum(change[i]>threshold for i in out)/max(1,len(out));noiseRate=sum(noise[i]>threshold for i in out)/max(1,len(out));metrics['offRoiSignalFraction']=offRate
 if offRate>max(.001,noiseRate+.0005):errors.append('unexplained off-ROI image change')
 for name in ('core','halo'):
  eligible=pixels[name];minimum=max(2,math.ceil(POLICY['minEligible390']*scale*scale));metrics[name+'EligiblePixels']=len(eligible)
  if len(eligible)<minimum:errors.append('insufficient '+name+' image evidence');continue
  ratios=[min(contrast(on['pixels'][i],off['pixels'][i]) for on in ons for off in offs) for i in eligible];signal=sum(min(max(abs(a-b) for a,b in zip(on['pixels'][i],off['pixels'][i])) for on in ons for off in offs)>threshold for i in eligible)
  fraction=sum(v>=3 for v in ratios)/len(ratios);metrics[name+'ContrastFraction']=fraction;metrics[name+'Contrast10th']=percentile(ratios,.1);metrics[name+'SignalPixels']=signal
  if fraction+1e-9<POLICY[name+'ContrastFraction']:errors.append('low local '+name+' contrast')
  if signal<minimum:errors.append('weak actual '+name+' signal')
 return r

def main():
 p=argparse.ArgumentParser();p.add_argument('manifest');p.add_argument('oracle');p.add_argument('output');p.add_argument('--proof-layer',choices=('geometry','native'),default='native');p.add_argument('--frozen-candidates',required=True,help='independently frozen candidateIds JSON');args=p.parse_args();base=Path(args.manifest).resolve().parent;m=json.loads(Path(args.manifest).read_text());o=json.loads(Path(args.oracle).read_text());expected={x['sceneId']:x for x in o['expected']};report={'method':'Independent stdlib PNG/JPEG-ancestry artifact geometry/local-image-support checker, no product imports','policy':POLICY,'proofLayer':args.proof_layer,'trials':[],'errors':[],'boundary':'Diagnostic coverage and native image support are separate; neither is human search/noticeability. No unobserved/missing captures count as passing.'}
 seen=set()
 for t in m['trials']:
  key=(t.get('candidate'),t.get('scene'),t.get('size'))
  if key in seen:report['errors'].append('duplicate trial')
  seen.add(key)
  try:
   if t['scene'] not in expected:raise ValueError('scene outside independent oracle')
   r=audit_trial(base,t,expected[t['scene']],native_required=args.proof_layer=='native');r['passed']=not r['errors']
  except Exception as e:r={'id':t.get('id'),'candidate':t.get('candidate'),'scene':t.get('scene'),'size':t.get('size'),'passed':False,'errors':[type(e).__name__+': '+str(e)]}
  report['trials'].append(r)
 frozen=json.loads(Path(args.frozen_candidates).read_text());candidates=frozen.get('candidateIds');
 if not isinstance(candidates,list) or not candidates or len(set(candidates))!=len(candidates):raise ValueError('invalid frozen candidate set')
 expectedkeys={(c,s,n) for c in candidates for s in expected for n in SIZES}
 if seen!=expectedkeys:report['errors'].append('incomplete candidate×oracle×three-size coverage')
 report['passed']=bool(report['trials']) and not report['errors'] and all(t['passed'] for t in report['trials']);Path(args.output).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'trials':len(report['trials']),'passedTrials':sum(t['passed'] for t in report['trials']),'passed':report['passed'],'errors':report['errors']},indent=2))
if __name__=='__main__':main()
