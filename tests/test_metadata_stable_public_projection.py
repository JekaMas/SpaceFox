"""Actual public cloud CLI with ordered metadata; no live LL2."""
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from tests.test_catalog_refresh import git
from tests.test_cloud_delivery import World
from tests.test_metadata_page_policy import source_server, suffix
from tools.spacefox.catalog_refresh import CatalogRefresh
from tools.spacefox.publisher import GitState, Publisher

ROOT = Path(__file__).resolve().parents[1]

class StablePublicProjectionTest(unittest.TestCase):
    def test_public_cloud_cli_migrates_and_finishes(self):
        self.assertEqual('', git(ROOT, 'status', '--porcelain'))
        code = git(ROOT, 'rev-parse', 'HEAD')
        with tempfile.TemporaryDirectory(prefix='spacefox-stable-public-') as folder:
            remote = Path(folder) / 'remote.git'
            subprocess.run(['git','clone','--bare','--no-hardlinks','-q',str(ROOT),str(remote)],check=True)
            git(remote, 'update-ref', 'refs/heads/main', code)
            store, world = GitState(str(remote)), World(remote)
            try:
                store.bootstrap(code)
                pub = Publisher(store, code); pub.reconcile(None)
                token = pub.reserve(pub.head, 1000, trigger='manual')
                pub.accept_source(pub.head, token, (), 1000)
                with source_server(remote,counts=dict(countries=1,organizations=1,models=1,sites=2)) as (state,_,origin):
                    old = CatalogRefresh(pub, origin=origin, local_http=True, page_size=1)
                    self.assertEqual('partial',old.run(1001,max_requests=4).status)
                    prefix, accepted = deepcopy(old.journal['staging']['pages']), deepcopy(pub.ledger['accepted'])
                    git(remote,'update-ref','refs/heads/main',code)
                    def cli(command, now):
                        argv=[sys.executable,'-B',str(ROOT/'tools/cloud_feed.py'),'--repository','local/SpaceFox',
                              '--remote',str(remote),'--site',world.base+'/site','--api',world.base,
                              '--origin',origin,'--local-qualification','--now',str(now),command]
                        env={k:v for k,v in os.environ.items() if not k.startswith('GITHUB_') and k not in ('GH_TOKEN','PYTHONPATH')}
                        result=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,timeout=90)
                        self.assertEqual(0,result.returncode,result.stderr)
                        return json.loads(result.stdout)
                    cli('recover',1002)
                    state['now']=1002
                    answer=cli('metadata',1002)
                    self.assertEqual(('complete',2),(answer['status'],answer['requests']))
                    self.assertEqual([(suffix(3,1,0,True),None),(suffix(3,1,1,True),None)],state['calls'][-2:])
                    pub=Publisher(store,code); pub.reconcile(None)
                    c=CatalogRefresh(pub,origin=origin,local_http=True,stable_sites_order=True)
                    self.assertEqual(prefix[:3],c.current()['coverage']['pages'][:3])
                    self.assertEqual(dict(countries=1,organizations=1,models=1,sites=2),c.current()['coverage']['counts'])
                    self.assertEqual('id',c.current()['queryPolicy']['sitesOrdering'])
                    self.assertEqual(accepted,pub.ledger['accepted'])
            finally:
                world.close(); store.close()
