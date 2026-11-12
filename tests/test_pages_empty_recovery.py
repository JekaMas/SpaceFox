"""Actual HTTP200 empty-status recovery regression at local HTTP/Git boundaries.

The Actions fixture projects the relevant fields of the captured completed fault
attempt. Tests bind its repository/source/run identity to their temporary world.
Only remote service records and the explicit Actions OIDC response are replaced;
no authenticated GitHub, hosted recovery or native qualification is claimed.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tests import test_cloud_recovery_review as prior
from tests import test_cloud_runtime_checkout as runtime
from tools.spacefox.cloud import CloudError, journal, recover
from tools.spacefox.publisher import GitState, LiveRevision, Publisher
from tools.spacefox.provider import ProviderError

ROOT = Path(__file__).resolve().parents[1]


def captured_attempt(code, run_id=10):
    value = json.loads((ROOT / 'tests/fixtures/pages-empty-recovery/completed-skipped-attempt.json').read_bytes())
    run = value['run']
    run.update(id=run_id, run_attempt=1, head_sha=code, repository={'full_name': 'owner/SpaceFox'})
    for job in value['jobs']['jobs']:
        job.update(run_id=run_id, head_sha=code)
    prefix = f'/repos/owner/SpaceFox/actions/runs/{run_id}/attempts/1'
    return prefix, {prefix: run, prefix + '/jobs?per_page=100': value['jobs']}


class PagesEmptyRecoveryTest(unittest.TestCase):
    tearDown = prior.CloudRecoveryReviewTest.tearDown
    pending = prior.CloudRecoveryReviewTest.pending
    armed = prior.CloudRecoveryReviewTest.armed

    def setUp(self):
        prior.CloudRecoveryReviewTest.setUp(self)
        self.responses = [(200, b'{"status":""}')]
        self.poll_reads = []
        parent = self.world.server.RequestHandlerClass
        test = self

        class Handler(parent):
            def do_GET(self):
                if '/pages/deployments/' in self.path:
                    test.poll_reads.append(self.path)
                    status, raw = test.responses[0]
                    if len(test.responses) > 1:
                        test.responses.pop(0)
                    self.send(status, raw)
                else:
                    super().do_GET()

        self.world.server.RequestHandlerClass = Handler

    def prepare_attempt(self):
        expected = self.pending()
        self.armed()
        prefix, self.actions = captured_attempt(self.code)
        return expected, prefix

    def test_empty_status_positive_witness_preserves_exact_pending(self):
        expected, prefix = self.prepare_attempt()
        before = deepcopy(self.pub.ledger)
        old = journal(self.pub)
        tree = self.store._git('ls-tree', '-r', self.pub.head).stdout.decode()
        with patch('tools.spacefox.cloud.time.sleep') as sleep:
            self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual([((5,), {})] * 5, sleep.call_args_list)
        self.assertEqual(6, len(self.poll_reads))
        self.assertEqual([prefix, prefix + '/jobs?per_page=100'], self.action_reads)
        self.assertEqual(dict(old, status='not_started'), journal(self.pub))
        self.assertEqual(before, self.pub.ledger)
        self.assertEqual(expected, self.pub.pending_files())
        after = self.store._git('ls-tree', '-r', self.pub.head).stdout.decode()
        self.assertEqual([x for x in tree.splitlines() if not x.endswith('\tcloud.json')],
                         [x for x in after.splitlines() if not x.endswith('\tcloud.json')])
        self.assertEqual(([], 0), (self.world.posts, self.world.provider_calls))

    def test_empty_status_all_witness_negatives_retain_armed(self):
        _, prefix = self.prepare_attempt()
        valid = deepcopy(self.actions)
        jobs_key = prefix + '/jobs?per_page=100'
        def job(value):
            return next(j for j in value[jobs_key]['jobs'] if j['name'] == 'deploy')
        mutations = {
            'unknown-run': lambda x: x.pop(prefix),
            'in-progress': lambda x: x[prefix].update(status='in_progress'),
            'wrong-run': lambda x: x[prefix].update(id=11),
            'wrong-attempt': lambda x: x[prefix].update(run_attempt=2),
            'wrong-source': lambda x: x[prefix].update(head_sha='0' * 40),
            'foreign-repository': lambda x: x[prefix].update(repository={'full_name': 'foreign/repo'}),
            'wrong-workflow': lambda x: x[prefix].update(path='.github/workflows/foreign.yml'),
            'wrong-branch': lambda x: x[prefix].update(head_branch='other'),
            'unknown-jobs': lambda x: x.pop(jobs_key),
            'truncated-jobs': lambda x: x[jobs_key].update(total_count=5),
            'duplicate-deploy': lambda x: (x[jobs_key]['jobs'].append(deepcopy(job(x))),
                                            x[jobs_key].update(total_count=5)),
            'foreign-job-run': lambda x: job(x).update(run_id=11),
            'foreign-job-source': lambda x: job(x).update(head_sha='0' * 40),
            'running-job': lambda x: job(x).update(status='in_progress'),
            'cancelled-empty-job': lambda x: job(x).update(conclusion='cancelled'),
            'started-post': lambda x: job(x).update(conclusion='failure', steps=[{
                'name': 'POST once, then bound async polling and cancellation finality',
                'status': 'completed', 'conclusion': 'failure'}]),
            'cancelled-post': lambda x: job(x).update(conclusion='cancelled', steps=[{
                'name': 'POST once, then bound async polling and cancellation finality',
                'status': 'completed', 'conclusion': 'cancelled'}]),
        }
        before = self.store.load()
        for name, mutate in mutations.items():
            with self.subTest(name=name), patch('tools.spacefox.cloud.time.sleep'):
                self.actions = deepcopy(valid)
                mutate(self.actions)
                with self.assertRaises(CloudError):
                    recover(Publisher(self.store, self.code), self.site, self.pages)
                self.assertEqual(before, self.store.load())
                self.assertEqual(([], 0), (self.world.posts, self.world.provider_calls))

    def test_nonempty_malformed_and_error_observations_stay_strict(self):
        self.prepare_attempt()
        before = self.store.load()
        cases = {
            'progress-then-empty': [(200, b'{"status":"deploying"}'), (200, b'{"status":""}')],
            'unknown-then-empty': [(200, b'{"status":"future_status"}'), (200, b'{"status":""}')],
            'empty-then-progress-then-empty': [(200, b'{"status":""}'), (200, b'{"status":"queued"}'), (200, b'{"status":""}')],
            'progress-then-404': [(200, b'{"status":"deploying"}'), (404, b'')],
            'missing-status': [(200, b'{}')],
            'null-status': [(200, b'{"status":null}')],
            'boolean-status': [(200, b'{"status":false}')],
            'malformed-json': [(200, b'{')],
            'empty-body': [(200, b'')],
            'server-error': [(503, b'')],
            'error-after-empty': [(200, b'{"status":""}'), (503, b'')],
        }
        for name, responses in cases.items():
            with self.subTest(name=name), patch('tools.spacefox.cloud.time.sleep'):
                self.responses = list(responses)
                self.action_reads.clear()
                with self.assertRaises((CloudError, ProviderError)):
                    recover(Publisher(self.store, self.code), self.site, self.pages)
                self.assertEqual([], self.action_reads)
                self.assertEqual(before, self.store.load())
                self.assertEqual(([], 0), (self.world.posts, self.world.provider_calls))

    def test_normal_progress_terminal_never_needs_actions(self):
        self.prepare_attempt()
        # Actions is unavailable. Terminal Pages finality must remain sufficient.
        self.actions = {}
        for terminal in ('succeed', 'deployment_failed', 'deployment_cancelled'):
            with self.subTest(terminal=terminal), patch('tools.spacefox.cloud.time.sleep') as sleep:
                self.responses = [(200, prior.harness.encoded({'status': s}))
                                  for s in ('queued', '', 'deploying', terminal)]
                self.assertEqual(terminal, self.pages.wait('a' * 40))
                self.assertEqual([((5,), {})] * 3, sleep.call_args_list)
        self.assertEqual([], self.action_reads)
        self.assertEqual(([], 0), (self.world.posts, self.world.provider_calls))


class RichRuntimeEmptyRecoveryTest(unittest.TestCase):
    setUp = runtime.CloudRuntimeCheckoutTest.setUp
    tearDown = runtime.CloudRuntimeCheckoutTest.tearDown
    arguments = runtime.CloudRuntimeCheckoutTest.arguments
    cli = runtime.CloudRuntimeCheckoutTest.cli
    snapshot = runtime.CloudRuntimeCheckoutTest.snapshot
    runtime = runtime.CloudRuntimeCheckoutTest.runtime

    def test_rich_runtime_cli_empty_recovery_new_intent_and_http_finality(self):
        from tools.spacefox.schedule import (LaunchRecord, StableId, IdKind, Timing, TimePrecision, LaunchStatus)
        self.runtime('arm')
        store = GitState(str(self.remote)); self.stores.append(store); store.bootstrap(self.code)
        pub = Publisher(store, self.code); pub.reconcile(None)
        now = runtime.NOW
        previous, digest = runtime.files(pub.ledger['instance_id'], 1, 'old-live', None)
        pub.prepare(pub.head, now-7200, previous, digest,
                    feed_publisher=json.loads(previous['feed.json'])['publisher'])
        pub.reconcile(LiveRevision(1, pub.ledger['pending']['artifact_revision']))
        self.service.live = dict(previous)
        def identity(kind, value):
            return StableId(kind, 'll2', value)
        record = LaunchRecord(identity(IdKind.LAUNCH, 'bridge-literal'),
            Timing(TimePrecision.EXACT, exact_utc=now+7200), LaunchStatus.PENDING, now-3600,
            configuration_id=identity(IdKind.CONFIGURATION, '164'), operator_id=identity(IdKind.ORGANIZATION, '121'),
            site_id=identity(IdKind.SITE, '80'), country_id=identity(IdKind.COUNTRY, '2'),
            configuration_name='Falcon 9', operator_name='SpaceX', mission_name='Луна 零',
            mission_purpose='Measure lunar radiation', country_code='USA', site_location_name='Florida')
        token = pub.reserve(pub.head, now)
        pub.accept_source(pub.head, token, (record,), now, selection_validated_utc=now-3600)
        corpus = ROOT / 'tests/fixtures/bridge-v2'
        pins = json.loads((corpus / 'index.json').read_bytes())['a']['files']
        files = {p.relative_to(corpus/'a').as_posix(): p.read_bytes()
                 for p in (corpus/'a').rglob('*') if p.is_file()}
        self.assertEqual((76, 524776), (len(files), sum(map(len, files.values()))))
        for path, raw in files.items():
            self.assertEqual(len(raw), pins[path]['bytes'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), pins[path]['sha256'])
        for path in ('feed.json', 'wire2/feed.json'):
            value = json.loads(files[path]); value['publisher'] = pub.publisher_envelope(now)
            files[path] = runtime.encoded(value)
        feed = json.loads(files['feed.json'])
        pub.prepare(pub.head, now, files, feed['catalogDigest'],
                    feed_publisher=feed['publisher'], artifact_profile='visual-v2')
        original = deepcopy(pub.ledger)
        complete = {**{p: raw for p, raw in previous.items() if p != 'feed.json'}, **files}
        armed = self.cli('arm', '--expected-base', pub.head, '--artifact-id', '99')
        old = json.loads(runtime.git(self.remote, 'show', 'refs/heads/feed-state:cloud.json'))
        version = old['intent']['buildVersion']
        self.service.statuses[version] = ''
        _, self.service.actions = captured_attempt(self.code, 87)
        self.run_id = 88
        # The new run cannot execute the old intent even before reconciliation.
        before = self.snapshot()
        self.cli('deploy', '--expected-base', pub.head, success=False, oidc_calls=0)
        self.assertEqual(before, self.snapshot())
        runtime.git(self.source, 'commit', '--allow-empty', '-qm', 'unadopted local source')
        self.cli('deploy', '--expected-base', armed['head'], success=False, oidc_calls=0)
        self.assertEqual(before, self.snapshot())
        runtime.git(self.source, 'reset', '--hard', self.code)
        self.cli('deploy', '--expected-base', armed['head'], success=False)
        self.assertEqual(before, self.snapshot())
        self.assertEqual([], self.service.posts)
        self.cli('recover')  # Six actual 200-empty HTTP polls, original 5s delays.
        after = json.loads(runtime.git(self.remote, 'show', 'refs/heads/feed-state:cloud.json'))
        self.assertEqual(dict(old, status='not_started'), after)
        reopened = Publisher(store, self.code)
        self.assertEqual(original, reopened.ledger)
        self.assertEqual(files, reopened.pending_files())
        self.assertEqual(previous, self.service.live)
        fresh = self.cli('arm', '--expected-base', reopened.head, '--artifact-id', '100')
        current = json.loads(runtime.git(self.remote, 'show', 'refs/heads/feed-state:cloud.json'))
        self.assertNotEqual(version, current['intent']['buildVersion'])
        self.assertEqual((88, 1, self.code), tuple(current['intent'][k] for k in ('runId', 'runAttempt', 'source')))
        self.service.artifact = complete
        self.runtime('deploy')
        self.cli('deploy', '--expected-base', fresh['head'])
        self.assertEqual(1, len(self.service.posts))
        self.assertEqual(current['intent']['buildVersion'], self.service.posts[0][1]['pages_build_version'])
        optional = next(p for p in files if p.startswith('objects/'))
        self.service.live[optional] = b'{}'
        self.runtime('promote')
        self.cli('recover', success=False)
        self.assertEqual('succeed', json.loads(runtime.git(self.remote, 'show', 'refs/heads/feed-state:cloud.json'))['status'])
        self.assertEqual(original, Publisher(store, self.code).ledger)
        self.service.live = dict(complete)
        self.cli('recover')
        final = Publisher(store, self.code)
        self.assertEqual(original['pending'], final.ledger['active'])
        self.assertIsNone(final.ledger['pending'])
        for key in ('accepted', 'requests', 'last_poll_utc', 'selection_validated_utc', 'backoff_until_utc'):
            self.assertEqual(original[key], final.ledger[key], key)
        self.assertEqual((1, 0), (len(self.service.posts), self.service.provider_calls))
        self.assertEqual(complete, self.service.live)
        self.assertEqual(19, sum(1 for p in self.source.rglob('*') if p.is_file() and '.git' not in p.relative_to(self.source).parts))
        print('EMPTY_RECOVERY_TRACE ' + json.dumps({'files': len(files), 'oldPosts': 0, 'newPosts': 1,
              'providerCalls': 0, 'pendingExact': True, 'sourceAgeAndQuotaExact': True,
              'optionalCorruptionRefusedAfterFinality': True}, sort_keys=True))
