"""Production-owned source construction preserves exact real output."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from tests.test_current_motion_publisher import captured_starship, NOW
from tools.spacefox import catalog, graphics, native_motion, visual_bridge
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import DEFAULT_POLICY, ScheduleState, merge_schedule

ROOT = Path(__file__).resolve().parents[1]


class RepositoryFactoryTest(unittest.TestCase):
    def test_owned_catalog_real_output_and_no_full_copy(self):
        operation = native_motion._RepositoryCatalogOperation(ROOT)
        state = merge_schedule(ScheduleState(), (normalize_launch(captured_starship(), NOW),), NOW)
        full_copies = []
        def observe(value):
            if isinstance(value, dict) and isinstance(value.get('dictionaries'), dict):
                rows = sum(len(v) for v in value['dictionaries'].values())
                if rows > 1000:
                    full_copies.append(rows)
            return copy.deepcopy(value)
        patches = [patch.object(module, 'deepcopy', side_effect=observe)
                   for module in (catalog, graphics, native_motion, visual_bridge)]
        for item in patches: item.start()
        try:
            files, digest = operation.build(state, None, NOW,
                publisher={'instance':'a'*64, 'generation':1, 'selectionValidatedUtc':NOW},
                policy=DEFAULT_POLICY, traversal=None)
        finally:
            for item in reversed(patches): item.stop()
        expected = json.loads((ROOT/'openspec/changes/spacefox-watchface/evidence/performance021/a/ELIGIBLE-BASELINE.json').read_text())
        self.assertEqual({p:hashlib.sha256(raw).hexdigest() for p,raw in files.items()}, expected['files'])
        self.assertEqual(sum(map(len,files.values())), expected['bytes'])
        self.assertEqual(digest, expected['catalog'])
        self.assertEqual(full_copies, [])
        self.assertTrue(operation.review)

    def test_cloud_owned_content_change_preserves_age_without_provider(self):
        from tests.test_schedule_producer_transport import local_authority
        from tools.cloud_feed import _prepare_content_from_source
        from tools.spacefox.native_motion import PROFILE, build_artifact, validate_artifact
        from tools.spacefox.publisher import LiveRevision, Publisher
        with local_authority() as (pub, store, code):
            record = normalize_launch(captured_starship(), NOW)
            token = pub.reserve(pub.head, NOW, trigger='manual')
            pub.accept_source(pub.head, token, (record,), NOW, selection_validated_utc=NOW)
            previous = catalog.build_catalog(ROOT)
            previous['source']['assetSeed']['description'] += ' '
            envelope = pub.publisher_envelope(NOW)
            files, digest = build_artifact(pub.schedule, previous, NOW, publisher=envelope, root=ROOT)
            revision = pub.prepare(pub.head, NOW, files, digest, feed_publisher=envelope, artifact_profile=PROFILE)
            self.assertEqual(pub.reconcile(revision), 'promoted')
            class ForbiddenProvider:
                def __getattr__(self, name):
                    raise AssertionError('content-only operation accessed provider: ' + name)
            result = _prepare_content_from_source(pub, ForbiddenProvider(), NOW+1, root=ROOT)
            self.assertEqual((result['result'], result['requests']), ('content_pending', 0))
            candidate = validate_artifact(pub.pending_files())
            self.assertEqual(candidate['launch']['launch_id'], 'll2:launch:' + record.launch_id.value)
            self.assertEqual(candidate['launch']['source_validated_utc'], NOW)
            self.assertEqual(candidate['publisher']['selectionValidatedUtc'], NOW)
            self.assertEqual(len(pub.ledger['requests']), 1)
            self.assertEqual(pub.reconcile(LiveRevision(**result['revision'])), 'promoted')
            reopened = Publisher(store, code)
            self.assertEqual(reopened.ledger['selection_validated_utc'], NOW)
