"""One isolated scenario, with distinct literal positive and refusal checks."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests.test_current_motion_publisher import captured_starship, git, NOW, ROOT, MemoryHTTP
from tools.spacefox.catalog import build_catalog
from tools.spacefox.cloud import delivery, delivery_files
from tools.spacefox.native_motion import PROFILE, build_artifact
from tools.spacefox.provider import normalize_launch
from tools.spacefox.publisher import GitState, Publisher, STATE_REF, StateError


class HostedRocketControlTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='spacefox-closure-')
        path = Path(cls.tmp.name)
        remote = path / 'remote.git'
        source = path / 'source'
        source.mkdir()
        subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
        git(source, 'init', '-q')
        git(source, 'config', 'user.name', 'Local qualification')
        git(source, 'config', 'user.email', 'local@example.invalid')
        git(source, 'commit', '--allow-empty', '-qm', 'source')
        code = git(source, 'rev-parse', 'HEAD')
        git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
        store = GitState(str(remote))
        try:
            store.bootstrap(code)
            pub = Publisher(store, code)
            pub.reconcile(None)
            row = captured_starship()
            token = pub.reserve(pub.head, NOW, trigger='manual')
            pub.accept_source(pub.head, token, (normalize_launch(row, NOW),), NOW, selection_validated_utc=NOW)
            catalog = build_catalog(ROOT)
            envelope = pub.publisher_envelope(NOW)
            first, digest = build_artifact(pub.schedule, catalog, NOW, publisher=envelope, root=ROOT)
            revision = pub.prepare(pub.head, NOW, first, digest, feed_publisher=envelope, artifact_profile=PROFILE)
            if pub.reconcile(revision) != 'promoted':
                raise AssertionError('initial candidate was not promoted')
            site = MemoryHTTP(first)
            served_before = site.request('GET', 'http://local/site/feed.json', limit=8192)
            active_head = pub.head
            git(remote, 'update-ref', '-d', STATE_REF, active_head)
            try:
                Publisher(store, code)
            except StateError:
                missing_refused = True
            else:
                missing_refused = False
            try:
                store.bootstrap(code)
            except StateError:
                bootstrap_refused = True
            else:
                bootstrap_refused = False
            served_after = site.request('GET', 'http://local/site/feed.json', limit=8192)
            no_state = store._refs(STATE_REF) == {}
            git(remote, 'update-ref', STATE_REF, active_head)
            pub = Publisher(store, code)
            pub.reconcile(revision)
            changed = dict(row, net='2026-11-13T23:00:00Z', window_start='2026-11-13T23:00:00Z',
                           last_updated='2026-11-13T07:20:00Z')
            later = NOW + 3601
            token = pub.reserve(pub.head, later, trigger='scheduled')
            pub.accept_source(pub.head, token, (normalize_launch(changed, later),), later,
                              selection_validated_utc=later)
            pub = Publisher(store, code)
            pub.reconcile(revision)
            rescheduled = pub.schedule.entries[0].rescheduled
            source_age = pub.ledger['selection_validated_utc']
            envelope = pub.publisher_envelope(later)
            second, digest = build_artifact(pub.schedule, catalog, later, publisher=envelope, root=ROOT)
            first_feed = json.loads(first['feed.json'])
            second_feed = json.loads(second['feed.json'])
            scene = json.loads(first[first_feed['visualSelection']['path']])
            rocket = json.loads(first[scene['roles']['rocket']['descriptor']['path']])
            raster = rocket['shards'][0]['path']
            broken = dict(second)
            del broken[raster]
            broken.pop(raster + '.txt', None)
            before = pub.head
            try:
                pub.prepare(before, later, broken, digest, feed_publisher=envelope, artifact_profile=PROFILE)
            except (ValueError, RuntimeError):
                omitted_refused = True
            else:
                omitted_refused = False
            unchanged_head = pub.head == before
            no_pending = pub.ledger['pending'] is None
            if omitted_refused:
                pub.prepare(before, later, second, digest, feed_publisher=envelope, artifact_profile=PROFILE)
                complete = delivery_files(pub, delivery(pub))
            else:
                complete = {}
            cls.observation = dict(missing_refused=missing_refused, bootstrap_refused=bootstrap_refused,
                served_before=served_before, served_after=served_after, no_state=no_state,
                rescheduled=rescheduled, source_age=source_age, later=later,
                old_net=first_feed['launch']['timing']['source_net'], new_net=second_feed['launch']['timing']['source_net'],
                first_raster=first[raster], second_raster=second[raster], delivered_raster=complete.get(raster),
                second_feed=second['feed.json'], delivered_feed=complete.get('feed.json'),
                omitted_refused=omitted_refused, unchanged_head=unchanged_head, no_pending=no_pending)
        finally:
            store.close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_missing_authority_keeps_existing_deployment(self):
        o = self.observation
        self.assertTrue(o['missing_refused'])
        self.assertTrue(o['bootstrap_refused'])
        self.assertTrue(o['no_state'])
        self.assertEqual(o['served_before'], o['served_after'])
        self.assertEqual(o['served_before'][0], 200)

    def test_schedule_change_keeps_referenced_raster_and_reopens(self):
        o = self.observation
        self.assertEqual(o['old_net'], '2026-11-13T22:45:00Z')
        self.assertEqual(o['new_net'], '2026-11-13T23:00:00Z')
        self.assertTrue(o['rescheduled'])
        self.assertEqual(o['source_age'], o['later'])
        self.assertEqual(o['first_raster'], o['second_raster'])
        self.assertEqual(o['first_raster'], o['delivered_raster'])
        self.assertEqual(o['second_feed'], o['delivered_feed'])

    def test_omitted_rocket_shard_refuses_before_pending(self):
        o = self.observation
        self.assertTrue(o['omitted_refused'])
        self.assertTrue(o['unchanged_head'])
        self.assertTrue(o['no_pending'])
