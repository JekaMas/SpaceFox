"""Read source-bound FR165 SDK observations; this does not launch a simulator."""
import hashlib
import json
import re
import unittest
from pathlib import Path
from tools.run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'openspec/changes/add-launch-reminders/evidence/native-reminder-tests'
INTEGRATED = ROOT / 'openspec/changes/spacefox-watchface/evidence/display04-integrated016/reminder'
NAMES = ('settingsPositive', 'cadencePositive', 'cadenceNegative', 'quietPositive',
         'quietNegative', 'identityPositive', 'identityNegative', 'schedulerPositive',
         'schedulerNegative', 'equivalencePositive', 'equivalenceNegative', 'sharedRegistration', 'snapshotWrites')

class ReminderTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        receipt = json.loads((INTEGRATED / 'binding.json').read_text())
        for name, expected in receipt['inputs'].items():
            actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
            if actual != expected:
                raise AssertionError('SDK observation source changed: ' + name)
        fixture = json.loads((ROOT / 'tests/fixtures/watch_refresh_cache/packets.json').read_text())
        if json.loads((EVIDENCE / 'peer-DisplayCatalog.json').read_text()) != fixture['catalogs']['initial'] or json.loads((EVIDENCE / 'peer-DisplayInitial.json').read_text()) != {'raw': fixture['packets']['initial']}:
            raise AssertionError('SDK lifecycle resources differ from retained cache fixture')
        source = (ROOT / 'watchface/reminder-tests/ReminderFixture.mc').read_text()
        captured = json.loads((ROOT / 'tests/fixtures/typed_operator/feed.json').read_text())
        captured['publisher']['generation'] += 1
        captured['publisher']['selectionValidatedUtc'] += 10
        captured['launch']['source_validated_utc'] += 10
        wire = json.dumps(captured, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
        literal = re.search(r'function reminderRawFixture\(\) \{return (.*);\}', source)
        if literal is None or json.loads(literal.group(1)) != wire:
            raise AssertionError('real-format source-only fixture differs')
        masked = json.loads(wire)
        for key in ('publisher', 'pollIntervalSeconds', 'timingState'):
            masked[key] = None
        for key in ('source_validated_utc', 'stale', 'rescheduled'):
            masked['launch'][key] = None
        independent = hashlib.sha256(json.dumps(masked, sort_keys=True, ensure_ascii=False,
                                                separators=(',', ':')).encode()).hexdigest()
        if independent not in source:
            raise AssertionError('independent semantic digest differs')
        raw = (INTEGRATED / 'native-final.log').read_text()
        if hashlib.sha256(raw.encode()).hexdigest() != receipt['logSha256']:
            raise AssertionError('SDK log changed')
        if 'BUILD SUCCESSFUL' not in (INTEGRATED / 'compile-final.log').read_text():
            raise AssertionError('SDK compile incomplete')
        result = parse_output(raw, receipt['rawExit'], NAMES)
        if result['status'] != 'passed':
            raise AssertionError('SDK framework table incomplete or contains an error')
        cls.result = result['observed_tests']

    def test_cadence_positive(self):
        self.assertEqual(self.result['settingsPositive'], 'PASS')
        self.assertEqual(self.result['snapshotWrites'], 'PASS')
        self.assertEqual(self.result['cadencePositive'], 'PASS')

    def test_cadence_negative(self):
        self.assertEqual(self.result['cadenceNegative'], 'PASS')

    def test_quiet_positive(self):
        self.assertEqual(self.result['quietPositive'], 'PASS')

    def test_quiet_negative(self):
        self.assertEqual(self.result['quietNegative'], 'PASS')

    def test_identity_positive(self):
        self.assertEqual(self.result['identityPositive'], 'PASS')
        self.assertEqual(self.result['equivalencePositive'], 'PASS')

    def test_identity_negative(self):
        self.assertEqual(self.result['identityNegative'], 'PASS')
        self.assertEqual(self.result['equivalenceNegative'], 'PASS')

    def test_scheduler_positive(self):
        self.assertEqual(self.result['schedulerPositive'], 'PASS')
        self.assertEqual(self.result['sharedRegistration'], 'PASS')

    def test_scheduler_negative(self):
        self.assertEqual(self.result['schedulerNegative'], 'PASS')
