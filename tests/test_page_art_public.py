"""Portable current-public composition probe; no hosted/native acceptance.

Exact public G7 raw metadata pages are installed as explicit fixture setup in a
fresh Git authority. Only the external official HTTP endpoint is relayed to a
loopback server. Catalog, scheduled policy, Git CAS, quota and exporter are real.
"""
from copy import deepcopy
from email.utils import formatdate
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from urllib.parse import urlsplit

from tools.refresh_catalog import scheduled
from tools.spacefox.catalog_refresh import CatalogRefresh, CatalogHTTPTransport
from tools.spacefox.publisher import GitState, Publisher, StateError

ROOT = Path(__file__).resolve().parents[1]
PREFIX = ROOT / 'tests/fixtures/metadata-page-policy'
NOW = 1794477403


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args]).decode().strip()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class PageArtPublicTest(unittest.TestCase):
    def test_current_public_prefix_policy_sparse_closure_and_radial_producer(self):
        self.assertFalse((ROOT / '.agents').exists(), 'execute in the exported public checkout')
        self.assertFalse(git(ROOT, 'status', '--porcelain'))
        manifest = json.loads((ROOT / 'distribution/publisher-source-snapshot.json').read_bytes())
        for path in manifest['files']:
            if path.startswith('tests/test_') and path.endswith('.py'):
                importlib.import_module(path[:-3].replace('/', '.'))
        self.assertEqual('2026-11-12.global.8.current2026-review1',
                         json.loads((ROOT / 'catalog/source.json').read_bytes())['catalogVersion'])
        raw_journal = (PREFIX / 'observed-journal.raw.json').read_bytes()
        self.assertEqual('f4afca950f9ddc6ff7275a2bbae04a1645244078a5e0f34f0aa1cfb1f59a8a43', digest(raw_journal))
        legacy = json.loads(raw_journal)
        prefix = deepcopy(legacy['staging']['pages'])
        self.assertEqual([20] * 4, [p['rows'] for p in prefix])
        self.assertEqual([1794477356, 1794477371, 1794477386, 1794477402],
                         [p['validatedUtc'] for p in prefix])
        with tempfile.TemporaryDirectory(prefix='spacefox-public-page-art-') as folder:
            base = Path(folder)
            remote = base / 'authority.git'
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            code = git(ROOT, 'rev-parse', 'HEAD')
            subprocess.run(['git', '-C', str(ROOT), 'push', '-q', str(remote),
                            'HEAD:refs/heads/main'], check=True)
            store = GitState(str(remote))
            store.bootstrap(code)
            pub = Publisher(store, code)
            pub.reconcile(None)
            slot = pub.reserve(pub.head, 1794474006)
            pub.accept_source(pub.head, slot, (), 1794474006)
            files = {'catalog-refresh/journals/' + digest(raw_journal) + '.json': raw_journal}
            for page in prefix:
                raw = (PREFIX / (page['body']['sha256'] + '.json')).read_bytes()
                self.assertEqual(page['body'], {'sha256': digest(raw), 'bytes': len(raw)})
                files['catalog-refresh/objects/' + digest(raw) + '.json'] = raw
            pub.checkpoint_catalog(pub.head, NOW, {'sha256': digest(raw_journal), 'bytes': len(raw_journal)}, files)
            source = deepcopy(pub.ledger)
            calls = []
            test = self

            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *_args):
                    pass

                def do_GET(self):
                    observer = GitState(str(remote))
                    try:
                        _, ledger = observer.load()
                        test.assertEqual(('catalog', 'reserved'),
                            (ledger['requests'][-1]['purpose'], ledger['requests'][-1]['outcome']))
                    finally:
                        observer.close()
                    calls.append(self.path)
                    countries = '/2.3.0/config/countries/' in self.path
                    model = '/launcher_configurations/' in self.path
                    if countries:
                        offset = 80 if 'offset=80' in self.path else 100
                        rows = [dict(id=i, name='Literal tail ' + str(i), alpha_2_code='XY', alpha_3_code='XYZ')
                                for i in range(offset + 1, min(offset + 21, 104))]
                        next_url = 'https://ll.thespacedevs.com/2.3.0/config/countries/?format=json&limit=20&offset=100' if offset == 80 else None
                        count = 103
                        previous = 'https://ll.thespacedevs.com/2.3.0/config/countries/?format=json&limit=20&offset=' + str(offset - 20)
                    else:
                        path = urlsplit(self.path).path
                        row = dict(id=123, name='Literal public model' if model else 'Literal public agency',
                                   url='https://ll.thespacedevs.com' + path + '123/',
                                   response_mode='detailed' if model else 'normal')
                        row.update(dict(full_name=row['name'], variant='', active=False, pending_launches=0,
                                        is_placeholder=False, families=[], manufacturer=None) if model
                                   else dict(abbrev='', type=None, country=[]))
                        rows, next_url, count, previous = [row], None, 1, None
                    raw = json.dumps(dict(count=count, next=next_url, previous=previous, results=rows),
                                     separators=(',', ':')).encode()
                    self.send_response_only(200)
                    self.send_header('Date', formatdate(NOW, usegmt=True))
                    self.send_header('Content-Type', 'application/json')
                    self.send_header('Content-Length', str(len(raw)))
                    self.end_headers()
                    self.wfile.write(raw)

            server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            class Relay:
                def get(self, url, etag=None):
                    parts = urlsplit(url)
                    return CatalogHTTPTransport().get('http://127.0.0.1:' + str(server.server_port)
                                                       + parts.path + '?' + parts.query, etag)
            try:
                result = scheduled(pub, NOW, transport=Relay())
                self.assertEqual(('partial', 4), (result['status'], result['requests']))
                expected = ['/2.3.0/config/countries/?format=json&limit=20&offset=80',
                            '/2.3.0/config/countries/?format=json&limit=20&offset=100',
                            '/2.3.0/agencies/?format=json&limit=100&mode=normal',
                            '/2.3.0/launcher_configurations/?format=json&limit=100&mode=detailed']
                self.assertEqual(expected, calls)
                collector = CatalogRefresh(pub, transport=Relay())
                self.assertEqual(prefix, collector.journal['staging']['pages'][:4])
                self.assertEqual(dict(countries=20, organizations=100, models=100, sites=100),
                                 collector.journal['staging']['pageSizes'])
                self.assertIsNone(collector.current())
                for field in ('accepted', 'active', 'pending', 'generation', 'last_poll_utc', 'selection_validated_utc'):
                    self.assertEqual(source.get(field), pub.ledger.get(field), field)
                self.assertEqual(source['requests'], pub.ledger['requests'][:-4])
                stable = pub.head
                with self.assertRaises(StateError):
                    CatalogRefresh(pub, page_size=20, transport=Relay())
                self.assertEqual(stable, pub.head)
                self.assertEqual(4, len(calls))
            finally:
                server.shutdown()
                server.server_close()
                thread.join()
                store.close()
            # Use the real current producer CLI; literal exact model/asset/rights
            # are an oracle independent of the recipe's selected asset lookup.
            output = base / 'visuals'
            result = subprocess.run([sys.executable, '-B', 'tools/export_visuals.py', '--output', str(output),
                                     '--root', 'll2:configuration:123'], cwd=ROOT, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr.decode())
            visual = json.loads((output / 'manifest.json').read_bytes())
            model = visual['selection']['dictionaries']['configurations']['ll2:configuration:123']
            identity = 'spacefox:asset:further-r2-lm5-yz2-radial-firstflight'
            self.assertEqual(identity, model['references']['visual'])
            self.assertIsNone(model['references']['origin'])
            asset = visual['assets'][identity]
            self.assertEqual('MIT', asset['rights']['license'])
            self.assertIn('SpaceFox', asset['rights']['credit'])
            self.assertEqual(['ll2:configuration:123'], asset['catalogRecord']['facts']['coverage']['configurationIds'])
            for shard in asset['shards']:
                raw = (output / shard['path']).read_bytes()
                self.assertEqual(shard['sha256'], digest(raw))
                self.assertLessEqual(len(raw), 4096)
            # Execute the actual YAML sparse shell without invoking a historical
            # long behavior suite or full current-source materializer.
            checkout = base / 'sparse'
            subprocess.run(['git', 'clone', '-q', '--no-checkout', str(ROOT), str(checkout)], check=True)
            git(checkout, 'sparse-checkout', 'init', '--no-cone')
            git(checkout, 'sparse-checkout', 'set', '--no-cone', '/.github/spacefox-inputs.txt')
            git(checkout, 'checkout', '-q')
            from tests.test_cloud_runtime_checkout import job_script
            script = job_script('metadata', 'Check out runtime seed for exact saved-state validation')
            result = subprocess.run(['bash', '-eu', '-c', script], cwd=checkout, capture_output=True)
            self.assertEqual(0, result.returncode, result.stderr.decode())
            runtime = {p.relative_to(checkout).as_posix() for p in checkout.rglob('*')
                       if p.is_file() and '.git' not in p.relative_to(checkout).parts}
            self.assertEqual(21, len(runtime))
            self.assertFalse(any(p.startswith(('catalog/', 'assets/', 'tests/', '.agents/')) for p in runtime))
            print('PUBLIC_PAGE_ART ' + json.dumps(dict(public=code, metadataRequests=4, primaryDuringMetadata=0,
                exactPrefixRows=80, candidateComplete=False, automaticAdoption=False, sparseFiles=len(runtime),
                producerAsset=identity, producerDigest=asset['sha256'], unknownOrigin=True,
                importedPublicTests=sum(p.startswith('tests/test_') and p.endswith('.py') for p in manifest['files']))))


if __name__ == '__main__':
    unittest.main()
