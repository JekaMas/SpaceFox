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
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import unittest

from tests.test_basic_publisher_clock import current_source_closure
from tests.test_current_motion_publisher import captured_starship, NOW
from tests.test_current_metadata_publisher import captured
from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.cloud import (CloudError, Site,
    arm, delivery, delivery_files, journal, snapshot_files)
from tools.spacefox.native_motion import PROFILE, build_artifact, validate_artifact
from tools.spacefox.provider import normalize_launch
from tools.spacefox.publisher import (Conflict, GitState, LiveRevision, Publisher,
    STATE_REF, _canonical, _sha)
from tools.spacefox.schedule import RefreshPolicy, ScheduleState, merge_schedule

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
        # Literal real Starship/SpaceX/Orbital Launch Pad2/USA source closure.
        # It contains every reference of the unchanged captured launch and of
        # these four actual typed records; no relationship is fabricated.
        selected={'countries':2,'organizations':121,'models':522,'sites':235}
        for collection,identity in selected.items():
            rows=[row for page in candidate['coverage']['pages'] if page['collection']==collection
                  for row in json.loads(files['objects/'+page['body']['sha256']+'.json'])['results']
                  if row['id']==identity]
            if len(rows)!=1:raise AssertionError('captured metadata identity closure')
            # Verbatim records; only count/pagination and later transport origin
            # are controlled. This is no new complete-provider observation.
            self.metadata[collection]=_canonical(dict(count=1,next=None,previous=None,results=rows))
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
            # Preserve real display/fact fields; only transport-scoped LL2 URL
            # origin is rebased for the explicit anonymous loopback boundary.
            raw=self.metadata[collection].replace(b'https://ll.thespacedevs.com',self.url.encode())
            return 200, raw, h
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
        from tools.spacefox.native_motion import with_text_transport
        files = {path: raw for path, raw in self.template.items() if not path.endswith('.txt')}
        feed = json.loads(files['feed.json'])
        feed['publisher'] = pub.publisher_envelope(now)
        files['feed.json'] = canonical_bytes(feed)
        files = with_text_transport(files)
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
        if event=='import' and args[0]=='tools.spacefox.catalog_refresh' and os.environ.get('FORBID_CATALOG_IMPORT')=='1':
            raise AssertionError('blocked command imported metadata collector')
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
            cwd=source, env=environment, capture_output=True, text=True, timeout=300)
        self.assertEqual(result.returncode, 0 if success else 2, result.stdout + result.stderr)
        return json.loads(result.stdout.splitlines()[-1]) if success else result


    def pub(self, store): return Publisher(store, self.code)


    def stable(self, pub):
        return {k: pub.ledger[k] for k in ('accepted','active','pending','generation','selection_validated_utc')}

    def test_missing_authority_refuses_actual_updater_with_usable_provider(self):
        source = self.checkout()
        materialize = subprocess.run(['bash', '-ec', shell_step('Materialize exact reviewed runtime and catalog closure')],
                                     cwd=source, capture_output=True)
        self.assertEqual(materialize.returncode, 0, materialize.stderr)
        remote = self.base / 'missing-authority.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
        git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
        with Service().serving() as service:
            result = self.cli(source, remote, service, 'prepare', '--bootstrap', '--output',
                              self.base / 'initial-pending', runtime=False)
            self.assertEqual((result['pending'], result['requests']), ('true', 1))
            store = GitState(str(remote))
            try:
                pub = self.pub(store)
                self.assertIsNotNone(pub.ledger['pending'])
                pending = pub.pending_files()
                service.files = pending
                old_head = pub.head
                anchor = store._refs('refs/tags/spacefox-state-bootstrap-map-v3')
                git(remote, 'update-ref', '-d', STATE_REF, old_head)
                before_calls = len(service.calls)
                refused = self.cli(source, remote, service, 'prepare', '--output',
                                   self.base / 'missing-pending', runtime=False, success=False)
                self.assertTrue(refused.stderr.strip())
                self.assertEqual(store._refs(STATE_REF), {})
                self.assertEqual(store._refs('refs/tags/spacefox-state-bootstrap-map-v3'), anchor)
                self.assertFalse(any('/2.3.0/' in c[1] for c in service.calls[before_calls:]))
                self.assertEqual(service.files, pending)
                self.cli(source, remote, service, 'prepare', '--bootstrap', '--output',
                         self.base / 'missing-bootstrap', runtime=False, success=False)
                self.assertEqual(store._refs(STATE_REF), {})
                self.assertEqual(store._refs('refs/tags/spacefox-state-bootstrap-map-v3'), anchor)
            finally:
                store.close()

    def test_restart_promotes_exact_pending_before_generation_three(self):
        with self.authority() as (source, remote, store, pub), Service().serving() as service:
            first, first_revision = self.active(pub, service)
            second, second_revision = self.prepare(pub, NOW + 1)
            service.files = delivery_files(pub, delivery(pub))
            pending_head = pub.head
            restarted = self.pub(store)
            observed = Site(service.url + '/site', local_http=True).observe(restarted)
            self.assertEqual(observed, second_revision)
            self.assertEqual(restarted.reconcile(observed), 'promoted')
            self.assertNotEqual(restarted.head, pending_head)
            self.assertEqual(restarted.ledger['active']['generation'], 2)
            self.assertIsNone(restarted.ledger['pending'])
            self.assertEqual(snapshot_files(store, restarted.head, 2)[1], second)
            third, _ = self.prepare(restarted, NOW + 2)
            self.assertEqual(restarted.ledger['active']['generation'], 2)
            self.assertEqual(restarted.ledger['pending']['generation'], 3)
            self.assertEqual(restarted.pending_files(), third)
            self.assertEqual(service.files['feed.json'], second['feed.json'])
            self.assertNotEqual(first['feed.json'], second['feed.json'])

    def test_stale_worker_cannot_request_after_new_pending(self):
        with self.authority() as (source, remote, store, pub), Service().serving() as service:
            first, revision = self.active(pub, service)
            script = '''import json,sys
from tools.spacefox.publisher import GitState,Publisher,LiveRevision,StateError
from tools.spacefox.provider import LL2Client
s=GitState(sys.argv[1]); p=Publisher(s,sys.argv[2]); p.reconcile(LiveRevision(**json.loads(sys.argv[3])))
print('ready',flush=True); sys.stdin.readline()
try: LL2Client(origin=sys.argv[4],local_http=True).request(p,int(sys.argv[5]),trigger='extra')
except StateError: sys.exit(0)
sys.exit(3)
'''
            child = subprocess.Popen([sys.executable, '-B', '-c', script, str(remote), self.code,
                                      json.dumps(vars(revision)), service.url, str(NOW + 2)],
                                     cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE, text=True)
            try:
                self.assertEqual(child.stdout.readline().strip(), 'ready')
                second, _ = self.prepare(pub, NOW + 1)
                service.files = delivery_files(pub, delivery(pub))
                saved = pub.head
                calls = len(service.calls)
                out, err = child.communicate('\n', timeout=30)
                self.assertEqual(child.returncode, 0, out + err)
                self.assertEqual(store._refs(STATE_REF)[STATE_REF], saved)
                self.assertFalse(any('/2.3.0/' in c[1] for c in service.calls[calls:]))
                self.assertEqual(service.files['feed.json'], second['feed.json'])
                self.assertNotEqual(first['feed.json'], second['feed.json'])
            finally:
                if child.poll() is None:
                    child.kill()
                    child.communicate()


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
            self.assertTrue(all(s.files[name]==raw for name,raw in first.items() if name not in ('feed.json','feed.json.txt')))
            self.assertEqual(s.files['feed.json'],second['feed.json'])
            self.assertEqual(s.files['feed.json.txt'],second['feed.json'])
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
            path=next(p for p in first if p not in second); good=s.files[path]; s.files[path]=good+b'x'
            with self.assertRaises(CloudError): Site(s.url+'/site',local_http=True).observe(pub,journal(pub)['files'])
            s.files[path]=good
            self.assertEqual(Site(s.url+'/site',local_http=True).observe(pub,journal(pub)['files']),second_rev)
            self.assertFalse(any('/2.3.0/' in c[1] for c in s.calls))


    def test_saved_faults_stale_source_and_cas_refuse_without_publication(self):
        with self.authority() as (source,remote,store,pub), Service().serving() as s:
            self.accept(pub); files,rev=self.prepare(pub); original=pub.head
            good_doc=pub.ledger
            # Hash-consistent faults force semantic admission, not just digest checks.
            faults=[]
            for field,value in [('schemaVersion',2),('rendererProfile','unsupported'),('publisher',dict(instance='b'*64,generation=1,selectionValidatedUtc=NOW)),('pollIntervalSeconds',7200)]:
                altered=dict(files); feed=json.loads(files['feed.json']); feed[field]=value
                altered['feed.json']=canonical_bytes(feed)
                altered['feed.json.txt']=altered['feed.json']
                faults.append(altered)
            altered=dict(files)
            key=next(k for k in files if k.startswith('rasters/') and not k.endswith('.txt'))
            altered[key]+=b'x'
            if key+'.txt' in altered:
                altered[key+'.txt']=altered[key]
            faults.append(altered)
            for number,altered in enumerate(faults):
                self.assertEqual(altered['feed.json'],altered['feed.json.txt'])
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
