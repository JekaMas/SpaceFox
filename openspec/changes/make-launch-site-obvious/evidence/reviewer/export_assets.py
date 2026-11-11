# SPDX-License-Identifier: MIT
"""Independent artifact adapter: export-owned PNGs/refs and native board crops, no product imports."""
import argparse,base64,collections,gzip,hashlib,json,subprocess,struct,zlib
from pathlib import Path
from png_decoder_source import decode_png
sha=lambda b:hashlib.sha256(b).hexdigest()

def png(w,h,ch,rows):
 def chunk(k,b):return struct.pack('>I',len(b))+k+b+struct.pack('>I',zlib.crc32(k+b)&0xffffffff)
 return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,6 if ch==4 else 2,0,0,0))+chunk(b'IDAT',zlib.compress(b''.join(b'\0'+bytes(r) for r in rows),6))+chunk(b'IEND',b'')
def put(out,b,suffix):
 name='objects/'+sha(b)+suffix;p=out/name
 if not p.exists():p.write_bytes(b)
 return {'file':name,'sha256':sha(b)}
def blocktrial(rec,asset,out,size):
 o=rec['observation'];m=o['marker'];snap=m['snapshot'];protected=[*o['text'],*o['icons'],*o['badges'],o['rocket']]
 for b in (snap['foreground'] if snap else []):
  if b['w']>0 and b['h']>0 and b['display'] not in ('none','contents'):protected.append(b)
 masks=None;visible=None;reference=None
 if asset:
  masks={k:{**asset['files'][f'{size}/{k}/raw'],'origin':[0,0]} for k in ('glyph','core','halo')};visible={k:{**asset['files'][f'{size}/{k}/visible'],'origin':[0,0]} for k in ('glyph','core','halo')};reference=asset['referenceSvgFile']
 return {'id':f"{rec['candidate']}:{rec['scene']}:{size}",'candidate':rec['candidate'],'scene':rec['scene'],'size':size,'sourcePoint':m['sourcePoint'],'geometry':{'anchor':m['anchor'],'clips':[{'role':'watch','kind':'circle','cx':195,'cy':195,'r':195},{'role':'geography','kind':'rect',**snap['geo']}] if snap else [{'role':'watch','kind':'circle','cx':195,'cy':195,'r':195},{'role':'geography','kind':'rect','x':0,'y':0,'w':390,'h':390}],'occluders':snap['foreground'] if snap else o['occluders'],'protected':protected if snap else [*o['text'],*o['icons'],*o['badges'],o['rocket']]},'masks':masks,'visibleMasks':visible,'markerReferenceSvg':reference,'reported':m['masks'].get(str(size)),'assetKey':rec['assetKey']}
def main():
 p=argparse.ArgumentParser();p.add_argument('campaign');p.add_argument('output');p.add_argument('--native-dir');p.add_argument('--generation',default=None);p.add_argument('--stage',default=None);p.add_argument('--frozen-candidates');p.add_argument('--oracle');p.add_argument('--native-oracle');args=p.parse_args();out=Path(args.output).resolve();out.mkdir(exist_ok=True);(out/'objects').mkdir(exist_ok=True);raw=Path(args.campaign).read_bytes();campaign=json.loads(gzip.decompress(raw) if str(args.campaign).endswith('.gz') else raw)
 # JS serialization verifies the author's asset-key binding without loading product code.
 js="const f=require('fs'),z=require('zlib'),h=require('crypto');let p=process.argv[1],b=f.readFileSync(p),c=JSON.parse(p.endsWith('.gz')?z.gunzipSync(b):b);for(let[k,v]of Object.entries(c.assets))if(h.createHash('sha256').update(JSON.stringify(v)).digest('hex')!==k)throw Error('asset-key mismatch');process.stdout.write(String(Object.keys(c.assets).length));"
 subprocess.run(['node','-e',js,str(Path(args.campaign).resolve())],check=True,stdout=subprocess.DEVNULL)
 assets={}
 for key,a in campaign['assets'].items():
  files={}
  for name,data in a['assets'].items():
   prefix='data:image/png;base64,'
   if not data.startswith(prefix):raise ValueError('non-PNG asset')
   files[name]=put(out,base64.b64decode(data[len(prefix):],validate=True),'.png')
  assets[key]={'files':files,'referenceSvgFile':put(out,a['referenceSvg'].encode(),'.svg')}
 (out/'asset-index.json').write_text(json.dumps({'campaignSha256':sha(raw),'assets':assets},indent=2)+'\n')
 groups=[*campaign['generations'],*campaign.get('controls',[])];extra=campaign.get('authorNative',[])
 if isinstance(extra,dict):extra=[extra]
 groups+=extra
 records=[r for g in groups for r in g.get('records',[])];by={(r['candidate'],r['scene']):r for r in records};geometry=[]
 if args.stage and (not args.frozen_candidates or not args.oracle):raise ValueError('--stage requires external frozen candidates and oracle')
 stage=args.stage or args.generation
 matches=[g for g in groups if g.get('name')==stage] if stage else [campaign['generations'][0]]
 if len(matches)!=1:raise ValueError('explicit unique --stage required')
 chosen=matches[0]
 if args.frozen_candidates:
  frozen=json.loads(Path(args.frozen_candidates).read_text());expected_ids=frozen['candidateIds']
 else:expected_ids=([f'M2-{i}{j}' for i in range(1,6) for j in range(1,5)] if chosen['name']=='G2' else [f'OLD-{i}' for i in range(1,6)]+[f'M1-{i}{j}' for i in range(1,6) for j in range(1,7)])
 if not expected_ids or len(set(expected_ids))!=len(expected_ids):raise ValueError('invalid external frozen candidate set')
 if set(r['candidate'] for r in chosen['records'])!=set(expected_ids):raise ValueError('stage candidate coverage differs frozen set')
 for r in chosen['records']:
  for size in (390,222,195):geometry.append(blocktrial(r,assets.get(r['assetKey']),out,size))
 (out/'geometry-manifest.json').write_text(json.dumps({'schemaVersion':1,'stage':chosen['name']+'-complete-source-masks','trials':geometry},separators=(',',':'))+'\n')
 oracle=json.loads(Path(args.oracle).read_text()) if args.oracle else {'schemaVersion':1,'expected':[{'sceneId':s['id'],'sourcePoint':s['fixture']['point']} for s in campaign['training']]};(out/'author-oracle.json').write_text(json.dumps(oracle,indent=2)+'\n');(out/'g1-expected-candidates.json').write_text(json.dumps({'candidateIds':expected_ids},indent=2)+'\n');(out/'expected-candidates.json').write_text(json.dumps({'candidateIds':expected_ids},indent=2)+'\n')
 report={'campaignSha256':sha(raw),'records':len(records),'assetObjects':len(assets),'uniqueDecodedPngs':len(list((out/'objects').glob('*.png'))),'nativeBoards':0,'watchCrops':0,'missingExactSourceRecords':[],'errors':[]};captures=collections.defaultdict(list)
 if args.native_dir:
  folder=Path(args.native_dir).resolve()
  for mp in sorted(folder.glob('*.json')):
   meta=json.loads(mp.read_text());jp=mp.with_suffix('.jpg');target=out/'objects'/('decoded-'+sha(jp.read_bytes())+'.png')
   if not target.exists():subprocess.run(['/usr/bin/sips','-s','format','png',str(jp),'--out',str(target)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
   w,h,ch,rows=decode_png(target.read_bytes());viewport=meta['viewport']
   if [w,h]!=viewport:report['errors'].append({'file':mp.name,'error':'raw dimensions != CSS viewport; no silent resize/crop registration','raw':[w,h],'viewport':viewport});continue
   report['nativeBoards']+=1
   for t in meta['trials']:
    fr=t['faceRect'];n=t['size'];x,y=fr['x'],fr['y']
    if not all(isinstance(v,int) for v in (x,y,n)) or abs(fr['w']-n)>1e-4 or abs(fr['h']-n)>1e-4 or x<0 or y<0 or x+n>w or y+n>h:raise ValueError('unregistered face crop')
    b=png(n,n,ch,[row[x*ch:(x+n)*ch] for row in rows[y:y+n]]);cropasset=put(out,b,'.png');desc=put(out,json.dumps(t['nonMarker'],sort_keys=True,separators=(',',':')).encode(),'.json');captures[(t['candidate'],t['scene'],n)].append({**t,'image':cropasset,'descriptor':desc,'rawJpeg':{'file':str(jp),'sha256':sha(jp.read_bytes())},'rawMetadata':{'file':str(mp),'sha256':sha(mp.read_bytes())},'ancestry':'Native JPEG decoded by sips then integer cropped; no resampling; CSSOM dimension tolerance1e-4px'});report['watchCrops']+=1
   target.unlink() # Keep raw JPEGs, content-addressed exact crops; temporary whole-board analysis need not consume disk.
 native=[]
 for (candidate,scene,size),cap in captures.items():
  rec=by.get((candidate,scene))
  if not rec:report['missingExactSourceRecords'].append([candidate,scene,size]);continue
  trial=blocktrial(rec,assets.get(rec['assetKey']),out,size);on=sorted([v for v in cap if v['on']],key=lambda v:v['rep']);hide=sorted([v for v in cap if not v['on']],key=lambda v:v['rep'])
  if len(on)!=2 or len(hide)!=2:report['errors'].append({'candidate':candidate,'size':size,'error':'missing ON2/HIDE2'});continue
  def image(v):return{**v['image'],'faceRect':{'x':0,'y':0,'w':size,'h':size}}
  trial['capture']={'provenance':'native-jpeg','on':[image(v) for v in on],'hide':[image(v) for v in hide],'nonMarkerOn':on[0]['descriptor'],'nonMarkerHide':hide[0]['descriptor'],'rawCaptureProvenance':[{'rawJpeg':v['rawJpeg'],'rawMetadata':v['rawMetadata'],'ancestry':v['ancestry']} for v in cap]};native.append(trial)
 
 if args.native_oracle:
  no=json.loads(Path(args.native_oracle).read_text());(out/'native-oracle.json').write_text(json.dumps(no,indent=2)+'\n');expected_keys={(c,v['sceneId'],n) for c in expected_ids for v in no['expected'] for n in (390,222,195)}
  if set(captures)!=expected_keys:report['errors'].append('native capture tuple coverage differs explicit frozen candidates/native oracle')
 (out/'native-manifest.json').write_text(json.dumps({'schemaVersion':1,'stage':'g1-fixed-author-hero-native','trials':native},separators=(',',':'))+'\n');(out/'native-capture-index.json').write_text(json.dumps({'captures':[{'candidate':k[0],'scene':k[1],'size':k[2],'frames':v} for k,v in captures.items()]},separators=(',',':'))+'\n');(out/'adapter-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2),flush=True)
if __name__=='__main__':main()
