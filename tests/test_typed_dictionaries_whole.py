"""Current typed catalog and selected schema-3 projection, using captured records."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from tests.test_current_motion_publisher import NOW, captured_starship
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes, dependency_closure, loads_json
from tools.spacefox.native_motion import build_artifact, native_transport_paths, validate_artifact
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, merge_schedule

ROOT = Path(__file__).resolve().parents[1]


class TypedDictionariesWholeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)
        record = normalize_launch(captured_starship(), NOW)
        cls.state = merge_schedule(ScheduleState(), (record,), NOW)
        cls.publisher = {'instance': 'a' * 64, 'generation': 1, 'selectionValidatedUtc': NOW}
        cls.files, _ = build_artifact(cls.state, cls.catalog, NOW, publisher=cls.publisher, root=ROOT)

    def test_shared_actual_entities_positive(self):
        corpus = json.loads((ROOT/'corpus/real-schedule-20261113/display-corpus.json').read_bytes())
        launches = {row[0]: row for row in corpus['launches']}
        ids = ['e4200e5c-2726-43f2-8439-36bd1be59821', '56db9abd-41b8-41a3-9d6d-88e52460682b']
        self.assertEqual([launches[i][2] for i in ids], [[164, 121, 80, 2]] * 2)
        roots = ['ll2:configuration:164', 'll2:organization:121', 'll2:site:80', 'll2:country:2']
        individual = [dependency_closure(self.catalog, [f'll2:{kind}:{number}' for kind, number in zip(('configuration', 'organization', 'site', 'country'), launches[i][2])], expected_revision=self.catalog['catalogVersion']) for i in ids]
        selected = dependency_closure(self.catalog, roots * 2, expected_revision=self.catalog['catalogVersion'])
        self.assertEqual(selected['roots'], sorted(roots))
        for table, identity in zip(('configurations', 'organizations', 'sites', 'countries'), roots):
            self.assertEqual(selected['dictionaries'][table][identity], self.catalog['dictionaries'][table][identity])
            self.assertEqual(list(selected['dictionaries'][table]).count(identity), 1)
            digest = hashlib.sha256(canonical_bytes(selected['dictionaries'][table][identity])).hexdigest()
            self.assertEqual([hashlib.sha256(canonical_bytes(view['dictionaries'][table][identity])).hexdigest() for view in individual], [digest, digest])
        feed = validate_artifact(self.files)
        self.assertEqual((feed['schemaVersion'], feed['rendererProfile']), (3, 'SFR1M'))
        wire = json.loads(self.files[feed['catalogPath']])
        self.assertEqual(wire['catalogVersion'], self.catalog['catalogVersion'])
        self.assertEqual(wire['projection'], 'selected-display-motion-v3')
        self.assertEqual(set(wire['entries']), {'ll2:configuration:522', 'll2:organization:121', 'll2:site:235', 'll2:country:2'})
        self.assertEqual(wire['entries']['ll2:configuration:522']['name'], 'Starship V3')
        self.assertEqual(wire['entries']['ll2:organization:121']['name'], 'SpaceX')
        self.assertEqual(wire['entries']['ll2:site:235']['position'], {
            'encoding': 'decimal-text-v1', 'latitude': '25.99677', 'longitude': '-97.15799',
            'units': 'degrees', 'qualification': 'unverified-reference'})
        scene = loads_json(self.files[feed['visualSelection']['path']])
        for role, table in (('model', 'configurations'), ('operator', 'organizations')):
            binding = scene['origins'][role]
            source = loads_json(self.files[binding['sourceRecord']['path']])
            self.assertEqual(source['owner'], self.catalog['dictionaries'][table][binding['ownerId']])
            self.assertTrue(source['owner']['provenance'])
        site_source = loads_json(self.files[scene['siteCountrySource']['path']])
        self.assertEqual(site_source['catalogSelection']['dictionaries']['sites']['ll2:site:235'],
                         self.catalog['dictionaries']['sites']['ll2:site:235'])
        self.assertLessEqual(len(native_transport_paths(self.files)), 43)
        self.assertTrue(all(not path.startswith('sources/') for path in native_transport_paths(self.files)))

    def test_shared_identity_negative(self):
        tables = self.catalog['dictionaries']
        self.assertEqual(tables['countries']['ll2:country:1']['kind'], 'country')
        self.assertEqual(tables['organizations']['ll2:organization:1']['kind'], 'organization')
        self.assertNotEqual(tables['countries']['ll2:country:1'], tables['organizations']['ll2:organization:1'])
        self.assertEqual(tables['configurations']['ll2:configuration:121']['kind'], 'configuration')
        self.assertEqual(tables['organizations']['ll2:organization:121']['kind'], 'organization')
        self.assertNotEqual(tables['configurations']['ll2:configuration:121']['facts'], tables['organizations']['ll2:organization:121']['facts'])
        for roots, revision in ((['ll2:configuration:121'], 'unsupported-revision'), (['ll2:site:999999999'], self.catalog['catalogVersion'])):
            with self.subTest(roots=roots, revision=revision), self.assertRaises(CatalogError):
                dependency_closure(self.catalog, roots, expected_revision=revision)

    def test_reordered_dictionaries_positive(self):
        reordered = copy.deepcopy(self.catalog)
        reordered['dictionaries'] = {k: dict(reversed(list(v.items()))) for k, v in reversed(list(reordered['dictionaries'].items()))}
        self.assertEqual(canonical_bytes(reordered), canonical_bytes(self.catalog))
        roots = ['ll2:configuration:164', 'll2:organization:121', 'll2:site:80', 'll2:country:2']
        a = dependency_closure(self.catalog, roots, expected_revision=self.catalog['catalogVersion'])
        b = dependency_closure(reordered, list(reversed(roots)), expected_revision=self.catalog['catalogVersion'])
        self.assertEqual(canonical_bytes(a), canonical_bytes(b))
        other, _ = build_artifact(self.state, reordered, NOW, publisher=self.publisher, root=ROOT)
        self.assertEqual(other, self.files)
        self.assertEqual(validate_artifact(other)['launch'], validate_artifact(self.files)['launch'])

    def test_unsupported_schema_negative(self):
        accepted = copy.deepcopy(self.files)
        candidate = dict(self.files)
        feed = json.loads(candidate['feed.json'])
        feed['schemaVersion'] = 4
        candidate['feed.json'] = canonical_bytes(feed)
        candidate['feed.json.txt'] = candidate['feed.json']
        with self.assertRaises(ValueError):
            validate_artifact(candidate)
        self.assertEqual(self.files, accepted)
        self.assertEqual(validate_artifact(self.files)['schemaVersion'], 3)
