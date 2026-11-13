"""Independent public cloud CLI witness; all Git/HTTP are disposable and local.

Run from a clean public source checkout. The source-adoption event uses two
real disposable Git revisions with the same available tree; this is not an
old-code execution witness. No ancestor objects or live LL2 are required.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_catalog_refresh import git
from tests.test_cloud_delivery import World, literal_files
from tests.test_metadata_page_policy import source_server, suffix, encoded
from tools.spacefox.catalog_refresh import CatalogRefresh, RefreshError
from tools.spacefox.publisher import GitState, Publisher

ROOT = Path(__file__).resolve().parents[1]


def preserved(pub):
    return deepcopy({k: pub.ledger.get(k) for k in ('accepted', 'active', 'pending', 'generation',
        'selection_validated_utc', 'last_poll_utc')})


class PublicMetadataProjectionTest(unittest.TestCase):
    def test_cloud_cli_adoption_legacy_duplicate_quota_recovery_and_pending(self):
        self.assertEqual('', git(ROOT, 'status', '--porcelain'))
        code = git(ROOT, 'rev-parse', 'HEAD')
        with tempfile.TemporaryDirectory(prefix='spacefox-public-cli-') as folder:
            remote = Path(folder) / 'remote.git'
            subprocess.run(['git', 'clone', '--bare', '--no-hardlinks', '-q', str(ROOT), str(remote)], check=True)
            # A distinct source event exercises real adoption without requiring
            # historical Git objects in a single-commit/shallow public checkout.
            initial_code = git(remote, '-c', 'user.name=Public source fixture',
                               '-c', 'user.email=fixture@example.invalid',
                               'commit-tree', code + '^{tree}', '-m', 'Initial source authority fixture')
            self.assertNotEqual(code, initial_code)
            git(remote, 'update-ref', 'refs/heads/main', initial_code)
            store = GitState(str(remote))
            world = World(remote)
            try:
                store.bootstrap(initial_code)
                pub = Publisher(store, initial_code)
                pub.reconcile(None)
                slot = pub.reserve(pub.head, 1000, trigger='manual')
                pub.accept_source(pub.head, slot, (), 1000)
                with source_server(remote, counts=dict(countries=1, organizations=1, models=1, sites=2)) as (state, _, origin):
                    # Legacy schema/query checkpoint through real owner events.
                    collector = CatalogRefresh(pub, origin=origin, local_http=True, page_size=1)
                    self.assertEqual('partial', collector.run(1001, max_requests=4).status)
                    before = preserved(pub)
                    prefix = deepcopy(collector.journal['staging']['pages'])
                    cache = deepcopy(collector.journal['cache'])
                    bodies = {p['body']['sha256']: collector._read(p['body']) for p in prefix[:3]}
                    self.assertEqual(1, collector.journal['schemaVersion'])
                    git(remote, 'update-ref', 'refs/heads/main', code)
                    def cli(command='metadata', now=1002, expected=0):
                        argv = [sys.executable, '-B', str(ROOT / 'tools/cloud_feed.py'), '--repository', 'local/SpaceFox',
                            '--remote', str(remote), '--site', world.base + '/site', '--api', world.base,
                            '--origin', origin, '--local-qualification', '--now', str(now), command]
                        # Credentials and CI output are intentionally absent, not inherited.
                        env = {k: v for k, v in os.environ.items() if not k.startswith('GITHUB_') and k not in ('GH_TOKEN', 'PYTHONPATH')}
                        run = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=90)
                        print(json.dumps(dict(command=argv, exit=run.returncode, stdout=run.stdout, stderr=run.stderr)), flush=True)
                        self.assertEqual(expected, run.returncode, run.stderr)
                        return run
                    head = pub.head
                    self.assertIn('source writer adoption first', cli(expected=2).stderr)
                    self.assertEqual(head, store.load()[0])
                    self.assertEqual(4, len(state['calls']))
                    cli('recover')
                    pub = Publisher(store, code); pub.reconcile(None)
                    self.assertEqual(before, preserved(pub))
                    self.assertEqual(code, pub.ledger['code_revision'])
                    old_requests = deepcopy(pub.ledger['requests'])
                    # Migration restarts pads with ordering=id; inject the same
                    # typed overlap on its second page, with coherent links.
                    path = suffix(3, 1, 1, True)
                    state['overrides'][path] = encoded(dict(count=2, next=None, previous=origin + suffix(3, 1, ordered=True),
                        results=[deepcopy(state['rows']['sites'][0])]))
                    state['now'] = 1002
                    self.assertIn('duplicate source identity', cli(expected=2).stderr)
                    pub = Publisher(store, code); pub.reconcile(None)
                    recovered = CatalogRefresh(pub, origin=origin, local_http=True, stable_sites_order=True)
                    self.assertEqual(3, recovered.journal['schemaVersion'])
                    self.assertEqual(prefix[:3], recovered.journal['staging']['pages'])
                    self.assertEqual(before, preserved(pub))
                    self.assertEqual(old_requests, pub.ledger['requests'][:-2])
                    self.assertEqual(['success', 'failed'], [r['outcome'] for r in pub.ledger['requests'][-2:]])
                    self.assertEqual('failed', pub.ledger['requests'][-1]['outcome'])
                    self.assertGreater(pub.ledger['backoff_until_utc'], 1002)
                    # The abandoned unordered URL stays separately cached; failed
                    # ordered pages cannot populate or evict that other query.
                    expected_cache = {url: dict(meta, pageSize=1) for url, meta in cache.items()}
                    self.assertEqual(expected_cache, recovered.journal['cache'])
                    self.assertEqual(bodies, {p['body']['sha256']: recovered._read(p['body']) for p in prefix[:3]})
                    calls = list(state['calls']); failed_head = pub.head
                    self.assertEqual('yielded', json.loads(cli(now=1003).stdout)['status'])
                    self.assertEqual(calls, state['calls']); self.assertEqual(failed_head, store.load()[0])
                    del state['overrides'][path]
                    state['now'] = 5000
                    self.assertEqual('yielded', json.loads(cli(now=5000).stdout)['status'])
                    self.assertEqual(calls, state['calls'])  # due primary source wins
                    pub = Publisher(store, code); pub.reconcile(None)
                    slot = pub.reserve(pub.head, 5000, trigger='manual')
                    pub.accept_source(pub.head, slot, (), 5000)
                    before = preserved(pub)
                    state['now'] = 5001
                    finished = json.loads(cli(now=5001).stdout)
                    self.assertEqual(('complete', 2), (finished['status'], finished['requests']))
                    self.assertEqual([(suffix(3, 1, ordered=True), None), (suffix(3, 1, 1, True), None)], state['calls'][-2:])
                    pub = Publisher(store, code); pub.reconcile(None)
                    current = CatalogRefresh(pub, origin=origin, local_http=True, stable_sites_order=True).current()
                    self.assertEqual(prefix[:3], current['coverage']['pages'][:3])
                    self.assertEqual(dict(countries=1, organizations=1, models=1, sites=2), current['coverage']['counts'])
                    self.assertEqual(before, preserved(pub))
                    self.assertEqual([1001, 1001, 1001, 5001, 5001], [p['validatedUtc'] for p in current['coverage']['pages']])
                    self.assertEqual(3, len(pub.ledger['requests']))  # new hour: one primary + two catalog attempts
                    calls = list(state['calls'])
                    self.assertEqual('not_due', json.loads(cli(now=5002).stdout)['status'])
                    self.assertEqual(calls, state['calls'])
                    # Real publication event proves cloud pending wins before metadata/site work.
                    files, digest = literal_files(pub.ledger['instance_id'])
                    pub.prepare(pub.head, 5003, files, digest, feed_publisher=pub.publisher_envelope(5003))
                    snapshot, reads = deepcopy(pub.ledger), list(world.gets)
                    self.assertEqual('yielded_pending', json.loads(cli(now=5003).stdout)['status'])
                    self.assertEqual(snapshot, store.load()[1]); self.assertEqual(reads, world.gets)
                    self.assertEqual(calls, state['calls']); self.assertEqual([], world.posts)
            finally:
                world.close(); store.close()

    def test_durable_typed_duplicate_remains_hard_refusal(self):
        # Explicit corrupt durable-state fixture: valid Git/object hashes cannot
        # make duplicated typed source identities an admissible checkpoint.
        from tests.test_catalog_refresh import CatalogRefreshTest
        from tools.spacefox.catalog_refresh import object_ref, object_path
        with CatalogRefreshTest().authority(with_launch=False) as (_, _, remote, store, pub, _):
            with source_server(remote, counts=dict(countries=2, organizations=1, models=1, sites=1)) as (state, _, origin):
                c = CatalogRefresh(pub, origin=origin, local_http=True, page_size=2)
                c.run(1001)
                page = c.journal['staging']['pages'][0]
                raw = json.loads(c._read(page['body']))
                raw['results'][1] = deepcopy(raw['results'][0])
                body = encoded(raw); page['body'] = object_ref(body)
                c.journal['cache'][page['url']]['body'] = page['body']
                journal = encoded(c.journal); ref = object_ref(journal)
                pub.checkpoint_catalog(pub.head, 1002, ref, {'catalog-refresh/journals/' + ref['sha256'] + '.json': journal,
                    object_path(page['body']): body})
                frozen = store.load(); calls = list(state['calls'])
                with self.assertRaisesRegex(RefreshError, 'duplicate source identity'):
                    CatalogRefresh(pub, origin=origin, local_http=True, page_size=2)
                self.assertEqual(frozen, store.load()); self.assertEqual(calls, state['calls'])


if __name__ == '__main__':
    unittest.main()
