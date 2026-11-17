"""In-memory effect ports; actual GitState ledger/transition/CAS callers remain SUT.

Fixture reads happen during harness setup, before the forbidden business-I/O guard.
No temporary repository, subprocess, provider or OS business clock is used.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import uuid
import zipfile

from tools.spacefox import publisher as production


def encode(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def digest(value, size=64):
    return hashlib.sha256(value).hexdigest()[:size]


class Tokens:
    def __init__(self, namespace): self.count = 0;self.prefix=int(hashlib.sha256(namespace.encode()).hexdigest()[:16],16)
    def __call__(self):
        self.count += 1
        return uuid.UUID(int=(self.prefix<<64)|self.count)


class MemoryRemote:
    def __init__(self, namespace):
        self.namespace = namespace
        self.code = 'a' * 40
        self.refs = {'refs/heads/main': self.code}
        self.blobs, self.trees, self.commits = {}, {}, {}
        self.pushes = self.failed_pushes = self.commands = 0
        self.fail_next_push = False
        self.source_after_push = None
        self.unavailable = False
        self.corrupt = None
        self.tokens = Tokens(namespace)


class MemoryGit(production.GitState):
    """Git *transport* fake. Inherits real bootstrap/load/write/_commit/_files.

    Every supported command records an effect. Unsupported commands fail closed,
    rather than delegating to the OS. Each instance has its own local index/refs.
    """
    def __init__(self, remote):
        self.realm = remote
        self.remote = 'memory://' + remote.namespace
        self.source_ref = 'refs/heads/main'
        self._token_source = remote.tokens
        self._fetched_refs = None
        self.local, self.index = {}, {}

    def close(self): pass

    def _blobs(self, revision, requests):
        tree = self.realm.commits[revision]['files']
        result = {}
        for path, limit in requests.items():
            raw = tree[path]
            if self.realm.corrupt == path: raw = raw + b'!'
            if len(raw) > limit: raise production.StateError('memory object exceeds bound')
            result[path] = raw
        return result

    def _git(self, *args, data=None, check=True):
        r = self.realm
        r.commands += 1
        command = args[0]
        code, output = 0, b''
        if command == 'ls-remote':
            if r.unavailable: raise production.StateError('fake authority unavailable')
            output = ''.join(f'{r.refs[x]}\t{x}\n' for x in args[3:] if x in r.refs).encode()
        elif command == 'fetch':
            for spec in args[4:]:
                source, target = spec.lstrip('+').split(':')
                self.local[target] = r.refs[source]
        elif command == 'rev-parse':
            value = self.local.get(args[-1], r.refs.get(args[-1]))
            code, output = (0, (value+'\n').encode()) if value else (1, b'')
        elif command == 'merge-base':
            ancestor, head = args[-2:]
            while head is not None and head != ancestor: head = r.commits[head]['parent']
            code = int(head is None)
        elif command == 'rev-list':
            head = args[-1];parent = r.commits[head]['parent']
            output = (head + (' '+parent if parent else '')+'\n').encode()
        elif command == 'cat-file':
            revision, path = args[-1].split(':', 1)
            code = int(path not in r.commits[revision]['files'])
        elif command == 'read-tree':
            self.index = {} if args[1] == '--empty' else dict(r.commits[args[1]]['files'])
        elif command == 'ls-files':
            prefixes = args[2:]
            output = b''.join(k.encode()+b'\0' for k in self.index if any(k == p or k.startswith(p+'/') for p in prefixes))
        elif command == 'hash-object':
            key = digest(data, 40);r.blobs[key] = data;output = key.encode()+b'\n'
        elif command == 'update-index':
            if '--index-info' in args:
                for line in data.split(b'\0'):
                    if line: self.index.pop(line.split(b'\t', 1)[1].decode(), None)
            else:
                _, key, path = args[-1].split(',', 2);self.index[path] = r.blobs[key]
        elif command == 'write-tree':
            key = digest(encode({k: digest(v) for k, v in self.index.items()}),40)
            r.trees[key] = dict(self.index);output = key.encode()+b'\n'
        elif command == 'commit-tree':
            parent = args[3] if len(args)>2 else None
            key = digest(encode([args[1],parent,len(r.commits)]),40)
            r.commits[key] = dict(parent=parent, files=dict(r.trees[args[1]]))
            output = key.encode()+b'\n'
        elif command == 'push':
            leases = [x.split('=',1)[1].split(':',1) for x in args if x.startswith('--force-with-lease=')]
            code = int(r.fail_next_push or any(r.refs.get(ref,'') != expected for ref,expected in leases))
            r.fail_next_push = False
            if code: r.failed_pushes += 1
            else:
                for x in args[1:]:
                    if not x.startswith('-') and ':' in x and not x.startswith('memory://'):
                        key, ref = x.split(':',1);r.refs[ref] = key
                r.pushes += 1
                if r.source_after_push is not None:
                    r.refs['refs/heads/main'] = r.source_after_push
                    r.source_after_push = None
        else:
            raise AssertionError('FORBIDDEN real Git command: '+repr(args))
        if check and code: raise production.StateError('fake Git command refused '+repr(args))
        return SimpleNamespace(returncode=code, stdout=output, stderr=b'')


def create_publisher(namespace):
    remote=MemoryRemote(namespace);store=MemoryGit(remote)
    store.bootstrap(remote.code)
    sut=production.Publisher(store,remote.code,token_source=remote.tokens)
    sut.reconcile(None)
    return sut,remote


class ArtifactFixture:
    """Harness input loader and fake render service: immutable captured pixels.

    Host state properties do not qualify rendering/projection. The fake returns
    captured role bytes and a current feed envelope for the supplied model input;
    actual Publisher artifact admission still runs without subprocesses.
    """
    def __init__(self):
        from tools.spacefox.publisher import _schedule
        root=Path(__file__).resolve().parents[1]
        with zipfile.ZipFile(root/'tests/fixtures/current_authority/frozen-current.zip') as archive:
            self.files={name:archive.read(name) for name in archive.namelist() if not name.endswith('/')}
        self.feed=json.loads(self.files['feed.json'])
        source=deepcopy(self.feed['launch'])
        self.flags={k:source.pop(k) for k in ('rescheduled','stale')}
        for key in ('launch_id','configuration_id','operator_id','site_id','country_id'):
            if source[key] is not None:
                namespace,kind,value=source[key].split(':',2)
                source[key]=dict(namespace=namespace,kind=kind,value=value)
        self.record=_schedule({'entries':[dict(record=source,**self.flags)],'evaluated_at_utc':self.feed['launch']['source_validated_utc']}).entries[0].record

    def render(self,records,instance,generation,epoch,policy):
        from tools.spacefox.native_motion import with_text_transport
        from tools.spacefox.schedule import ScheduleState
        from tools.spacefox.wire import project_launch
        from tools.spacefox.schedule import AcceptedLaunch
        feed=deepcopy(self.feed)
        feed['publisher']=dict(instance=instance,generation=generation,selectionValidatedUtc=epoch)
        feed['upcoming']=[]
        feed['selection']['acceptedRecords']=len(records)
        feed['selection']['includedRecords']=1
        if not records:
            feed['launch']=None;feed['timingState']='no-schedule';feed['selection']['includedRecords']=0
            feed['sourceContentRevision']=hashlib.sha256(b'[]').hexdigest();feed['refreshPolicy']=dict(policy)
            catalog=json.loads(self.files[feed['catalogPath']]);catalog['entries']={};catalog['unresolved']=[];catalog['visualSelection']=None
            raw=encode(catalog);key=hashlib.sha256(raw).hexdigest();feed['catalogDigest']=key;feed['catalogPath']='wire3/catalogs/'+key+'.json'
            transfer=json.loads(self.files[feed['nativeTransfer']['path']]);transfer['scene']=None;transfer['objects']=[]
            encoded=encode(transfer);sha=hashlib.sha256(encoded).hexdigest();path='descriptors/'+sha+'.json'
            feed['nativeTransfer']=dict(path=path,sha256=sha,decodedBytes=len(encoded));feed['visualSelection']=None;feed['unresolvedCatalogIds']=[]
            files=dict(self.files);files[feed['catalogPath']]=raw;files[path]=encoded;files['feed.json']=encode(feed)
            return with_text_transport(files),key
        entry=records[0]
        feed['launch']=project_launch(AcceptedLaunch(entry['record'],entry['rescheduled'],entry['stale']))
        feed['timingState']='countdown' if entry['record'].timing.exact_utc is not None else 'uncertain'
        # Construct malformed/future-origin inputs too; the real SUT must
        # refuse them. This hash is an input producer, not an oracle value.
        content=[e['record'].content() for e in sorted(records,key=lambda e:e['record'].launch_id.key)]
        feed['sourceContentRevision']=hashlib.sha256(encode(content)).hexdigest()
        feed['refreshPolicy']=dict(policy)
        files=dict(self.files);files['feed.json']=encode(feed)
        return with_text_transport(files),feed['catalogDigest']

# Thread-local dispatch is installed once per coordinator process. Patching in
# each worker would race; all mutable fake services/counters live in this scope.
import builtins
import contextlib
import contextvars
import io
import os
import socket
import subprocess
import tempfile
import time
import threading
from unittest.mock import patch

ACTIVE = contextvars.ContextVar('host_pbt_business', default=None)


class ProductAdmission:
    """Fake graphics/product service; actual wire + Publisher identity checks run.

    Rendering and full source/pixel closure qualification are intentionally not
    this FSM property. Fixture bytes are already captured; no renderer is run.
    """
    def __init__(self, fixture):
        self.fixture=fixture;self.calls=0;self.fail=False
    def validate(self, files):
        from tools.spacefox.wire import validate_current_feed
        self.calls+=1
        if self.fail: raise ValueError('event-controlled product service failure')
        feed=validate_current_feed(files.get('feed.json'))
        # This port only offers immutable captured art. SUT/storage digest
        # checks are real, not delegated to this fake service.
        for name, raw in self.fixture.files.items():
            if name not in ('feed.json','watch.json') and not name.endswith('.txt') and files.get(name)!=raw:
                raise ValueError('fake product service refuses changed captured art')
        return feed


@dataclass
class BusinessScope:
    product: object
    forbidden: int = 0


@contextlib.contextmanager
def business(scope):
    token=ACTIVE.set(scope)
    try: yield
    finally: ACTIVE.reset(token)


@contextlib.contextmanager
def forbid_real_effects():
    """Runtime guards include startup, caught failures and every worker thread.

    The coordinator's clocks, fixture/trace IO and executor scheduling remain
    outside business(scope). No real clock can feed the SUT through this guard.
    """
    def wrap(original, label):
        def guarded(*args, **kwargs):
            scope=ACTIVE.get()
            if scope is not None:
                scope.forbidden+=1
                raise AssertionError('FORBIDDEN business effect: '+label)
            return original(*args,**kwargs)
        return guarded
    from tools.spacefox import native_motion
    original=native_motion.validate_artifact
    def product(files):
        scope=ACTIVE.get()
        return scope.product.validate(files) if scope is not None else original(files)
    with contextlib.ExitStack() as stack:
        stack.enter_context(patch.object(native_motion,'validate_artifact',product))
        for obj, name in [(builtins,'open'),(io,'open'),(os,'open'),(os,'urandom'),
                          (subprocess,'run'),(subprocess,'Popen'),(tempfile,'TemporaryDirectory'),
                          (socket,'create_connection'),(socket.socket,'connect'),(socket.socket,'connect_ex'),(socket.socket,'sendto'),
                          (threading.Thread,'start'),(os,'mkdir'),(os,'unlink'),(os,'rename'),(os,'replace'),(os,'rmdir'),
                          (time,'time'),(time,'monotonic'),(time,'perf_counter'),(time,'sleep'),(uuid,'uuid4')]:
            stack.enter_context(patch.object(obj,name,wrap(getattr(obj,name),obj.__name__+'.'+name)))
        yield
