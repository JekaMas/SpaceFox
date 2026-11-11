# SPDX-License-Identifier: MIT
"""After response lock, bind exact scene mask truth for independent scoring."""
import argparse,base64,datetime,gzip,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('campaign');p.add_argument('packet');a=p.parse_args();x=json.load(gzip.open(a.campaign));root=Path(a.packet);truth=json.loads((root/'truth.json').read_text());records=[r for g in x['generations']+x['controls'] for r in g['records']]
for t in truth['trials']:
 if not t['expectedVisible']:continue
 r=next(r for r in reversed(records)if r['candidate']==t['candidate'] and r['scene']==t['scene']);asset=x['assets'][r['assetKey']];raw=base64.b64decode(asset['assets'][str(t['size'])+'/glyph/visible'].split(',')[1]);name=t['imageId']+'-truth.png';(root/name).write_bytes(raw);t['visibleGlyphMask']={'file':name,'sha256':hashlib.sha256(raw).hexdigest(),'origin':[0,0]};t['anchor390']=r['observation']['marker']['anchor']
(root/'truth.json').write_text(json.dumps(truth,ensure_ascii=False,indent=2));ids=list(dict.fromkeys(t['candidate']for t in truth['trials']));(root/'candidate-ids.json').write_text(json.dumps({'candidateIds':ids}));sha=lambda f:hashlib.sha256((root/f).read_bytes()).hexdigest();(root/'response-lock.json').write_text(json.dumps({'answersSha256':sha('answers.json'),'truthSha256':sha('truth.json'),'lockedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2))
