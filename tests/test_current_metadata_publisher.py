"""Current metadata authority tests; captured source bodies and real local Git.

HTTP is a controlled response port. These tests do not call LL2 or Pages.
"""
from contextlib import contextmanager
from copy import deepcopy
from email.utils import formatdate
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
import zipfile

from tools.spacefox.catalog_refresh import CatalogRefresh, RefreshError
from tools.spacefox.publisher import GitState, Publisher, _canonical, _catalog_ref
from tools.spacefox.provider import Response
from tools.refresh_catalog import scheduled


NOW = 1794541187
FIXTURE = Path(__file__).parent / 'fixtures/metadata-current/captured-schema3.zip'
RECEIPT = FIXTURE.with_name('captured-schema3-receipt.json')
SIZES = {'countries': 20, 'organizations': 20, 'models': 100, 'sites': 100}


def captured():
    receipt = json.loads(RECEIPT.read_bytes())
    raw = FIXTURE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != receipt['archiveSha256']:
        raise AssertionError('captured fixture archive digest')
    with zipfile.ZipFile(FIXTURE) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    if set(files) != set(receipt['files']):
        raise AssertionError('captured fixture closure')
    for name, data in files.items():
        if receipt['files'][name] != dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()):
            raise AssertionError('captured source byte pin')
    candidate = json.loads(files['complete-candidate.json'])
    return candidate, files


class CapturedTransport:
    """Exact captured raw bodies; controlled response metadata, no network."""
    def __init__(self, pub, candidate, files):
        self.pub = pub
        self.pages = {page['url']: page for page in candidate['coverage']['pages']}
        self.files = files
        self.calls = []
        self.epoch = None

    def get(self, url, etag):
        request = self.pub.ledger['requests'][-1]
        if request['purpose'] != 'catalog' or request['outcome'] != 'reserved':
            raise AssertionError('transport preceded durable catalog permission')
        page = self.pages[url]
        raw = self.files['objects/' + page['body']['sha256'] + '.json']
        self.calls.append(dict(url=url, at=request['at_utc'], sha256=hashlib.sha256(raw).hexdigest()))
        epoch = page['validatedUtc'] if self.epoch is None else self.epoch
        return Response(200, {'date': formatdate(epoch, usegmt=True), 'content-type': 'application/json'}, raw)



def git(folder, *args):
    return subprocess.check_output(['git', '-C', str(folder), *args], stderr=subprocess.DEVNULL).decode().strip()


class CurrentMetadataPublisherTest(unittest.TestCase):
    @contextmanager
    def authority(self):
        with tempfile.TemporaryDirectory(prefix='spacefox-current-metadata-') as folder:
            root = Path(folder); source = root / 'source'; source.mkdir(); remote = root / 'remote.git'
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            git(source, 'init', '-q'); git(source, 'config', 'user.name', 'Current metadata test')
            git(source, 'config', 'user.email', 'metadata@example.invalid')
            git(source, 'commit', '--allow-empty', '-qm', 'source')
            code = git(source, 'rev-parse', 'HEAD'); git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            try:
                store.bootstrap(code); pub = Publisher(store, code); pub.reconcile(None)
                yield pub, store, code
            finally:
                store.close()

    def test_current_policy_is_the_only_default(self):
        with self.authority() as (pub, _, _):
            collector = CatalogRefresh(pub)
            self.assertEqual(collector.journal['schemaVersion'], 3)
            expected = {
                'countries': 'https://ll.thespacedevs.com/2.3.0/config/countries/?format=json&limit=20',
                'organizations': 'https://ll.thespacedevs.com/2.3.0/agencies/?format=json&limit=20&mode=normal',
                'models': 'https://ll.thespacedevs.com/2.3.0/launcher_configurations/?format=json&limit=100&mode=detailed',
                'sites': 'https://ll.thespacedevs.com/2.3.0/pads/?format=json&limit=100&mode=detailed&ordering=id'}
            self.assertEqual({c: collector._url(c, 0) for c in expected}, expected)

    def test_obsolete_metadata_journals_are_refused(self):
        for version in (1, 2):
            with self.subTest(version=version), self.authority() as (pub, store, code):
                raw = _canonical(dict(schemaVersion=version, origin='https://ll.thespacedevs.com',
                    pageSize=20, maxSourceAgeSeconds=86400, staging=None, cache={}, current=None, previous=None))
                ref = dict(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
                pub.checkpoint_catalog(pub.head, NOW, ref, {_catalog_ref(ref): raw})
                before = pub.head
                with self.assertRaises(RefreshError):
                    CatalogRefresh(Publisher(store, code))
                self.assertEqual(store.load()[0], before)

    def primary(self, pub, now, *, accept=False):
        token = pub.reserve(pub.head, now, trigger='manual')
        if accept:
            pub.accept_source(pub.head, token, (), now, selection_validated_utc=now)
        else:
            pub.finish_request(pub.head, token, now, 'success')

    def preserved(self, pub):
        return {key: pub.ledger[key] for key in
                ('accepted', 'active', 'pending', 'generation', 'selection_validated_utc')}

    def test_captured_whole_traversal_reopens_preserves_ages_and_source_headroom(self):
        expected, files = captured()
        self.assertEqual(expected['schemaVersion'], 3)
        self.assertEqual(expected['queryPolicy']['pageSizes'], SIZES)
        self.assertEqual(expected['coverage']['counts'],
                         {'countries': 103, 'organizations': 350, 'models': 532, 'sites': 251})
        with self.authority() as (pub, store, code):
            self.primary(pub, NOW, accept=True)
            preserved = self.preserved(pub)
            transport = CapturedTransport(pub, expected, files)
            prefix = []
            done = False
            yields = 0
            for hour in range(6):
                instant = NOW + hour * 3600
                if hour:
                    pub = Publisher(store, code); pub.reconcile(None)
                    self.primary(pub, instant)
                    transport.pub = pub
                while True:
                    collector = CatalogRefresh(pub, transport=transport)
                    result = collector.run(instant, max_requests=4)
                    self.assertEqual(self.preserved(pub), preserved)
                    stage = collector.journal['staging']
                    if stage is not None:
                        self.assertEqual(stage['pages'][:len(prefix)], prefix)
                        prefix = deepcopy(stage['pages'])
                    if result.status == 'complete':
                        done = True
                        break
                    if result.status == 'yielded':
                        yields += 1
                        saved_head, calls = pub.head, len(transport.calls)
                        self.assertEqual(collector.run(instant).requests, 0)
                        self.assertEqual((pub.head, len(transport.calls)), (saved_head, calls))
                        # Metadata leaves eight primary slots at the shortest
                        # ordinary cadence, after one primary plus six metadata.
                        self.assertEqual(len(pub.ledger['requests']), 7)
                        break
                    pub = Publisher(store, code); pub.reconcile(None); transport.pub = pub
                if done:
                    break
            self.assertTrue(done)
            self.assertEqual(yields, 5)
            observed = collector.current()
            self.assertEqual(observed['reference'], expected['reference'])
            self.assertEqual(observed['coverage']['counts'], expected['coverage']['counts'])
            self.assertEqual(observed['coverage']['distinctIds'], expected['coverage']['distinctIds'])
            self.assertEqual(observed['coverage']['recordValidatedUtc'], expected['coverage']['recordValidatedUtc'])
            self.assertEqual([c['url'] for c in transport.calls], [p['url'] for p in expected['coverage']['pages']])
            self.assertEqual([c['sha256'] for c in transport.calls], [p['body']['sha256'] for p in expected['coverage']['pages']])
            self.assertEqual([p['validatedUtc'] for p in observed['coverage']['pages']],
                             [p['validatedUtc'] for p in expected['coverage']['pages']])
            self.assertEqual(observed['source']['completedUtc'], NOW + 18000)
            self.assertEqual(observed['queryPolicy'], dict(origin='https://ll.thespacedevs.com',
                pageSizes=SIZES, maxSourceAgeSeconds=86400, sitesOrdering='id'))
            pub = Publisher(store, code); pub.reconcile(None)
            self.assertEqual(CatalogRefresh(pub).current(), observed)
            head = pub.head
            self.assertEqual(scheduled(pub, NOW + 18001)['status'], 'not_due')
            self.assertEqual(pub.head, head)
            # A newly pinned current candidate with an old candidate version
            # must refuse; a matching content digest does not grant admission.
            for version in (1, 2):
                altered = dict(observed, schemaVersion=version)
                raw = _canonical(altered); digest = hashlib.sha256(raw).hexdigest()
                journal = deepcopy(collector.journal)
                journal['current'] = dict(sha256=digest, bytes=len(raw))
                saved = _canonical(journal)
                ref = dict(sha256=hashlib.sha256(saved).hexdigest(), bytes=len(saved))
                objects = {name: data for name, data in collector.objects.items()
                           if name.startswith('catalog-refresh/objects/')}
                objects['catalog-refresh/objects/' + digest + '.json'] = raw
                objects[_catalog_ref(ref)] = saved
                pub.checkpoint_catalog(pub.head, NOW + 18001, ref, objects)
                with self.assertRaises(RefreshError):
                    CatalogRefresh(Publisher(store, code))
                # Restore the same current bytes through the same explicit CAS;
                # neither source state nor reservations are replaced.
                original = _canonical(collector.journal)
                original_ref = dict(sha256=hashlib.sha256(original).hexdigest(), bytes=len(original))
                objects[_catalog_ref(original_ref)] = original
                pub.checkpoint_catalog(pub.head, NOW + 18001, original_ref, objects)
            self.assertEqual(self.preserved(pub), preserved)
            print(json.dumps(dict(control='captured-current3-whole', pages=len(transport.calls),
                fixtureSha256=json.loads(RECEIPT.read_bytes())['archiveSha256'],
                yields=yields, sourceAgePreserved=pub.ledger['selection_validated_utc'],
                counts=observed['coverage']['counts'])))

    def test_expired_current_prefix_restarts_without_renewing_source_or_quota(self):
        expected, files = captured()
        with self.authority() as (pub, store, code):
            self.primary(pub, NOW, accept=True)
            preserved = self.preserved(pub)
            transport = CapturedTransport(pub, expected, files)
            transport.epoch = NOW - 59
            collector = CatalogRefresh(pub, transport=transport, max_source_age_seconds=60)
            self.assertEqual(collector.run(NOW).status, 'partial')
            first = deepcopy(collector.journal['staging']['pages'][0])
            self.assertEqual(first['validatedUtc'], NOW - 59)
            before_requests = deepcopy(pub.ledger['requests'])
            pub = Publisher(store, code); pub.reconcile(None); transport.pub = pub
            transport.epoch = NOW + 2
            collector = CatalogRefresh(pub, transport=transport, max_source_age_seconds=60)
            self.assertEqual(collector.run(NOW + 2).status, 'partial')
            restarted = collector.journal['staging']['pages']
            self.assertEqual(len(restarted), 1)
            self.assertEqual(restarted[0]['body'], first['body'])
            self.assertEqual(restarted[0]['validatedUtc'], NOW + 2)
            self.assertEqual(collector.journal['staging']['startedUtc'], NOW + 2)
            self.assertEqual(pub.ledger['requests'][:-1], before_requests)
            self.assertEqual(len(transport.calls), 2)
            self.assertEqual(transport.calls[0]['url'], transport.calls[1]['url'])
            self.assertEqual(self.preserved(pub), preserved)
            # Ordinary reopen resumes after the new first page with its exact
            # source epoch; rebuilding the checkpoint never changes that epoch.
            pub = Publisher(store, code); pub.reconcile(None); transport.pub = pub
            collector = CatalogRefresh(pub, transport=transport, max_source_age_seconds=60)
            self.assertEqual(collector.run(NOW + 3).status, 'partial')
            self.assertEqual(collector.journal['staging']['pages'][0], restarted[0])
            self.assertEqual(len(pub.ledger['requests']), 4)
            self.assertEqual(self.preserved(pub), preserved)



if __name__ == '__main__':
    unittest.main()
