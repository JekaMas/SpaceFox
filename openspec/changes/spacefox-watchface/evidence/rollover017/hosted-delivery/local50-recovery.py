import json
from tools.spacefox.publisher import GitState,Publisher
from tools.spacefox.cloud import Site,arm,delivery,delivery_files,deploy,journal,recover
remote='/Users/jekamas/.codex/tmp/spacefox-rollover017-replay-20261116.git'
code='bc744093d9f2546461de8a353361e8a2e2f71734'
class LocalSite(Site):
 def __init__(self,files): self.files=files
 def get(self,path,limit):
  raw=self.files.get(path)
  return (200,raw) if raw is not None and len(raw)<=limit else (404,b'')
class LocalPages:
 repository='JekaMas/SpaceFox'
 def __init__(self,site,files): self.site,self.files,self.posts=site,files,0
 def create(self,intent,token): self.posts+=1;self.site.files=self.files
 def wait(self,*args,**kwargs): return 'succeed'
s=GitState(remote)
try:
 p=Publisher(s,code); before=p.ledger
 assert (before['active']['generation'],before['pending']['generation'])==(49,50)
 old=journal(p);site=LocalSite(delivery_files(p,old['files']))
 files=delivery_files(p,delivery(p)); feed=json.loads(files['feed.json'])
 assert len(feed['upcoming'])==2
 pages=LocalPages(site,files)
 p,intent=arm(p,expected=p.head,repository=pages.repository,run_id=2,run_attempt=1,artifact_id=2,now=before['last_event_utc'])
 assert deploy(p,pages,site,expected=p.head,repository=pages.repository,run_id=2,run_attempt=1,id_token='local')=='succeed'
 p=recover(p,site,pages)
 assert p.ledger['active']['generation']==50 and p.ledger['pending'] is None
 assert p.ledger['selection_validated_utc']==before['selection_validated_utc'] and p.ledger['requests']==before['requests']
 assert site.observe(p).generation==50
 print('local generation 50 promoted and exact read back:',len(files),'files',sum(map(len,files.values())),'bytes',len(feed['upcoming']),'upcoming,',pages.posts,'simulated POST, source epoch and quota unchanged',flush=True)
finally:s.close()
