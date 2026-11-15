"""Current portable schedule boundaries and retained native countdown observation.

The native test is a source-bound receipt check, not a new SDK or device run.
"""
from copy import deepcopy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import unittest

from tests.test_current_motion_publisher import captured_starship, NOW
from tools.run_native_tests import parse_output
from tools.spacefox.provider import normalize_launch
from tools.spacefox.schedule import (LaunchStatus, ScheduleState, TimePrecision, Timing,
                                     advance_schedule, merge_schedule, select_next)

ROOT = Path(__file__).resolve().parents[1]
DIRECTED = ROOT / 'openspec/changes/spacefox-watchface/evidence/current-native-ui/directed'
NAMES = ('displayEventSequence', 'displayRealSiteMarker', 'displayCapturedZhuqueMarker',
         'displayAssetJobSequence', 'displayPairedInputs', 'displayBatchRetry', 'displayHighBeforeShow')


def selected_state():
    first = normalize_launch(captured_starship(), NOW)
    first = replace(first, timing=Timing(TimePrecision.EXACT, exact_utc=NOW))
    raw = deepcopy(captured_starship())
    raw['id'] = '00000000-0000-4000-8000-000000000033'
    second = replace(normalize_launch(raw, NOW), timing=Timing(TimePrecision.EXACT, exact_utc=NOW + 1800))
    return first, second, merge_schedule(ScheduleState(), (first, second), NOW)


def check_native_pair(log):
    for marker in ('PAIR utc=1794433377 target=1794609900 active=T- 49:02:03 low=T- 49:02:03 oracle=T- 49:02:03',
                   'PAIR utc=1794609841 target=1794609900 active=T- 00:00:59 low=T- 00:00:59 oracle=T- 00:00:59',
                   'PAIR utc=1794609900 target=1794609900 active=T+ 00:00:00 low=T+ 00:00:00 oracle=T+ 00:00:00',
                   'PAIR utc=1794609901 target=1794609900 active=T+ 00:00:01 low=T+ 00:00:01 oracle=T+ 00:00:01',
                   'PAIR utc=1794610801 target=1794609900 active=T+ 00:15:01 low=T+ 00:15:01 oracle=T+ 00:15:01'):
        if marker not in log:
            raise ValueError('missing exact paired countdown observation')


class CurrentTimingConvergenceTest(unittest.TestCase):
    def test_retention_and_postponement_positive(self):
        first, second, state = selected_state()
        for offset in (0, 59, 899, 900):
            self.assertEqual(select_next(advance_schedule(state, NOW + offset)).entry.record.launch_id, first.launch_id)
        self.assertEqual(select_next(advance_schedule(state, NOW + 901)).entry.record.launch_id, second.launch_id)
        postponed = replace(first, timing=Timing(TimePrecision.EXACT, exact_utc=NOW + 3600),
                            source_validated_utc=NOW + 1, source_updated_utc=NOW + 1, source_updated_iso=None)
        updated = merge_schedule(state, (postponed,), NOW + 1)
        self.assertEqual(select_next(updated).entry.record.launch_id, second.launch_id)
        self.assertTrue(next(e for e in updated.entries if e.record.launch_id == first.launch_id).rescheduled)

    def test_terminal_and_elapsed_negative(self):
        first, second, state = selected_state()
        self.assertNotEqual(first.status, LaunchStatus.COMPLETED)
        for status in (LaunchStatus.CANCELLED, LaunchStatus.COMPLETED):
            terminal = replace(first, status=status)
            mixed = merge_schedule(ScheduleState(), (terminal, second), NOW)
            self.assertEqual(select_next(mixed).entry.record.launch_id, second.launch_id)
        lone = merge_schedule(ScheduleState(), (first,), NOW)
        self.assertEqual(select_next(advance_schedule(lone, NOW + 7200)).entry.record.status, LaunchStatus.PENDING)

    def test_retained_native_countdown_pair_positive(self):
        receipt_bytes = (DIRECTED / 'receipt.json').read_bytes()
        log_bytes = (DIRECTED / 'native.log').read_bytes()
        self.assertEqual(hashlib.sha256(receipt_bytes).hexdigest(), '476da9bfc181dd593ab3467ad621b1f53e2f86d7838385d1150645c21bb41211')
        self.assertEqual(hashlib.sha256(log_bytes).hexdigest(), '888777a972c34b561d457ab5b45c102ebadcc5dc770566919b9713b5bb3691f7')
        receipt = json.loads(receipt_bytes)
        raw = log_bytes.decode()
        self.assertEqual(parse_output(raw, receipt['rawExit'], NAMES)['status'], 'passed')
        self.assertEqual(receipt['tests']['observed_tests']['displayPairedInputs'], 'PASS')
        check_native_pair(raw)
        # The exact source under this observation is reconstructed at its known
        # 0.1.10 UI revision; exact menu delta is reconstructed separately, plus version.
        for name, expected in receipt['inputHashes'].items():
            data = (ROOT / name).read_bytes()
            if name in ("watchface/source/SettingsMenu.mc", "watchface/source/SettingsMenuText.mc"):
                from tools.verify_current_ui_batch import historical_owner
                data = historical_owner(ROOT, name)
            if name == 'watchface/manifest.xml':
                self.assertEqual(data.count(b'version="0.1.12"'), 1, name)
                data = data.replace(b'version="0.1.12"', b'version="0.1.10"')
            elif name == 'watchface/source/generated/NativeVersion.mc':
                self.assertEqual(data.count(b'BUILD = "0.1.12"'), 1, name)
                self.assertEqual(data.count(b'ID = "07120ad9"'), 1, name)
                data = data.replace(b'BUILD = "0.1.12"', b'BUILD = "0.1.10"')
                # The build ID is version-derived; bind its earlier exact value.
                data = data.replace(b'ID = "07120ad9"', b'ID = "de5011f4"')
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected, name)

    def test_missing_zero_observation_negative(self):
        raw = (DIRECTED / 'native.log').read_text()
        check_native_pair(raw)
        for old, wrong in (('active=T+ 00:00:00', 'active=T+ 00:00:01'),
                           ('low=T- 00:00:59', 'low=T- 00:01:00'),
                           ('active=T- 49:02:03', 'active=T- 01:02:03')):
            with self.subTest(actual=old), self.assertRaisesRegex(ValueError, 'missing exact paired'):
                check_native_pair(raw.replace(old, wrong))
