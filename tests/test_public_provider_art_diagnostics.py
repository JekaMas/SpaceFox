"""Actual clean public CLI/Git/HTTP boundary; only LL2/CDN are loopback.

The first publication is explicitly promoted by an observer-supplied revision;
subsequent positive/corrupt readback uses the real cloud recover CLI. No hosted,
cron, provider freshness, family completeness or native acceptance is claimed.
"""
import copy
from email.utils import formatdate
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.parse import urlsplit

from tests import test_provider_detail_efficiency as detail
from tools.spacefox.publisher import GitState, LiveRevision, Publisher
from tools.spacefox.cloud import journal

ROOT = Path(__file__).resolve().parents[1]
NOW = 1794441600
ART = 'spacefox:asset:remaining-r3-simorgh-mod2021'
ART_SHA = 'f5e79ba0de9c3951bb7849e0b29a7aed8a5c12f17a357bc68bb222797f7d12f0'
MODELS = {142: 'simorgh-mod2021'}


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode().strip()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


class PublicProviderArtDiagnosticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if (ROOT / '.agents').exists() or git(ROOT, 'status', '--porcelain'):
            raise AssertionError('run in actual clean exported public checkout')
        cls.code = git(ROOT, 'rev-parse', 'HEAD')
        manifest = json.loads((ROOT / 'distribution/publisher-source-snapshot.json').read_bytes())
        for path in manifest['files']:
            if path.startswith('tests/test_') and path.endswith('.py'):
                importlib.import_module(path[:-3].replace('/', '.'))
        cls.tmp = tempfile.TemporaryDirectory(prefix='spacefox-public-current-')
        cls.base = Path(cls.tmp.name)
        cls.remote = cls.base / 'authority.git'
        subprocess.run(['git', 'init', '--bare', '-q', str(cls.remote)], check=True)
        git(ROOT, 'push', '-q', str(cls.remote), 'HEAD:refs/heads/main')
        cls.live, cls.reads, cls.calls, cls.permissions = {}, [], [], []
        cls.rows = [detail.row(1, 3), detail.row(2)]
        cls.details, cls.epoch = {}, NOW
        owner = cls

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *_args):
                pass

            def do_GET(self):
                if self.path.startswith('/site/'):
                    path = self.path.removeprefix('/site/')
                    owner.reads.append(path)
                    raw = owner.live.get(path)
                    status = 404 if raw is None else 200
                    raw = b'' if raw is None else raw
                else:
                    owner.calls.append(self.path)
                    store = GitState(str(owner.remote))
                    try:
                        ledger = store.load()[1]
                        owner.permissions.append(ledger['requests'][-1]['outcome'])
                    finally:
                        store.close()
                    if urlsplit(self.path).path.endswith('/upcoming/'):
                        value = dict(count=len(owner.rows), next=None, previous=None, results=owner.rows)
                    else:
                        identity = urlsplit(self.path).path.split('/')[-2]
                        value = owner.details.get(identity)
                    status, raw = 200, json.dumps(value).encode()
                self.send_response_only(status)
                self.send_header('Date', formatdate(owner.epoch, usegmt=True))
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.origin = f'http://127.0.0.1:{cls.http.server_port}'
        cls.invoke(cls.remote, NOW, 'prepare', '--bootstrap', '--output', str(cls.base / 'first'))
        store = GitState(str(cls.remote))
        try:
            pub = Publisher(store, cls.code)
            pending = pub.ledger['pending']
            pub.reconcile(LiveRevision(pending['generation'], pending['artifact_revision']))
            cls.old_terminal = next(e for e in pub.schedule.entries if e.record.launch_id.value.endswith('000000000001'))
        finally:
            store.close()
        cls.live = {p.relative_to(cls.base / 'first').as_posix(): p.read_bytes()
                    for p in (cls.base / 'first').rglob('*') if p.is_file()}
        primary = detail.row(3)
        primary['rocket']['configuration'].update(id=142, name='Simorgh')
        reconciled = detail.row(2, 3, mode='detailed', modified='2026-11-12T00:30:00Z')
        cls.rows, cls.details, cls.epoch = [primary], {reconciled['id']: reconciled}, NOW + 3600
        cls.calls, cls.permissions = [], []
        cls.result = cls.invoke(cls.remote, NOW + 3600, 'prepare', '--output', str(cls.base / 'pending'))
        cls.files = {p.relative_to(cls.base / 'pending').as_posix(): p.read_bytes()
                     for p in (cls.base / 'pending').rglob('*') if p.is_file()}
        store = GitState(str(cls.remote))
        try:
            pub = Publisher(store, cls.code)
            cls.ledger = copy.deepcopy(pub.ledger)
            cls.journal = journal(pub)
            cls.entries = copy.deepcopy(pub.schedule.entries)
        finally:
            store.close()
        feed = json.loads(cls.files['wire2/feed.json'])
        cls.selection = json.loads(cls.files[feed['visualSelection']['path']])
        cls.descriptor = json.loads(cls.files[cls.selection['roles']['rocket']['descriptor']['path']])
        cls.art_path = cls.descriptor['shards'][0]['path']
        cls.live = dict(cls.files)

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join()
        cls.tmp.cleanup()

    @classmethod
    def invoke(cls, remote, now, *args, success=True):
        environment = dict(os.environ)
        for key in ('GH_TOKEN', 'GITHUB_OUTPUT'):
            environment.pop(key, None)
        command = [sys.executable, '-B', 'tools/cloud_feed.py', '--repository', 'local/SpaceFox',
                   '--remote', str(remote), '--site', cls.origin + '/site', '--api', cls.origin,
                   '--origin', cls.origin, '--local-qualification', '--now', str(now), *args]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, env=environment, timeout=180)
        if success:
            if result.returncode != 0:
                raise AssertionError(result.stderr)
            return json.loads(result.stdout)
        if result.returncode != 2:
            raise AssertionError((result.returncode, result.stdout, result.stderr))
        return result.stderr

    def setUp(self):
        self.copy = self.base / self._testMethodName
        subprocess.run(['git', 'clone', '--bare', '-q', str(self.remote), str(self.copy)], check=True)
        type(self).live, type(self).reads = dict(self.files), []
        self.refs = git(self.copy, 'show-ref')
        self.head = git(self.copy, 'rev-parse', 'refs/heads/feed-state')
        self.tree = git(self.copy, 'ls-tree', '-r', 'refs/heads/feed-state')

    def test_public_cli_current_provider_four_art_and_exact_readback(self):
        self.assertEqual(('pending', 2, 1, []),
                         (self.result['result'], self.result['requests'],
                          self.result['traversal']['detailRequests'], self.result['detailFailures']))
        self.assertEqual(['reserved', 'reserved'], self.permissions)
        self.assertEqual(2, len(self.calls))
        self.assertIn('/upcoming/', self.calls[0])
        self.assertTrue(self.calls[1].endswith('/00000000-0000-4000-8000-000000000002/?mode=normal'))
        entries = {e.record.launch_id.value: e for e in self.entries}
        self.assertEqual(self.old_terminal, entries['00000000-0000-4000-8000-000000000001'])
        row = entries['00000000-0000-4000-8000-000000000002'].record
        self.assertEqual(('completed', NOW + 3600, NOW + 1800),
                         (row.status.value, row.source_validated_utc, row.source_updated_utc))
        self.assertEqual(('ll2:configuration:142', ART, ART_SHA),
                         (self.selection['modelId'], self.descriptor['assetId'], self.descriptor['sha256']))
        self.assertEqual(self.code, self.ledger['code_revision'])
        result = self.invoke(self.copy, NOW + 3600, 'recover')
        self.assertEqual('false', result['pending'])
        store = GitState(str(self.copy))
        try:
            after = Publisher(store, self.code).ledger
        finally:
            store.close()
        self.assertIsNone(after['pending'])
        self.assertEqual(self.ledger['pending'], after['active'])
        for field in ('accepted', 'requests', 'selection_validated_utc', 'last_poll_utc', 'backoff_until_utc'):
            self.assertEqual(self.ledger[field], after[field], field)
        # With no armed journal, recover checks the pending generation, not
        # the output directory's additional retained prior-generation files.
        self.assertIsNone(self.journal)
        expected = set(self.ledger['pending']['files'])
        self.assertTrue(expected < set(self.files))
        self.assertEqual(expected, set(self.reads))
        self.assertEqual((2, 2, len(expected) + 2),
                         (self.reads.count('feed.json'), self.reads.count('wire2/feed.json'), len(self.reads)))
        self.assertEqual(2, len(self.calls), 'readback must issue no provider request')
        output = self.base / 'four-art'
        command = [sys.executable, '-B', 'tools/export_visuals.py', '--output', str(output)]
        for identity in MODELS:
            command += ['--root', 'll2:configuration:' + str(identity)]
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=180)
        self.assertEqual(0, result.returncode, result.stderr)
        visual = json.loads((output / 'manifest.json').read_bytes())
        for number, name in MODELS.items():
            identity = 'll2:configuration:' + str(number)
            asset_id = 'spacefox:asset:remaining-r3-' + name
            self.assertEqual(asset_id, visual['selection']['dictionaries']['configurations'][identity]['references']['visual'])
            asset = visual['assets'][asset_id]
            self.assertEqual('MIT', asset['rights']['license'])
            self.assertEqual([identity], asset['catalogRecord']['facts']['coverage']['configurationIds'])
            for shard in asset['shards']:
                raw = (output / shard['path']).read_bytes()
                self.assertEqual(shard['sha256'], sha(raw))
                self.assertLessEqual(len(raw), 4096)
        print('PUBLIC_CURRENT_POSITIVE ' + json.dumps(dict(public=self.code, requests=2, detailRequests=1,
              art=ART, semanticDigest=ART_SHA, exactReadbackFiles=len(expected),
              sourceEpoch=after['selection_validated_utc'], currentArtRights='MIT', importedPublicTests=True)))

    def test_public_cli_corrupt_current_art_rejects_without_state_or_age_change(self):
        raw = b'response-body-secret'
        type(self).live[self.art_path] = raw
        error = self.invoke(self.copy, NOW + 3600, 'recover', success=False)
        self.assertLess(len(error.encode()), 1024)
        self.assertNotIn('response-body-secret', error)
        self.assertNotIn(self.origin, error)
        context = json.loads(error.split('; readback=', 1)[1])
        expected = self.files[self.art_path]
        self.assertEqual(dict(path=self.art_path, kind='immutable-file', phase='closure', status=200,
                              expected=dict(bytes=len(expected), sha256=sha(expected)),
                              actual=dict(bytes=len(raw), sha256=sha(raw))), context)
        self.assertEqual(self.refs, git(self.copy, 'show-ref'))
        self.assertEqual(self.head, git(self.copy, 'rev-parse', 'refs/heads/feed-state'))
        self.assertEqual(self.tree, git(self.copy, 'ls-tree', '-r', 'refs/heads/feed-state'))
        store = GitState(str(self.copy))
        try:
            self.assertEqual(self.ledger, Publisher(store, self.code).ledger)
        finally:
            store.close()
        self.assertEqual(1, self.reads.count(self.art_path))
        self.assertEqual(2, len(self.calls))
        print('PUBLIC_CURRENT_NEGATIVE ' + json.dumps(dict(public=self.code, diagnostic=context,
              stateRetained=True, providerRequestsDuringReadback=0)))


if __name__ == '__main__':
    unittest.main()
