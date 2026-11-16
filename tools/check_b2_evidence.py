#!/usr/bin/env python3
"""Check named completed SDK tables; does not launch SDK or prove hardware."""
import sys
from pathlib import Path
from tools.run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'openspec/changes/restore-fr165-runtime-guarantees/evidence'
CASES = {'b2ArithmeticAndRetention': 'b2-arithmetic.log',
         'b2AdmittedFactsWithoutArt': 'b2-facts.log',
         'b2FailedAndInterruptedReplacement': 'b2-recovery.log',
         'b2CapturedHourAndMissingPoint': 'b2-hour.log',
         'b2RescheduleAndNewSelection': 'b2-replacement.log',
         'b2LowUnmatchedPoint': 'b2-peer-low.log',
         'b2SourcedAscentRetention': 'b2-sourced-ascent.log',
         'b2CrossVmSeedInterrupted': 'b2-crossvm-seed.log',
         'b2CrossVmObserveRestored': 'b2-crossvm-observe.log',
         'b1CapturedSuccessorTicksInFallback': 'b2-b1-minute.log',
         'b1RealDecodeTicksAndCancels': 'b2-b1-decode.log',
         'b1LowHeapDefersOptionalDecode': 'b2-b1-low-heap.log',
         'b1ShortWakeResume': 'b2-b1-wake.log'}

def main():
    names = sys.argv[1:] or list(CASES)
    for name in names:
        if name not in CASES or parse_output((BASE / CASES[name]).read_text(), 1, (name,))['status'] != 'passed':
            raise SystemExit('SDK receipt incomplete: ' + name)
        print(name)

if __name__ == '__main__':
    main()
