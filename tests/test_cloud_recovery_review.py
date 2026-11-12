"""Independent R1 cloud witnesses using actual bare Git and loopback HTTP.

Only remote Actions/Pages state is substituted. No GitHub/OIDC acceptance.
"""
import copy
import hashlib
import json
import subprocess
import sys
import unittest

from tests import test_cloud_delivery as harness
from tools.spacefox.cloud import CloudError, HTTP, delivery, delivery_files, journal, recover
from tools.spacefox.publisher import GitState, Publisher


class CloudRecoveryReviewTest(unittest.TestCase):
    tearDown = harness.CloudDeliveryTest.tearDown
    pending = harness.CloudDeliveryTest.pending
    armed = harness.CloudDeliveryTest.armed
    send = harness.CloudDeliveryTest.send

    def setUp(self):
        harness.CloudDeliveryTest.setUp(self)
        self.actions = {}
        self.feed_fault = None
        self.action_reads = []
        parent = self.world.server.RequestHandlerClass
        test = self

        class Handler(parent):
            def do_GET(self):
                if self.path == '/site/feed.json' and test.feed_fault is not None:
                    status, body, declared = test.feed_fault
                    self.send(status, body, declared=declared)
                elif '/actions/' in self.path:
                    test.action_reads.append(self.path)
                    value = test.actions.get(self.path)
                    self.send(404 if value is None else 200, b'' if value is None else harness.encoded(value))
                else:
                    super().do_GET()

        self.world.server.RequestHandlerClass = Handler

    def skipped_attempt(self):
        prefix = '/repos/owner/SpaceFox/actions/runs/10/attempts/1'
        self.actions[prefix] = {
            'id': 10, 'run_attempt': 1, 'head_sha': self.code, 'head_branch': 'main',
            'event': 'workflow_dispatch', 'status': 'completed', 'conclusion': 'cancelled',
            'path': '.github/workflows/update-feed.yml',
            'repository': {'full_name': 'owner/SpaceFox'}}
        self.actions[prefix + '/jobs?per_page=100'] = {'total_count': 1, 'jobs': [{
            'id': 123, 'run_id': 10, 'head_sha': self.code, 'name': 'deploy',
            'status': 'completed', 'conclusion': 'cancelled', 'steps': [{
                'name': 'POST once, then bound async polling and cancellation finality',
                'status': 'completed', 'conclusion': 'skipped'}]}]}
        return prefix

    def test_never_started_deploy_can_recover_exact_pending(self):
        expected = self.pending()
        original = copy.deepcopy(self.pub.ledger)
        first = self.armed()
        prefix = self.skipped_attempt()
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual('not_started', journal(self.pub)['status'])
        self.assertEqual(original, self.pub.ledger)
        self.assertEqual(expected, self.pub.pending_files())
        self.assertEqual([], self.world.posts)
        self.assertEqual([prefix, prefix + '/jobs?per_page=100'], self.action_reads)
        second = self.armed(run=11)
        self.assertNotEqual(first['buildVersion'], second['buildVersion'])
        self.assertEqual(first['artifactRevision'], second['artifactRevision'])
        self.assertEqual(expected, delivery_files(self.pub, delivery(self.pub)))

    def test_explicit_skipped_job_recovers_but_cancelled_empty_job_does_not(self):
        expected = self.pending()
        self.armed()
        prefix = self.skipped_attempt()
        job = self.actions[prefix + '/jobs?per_page=100']['jobs'][0]
        job['steps'] = []
        before = self.store.load()
        with self.assertRaises(CloudError):
            recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual(before, self.store.load())
        job['conclusion'] = 'skipped'
        self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
        self.assertEqual('not_started', journal(self.pub)['status'])
        self.assertEqual(expected, self.pub.pending_files())
        self.assertIsNone(self.pub.ledger['active'])
        self.assertEqual([], self.world.posts)

    def test_incomplete_wrong_attempt_and_started_step_stay_armed(self):
        self.pending()
        self.armed()
        prefix = self.skipped_attempt()
        valid = copy.deepcopy(self.actions)
        mutations = [
            ('run-in-progress', lambda x: x[prefix].update(status='in_progress')),
            ('wrong-attempt', lambda x: x[prefix].update(run_attempt=2)),
            ('wrong-source', lambda x: x[prefix].update(head_sha='0' * 40)),
            ('wrong-workflow', lambda x: x[prefix].update(path='.github/workflows/other.yml')),
            ('wrong-repository', lambda x: x[prefix].update(repository={'full_name': 'other/repo'})),
            ('missing-jobs', lambda x: x.pop(prefix + '/jobs?per_page=100')),
            ('missing-step', lambda x: x[prefix + '/jobs?per_page=100']['jobs'][0].update(steps=[])),
            ('started-step', lambda x: x[prefix + '/jobs?per_page=100']['jobs'][0]['steps'][0].update(conclusion='failure')),
            ('cancelled-step', lambda x: x[prefix + '/jobs?per_page=100']['jobs'][0]['steps'][0].update(conclusion='cancelled')),
            ('truncated-jobs', lambda x: x[prefix + '/jobs?per_page=100'].update(total_count=2)),
        ]
        before = self.store.load()
        for name, mutate in mutations:
            with self.subTest(name=name):
                self.actions = copy.deepcopy(valid)
                mutate(self.actions)
                with self.assertRaises(CloudError):
                    recover(Publisher(self.store, self.code), self.site, self.pages)
                self.assertEqual(before, self.store.load())
                self.assertEqual('armed', journal(Publisher(self.store, self.code))['status'])
                self.assertEqual([], self.world.posts)

    def test_large_404_body_allows_empty_site(self):
        self.feed_fault = (404, b'x' * 9115, None)
        self.assertEqual((404, b''), HTTP().request('GET', self.world.base + '/site/feed.json', limit=8192))
        self.assertIsNone(self.site.observe(self.pub))
        self.assertEqual([], self.world.posts)

    def test_success_oversize_truncated_redirect_stay_rejected(self):
        for status, raw, declared in [(200, b'x' * 8193, None), (200, b'{}', 100),
                                       (302, b'', None)]:
            with self.subTest(status=status, length=len(raw), declared=declared):
                self.feed_fault = status, raw, declared
                with self.assertRaises(CloudError):
                    self.site.observe(self.pub)
        self.assertEqual([], self.world.posts)

    def test_data_only_amendment_is_automatically_materialized(self):
        clone = self.root / 'sparse-content'
        subprocess.run(['git', 'clone', '-q', '--shared', '--sparse', str(harness.ROOT), str(clone)], check=True)
        harness.git(clone, 'config', 'user.name', 'Cloud review')
        harness.git(clone, 'config', 'user.email', 'review@example.invalid')
        # Copy the currently reviewed cloud files without relying on committed
        # evidence output or another worktree's pending changes.
        for name in ('.github/spacefox-inputs.txt', 'tools/cloud_inputs.py'):
            source = harness.ROOT / name
            if source.exists():
                target = clone / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read_bytes())
        seed = (clone / '.github/spacefox-inputs.txt').read_bytes()
        subprocess.run(['git', '-C', str(clone), 'sparse-checkout', 'set', '--no-cone', '--stdin'],
                       input=seed + b'/tools/catalog.py\n', check=True)
        harness.git(clone, 'add', '.github/spacefox-inputs.txt', 'tools')
        harness.git(clone, 'commit', '--allow-empty', '-qm', 'reviewed cloud runtime seed')
        if (clone / 'tools/cloud_inputs.py').exists():
            initial = subprocess.run([sys.executable, '-B', 'tools/cloud_inputs.py'], cwd=clone,
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(0, initial.returncode, initial.stderr.decode())
        svg = clone / 'assets/review-new/svg/new-country.svg'
        svg.parent.mkdir(parents=True)
        raw = (clone / 'assets/global/svg/country-code-ae.svg').read_bytes()
        svg.write_bytes(raw)
        supplement = clone / 'assets/review-new/new-country.json'
        facts = {
            'id': 'review-new-model', 'name': 'Review model',
            'file': 'svg/new-country.svg', 'exportSize': [20, 16],
            'creator': 'SpaceFox contributors', 'license': 'MIT',
            'sources': ['https://ll.thespacedevs.com/docs/'],
            'kind': 'generic',
            'officialLogo': False, 'sourceSha256': hashlib.sha256(raw).hexdigest()}
        supplement.write_bytes(harness.encoded({
            'schemaVersion': 1, 'id': 'review-new-country', 'reviewedAt': '2026-11-12',
            'sources': ['https://ll.thespacedevs.com/docs/'], 'reason': 'Cloud maintenance witness',
            'assets': [{'collection': 'models', 'facts': facts}], 'updates': [], 'additions': []}))
        amend = subprocess.run([
            sys.executable, '-B', str(clone / 'tools/catalog.py'), '--repo', str(clone),
            '--amend', str(supplement), '--catalog-version', 'review-cloud-new',
            '--output', str(clone / 'build/catalog.json'), '--report', str(clone / 'build/report.json')],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, amend.returncode, amend.stderr.decode())
        harness.git(clone, 'add', '--sparse', '.github/spacefox-inputs.txt', 'tools', 'catalog/source.json', 'assets/review-new')
        harness.git(clone, 'commit', '-qm', 'valid data-only addition without second input catalog')
        subprocess.run(['git', '-C', str(clone), 'sparse-checkout', 'init', '--no-cone'], check=True)
        subprocess.run(['git', '-C', str(clone), 'sparse-checkout', 'set', '--no-cone', '--stdin'],
                       input=(clone / '.github/spacefox-inputs.txt').read_bytes(), check=True)
        self.assertFalse(svg.exists())
        if (clone / 'tools/cloud_inputs.py').exists():
            materialize = subprocess.run([sys.executable, '-B', 'tools/cloud_inputs.py'], cwd=clone,
                                         stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(0, materialize.returncode, materialize.stderr.decode())
        result = subprocess.run([sys.executable, '-B', '-c',
            'from pathlib import Path; from tools.spacefox.catalog import build_catalog; '
            'import json; print(json.dumps(build_catalog(Path.cwd())["inputDigests"],sort_keys=True))'],
            cwd=clone, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        pins = json.loads(result.stdout)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), pins['assets/review-new/svg/new-country.svg'])
        self.assertIn('assets/review-new/new-country.json', pins)
        self.assertFalse((clone / 'openspec/changes/spacefox-watchface/evidence/cloud-delivery').exists())
        self.assertEqual('', harness.git(clone, 'status', '--porcelain', '--untracked-files=no'))

    def test_three_generations_reopen_and_adopt_exact_promoted_closure(self):
        prior = None
        first_path = None
        for generation, version in [(1, 'A'), (2, 'B'), (3, 'C')]:
            current = self.pending(generation, version, harness.NOW + (generation - 1) * 3600)
            if generation == 1:
                first_path = next(path for path in current if path != 'feed.json')
            expected = dict(prior or {}, **current)
            self.assertEqual(expected, delivery_files(self.pub, delivery(self.pub)))
            self.armed()
            self.world.artifact = expected
            self.assertEqual('succeed', self.send())
            self.pub = recover(Publisher(self.store, self.code), self.site, self.pages)
            self.assertEqual(generation, self.pub.ledger['active']['generation'])
            self.assertIsNone(self.pub.ledger['pending'])
            prior = current
        self.assertEqual(3, len(expected))
        self.assertNotIn(first_path, expected)
        original = self.pub.ledger['active']
        harness.git(self.source, 'commit', '--allow-empty', '-qm', 'source adoption after promotedC')
        code = harness.git(self.source, 'rev-parse', 'HEAD')
        harness.git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.store.close()
        self.store = GitState(str(self.remote))
        self.pub = Publisher(self.store, code)
        self.pub.adopt_code(self.pub.head)
        saved = journal(self.pub)
        self.assertEqual(expected, delivery_files(self.pub, saved['files']))
        self.assertEqual(original, self.pub.ledger['active'])
        self.pub = recover(self.pub, self.site, self.pages)
        self.assertEqual(original, self.pub.ledger['active'])
        self.assertEqual([], self.pub.ledger['requests'])
        self.assertIsNone(self.pub.ledger['selection_validated_utc'])
        self.assertEqual(3, len(self.world.posts))
        self.assertEqual(3, len({post['pages_build_version'] for post in self.world.posts}))

    def test_rerun_attempt_cannot_post_original_intent(self):
        self.pending()
        self.armed()
        before = self.store.load()
        from tools.spacefox.cloud import deploy
        with self.assertRaises(CloudError):
            deploy(self.pub, self.pages, self.site, expected=self.pub.head,
                   repository='owner/SpaceFox', run_id=10, run_attempt=2,
                   id_token='local-oidc', polls=1)
        self.assertEqual(before, self.store.load())
        self.assertEqual([], self.world.posts)
