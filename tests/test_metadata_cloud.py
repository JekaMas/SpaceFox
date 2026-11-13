"""Directed metadata scheduling and real public sparse rich-artifact integration.

Only external provider/Pages/Actions/OIDC transport is substituted by loopback.
No validator, collector, builder, quota owner, Git CAS or live reader is replaced.
"""
from email.utils import formatdate
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import subprocess
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

from tests import test_cloud_runtime_checkout as runtime
from tests import test_catalog_refresh as literal
from tools.refresh_catalog import scheduled
from tools.spacefox.catalog_refresh import CatalogRefresh
from tools.spacefox.cloud import arm, journal
from tools.spacefox.publisher import GitState, LiveRevision, Publisher, StateError
from tools.spacefox.schedule import (IdKind, LaunchRecord, LaunchStatus, RefreshPolicy,
                                     StableId, TimePrecision, Timing)

ROOT = Path(__file__).resolve().parents[1]
NOW = runtime.NOW


class MetadataCadenceTest(unittest.TestCase):
    def test_daily_partial_resume_304_deadline_and_immutable_export(self):
        with literal.CatalogRefreshTest().authority() as (_, _, _, store, pub, transport):
            preserved = {k: pub.ledger[k] for k in ('accepted', 'active', 'pending', 'generation',
                         'selection_validated_utc', 'last_poll_utc')}
            settings = dict(transport=transport)
            first = scheduled(pub, 1001, max_requests=2, **settings)
            self.assertEqual(('partial', 2), (first['status'], first['requests']))
            self.assertEqual(2, len(CatalogRefresh(pub, stable_sites_order=True, **settings).journal['staging']['pages']))
            transport.now = 1002
            second = scheduled(pub, 1002, max_requests=2, **settings)
            self.assertEqual(('complete', 2), (second['status'], second['requests']))
            saved = pub.head
            current = CatalogRefresh(pub, stable_sites_order=True, **settings).current()
            self.assertEqual({'countries': 2, 'organizations': 1, 'models': 2, 'sites': 1}, current['coverage']['counts'])
            self.assertEqual([1001, 1001, 1002, 1002], [p['validatedUtc'] for p in current['coverage']['pages']])
            # Completion age, not current source age or wall tick, controls due.
            for at in (1003, 87401):
                result = scheduled(pub, at, **settings)
                self.assertEqual(('not_due', 0, saved), (result['status'], result['requests'], pub.head))
            self.assertEqual(4, len(transport.calls))
            # Source writer's next successful event owns its own launch epochs.
            token = pub.reserve(pub.head, 87402, trigger='manual')
            pub.accept_source(pub.head, token, (literal.launch(1000),), 87402)
            preserved = {k: pub.ledger[k] for k in preserved}
            transport.now = 87402
            transport.conditional = True
            result = scheduled(pub, 87402, **settings)
            self.assertEqual(('complete', 4), (result['status'], result['requests']))
            collector = CatalogRefresh(pub, stable_sites_order=True, **settings)
            self.assertEqual(second['completed'], collector.journal['previous'])
            self.assertEqual([304] * 4, [p['status'] for p in collector.current()['coverage']['pages']])
            self.assertEqual(87402, collector.current()['source']['completedUtc'])
            self.assertEqual(preserved, {k: pub.ledger[k] for k in preserved})
            self.assertEqual(8, len(transport.calls))
            self.assertLessEqual(store.measure()['catalog_blob_bytes'], 67108864)
            with self.assertRaisesRegex(StateError, 'cadence'):
                scheduled(pub, 87402, interval_seconds=3599, **settings)
            with self.assertRaisesRegex(StateError, 'invocation'):
                scheduled(pub, 87402, max_requests=5, **settings)

    def test_source_due_backoff_uncertainty_primary_capacity_and_fast_preflight(self):
        # Every row reaches the real scheduler/public allowance boundary. Literal
        # call/head/journal expectations distinguish observed no-mutation events.
        observed = {}
        for event in ('launch_due', 'backoff', 'uncertain', 'headroom', 'fast'):
            policy = RefreshPolicy(fast_interval_seconds=300) if event == 'fast' else None
            with literal.CatalogRefreshTest().authority(policy=policy) as (_, _, _, _, pub, transport):
                at = 1001
                if event == 'launch_due':
                    at = 4600
                elif event in ('backoff', 'uncertain'):
                    token = pub.reserve(pub.head, 1001, purpose='version', trigger='manual')
                    if event == 'backoff':
                        pub.finish_request(pub.head, token, 1001, 'failed')
                    at = 1002
                elif event == 'headroom':
                    for _ in range(6):
                        token = pub.reserve(pub.head, 1001, purpose='version', trigger='manual')
                        pub.finish_request(pub.head, token, 1001, 'success')
                before = pub.head, pub.ledger
                outcome = scheduled(pub, at, transport=transport)
                self.assertEqual(('yielded', 0), (outcome['status'], outcome['requests']), event)
                self.assertEqual(before, (pub.head, pub.ledger), event)
                self.assertEqual([], transport.calls, event)
                self.assertNotIn('catalog_refresh', pub.ledger, event)
                observed[event] = 'observed_no_mutation'
        self.assertEqual({e: 'observed_no_mutation' for e in
                         ('launch_due', 'backoff', 'uncertain', 'headroom', 'fast')}, observed)

    def test_workflow_same_minutes_source_first_failure_gates_and_fault_exact(self):
        text = (ROOT / '.github/workflows/update-feed.yml').read_text()
        self.assertEqual(['7 * * * *', '22 * * * *', '37 * * * *', '52 * * * *'],
                         [line.split("'")[1] for line in text.splitlines() if '- cron:' in line])
        # All four hours have identical minute sets, no added ticks/provider jobs.
        old = {hour * 60 + minute for hour in range(24) for minute in (7, 22, 37, 52)}
        new = {hour * 60 + int(line.split("'")[1].split()[0]) for hour in range(24)
               for line in text.splitlines() if '- cron:' in line}
        self.assertEqual(old, new)
        self.assertEqual(1, text.count('group: spacefox-whole-publisher-v1'))
        metadata = text.split('\n  metadata:\n')[1]
        self.assertIn('needs: [prepare, arm, deploy, promote]', metadata)
        condition = "if: always() && needs.prepare.result == 'success' && (needs.prepare.outputs.pending == 'false' || needs.promote.result == 'success')"
        self.assertIn(condition, metadata)
        # Literal required observations for success/skips/fault/failure. This
        # table tests this exact declarative expression, not an Actions runner.
        for prepare, pending, promote, want in [('success', 'false', 'skipped', True),
                ('success', 'true', 'success', True), ('failure', 'false', 'skipped', False),
                ('success', 'true', 'failure', False), ('success', 'true', 'skipped', False)]:
            self.assertEqual(want, prepare == 'success' and (pending == 'false' or promote == 'success'))
        self.assertIn('qualify_pre_post_recovery:\n', text)
        self.assertIn("if: github.event_name == 'workflow_dispatch' && inputs.qualify_pre_post_recovery", text)
        self.assertIn('          exit 97', text)
        self.assertIn("      qualify_pre_post_recovery:\n        description: Deliberately fail after durable arm to qualify skipped-deploy recovery\n        type: boolean\n        default: false", text)


class MetadataCloudTest(unittest.TestCase):
    setUp = runtime.CloudRuntimeCheckoutTest.setUp
    tearDown = runtime.CloudRuntimeCheckoutTest.tearDown
    snapshot = runtime.CloudRuntimeCheckoutTest.snapshot
    cli = runtime.CloudRuntimeCheckoutTest.cli
    runtime = runtime.CloudRuntimeCheckoutTest.runtime

    def arguments(self, *command):
        args = runtime.CloudRuntimeCheckoutTest.arguments(self, *command)
        if hasattr(self, 'metadata_origin'):
            args[args.index('--origin') + 1] = self.metadata_origin
        if hasattr(self, 'logical_now'):
            args[args.index('--now') + 1] = str(self.logical_now)
        return args

    def publisher(self):
        store = GitState(str(self.remote)); self.stores.append(store)
        return Publisher(store, self.code)

    def rich_authority(self):
        store = GitState(str(self.remote)); self.stores.append(store); store.bootstrap(self.code)
        pub = Publisher(store, self.code); pub.reconcile(None)
        identity = lambda kind, value: StableId(kind, 'll2', value)
        record = LaunchRecord(identity(IdKind.LAUNCH, 'bridge-literal'),
            Timing(TimePrecision.EXACT, exact_utc=NOW + 7200), LaunchStatus.PENDING, NOW - 3600,
            configuration_id=identity(IdKind.CONFIGURATION, '164'), operator_id=identity(IdKind.ORGANIZATION, '121'),
            site_id=identity(IdKind.SITE, '80'), country_id=identity(IdKind.COUNTRY, '2'),
            configuration_name='Falcon 9', operator_name='SpaceX', mission_name='Луна 零',
            mission_purpose='Measure lunar radiation', country_code='USA', site_location_name='Florida')
        token = pub.reserve(pub.head, NOW)
        pub.accept_source(pub.head, token, (record,), NOW, selection_validated_utc=NOW - 3600)
        corpus = ROOT / 'tests/fixtures/bridge-v2/a'
        files = {p.relative_to(corpus).as_posix(): p.read_bytes() for p in corpus.rglob('*') if p.is_file()}
        self.assertEqual((76, 524776), (len(files), sum(map(len, files.values()))))
        for path in ('feed.json', 'wire2/feed.json'):
            value = json.loads(files[path]); value['publisher'] = pub.publisher_envelope(NOW)
            files[path] = runtime.encoded(value)
        pub.prepare(pub.head, NOW, files, json.loads(files['feed.json'])['catalogDigest'],
                    feed_publisher=pub.publisher_envelope(NOW), artifact_profile='visual-v2')
        self.service.live = dict(files)
        pub, intent = arm(pub, expected=pub.head, repository='owner/SpaceFox',
                          run_id=85, run_attempt=1, artifact_id=899, now=NOW)
        self.service.statuses[intent['buildVersion']] = 'succeed'
        self.cli('recover')
        pub = self.publisher()
        return pub, files, record

    def metadata_server(self):
        test = self
        state = {'calls': [], 'now': NOW, 'age': 2, 'conditional': True}

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                check = GitState(str(test.remote))
                try:
                    _, ledger = check.load()
                    assert ledger['requests'][-1]['purpose'] == 'catalog'
                    assert ledger['requests'][-1]['outcome'] == 'reserved'
                finally:
                    check.close()
                raw = state['bodies'][self.path.split('?')[0]]
                tag = '"' + hashlib.sha256(raw).hexdigest() + '"'
                status = 304 if state['conditional'] and self.headers.get('If-None-Match') == tag else 200
                state['calls'].append((self.path, status, ledger['requests'][-1]['at_utc']))
                self.send_response_only(status)
                self.send_header('Date', formatdate(state['now'], usegmt=True))
                self.send_header('Age', str(state['age']))
                self.send_header('ETag', tag)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw) if status == 200 else 0))
                self.end_headers()
                if status == 200:
                    self.wfile.write(raw)
        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.metadata_origin = f'http://127.0.0.1:{server.server_port}'
        origin = self.metadata_origin
        rows = {
            '/2.3.0/config/countries/': [dict(id=2, name='United States', alpha_2_code='US', alpha_3_code='USA')],
            '/2.3.0/agencies/': [dict(id=121, name='SpaceX', url=origin + '/2.3.0/agencies/121/',
                response_mode='normal', abbrev='SpX', type=None, country=[{'id': 2}])],
            '/2.3.0/launcher_configurations/': [dict(id=164, name='Falcon 9',
                url=origin + '/2.3.0/launcher_configurations/164/', response_mode='detailed',
                full_name='Falcon 9 literal fixture', variant='', active=False, pending_launches=1,
                is_placeholder=False, families=[], manufacturer={'id': 121, 'country': [{'id': 2}]})],
            '/2.3.0/pads/': [dict(id=80, name='Literal launch pad', url=origin + '/2.3.0/pads/80/',
                active=False, location=None, country={'id': 2}, latitude=None, longitude=None, agencies=[{'id': 121}])],
        }
        state['bodies'] = {path: json.dumps(dict(count=1, next=None, previous=None, results=value),
                             separators=(',', ':')).encode() for path, value in rows.items()}
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close(), thread.join()))
        return state

    def test_sparse_cli_rich_checkpoint_source_adoption_and_pending_preservation(self):
        self.runtime('metadata')
        pub, files, record = self.rich_authority()
        world = self.metadata_server()
        original = pub.ledger
        original_journal = runtime.git(self.remote, 'show', f'{pub.head}:cloud.json')
        # Actual saved-state readback first, then two-request partial checkpoint.
        first = self.cli('metadata', '--max-requests', '2')
        self.assertEqual(('partial', 2), (first['status'], first['requests']))
        pub = self.publisher()
        collector = CatalogRefresh(pub, origin=self.metadata_origin, local_http=True, stable_sites_order=True)
        self.assertEqual(2, len(collector.journal['staging']['pages']))
        corpus = git_tree(self.remote, pub.head, 'catalog-refresh')
        # Real source writer event retains exact auxiliary tree and source date.
        pub.reconcile(LiveRevision(1, pub.ledger['active']['artifact_revision']))
        slot = pub.reserve(pub.head, NOW, trigger='manual')
        pub.accept_source(pub.head, slot, (record,), NOW, selection_validated_utc=NOW - 3600)
        self.assertEqual(corpus, git_tree(self.remote, pub.head, 'catalog-refresh'))
        second = self.cli('metadata', '--max-requests', '2')
        self.assertEqual(('complete', 2), (second['status'], second['requests']))
        pub = self.publisher(); collector = CatalogRefresh(pub, origin=self.metadata_origin, local_http=True, stable_sites_order=True)
        candidate = collector.current()
        self.assertEqual({'countries': [2], 'organizations': [121], 'models': [164], 'sites': [80]}, candidate['coverage']['distinctIds'])
        self.assertEqual([NOW - 2] * 4, [p['validatedUtc'] for p in candidate['coverage']['pages']])
        self.assertEqual([hashlib.sha256(v).hexdigest() for v in world['bodies'].values()],
                         [p['body']['sha256'] for p in candidate['coverage']['pages']])
        self.assertEqual([200] * 4, [row[1] for row in world['calls']])
        self.assertEqual(files, {p.split('/', 2)[2]: raw for p, raw in pub.store._files(pub.head, pub.ledger).items()})
        self.assertEqual(original_journal, runtime.git(self.remote, 'show', f'{pub.head}:cloud.json'))
        for key in ('accepted', 'active', 'pending', 'generation', 'last_poll_utc', 'selection_validated_utc'):
            self.assertEqual(original[key], pub.ledger[key], key)
        head = pub.head
        idle = self.cli('metadata')
        self.assertEqual(('not_due', 0), (idle['status'], idle['requests']))
        self.assertEqual(head, self.publisher().head)
        corpus = git_tree(self.remote, head, 'catalog-refresh')
        # New source cannot be adopted by metadata, even with valid live files.
        runtime.git(self.source, 'commit', '--allow-empty', '-qm', 'compatible source event')
        old_code = self.code
        self.code = runtime.git(self.source, 'rev-parse', 'HEAD')
        runtime.git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        runtime.git(self.source, 'checkout', '-q', old_code)
        self.cli('metadata', success=False)
        self.assertEqual(head, self.publisher().head)
        runtime.git(self.source, 'checkout', '-q', self.code)
        self.cli('metadata', success=False)
        self.assertEqual(head, self.publisher().head)
        pub = self.publisher(); pub.adopt_code(pub.head)
        self.assertEqual(corpus, git_tree(self.remote, pub.head, 'catalog-refresh'))
        # A pending rich artifact with a different generation is armed by the
        # unchanged real cloud owner. Metadata must not recover/write/adopt it.
        pub.reconcile(LiveRevision(1, pub.ledger['active']['artifact_revision']))
        replacement = dict(files)
        for path in ('feed.json', 'wire2/feed.json'):
            value = json.loads(replacement[path]); value['publisher'] = pub.publisher_envelope(NOW)
            replacement[path] = runtime.encoded(value)
        pub.prepare(pub.head, NOW, replacement, json.loads(replacement['feed.json'])['catalogDigest'],
                    feed_publisher=pub.publisher_envelope(NOW), artifact_profile='visual-v2')
        pub, _ = arm(pub, expected=pub.head, repository='owner/SpaceFox', run_id=87, run_attempt=1, artifact_id=901, now=NOW)
        armed = pub.head, pub.ledger, runtime.git(self.remote, 'show', f'{pub.head}:cloud.json')
        result = self.cli('metadata')
        self.assertEqual(('yielded_pending', 0), (result['status'], result['requests']))
        self.assertEqual(armed, (self.publisher().head, self.publisher().ledger,
                         runtime.git(self.remote, 'show', f'{pub.head}:cloud.json')))
        self.assertEqual('armed', journal(pub)['status'])
        self.assertEqual(corpus, git_tree(self.remote, pub.head, 'catalog-refresh'))
        self.assertEqual((4, 0, 0), (len(world['calls']), len(self.service.posts), self.service.provider_calls))
        # Existing recovery still refuses unknown/started service finality. The
        # exact rich pending and auxiliary tree survive this refused invocation.
        self.cli('recover', success=False)
        self.assertEqual(armed[:2], (self.publisher().head, self.publisher().ledger))
        self.assertEqual(corpus, git_tree(self.remote, pub.head, 'catalog-refresh'))
        self.service.statuses[journal(pub)['intent']['buildVersion']] = 'succeed'
        self.service.live = dict(replacement)
        self.cli('recover')
        pub = self.publisher()
        self.assertIsNone(pub.ledger['pending'])
        self.assertEqual(2, pub.ledger['active']['generation'])
        self.assertEqual('succeed', journal(pub)['status'])
        self.assertEqual(corpus, git_tree(self.remote, pub.head, 'catalog-refresh'))
        self.assertEqual(('not_due', 0), tuple((lambda r: (r['status'], r['requests']))(self.cli('metadata'))))
        print('METADATA_RICH_TRACE ' + json.dumps({'richFiles': len(files), 'http': 4,
             'literalSourceUtc': NOW - 2, 'sourceEpoch': NOW - 3600,
             'reservationBeforeEveryHTTP': True, 'catalogPreservedAcrossSourceAndCode': True,
             'unknownArmedRefused': True, 'providerPolls': 0, 'posts': 0}, sort_keys=True))


    def test_portable_prepare_guard_and_metadata_cli_smoke(self):
        script = runtime.job_script('prepare', 'Materialize exact reviewed runtime and catalog closure')
        materialize = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script],
                                    cwd=self.source, capture_output=True)
        self.assertEqual(0, materialize.returncode, materialize.stderr.decode())
        self.assertEqual(596, json.loads(materialize.stdout)['catalogInputs'])
        recipe = self.source / 'catalog/source.json'
        original = recipe.read_bytes()
        recipe.write_bytes(original + b' ')
        refused = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script],
                                cwd=self.source, capture_output=True)
        self.assertNotEqual(0, refused.returncode)
        self.assertEqual(original + b' ', recipe.read_bytes())
        self.assertEqual(0, self.service.provider_calls)
        self.assertNotEqual(0, subprocess.run(['git', '-C', str(self.remote), 'rev-parse',
                            '--verify', 'refs/heads/feed-state'], capture_output=True).returncode)
        recipe.write_bytes(original)
        output = self.base / 'site'
        prepared = subprocess.run([__import__('sys').executable, '-B', 'tools/cloud_feed.py',
            *self.arguments('prepare', '--bootstrap', '--output', str(output))],
            cwd=self.source, capture_output=True)
        self.assertEqual(0, prepared.returncode, prepared.stderr.decode())
        self.assertEqual(('true', 1), tuple(json.loads(prepared.stdout)[k] for k in ('pending', 'requests')))
        self.service.live = {p.relative_to(output).as_posix(): p.read_bytes()
                             for p in output.rglob('*') if p.is_file()}
        self.runtime('metadata')
        self.cli('recover')
        self.metadata_server()
        complete = self.cli('metadata')
        self.assertEqual(('complete', 4), (complete['status'], complete['requests']))
        before = self.snapshot()
        idle = self.cli('metadata')
        self.assertEqual(('not_due', 0), (idle['status'], idle['requests']))
        # A fresh saved-state process must not even import the full metadata
        # collector when an auxiliary corpus is present on its real Git state.
        driver = runtime.RUNTIME_DRIVER.replace('    result=cli.main(sys.argv[1:])',
            "    result=cli.main(sys.argv[1:])\n    assert 'tools.spacefox.catalog_refresh' not in sys.modules")
        with patch.object(runtime, 'RUNTIME_DRIVER', driver):
            self.cli('recover')
        self.assertEqual(before, self.snapshot())
        self.assertEqual((1, 0), (self.service.provider_calls, len(self.service.posts)))
        print('PUBLIC_METADATA_SMOKE ' + json.dumps({'materialized': 596, 'runtimeFiles': 21,
            'metadataCalls': 4, 'notDueCalls': 0, 'primaryCalls': 1,
            'badRecipeBeforeAuthority': True, 'recoverMetadataImport': False}, sort_keys=True))


def git_tree(remote, head, prefix):
    return runtime.git(remote, 'ls-tree', '-r', head, prefix)


if __name__ == '__main__':
    unittest.main()
