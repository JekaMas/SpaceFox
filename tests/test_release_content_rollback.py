"""Current publisher rollback using retained source, real assets and local Git."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests.test_basic_publisher_clock import current_source_closure
from tests.test_current_motion_publisher import captured_starship, git, NOW, ROOT
from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.native_motion import PROFILE, build_artifact, read_ref, with_text_transport
from tools.spacefox.provider import normalize_launch
from tools.spacefox.publisher import GitState, Publisher, StateError


class ContentRollbackTest(unittest.TestCase):
    def test_prior_art_republished_with_new_generation_and_honest_age(self):
        with tempfile.TemporaryDirectory(prefix='spacefox-rollback-') as tmp:
            base = Path(tmp); content = base / 'content'; content.mkdir()
            for name, raw in current_source_closure().items():
                path = content / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
            remote = base / 'state.git'; source = base / 'source'; source.mkdir()
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            git(source, 'init', '-q'); git(source, 'config', 'user.name', 'Local test')
            git(source, 'config', 'user.email', 'local@example.invalid')
            git(source, 'commit', '--allow-empty', '-qm', 'source')
            code = git(source, 'rev-parse', 'HEAD'); git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            try:
                store.bootstrap(code); pub = Publisher(store, code); pub.reconcile(None)
                token = pub.reserve(pub.head, NOW, trigger='manual')
                pub.accept_source(pub.head, token, (normalize_launch(captured_starship(), NOW),), NOW, selection_validated_utc=NOW)
                catalog_a = build_catalog(content)
                def publish(catalog, now):
                    files, digest = build_artifact(pub.schedule, catalog, now, publisher=pub.publisher_envelope(now), root=content)
                    revision = pub.prepare(pub.head, now, files, digest, feed_publisher=pub.publisher_envelope(now), artifact_profile=PROFILE)
                    self.assertEqual(pub.reconcile(revision), 'promoted')
                    return files
                first = publish(catalog_a, NOW)
                svg = content / 'assets/global/further-20261112-r2/svg/starship-v3-2026.svg'
                original = svg.read_bytes()
                # Mutate an actual SVG color, and re-pin the reviewed-source chain in isolation.
                import re, hashlib
                match = re.search(rb'#[0-9a-fA-F]{6}', original)
                self.assertIsNotNone(match)
                replacement = b'#123456' if match.group() != b'#123456' else b'#654321'
                svg.write_bytes(original[:match.start()] + replacement + original[match.end():])
                curate = content / 'assets/global/curation-20261112-further-r2.json'
                old_hash = hashlib.sha256(original).hexdigest(); new_hash = hashlib.sha256(svg.read_bytes()).hexdigest()
                raw = curate.read_bytes(); self.assertIn(old_hash.encode(), raw)
                curate.write_bytes(raw.replace(old_hash.encode(), new_hash.encode()))
                recipe = content / 'catalog/source.json'; raw_recipe = recipe.read_bytes()
                # The original curation digest must be pinned in the actual recipe.
                old_curate = hashlib.sha256(raw).hexdigest(); new_curate = hashlib.sha256(curate.read_bytes()).hexdigest()
                self.assertIn(old_curate.encode(), raw_recipe)
                recipe.write_bytes(raw_recipe.replace(old_curate.encode(), new_curate.encode()))
                catalog_b = build_catalog(content)
                second = publish(catalog_b, NOW+1)
                def rocket(files):
                    feed=json.loads(files['feed.json']); scene=json.loads(read_ref(feed['visualSelection'],files))
                    return scene['roles']['rocket']['descriptor']['sha256']
                self.assertNotEqual(rocket(first), rocket(second))
                # Restore exact source and pins before building generation 3.
                svg.write_bytes(original); curate.write_bytes(raw); recipe.write_bytes(raw_recipe)
                third = publish(build_catalog(content), NOW+2)
                self.assertEqual(rocket(first), rocket(third))
                self.assertEqual(pub.ledger['active']['generation'], 3)
                self.assertEqual(pub.ledger['selection_validated_utc'], NOW)
                self.assertEqual(pub.schedule.entries[0].record.source_validated_utc, NOW)
                head = pub.head
                with self.assertRaises(StateError):
                    pub.prepare(head, NOW+3, first, json.loads(first['feed.json'])['catalogDigest'], artifact_profile=PROFILE)
                self.assertEqual(pub.head, head)
                forged = dict(third); feed = json.loads(forged['feed.json'])
                feed['publisher'] = pub.publisher_envelope(NOW+3); feed['publisher']['selectionValidatedUtc'] = NOW+3
                forged['feed.json'] = canonical_bytes(feed); forged = with_text_transport(forged)
                with self.assertRaises(StateError):
                    pub.prepare(head, NOW+3, forged, feed['catalogDigest'], artifact_profile=PROFILE)
                self.assertEqual(pub.head, head)
            finally:
                store.close()

    def test_old_generation_and_faked_validation_are_refused(self):
        with tempfile.TemporaryDirectory(prefix='spacefox-rollback-negative-') as tmp:
            base = Path(tmp); remote = base / 'state.git'; source = base / 'source'; source.mkdir()
            subprocess.run(['git', 'init', '--bare', '-q', str(remote)], check=True)
            git(source, 'init', '-q'); git(source, 'config', 'user.name', 'Local test')
            git(source, 'config', 'user.email', 'local@example.invalid')
            git(source, 'commit', '--allow-empty', '-qm', 'source')
            code = git(source, 'rev-parse', 'HEAD'); git(source, 'push', '-q', str(remote), 'HEAD:refs/heads/main')
            store = GitState(str(remote))
            try:
                store.bootstrap(code); pub = Publisher(store, code); pub.reconcile(None)
                token = pub.reserve(pub.head, NOW, trigger='manual')
                pub.accept_source(pub.head, token, (normalize_launch(captured_starship(), NOW),), NOW, selection_validated_utc=NOW)
                first, digest = build_artifact(pub.schedule, build_catalog(ROOT), NOW, publisher=pub.publisher_envelope(NOW), root=ROOT)
                revision = pub.prepare(pub.head, NOW, first, digest, feed_publisher=pub.publisher_envelope(NOW), artifact_profile=PROFILE)
                self.assertEqual(pub.reconcile(revision), 'promoted'); head = pub.head
                with self.assertRaises(StateError):
                    pub.prepare(head, NOW+1, first, digest, artifact_profile=PROFILE)
                self.assertEqual(pub.head, head)
                forged = dict(first); feed = json.loads(first['feed.json'])
                feed['publisher'] = pub.publisher_envelope(NOW+1)
                feed['publisher']['selectionValidatedUtc'] = NOW+1
                forged['feed.json'] = canonical_bytes(feed); forged = with_text_transport(forged)
                with self.assertRaises(StateError):
                    pub.prepare(head, NOW+1, forged, digest, artifact_profile=PROFILE)
                self.assertEqual(pub.head, head)
                self.assertEqual(pub.ledger['selection_validated_utc'], NOW)
                # A real empty source observation can advance selection freshness
                # while leaving the omitted launch's own validation unchanged.
                token = pub.reserve(pub.head, NOW+2, trigger='manual')
                pub.accept_source(pub.head, token, (), NOW+2, selection_validated_utc=NOW+2)
                self.assertEqual(pub.schedule.entries[0].record.source_validated_utc, NOW)
                next_files, next_digest = build_artifact(pub.schedule, build_catalog(ROOT), NOW+2,
                    publisher=pub.publisher_envelope(NOW+2), root=ROOT)
                forged_record = dict(next_files); next_feed = json.loads(next_files['feed.json'])
                next_feed['launch']['source_validated_utc'] = NOW+1
                forged_record['feed.json'] = canonical_bytes(next_feed)
                forged_record = with_text_transport(forged_record)
                # It must pass packet validation, so the independent durable
                # schedule comparison—not an unrelated schema guard—rejects it.
                from tools.spacefox.native_motion import validate_artifact
                validate_artifact(forged_record)
                head = pub.head
                with self.assertRaisesRegex(StateError, 'selected facts disagree'):
                    pub.prepare(head, NOW+2, forged_record, next_digest, artifact_profile=PROFILE)
                self.assertEqual(pub.head, head)
                self.assertEqual(pub.schedule.entries[0].record.source_validated_utc, NOW)
            finally:
                store.close()
