"""Physical -400 regression boundary: exact bytes, HTTP MIME and durable closure.

Local standard-library HTTP and real Git only; no phone/Pages acceptance claim.
"""
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
from threading import Thread
import unittest
from urllib.request import urlopen

from tools.spacefox.cloud import HTTP, CloudError
from tools.spacefox.native_motion import native_transport_paths, with_text_transport, validate_artifact

ROOT = Path(__file__).resolve().parents[1]
PROFILE = ROOT/'openspec/changes/spacefox-watchface/evidence/site-flag-visual-batch/native-artifact'

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *args): pass

class PhoneTextTransportTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = {str(p.relative_to(PROFILE)):p.read_bytes() for p in PROFILE.rglob('*') if p.is_file()}
        cls.original = {p:b for p,b in cls.original.items() if not p.endswith('.txt')}
        cls.files = with_text_transport(cls.original)

    def test_exact_native_closure_preserves_all_original_bytes_and_hashes(self):
        validate_artifact(self.files)
        self.assertEqual({p:b for p,b in self.files.items() if not p.endswith('.txt')}, self.original)
        feed=json.loads(self.original['feed.json']); index=json.loads(self.original[feed['nativeTransfer']['path']])
        expected={'feed.json',feed['catalogPath'],feed['nativeTransfer']['path']}
        expected.update(('rasters/' if kind else 'descriptors/')+digest+('.sfr' if kind else '.json') for kind,digest,size in index['objects'])
        self.assertEqual(native_transport_paths(self.original),expected)
        self.assertEqual(set(self.files)-set(self.original), {p+'.txt' for p in expected})
        for p in expected:
            self.assertEqual(self.files[p+'.txt'],self.original[p])
            self.assertEqual(hashlib.sha256(self.files[p+'.txt']).digest(),hashlib.sha256(self.original[p]).digest())
        self.assertLessEqual(len(self.files),256);self.assertLessEqual(sum(map(len,self.files.values())),1048576)
        self.assertEqual(with_text_transport(self.files),self.files)

    def test_partial_stale_extra_and_corrupt_sidecars_refuse(self):
        names=sorted(p for p in self.files if p.endswith('.txt'))
        for change in ('missing','corrupt','extra'):
            files=dict(self.files)
            if change=='missing':del files[names[0]]
            elif change=='corrupt':files['feed.json.txt']+=b' '
            else:files['not-native.json.txt']=b'{}'
            with self.subTest(change=change), self.assertRaises(ValueError):validate_artifact(files)

    def test_actual_http_plain_mime_raw_body_and_wrong_mime_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            for name,raw in self.files.items():
                p=path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=tmp))
            thread=Thread(target=server.serve_forever,daemon=True);thread.start()
            base=f'http://127.0.0.1:{server.server_port}/'
            try:
                for name in sorted(p for p in self.files if p.endswith('.txt')):
                    with urlopen(base+name) as response:
                        self.assertEqual(response.headers.get_content_type(),'text/plain')
                        self.assertEqual(response.read(),self.files[name])
                status,raw=HTTP().request('GET',base+'feed.json.txt',limit=8192)
                self.assertEqual((status,raw),(200,self.original['feed.json']))
                class WrongMime(QuietHandler):
                    def guess_type(self,path):return 'application/json'
                wrong=ThreadingHTTPServer(('127.0.0.1',0),partial(WrongMime,directory=tmp))
                wt=Thread(target=wrong.serve_forever,daemon=True);wt.start()
                try:
                    with self.assertRaises(CloudError):HTTP().request('GET',f'http://127.0.0.1:{wrong.server_port}/feed.json.txt',limit=8192)
                finally:wrong.shutdown();wrong.server_close();wt.join()
            finally:server.shutdown();server.server_close();thread.join()

    def test_final_mutable_metadata_is_mirrored_without_freshness_reset(self):
        # Technical metadata mutation of retained real content, not new launch text.
        from tools.spacefox.catalog import canonical_bytes
        files=dict(self.original);feed=json.loads(files['feed.json']);age=feed['launch']['source_validated_utc']
        feed['publisher']['generation']+=1;files['feed.json']=canonical_bytes(feed)
        after=with_text_transport(files)
        self.assertEqual(after['feed.json.txt'],files['feed.json'])
        self.assertEqual(json.loads(after['feed.json.txt'])['launch']['source_validated_utc'],age)
        self.assertEqual({p:b for p,b in after.items() if p not in ('feed.json','feed.json.txt') and not p.endswith('.txt')},{p:b for p,b in self.original.items() if p!='feed.json'})

    def test_protected_pre_sidecar_snapshot_has_bounded_byte_identical_retained_copies(self):
        from tools.spacefox.cloud import retained_files
        before={p:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for p,b in self.original.items()}
        prior=retained_files({'files':before},self.original,text_transport=True)
        expected=native_transport_paths(self.original)-{'feed.json'}
        self.assertEqual(set(prior), (set(self.original)-{'feed.json'})|{p+'.txt' for p in expected})
        for name in expected:self.assertEqual(prior[name+'.txt'],before[name])
        self.assertNotIn('feed.json.txt',prior)
        self.assertEqual(retained_files({'files':before},self.original,text_transport=False),{p:m for p,m in before.items() if p!='feed.json'})

    def test_transport_only_prepare_uses_saved_source_without_provider_or_quota(self):
        import subprocess
        from unittest.mock import patch
        from tests.test_current_motion_publisher import git, NOW
        from tools.cloud_feed import prepare_content
        from tools.spacefox.catalog import build_catalog
        from tools.spacefox.native_motion import build_artifact, PROFILE
        from tools.spacefox.publisher import GitState, Publisher
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);remote=path/'remote.git';source=path/'source';source.mkdir()
            subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
            git(source,'init','-q');git(source,'config','user.name','Local qualification');git(source,'config','user.email','local@example.invalid');git(source,'commit','--allow-empty','-qm','source')
            code=git(source,'rev-parse','HEAD');git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
            store=GitState(str(remote))
            try:
                store.bootstrap(code);pub=Publisher(store,code);pub.reconcile(None);catalog=build_catalog(ROOT)
                with patch('tools.spacefox.native_motion.with_text_transport',lambda files:files):
                    old,digest=build_artifact(pub.schedule,catalog,NOW,publisher=pub.publisher_envelope(NOW),root=ROOT)
                    revision=pub.prepare(pub.head,NOW,old,digest,artifact_profile=PROFILE)
                pub.reconcile(revision);before=pub.ledger
                class ForbiddenProvider:
                    def __getattr__(self,name):raise AssertionError('transport-only provider access '+name)
                result=prepare_content(pub,ForbiddenProvider(),NOW+1,catalog,root=ROOT)
                self.assertEqual((result['result'],result['requests']),('content_pending',0))
                after=Publisher(store,code);new=after.pending_files()
                self.assertEqual(new['feed.json.txt'],new['feed.json'])
                self.assertEqual(after.ledger['accepted']['entries'],before['accepted']['entries'])
                self.assertEqual(after.ledger['accepted']['evaluated_at_utc'],NOW+1)
                for key in ('requests','selection_validated_utc','last_poll_utc'):
                    self.assertEqual(after.ledger[key],before[key])
                self.assertEqual(json.loads(new['feed.json'])['providerTraversal'],json.loads(old['feed.json'])['providerTraversal'])
            finally:store.close()
