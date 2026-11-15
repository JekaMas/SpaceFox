"""Host-only current feed authority at durable and loopback boundaries.

Uses the retained captured Starship and real publisher/renderer; service responses
are controlled locally. Does not establish hosted, device, or signed-code behavior.
"""
from copy import deepcopy
import hashlib
from pathlib import Path
import json
import unittest

from tests.test_autonomous_publisher_whole import AutonomousPublisherWholeTest, Service
from tests.test_current_motion_publisher import NOW
from tools.spacefox.catalog import canonical_bytes, loads_json
from tools.spacefox.cloud import CloudError, Site, delivery, delivery_files, snapshot_files
from tools.spacefox.native_motion import PROFILE, build_artifact, with_text_transport
from tools.spacefox.publisher import Publisher, StateError, validate_snapshot_artifact


class CurrentFeedAuthorityWholeTest(AutonomousPublisherWholeTest):
    def test_prepare_refuses_bad_profile_envelope_age_and_missing_closure_atomically(self):
        with self.authority() as (_, _, store, pub):
            self.accept(pub)
            files = self.candidate(pub)
            before = pub.head
            feed = json.loads(files['feed.json'])
            absent = dict(feed); absent.pop('publisher')
            old = deepcopy(feed); old['launch']['source_validated_utc'] -= 1
            purpose = deepcopy(feed); purpose['launch']['mission_purpose'] = None
            changed = []
            for name, doc in [('missing-envelope', absent), ('source-age', old), ('source-fact', purpose)]:
                logical = {p: b for p, b in files.items() if not p.endswith('.txt')}
                logical['feed.json'] = canonical_bytes(doc)
                candidate = with_text_transport(logical)
                if name != 'missing-envelope':
                    from tools.spacefox.native_motion import validate_artifact
                    validate_artifact(candidate)
                changed.append((name, candidate, PROFILE))
            missing = dict(files)
            selected = feed['visualSelection']['path']
            del missing[selected]
            changed.extend([('closure', missing, PROFILE), ('profile', files, None),
                            ('wrong-profile', files, 'other')])
            for name, candidate, profile in changed:
                with self.subTest(name=name), self.assertRaises(StateError):
                    pub.prepare(before, NOW, candidate, self.digest, artifact_profile=profile)
                reopened = Publisher(store, self.code)
                self.assertEqual(before, reopened.head)
                self.assertIsNone(reopened.ledger['pending'])
                self.assertEqual(NOW, reopened.ledger['selection_validated_utc'])
                self.assertEqual(1, len(reopened.ledger['requests']))
            revision = pub.prepare(before, NOW, files, self.digest, artifact_profile=PROFILE)
            self.assertEqual(1, revision.generation)
            self.assertEqual(files, Publisher(store, self.code).pending_files())

    def test_repinned_role_point_and_catalog_grammar_refused_before_persistence(self):
        from tools.spacefox.native_motion import _index
        with self.authority() as (_, _, store, pub):
            self.accept(pub)
            files = self.candidate(pub)
            feed = json.loads(files['feed.json'])
            scene_path = feed['visualSelection']['path']
            scene = json.loads(files[scene_path])

            def rewrite(target, mutate):
                rebuilt, memo = {}, {}
                def document(path):
                    if path in memo:
                        return memo[path]
                    raw = files[path]
                    if path.endswith('.json'):
                        row = walk(loads_json(raw))
                        if isinstance(row, dict) and row.get('type') == 'native-transfer':
                            row = _index(rebuilt, row['scene'])
                        if path == target:
                            mutate(row)
                        raw = canonical_bytes(row)
                    digest = hashlib.sha256(raw).hexdigest()
                    name = 'feed.json' if path == 'feed.json' else path.rsplit('/', 1)[0] + '/' + digest + Path(path).suffix
                    rebuilt[name] = raw
                    memo[path] = dict(path=name, sha256=digest, decodedBytes=len(raw))
                    return memo[path]
                def walk(row):
                    if isinstance(row, list):
                        return [walk(v) for v in row]
                    if not isinstance(row, dict):
                        return row
                    if set(row) == {'path', 'sha256', 'decodedBytes'}:
                        return document(row['path'])
                    row = {k: walk(v) for k, v in row.items()}
                    if 'catalogPath' in row:
                        pin = document(row['catalogPath'])
                        row.update(catalogPath=pin['path'], catalogDigest=pin['sha256'])
                    return row
                document('feed.json')
                return with_text_transport(rebuilt)

            self.assertEqual(files, rewrite(scene_path, lambda row: None))
            cases = [
                ('role', scene_path, lambda x: x['roles']['rocket'].update(entityId=x['operatorId'])),
                ('point', scene_path, lambda x: x.update(position=[999, 999])),
                ('catalog', feed['catalogPath'], lambda x: x.update(schemaVersion=True)),
                ('source-role', scene['sourceSelection']['path'],
                    lambda x: x['roles']['rocket'].update(entityId=x['operatorId'])),
            ]
            before = pub.head
            for name, target, mutate in cases:
                candidate = rewrite(target, mutate)
                with self.subTest(name=name), self.assertRaises(StateError):
                    pub.prepare(before, NOW, candidate, self.digest, artifact_profile=PROFILE)
                reopened = Publisher(store, self.code)
                self.assertEqual(before, reopened.head)
                self.assertIsNone(reopened.ledger['pending'])
            pub.prepare(before, NOW, files, self.digest, artifact_profile=PROFILE)
            self.assertEqual(files, Publisher(store, self.code).pending_files())

    def test_snapshot_instance_and_source_facts_bind_authenticated_namespace(self):
        with self.authority() as (_, _, store, pub):
            self.accept(pub)
            files, _ = self.prepare(pub)
            snap, raw = snapshot_files(store, pub.head, 1)
            self.assertEqual(files, raw)
            policy = pub.ledger['refresh_policy']
            instance = pub.ledger['instance_id']
            self.assertEqual(validate_snapshot_artifact(snap, raw, refresh_policy=policy,
                instance=instance, selection_validated_utc=NOW, require_selection_epoch=True)['publisher']['instance'], instance)
            with self.assertRaises(StateError):
                validate_snapshot_artifact(snap, raw, refresh_policy=policy, instance='f'*64,
                    selection_validated_utc=NOW, require_selection_epoch=True)
            with self.assertRaises(StateError):
                validate_snapshot_artifact(snap, raw, refresh_policy=policy, instance=instance,
                    selection_validated_utc=NOW-1, require_selection_epoch=True)
            changed = deepcopy(snap)
            changed['schedule']['entries'][0]['record']['source_validated_utc'] -= 1
            with self.assertRaises(StateError):
                validate_snapshot_artifact(changed, raw, refresh_policy=policy, instance=instance)
            self.assertEqual(files, Publisher(store, self.code).pending_files())

    def test_rehashed_foreign_instance_snapshot_refuses_cloud_and_reopen(self):
        from tools.spacefox.publisher import STATE_REF
        with self.authority() as (_, remote, store, pub):
            self.accept(pub)
            files, _ = self.prepare(pub)
            good = pub.head
            document = deepcopy(pub.ledger)
            logical = {p: b for p, b in files.items() if not p.endswith('.txt')}
            feed = json.loads(logical['feed.json'])
            feed['publisher']['instance'] = 'f' * 64 if pub.ledger['instance_id'] != 'f' * 64 else 'e' * 64
            logical['feed.json'] = canonical_bytes(feed)
            altered = with_text_transport(logical)
            # A complete self-consistent artifact is not the ledger's authority.
            from tools.spacefox.native_motion import validate_artifact
            validate_artifact(altered)
            snap = document['pending']
            snap['files'] = {p: dict(sha256=hashlib.sha256(b).hexdigest(), bytes=len(b)) for p, b in altered.items()}
            unsigned = {k: v for k, v in snap.items() if k != 'artifact_revision'}
            frozen = json.dumps(unsigned, ensure_ascii=False, sort_keys=True,
                                separators=(',', ':'), allow_nan=False).encode('utf-8')
            snap['artifact_revision'] = hashlib.sha256(frozen).hexdigest()
            bad = store._commit(document, good, {f'artifacts/1/{p}': b for p, b in altered.items()})
            with self.assertRaises((StateError, CloudError)):
                snapshot_files(store, bad, 1)
            store._git('push', f'--force-with-lease={STATE_REF}:{good}', str(remote), f'{bad}:{STATE_REF}')
            try:
                with self.assertRaises(StateError):
                    Publisher(store, self.code)
                self.assertEqual(bad, store._refs(STATE_REF)[STATE_REF])
            finally:
                store._git('push', f'--force-with-lease={STATE_REF}:{bad}', str(remote), f'{good}:{STATE_REF}')
            self.assertEqual(files, Publisher(store, self.code).pending_files())

    def test_exact_union_and_final_root_reread_for_current_and_recovery(self):
        with self.authority() as (_, _, store, pub), Service().serving() as service:
            first, first_revision = self.active(pub, service)
            catalog = deepcopy(self.catalog)
            catalog['catalogVersion'] += '.authority'
            second, digest = build_artifact(pub.schedule, catalog, NOW+1,
                publisher=pub.publisher_envelope(NOW+1), root=self.fixture)
            second_revision = pub.prepare(pub.head, NOW+1, second, digest, artifact_profile=PROFILE)
            manifest = delivery(pub)
            complete = delivery_files(pub, manifest)
            self.assertEqual(second['feed.json'], complete['feed.json'])
            self.assertTrue(all(complete[p] == b for p, b in first.items()
                                if p not in ('feed.json', 'feed.json.txt')))
            for remove in (next(p for p, m in manifest.items() if m['role'] == 'previous'),
                           next(p for p, m in manifest.items() if m['role'] == 'current' and p != 'feed.json')):
                incomplete = dict(manifest); del incomplete[remove]
                with self.subTest(path=remove), self.assertRaises(CloudError):
                    delivery_files(pub, incomplete)
            service.files = complete
            site = Site(service.url+'/site', local_http=True)
            service.root_reads = 0
            self.assertEqual(second_revision, site.observe(pub, manifest))
            self.assertEqual(2, service.root_reads)
            service.root_reads = 0; service.after_root = first['feed.json']
            with self.assertRaisesRegex(CloudError, 'changed during'):
                site.observe(pub, manifest)
            self.assertEqual(2, service.root_reads)
            service.after_root = None; service.root_reads = 0; service.files = first
            self.assertEqual(first_revision, site.observe(pub, manifest))
            self.assertEqual(2, service.root_reads)
            service.root_reads = 0; service.after_root = second['feed.json']
            with self.assertRaisesRegex(CloudError, 'changed during'):
                site.observe(pub, manifest)
            reopened = Publisher(store, self.code)
            self.assertEqual(first, snapshot_files(store, reopened.head, 1)[1])
            self.assertEqual(second, reopened.pending_files())
            self.assertEqual(NOW, reopened.ledger['selection_validated_utc'])
            self.assertEqual(1, len(reopened.ledger['requests']))


def load_tests(loader, standard_tests, pattern):
    return unittest.TestSuite(loader.loadTestsFromName(name, CurrentFeedAuthorityWholeTest)
        for name in CurrentFeedAuthorityWholeTest.__dict__ if name.startswith('test_'))
