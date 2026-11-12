"""R2 calendar-bound lifecycle review at the actual amendment boundary."""
from datetime import datetime, timedelta, timezone
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.spacefox.catalog import CatalogError, canonical_bytes
from tests.test_global_catalog import temporary_catalog, supplement, save_revision
from tests.test_global_content import lifecycle, URL


class GlobalContentReviewDateTest(unittest.TestCase):
    def test_future_lifecycle_review_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            before = source.read_bytes()
            future = (datetime.now(timezone.utc).date()+timedelta(days=1)).isoformat()
            value = supplement('r2-future-lifecycle-review')
            value['reviewedAt'] = future
            facts = lifecycle()
            facts['officialLifecycleReviewedAt'] = future
            value['updates'] = [{'identity': 'll2:configuration:164',
                                 'changes': facts, 'sources': [URL]}]
            with self.assertRaisesRegex(CatalogError, 'official lifecycle review cannot postdate its curation or UTC admission date'):
                amend_recipe(root, source, save_revision(root, value), 'r2.future.review')
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_today_lifecycle_review_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            value = supplement('r2-today-lifecycle-review')
            value['reviewedAt'] = datetime.now(timezone.utc).date().isoformat()
            facts = lifecycle()
            facts['officialLifecycleReviewedAt'] = value['reviewedAt']
            value['updates'] = [{'identity': 'll2:configuration:164',
                                 'changes': facts, 'sources': [URL]}]
            catalog = amend_recipe(root, source, save_revision(root, value), 'r2.today.review')
            row = catalog['dictionaries']['configurations']['ll2:configuration:164']
            self.assertEqual(row['facts']['officialLifecycleReviewedAt'], facts['officialLifecycleReviewedAt'])
            self.assertEqual(row['curationHistory'][-1]['sources'], [URL])
            self.assertNotIn('officialLifecycleReviewedAt', row['originalFacts'])
            self.assertEqual(canonical_bytes(row['curationHistory'][-1]['changes']), canonical_bytes(facts))

    def test_malformed_lifecycle_review_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp)
            source = root/'catalog/source.json'
            before = source.read_bytes()
            for number, malformed in enumerate(('2026-02-30', '20261112', '2026-11-12T00:00:00Z')):
                value = supplement('r2-malformed-review-'+str(number))
                facts = lifecycle()
                facts['officialLifecycleReviewedAt'] = malformed
                value['updates'] = [{'identity': 'll2:configuration:164',
                                     'changes': facts, 'sources': [URL]}]
                with self.subTest(malformed=malformed), self.assertRaises(CatalogError):
                    amend_recipe(root, source, save_revision(root, value), 'r2.malformed.review')
                self.assertEqual(source.read_bytes(), before)
                self.assertFalse(list((root/'catalog').glob('.recipe-*')))


if __name__ == '__main__':
    unittest.main()
