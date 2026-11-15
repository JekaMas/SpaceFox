#!/usr/bin/env python3
"""Inventory and run current native suites sequentially under a caller-owned SDK lease.

Does not create isolation, acquire a simulator lease, or restore simulator state.
Run only after the caller has proved exclusive ownership and arranged restoration.
The scene, incident, UX and localization families have separate harnesses and are
reported as outstanding here; this command is not by itself the whole native suite.
"""
import argparse
import ast
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PROBES = ROOT / 'tests/native_scene_diagnostics/current-508'


def inventory(root=ROOT):
    root = Path(root)
    probes = root / 'tests/native_scene_diagnostics/current-508'
    entries = []
    mapped = set()
    for path in sorted(probes.glob('current_*_probe.py')):
        text = path.read_text()
        tree = ast.parse(text)
        names = next(ast.literal_eval(n.value) for n in tree.body
                     if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'NAMES' for t in n.targets))
        match = re.search(r"ROOT/'(watchface/current-[^']+\.mc)'", text)
        if not match:
            raise ValueError('missing current source binding: ' + str(path))
        source = root / match.group(1)
        actual = re.findall(r'\(:test[^\n]*\)\s*function\s+(\w+)', source.read_text())
        if not actual or len(actual) != len(set(actual)) or set(actual) != set(names):
            raise ValueError(f'native inventory differs: {source}, declared={names}, actual={actual}')
        mapped.add(source.parent)
        entries.append({'probe': str(path.relative_to(root)), 'source': str(source.relative_to(root)), 'tests': list(names)})
    current = {p for p in (root/'watchface').glob('current-*-tests') if p.is_dir()}
    if mapped != current:
        raise ValueError(f'current suite directory mismatch: missing={current-mapped}, unexpected={mapped-current}')
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventory', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--source', action='append', help='run named inventory source after retaining earlier observations')
    parser.add_argument('--isolated-simulator', type=Path, help='launch and stop an owned simulator for each suite; caller owns the exclusive lane')
    args = parser.parse_args()
    rows = inventory()
    report = {'currentSuites': rows, 'currentTestCount': sum(len(r['tests']) for r in rows),
              'separateNativeFamilies': ['watchface/tests', 'watchface/scene-tests', 'watchface/incident-tests',
                                         'watchface/ux-tests', 'watchface/localization-tests'],
              'boundary': 'inventory only' if args.inventory else 'caller-owned simulator lease'}
    if args.inventory:
        print(json.dumps(report, indent=2))
        return
    if args.output is None:
        parser.error('--output is required when running')
    if args.source:
        selected=set(args.source);known={r['source'] for r in rows}
        if not selected<=known:parser.error('unknown source selector')
        rows=[r for r in rows if r['source'] in selected]
        report['selectedSources']=[r['source'] for r in rows]
    args.output.mkdir(parents=True, exist_ok=True)
    for row in rows:
        out = args.output / Path(row['probe']).stem
        simulator=None
        try:
            if args.isolated_simulator:
                simulator=subprocess.Popen([str(args.isolated_simulator)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                time.sleep(3)
                if simulator.poll() is not None:raise RuntimeError('owned simulator exited before suite')
            result = subprocess.run([sys.executable, str(ROOT/row['probe']), str(out)], cwd=ROOT, check=False)
        finally:
            if simulator is not None and simulator.poll() is None:
                simulator.terminate()
                try:simulator.wait(timeout=10)
                except subprocess.TimeoutExpired:simulator.kill();simulator.wait()
        row['runnerExit'] = result.returncode
        if result.returncode:
            raise RuntimeError('native suite failed: '+row['probe'])
    (args.output/'inventory.json').write_text(json.dumps(report, indent=2)+'\n')
    print('PASS selected current suites; see inventory.json; any unselected and separate native families remain required')

if __name__ == '__main__':
    main()
