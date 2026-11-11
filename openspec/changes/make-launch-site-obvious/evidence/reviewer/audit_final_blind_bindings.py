# SPDX-License-Identifier: MIT
"""Post-lock independent truth/source/response binding audit; reuses frozen scorer greens.
No new perceptual threshold. Direct positive positions checked on actual source masks.
"""
import json,gzip,hashlib,math,collections
from pathlib import Path
from png_decoder_source import decode_png
T=Path(__file__).parent;B=Path('/tmp/spacefox-marker-final-blind');A=T/'confirm-adapted';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();truth=json.loads((B/'truth.json').read_text());freeze=json.loads((T/'final-freeze.json').read_text());packet=json.loads((T/'confirm24/inputs.json').read_text());native=json.loads((A/'native-manifest.json').read_text());by={(t['candidate'],t['scene'],t['size']):t for t in native['trials']};expected_ids=freeze['candidateIds'];sources={s['id']:s for s in packet['scenes']};errors=[];bindings=[];CACHE={}
def read_image(base,a):
 p=(base/a['file']).resolve()
 if sha(p)!=a['sha256']:raise ValueError('image artifact hash mismatch')
 if a['sha256'] not in CACHE:
  w,h,ch,rows=decode_png(p.read_bytes());CACHE[a['sha256']]=(w,h,ch,rows)
 return CACHE[a['sha256']]
def RGB(im):
 w,h,ch,rows=im
 return b''.join(bytes(row) if ch==3 else bytes(v for x in range(w) for v in row[x*ch:x*ch+3]) for row in rows)
first={lang:next(s for s in packet['scenes'] if s['language']==lang and s['fixture']['point'] is not None)['id'] for lang in ('ru','en')};firstnull=next(s for s in packet['scenes'] if s['fixture']['point'] is None)['id'];expected=collections.Counter((c,s,n,k) for c in expected_ids for n in (390,222,195) for s,k in [(first['ru'],'active'),(first['en'],'active'),(firstnull,'genuine-null'),(first['ru'],'map-present-marker-hidden')]);actual=collections.Counter((t['candidate'],t['scene'],t['size'],t['kind']) for t in truth['trials']);assert actual==expected,'frozen sample rule mismatch';assert truth['profile']=='final' and len(truth['trials'])==60
for t in truth['trials']:
 key=(t['candidate'],t['scene'],t['size']);source=by[key];mode='hide' if t['kind']=='map-present-marker-hidden' else 'on';assert t['on']==(mode=='on') and t['rep']==1;im=read_image(B,t['image']);src=read_image(A,source['capture'][mode][0]);assert im[:2]==(t['size'],t['size']) and RGB(im)==RGB(src),'blind image not exact native crop'
 raw=Path(t['rawFile']);assert sha(raw)==t['rawSha256'];assert any(p['rawJpeg']['sha256']==t['rawSha256'] for p in source['capture']['rawCaptureProvenance'])
 if t['expectedVisible']:
  assert t['anchor390']==source['geometry']['anchor'];m=read_image(B,t['visibleGlyphMask']);sm=read_image(A,source['visibleMasks']['glyph']);assert m[:3]==sm[:3] and m[3]==sm[3],'truth mask not actual source mask'
 else:
  assert (sources[t['scene']]['fixture']['point'] is None)==(t['kind']=='genuine-null')
 bindings.append({'imageId':t['imageId'],'candidate':t['candidate'],'scene':t['scene'],'size':t['size'],'kind':t['kind'],'passed':True})
result={'method':'Independent post-lock native-image/mask/anchor/sample-rule/answer-hash binding and positive-coordinate check; frozen scorer outputs reused, not rerun. New assertions validate their actual source oracle.','bindings':bindings,'observers':[],'errors':errors}
for obs in ('a','b'):
 answersfile=B/f'observer-{obs}/answers.json';answers=json.loads(answersfile.read_text())['answers'];lock=json.loads((B/f'response-lock-{obs}.json').read_text());scores=json.loads((B/f'scores-{obs}.json').read_text());assert sha(answersfile)==lock['answersSha256']==scores['answersSha256'];assert sha(B/'truth.json')==lock['truthSha256']==scores['truthSha256'];order=json.loads((B/f'observer-{obs}/order.json').read_text());assert len(order)==60 and set(order)=={t['imageId'] for t in truth['trials']};ans={a['imageId']:a for a in answers};assert len(ans)==len(answers)==60 and set(ans)==set(order);counts=collections.Counter();positions=[]
 for t in truth['trials']:
  a=ans[t['imageId']]
  if t['expectedVisible']:
   assert a['status']=='located' and a['classification']=='launch-site';assert all(isinstance(a[k],(int,float)) and math.isfinite(a[k]) for k in ('x','y'));assert 0<=a['x']<t['size'] and 0<=a['y']<t['size'];w,h,ch,rows=read_image(A,by[(t['candidate'],t['scene'],t['size'])]['visibleMasks']['glyph']);scale=t['size']/390;anchor=t['anchor390'];anchor_distance=math.hypot(a['x']-anchor[0]*scale,a['y']-anchor[1]*scale);mask_distance=min(math.hypot(a['x']-(x+.5),a['y']-(y+.5)) for y,row in enumerate(rows) for x in range(w) if row[x*4+3]>12.75);assert min(anchor_distance,mask_distance)<=6*scale,'positive point outside frozen tolerance';counts['positiveLocatedMeaningCorrect']+=1;positions.append({'imageId':t['imageId'],'anchorDistance390':anchor_distance/scale,'maskDistance390':mask_distance/scale,'passed':True})
  else:
   assert a['status'] in ('none','unable') and a.get('x') is None and a.get('y') is None;counts['negativeNone' if a['status']=='none' else 'negativeUncertain']+=1
 assert scores['passed'] and scores['counts']['materialFailures']==0;assert scores['counts']['negativeUnable']==counts['negativeUncertain'];result['observers'].append({'observer':obs,'counts':dict(counts),'noFalsePoint':True,'positivePositions':positions,'retainedFrozenScore':'scores-'+obs+'.json','responsesAndTruthLocksVerified':True})
result['passed']=True;result['boundary']='No material errors under the unchanged visible-positive/negative-uncertainty rule; seven negative uncertainties are not successful none decisions. This is model-image evidence, not human accuracy or search time.';(T/'final-blind-independent-binding-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':True,'sourceImageBindings':len(bindings),'observers':[{'observer':o['observer'],'counts':o['counts'],'maxAnchorDistance390':max(p['anchorDistance390'] for p in o['positivePositions'])} for o in result['observers']]},indent=2))
