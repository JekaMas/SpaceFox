#!/usr/bin/env python3
"""Strictly parse retained B3 SDK tables; does not launch SDK or prove hardware."""
import sys
from pathlib import Path
from tools.run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'openspec/changes/restore-fr165-runtime-guarantees/evidence/b3-023'
CASES = {'b3QueueAndRollover', 'b3AdmissionAndUnknown', 'b3QuietProvider',
         'b3OrdinaryReopen', 'b3RescheduleAndQuiet',
         'b1LowHeapDefersOptionalDecode', 'b1ShortWakeResume'}

def main():
    for name in sys.argv[1:] or sorted(CASES):
        if name not in CASES or parse_output((BASE / (name + '.log')).read_text(), 1, (name,))['status'] != 'passed':
            raise SystemExit('SDK receipt incomplete: ' + name)
        print(name)

if __name__ == '__main__':
    main()
