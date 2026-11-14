"""Focused working checks for selected site flag and additive source metadata.

This is not the finite global matrix or native qualification receipt.
"""
from dataclasses import replace
from copy import deepcopy
from decimal import Decimal
import unittest

from tests import test_current_motion_publisher as captured
from tools.spacefox.catalog import build_catalog, loads_json
from tools.spacefox.native_motion import build_artifact, validate_artifact
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import ScheduleState, merge_schedule, StableId, IdKind
from tools.spacefox.bridge_map import build_map


class SiteFlagWorkingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(captured.ROOT)
        cls.record = normalize_launch(captured.captured_starship(), captured.NOW)

    def build(self, record):
        state = merge_schedule(ScheduleState(), (record,), captured.NOW)
        files, _ = build_artifact(state, self.catalog, captured.NOW,
            publisher=dict(instance='a'*64, generation=1, selectionValidatedUtc=captured.NOW),
            root=captured.ROOT)
        feed = validate_artifact(files)
        return files, feed, loads_json(files[feed['visualSelection']['path']])

    def test_selected_country_and_mismatch(self):
        files, feed, scene = self.build(self.record)
        self.assertEqual(set(scene['roles']), {'map', 'rocket', 'siteCountry'})
        self.assertEqual(scene['roles']['siteCountry']['entityId'], 'll2:country:2')
        transfer = loads_json(files[feed['nativeTransfer']['path']])
        indexed = {row[1] for row in transfer['objects']}
        self.assertIn(scene['roles']['siteCountry']['descriptor']['sha256'], indexed)
        altered = replace(self.record, country_id=StableId(IdKind.COUNTRY, 'll2', '28'))
        _, _, mismatch = self.build(altered)
        self.assertIsNone(mismatch['roles']['siteCountry'])
        _, _, wrong_code = self.build(replace(self.record, country_code='JP'))
        self.assertIsNone(wrong_code['roles']['siteCountry'])

    def test_source_abbreviation_addition_retains_age(self):
        old = replace(self.record, operator_abbrev=None)
        initial = merge_schedule(ScheduleState(), (old,), captured.NOW)
        updated = merge_schedule(initial, (self.record,), captured.NOW)
        entry = updated.entries[0]
        self.assertEqual(entry.record.operator_abbrev, 'SpX')
        self.assertEqual(entry.record.source_validated_utc, old.source_validated_utc)
        self.assertFalse(entry.rescheduled)

    def test_corrected_site_rebuilds_the_projected_point(self):
        identity='ll2:site:29'
        original=deepcopy(self.catalog)
        corrected=deepcopy(original)
        site=corrected['dictionaries']['sites'][identity]
        # A technical coordinate correction of a real catalog record, not a
        # statement that the corrected coordinate is an actual launch pad.
        corrected_latitude=site['facts']['latitude']+Decimal('0.01')
        original_longitude=site['facts']['longitude']
        site['facts']['latitude']=corrected_latitude
        site['position']={'latitude':corrected_latitude,'longitude':original_longitude,
                          'units':'degrees','qualification':'unverified-reference'}
        files1={};files2={}
        ref1=build_map(captured.ROOT,original,identity,files1)
        ref2=build_map(captured.ROOT,corrected,identity,files2)
        first=loads_json(files1[ref1['path']]);second=loads_json(files2[ref2['path']])
        self.assertNotEqual(first['center'],second['center'])
        self.assertEqual(second['center'],[str(corrected_latitude),str(original_longitude)])
        self.assertNotEqual(first['definitionSha256'],second['definitionSha256'])
        self.assertEqual(first['marker']['anchor'],[335,165])
        self.assertEqual(second['marker']['anchor'],[335,165])
