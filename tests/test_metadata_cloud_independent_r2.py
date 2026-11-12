"""New R2 local CLI witnesses for armed refusal and auxiliary isolation.

Only external HTTP service responses use the retained local transport fixture.
State comes from real public Publisher/arm events, never fabricated ledgers.
"""
import json
import os
import subprocess
import sys
import unittest
from urllib.parse import urlsplit

from tests import test_cloud_runtime_checkout as runtime
from tools.spacefox.cloud import arm, journal
from tools.spacefox.publisher import GitState, LiveRevision, Publisher


PATHS = ['/2.3.0/config/countries/', '/2.3.0/agencies/',
         '/2.3.0/launcher_configurations/', '/2.3.0/pads/']
FIELDS = ('accepted', 'last_poll_utc', 'selection_validated_utc', 'generation', 'active', 'pending')

# This observer only fails a forbidden import. It does not replace an owner or
# make recovery/cadence succeed. A fresh CLI process starts for every observation.
BLOCKED_DRIVER = runtime.RUNTIME_DRIVER.replace(
    'def audit(event,args):',
    "def audit(event,args):\n"
    "    if event=='import' and args[0] in ('tools.refresh_catalog','tools.spacefox.catalog_refresh'):\n"
    "        raise AssertionError('blocked metadata imported collector')")


class IndependentMetadataCliR2(unittest.TestCase):
    setUp = runtime.CloudRuntimeCheckoutTest.setUp
    tearDown = runtime.CloudRuntimeCheckoutTest.tearDown
    cli = runtime.CloudRuntimeCheckoutTest.cli
    arguments = runtime.CloudRuntimeCheckoutTest.arguments
    snapshot = runtime.CloudRuntimeCheckoutTest.snapshot
    runtime = runtime.CloudRuntimeCheckoutTest.runtime

    def publisher(self):
        store = GitState(str(self.remote))
        self.stores.append(store)
        return Publisher(store, self.code)

    def active_authority(self):
        self.runtime('metadata')
        pub, _, files = runtime.CloudRuntimeCheckoutTest.authority(self)
        self.service.live = dict(files)
        pub.reconcile(LiveRevision(1, pub.ledger['pending']['artifact_revision']))
        token = pub.reserve(pub.head, runtime.NOW, trigger='manual')
        pub.accept_source(pub.head, token, (), runtime.NOW,
                          selection_validated_utc=runtime.NOW - 3600)
        return pub, files

    def auxiliary(self, pub):
        return runtime.git(self.remote, 'ls-tree', '-r', pub.head, 'catalog-refresh')

    def blocked_cli(self, expected):
        before, reads = self.snapshot(), len(self.service.reads)
        env = dict(os.environ, GITHUB_RUN_ID='87', GITHUB_RUN_ATTEMPT='1')
        for key in ('GH_TOKEN', 'GITHUB_OUTPUT', 'GIT_CONFIG_COUNT'):
            env.pop(key, None)
        result = subprocess.run([sys.executable, '-B', '-c', BLOCKED_DRIVER,
                                 *self.arguments('metadata')], cwd=self.source,
                                env=env, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        value = json.loads(result.stdout)
        self.assertEqual((expected, 0), (value['status'], value['requests']))
        self.assertEqual(before, self.snapshot())
        self.assertEqual(reads, len(self.service.reads))
        self.assertEqual([], self.service.posts)
        boundary = json.loads(result.stderr.decode().split('RUNTIME_BOUNDARY ', 1)[1])
        self.assertEqual(dict(builderCalls=0, nodeCalls=0, oidcCalls=0, sourceDataReads=0), boundary)

    def test_partial_corpus_survives_pending_then_armed_core_promotion_and_explicit_recovery(self):
        pub, first_files = self.active_authority()
        first = self.cli('metadata', '--max-requests', '1')
        self.assertEqual(('partial', 1), (first['status'], first['requests']))
        pub = self.publisher()
        prefix = self.auxiliary(pub)
        self.assertTrue(prefix)
        pub.reconcile(LiveRevision(1, pub.ledger['active']['artifact_revision']))
        replacement, digest = runtime.files(pub.ledger['instance_id'], 2, 'R2-partial-B', runtime.NOW - 3600)
        pub.prepare(pub.head, runtime.NOW, replacement, digest,
                    feed_publisher=json.loads(replacement['feed.json'])['publisher'])
        pub, intent = arm(pub, expected=pub.head, repository='owner/SpaceFox',
                          run_id=87, run_attempt=1, artifact_id=904, now=runtime.NOW)
        self.blocked_cli('yielded_pending')
        self.assertEqual(prefix, self.auxiliary(pub))
        # A real replacement delivery retains the prior immutable catalog.
        # Seed that literal two-generation union at the external site only.
        self.service.live = dict(first_files, **replacement)
        pub.reconcile(LiveRevision(2, pub.ledger['pending']['artifact_revision']))
        facts = {key: pub.ledger[key] for key in FIELDS}
        self.assertIsNone(pub.ledger['pending'])
        self.assertEqual('armed', journal(pub)['status'])
        # The external status is deliberately unavailable. The CLI must refuse
        # without asking that service or importing the saved partial collector.
        self.blocked_cli('yielded_armed')
        self.assertEqual(prefix, self.auxiliary(pub))
        self.assertEqual(1, self.service.provider_calls)
        self.service.statuses[intent['buildVersion']] = 'succeed'
        self.cli('recover')
        pub = self.publisher()
        terminal = runtime.git(self.remote, 'show', f'{pub.head}:cloud.json')
        self.assertEqual('succeed', journal(pub)['status'])
        self.assertEqual(prefix, self.auxiliary(pub))
        self.assertEqual(facts, {key: pub.ledger[key] for key in FIELDS})
        resumed = self.cli('metadata', '--max-requests', '3')
        self.assertEqual(('complete', 3), (resumed['status'], resumed['requests']))
        pub = self.publisher()
        self.assertEqual(facts, {key: pub.ledger[key] for key in FIELDS})
        self.assertEqual(terminal, runtime.git(self.remote, 'show', f'{pub.head}:cloud.json'))
        self.assertEqual(PATHS, [urlsplit(p).path for p in self.service.reads if p.startswith('/2.3.0/')])
        self.assertEqual((4, []), (self.service.provider_calls, self.service.posts))
        print('R2_PARTIAL_ARMED ' + json.dumps(dict(metadataHttp=4, pendingHttp=0,
            armedHttp=0, blockedWrites=0, blockedCollectorImports=0, resumedPages=3,
            launchSourceUtc=runtime.NOW - 3600, terminalJournalPreserved=True), sort_keys=True))

    def test_no_journal_live_closure_precedes_metadata_and_idle_cadence_preserves_source_and_auxiliary(self):
        pub, files = self.active_authority()
        facts = {key: pub.ledger[key] for key in FIELDS}
        catalog_path = next(path for path in files if path != 'feed.json')
        before = self.snapshot()
        self.service.live[catalog_path] += b' '
        self.cli('metadata', success=False)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(0, self.service.provider_calls)
        self.assertEqual('', self.auxiliary(pub))
        self.service.live = dict(files)
        complete = self.cli('metadata')
        self.assertEqual(('complete', 4), (complete['status'], complete['requests']))
        pub = self.publisher()
        self.assertEqual(facts, {key: pub.ledger[key] for key in FIELDS})
        self.assertIsNone(journal(pub))
        prefix = self.auxiliary(pub)
        self.assertTrue(prefix)
        before, reads = self.snapshot(), len(self.service.reads)
        # Cadence idleness cannot bypass the required exact live closure either.
        self.service.live[catalog_path] += b' '
        self.cli('metadata', success=False)
        self.assertEqual(before, self.snapshot())
        self.assertEqual(4, self.service.provider_calls)
        self.service.live = dict(files)
        idle = self.cli('metadata')
        self.assertEqual(('not_due', 0), (idle['status'], idle['requests']))
        self.assertEqual(before, self.snapshot())
        self.assertGreater(len(self.service.reads), reads)
        pub = self.publisher()
        self.assertEqual(prefix, self.auxiliary(pub))
        self.assertEqual(facts, {key: pub.ledger[key] for key in FIELDS})
        self.assertIsNone(journal(pub))
        self.assertEqual(PATHS, [urlsplit(p).path for p in self.service.reads if p.startswith('/2.3.0/')])
        self.assertEqual((4, []), (self.service.provider_calls, self.service.posts))
        print('R2_NO_JOURNAL ' + json.dumps(dict(metadataHttp=4, idleHttp=0,
            rejectedMixedLive=2, idleWrites=0, launchSourceUtc=runtime.NOW - 3600,
            sourceAndAuxiliaryPreserved=True, cloudJournalCreated=False), sort_keys=True))
