"""Independent creation/history discriminators at actual catalog boundaries."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes, loads_json
from tests.test_global_catalog import temporary_catalog, supplement, save_revision
from tests.test_global_content import lifecycle, URL

ROOT = Path(__file__).resolve().parents[1]


class GlobalContentCreationR3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)

    def addition(self, token, *, collection='configurations'):
        identity = 'spacefox:'+{'configurations': 'configuration', 'organizations': 'organization',
                               'sites': 'site', 'countries': 'country'}[collection]+':'+token
        source = {'configurations': 'spacefox:configuration:miura9',
                  'organizations': 'll2:organization:183', 'sites': 'll2:site:65',
                  'countries': 'll2:country:17'}[collection]
        row = self.catalog['dictionaries'][collection][source]
        facts = copy.deepcopy(row['facts'])
        facts.update(sourceId=token, name='Literal specifically identified '+token, sourceUrl=URL)
        if collection == 'configurations':
            facts.update(fullName=facts['name'])
        if collection == 'countries':
            facts.update(alpha2='ZX', alpha3='ZXX', jurisdictionKind='unknown')
        return {'identity': identity, 'facts': facts, 'references': copy.deepcopy(row['references'])}

    def build_revision(self, root, value):
        path = save_revision(root, value)
        recipe = loads_json((root/'catalog/source.json').read_bytes())
        recipe['curations'].append({'path': path.name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        candidate = root/'catalog/candidate-source.json'
        candidate.write_bytes(canonical_bytes(recipe))
        return build_catalog(root, candidate)

    def test_future_creation_amendment_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            before = source.read_bytes()
            value = supplement('r3-future-creation')
            future = (datetime.now(timezone.utc).date()+timedelta(days=1)).isoformat()
            value['reviewedAt'] = future
            addition = self.addition('r3-future-creation')
            addition['facts'].update(lifecycle(), officialLifecycleReviewedAt=future)
            value['additions'] = [addition]
            with self.assertRaisesRegex(CatalogError, 'official lifecycle review cannot postdate'):
                amend_recipe(root, source, save_revision(root, value), 'r3.future.creation')
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_typed_creation_matrix_negative(self):
        # The expected outcomes are literal contract violations; no production
        # function supplies the oracle. Replay uses real pinned input copies.
        cases = [
            ('boolean-state', 'configurations', {'officialLifecycle': True}),
            ('invalid-state', 'configurations', {'officialLifecycle': 'imagined'}),
            ('malformed-date', 'configurations', {'officialLifecycleReviewedAt': '20261112'}),
            ('after-curation', 'configurations', {'officialLifecycleReviewedAt': '2026-11-12'}),
            ('unlisted-source', 'configurations', {'officialLifecycleSource': URL+'/unlisted'}),
            ('wrong-organization', 'organizations', {}),
            ('wrong-site', 'sites', {}),
            ('wrong-country', 'countries', {}),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            before = (root/'catalog/source.json').read_bytes()
            for name, collection, patch in cases:
                value = supplement('r3-'+name)
                addition = self.addition('r3-'+name, collection=collection)
                addition['facts'].update(lifecycle(), **patch)
                if name == 'after-curation':
                    value['reviewedAt'] = '2026-11-11'
                value['additions'] = [addition]
                with self.subTest(name=name), self.assertRaises(CatalogError):
                    self.build_revision(root, value)
                self.assertEqual((root/'catalog/source.json').read_bytes(), before)

    def test_incomplete_new_creation_amendment_negative(self):
        # Old two-field primary source facts remain readable, but a new
        # amendment cannot opt out of typed review by omitting fields.
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            before = source.read_bytes()
            for name, fields in [('one', {'officialLifecycle': 'operating'}),
                                 ('legacy-style', {'officialLifecycle': 'operating-listed',
                                                   'officialLifecycleSource': URL})]:
                value = supplement('r3-incomplete-'+name)
                addition = self.addition('r3-incomplete-'+name)
                for field in list(addition['facts']):
                    if field.startswith('officialLifecycle'):
                        del addition['facts'][field]
                addition['facts'].update(fields)
                value['additions'] = [addition]
                with self.subTest(name=name), self.assertRaises(CatalogError):
                    amend_recipe(root, source, save_revision(root, value), 'r3.incomplete.creation')
                self.assertEqual(source.read_bytes(), before)
                self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_creation_unknown_and_known_corrections_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            value = supplement('r3-valid-creation')
            today = datetime.now(timezone.utc).date().isoformat()
            value['reviewedAt'] = today
            model = self.addition('r3-valid-model')
            model['facts'].update(lifecycle(), officialLifecycleReviewedAt=today)
            country = self.addition('r3-identified-jurisdiction', collection='countries')
            value['additions'] = [model, country]
            first = amend_recipe(root, source, save_revision(root, value, 'first.json'), 'r3.creation.valid')
            self.assertEqual(first['dictionaries']['configurations'][model['identity']]['facts'], model['facts'])
            self.assertEqual(first['dictionaries']['countries'][country['identity']]['jurisdictionKind'], 'unknown')
            value = supplement('r3-ordinary-corrections')
            value['updates'] = [
                {'identity': country['identity'], 'changes': {'name': 'Literal specific jurisdiction correction',
                                                             'alpha2': 'ZY', 'alpha3': 'ZYY'}, 'sources': [URL]},
                {'identity': 'll2:country:28', 'changes': {'name': 'Japan literal correction'}, 'sources': [URL]},
                {'identity': 'll2:organization:37', 'changes': {'name': 'JAXA literal correction'}, 'sources': [URL]},
                {'identity': 'll2:configuration:182', 'changes': {'name': 'Atlas V literal correction',
                                                               'placeholder': False}, 'sources': [URL]},
            ]
            second = amend_recipe(root, source, save_revision(root, value, 'second.json'), 'r3.ordinary.valid')
            row = second['dictionaries']['countries'][country['identity']]
            self.assertEqual(row['jurisdictionKind'], 'unknown')
            self.assertIsNone(row['references']['mark'])
            self.assertEqual(row['originalFacts'], country['facts'])
            value = supplement('r3-reviewed-specific-jurisdiction')
            value['updates'] = [{'identity': country['identity'], 'changes': {'jurisdictionKind': 'country'},
                                 'sources': [URL]}]
            for collection, identity, asset_id, field in [
                    ('companies', 'll2:organization:37', 'content-r1-operator-37', 'currentPackBadgeId'),
                    ('models', 'll2:configuration:52', 'content-r1-vehicle-minotaur-iv', 'currentPackAssetId')]:
                original = self.catalog['dictionaries']['assets']['spacefox:asset:'+asset_id]
                facts = copy.deepcopy(original['facts'])
                facts.update(id='r3-valid-'+collection, file=original['content']['path'],
                             originCode='ZY', originSources=[URL])
                value['assets'].append({'collection': collection, 'facts': facts})
                value['updates'].append({'identity': identity, 'changes': {field: facts['id']}, 'sources': [URL]})
            third = amend_recipe(root, source, save_revision(root, value, 'third.json'), 'r3.reviewed.valid')
            self.assertEqual(third['dictionaries']['countries'][country['identity']]['jurisdictionKind'], 'country')
            for collection, identity in [('organizations', 'll2:organization:37'),
                                         ('configurations', 'll2:configuration:52')]:
                self.assertEqual(third['dictionaries'][collection][identity]['references']['origin'], country['identity'])
            for collection, identity in [('countries', 'll2:country:28'), ('organizations', 'll2:organization:37'),
                                         ('configurations', 'll2:configuration:182')]:
                row = third['dictionaries'][collection][identity]
                old = self.catalog['dictionaries'][collection][identity]
                self.assertEqual(canonical_bytes(row['originalFacts']), canonical_bytes(old.get('originalFacts', old['facts'])))
            for token in ('s310', 's520', 'ss520'):
                identity = 'spacefox:configuration:'+token
                self.assertEqual(third['dictionaries']['configurations'][identity],
                                 self.catalog['dictionaries']['configurations'][identity])


if __name__ == '__main__':
    unittest.main()
