"""Captured MIN refresh, source-age, and unchanged-target regressions."""
from dataclasses import replace
import unittest
from tests.test_current_motion_publisher import ROOT
from tools.spacefox.catalog import build_catalog
from tools.spacefox.schedule import (ScheduleState, RefreshPolicy, TimePrecision, Timing,
    cadence_seconds, merge_schedule, advance_schedule)

class MinuteRefreshTest(unittest.TestCase):
    def test_captured_minute_cadence_and_slept_through_stale(self):
        import gzip, hashlib, json
        from tools.spacefox.provider import normalize_launch
        fixture = ROOT / 'tests/fixtures/provider/current-starship/captured-page.json.gz'
        receipt = json.loads(fixture.with_name('receipt.json').read_bytes())
        compressed = fixture.read_bytes()
        self.assertEqual(hashlib.sha256(compressed).hexdigest(), receipt['compressedSha256'])
        raw = gzip.decompress(compressed)
        self.assertEqual(hashlib.sha256(raw).hexdigest(), receipt['rawPageSha256'])
        source = next(row for row in json.loads(raw)['results'] if row['id'] == receipt['launchId'])
        self.assertEqual(hashlib.sha256(json.dumps(source, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest(), receipt['recordSha256'])
        record = normalize_launch(source, 1794551192)
        self.assertEqual(record.timing.precision, TimePrecision.SOURCE_COARSE)
        self.assertEqual(record.timing.source_precision_id, 1)
        self.assertIsNone(record.timing.exact_utc)
        self.assertEqual(record.timing.nominal_utc, 1794609900)
        self.assertEqual([cadence_seconds(record, at) for at in
                          (1794602699, 1794602700, 1794611700, 1794611701)],
                         [3600, 3600, 3600, 3600])
        changed_context = replace(record, timing=replace(record.timing, window_end_utc=1794614460),
                                  source_validated_utc=1794551193,
                                  source_updated_utc=1794348407, source_updated_iso='2026-11-10T22:06:47Z')
        initial = merge_schedule(ScheduleState(), (record,), 1794551192)
        self.assertFalse(merge_schedule(initial, (changed_context,), 1794551193).entries[0].rescheduled)
        near = replace(record, source_validated_utc=1794602700)
        state = merge_schedule(ScheduleState(), (near,), 1794602700)
        from tools.spacefox.wire import project_schedule
        projected = project_schedule(state, build_catalog(ROOT), 1794602700,
                                     publisher={'instance':'a'*64, 'generation':1, 'selectionValidatedUtc':1794602700})
        self.assertEqual(projected['pollIntervalSeconds'], 3600)
        self.assertEqual(projected['timingState'], 'uncertain')
        self.assertIsNone(projected['launch']['timing']['exact_utc'])
        self.assertEqual(projected['launch']['timing']['nominal_utc'], 1794609900)
        self.assertFalse(advance_schedule(state, 1794605399).entries[0].stale)
        self.assertTrue(advance_schedule(state, 1794605400).entries[0].stale)
        slept = advance_schedule(state, 1794611701)
        self.assertTrue(slept.entries[0].stale)
        self.assertTrue(merge_schedule(slept, (near,), 1794611701).entries[0].stale)
        renewed = replace(near, source_validated_utc=1794611701)
        self.assertFalse(merge_schedule(slept, (renewed,), 1794611701).entries[0].stale)
        for timing in (Timing(TimePrecision.UNKNOWN),
                       Timing(TimePrecision.DATE, date_utc='2026-11-13'),
                       Timing(TimePrecision.WINDOW, window_start_utc=1794609900)):
            self.assertEqual(cadence_seconds(replace(record, timing=timing), 1794609900), 3600)
