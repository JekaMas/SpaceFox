#!/usr/bin/env python3
"""Validate the complete B1 native test table, including the SDK raw exit."""
import argparse
import json
from pathlib import Path

from run_native_tests import parse_output

EXPECTED = tuple('''
b1ClockWithUnavailableSettings b1ClockWithUnavailableHealth
b1ActualColdViewDefersCache b1ClockAfterDrawingFailure b1ClockAfterLoaderFailure
b1ClockBeforeLoader b1LowBeforeLoader b1ClockWithUnavailableRenderer
b1CapturedSuccessorTicksInFallback b1ColdAcquisition b1AdmissionFitnessLifecycle
b1RealDecodeTicksAndCancels b1MeasureCapturedCallbacks b1StagedLiveFeedAdmission
b1StagedSupersededToken b1StagedRestoreExactAndRecovery b1CompactingProjectionEquality b1PreparedSupersededToken b1PreparedFailureKeepsOldCommit b1GraphemeReleaseAndRebind b1LowHeapDefersOptionalDecode
'''.split())

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('log', type=Path)
parser.add_argument('raw_exit', type=int)
parser.add_argument('--prior-21', action='store_true', help='validate the retained pre-icon 21-case receipt')
args = parser.parse_args()
expected = EXPECTED if args.prior_21 else EXPECTED + ('b1ProviderIconBudget',)
result = parse_output(args.log.read_text(), args.raw_exit, expected)
print(json.dumps(result, indent=2))
raise SystemExit(0 if result['status'] == 'passed' else 1)
