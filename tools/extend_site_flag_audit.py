"""Add newly discovered no-point source sites without rerunning valid maps."""
import hashlib,json
from pathlib import Path
from PIL import Image
from tools.audit_site_flag_batch import audit,ROOT
from tools.audit_site_flag_visuals import sheet
from tools.spacefox.catalog import build_catalog,loads_json
from tools.spacefox.bridge_map import build_map

OUT=ROOT/'openspec/changes/spacefox-watchface/evidence/site-flag-visual-batch'
OLD=OUT/'before-supplement'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
 prior=json.loads((OLD/'source-pixel-audit.json').read_text());inv=audit();catalog=build_catalog(ROOT)
 if prior['catalogVersion']!=catalog['catalogVersion'] or prior['inventory']['modelsCurrentOrEventReferenced']!=inv['modelsCurrentOrEventReferenced']:
  raise ValueError('model source changed; cannot retain prior pixels')
 oldmaps={r['id']:r for r in prior['maps']};oldsites={r['id']:r for r in prior['inventory']['eventAndAnnouncedSites']};newsites={r['id']:r for r in inv['eventAndAnnouncedSites']}
 if not set(oldsites)<=set(newsites) or any(newsites[k]!=v for k,v in oldsites.items()):raise ValueError('previous site data changed')
 newids=sorted(set(newsites)-set(oldsites));image=Image.open(OLD/'sites-contact.png').convert('RGB');oldtiles={}
 for i,r in enumerate(prior['maps']):
  x=(i%6)*130;y=(i//6)*165;oldtiles[r['id']]=image.crop((x,y,x+130,y+127))
 additions={}
 for identity in newids:
  files={};ref=build_map(ROOT,catalog,identity,files);d=loads_json(files[ref['path']])
  if d['position'] is not None or d['marker'] is not None:raise ValueError('new source site is not no-point')
  additions[identity]={'id':identity,'position':None,'reason':d['contextLimits']}
 maps=[oldmaps.get(k) or additions[k] for k in sorted(newsites)]
 rows=[(r['id']+(' NO POINT' if r['position'] is None else ''),oldtiles.get(r['id'])) for r in maps]
 result=dict(prior);result['inventory']=inv;result['maps']=maps;result['sheets']=dict(prior['sheets']);result['sheets']['sites']=sheet(rows,6,(130,165),'sites-contact.png')
 result['reuse']={'priorAudit':str((OLD/'source-pixel-audit.json').relative_to(ROOT)),'priorAuditSha256':sha(OLD/'source-pixel-audit.json'),'priorSitesSheetSha256':sha(OLD/'sites-contact.png'),'newNoPointSiteIds':newids,'boundary':'Retained prior per-site pixels and added only source-proven no-point sites.'}
 (OUT/'source-pixel-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
 print('retained maps',len(oldmaps),'new no-point',newids)
if __name__=='__main__':main()
