"""Integrated public-only sparse dual producer and saved-state CLI witnesses.

The source launch below is an authored fixture. Real producer, source checkout,
Git authority, CLI, complete validators and HTTP readback run unchanged. External
Pages/artifact transport and the Actions OIDC response use the loopback boundary
documented by test_cloud_runtime_checkout; no native or hosted claim is made.
"""
import hashlib
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from tests import test_cloud_runtime_checkout as prior
from tools.spacefox.publisher import GitState, Publisher

NOW = prior.NOW
ROOT = Path(__file__).resolve().parents[1]
git = prior.git

SEED = '''
import json,sys
from pathlib import Path
from tools.spacefox.catalog import build_catalog
from tools.spacefox.visual_bridge import build_artifact
from tools.spacefox.publisher import GitState,Publisher
from tools.spacefox.schedule import LaunchRecord,StableId,IdKind,Timing,TimePrecision,LaunchStatus
root=Path.cwd(); now=1794441600
def identity(kind,value): return StableId(kind,'ll2',value)
record=LaunchRecord(identity(IdKind.LAUNCH,'public-integration'),Timing(TimePrecision.EXACT,exact_utc=now+7200),LaunchStatus.PENDING,now-3600,configuration_id=identity(IdKind.CONFIGURATION,'164'),operator_id=identity(IdKind.ORGANIZATION,'121'),site_id=identity(IdKind.SITE,'80'),country_id=identity(IdKind.COUNTRY,'2'),configuration_name='Falcon 9',operator_name='SpaceX',mission_name='Луна 零',mission_purpose='Measure radiation',country_code='USA',site_location_name='Florida')
store=GitState(sys.argv[1]);store.bootstrap(sys.argv[2]);pub=Publisher(store,sys.argv[2]);pub.reconcile(None)
token=pub.reserve(pub.head,now)
pub.accept_source(pub.head,token,(record,),now,selection_validated_utc=now-3600)
publisher=pub.publisher_envelope(now)
files,digest=build_artifact(pub.schedule,build_catalog(root),now,publisher=publisher,root=root)
pub.prepare(pub.head,now,files,digest,feed_publisher=publisher,artifact_profile='visual-v2')
print(json.dumps({'files':len(files),'bytes':sum(map(len,files.values())),'head':pub.head}))
store.close()
'''


class BridgeRuntimePublicTest(unittest.TestCase):
    setUp = prior.CloudRuntimeCheckoutTest.setUp
    tearDown = prior.CloudRuntimeCheckoutTest.tearDown
    arguments = prior.CloudRuntimeCheckoutTest.arguments
    runtime = prior.CloudRuntimeCheckoutTest.runtime
    cli = prior.CloudRuntimeCheckoutTest.cli
    snapshot = prior.CloudRuntimeCheckoutTest.snapshot
    poison = prior.CloudRuntimeCheckoutTest.poison
    authority = prior.CloudRuntimeCheckoutTest.authority

    def full_checkout(self):
        script = prior.job_script('prepare', 'Materialize exact reviewed runtime and catalog closure')
        result = subprocess.run(['bash', '-e', '-o', 'pipefail', '-c', script],
                                cwd=self.source, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        #595canonical inputDigests plus the authenticated recipe itself.
        self.assertEqual(596, json.loads(result.stdout)['catalogInputs'])
        # Independent inventory follows the literal source declarations rather
        # than build_catalog.inputDigests or production dependencies() helpers.
        data = {'catalog/source.json'}
        def read(pin):
            data.add(pin['path'])
            raw = (self.source / pin['path']).read_bytes()
            self.assertEqual(pin['sha256'], hashlib.sha256(raw).hexdigest())
            return json.loads(raw)
        recipe = json.loads((self.source / 'catalog/source.json').read_bytes())
        read(recipe['reference']);read(recipe['geography'])
        for pin in (recipe['assetSeed'], *recipe['curations']):
            source = read(pin)
            rows = ([a['facts'] for a in source['assets']] if 'assets' in source else
                    [row for kind in ('models','companies','countries') for row in source[kind]])
            data.update((Path(pin['path']).parent / row['file']).as_posix() for row in rows)
        bridge = read(recipe['visualBridge'])
        for pin in (bridge['topology'], bridge['d3'], bridge['topojson'], *bridge['notices']):
            data.add(pin['path'])
            self.assertEqual(pin['sha256'], hashlib.sha256((self.source / pin['path']).read_bytes()).hexdigest())
        regional = read(bridge['regional'])
        for pin in (regional['baseWorld'], *regional['clips'], *regional['notices'],
                    *[p for item in regional.get('supplements',[]) for p in (item,item['metadata'])]):
            data.add(pin['path'])
            self.assertEqual(pin['sha256'], hashlib.sha256((self.source / pin['path']).read_bytes()).hexdigest())
        self.assertEqual(595, len(data - {'catalog/source.json'}))
        seed = {p.removeprefix('/') for p in (self.source / '.github/spacefox-inputs.txt').read_text().splitlines()}
        tracked = set(git(self.source, 'ls-tree', '-r', '--name-only', 'HEAD').splitlines())
        seed &= tracked
        actual = {p.relative_to(self.source).as_posix() for p in self.source.rglob('*')
                  if p.is_file() and '.git' not in p.relative_to(self.source).parts}
        self.assertEqual(data | seed, actual)
        self.assertEqual('', git(self.source, 'status', '--porcelain'))

    def prepare(self, output):
        env = dict(os.environ, GITHUB_RUN_ID='87', GITHUB_RUN_ATTEMPT='1')
        for key in ('GH_TOKEN', 'GITHUB_OUTPUT', 'GIT_CONFIG_COUNT'):
            env.pop(key, None)
        result = subprocess.run([sys.executable, '-B', 'tools/cloud_feed.py',
                                 *self.arguments('prepare', '--output', str(output))],
                                cwd=self.source, env=env, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        return json.loads(result.stdout)

    def publisher(self):
        store = GitState(str(self.remote)); self.stores.append(store)
        return Publisher(store, self.code)

    def publish(self, output, *, challenge_roots=False):
        pub = self.publisher()
        expected = {p.relative_to(output).as_posix(): p.read_bytes()
                    for p in output.rglob('*') if p.is_file()}
        before = pub.ledger
        self.runtime('arm')
        armed = self.cli('arm', '--expected-base', pub.head, '--artifact-id', '99')
        self.runtime('deploy')
        self.service.artifact = expected
        self.assertEqual({'status': 'succeed'}, self.cli('deploy', '--expected-base', armed['head']))
        self.runtime('promote')
        if challenge_roots:
            for root in ('feed.json', 'wire2/feed.json'):
                count = 0
                def switch(path):
                    nonlocal count
                    if path == '/site/' + root:
                        count += 1
                        if count == 2:
                            self.service.live[root] = b'{}'
                self.service.read_hook = switch
                snapshot = self.snapshot()
                prior_journal = json.loads(git(self.remote,'show','refs/heads/feed-state:cloud.json'))
                posts = len(self.service.posts)
                self.cli('recover', success=False)
                self.assertGreaterEqual(count, 2)
                current = self.snapshot()
                if prior_journal['status'] == 'armed':
                    # Successful remote finality is durably recorded before
                    # HTTP admission. A failed root reread may change only that
                    # journal status, never ledger/pending/immutable bytes.
                    self.assertEqual([line for line in snapshot[1].splitlines() if not line.endswith('\tcloud.json')],
                                     [line for line in current[1].splitlines() if not line.endswith('\tcloud.json')])
                    observed = json.loads(git(self.remote,'show','refs/heads/feed-state:cloud.json'))
                    self.assertEqual(dict(prior_journal,status='succeed'),observed)
                else:
                    self.assertEqual(snapshot,current)
                self.assertEqual(before,self.publisher().ledger)
                self.assertEqual(posts, len(self.service.posts))
                self.service.read_hook = None
                self.service.live = dict(expected)
        self.cli('recover')
        after = self.publisher().ledger
        self.assertIsNone(after['pending'])
        self.assertEqual(before['pending'], after['active'])
        for key in ('accepted', 'requests', 'last_poll_utc', 'selection_validated_utc', 'backoff_until_utc'):
            self.assertEqual(before[key], after[key], key)
        self.assertEqual(expected, self.service.live)
        self.assertEqual(0, self.service.provider_calls)
        for path in expected:
            self.assertIn('/site/' + path, self.service.reads)
        return expected

    def test_dual_producer_pending_content_source_clocks_and_runtime_roots(self):
        self.full_checkout()
        result = subprocess.run([sys.executable, '-B', '-c', SEED, str(self.remote), self.code],
                                cwd=self.source, capture_output=True)
        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertGreater(json.loads(result.stdout)['files'], 71)
        pub = self.publisher(); original = pub.ledger
        first_output = self.base / 'first'
        recovered = self.prepare(first_output)
        self.assertEqual(('recovered_pending', 0), (recovered['result'], recovered['requests']))
        self.assertEqual(original, self.publisher().ledger)
        first = self.publish(first_output, challenge_roots=True)
        self.assertEqual((1, 2), tuple(json.loads(first[p])['schemaVersion'] for p in ('feed.json', 'wire2/feed.json')))
        # Restore the full authenticated source only for prepare, then change a
        # genuine recipe semantic input in the isolated public source clone.
        self.full_checkout()
        recipe = json.loads((self.source / 'catalog/source.json').read_bytes())
        recipe['catalogVersion'] += '.content-clock'
        (self.source / 'catalog/source.json').write_bytes(prior.encoded(recipe))
        git(self.source, 'add', '--sparse', 'catalog/source.json')
        git(self.source, 'commit', '-qm', 'data-only catalog revision fixture')
        self.code = git(self.source, 'rev-parse', 'HEAD')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        before = original
        second_output = self.base / 'second'
        content = self.prepare(second_output)
        self.assertEqual(('content_pending', 0), (content['result'], content['requests']))
        pub = self.publisher()
        for key in ('accepted', 'requests', 'last_poll_utc', 'selection_validated_utc'):
            self.assertEqual(before[key], pub.ledger[key], key)
        # Deliberately corrupt one authenticated saved optional shard. Runtime
        # must reject before intent/POST, retaining exact corrupt fixture state.
        baseline = pub.head
        optional = next(p for p in pub.pending_files() if p.startswith('objects/'))
        self.runtime('arm')
        self.poison('artifacts/2/' + optional, b'{}')
        corrupt = self.snapshot(); posts = len(self.service.posts)
        self.cli('arm', '--expected-base', corrupt[0], '--artifact-id', '99', success=False)
        self.assertEqual(corrupt, self.snapshot())
        self.assertEqual((posts, 0), (len(self.service.posts), self.service.provider_calls))
        git(self.remote, 'update-ref', 'refs/heads/feed-state', baseline)
        second = self.publish(second_output)
        for path, raw in first.items():
            if path not in ('feed.json', 'wire2/feed.json'):
                self.assertEqual(raw, second[path])
        self.assertNotEqual(first['wire2/feed.json'], second['wire2/feed.json'])
        self.assertEqual(2, len(self.service.posts))
        # Code-only adoption has no artifact generation or source-age effect.
        self.full_checkout()
        git(self.source, 'commit', '--allow-empty', '-qm', 'source-only fixture')
        self.code = git(self.source, 'rev-parse', 'HEAD')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        before = self.publisher().ledger
        no_output = self.base / 'not-due'
        not_due = self.prepare(no_output)
        self.assertEqual(('not_due', 0), tuple(not_due[k] for k in ('result', 'requests')))
        after = self.publisher().ledger
        for key in ('active', 'generation', 'accepted', 'requests', 'last_poll_utc', 'selection_validated_utc'):
            self.assertEqual(before[key], after[key], key)
        self.assertFalse(no_output.exists())
        self.assertEqual((2, 0), (len(self.service.posts), self.service.provider_calls))
        tracked = set(git(ROOT,'ls-tree','-r','--name-only','HEAD').splitlines())
        runtime_files = {p.removeprefix('/') for p in (ROOT / '.github/spacefox-inputs.txt').read_text().splitlines()
                         if p != '/catalog/source.json'} & tracked
        print('BRIDGE_TRACE ' + json.dumps({'runtimeFiles': len(runtime_files),
              'prepareInputs':596,'canonicalInputDigests':595,'firstFiles':len(first),'unionFiles':len(second),'unionBytes':sum(map(len,second.values())),
              'posts':2,'providerCalls':0,'selectionValidatedUtc':after['selection_validated_utc'],
              'twoMutableRootsChallenged':True,'sourceOnlyGeneration':after['generation']},sort_keys=True))

    def test_unmarked_v1_pending_adoption_remains_exact_without_source_data(self):
        self.runtime('arm')
        pub, _, first = self.authority()
        ledger = pub.ledger
        ledger['pending'].pop('artifact_profile')
        snap = ledger['pending']
        snap['artifact_revision'] = hashlib.sha256(prior.encoded({k:v for k,v in snap.items() if k!='artifact_revision'})).hexdigest()
        # Historical compatibility fixture: current API intentionally emits an
        # explicit profile, so install exact old-format durable bytes directly.
        # Start the historical pending branch at its genuine no-pending parent.
        # Stripping a profile from an existing pending commit is intentionally
        # forbidden; that would be an impossible historical transition.
        parent = git(self.remote,'rev-parse',pub.head+'^')
        origin = pub.store._commit(ledger, parent, {f'artifacts/1/{p}':raw for p,raw in first.items()})
        pub.store._git('push', f'--force-with-lease=refs/heads/feed-state:{pub.head}',
                       pub.store.remote, f'{origin}:refs/heads/feed-state')
        historical = ledger['pending']
        git(self.source, 'commit', '--allow-empty', '-qm', 'new code adopts historical v1')
        self.code = git(self.source, 'rev-parse', 'HEAD')
        git(self.source, 'push', '-q', str(self.remote), 'HEAD:refs/heads/main')
        self.cli('recover')
        adopted = self.publisher()
        self.assertEqual(historical, adopted.ledger['pending'])
        self.assertEqual(first, adopted.pending_files())
        output = self.base / 'historical';output.mkdir()
        for path, raw in first.items():
            target=output/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        self.publish(output)
        self.assertEqual(historical,self.publisher().ledger['active'])
        self.assertEqual((1,0),(len(self.service.posts),self.service.provider_calls))

    def test_manual_pre_post_fault_retains_intent_and_requires_exact_skipped_attempt(self):
        workflow = (ROOT / '.github/workflows/update-feed.yml').read_text()
        definition = workflow.split('      qualify_pre_post_recovery:\n',1)[1].split('\n\n',1)[0]
        self.assertIn('        type: boolean\n        default: false', definition)
        arm = workflow.split('\n  arm:\n',1)[1].split('\n  deploy:\n',1)[0]
        intent = 'Persist unique candidate/source/run/artifact deployment intent'
        fault = 'Qualify recovery after intent before Pages POST'
        self.assertLess(arm.index(intent),arm.index(fault))
        condition = arm.split('      - name: '+fault+'\n',1)[1].splitlines()[0]
        self.assertEqual("        if: github.event_name == 'workflow_dispatch' && inputs.qualify_pre_post_recovery",condition)
        # The literal condition has one manual-event conjunct and one boolean
        # input conjunct. Its truth table guards default/schedule/push paths.
        for event,enabled,expected in [('workflow_dispatch',False,False),('workflow_dispatch',True,True),
                                       ('schedule',True,False),('push',True,False)]:
            self.assertEqual(expected,event=='workflow_dispatch' and enabled)
        self.assertTrue(workflow.split('\n  deploy:\n',1)[1].startswith('    needs: arm\n'))
        self.assertIn("if: always() && needs.arm.result == 'success'",workflow)
        self.runtime('arm')
        pub, _, expected = self.authority()
        original = pub.ledger
        self.cli('arm','--expected-base',pub.head,'--artifact-id','99')
        before = self.snapshot()
        script = prior.job_script('arm',fault)
        result = subprocess.run(['bash','-e','-o','pipefail','-c',script],cwd=self.source,capture_output=True)
        self.assertEqual(97,result.returncode)
        self.assertIn(b'Deliberate qualification fault',result.stderr)
        saved = json.loads(git(self.remote,'show','refs/heads/feed-state:cloud.json'))
        self.assertEqual('armed',saved['status'])
        self.assertEqual(before,self.snapshot())
        self.assertEqual(original,self.publisher().ledger)
        self.assertEqual(([],0),(self.service.posts,self.service.provider_calls))
        # New normal invocation may resolve404 only from the authenticated exact
        # completed old attempt, with an explicitly skipped deploy/empty steps.
        self.run_id = 88
        prefix='/repos/owner/SpaceFox/actions/runs/87/attempts/1'
        valid_run={'id':87,'run_attempt':1,'head_sha':self.code,'head_branch':'main','status':'completed',
                   'event':'workflow_dispatch','path':'.github/workflows/update-feed.yml',
                   'repository':{'full_name':'owner/SpaceFox'}}
        valid_job={'name':'deploy','run_id':87,'head_sha':self.code,'status':'completed','conclusion':'skipped','steps':[]}
        valid={prefix:valid_run,prefix+'/jobs?per_page=100':{'total_count':1,'jobs':[valid_job]}}
        for mode in ('unknown','run-started','deploy-started','wrong-attempt'):
            self.service.actions=deepcopy(valid)
            if mode=='unknown':self.service.actions={}
            elif mode=='run-started':self.service.actions[prefix]['status']='in_progress'
            elif mode=='wrong-attempt':self.service.actions[prefix]['run_attempt']=2
            else:self.service.actions[prefix+'/jobs?per_page=100']['jobs'][0].update(conclusion='failure',steps=[
                {'name':'POST once, then bound async polling and cancellation finality','status':'completed','conclusion':'failure'}])
            self.cli('recover',success=False)
            self.assertEqual(before,self.snapshot())
            self.assertEqual(([],0),(self.service.posts,self.service.provider_calls))
        self.service.actions=valid
        self.cli('recover')
        after=json.loads(git(self.remote,'show','refs/heads/feed-state:cloud.json'))
        self.assertEqual('not_started',after['status'])
        self.assertEqual(saved['intent'],after['intent'])
        pub=self.publisher()
        self.assertEqual(original,pub.ledger)
        self.assertEqual(expected,pub.pending_files())
        self.assertIsNone(pub.ledger['active'])
        self.assertEqual(([],0),(self.service.posts,self.service.provider_calls))
        print('PRE_POST_RECOVERY '+json.dumps({'faultExit':97,'intentStatusBefore':'armed','intentStatusAfter':'not_started',
              'refusals':4,'newRunId':88,'oldRunId':87,'posts':0,'providerCalls':0,'pendingExact':True},sort_keys=True))

    def test_frozen_rich_a_b_exact_union_through_runtime_only_cli(self):
        from tools.spacefox.schedule import (LaunchRecord,StableId,IdKind,Timing,TimePrecision,LaunchStatus)
        from tools.spacefox.publisher import LiveRevision
        self.runtime('arm')
        store=GitState(str(self.remote));self.stores.append(store);store.bootstrap(self.code)
        pub=Publisher(store,self.code);pub.reconcile(None)
        def identity(kind,value):return StableId(kind,'ll2',value)
        record=LaunchRecord(identity(IdKind.LAUNCH,'bridge-literal'),Timing(TimePrecision.EXACT,exact_utc=NOW+7200),
            LaunchStatus.PENDING,NOW-3600,configuration_id=identity(IdKind.CONFIGURATION,'164'),
            operator_id=identity(IdKind.ORGANIZATION,'121'),site_id=identity(IdKind.SITE,'80'),
            country_id=identity(IdKind.COUNTRY,'2'),configuration_name='Falcon 9',operator_name='SpaceX',
            mission_name='Луна 零',mission_purpose='Measure lunar radiation',country_code='USA',site_location_name='Florida')
        token=pub.reserve(pub.head,NOW)
        pub.accept_source(pub.head,token,(record,),NOW,selection_validated_utc=NOW-3600)
        original=pub.ledger
        corpus=ROOT/'tests/fixtures/bridge-v2';index=json.loads((corpus/'index.json').read_bytes())
        previous={};observed=[]
        for generation,label in ((1,'a'),(2,'b')):
            files={p.relative_to(corpus/label).as_posix():p.read_bytes()
                   for p in (corpus/label).rglob('*') if p.is_file()}
            self.assertEqual(set(index[label]['files']),set(files))
            for path,raw in files.items():
                self.assertEqual(index[label]['files'][path]['sha256'],hashlib.sha256(raw).hexdigest())
                self.assertEqual(index[label]['files'][path]['bytes'],len(raw))
            # Keep every frozen immutable artifact byte exact. Only the two
            # mutable roots bind this freshly bootstrapped fixture namespace.
            for path in ('feed.json','wire2/feed.json'):
                root=json.loads(files[path]);root['publisher']=pub.publisher_envelope(NOW)
                files[path]=prior.encoded(root)
            root=json.loads(files['feed.json'])
            self.assertEqual(('ll2:configuration:164','ll2:organization:121','ll2:site:80','ll2:country:2'),
                tuple(root['launch'][k] for k in ('configuration_id','operator_id','site_id','country_id')))
            pub.prepare(pub.head,NOW,files,root['catalogDigest'],feed_publisher=root['publisher'],artifact_profile='visual-v2')
            # A fresh reader must reopen this exact full rich pending closure.
            self.assertEqual(files,self.publisher().pending_files())
            expected={**{p:raw for p,raw in previous.items() if p not in ('feed.json','wire2/feed.json')},**files}
            output=self.base/('frozen-'+label);output.mkdir()
            for path,raw in expected.items():
                target=output/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
            actual=self.publish(output,challenge_roots=generation==2)
            self.assertEqual(expected,actual)
            observed.append({'generation':generation,'files':len(actual),'bytes':sum(map(len,actual.values()))})
            pub=self.publisher()
            # publish() just completed exact real HTTP readback and promotion.
            # Reopen requires the same observed live revision before new work.
            active=pub.ledger['active']
            pub.reconcile(LiveRevision(active['generation'],active['artifact_revision']))
            previous=files
        self.assertEqual((87,545120),(len(actual),sum(map(len,actual.values()))))
        for key in ('accepted','requests','last_poll_utc','selection_validated_utc','backoff_until_utc'):
            self.assertEqual(original[key],pub.ledger[key],key)
        self.assertEqual((2,0),(len(self.service.posts),self.service.provider_calls))
        self.assertFalse((self.source/'catalog').exists())
        self.assertFalse((self.source/'tests').exists())
        print('FROZEN_RICH_TRACE '+json.dumps({'generations':observed,'bothMutableRootsChallenged':True,
              'providerCalls':0,'builderCalls':0,'nodeCalls':0,'catalogSourceReads':0,'immutableFixtureBytesExact':True},sort_keys=True))


if __name__ == '__main__':
    unittest.main()
