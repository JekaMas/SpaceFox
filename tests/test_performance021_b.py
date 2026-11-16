import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from unittest.mock import patch

from tools.spacefox.cloud import CloudError, Site


class GroupBTest(unittest.TestCase):
    def test_readback_overlap_and_refusal(self):
        files = {'feed.json': b'root', **{f'file{i}.txt': f'actual-{i}'.encode() for i in range(8)}}
        state = {'active': 0, 'peak': 0, 'gets': 0, 'posts': 0, 'mode': 'valid', 'roots': 0}
        lock = threading.Lock()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_POST(self):
                with lock: state['posts'] += 1
                self.send_error(405)
            def do_GET(self):
                name = self.path[1:]
                with lock:
                    state['gets'] += 1
                    if name == 'feed.json': state['roots'] += 1
                    state['active'] += 1
                    state['peak'] = max(state['peak'], state['active'])
                try:
                    if name != 'feed.json': time.sleep(.2)
                    body = files[name]
                    if state['mode'] == 'corrupt' and name == 'file3.txt': body = b'corrupt!'
                    if state['mode'] == 'race' and name == 'feed.json' and state['roots'] == 2: body = b'other'
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.send_header('Content-Length', str(len(body)))
                    self.end_headers()
                    self.wfile.write(body[:-1] if state['mode'] == 'partial' and name == 'file3.txt' else body)
                finally:
                    with lock: state['active'] -= 1
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        self.addCleanup(worker.join)
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        site = Site(f'http://127.0.0.1:{server.server_port}', local_http=True)
        pub = SimpleNamespace(ledger={'active': {'generation': 1, 'artifact_revision': 'a' * 64}, 'pending': None}, store=None, head=None)
        with patch('tools.spacefox.cloud.snapshot_files', return_value=(None, files)):
            start = time.monotonic()
            for name, raw in files.items(): self.assertEqual(site.get(name, len(raw)), (200, raw))
            baseline = time.monotonic() - start
            state.update(peak=0, gets=0, roots=0)
            start = time.monotonic(); result = site.observe(pub); elapsed = time.monotonic()-start
            print(f'local readback baseline={baseline:.3f}s concurrent={elapsed:.3f}s requests={state["gets"]} peak={state["peak"]}')
            self.assertEqual(result.generation, 1)
            self.assertEqual(state['gets'], 10)
            self.assertGreater(state['peak'], 1)
            self.assertLessEqual(state['peak'], 4)
            for mode in ('corrupt', 'partial', 'race'):
                state.update(mode=mode, roots=0)
                with self.assertRaises(CloudError): site.observe(pub)
                self.assertEqual(state['posts'], 0)

    def test_operator_http_deadline_and_bounds(self):
        import tempfile
        from pathlib import Path
        from tools import display_corpus, verify_native_text_http
        from tools.spacefox import catalog
        workers = []
        real_popen = catalog.subprocess.Popen
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                self.send_response(200); self.send_header('Content-Type', 'text/plain'); self.end_headers()
                try:
                    if self.path == '/oversize': self.wfile.write(b'x' * 128); return
                    for _ in range(20):
                        self.wfile.write(b'x'); self.wfile.flush(); time.sleep(.1)
                except (BrokenPipeError, ConnectionResetError): pass
        server=ThreadingHTTPServer(('127.0.0.1',0), Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(thread.join);self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        base=f'http://127.0.0.1:{server.server_port}'
        def capture(*args, **kwargs):
            p=real_popen(*args,**kwargs); workers.append(p);return p
        with patch.object(catalog.subprocess,'Popen',side_effect=capture), patch.object(display_corpus,'HTTP_TOTAL_SECONDS',.5), patch.object(verify_native_text_http,'HTTP_TOTAL_SECONDS',.5):
            start=time.monotonic()
            with self.assertRaises(ValueError):display_corpus.http_get(base+'/slow')
            self.assertLess(time.monotonic()-start,1.5)
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);(root/'feed.json').write_bytes(b'x'*30);(root/'feed.json.txt').write_bytes(b'x'*30)
                start=time.monotonic();record=verify_native_text_http.verify(root,base,local_http=True)
                self.assertLess(time.monotonic()-start,1.5);self.assertEqual(record['status'],'failed')
            with patch.object(display_corpus,'MAX_BYTES',10):
                with self.assertRaises(ValueError): display_corpus.http_get(base+'/oversize')
            self.assertTrue(workers);self.assertTrue(all(p.poll() is not None for p in workers))

    def test_git_deadline(self):
        import tempfile
        from tools.spacefox import publisher
        with tempfile.TemporaryDirectory() as tmp:
            store=publisher.GitState(tmp)
            try:
                with patch.object(publisher,'GIT_TOTAL_SECONDS',.3):
                    start=time.monotonic()
                    with self.assertRaisesRegex(publisher.StateError,'deadline'):
                        store._git('-c','alias.slow=!sleep 20','slow')
                    self.assertLess(time.monotonic()-start,1.5)
                self.assertEqual(store._git('rev-parse','--is-bare-repository').stdout,b'true\n')
            finally: store.close()

    def test_git_batch_exact_identity(self):
        import subprocess, tempfile
        from pathlib import Path
        from tools.spacefox import publisher, catalog
        with tempfile.TemporaryDirectory() as tmp:
            store=publisher.GitState(tmp)
            try:
                blob1=store._git('hash-object','-w','--stdin',data=b'one').stdout.strip().decode()
                blob2=store._git('hash-object','-w','--stdin',data=b'two').stdout.strip().decode()
                store._git('update-index','--add','--cacheinfo',f'100644,{blob1},a')
                store._git('update-index','--add','--cacheinfo',f'100644,{blob2},b')
                tree=store._git('write-tree').stdout.strip().decode()
                commit=store._git('commit-tree',tree,data=b'first\n').stdout.strip().decode()
                expected_sizes=[int(subprocess.check_output(['git','-C',store.path,'cat-file','-s',oid]))
                                for oid in (commit,tree,blob1,blob2)]
                self.assertEqual(store._history_sizes(commit),(4,sum(expected_sizes)))
                calls=[]; original=catalog._run_bounded_child
                def counted(*args,**kwargs):
                    calls.append(args[0]);return original(*args,**kwargs)
                with patch.object(catalog,'_run_bounded_child',side_effect=counted):
                    self.assertEqual(store._blobs(commit,{'a':3,'b':3}),{'a':b'one','b':b'two'})
                    self.assertEqual(store._blobs(commit,{'a':3,'b':3}),{'a':b'one','b':b'two'})
                    self.assertEqual(len(calls),1)
                    with self.assertRaises(publisher.StateError):store._blob(commit,'a',2)
                    with self.assertRaises(publisher.StateError):store._blob(commit,'missing',10)
                    self.assertEqual(len(calls),2)
                    print('git blob observation: 2 paths, first batch 1 process, repeated snapshot 0 processes, missing 1 process')
            finally: store.close()

    def test_readback_slow_body_reaps_children(self):
        import subprocess
        from tools.spacefox import cloud
        from types import SimpleNamespace
        requests=[];children=[]
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_GET(self):
                requests.append(('GET',self.path))
                data=b'root' if self.path=='/feed.json' else b'x'*32
                self.send_response(200);self.send_header('Content-Type','text/plain');self.send_header('Content-Length',str(len(data)));self.end_headers()
                try:
                    if self.path=='/feed.json': self.wfile.write(data);return
                    for byte in data:
                        self.wfile.write(bytes([byte]));self.wfile.flush();time.sleep(.1)
                except (BrokenPipeError,ConnectionResetError): pass
            def do_POST(self):
                requests.append(('POST',self.path));self.send_error(405)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(thread.join);self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        site=Site(f'http://127.0.0.1:{server.server_port}',local_http=True)
        files={'feed.json':b'root',**{f'f{i}.txt':b'x'*32 for i in range(4)}}
        pub=SimpleNamespace(ledger={'active':{'generation':1,'artifact_revision':'a'*64},'pending':None},store=None,head=None)
        run=subprocess.run; popen=subprocess.Popen
        def short_run(*args,**kwargs):
            kwargs['timeout']=.5
            return run(*args,**kwargs)
        def capture(*args,**kwargs):
            child=popen(*args,**kwargs);children.append(child);return child
        with patch('tools.spacefox.cloud.snapshot_files',return_value=(None,files)), patch.object(cloud.subprocess,'run',side_effect=short_run), patch.object(cloud.subprocess,'Popen',side_effect=capture), patch.object(cloud,'READBACK_DEADLINE_SECONDS',.2):
            start=time.monotonic()
            with self.assertRaisesRegex(CloudError,'complete closure observation deadline exceeded'):site.observe(pub)
            self.assertLess(time.monotonic()-start,2)
        self.assertGreaterEqual(len(children),2)
        self.assertTrue(all(child.poll() is not None for child in children))
        self.assertTrue(requests);self.assertFalse(any(method=='POST' for method,_ in requests))

    def test_git_fetch_hang_reaps_transport(self):
        import os, tempfile
        from pathlib import Path
        from tools.spacefox import publisher
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); ssh=root/'ssh'; marker=root/'transport.pid'
            ssh.write_text('#!/bin/sh\nprintf "%s" "$$" > "$SPACEFOX_TEST_PID"\nexec sleep 30\n')
            ssh.chmod(0o755)
            store=publisher.GitState(str(root/'unused'))
            try:
                with patch.dict(os.environ,{'GIT_SSH_COMMAND':str(ssh),'SPACEFOX_TEST_PID':str(marker)}), patch.object(publisher,'GIT_TOTAL_SECONDS',.5):
                    with self.assertRaisesRegex(publisher.StateError,'deadline'):
                        store._git('fetch','--no-tags','-q','ssh://example.invalid/local/repo')
                self.assertTrue(marker.exists())
                pid=int(marker.read_text())
                try: os.kill(pid,0)
                except ProcessLookupError: pass
                else:
                    # A killed orphan can remain as a zombie until its parent reaps it.
                    status=Path(f'/proc/{pid}/stat')
                    if not status.exists() or status.read_text().split()[2] != 'Z':
                        self.fail('owned Git transport remains live')
            finally:store.close()

    def test_git_fresh_ref_and_fetch_reuse(self):
        import subprocess, tempfile
        from pathlib import Path
        from tools.spacefox import publisher
        def git(cwd,*args):
            return subprocess.check_output(['git','-C',str(cwd),*args]).decode().strip()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); remote=root/'remote.git';source=root/'source';source.mkdir()
            subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
            git(source,'init','-q');git(source,'config','user.name','local');git(source,'config','user.email','local@example.invalid')
            git(source,'commit','--allow-empty','-qm','source');code=git(source,'rev-parse','HEAD')
            git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
            store=publisher.GitState(str(remote))
            try:
                store.bootstrap(code)
                commands=[];original=store._git
                def observed(*args,**kwargs):commands.append(args[0]);return original(*args,**kwargs)
                with patch.object(store,'_git',side_effect=observed):
                    head,_=store.load();store.load()
                    self.assertEqual(commands.count('fetch'),1)
                    self.assertGreaterEqual(commands.count('ls-remote'),2)
                    store._git('update-ref','-d','refs/spacefox/state')
                    self.assertEqual(store.load()[0],head)
                    self.assertEqual(commands.count('fetch'),2)
                    git(remote,'update-ref','-d',publisher.STATE_REF,head)
                    with self.assertRaises(publisher.StateError):store.load()
                    self.assertEqual(commands.count('fetch'),2)
                    print('git reopen: 3 fresh remote observations, 1 unchanged-ref fetch; missing local ref forced second fetch; missing remote refused')
            finally:store.close()

    def test_git_catalog_object_above_artifact_limit(self):
        import tempfile
        from tools.spacefox import publisher
        with tempfile.TemporaryDirectory() as tmp:
            store=publisher.GitState(tmp)
            try:
                data=b'x'*(publisher.MAX_ARTIFACT_BYTES*2+1)
                oid=store._git('hash-object','-w','--stdin',data=data).stdout.strip().decode()
                store._git('update-index','--add','--cacheinfo',f'100644,{oid},catalog')
                tree=store._git('write-tree').stdout.strip().decode()
                commit=store._git('commit-tree',tree,data=b'large catalog\n').stdout.strip().decode()
                self.assertEqual(store._blob(commit,'catalog',publisher.MAX_CATALOG_OBJECT_BYTES),data)
                with self.assertRaises(publisher.StateError):store._blob(commit,'catalog',publisher.MAX_ARTIFACT_BYTES)
            finally:store.close()

    def test_real_artifact_readback_concurrency_and_corruption(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]/'openspec/changes/spacefox-watchface/evidence/current-native-scene-whole/profile-a'
        files={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
        self.assertEqual(len(files),106);self.assertEqual(sum(map(len,files.values())),606248)
        corrupt=next(name for name in files if name not in ('feed.json','feed.json.txt') and files[name])
        lock=threading.Lock();state={'gets':0,'active':0,'peak':0,'corrupt':False,'posts':0}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                with lock:state['posts']+=1
                self.send_error(405)
            def do_GET(self):
                from urllib.parse import unquote
                name=unquote(self.path[1:])
                with lock:
                    state['gets']+=1;state['active']+=1;state['peak']=max(state['peak'],state['active'])
                try:
                    if name!='feed.json':time.sleep(.02)
                    raw=files[name]
                    if state['corrupt'] and name==corrupt:raw=bytes([raw[0]^1])+raw[1:]
                    self.send_response(200);self.send_header('Content-Type','text/plain');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
                finally:
                    with lock:state['active']-=1
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(thread.join);self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        site=Site(f'http://127.0.0.1:{server.server_port}',local_http=True)
        pub=SimpleNamespace(ledger={'active':{'generation':1,'artifact_revision':'a'*64},'pending':None},store=None,head=None)
        with patch('tools.spacefox.cloud.snapshot_files',return_value=(None,files)):
            start=time.monotonic()
            for name,raw in files.items():self.assertEqual(site.get(name,len(raw)),(200,raw))
            baseline=time.monotonic()-start
            state.update(gets=0,peak=0);start=time.monotonic();site.observe(pub);elapsed=time.monotonic()-start
            self.assertEqual(state['gets'],107);self.assertGreater(state['peak'],1);self.assertLessEqual(state['peak'],4)
            print(f'real artifact: 106 files 606248 bytes, serial {baseline:.3f}s concurrent {elapsed:.3f}s, 107 GET, peak {state["peak"]}')
            state['corrupt']=True
            with self.assertRaises(CloudError):site.observe(pub)
            self.assertEqual(state['posts'],0)

    def test_operator_empty_content_encoding_rejected(self):
        import tempfile
        from pathlib import Path
        from tools import verify_native_text_http
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                self.send_response(200);self.send_header('Content-Type','text/plain');self.send_header('Content-Encoding','');self.end_headers();self.wfile.write(b'abc')
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(thread.join);self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'feed.json').write_bytes(b'abc');(root/'feed.json.txt').write_bytes(b'abc')
            result=verify_native_text_http.verify(root,f'http://127.0.0.1:{server.server_port}',local_http=True)
            self.assertEqual(result['status'],'failed');self.assertEqual(result['responses'][0]['contentEncoding'],'')

    def test_actual_catalog_midnight_disagreement_withholds_witness(self):
        from datetime import datetime, timezone, timedelta
        from pathlib import Path
        from tools.spacefox import native_motion
        now=datetime.now(timezone.utc)
        class Clock:
            calls=0
            @classmethod
            def now(cls,tz):
                cls.calls+=1
                return now if cls.calls==1 else now+timedelta(days=1)
        with patch.object(native_motion,'datetime',Clock):
            owner=native_motion._RepositoryCatalogOperation(Path(__file__).resolve().parents[1])
        self.assertEqual(Clock.calls,2)
        self.assertIsNone(owner.scheduling_date)
        self.assertEqual(len(owner.source_digest()),64)

    def test_metadata_due_and_staging_decision(self):
        from tools.refresh_catalog import metadata_not_due
        from tools.spacefox.publisher import StateError
        journal={'staging':None}; current={'source':{'completedUtc':1000}}
        self.assertTrue(metadata_not_due(journal,current,1001,86400))
        self.assertFalse(metadata_not_due(journal,current,87400,86400))
        self.assertFalse(metadata_not_due({'staging':{'pages':[]}},current,1001,86400))
        self.assertFalse(metadata_not_due(journal,None,1001,86400))
        with self.assertRaises(StateError):metadata_not_due(journal,current,999,86400)

    def test_cloud_sparse_source_fence_hidden_change(self):
        import subprocess,tempfile
        from pathlib import Path
        from tools.cloud_feed import _cloud_source_fence
        def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args]).decode().strip()
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for name,raw in {'.github/spacefox-inputs.txt':b'/.github/spacefox-inputs.txt\n/tools/cloud_feed.py\n/catalog/source.json\n','tools/cloud_feed.py':b'runtime\n','catalog/source.json':b'{}\n','assets/item.svg':b'<svg/>\n'}.items():
                path=root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
            git(root,'init','-q');git(root,'config','user.name','local');git(root,'config','user.email','local@example.invalid');git(root,'add','.');git(root,'commit','-qm','source')
            code=git(root,'rev-parse','HEAD')
            git(root,'update-index','--skip-worktree','catalog/source.json');(root/'catalog/source.json').unlink()
            self.assertTrue(_cloud_source_fence(root,code))
            git(root,'update-index','--assume-unchanged','assets/item.svg');(root/'assets/item.svg').write_bytes(b'changed')
            self.assertFalse(_cloud_source_fence(root,code))
            (root/'assets/item.svg').write_bytes(b'<svg/>\n');self.assertTrue(_cloud_source_fence(root,code))
            (root/'tools/cloud_feed.py').unlink();self.assertFalse(_cloud_source_fence(root,code))

    def test_probe_decision_unit_matrix(self):
        import hashlib,json
        from datetime import datetime,timezone
        from pathlib import Path
        from tools import cloud_feed
        from tools.spacefox import catalog_refresh, publisher
        from tools.spacefox.cloud import JOURNAL,SCHEDULING_WITNESS
        root=Path(__file__).resolve().parents[1]/'openspec/changes/spacefox-watchface/evidence/current-native-scene-whole/profile-a'
        feed_path=Path(__file__).resolve().parents[1]/'openspec/changes/spacefox-watchface/evidence/fields018/stock-final390/feed.json'
        raw_feed=feed_path.read_bytes();files={'feed.json':raw_feed,'feed.json.txt':raw_feed}
        feed=json.loads(raw_feed); head='a'*40;anchor='b'*40;code='c'*40;state='d'*40
        active={'generation':1,'code_revision':code,'artifact_revision':'e'*64,'files':{p:{'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for p,raw in files.items()}}
        now=int(datetime.now(timezone.utc).timestamp())
        witness={'schemaVersion':1,'date':datetime.now(timezone.utc).date().isoformat(),'source':code,'instance':'f'*64,'generation':1,'artifactRevision':'e'*64,'catalogSourceDigest':feed['catalogSourceDigest']}
        manifest={p:{**meta,'state':state,'generation':1,'role':'current'} for p,meta in active['files'].items()}
        intent={'buildVersion':state,'state':state,'generation':1,'artifactRevision':'e'*64,'source':code,'sourceRef':'refs/heads/main','repository':'local/spacefox','runId':1,'runAttempt':1,'artifactId':1}
        doc={'active':active,'pending':None,'code_revision':code,'instance_id':'f'*64,'accepted':{},'refresh_policy':{}}
        class Store:
            source_ref='refs/heads/main'
            def _load_authority(self,**kw):return head,doc
            def _git(self,*args,**kw):return SimpleNamespace(stdout=(anchor+'\n').encode())
            def _blob(self,rev,path,limit):
                return files['feed.json'] if path.endswith('/feed.json') else json.dumps(witness if path==SCHEDULING_WITNESS else {'schemaVersion':1,'intent':intent,'status':'succeed','files':manifest}).encode()
            def _ledger_at(self,revision):return {'active':active,'pending':None}
            def definitely_not_due(self,*args):return True
            def _refs(self,*args):return {publisher.STATE_REF:head,publisher.ANCHOR_REF:anchor,self.source_ref:code}
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                body=files['feed.json'];self.send_response(200);self.end_headers();self.wfile.write(body)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(thread.join);self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        site=Site(f'http://127.0.0.1:{server.server_port}',local_http=True);collector=SimpleNamespace(journal={'staging':None},current=lambda:{'source':{'completedUtc':now}})
        with patch.object(catalog_refresh,'CatalogRefresh',return_value=collector),patch.object(cloud_feed,'_cloud_source_fence',return_value=True),patch.object(cloud_feed,'_projection_changed',return_value=False),patch.object(cloud_feed,'_schedule',return_value=None),patch.object(cloud_feed,'RefreshPolicy',return_value=None):
            def observe():return cloud_feed._scheduling_no_work(Store(),site,code,'local/spacefox',now,root=root)
            self.assertEqual(observe(),head)
            witness['date']='2000-01-01';self.assertIsNone(observe());witness['date']=datetime.now(timezone.utc).date().isoformat()
            collector.journal['staging']={'pages':[]};self.assertIsNone(observe());collector.journal['staging']=None
            collector.current=lambda:{'source':{'completedUtc':now-86400}};self.assertIsNone(observe())
            doc['pending']=active;self.assertIsNone(observe())

    def test_readback_sequence_independent_oracle(self):
        from pathlib import Path
        from urllib.parse import unquote
        root=Path(__file__).resolve().parents[1]/'openspec/changes/spacefox-watchface/evidence/current-native-scene-whole/profile-a'
        files={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
        corrupt=next(p for p,b in files.items() if p not in ('feed.json','feed.json.txt') and b)
        state={'event':'valid','gets':0,'roots':0,'posts':0};lock=threading.Lock()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                with lock:state['posts']+=1
                self.send_error(405)
            def do_GET(self):
                name=unquote(self.path[1:])
                with lock:
                    state['gets']+=1
                    if name=='feed.json':state['roots']+=1
                    roots=state['roots'];event=state['event']
                raw=files[name]
                if event=='corrupt' and name==corrupt:raw=bytes([raw[0]^1])+raw[1:]
                if event=='race' and name=='feed.json' and roots>1:raw=b'{}'
                self.send_response(200);self.send_header('Content-Type','text/plain');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(thread.join);self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        site=Site(f'http://127.0.0.1:{server.server_port}',local_http=True)
        pub=SimpleNamespace(ledger={'active':{'generation':1,'artifact_revision':'a'*64},'pending':None},store=None,head=None)
        # The model is independent of the SUT: these are event contracts and
        # expected observable outcomes, not values obtained from Site.
        events=[('valid','accept',107),('corrupt','reject',None),('race','reject',107),('restored','accept',107)]
        required={(event,'observed_no_mutation') for event,_,_ in events};seen=set()
        with patch('tools.spacefox.cloud.snapshot_files',return_value=(None,files)):
            for index,(event,expected,exact_gets) in enumerate(events):
                state.update(event='valid' if event=='restored' else event,gets=0,roots=0)
                try:
                    result=site.observe(pub);observed='accept'
                    self.assertEqual((result.generation,result.artifact_revision),(1,'a'*64))
                except CloudError:
                    observed='reject'
                self.assertEqual(observed,expected,(index,event))
                self.assertEqual(state['posts'],0,(index,event))
                self.assertGreater(state['gets'],0,(index,event));self.assertLessEqual(state['gets'],107,(index,event))
                if exact_gets is not None:self.assertEqual(state['gets'],exact_gets,(index,event))
                seen.add((event,'observed_no_mutation'))
        self.assertEqual(seen,required)

    def test_later_stage_fresh_admission_needs_renderer(self):
        import os,tempfile
        from pathlib import Path
        from tools.spacefox.native_motion import validate_artifact
        root=Path(__file__).resolve().parents[1]/'openspec/changes/spacefox-watchface/evidence/current-native-scene-whole/profile-a'
        files={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
        # Actual source-derived visual validation must run when this process has
        # no prior cache and no renderer; absence cannot be mistaken for admission.
        with tempfile.TemporaryDirectory() as path, patch.dict(os.environ,{'PATH':path}):
            with self.assertRaises((OSError,ValueError)):
                validate_artifact(files)
        self.assertEqual(validate_artifact(files)['schemaVersion'],3)

    def test_cancelled_readback_reaps_http_workers(self):
        import os,signal,subprocess,sys,tempfile
        from pathlib import Path
        from urllib.parse import unquote
        root=Path(__file__).resolve().parents[1]/'openspec/changes/spacefox-watchface/evidence/current-native-scene-whole/profile-a'
        files={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}
        state={'content':0,'posts':0};lock=threading.Lock()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                with lock:state['posts']+=1
                self.send_error(405)
            def do_GET(self):
                name=unquote(self.path[1:]);raw=files[name]
                self.send_response(200);self.send_header('Content-Type','text/plain');self.send_header('Content-Length',str(len(raw)));self.end_headers()
                if name!='feed.json':
                    with lock:state['content']+=1
                    time.sleep(2)
                try:self.wfile.write(raw)
                except (BrokenPipeError,ConnectionResetError):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(thread.join);self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        script='''import os,sys\nfrom pathlib import Path\nfrom types import SimpleNamespace\nfrom tools.spacefox import cloud\nroot=Path(sys.argv[1]);files={p.relative_to(root).as_posix():p.read_bytes() for p in root.rglob('*') if p.is_file()}\ncloud.snapshot_files=lambda *args:(None,files)\noriginal=cloud.subprocess.Popen\ndef spawn(*args,**kwargs):\n p=original(*args,**kwargs)\n fd=os.open(sys.argv[3],os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600);os.write(fd,(str(p.pid)+"\\n").encode());os.close(fd)\n return p\ncloud.subprocess.Popen=spawn\npub=SimpleNamespace(ledger={'active':{'generation':1,'artifact_revision':'a'*64},'pending':None},store=None,head=None)\ntry:cloud.Site(sys.argv[2],local_http=True).observe(pub)\nexcept KeyboardInterrupt:print('cancelled',flush=True);sys.exit(130)\n'''
        with tempfile.TemporaryDirectory() as tmp:
            pidfile=Path(tmp)/'children';proc=subprocess.Popen([sys.executable,'-B','-c',script,str(root),f'http://127.0.0.1:{server.server_port}',str(pidfile)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
            try:
                deadline=time.monotonic()+8
                while time.monotonic()<deadline:
                    with lock:active=state['content']
                    if active>=2:break
                    if proc.poll() is not None:self.fail('readback stopped before cancellation')
                    time.sleep(.02)
                else:self.fail('readback did not reach concurrent content')
                os.kill(proc.pid,signal.SIGINT)
                stdout,stderr=proc.communicate(timeout=8)
                self.assertEqual(proc.returncode,130,stderr);self.assertIn('cancelled',stdout)
                children=[int(value) for value in pidfile.read_text().splitlines()]
                self.assertGreaterEqual(len(children),3)
                for pid in children:
                    try:os.kill(pid,0)
                    except ProcessLookupError:continue
                    self.fail(f'HTTP worker {pid} remains alive after cancellation')
                self.assertEqual(state['posts'],0)
            finally:
                if proc.poll() is None:proc.kill();proc.communicate()

    def test_git_large_duplex_batch_uses_file_input(self):
        import hashlib,tempfile
        from pathlib import Path
        from tools.spacefox import publisher,catalog
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);store=publisher.GitState(tmp)
            try:
                large=b'L'*900000
                large_oid=store._git('hash-object','-w','--stdin',data=large).stdout.strip().decode()
                paths=[];expected={};names=[]
                for i in range(511):
                    content=f'actual-git-object-{i:04d}'.encode()
                    path=root/f'input-{i:04d}';path.write_bytes(content);paths.append(path)
                    name=f'{i+1:04d}'+('x'*220);names.append(name);expected[name]=content
                raw=store._git('hash-object','-w','--stdin-paths',data=b''.join(str(p).encode()+b'\n' for p in paths)).stdout
                oids=raw.decode().splitlines();self.assertEqual(len(set(oids)),511)
                first='0000'+('x'*220);expected={first:large,**expected}
                tree_lines=[f'100644 blob {large_oid}\t{first}\n']+[f'100644 blob {oid}\t{name}\n' for oid,name in zip(oids,names)]
                tree=store._git('mktree',data=''.join(tree_lines).encode()).stdout.strip().decode()
                commit=store._git('commit-tree',tree,data=b'bounded batch\n').stdout.strip().decode()
                request_bytes=sum(len(f'{commit}:{name}\n'.encode()) for name in expected)
                self.assertGreater(request_bytes,65536);self.assertEqual(len(expected),512)
                calls=[];actual=catalog._run_bounded_child
                def observe(*args,**kwargs):calls.append(args[0]);return actual(*args,**kwargs)
                with patch.object(catalog,'_run_bounded_child',side_effect=observe):
                    start=time.monotonic();result=store._blobs(commit,{name:len(data) for name,data in expected.items()});elapsed=time.monotonic()-start
                self.assertLess(elapsed,publisher.GIT_TOTAL_SECONDS)
                self.assertEqual(len(calls),1);self.assertEqual(len(result),512)
                self.assertEqual({name:hashlib.sha256(raw).digest() for name,raw in result.items()},
                                 {name:hashlib.sha256(raw).digest() for name,raw in expected.items()})
                print(f'real Git batch: 512 distinct objects, request {request_bytes} bytes, output {sum(map(len,result.values()))} bytes, one cat-file child, {elapsed:.3f}s')
            finally:store.close()

    def test_manifest_normalization_keeps_correct_bytes_and_repairs_extra_attributes(self):
        import tempfile
        from pathlib import Path
        from tools.build_native_localization import _write_manifest_languages
        source=Path(__file__).resolve().parents[1]/'watchface/manifest.xml'
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'manifest.xml';original=source.read_bytes();target.write_bytes(original)
            _write_manifest_languages(target,['eng','rus','deu','fre','spa'])
            self.assertEqual(target.read_bytes(),original)
            changed=original.replace(b'<iq:language>eng</iq:language>',b'<iq:language unexpected="1">eng</iq:language>',1)
            self.assertNotEqual(changed,original);target.write_bytes(changed)
            _write_manifest_languages(target,['eng','rus','deu','fre','spa'])
            self.assertNotIn(b'unexpected',target.read_bytes())
