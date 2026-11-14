"""Catalog-qualified presentation without changing accepted provider facts."""
from copy import deepcopy
from dataclasses import replace
import unittest

from tests.test_site_flag_protocol_working import SiteFlagWorkingTest
from tools.spacefox.catalog import loads_json
from tools.spacefox.native_motion import validate_artifact, with_text_transport
from tools.spacefox.visual_bridge import canonical_bytes, sha


def changed_catalog(files, mutate):
    files = dict(files)
    feed = loads_json(files['feed.json'])
    catalog = loads_json(files.pop(feed['catalogPath']))
    mutate(catalog)
    raw = canonical_bytes(catalog)
    feed['catalogDigest'] = sha(raw)
    feed['catalogPath'] = 'wire3/catalogs/' + feed['catalogDigest'] + '.json'
    files[feed['catalogPath']] = raw
    files['feed.json'] = canonical_bytes(feed)
    return with_text_transport(files) if any(name.endswith('.txt') for name in files) else files


class TypedOperatorPresentationTest(unittest.TestCase):
    setUpClass = classmethod(SiteFlagWorkingTest.setUpClass.__func__)
    build = SiteFlagWorkingTest.build
    def test_source_bound_abbreviation(self):
        record = replace(self.record, operator_abbrev=None)
        files, feed, scene = self.build(record)
        operator = feed['launch']['operator_id']
        source = loads_json(files[scene['origins']['operator']['sourceRecord']['path']])
        catalog = loads_json(files[feed['catalogPath']])
        abbreviation = source['owner']['facts']['abbrev']
        self.assertEqual(catalog['entries'][operator]['abbrev'], abbreviation)
        self.assertNotIn('operator_abbrev', feed['launch'])
        self.assertEqual(feed['launch']['operator_name'], record.operator_name)
        self.assertEqual(feed['launch']['source_validated_utc'], record.source_validated_utc)
        self.assertLessEqual(len(files['feed.json']), 8192)
        self.assertLessEqual(sum(map(len, files.values())), 1048576)
    def test_unqualified_abbreviation_rejection(self):
        record = replace(self.record, operator_abbrev=None)
        files, feed, scene = self.build(record)
        operator = feed['launch']['operator_id']
        source = loads_json(files[scene['origins']['operator']['sourceRecord']['path']])
        abbreviation = source['owner']['facts']['abbrev']
        # A producer lacking this optional projection remains valid and displays
        # the source name; wrong facts or a different identity cannot borrow it.
        absent = changed_catalog(files, lambda c: c['entries'][operator].pop('abbrev'))
        validate_artifact(absent)
        wrong = changed_catalog(files, lambda c: c['entries'][operator].__setitem__('abbrev', 'wrong'))
        with self.assertRaises(ValueError): validate_artifact(wrong)
        def move(c):
            c['entries'][operator].pop('abbrev')
            c['entries'][feed['launch']['configuration_id']]['abbrev'] = abbreviation
        with self.assertRaises(ValueError): validate_artifact(changed_catalog(files, move))
        corrupted = dict(files)
        corrupted[scene['origins']['operator']['sourceRecord']['path']] += b' '
        with self.assertRaises(ValueError): validate_artifact(corrupted)
        missing = dict(files)
        del missing[scene['origins']['operator']['sourceRecord']['path']]
        with self.assertRaises(ValueError): validate_artifact(missing)
        wrong_digest = dict(files)
        altered_feed = deepcopy(feed)
        altered_feed['catalogSourceDigest'] = '0' * 64
        wrong_digest['feed.json'] = canonical_bytes(altered_feed)
        with self.assertRaises(ValueError): validate_artifact(wrong_digest)
