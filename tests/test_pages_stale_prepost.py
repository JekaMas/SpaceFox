"""Recovery permits a proven stale pre-POST failure, never ambiguous POSTs."""
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
from tools.spacefox.cloud import Pages

ROOT = Path(__file__).resolve().parents[1]
SOURCE = 'a' * 40
INTENT = {'repository':'local/spacefox','runId':42,'runAttempt':1,'source':SOURCE}

class FakePages(Pages):
    def __init__(self):
        self.repository='local/spacefox'
        self.run={'id':42,'run_attempt':1,'head_sha':SOURCE,'head_branch':'main','status':'completed','event':'push','path':'.github/workflows/update-feed.yml','repository':{'full_name':self.repository}}
        self.job={'id':55,'run_id':42,'head_sha':SOURCE,'name':'deploy','status':'completed','conclusion':'failure','steps':[{'name':'POST once, then bound async polling and cancellation finality','status':'completed','conclusion':'failure','started_at':'2026-11-17T01:01:43Z','completed_at':'2026-11-17T01:02:04Z'}]}
        self.log='deploy\tUNKNOWN STEP\t2026-11-17T01:02:03Z cloud-feed: queued source code is stale before work permission\ndeploy\tUNKNOWN STEP\t2026-11-17T01:02:04Z ##[error]Process completed with exit code 2.\n'
        self.sources={name:(ROOT/name).read_text() for name in ('tools/cloud_feed.py','tools/spacefox/cloud.py','tools/spacefox/publisher.py','.github/workflows/update-feed.yml')}
    def repo_call(self, method, suffix, document=None):
        return {'jobs':[self.job],'total_count':1} if '/jobs?' in suffix else self.run
    def _job_log(self, intent, job): return self.log
    def _source_text(self, name, revision): return self.sources[name]

class StalePrePost(unittest.TestCase):
    def test_exact_prepost_failure_recovers_but_ambiguous_cases_refuse(self):
        p=FakePages();self.assertTrue(p.never_started(INTENT))
        for log in ('', 'cloud-feed: some other error\n', p.log+p.log):
            with self.subTest(log=log):p.log=log;self.assertFalse(p.never_started(INTENT))
        p=FakePages()
        p.sources['tools/spacefox/cloud.py']=p.sources['tools/spacefox/cloud.py'].replace('pages.create(intent, id_token)', 'pages.create(intent, id_token)\n    pub._context(expected)',1)
        self.assertFalse(p.never_started(INTENT))
        p=FakePages();p.job['steps'][0]['completed_at']='2026-11-17T01:02:02Z';self.assertFalse(p.never_started(INTENT))
        p=FakePages();p.job['head_sha']='b'*40;self.assertFalse(p.never_started(INTENT))
        p=FakePages();p.run['run_attempt']=2;self.assertFalse(p.never_started(INTENT))
        p=FakePages();p.job['steps'][0]['conclusion']='cancelled';self.assertFalse(p.never_started(INTENT))

    def test_readback_503_prepost_requires_matching_control_flow_and_exact_error(self):
        p=FakePages()
        p.log=(ROOT/'openspec/changes/qualify-current-rocket-art/evidence/pages-prepost/original-44226344248-excerpt.log').read_text()
        p.job['steps'][0]['started_at']='2026-11-18T03:00:43Z'
        p.job['steps'][0]['completed_at']='2026-11-18T03:01:03Z'
        self.assertTrue(p.never_started(INTENT))
        for mutation in ('status', 'after_post', 'duplicate', 'workflow'):
            q=FakePages();q.log=p.log;q.job['steps'][0].update(p.job['steps'][0])
            if mutation=='status': q.log=q.log.replace('"status":503','"status":200')
            if mutation=='after_post': q.sources['tools/spacefox/cloud.py']=q.sources['tools/spacefox/cloud.py'].replace('pages.create(intent, id_token)  # Exactly one POST; no transport retry.', 'pages.create(intent, id_token)\n    site.observe(pub)')
            if mutation=='duplicate': q.log+=q.log
            if mutation=='workflow': q.sources['.github/workflows/update-feed.yml']+='\n# unknown workflow change\n'
            with self.subTest(mutation=mutation):self.assertFalse(q.never_started(INTENT))

    def test_503_witness_reaches_owned_not_started_transition(self):
        from tools.spacefox.cloud import recover, DeploymentStatusEmpty
        p=FakePages();p.log=(ROOT/'openspec/changes/qualify-current-rocket-art/evidence/pages-prepost/original-44226344248-excerpt.log').read_text()
        p.job['steps'][0]['started_at']='2026-11-18T03:00:43Z';p.job['steps'][0]['completed_at']='2026-11-18T03:01:03Z'
        p.wait=Mock(side_effect=DeploymentStatusEmpty('empty'))
        pub=Mock();pub.head='head';pub.deployment_event.return_value=(pub,None)
        intent=dict(INTENT,buildVersion='a'*40)
        value={'status':'armed','intent':intent,'files':{}}
        site=Mock();site.observe.return_value=None
        with patch('tools.spacefox.cloud.journal',side_effect=[value,{'status':'not_started','intent':intent,'files':{}}]):
            self.assertIs(recover(pub,site,p),pub)
        pub.deployment_event.assert_called_once_with('observed',intent=intent,status='not_started')
        pub.reconcile.assert_called_once_with(None)

    def test_post_then_stale_second_command_is_not_unstarted(self):
        p=FakePages()
        name='.github/workflows/update-feed.yml'
        command='run: python3 -B tools/cloud_feed.py --site "$SPACEFOX_SITE" deploy --expected-base "$EXPECTED_BASE"'
        self.assertEqual(p.sources[name].count(command),1)
        p.sources[name]=p.sources[name].replace(command,
            'run: |\n          python3 -B tools/cloud_feed.py --site "$SPACEFOX_SITE" deploy --expected-base "$EXPECTED_BASE"\n          python3 -B tools/cloud_feed.py --site "$SPACEFOX_SITE" probe')
        # Functions, identity and the single final stale error still match, but
        # the first command could already POST. The error proves only the
        # second invocation failed before its own work permission.
        self.assertFalse(p.never_started(INTENT))

    def test_sparse_closure_contains_current_workflow_for_historical_comparison(self):
        lines=(ROOT/'.github/spacefox-inputs.txt').read_text().splitlines()
        self.assertEqual(lines.count('/.github/workflows/update-feed.yml'),1)

    def test_missing_workflow_source_remains_armed(self):
        p=FakePages();p.sources['.github/workflows/update-feed.yml']=None
        self.assertFalse(p.never_started(INTENT))
