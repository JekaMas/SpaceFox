"""Current metadata/art/cloud integration through an actual public sparse checkout.

The frozen actual generation5 selected record is public provider data. External
service transport uses loopback; every source, builder, validator, CAS, collector
and readback owner is real. No native, hosted or current-provider claim follows.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from tests import test_cloud_runtime_checkout as runtime
from tests import test_metadata_cloud as metadata
from tools.spacefox.catalog_refresh import CatalogRefresh
from tools.spacefox.cloud import journal
from tools.spacefox.publisher import LiveRevision

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / 'tests/fixtures/metadata-art'
SOURCE_UTC = 1794463916
NOW = SOURCE_UTC + 1
FIELDS = ('last_poll_utc', 'selection_validated_utc', 'requests')
SEED = '''
import json,sys
from pathlib import Path
from tools.spacefox.catalog import build_catalog
from tools.spacefox.visual_bridge import build_artifact
from tools.spacefox.publisher import GitState,Publisher,_schedule
root=Path.cwd(); now=1794463916
record=_schedule(json.loads(Path(sys.argv[3]).read_bytes())).entries[0].record
store=GitState(sys.argv[1]);store.bootstrap(sys.argv[2]);pub=Publisher(store,sys.argv[2]);pub.reconcile(None)
slot=pub.reserve(pub.head,now)
pub.accept_source(pub.head,slot,(record,),now,selection_validated_utc=now)
envelope=pub.publisher_envelope(now)
catalog=build_catalog(root,Path(sys.argv[4]))
files,digest=build_artifact(pub.schedule,catalog,now,publisher=envelope,root=root)
pub.prepare(pub.head,now,files,digest,feed_publisher=envelope,artifact_profile='visual-v2')
print(json.dumps({'files':len(files),'bytes':sum(map(len,files.values()))}))
store.close()
'''
BLOCKED_DRIVER = runtime.RUNTIME_DRIVER.replace(
    'def audit(event,args):',
    "def audit(event,args):\n"
    "    if event=='import' and args[0] in ('tools.refresh_catalog','tools.spacefox.catalog_refresh'):\n"
    "        raise AssertionError('blocked command imported collector')")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def selection(files):
    feed = json.loads(files['wire2/feed.json'])
    selected = json.loads(files[feed['visualSelection']['path']])
    roles = {k: None if v is None else json.loads(files[v['descriptor']['path']])
             for k, v in selected['roles'].items()}
    return feed, selected, roles


class MetadataArtPublicTest(unittest.TestCase):
    def setUp(self):
        runtime.CloudRuntimeCheckoutTest.setUp(self)
        # This witness is the frozen historical 194-specific public recipe.
        # This historical recipe is independent of subsequent eligibility
        # decisions. Global.13 qualifies 194 again; current admission/refusal is
        # tested separately. Bind the exact public-ancestral historical tree.
        revision = 'c46c5f9a30da354dc0d32f3191249286e4223873'
        expected_tree = '47d7d8cdc16aa134419f603cc57c10e243f06bc4'
        self.assertEqual(expected_tree, runtime.git(self.source, 'rev-parse', revision + '^{tree}'))
        runtime.git(self.source, 'checkout', '--detach', '-q', revision)
        self.assertEqual('', runtime.git(self.source, 'status', '--porcelain'))
        self.code = revision
        runtime.git(self.source, 'push', '--force', '-q', str(self.remote), 'HEAD:refs/heads/main')

    tearDown = runtime.CloudRuntimeCheckoutTest.tearDown
    cli = runtime.CloudRuntimeCheckoutTest.cli
    snapshot = runtime.CloudRuntimeCheckoutTest.snapshot
    publisher = metadata.MetadataCloudTest.publisher
    metadata_server = metadata.MetadataCloudTest.metadata_server
    runtime = runtime.CloudRuntimeCheckoutTest.runtime

    def arguments(self, *command):
        args = runtime.CloudRuntimeCheckoutTest.arguments(self, *command)
        args[args.index('--now') + 1] = str(NOW)
        if hasattr(self, 'metadata_origin'):
            args[args.index('--origin') + 1] = self.metadata_origin
        return args

    def blocked(self, status):
        before, reads = self.snapshot(), len(self.service.reads)
        with patch.object(runtime, 'RUNTIME_DRIVER', BLOCKED_DRIVER):
            value = self.cli('metadata')
        self.assertEqual((status, 0), (value['status'], value['requests']))
        self.assertEqual(before, self.snapshot())
        self.assertEqual(reads, len(self.service.reads))

    def test_frozen_actual194_content_update_sparse_recovery_metadata_and_source_gates(self):
        self._frozen_actual194(negative=False)

    def test_metadata_gate_refusals_and_source_adoption_preserve_state(self):
        self._frozen_actual194(negative=True)

    def _frozen_actual194(self, *, negative):
        # Full current-recipe materializer633 was already observed before the
        # earlier evaluation-clock oracle failure. This standalone behavior
        # fixture uses only the public tree; do not repeat that unchanged gate.
        runtime.git(self.source, 'sparse-checkout', 'disable')
        self.assertFalse((self.source / '.agents').exists())
        result = subprocess.run([sys.executable, '-B', '-c', SEED, str(self.remote), self.code,
                                 str(FIXTURE / 'g5-selected.json'), str(FIXTURE / 'g5-recipe.json')],
                                cwd=self.source, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        pub = self.publisher()
        old = pub.pending_files()
        old_feed, old_selection, old_roles = selection(old)
        self.assertEqual('spacefox:asset:generic', old_roles['rocket']['assetId'])
        self.assertEqual(('ll2:configuration:194', 'll2:site:21'),
                         (old_selection['modelId'], old_selection['siteId']))
        self.service.live = dict(old)
        pub.reconcile(LiveRevision(1, pub.ledger['pending']['artifact_revision']))
        source_facts = {k: pub.ledger[k] for k in FIELDS}
        accepted_entries = pub.ledger['accepted']['entries']
        output = self.base / 'content-update'
        env = dict(os.environ, GITHUB_RUN_ID='87', GITHUB_RUN_ATTEMPT='1')
        for key in ('GH_TOKEN', 'GITHUB_OUTPUT', 'GIT_CONFIG_COUNT'):
            env.pop(key, None)
        result = subprocess.run([sys.executable, '-B', 'tools/cloud_feed.py',
                                 *self.arguments('prepare', '--output', str(output))],
                                cwd=self.source, env=env, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        prepared = json.loads(result.stdout)
        self.assertEqual(('content_pending', 0), (prepared['result'], prepared['requests']))
        pub = self.publisher()
        self.assertEqual(source_facts, {k: pub.ledger[k] for k in FIELDS})
        self.assertEqual(accepted_entries, pub.ledger['accepted']['entries'])
        self.assertEqual(NOW, pub.ledger['accepted']['evaluated_at_utc'])
        new = pub.pending_files()
        new_feed, selected, roles = selection(new)
        self.assertEqual('spacefox:asset:remaining-r1-kuaizhou11', roles['rocket']['assetId'])
        self.assertEqual(old_feed['launch'], new_feed['launch'])
        self.assertEqual(old_feed['sourceContentRevision'], new_feed['sourceContentRevision'])
        self.assertEqual(old_selection['siteId'], selected['siteId'])
        self.assertIsNone(selected['originId'])
        for key in ('siteId', 'position', 'sourcePosition', 'positionMode'):
            self.assertEqual(old_roles['geography'][key], roles['geography'][key], key)
        self.assertEqual(old_selection['roles']['geography']['descriptor'],
                            selected['roles']['geography']['descriptor'])
        union = {p.relative_to(output).as_posix(): p.read_bytes() for p in output.rglob('*') if p.is_file()}
        for path, raw in old.items():
            if path not in ('feed.json', 'wire2/feed.json'):
                self.assertEqual(raw, union[path])
        self.assertLessEqual(sum(map(len, union.values())), 1048576)
        self.assertLessEqual(len(union), 256)
        self.runtime('metadata')
        actual = {p.relative_to(self.source).as_posix() for p in self.source.rglob('*')
                  if p.is_file() and '.git' not in p.relative_to(self.source).parts}
        self.assertEqual(21, len(actual))
        if negative:
            self.blocked('yielded_pending')
        self.cli('arm', '--expected-base', pub.head, '--artifact-id', '990')
        pub = self.publisher()
        intent = journal(pub)['intent']
        self.service.live = union
        # Legal public core promotion can precede cloud journal finality.
        pub.reconcile(LiveRevision(2, pub.ledger['pending']['artifact_revision']))
        if negative:
            self.blocked('yielded_armed')
        self.service.statuses[intent['buildVersion']] = 'succeed'
        with patch.object(runtime, 'RUNTIME_DRIVER', BLOCKED_DRIVER):
            self.cli('recover')
        pub = self.publisher()
        self.assertEqual('succeed', journal(pub)['status'])
        self.assertEqual(source_facts, {k: pub.ledger[k] for k in FIELDS})
        self.assertEqual(accepted_entries, pub.ledger['accepted']['entries'])
        self.assertEqual(union, self.service.live)
        terminal = runtime.git(self.remote, 'show', f'{pub.head}:cloud.json')
        world = self.metadata_server()
        world['now'] = NOW
        # Literal typed table fixture for the exact selected reference roles.
        for path, raw in list(world['bodies'].items()):
            value = json.loads(raw)
            row = value['results'][0]
            if '/countries/' in path:
                row.update(id=6, name='China', alpha_2_code='CN', alpha_3_code='CHN')
            elif '/agencies/' in path:
                row.update(id=194, name='ExPace', country=[{'id': 6}])
                row['url'] = row['url'].replace('/121/', '/194/')
            elif '/launcher_configurations/' in path:
                row.update(id=194, name='Kuaizhou 11', full_name='Kuaizhou 11',
                           manufacturer={'id': 194, 'country': [{'id': 6}]})
                row['url'] = row['url'].replace('/164/', '/194/')
            else:
                row.update(id=21, name='Launch Area 95A', country={'id': 6}, agencies=[{'id': 194}])
                row['url'] = row['url'].replace('/80/', '/21/')
            world['bodies'][path] = runtime.encoded(value)
        completed = self.cli('metadata')
        self.assertEqual(('complete', 4), (completed['status'], completed['requests']))
        pub = self.publisher()
        candidate = CatalogRefresh(pub, origin=self.metadata_origin, local_http=True).current()
        self.assertEqual({'countries': [6], 'organizations': [194], 'models': [194], 'sites': [21]},
                         candidate['coverage']['distinctIds'])
        self.assertEqual([NOW - 2] * 4, [p['validatedUtc'] for p in candidate['coverage']['pages']])
        for key in FIELDS[:-1]:
            self.assertEqual(source_facts[key], pub.ledger[key], key)
        self.assertEqual(terminal, runtime.git(self.remote, 'show', f'{pub.head}:cloud.json'))
        self.assertEqual(accepted_entries, pub.ledger['accepted']['entries'])
        before = self.snapshot()
        idle = self.cli('metadata')
        self.assertEqual(('not_due', 0), (idle['status'], idle['requests']))
        self.assertEqual(before, self.snapshot())
        # Current source permission and explicit adoption remain independent.
        runtime.git(self.source, 'commit', '--allow-empty', '-qm', 'new source event fixture')
        old_code, self.code = self.code, runtime.git(self.source, 'rev-parse', 'HEAD')
        runtime.git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        if negative:
            for code in (old_code, self.code):
                runtime.git(self.source, 'checkout', '-q', code)
                self.cli('metadata', success=False)
                self.assertEqual(before, self.snapshot())
        pub = self.publisher()
        pub.adopt_code(pub.head)
        adopted = self.snapshot()
        idle = self.cli('metadata')
        self.assertEqual(('not_due', 0), (idle['status'], idle['requests']))
        self.assertEqual(adopted, self.snapshot())
        self.assertEqual((0, 0, 4), (self.service.provider_calls, len(self.service.posts), len(world['calls'])))
        print('METADATA_ART_PUBLIC ' + json.dumps(dict(runtimeFiles=21, oldFiles=len(old), currentFiles=len(new), unionFiles=len(union),
              unionBytes=sum(map(len, union.values())), primaryCalls=0, metadataCalls=4,
              notDueCalls=0, gateChecksExecuted=negative,
              sourceUtc=SOURCE_UTC, model194Specific=True, siteAndLaunchUnchanged=True,
              versionedMapReusedExactly=True, recoveryBuilderCalls=0, recoveryCollectorImports=0,
              **({'pendingCalls':0, 'armedCalls':0, 'pendingWrites':0, 'armedWrites':0} if negative else {})), sort_keys=True))
