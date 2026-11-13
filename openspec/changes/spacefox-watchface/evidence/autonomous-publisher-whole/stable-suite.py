"""Whole current publisher: real sparse Git, CLI and anonymous loopback HTTP.

No external provider, Pages, OIDC, SDK or account is contacted. Source launch and
metadata strings come from captured real records; only pagination, times and
technical faults are controlled. HTTP service answers and OIDC are the only
replaced boundaries. Runtime open/process observers fail on source/build use.
"""
from contextlib import contextmanager
from copy import deepcopy
from email.utils import formatdate
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import urlsplit

from tests.test_basic_publisher_clock import current_source_closure
from tests.test_current_motion_publisher import captured_starship, NOW
from tests.test_current_metadata_publisher import captured
from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.cloud import (CloudError, DeploymentStatusEmpty, Pages, Site,
    arm, delivery, delivery_files, journal, recover, snapshot_files)
from tools.spacefox.native_motion import PROFILE, build_artifact, validate_artifact
from tools.spacefox.provider import normalize_launch
from tools.spacefox.publisher import (Conflict, GitState, LiveRevision, Publisher,
    STATE_REF, StateError, _canonical, _sha, _catalog_ref)
from tools.spacefox.catalog_refresh import CatalogRefresh, RefreshError
from tools.spacefox.schedule import RefreshPolicy, ScheduleState, merge_schedule
from tools.refresh_catalog import scheduled

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (ROOT / '.github/workflows/update-feed.yml').read_text()


def git(root, *args, data=None):
    return subprocess.run(['git', '-C', str(root), *args], input=data, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout


def shell_step(name):
    # Read the checked-in shell itself, not a reimplemented materializer recipe.
    match = re.search(r'      - name: ' + re.escape(name) + r'\n(?:[^\n]*\n)*?        run: \|\n((?:          [^\n]*\n)+)', WORKFLOW)
    if match is None:
        raise AssertionError('workflow shell missing: ' + name)
    return '\n'.join(line[10:] for line in match[1].splitlines())


class Service:
    def __init__(self):
        self.files = {}
        self.calls = []
        self.statuses = ['succeed']
        self.status_code = 200
        self.run = None
        self.jobs = None
        self.version = None
        self.epoch = NOW
        self.mode304 = False
        self.bad_etag = False
        self.page_fault = None
        self.after_root = None
        self.root_reads = 0
        candidate, files = captured()
        self.metadata = {}
        for collection in ('countries', 'organizations', 'models', 'sites'):
            page = next(p for p in candidate['coverage']['pages'] if p['collection'] == collection)
            body = json.loads(files['objects/' + page['body']['sha256'] + '.json'])
            # Actual verbatim records. Pagination/count are technical controls;
            # this is not evidence of a newly observed complete LL2 catalog.
            self.metadata[collection] = _canonical(dict(count=1, next=None, previous=None, results=body['results'][:1]))
        self.primary = _canonical(dict(count=1, next=None, previous=None, results=[captured_starship()]))

    def answer(self, method, path, headers, body):
        self.calls.append((method, path, dict(headers), body))
        if path.startswith('/site/'):
            name = path[len('/site/'):]
            if name == 'feed.json':
                self.root_reads += 1
                if self.after_root and self.root_reads > 1:
                    return 200, self.after_root, {}
            raw = self.files.get(name)
            return (404, b'', {}) if raw is None else (200, raw, {})
        if '/actions/runs/' in path:
            value = self.jobs if '/jobs?' in path else self.run
            return (404, b'', {}) if value is None else (200, _canonical(value), {})
        if '/pages/deployments' in path:
            if method == 'POST':
                self.version = json.loads(body).get('pages_build_version', self.version)
                return 201, b'{}', {}
            value = self.statuses.pop(0) if len(self.statuses) > 1 else self.statuses[0]
            return self.status_code, _canonical(value if isinstance(value, dict) else dict(status=value)), {}
        if path.startswith('/2.3.0/launches/upcoming/'):
            return 200, self.primary, {'Date': formatdate(self.epoch, usegmt=True), 'Content-Type': 'application/json'}
        collection = next((c for c, route in dict(countries='config/countries', organizations='agencies',
            models='launcher_configurations', sites='pads').items() if path.startswith('/2.3.0/' + route + '/')), None)
        if collection:
            etag = '"' + collection + '"'
            h = {'Date': formatdate(self.epoch + 5, usegmt=True), 'Age': '5', 'ETag': etag, 'Content-Type': 'application/json'}
            if self.page_fault:
                return self.page_fault, b'', h
            if self.mode304 and headers.get('If-None-Match') == etag:
                if self.bad_etag:
                    h['ETag'] = '"wrong-url-tag"'
                return 304, b'', h
            return 200, self.metadata[collection], h
        return 404, b'', {}

    @contextmanager
    def serving(self):
        service = self
        class Handler(BaseHTTPRequestHandler):
            def handle_request(self):
                body = self.rfile.read(int(self.headers.get('Content-Length', '0')))
                status, raw, headers = service.answer(self.command, self.path, self.headers, body)
                self.send_response_only(status)
                for key, value in headers.items(): self.send_header(key, value)
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                self.close_connection = True
            do_GET = handle_request
            do_POST = handle_request
            def log_message(self, *_): pass
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            self.url = f'http://127.0.0.1:{server.server_port}'
            yield self
        finally:
            server.shutdown(); server.server_close(); thread.join()

    def witness(self, intent):
        self.run = dict(id=intent['runId'], run_attempt=intent['runAttempt'], head_sha=intent['source'],
            head_branch='main', status='completed', event='workflow_dispatch', path='.github/workflows/update-feed.yml',
            repository=dict(full_name=intent['repository']))
        self.jobs = dict(total_count=1, jobs=[dict(name='deploy', run_id=intent['runId'], head_sha=intent['source'],
            status='completed', conclusion='skipped', steps=[])])


class AutonomousPublisherWholeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='spacefox-autonomous-whole-')
        cls.base = Path(cls.temporary.name); cls.fixture = cls.base / 'source'; cls.fixture.mkdir()
        cls.closure = current_source_closure()
        cls.seed = (ROOT / '.github/spacefox-inputs.txt').read_bytes()
        cls.runtime = {}
        for line in cls.seed.decode().splitlines():
            name = line.removeprefix('/')
            if (ROOT / name).is_file(): cls.runtime[name] = (ROOT / name).read_bytes()
        cls.sources = {**cls.runtime, **cls.closure,
            '.github/workflows/update-feed.yml': WORKFLOW.encode()}
        for name, raw in cls.sources.items():
            target = cls.fixture / name; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        git(cls.fixture, 'init', '-q'); git(cls.fixture, 'config', 'user.name', 'Current publisher test')
        git(cls.fixture, 'config', 'user.email', 'current@example.invalid'); git(cls.fixture, 'add', '.')
        git(cls.fixture, 'commit', '-qm', 'current source/runtime only')
        cls.code = git(cls.fixture, 'rev-parse', 'HEAD').decode().strip()
        cls.catalog = build_catalog(ROOT)
        state = merge_schedule(ScheduleState(), (normalize_launch(captured_starship(), NOW),), NOW)
        cls.template, cls.digest = build_artifact(state, cls.catalog, NOW,
            publisher=dict(instance='a'*64, generation=1, selectionValidatedUtc=NOW), root=ROOT)
        cls.serial = 0

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def checkout(self, runtime=False):
        type(self).serial += 1
        path = self.base / ('checkout-' + str(self.serial))
        git(self.base, 'clone', '-q', '--no-checkout', '--shared', str(self.fixture), str(path))
        git(path, 'config', 'user.name', 'Current publisher test'); git(path, 'config', 'user.email', 'current@example.invalid')
        git(path, 'sparse-checkout', 'init', '--no-cone')
        seed = self.seed.replace(b'/catalog/source.json\n', b'') if runtime else self.seed
        git(path, 'sparse-checkout', 'set', '--no-cone', '--stdin', data=seed)
        git(path, 'checkout', '-q')
        return path

    @contextmanager
    def authority(self, *, runtime=True, policy=None):
        source = self.checkout(runtime=runtime); remote = source.parent / (source.name + '.git')
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
        git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
        store = GitState(str(remote))
        try:
            store.bootstrap(self.code, policy or RefreshPolicy()); pub = Publisher(store, self.code); pub.reconcile(None)
            yield source, remote, store, pub
        finally: store.close()

    def accept(self, pub, now=NOW):
        token = pub.reserve(pub.head, now, trigger='manual')
        pub.accept_source(pub.head, token, (normalize_launch(captured_starship(), NOW),), now, selection_validated_utc=NOW)

    def candidate(self, pub, now=NOW):
        files = dict(self.template); feed = json.loads(files['feed.json'])
        feed['publisher'] = pub.publisher_envelope(now)
        files['feed.json'] = canonical_bytes(feed)
        validate_artifact(files)
        return files

    def prepare(self, pub, now=NOW):
        files = self.candidate(pub, now)
        revision = pub.prepare(pub.head, now, files, self.digest,
            feed_publisher=pub.publisher_envelope(now), artifact_profile=PROFILE)
        return files, revision

    def active(self, pub, service):
        self.accept(pub); files, revision = self.prepare(pub)
        service.files = files; pub.reconcile(revision)
        return files, revision

    def cli(self, source, remote, service, command, *args, now=NOW, runtime=True, env=None, success=True, local=True):
        launcher = '''import os,sys
from pathlib import Path
import tools.cloud_feed as m
def oidc():
    print('LOCAL_OIDC_BOUNDARY',file=sys.stderr)
    return 'local-qualified-oidc'
m.oidc_token=oidc
if os.environ.get('RUNTIME_ONLY')=='1':
    def observer(event,args):
        if event=='open' and isinstance(args[0],(str,bytes)):
            p=Path(os.fsdecode(args[0])).resolve()
            if any(p==Path.cwd()/d or Path.cwd()/d in p.parents for d in ('catalog','assets')):
                raise AssertionError('runtime read authoring source: '+str(p))
    sys.addaudithook(observer)
    def forbidden_builder(*args,**kwargs):
        raise AssertionError('runtime invoked authoring builder')
    # Fail-only must-not-call guards, never a successful builder substitute.
    m.build_catalog=forbidden_builder
    m.build_artifact=forbidden_builder
sys.exit(m.main())'''
        environment = {k: v for k, v in os.environ.items() if not k.startswith(('GITHUB_', 'GH_TOKEN', 'ACTIONS_', 'GIT_CONFIG_'))}
        environment.update(RUNTIME_ONLY='1' if runtime else '0', GITHUB_RUN_ID='42', GITHUB_RUN_ATTEMPT='1')
        environment.update(env or {})
        result = subprocess.run([sys.executable, '-B', '-c', launcher, '--repository', 'local/spacefox',
            '--remote', str(remote), '--site', service.url + '/site', '--api', service.url,
            '--origin', service.url, *(['--local-qualification'] if local else []), '--now', str(now), command, *map(str,args)],
            cwd=source, env=environment, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0 if success else 2, result.stdout + result.stderr)
        return json.loads(result.stdout.splitlines()[-1]) if success else result

    def pub(self, store): return Publisher(store, self.code)

    def stable(self, pub):
        return {k: pub.ledger[k] for k in ('accepted','active','pending','generation','selection_validated_utc')}

    def test_selected_current_bound_and_explicit_unknown_absence(self):
        self.assertLessEqual(len(self.template['feed.json']),8192)
        self.assertLessEqual(sum(map(len,self.template.values())),1048576)
        empty,_=build_artifact(ScheduleState(),self.catalog,NOW,
            publisher=dict(instance='a'*64,generation=1,selectionValidatedUtc=None),root=ROOT)
        feed=validate_artifact(empty);self.assertIsNone(feed['launch']);self.assertIsNone(feed['visualSelection'])
        row=captured_starship();row['rocket']['configuration']['id']=999999;row['pad']['id']=999999
        state=merge_schedule(ScheduleState(),(normalize_launch(row,NOW),),NOW)
        files,_=build_artifact(state,self.catalog,NOW,
            publisher=dict(instance='a'*64,generation=1,selectionValidatedUtc=NOW),root=ROOT)
        feed=validate_artifact(files);cat=json.loads(files[feed['catalogPath']])
        self.assertIn('ll2:configuration:999999',feed['unresolvedCatalogIds']);self.assertIn('ll2:site:999999',feed['unresolvedCatalogIds'])
        scene=json.loads(files[feed['visualSelection']['path']]);self.assertIsNone(scene['roles']['rocket']);self.assertIsNone(scene['position'])
        self.assertIsNone(scene['roles']['map']);self.assertNotIn('ll2:configuration:999999',cat['entries'])
        self.assertLessEqual(sum(map(len,files.values())),1048576)

    def test_source_materialization_and_prepare_before_authority(self):
        source = self.checkout()
        result = subprocess.run(['bash', '-ec', shell_step('Materialize exact reviewed runtime and catalog closure')],
            cwd=source, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        actual = {p.relative_to(source).as_posix(): p.read_bytes() for p in source.rglob('*')
                  if '.git' not in p.relative_to(source).parts and p.is_file()}
        self.assertEqual(actual, {**self.runtime, **self.closure})
        self.assertEqual(git(source, 'status', '--porcelain'), b'')
        # Recipe data, not fixed counts or a second maintained path inventory.
        self.assertEqual(json.loads(result.stdout)['catalogInputs'], len(self.closure))
        with Service().serving() as service:
            remote = self.base / 'prepare.git'; subprocess.run(['git','init','--bare','-q',str(remote)],check=True)
            git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
            answer = self.cli(source,remote,service,'prepare','--bootstrap','--output',self.base/'prepared',runtime=False)
            self.assertEqual((answer['pending'],answer['requests']), ('true',1))
            store=GitState(str(remote))
            try:
                pub=self.pub(store); files=pub.pending_files(); feed=validate_artifact(files)
                self.assertEqual(feed['publisher']['selectionValidatedUtc'],NOW)
                self.assertEqual(feed['launch']['launch_id'],'ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b')
                self.assertEqual({p.relative_to(self.base/'prepared').as_posix():p.read_bytes() for p in (self.base/'prepared').rglob('*') if p.is_file()},files)
                self.assertEqual(len(pub.ledger['requests']),1)
            finally: store.close()
            self.assertEqual(sum('/launches/upcoming/' in c[1] for c in service.calls),1)
        # A wrong committed pin prevents the exact shell's later bootstrap command.
        broken=self.checkout(); recipe=json.loads((broken/'catalog/source.json').read_bytes())
        recipe['reference']['sha256']='0'*64; (broken/'catalog/source.json').write_bytes(_canonical(recipe))
        git(broken,'add','catalog/source.json'); git(broken,'commit','-qm','technical wrong pin')
        marker=self.base/'must-not-bootstrap'
        bad=subprocess.run(['bash','-ec',shell_step('Materialize exact reviewed runtime and catalog closure')+'\ntouch '+str(marker)],cwd=broken,capture_output=True)
        self.assertEqual(bad.returncode,2); self.assertFalse(marker.exists())
        self.assertEqual((broken/'catalog/source.json').read_bytes(),_canonical(recipe))

    def test_current_source_data_only_extension_and_preserved_refusals(self):
        # New tracked paths are admitted from declarations; original real name
        # and SVG bytes are retained. This never renders invented display text.
        source=self.checkout(); recipe=json.loads((source/'catalog/source.json').read_bytes())
        pin=recipe['curations'][0];value=json.loads(self.closure[pin['path']])
        # A tracked relocation of a complete current curation and all of its
        # real SVGs changes only declarations, never a maintained seed list.
        original=Path(pin['path']);new=Path('assets/local-closure-test/curation.json')
        paths=[]
        for item in value['assets']:
            name=item['facts']['file'];old=(original.parent/name).as_posix();target=source/new.parent/name
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(self.closure[old]);paths.append(target.relative_to(source).as_posix())
        raw=_canonical(value);target=source/new;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        pin.update(path=new.as_posix(),sha256=_sha(raw));(source/'catalog/source.json').write_bytes(_canonical(recipe))
        git(source,'add','--sparse','catalog/source.json',new.as_posix(),*paths)
        git(source,'commit','-qm','tracked data-only current declaration')
        git(source,'sparse-checkout','reapply')
        result=subprocess.run([sys.executable,'-B','tools/cloud_inputs.py'],cwd=source,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual((source/new).read_bytes(),raw)
        self.assertTrue(all((source/name).is_file() for name in paths))
        self.assertEqual((source/'.github/spacefox-inputs.txt').read_bytes(),self.seed)
        self.assertEqual(git(source,'status','--porcelain'),b'')
        # Exact source byte comparison protects edits hidden by sparse/index bits.
        for defect in ('ordinary','hidden','staged','missing','wrong-pin','untracked','rights'):
            with self.subTest(defect=defect):
                source=self.checkout();recipe=json.loads((source/'catalog/source.json').read_bytes());preserve=None
                if defect in ('ordinary','hidden','staged'):
                    path='.github/spacefox-inputs.txt' if defect=='ordinary' else recipe['currentContexts']['path']
                    data=self.sources[path]+b'\nlocal technical corruption\n';target=source/path
                    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data);preserve=(target,data)
                    if defect=='hidden':git(source,'update-index','--assume-unchanged',path)
                    if defect=='staged':git(source,'add','--sparse',path)
                elif defect=='rights':
                    bridgepath=recipe['visualBridge']['path'];bridge=json.loads(self.closure[bridgepath])
                    path=bridge['regional']['path'];index=json.loads(self.closure[path]);index['license']='MIT'
                    data=_canonical(index);target=source/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                    bridge['regional']['sha256']=_sha(data);bridgebytes=_canonical(bridge)
                    target=source/bridgepath;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(bridgebytes)
                    recipe['visualBridge']['sha256']=_sha(bridgebytes);(source/'catalog/source.json').write_bytes(_canonical(recipe))
                    git(source,'add','--sparse',path,bridgepath,'catalog/source.json');git(source,'commit','-qm','technical rights substitution')
                else:
                    pin=recipe['reference']
                    if defect=='wrong-pin':pin['sha256']='0'*64
                    else:
                        original=pin['path'];pin['path']='catalog/local-untracked.json'
                        if defect=='untracked':
                            target=source/pin['path'];data=self.closure[original];target.write_bytes(data);preserve=(target,data)
                    (source/'catalog/source.json').write_bytes(_canonical(recipe))
                    git(source,'add','catalog/source.json');git(source,'commit','-qm','technical declaration fault')
                head=git(source,'rev-parse','HEAD')
                result=subprocess.run([sys.executable,'-B','tools/cloud_inputs.py'],cwd=source,capture_output=True)
                self.assertEqual(result.returncode,2,result.stdout+result.stderr)
                self.assertEqual(git(source,'rev-parse','HEAD'),head)
                if preserve:self.assertEqual(preserve[0].read_bytes(),preserve[1])
                self.assertFalse((source/'build').exists())

    def test_runtime_only_two_generations_finality_and_exact_readback(self):
        with self.authority() as (source,remote,store,pub), Service().serving() as s:
            first,rev=self.active(pub,s); preserved_source=pub.ledger['selection_validated_utc']
            self.assertFalse((source/'catalog/source.json').exists()); self.assertFalse((source/'assets').exists())
            # Run the actual runtime shell, including source exclusion.
            result=subprocess.run(['bash','-ec',shell_step('Check out runtime seed for exact saved-state validation')],cwd=source,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr)
            with tempfile.TemporaryDirectory(prefix='spacefox-content-only-') as folder:
                content=Path(folder)
                for name,raw in self.closure.items():
                    target=content/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
                recipe=json.loads((content/'catalog/source.json').read_bytes());pin=recipe['curations'][0]
                raw=json.dumps(json.loads((content/pin['path']).read_bytes()),ensure_ascii=False,indent=3).encode()
                (content/pin['path']).write_bytes(raw);pin['sha256']=_sha(raw)
                (content/'catalog/source.json').write_bytes(_canonical(recipe));changed=build_catalog(content)
                self.assertEqual(changed['dictionaries'],self.catalog['dictionaries'])
                from tools.cloud_feed import prepare_content
                class ForbiddenProvider:
                    def __getattr__(self,name):raise AssertionError('content-only provider call')
                result=prepare_content(pub,ForbiddenProvider(),NOW+1,changed,root=content)
                self.assertEqual((result['result'],result['requests']),('content_pending',0))
                second=pub.pending_files();second_rev=LiveRevision(**result['revision'])
            complete=delivery_files(pub,delivery(pub)); s.files=first
            head=pub.head
            answer=self.cli(source,remote,s,'arm','--expected-base',head,'--artifact-id',77,now=NOW+1)
            pub=self.pub(store); intent=journal(pub)['intent']; self.assertEqual(intent['generation'],2)
            s.statuses=['succeed']
            self.cli(source,remote,s,'deploy','--expected-base',answer['head'],now=NOW+1)
            self.assertEqual(sum(c[0]=='POST' and c[1].endswith('/pages/deployments') for c in s.calls),1)
            s.files=complete; self.cli(source,remote,s,'recover',now=NOW+1)
            pub=self.pub(store)
            self.assertEqual(pub.ledger['active']['generation'],2); self.assertIsNone(pub.ledger['pending'])
            self.assertEqual(journal(pub)['status'],'succeed'); self.assertEqual(pub.ledger['selection_validated_utc'],preserved_source)
            self.assertEqual(len(pub.ledger['requests']),1)
            self.assertEqual(snapshot_files(store,pub.head,pub.ledger['active']['generation'])[1],second)
            self.assertTrue(all(s.files[name]==raw for name,raw in first.items() if name!='feed.json'))
            before=pub.head; calls=len(s.calls)
            answer=self.cli(source,remote,s,'prepare','--output',self.base/'not-due',now=NOW+2,runtime=False,success=False)
            # Runtime-only prepare cannot rebuild source; later jobs never need it.
            self.assertTrue(answer.stderr.strip())
            self.assertEqual(self.pub(store).head,before)
            self.assertFalse(any('/2.3.0/' in c[1] for c in s.calls[calls:]))
            # Sole mutable root must be reread after *all* immutable bytes.
            pub=self.pub(store); s.root_reads=0; s.after_root=first['feed.json']
            with self.assertRaisesRegex(CloudError,'changed during'):
                Site(s.url+'/site',local_http=True).observe(pub)
            self.assertEqual(self.pub(store).head,before)
            s.after_root=None; s.root_reads=0
            path=next(p for p in complete if p!='feed.json'); good=s.files[path]; s.files[path]=good+b'x'
            with self.assertRaises(CloudError): Site(s.url+'/site',local_http=True).observe(pub)
            s.files[path]=good
            self.assertEqual(Site(s.url+'/site',local_http=True).observe(pub),second_rev)
            self.assertFalse(any('/2.3.0/' in c[1] for c in s.calls))

    def test_saved_faults_stale_source_and_cas_refuse_without_publication(self):
        with self.authority() as (source,remote,store,pub), Service().serving() as s:
            self.accept(pub); files,rev=self.prepare(pub); original=pub.head
            good_doc=pub.ledger
            # Hash-consistent faults force semantic admission, not just digest checks.
            faults=[]
            for field,value in [('schemaVersion',2),('rendererProfile','unsupported'),('publisher',dict(instance='b'*64,generation=1,selectionValidatedUtc=NOW)),('pollIntervalSeconds',7200)]:
                altered=dict(files); feed=json.loads(files['feed.json']); feed[field]=value
                altered['feed.json']=canonical_bytes(feed); faults.append(altered)
            altered=dict(files); key=next(k for k in files if k.startswith('rasters/')); altered[key]+=b'x'; faults.append(altered)
            for number,altered in enumerate(faults):
                doc=deepcopy(good_doc); snap=doc['pending']; snap['files']={k:dict(sha256=_sha(v),bytes=len(v)) for k,v in altered.items()}
                snap['artifact_revision']=_sha(_canonical({k:v for k,v in snap.items() if k!='artifact_revision'}))
                bad=store._commit(doc,original,{f'artifacts/1/{k}':v for k,v in altered.items()})
                store._git('push',f'--force-with-lease={STATE_REF}:{original}',str(remote),f'{bad}:{STATE_REF}')
                for command in ('arm','deploy','recover'):
                    with self.subTest(fault=number,command=command):
                        before=len(s.calls); args=[] if command=='recover' else ['--expected-base',bad]
                        if command=='arm': args+=['--artifact-id',77]
                        self.cli(source,remote,s,command,*args,success=False)
                        self.assertEqual(store._refs(STATE_REF)[STATE_REF],bad)
                        self.assertFalse(any(c[0]=='POST' or '/2.3.0/' in c[1] for c in s.calls[before:]))
                store._git('push',f'--force-with-lease={STATE_REF}:{bad}',str(remote),f'{original}:{STATE_REF}')
            pub=self.pub(store); pub,intent=arm(pub,expected=pub.head,repository='local/spacefox',run_id=42,run_attempt=1,artifact_id=77,now=NOW)
            # Source advances while the queued runtime is unchanged.
            git(source,'commit','--allow-empty','-qm','new source'); git(source,'push','-q',str(remote),'HEAD:refs/heads/main')
            before=pub.head; calls=len(s.calls)
            for command in ('arm','deploy','recover','metadata'):
                args=[] if command in ('recover','metadata') else ['--expected-base',before]
                if command=='arm':args+=['--artifact-id',78]
                refused=self.cli(self.fixture,remote,s,command,*args,success=False)
                self.assertEqual(refused.stderr.count('LOCAL_OIDC_BOUNDARY'),int(command=='deploy'))
                self.assertEqual(store._refs(STATE_REF)[STATE_REF],before)
            self.assertEqual(len(s.calls),calls)
            with self.assertRaises(Conflict): pub.reserve('0'*40,NOW,trigger='extra')
            self.assertEqual(store._refs(STATE_REF)[STATE_REF],before)

    def test_empty_pages_exact_witness_and_nonempty_uncertainty(self):
        with self.authority() as (source,remote,store,pub), Service().serving() as s:
            first,rev=self.active(pub,s); second,rev2=self.prepare(pub,NOW+1)
            pub,intent=arm(pub,expected=pub.head,repository='local/spacefox',run_id=42,run_attempt=1,artifact_id=77,now=NOW+1)
            s.statuses=['']; s.witness(intent); pages=Pages('local/spacefox','local',api=s.url,local_http=True)
            old_wait=pages.wait; pages.wait=lambda version,**options: old_wait(version,polls=options.get('polls',2),delay=0)
            ledger=pub.ledger; pending=pub.pending_files(); before=pub.head
            # Wrong identities, running/started/foreign attempts do not clear.
            run=deepcopy(s.run); jobs=deepcopy(s.jobs)
            defects=[('run','id',43),('run','run_attempt',2),('run','head_sha','f'*40),('run','head_branch','other'),
                ('run','status','in_progress'),('run','path','other.yml'),('run','repository',dict(full_name='other/repo')),
                ('job','conclusion','success'),('job','run_id',43),('job','head_sha','f'*40),('job','status','in_progress')]
            for target,key,value in defects:
                s.run=deepcopy(run);s.jobs=deepcopy(jobs)
                (s.run if target=='run' else s.jobs['jobs'][0])[key]=value
                with self.subTest(target=target,key=key): self.assertFalse(pages.never_started(intent))
                self.assertEqual(store._refs(STATE_REF)[STATE_REF],before)
            # One full rich recovery rejection connects the witness refusal to
            # unchanged authority; the field table above tests the actual HTTP
            # witness owner without repeatedly validating identical map pixels.
            with self.assertRaises(DeploymentStatusEmpty): recover(pub,Site(s.url+'/site',local_http=True),pages)
            self.assertEqual(store._refs(STATE_REF)[STATE_REF],before)
            s.run=run;s.jobs=jobs
            for statuses in (['queued',''],['',{}],['in_progress',''],[dict(status=3)]):
                s.statuses=list(statuses); count=len(s.calls)
                with self.subTest(statuses=statuses), self.assertRaises(CloudError): old_wait(intent['buildVersion'],polls=2,delay=0)
                self.assertFalse(any('/actions/' in c[1] for c in s.calls[count:]))
                self.assertEqual(store._refs(STATE_REF)[STATE_REF],before)
            s.statuses=[''];s.status_code=503;count=len(s.calls)
            with self.assertRaises(CloudError):old_wait(intent['buildVersion'],polls=2,delay=0)
            self.assertFalse(any('/actions/' in c[1] for c in s.calls[count:]));s.status_code=200
            # Empty-only plus the unchanged completed skipped deploy witness
            # writes only cloud journal; accepted/pending bytes and quota survive.
            pub=recover(pub,Site(s.url+'/site',local_http=True),pages)
            self.assertEqual(journal(pub)['status'],'not_started');self.assertEqual(pub.ledger,ledger)
            self.assertEqual(pub.pending_files(),pending);self.assertEqual(snapshot_files(store,pub.head,pub.ledger['active']['generation'])[1],first)
            old_post=sum(c[0]=='POST' for c in s.calls)
            with self.assertRaises(CloudError):
                from tools.spacefox.cloud import deploy
                deploy(pub,pages,Site(s.url+'/site',local_http=True),expected=pub.head,repository='local/spacefox',run_id=42,run_attempt=1,id_token='local')
            self.assertEqual(sum(c[0]=='POST' for c in s.calls),old_post)
            pub,new=arm(pub,expected=pub.head,repository='local/spacefox',run_id=43,run_attempt=1,artifact_id=78,now=NOW+1)
            self.assertNotEqual(new['buildVersion'],intent['buildVersion']);s.statuses=['queued','in_progress','succeed']
            from tools.spacefox.cloud import deploy
            with patch('tools.spacefox.cloud.time.sleep') as sleep:
                self.assertEqual(deploy(pub,pages,Site(s.url+'/site',local_http=True),expected=pub.head,repository='local/spacefox',run_id=43,run_attempt=1,id_token='local',polls=3),'succeed')
                self.assertEqual(sleep.call_count,2)
            self.assertEqual(sum(c[0]=='POST' for c in s.calls),old_post+1)
            s.files=delivery_files(pub,journal(pub)['files']);s.statuses=['succeed']
            pub=recover(pub,Site(s.url+'/site',local_http=True),pages)
            self.assertEqual(pub.ledger['active']['generation'],2);self.assertEqual(pub.ledger['selection_validated_utc'],NOW)
            self.assertEqual(len(pub.ledger['requests']),1)

    def test_metadata_sparse_resume_304_cadence_source_isolation_and_no_journal(self):
        with self.authority() as (source,remote,store,pub), Service().serving() as s:
            first,rev=self.active(pub,s); preserved=self.stable(pub)
            for max_requests in (2,2):
                out=self.cli(source,remote,s,'metadata','--max-requests',max_requests)
            self.assertEqual(out['status'],'complete');pub=self.pub(store)
            self.assertEqual(self.stable(pub),preserved);self.assertIsNone(journal(pub))
            collector=CatalogRefresh(pub,origin=s.url,local_http=True); current=collector.current()
            self.assertEqual(current['coverage']['counts'],dict.fromkeys(('countries','organizations','models','sites'),1))
            self.assertEqual([p['validatedUtc'] for p in current['coverage']['pages']],[NOW]*4)
            self.assertEqual(len([c for c in s.calls if c[1].startswith('/2.3.0/')]),4)
            before=pub.head; calls=len(s.calls)
            self.assertEqual(self.cli(source,remote,s,'metadata',now=NOW+1)['status'],'not_due')
            self.assertEqual(self.pub(store).head,before); self.assertFalse(any(c[1].startswith('/2.3.0/') for c in s.calls[calls:]))
            # Both initial and idle no-journal paths validate immutable closure.
            key=next(p for p in first if p!='feed.json'); good=s.files[key];s.files[key]=good+b'x'
            self.cli(source,remote,s,'metadata',now=NOW+1,success=False);s.files[key]=good
            self.assertEqual(self.pub(store).head,before)
            # Completion controls min/default/max predeadline, with no writes.
            for interval in (3600,86400,604800):
                calls=len(s.calls)
                out=self.cli(source,remote,s,'metadata','--interval-seconds',interval,now=NOW+interval-1)
                self.assertEqual(out['status'],'not_due');self.assertEqual(self.pub(store).head,before)
                self.assertFalse(any(c[1].startswith('/2.3.0/') for c in s.calls[calls:]))
            # Metadata yields to due source, then resumes only after writer poll.
            self.assertEqual(self.cli(source,remote,s,'metadata','--interval-seconds',3600,now=NOW+3600)['status'],'yielded')
            pub=self.pub(store);pub.reconcile(rev);token=pub.reserve(pub.head,NOW+3600,trigger='manual');pub.finish_request(pub.head,token,NOW+3600,'success')
            source_age=pub.ledger['selection_validated_utc']; s.epoch=NOW+3600;s.mode304=True
            out=self.cli(source,remote,s,'metadata','--interval-seconds',3600,now=NOW+3600)
            self.assertEqual((out['status'],out['requests']),('complete',4));pub=self.pub(store)
            replaced=CatalogRefresh(pub,origin=s.url,local_http=True)
            self.assertEqual(replaced.journal['previous'],collector.journal['current'])
            self.assertEqual([p['status'] for p in replaced.current()['coverage']['pages']],[304]*4)
            self.assertEqual([p['validatedUtc'] for p in replaced.current()['coverage']['pages']],[NOW+3600]*4)
            self.assertEqual([p['body'] for p in replaced.current()['coverage']['pages']],[p['body'] for p in current['coverage']['pages']])
            self.assertEqual(pub.ledger['selection_validated_utc'],source_age);self.assertEqual(snapshot_files(store,pub.head,pub.ledger['active']['generation'])[1],first)
            self.assertIsNone(journal(pub));self.assertFalse(any(c[0]=='POST' for c in s.calls))

    def test_metadata_pending_armed_core_promotion_recovery_and_partial_prefix(self):
        with self.authority() as (source,remote,store,pub), Service().serving() as s:
            first,rev=self.active(pub,s)
            self.assertEqual(self.cli(source,remote,s,'metadata','--max-requests',1)['status'],'partial')
            pub=self.pub(store); stage=CatalogRefresh(pub,origin=s.url,local_http=True).journal['staging']; aux=pub.ledger['catalog_refresh']
            pub.reconcile(rev); second,rev2=self.prepare(pub,NOW+1)
            head=pub.head;calls=len(s.calls)
            self.assertEqual(self.cli(source,remote,s,'metadata',now=NOW+1)['status'],'yielded_pending')
            self.assertEqual(self.pub(store).head,head);self.assertEqual(len(s.calls),calls)
            pub,intent=arm(pub,expected=pub.head,repository='local/spacefox',run_id=42,run_attempt=1,artifact_id=77,now=NOW+1)
            complete=delivery_files(pub,journal(pub)['files']);s.files=complete
            # Legal core promotion leaves armed journal; only recover owns finality.
            pub.reconcile(rev2);head=pub.head;calls=len(s.calls)
            self.assertEqual(self.cli(source,remote,s,'metadata',now=NOW+1)['status'],'yielded_armed')
            self.assertEqual(self.pub(store).head,head);self.assertEqual(len(s.calls),calls)
            s.statuses=['succeed'];self.cli(source,remote,s,'recover',now=NOW+1)
            pub=self.pub(store);self.assertEqual(pub.ledger['catalog_refresh'],aux)
            self.assertEqual(CatalogRefresh(pub,origin=s.url,local_http=True).journal['staging'],stage)
            s.epoch=NOW+1
            out=self.cli(source,remote,s,'metadata',now=NOW+1)
            self.assertEqual((out['status'],out['requests']),('complete',3))
            pub=self.pub(store);self.assertEqual(pub.ledger['selection_validated_utc'],NOW)
            self.assertEqual(snapshot_files(store,pub.head,pub.ledger['active']['generation'])[1],second);self.assertEqual(journal(pub)['status'],'succeed')
            self.assertEqual(CatalogRefresh(pub,origin=s.url,local_http=True).current()['coverage']['pages'][0],stage['pages'][0])
            head=pub.head;self.assertEqual(self.cli(source,remote,s,'metadata',now=NOW+2)['status'],'not_due');self.assertEqual(self.pub(store).head,head)
            # Source writer events retain the exact auxiliary object tree and
            # successful deployment journal; metadata itself cannot adopt code.
            pub.reconcile(rev2);auxref=pub.ledger['catalog_refresh']
            saved={p:store._blob(pub.head,p,1048576) for p in git(store.path,'ls-tree','-r','--name-only',pub.head).decode().splitlines() if p.startswith('catalog-refresh/') or p=='cloud.json'}
            token=pub.reserve(pub.head,NOW+2,trigger='manual')
            pub.accept_source(pub.head,token,(normalize_launch(captured_starship(),NOW),),NOW+2,selection_validated_utc=NOW)
            self.assertEqual(pub.ledger['catalog_refresh'],auxref)
            self.assertEqual({p:store._blob(pub.head,p,1048576) for p in saved},saved)
            git(source,'commit','--allow-empty','-qm','current source adoption event');newcode=git(source,'rev-parse','HEAD').decode().strip()
            git(source,'push','-q',str(remote),'HEAD:refs/heads/main');head=pub.head;calls=len(s.calls)
            self.cli(source,remote,s,'metadata',now=NOW+2,success=False)
            self.assertEqual(store._refs(STATE_REF)[STATE_REF],head);self.assertEqual(len(s.calls),calls)
            adopted=Publisher(store,newcode);adopted.adopt_code(adopted.head)
            self.assertEqual(adopted.ledger['catalog_refresh'],auxref)
            self.assertEqual({p:store._blob(adopted.head,p,1048576) for p in saved},saved)


    def test_metadata_zero_work_gates_and_workflow_serialization(self):
        self.assertIn('group: spacefox-whole-publisher-v1\n  cancel-in-progress: false',WORKFLOW)
        minutes=[int(x) for x in re.findall(r"cron: '(\d+) \* \* \* \*'",WORKFLOW)]
        self.assertEqual({hour*60+minute for hour in range(24) for minute in minutes},{hour*60+minute for hour in range(24) for minute in (7,22,37,52)})
        self.assertIn("if: always() && needs.prepare.result == 'success' && (needs.prepare.outputs.pending == 'false' || needs.promote.result == 'success')",WORKFLOW)
        self.assertIn('retention-days: 1',WORKFLOW);self.assertIn('exit 97',WORKFLOW)
        for state in ('due','backoff','uncertain','headroom','fast'):
            policy=RefreshPolicy(fast_interval_seconds=300) if state=='fast' else None
            with self.subTest(state=state),self.authority(policy=policy) as (source,remote,store,pub),Service().serving() as s:
                if state!='due':
                    self.accept(pub)
                    if state=='backoff':
                        token=pub.reserve(pub.head,NOW,trigger='extra');pub.finish_request(pub.head,token,NOW,'throttled',retry_after_utc=NOW+120)
                    elif state=='uncertain':pub.reserve(pub.head,NOW,trigger='extra')
                    elif state=='headroom':
                        for _ in range(6):
                            token=pub.reserve(pub.head,NOW,trigger='extra');pub.finish_request(pub.head,token,NOW,'success')
                head=pub.head
                out=self.cli(source,remote,s,'metadata');self.assertEqual((out['status'],out['requests']),('yielded',0))
                self.assertEqual(self.pub(store).head,head);self.assertIsNone(self.pub(store).ledger.get('catalog_refresh'))
                self.assertFalse(any(c[1].startswith('/2.3.0/') or c[0]=='POST' for c in s.calls))
        with self.authority() as (source,remote,store,pub),Service().serving() as s:
            self.accept(pub);head=pub.head
            for args in (['--interval-seconds',3599],['--interval-seconds',604801],['--max-requests',0],['--max-requests',5]):
                self.cli(source,remote,s,'metadata',*args,success=False)
                self.assertEqual(self.pub(store).head,head);self.assertEqual(s.calls,[])
            # Dirty helper and untrusted main context fail before service calls.
            helper=source/'tools/refresh_catalog.py';raw=helper.read_bytes();helper.write_bytes(raw+b'\n# local change\n')
            self.cli(source,remote,s,'metadata',success=False);helper.write_bytes(raw)
            self.cli(source,remote,s,'metadata',success=False,local=False)
            self.assertEqual(s.calls,[]);self.assertEqual(self.pub(store).head,head)

    def test_metadata_current_policy_cli_refusals_cas_and_failure_preservation(self):
        with self.authority() as (source,remote,store,pub),Service().serving() as s:
            self.accept(pub)
            # CLI supplies current policy without a caller page-size override.
            self.assertEqual(self.cli(source,remote,s,'metadata','--max-requests',1)['status'],'partial')
            pub=self.pub(store);collector=CatalogRefresh(pub,origin=s.url,local_http=True)
            prefix=deepcopy(collector.journal['staging']);ref=pub.ledger['catalog_refresh']; head=pub.head
            self.assertEqual(collector.journal['schemaVersion'],3)
            for defect in ('schema','pageSize','origin','age','stagePolicy'):
                changed=deepcopy(collector.journal)
                if defect=='schema':changed['schemaVersion']=2
                elif defect=='pageSize':changed['pageSize']=20
                elif defect=='origin':changed['origin']='https://example.invalid'
                elif defect=='age':changed['maxSourceAgeSeconds']=60
                else:changed['staging']['pageSizes']['sites']=20
                raw=_canonical(changed);badref=dict(sha256=_sha(raw),bytes=len(raw))
                pub.reconcile(None);pub.checkpoint_catalog(pub.head,NOW,badref,{_catalog_ref(badref):raw})
                before=pub.head;calls=len(s.calls)
                self.cli(source,remote,s,'metadata',success=False)
                self.assertEqual(self.pub(store).head,before);self.assertEqual(len(s.calls),calls+1) # empty live root read only
                # Restore exact prior authority for the next independent fault.
                store._git('push',f'--force-with-lease={STATE_REF}:{before}',str(remote),f'{head}:{STATE_REF}')
                pub=self.pub(store)
            stale=self.pub(store);pub=self.pub(store);pub.reconcile(None)
            token=pub.reserve(pub.head,NOW,trigger='extra');pub.finish_request(pub.head,token,NOW,'success')
            with self.assertRaises(Conflict):CatalogRefresh(stale,origin=s.url,local_http=True).run(NOW)
            self.assertEqual(self.pub(store).head,pub.head)
            # Failed HTTP consumes one shared reservation but cannot replace prefix.
            s.page_fault=429; before=pub.ledger['selection_validated_utc']
            self.cli(source,remote,s,'metadata',success=False)
            pub=self.pub(store);after=CatalogRefresh(pub,origin=s.url,local_http=True)
            self.assertEqual(after.journal['staging'],prefix);self.assertEqual(pub.ledger['selection_validated_utc'],before)
            self.assertEqual(pub.ledger['requests'][-1]['outcome'],'throttled')
            head=pub.head;calls=len(s.calls);self.assertEqual(self.cli(source,remote,s,'metadata')['requests'],0)
            self.assertEqual(self.pub(store).head,head);self.assertFalse(any(c[1].startswith('/2.3.0/') for c in s.calls[calls:]))


if __name__=='__main__': unittest.main()
