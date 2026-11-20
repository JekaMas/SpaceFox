#!/usr/bin/env python3
"""Run the checked-in production Monkey C incident and STM regression suite.

Requires the pinned SDK, external test key and a task-owned running simulator.
Each exact selector is a separate execution; no SDK or simulator is installed.
"""
from __future__ import annotations
import argparse
import json
import hashlib
import re
from pathlib import Path
import sys

from tools.build_watchface import ROOT, BuildBlocked, build, discover
from tools.run_native_tests import observe_program, parse_output

SELECTORS = (
    'verifiedRocketDecode', 'incidentFreshHistory', 'incidentHistoryPolicy', 'incidentCustomDuplicateOrdering',
    'incidentFreshCacheTransientFailure', 'incidentGeneratedHistory', 'incidentFirstPaintExpiry',
    'physicalHealthRearmRegressionBatch', 'menuAffectedBatch', 'menuPeerControls', 'menuCadenceFrames',
    'countdownAffectedBatch', 'generatedViewLifecycle', 'generatedFitnessOwners',
    'foregroundArtTimerBudget', 'cadenceNoPeriodicTimers', 'coldLowAcquiresOneFieldSnapshot',
    'generatedForegroundCadence', 'anchoredModelFrame', 'stepsCountdownBatch',
)
PROFILES = ('fr165', 'fr165m')


def parse_runtime_output(raw: str, raw_exit: int, selector: str) -> dict:
    # These are the production lifecycle's precise diagnostics, not a general
    # allowance for unknown output. Any other line remains fail-closed.
    filtered = []
    active = False
    for line in raw.splitlines(keepends=True):
        text = line.strip()
        if re.fullmatch(r'Executing test \w+\.\.\.', text):
            active = True
        elif text in ('PASS', 'FAIL', 'ERROR', 'RESULTS'):
            active = False
        if active and re.fullmatch(r'SF_VIEW mode=(HIGH|LOW) pending=(true|false)', text):
            continue
        filtered.append(line)
    return parse_output(''.join(filtered), raw_exit, (selector,))


def reusable_build(root: Path, folder: Path, profile: str) -> dict | None:
    receipt_path = folder / 'build.json'
    if not receipt_path.exists():
        return None
    receipt = json.loads(receipt_path.read_text())
    expected = receipt.get('source_sha256', {})
    current = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (root / 'watchface').rglob('*') if p.is_file()}
    program = Path(receipt.get('package', ''))
    if (receipt.get('status') != 'compiled' or receipt.get('product') != profile
        or receipt.get('test_scope') != 'runtime' or expected != current
        or receipt.get('build_tool_sha256') != hashlib.sha256((root / 'tools/build_watchface.py').read_bytes()).hexdigest()
        or not program.is_file() or receipt.get('package_sha256') != hashlib.sha256(program.read_bytes()).hexdigest()):
        raise BuildBlocked('existing runtime output is not bound to current compiled inputs; use a new output directory')
    return receipt


def execute(root: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    context = discover(root)
    results_path = output / 'results.json'
    previous = json.loads(results_path.read_text()) if results_path.exists() else []
    by_selector = {(r['profile'], r['selector']): r for r in previous}
    results = []
    for profile in PROFILES:
        folder = output / profile
        receipt = reusable_build(root, folder, profile) or build(folder, root=root, tests=True, test_scope='runtime', profile=profile)
        for selector in SELECTORS:
            dest = folder / selector
            try:
                old = by_selector.get((profile, selector))
                log = dest / 'native-tests.log'
                if old is not None and log.is_file() and 'raw_exit_code' in old:
                    verdict = parse_runtime_output(log.read_text(), old['raw_exit_code'], selector)
                else:
                    actual = observe_program(receipt['package'], dest, context, selector, profile)
                    verdict = parse_runtime_output(actual['raw'], actual['raw_exit_code'], selector)
            except Exception as error:
                dest.mkdir(parents=True, exist_ok=True)
                (dest / 'runner-error.txt').write_text(repr(error) + '\n')
                verdict = {'status': 'failed', 'error': str(error)}
            results.append({'profile': profile, 'selector': selector, **verdict})
            (output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
            if verdict['status'] != 'passed':
                raise BuildBlocked('runtime selector failed or was incomplete: '+profile+'/'+selector)
    (output / 'results.json').write_text(json.dumps(results, indent=2) + '\n')
    if len(results) != len(PROFILES) * len(SELECTORS) or any(x['status'] != 'passed' for x in results):
        raise BuildBlocked('runtime regressions incomplete or failed; inspect raw result directory')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        execute(ROOT, args.output.resolve())
    except (BuildBlocked, OSError) as error:
        print('BLOCKED/FAILED: ' + str(error), file=sys.stderr)
        return 2
    print('Runtime regressions PASS: both profiles, all exact selectors')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
