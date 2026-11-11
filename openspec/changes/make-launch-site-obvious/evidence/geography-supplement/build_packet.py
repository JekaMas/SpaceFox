# SPDX-License-Identifier: MIT
"""Additional geography coverage after primary; no candidate/source tuning."""
import json,hashlib,math,subprocess,random
from pathlib import Path
repo=Path(__file__).resolve().parents[5];base=repo/'openspec/changes/make-launch-site-obvious/evidence';out=Path('/tmp/spacefox-marker-geography-blind');out.mkdir(exist_ok=True);scenes=json.load(open(base/'confirm24/inputs.json'))['scenes'];selection=json.load(open(base/'final-selection.json'));primary=json.load(open(base/'final-image-localization/truth.json'));activeIDs={t['scene']for t in primary['trials']if t['expectedVisible']};chosenPoints=[next(s['fixture']['point']for s in scenes if s['id']in activeIDs)]
def distance(a,b):
 l1,p1,l2,p2=map(math.radians,[*a,*b]);return 2*math.asin(min(1,math.sqrt(math.sin((p2-p1)/2)**2+math.cos(p1)*math.cos(p2)*math.sin((l2-l1)/2)**2)))
chosen=[]
for i in range(2):
 candidates=[s for s in scenes if s['fixture']['point']is not None and s['fixture']['point']not in chosenPoints];s=max(enumerate(candidates),key=lambda q:(min(distance(q[1]['fixture']['point'],p)for p in chosenPoints),-q[0]))[1];chosen.append(s);chosenPoints.append(s['fixture']['point'])
protocol={'stage':'Post-primary geography supplement, not anotherfreshconfirmation ornewgeneration','selectionRule':'Greedy farthest minimum great-circle distance from primarypoint andpreviouschosen; bankorder tie-break, no render/grade inspection. Two distinct non-null points.','sourceCandidates':selection['candidateIds'],'primaryPoint':chosenPoints[0],'scenes':[{'id':s['id'],'point':s['fixture']['point'],'language':s['language']}for s in chosen],'planned':{'active':30,'hidden':5,'images':35,'freshModelContexts':1},'parametersUnchanged':True,'bankSHA256':hashlib.sha256((base/'confirm24/inputs.json').read_bytes()).hexdigest()};Path(__file__).with_name('protocol.json').write_text(json.dumps(protocol,ensure_ascii=False,indent=2))
lookup={}
for p in sorted((base/'native/confirm').glob('*.json')):
 b=json.load(open(p))
 for t in b['trials']:
  if t['rep']==1:lookup[t['candidate'],t['scene'],t['size'],t['on']]=(t,p.with_suffix('.jpg'))
trials=[]
for c in selection['candidateIds']:
 conditions=[(s,z,True,'active')for s in chosen for z in [390,222,195]]+[(chosen[0],195,False,'map-present-marker-hidden')]
 for s,z,on,kind in conditions:
  t,raw=lookup[c,s['id'],z,on];r=t['faceRect'];assert all(abs(r[k]-round(r[k]))<.001 for k in ['x','y','w','h']);ident='image-'+hashlib.sha256((c+s['id']+str(z)+kind).encode()).hexdigest()[:12];file=out/(ident+'.png');subprocess.run(['/usr/bin/sips','-s','format','png','--cropToHeightWidth',str(z),str(z),'--cropOffset',str(round(r['y'])),str(round(r['x'])),str(raw),'--out',str(file)],capture_output=True,check=True);trials.append({**t,'imageId':ident,'image':{'file':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()},'rawFile':str(raw),'rawSha256':hashlib.sha256(raw.read_bytes()).hexdigest(),'kind':kind,'expectedVisible':on})
rng=random.Random(4109);rng.shuffle(trials);(out/'truth.json').write_text(json.dumps({'profile':'geography-supplement','trials':trials},ensure_ascii=False,indent=2));(out/'order.json').write_text(json.dumps([t['imageId']for t in trials]));print(protocol)
