"""Durable same-format source-extension selection; no hosted or device claim."""
import copy
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests.test_current_motion_publisher import NOW, ROOT, captured_starship, git
from tools.spacefox.catalog import build_catalog, loads_json
from tools.spacefox.cloud import CloudError, delivery, delivery_files, snapshot_files
from tools.spacefox.native_motion import PROFILE, build_artifact, read_ref
from tools.spacefox.provider import normalize_launch
from tools.spacefox.publisher import GitState, Publisher


class CurrentGeographyDurableTest(unittest.TestCase):
    def test_source_extension_survives_current_recovery_and_reopen(self):
        with tempfile.TemporaryDirectory(prefix='spacefox-geography-durable-') as tmp:
            directory = Path(tmp)
            remote, source = directory / 'remote.git', directory / 'source'
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
                token = pub.reserve(pub.head, NOW, trigger='manual')
                pub.accept_source(pub.head, token, (normalize_launch(captured_starship(), NOW),), NOW, selection_validated_utc=NOW)
                catalog = build_catalog(ROOT)
                first, digest = build_artifact(pub.schedule, catalog, NOW, publisher=pub.publisher_envelope(NOW), root=ROOT)
                first_revision = pub.prepare(pub.head, NOW, first, digest, artifact_profile=PROFILE)
                pub.reconcile(first_revision)
                current = copy.deepcopy(catalog)
                current['catalogVersion'] += '.source-extension'
                row = current['dictionaries']['configurations']['ll2:configuration:522']
                for facts in (row['facts'], row['originalFacts']):
                    facts['providerExtension'] = {'flag': False, 'missing': None}
                    facts['officialLifecycle'] = 'raw-provider-extension'
                second, digest2 = build_artifact(pub.schedule, current, NOW + 1, publisher=pub.publisher_envelope(NOW + 1), root=ROOT)
                second_revision = pub.prepare(pub.head, NOW + 1, second, digest2, artifact_profile=PROFILE)
                manifest = delivery(pub)
                combined = delivery_files(pub, manifest)
                self.assertTrue(all(combined[p] == data for p, data in first.items() if p not in ('feed.json', 'feed.json.txt')))
                self.assertEqual(combined['feed.json'], second['feed.json'])
                reopened = Publisher(store, code)
                self.assertEqual(reopened.pending_files(), second)
                self.assertEqual(snapshot_files(store, reopened.head, 1)[1], first)
                feed = loads_json(second['feed.json'])
                scene = loads_json(read_ref(feed['visualSelection'], second))
                origin = loads_json(second[scene['origins']['model']['sourceRecord']['path']])
                self.assertEqual(origin['owner']['facts']['officialLifecycle'], 'raw-provider-extension')
                self.assertEqual(origin['owner']['originalFacts']['providerExtension'], {'flag': False, 'missing': None})
                self.assertEqual(origin['owner']['references']['origin'], catalog['dictionaries']['configurations']['ll2:configuration:522']['references']['origin'])
                reopened.reconcile(second_revision)
                final = Publisher(store, code)
                self.assertEqual(snapshot_files(store, final.head, 2)[1], second)
                # Host durable lookup retains active+pending, not generation 1
                # after generation 2 is promoted. Prior bytes were checked above.
                with self.assertRaisesRegex(CloudError, 'not a durable snapshot'):
                    snapshot_files(store, final.head, 1)
            finally:
                store.close()
