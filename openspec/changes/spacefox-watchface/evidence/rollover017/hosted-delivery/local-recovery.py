import json
from pathlib import Path
from tools.spacefox.publisher import GitState, Publisher
import tools.spacefox.cloud as cloud
from tools.spacefox.cloud import delivery, delivery_files, journal, recover, arm, deploy, Site
from tools.cloud_feed import prepare_content
from tools.spacefox.catalog import build_catalog

remote='/Users/jekamas/.codex/tmp/spacefox-rollover017-replay-20261116.git'
code='bc744093d9f2546461de8a353361e8a2e2f71734'
root=Path('/Users/jekamas/projects/SpaceFox-worktrees/rollover017-hosted-delivery-20261116')
class LocalSite(Site):
    def __init__(self,files): self.files=files
    def get(self,path,limit):
        value=self.files.get(path)
        return (200,value) if value is not None and len(value)<=limit else (404,b'')
class LocalPages:
    repository='JekaMas/SpaceFox'
    def __init__(self,site): self.site=site;self.next=None;self.posts=0
    def create(self,intent,token): self.posts+=1;self.site.files=self.next
    def wait(self,*args,**kwargs): return 'succeed'
class Forbidden:
    def __getattr__(self,name): raise AssertionError('provider forbidden: '+name)
s=GitState(remote)
try:
 p=Publisher(s,code);p.adopt_code(p.head)
 before=p.ledger; old=journal(p)
 site=LocalSite(delivery_files(p,old['files']));pages=LocalPages(site)
 p=recover(p,site,pages)
 files=delivery_files(p,delivery(p))
 print('local 49 union',len(files),sum(map(len,files.values())),flush=True)
 p,intent=arm(p,expected=p.head,repository=pages.repository,run_id=1,run_attempt=1,artifact_id=1,now=p.ledger['last_event_utc'])
 pages.next=files
 assert deploy(p,pages,site,expected=p.head,repository=pages.repository,run_id=1,run_attempt=1,id_token='local-only')=='succeed'
 p=recover(p,site,pages)
 assert p.ledger['active']['generation']==49 and p.ledger['pending'] is None
 assert p.ledger['requests']==before['requests'] and p.ledger['selection_validated_utc']==before['selection_validated_utc']
 now=p.ledger['last_event_utc']+1
 result=prepare_content(p,Forbidden(),now,build_catalog(root),root=root)
 print('next preparation',json.dumps(result,sort_keys=True),flush=True)
 nextfiles=delivery_files(p,delivery(p)); feed=json.loads(nextfiles['feed.json'])
 print('local 50 union',len(nextfiles),sum(map(len,nextfiles.values())),'upcoming',len(feed.get('upcoming',[])),'posts',pages.posts,flush=True)
 assert p.ledger['requests']==before['requests'] and p.ledger['selection_validated_utc']==before['selection_validated_utc']
finally:s.close()
