"""Pinned hosted failure and bounded replacement; no provider or Pages calls."""
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import json
import tarfile

from tools.spacefox.cloud import (CloudError, delivery, delivery_files,
                                  preflight_delivery, MAX_DELIVERY_FILES)
from tools.spacefox.native_motion import validate_artifact
from tools.spacefox.publisher import MAX_ARTIFACT_BYTES, MAX_ARTIFACT_FILES

FIXTURE = Path(__file__).parent / 'fixtures/rollover017-hosted-state-9675e0f.tar.gz'
STATE = '9675e0f0e42297e2399ae55f106f31dad67856ff'


class HostedRolloverDelivery(TestCase):
    @classmethod
    def setUpClass(cls):
        with tarfile.open(FIXTURE, 'r:gz') as tar:
            data = {m.name: tar.extractfile(m).read() for m in tar.getmembers() if m.isfile()}
        cls.ledger = json.loads(data.pop('ledger.json'))
        cls.files = {}
        for gen in (48, 49):
            prefix = f'artifacts/{gen}/'
            cls.files[gen] = {k[len(prefix):]: v for k, v in data.items() if k.startswith(prefix)}
        cls.store = SimpleNamespace(_ledger_at=lambda _: cls.ledger)
        cls.pub = SimpleNamespace(ledger=cls.ledger, head=STATE, store=cls.store)

    def snapshot(self, store, state, generation):
        self.assertEqual(state, STATE)
        snap = next(s for s in (self.ledger['active'], self.ledger['pending'])
                    if s['generation'] == generation)
        files = self.files[generation]
        validate_artifact(files)
        return snap, files

    def test_captured_union_is_complete_and_within_bytes(self):
        self.assertEqual((MAX_ARTIFACT_FILES, MAX_DELIVERY_FILES, MAX_ARTIFACT_BYTES),
                         (256, 512, 1048576))
        with patch('tools.spacefox.cloud.snapshot_files', side_effect=self.snapshot):
            manifest = delivery(self.pub)
            result = delivery_files(self.pub, manifest)
            preflight_delivery(self.pub, self.files[49])
            self.assertEqual((len(result), sum(map(len, result.values()))), (274, 864544))
            self.assertEqual(result['feed.json'], self.files[49]['feed.json'])
            prior = set(self.files[48]) - {'feed.json', 'feed.json.txt'}
            self.assertTrue(prior <= result.keys())
            self.assertTrue(self.files[49].keys() <= result.keys())
            for name in prior - self.files[49].keys():
                self.assertEqual(result[name], self.files[48][name])
            incomplete = dict(manifest)
            del incomplete[next(name for name, row in manifest.items() if row['role'] == 'previous')]
            with self.assertRaisesRegex(CloudError, 'exact current/prior'):
                delivery_files(self.pub, incomplete)
        with self.assertRaisesRegex(CloudError, 'file bound'):
            delivery_files(None, {str(n): {} for n in range(513)})
        # 512 passes the count guard and is then rejected by entry validation;
        # this does not pretend 512 arbitrary names form valid snapshots.
        with self.assertRaisesRegex(CloudError, 'invalid durable delivery entry'):
            delivery_files(None, {str(n): {} for n in range(512)})

    def test_preflight_enforces_combined_byte_limit_before_commit(self):
        old = {'feed.json': b'o', 'old.bin': b'a' * 524288}
        pub = SimpleNamespace(ledger={'active': {'generation': 1}}, head=STATE, store=None)
        current = {'feed.json': b'n', 'new.bin': b'b' * 524288}
        with patch('tools.spacefox.cloud.snapshot_files', return_value=(None, old)):
            with self.assertRaisesRegex(CloudError, 'exceeds1MiB'):
                preflight_delivery(pub, current)
            current['new.bin'] = b'b' * 524287
            preflight_delivery(pub, current)

    def test_single_snapshot_file_bound_is_unchanged(self):
        with self.assertRaisesRegex(ValueError, 'complete artifact bound'):
            validate_artifact({f'{i}': b'' for i in range(257)})

    def test_preflight_failure_does_not_commit_pending_or_change_quota(self):
        from tests.test_schedule_producer_transport import local_authority, NOW, ROOT
        from tools.spacefox.catalog import build_catalog
        from tools.spacefox.native_motion import PROFILE, build_artifact
        with local_authority() as (pub, store, code):
            envelope = pub.publisher_envelope(NOW)
            files, digest = build_artifact(pub.schedule, build_catalog(ROOT), NOW,
                                           publisher=envelope, root=ROOT)
            revision = pub.prepare(pub.head, NOW, files, digest, feed_publisher=envelope,
                                   artifact_profile=PROFILE)
            pub.reconcile(revision)  # Local accepted active; no Pages interaction.
            envelope = pub.publisher_envelope(NOW + 1)
            files, digest = build_artifact(pub.schedule, build_catalog(ROOT), NOW + 1,
                                           publisher=envelope, root=ROOT)
            head, ledger = pub.head, pub.ledger
            # Substitute just the size of retained authenticated files, so the
            # real preflight and real pending-commit boundary are exercised.
            retained = {'protected.bin': {'sha256': 'a' * 64, 'bytes': 1048576}}
            with patch('tools.spacefox.cloud.retained_files', return_value=retained):
                with self.assertRaisesRegex(CloudError, 'exceeds1MiB'):
                    pub.prepare(head, NOW + 1, files, digest, feed_publisher=envelope,
                                artifact_profile=PROFILE)
            self.assertEqual((pub.head, pub.ledger), (head, ledger))
            self.assertEqual(store.load(), (head, ledger))
            pub.prepare(head, NOW + 1, files, digest, feed_publisher=envelope,
                        artifact_profile=PROFILE)
            self.assertIsNotNone(pub.ledger['pending'])

    def test_published_parent_cloud_remains_receipt_bound(self):
        import gzip
        import hashlib
        import tempfile
        from tools.native_rollover017_qualification import PARENT_CLOUD, parent_bytes, parent_input
        root = Path(__file__).resolve().parents[1]
        receipt = root / 'openspec/changes/spacefox-watchface/evidence/rollover017/published016-receipt.json.gz'
        with gzip.open(receipt, 'rt') as stream:
            expected = json.load(stream)['source_inputs_sha256']['tools/spacefox/cloud.py']
        self.assertNotEqual(hashlib.sha256((root / 'tools/spacefox/cloud.py').read_bytes()).hexdigest(), expected)
        original = parent_input(root, 'tools/spacefox/cloud.py', expected)
        self.assertEqual(hashlib.sha256(original).hexdigest(), expected)
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp)
            current = target / 'tools/spacefox/cloud.py'
            current.parent.mkdir(parents=True)
            current.write_bytes(b'changed host')
            fallback = target / PARENT_CLOUD
            fallback.parent.mkdir(parents=True)
            fallback.write_bytes(original + b'corrupt')
            with self.assertRaisesRegex(ValueError, 'published parent source differs'):
                parent_bytes(target, 'tools/spacefox/cloud.py', expected, {})
