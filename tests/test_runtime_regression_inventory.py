"""Portable inventory/parser controls; these do not run native code."""
import re
import unittest
from pathlib import Path
from tools.run_runtime_regressions import SELECTORS, PROFILES, parse_runtime_output
from tools.run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]

class RuntimeRegressionInventory(unittest.TestCase):
    def test_exact_selectors_exist_once_in_compiled_runtime_sources(self):
        names = ('stm-property-tests', 'activity-menu-tests', 'health-incident-tests', 'countdown-tests', 'physical-six-tests')
        source = '\n'.join(p.read_text() for name in names for p in (ROOT / 'watchface' / name).glob('*.mc'))
        self.assertEqual(PROFILES, ('fr165', 'fr165m'))
        self.assertEqual(len(SELECTORS), len(set(SELECTORS)))
        self.assertEqual(set(SELECTORS), {
            'verifiedRocketDecode', 'incidentFreshHistory', 'incidentHistoryPolicy', 'incidentCustomDuplicateOrdering',
            'incidentFreshCacheTransientFailure', 'incidentGeneratedHistory', 'incidentFirstPaintExpiry',
            'physicalHealthRearmRegressionBatch', 'menuAffectedBatch', 'menuPeerControls', 'menuCadenceFrames',
            'countdownAffectedBatch', 'generatedViewLifecycle', 'generatedFitnessOwners',
            'foregroundArtTimerBudget', 'cadenceNoPeriodicTimers', 'coldLowAcquiresOneFieldSnapshot',
            'generatedForegroundCadence', 'anchoredModelFrame',
        })
        for selector in SELECTORS:
            self.assertEqual(len(re.findall(r'(?m)^.*\(:test(?:,|\)).*\bfunction\s+'+re.escape(selector)+r'\s*\(', source)), 1, selector)

    def test_runner_rejects_missing_and_late_failure(self):
        raw = 'Executing test one...\nPASS\n===\nRESULTS\nTest: Status:\none PASS\nRan 1 test\nPASSED (passed=1, failed=0, errors=0)\n'
        self.assertEqual(parse_output(raw, 1, ('one',))['status'], 'passed')
        self.assertEqual(parse_output(raw, 1, ('one','two'))['status'], 'failed')
        self.assertEqual(parse_output(raw + 'ERROR\n', 1, ('one',))['status'], 'failed')
        observed = raw.replace('PASS\n===', 'SF_VIEW mode=HIGH pending=false\nPASS\n===')
        self.assertEqual(parse_runtime_output(observed, 1, 'one')['status'], 'passed')
        self.assertEqual(parse_runtime_output(observed.replace('pending=false', 'pending=unexpected'), 1, 'one')['status'], 'failed')
        self.assertEqual(parse_runtime_output(observed + 'ERROR\n', 1, 'one')['status'], 'failed')
        self.assertEqual(parse_output('', 124, ('one',))['status'], 'failed')

if __name__ == '__main__': unittest.main()
