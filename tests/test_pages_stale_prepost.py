"""Recovery permits a proven stale pre-POST failure, never ambiguous POSTs."""
import unittest
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
        self.sources={name:(ROOT/name).read_text() for name in ('tools/cloud_feed.py','tools/spacefox/cloud.py','tools/spacefox/publisher.py')}
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
