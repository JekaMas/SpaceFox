"""Independent checks of selected-operator presentation boundaries."""
from dataclasses import replace
import unittest

from tests import test_site_flag_protocol_working as fixture
from tests.test_typed_operator_presentation import changed_catalog
from tools.spacefox.catalog import loads_json
from tools.spacefox.native_motion import validate_artifact
from tools.spacefox.schedule import IdKind, StableId


class TypedOperatorIndependentReview(unittest.TestCase):
    setUpClass = classmethod(fixture.SiteFlagWorkingTest.setUpClass.__func__)
    build = fixture.SiteFlagWorkingTest.build

    def test_provider_caption_is_preserved_and_catalog_caption_refused(self):
        files, feed, _ = self.build(self.record)
        operator = feed['launch']['operator_id']
        self.assertEqual(feed['launch']['operator_abbrev'], 'SpX')
        catalog = loads_json(files[feed['catalogPath']])
        self.assertNotIn('abbrev', catalog['entries'][operator])
        edited = changed_catalog(files, lambda c: c['entries'][operator].__setitem__('abbrev', 'SpX'))
        with self.assertRaises(ValueError):
            validate_artifact(edited)

    def test_missing_operator_does_not_borrow_caption(self):
        record = replace(self.record, operator_id=StableId(IdKind.ORGANIZATION, 'll2', '999999999'),
                         operator_abbrev=None, operator_name=None)
        files, feed, scene = self.build(record)
        catalog = loads_json(files[feed['catalogPath']])
        self.assertEqual(feed['launch']['operator_id'], 'll2:organization:999999999')
        self.assertIn(feed['launch']['operator_id'], catalog['unresolved'])
        source = loads_json(files[scene['origins']['operator']['sourceRecord']['path']])
        self.assertIsNone(source['owner'])
        self.assertFalse(any('abbrev' in row for row in catalog['entries'].values()))


if __name__ == '__main__':
    unittest.main()
