"""Current joined producer/art/diagnostic boundary with real local Git and HTTP.

LL2 and CDN alone are authored loopback services. No hosted, native or physical
acceptance follows from these directed composition cases.
"""
import copy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import unittest

from tests import test_schedule_provider as support
from tests import test_provider_detail_efficiency as detail_support
from tools.spacefox.catalog import build_catalog
from tools.spacefox.cloud import CloudError, Site, delivery, delivery_files
from tools.spacefox.publisher import LiveRevision
from tools.spacefox.schedule import LaunchStatus
from tools.spacefox.visual_bridge import build_artifact
from tools.update_feed import update

ROOT = support.ROOT
NOW = support.NOW
ART = 'spacefox:asset:remaining-r3-shavit-nasa1996'
ART_SHA = '48b2da7730e72cec1cd76a45c3c3ed7b2c0857c8f809671732516207f9407217'


class ProviderArtDiagnosticsJoinTest(unittest.TestCase):
    server = detail_support.DetailEfficiencyTest.server

    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        owner = cls(methodName='runTest')
        support.ScheduleProviderTest.setUp(owner)
        cls.owner = owner
        terminal, nonterminal = detail_support.row(1, 3), detail_support.row(2)
        with owner.server([terminal, nonterminal]) as (client, _, _, _):
            update(owner.pub, client, NOW, cls.catalog, detail_limit=0)
        support.ScheduleProviderTest.promote(owner)
        cls.old_terminal = next(e for e in owner.pub.schedule.entries if e.record.launch_id.value == terminal['id'])
        primary = detail_support.row(3)
        primary['rocket']['configuration'].update(id=44, name='Shavit')
        detailed = {**nonterminal, 'response_mode': 'detailed',
                    'status': {'id': 3, 'name': 'Launch Successful'},
                    'last_updated': '2026-11-12T00:30:00Z'}
        with owner.server([primary], now=NOW + 3600,
                          details={nonterminal['id']: detailed}) as (client, _, calls, permissions):
            cls.result = update(owner.pub, client, NOW + 3600, cls.catalog,
                                detail_limit=1, artifact_profile='visual-v2',
                                artifact_builder=lambda *args, **kwargs: build_artifact(*args, **kwargs, root=ROOT))
            cls.calls, cls.permissions = list(calls), list(permissions)
        cls.pub, cls.store = owner.pub, owner.store
        cls.manifest = delivery(cls.pub)
        cls.files = delivery_files(cls.pub, cls.manifest)
        cls.ledger = copy.deepcopy(cls.pub.ledger)
        cls.refs = support.git(owner.remote, 'show-ref')
        feed = json.loads(cls.files['wire2/feed.json'])
        cls.selection = json.loads(cls.files[feed['visualSelection']['path']])
        cls.descriptor = json.loads(cls.files[cls.selection['roles']['rocket']['descriptor']['path']])
        cls.art_path = cls.descriptor['shards'][0]['path']

    @classmethod
    def tearDownClass(cls):
        support.ScheduleProviderTest.tearDown(cls.owner)

    def setUp(self):
        self.live, self.reads = dict(self.files), []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                path = self.path.removeprefix('/site/')
                owner.reads.append(path)
                raw = owner.live.get(path)
                self.send_response(404 if raw is None else 200)
                raw = b'' if raw is None else raw
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

        self.http = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()
        self.site = Site(f'http://127.0.0.1:{self.http.server_port}/site', local_http=True)

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join()
        self.assertEqual(self.ledger, self.pub.ledger)
        self.assertEqual(self.refs, support.git(self.owner.remote, 'show-ref'))
        self.assertEqual(self.files, delivery_files(self.pub, self.manifest))

    def test_current_provider_art_and_exact_dual_readback_compose(self):
        self.assertEqual(('pending', 2, 1, []),
                         (self.result['result'], self.result['requests'],
                          self.result['traversal']['detailRequests'], self.result['detailFailures']))
        self.assertEqual(['reserved', 'reserved'], self.permissions)
        self.assertIn('/upcoming/', self.calls[0])
        self.assertTrue(self.calls[1].endswith('/00000000-0000-4000-8000-000000000002/?mode=normal'))
        current = {e.record.launch_id.value: e for e in self.pub.schedule.entries}
        self.assertEqual(self.old_terminal, current['00000000-0000-4000-8000-000000000001'])
        reconciled = current['00000000-0000-4000-8000-000000000002'].record
        self.assertEqual((LaunchStatus.COMPLETED, NOW + 3600, NOW + 1800),
                         (reconciled.status, reconciled.source_validated_utc, reconciled.source_updated_utc))
        self.assertEqual(NOW + 3600, self.pub.ledger['selection_validated_utc'])
        self.assertEqual(('ll2:launch:00000000-0000-4000-8000-000000000003', 'll2:configuration:44'),
                         (self.selection['launchId'], self.selection['modelId']))
        self.assertEqual((ART, ART_SHA), (self.descriptor['assetId'], self.descriptor['sha256']))
        pending = self.pub.ledger['pending']
        self.assertEqual(LiveRevision(pending['generation'], pending['artifact_revision']),
                         self.site.observe(self.pub, self.manifest))
        self.assertEqual(set(self.files), set(self.reads))
        self.assertEqual((2, 2, len(self.files) + 2),
                         (self.reads.count('feed.json'), self.reads.count('wire2/feed.json'), len(self.reads)))

    def test_corrupt_new_art_reports_exact_immutable_digest_without_mutation(self):
        raw = b'response-body-secret'
        self.live[self.art_path] = raw
        with self.assertRaises(CloudError) as caught:
            self.site.observe(self.pub, self.manifest)
        message = str(caught.exception)
        self.assertLess(len(message.encode()), 1024)
        self.assertNotIn('response-body-secret', message)
        self.assertNotIn(self.site.base, message)
        context = json.loads(message.split('; readback=', 1)[1])
        expected = self.files[self.art_path]
        self.assertEqual(dict(path=self.art_path, kind='immutable-file', phase='closure', status=200,
                              expected={'bytes': len(expected), 'sha256': hashlib.sha256(expected).hexdigest()},
                              actual={'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}), context)
        self.assertEqual(1, self.reads.count(self.art_path))
        self.assertEqual(1, self.reads.count('feed.json'))
        self.assertFalse(any('/2.3.0/' in p or '/repos/' in p for p in self.reads))


if __name__ == '__main__':
    unittest.main()
