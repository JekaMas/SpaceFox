#!/usr/bin/env python3
"""Run isolated native STM campaigns; no Python business model or live services."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time

try:
    from tools.run_native_tests import parse_output
except ModuleNotFoundError:
    from run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
SDK = '/sdk/Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262/bin'
LANES = (('spacefox-event-pbt-20261117', Path('/Users/jekamas/.codex/tmp/spacefox-stm-pbt-20261117')),
         ('spacefox-event-pbt-pilot-1', Path('/Users/jekamas/.codex/tmp/spacefox-stm-pbt-pilot-1')))
NAMES = ('display', 'request', 'scene', 'storage', 'temporal', 'cache-map', 'view',
         'foreground', 'fields', 'fitness', 'reminder', 'source', 'art-lease', 'wake', 'service-failure')


def coverage_counts(value):
    if not value.startswith('{') or not value.endswith('}'):
        return None
    result = {}
    for item in value[1:-1].split(', '):
        match = re.fullmatch(r'([A-Za-z0-9_]+)=>(\d+)', item)
        if match is None or match[1] in result or int(match[2]) <= 0:
            return None
        result[match[1]] = int(match[2])
    return result or None


def command(*args, **kwargs):
    return subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, **kwargs)


def execute(owner, worker, seconds, output):
    container, task = LANES[worker]
    isolated = task / 'isolated'
    for src in (ROOT / 'watchface/stm-property-tests').glob('*.mc'):
        shutil.copyfile(src, isolated / src.name)
    (isolated / 'PbtConfig.mc').write_text(
        f'(:test) module PbtConfig {{ const WORKER={worker}; const OWNER={owner}; const FIRST_SEED={1+worker*400000}; const DURATION_MS={seconds*1000}; }}\n')
    compile_cmd = ('docker', 'exec', container, f'{SDK}/monkeyc', '-f', '/task/test.jungle',
                   '-o', '/task/campaign.prg', '-d', 'fr165m', '-y', '/task/test.der', '-t', '-l', '3')
    compiled = command(*compile_cmd, timeout=180)
    (output / f'{NAMES[owner]}-compile.log').write_text(compiled.stdout)
    # Containers are dedicated to this task. No host or foreign process is touched.
    command('docker', 'exec', container, 'sh', '-c',
            f'pkill -f "[/]bin/simulator" || true; DISPLAY=:99 {SDK}/connectiq > /task/campaign-simulator.log 2>&1 &')
    cmd = ('docker', 'exec', container, 'env', 'DISPLAY=:99', f'{SDK}/monkeydo',
           '/task/campaign.prg', 'fr165m', '-t', 'campaignPilot')
    started = time.monotonic()
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, bufsize=1)
    watchdog = threading.Timer(seconds + 180, process.kill)
    watchdog.start()
    lines, begin, end = [], None, None
    try:
        with (output / f'{NAMES[owner]}.log').open('w') as log:
            for line in process.stdout:
                log.write(line); log.flush(); lines.append(line)
                if 'PBT_CAMPAIGN_BEGIN ' in line:
                    begin = time.monotonic()
                if 'PBT_CAMPAIGN_END ' in line:
                    end = time.monotonic()
        rc = process.wait()
    finally:
        watchdog.cancel()
    raw = ''.join(lines)
    marker = re.search(r'PBT_CAMPAIGN_END worker=(\d+) owner=(\d+) first=(\d+) next=(\d+) batches=(\d+) events=(\d+) productive_ms=(\d+)', raw)
    cov = re.search(r'PBT_CAMPAIGN_COVERAGE (.+) assertions=(\d+) skipped=(\d+)', raw)
    parsed = parse_output(raw, rc, ('campaignPilot',))
    counts = None if cov is None else coverage_counts(cov[1])
    good = (parsed['status'] == 'passed' and marker is not None and cov is not None and counts is not None and
            int(marker[1]) == worker and int(marker[2]) == owner and int(marker[4]) > int(marker[3]) and
            int(marker[5]) > 0 and int(marker[6]) > 0 and int(marker[7]) >= seconds*1000 and
            int(cov[2]) > int(marker[6]) and begin is not None and end is not None)
    return {'owner': NAMES[owner], 'worker': worker, 'status': 'GREEN' if good else 'RED',
            'raw_exit': rc, 'launcher': parsed, 'host_start': started, 'productive_begin': begin,
            'productive_end': end, 'coverage': counts,
            'assertions': None if cov is None else int(cov[2]), 'skipped': None if cov is None else int(cov[3]),
            'first_seed': None if marker is None else int(marker[3]),
            'next_seed': None if marker is None else int(marker[4]),
            'traces': None if marker is None else int(marker[4])-int(marker[3]),
            'events': None if marker is None else int(marker[6]),
            'productive_ms': None if marker is None else int(marker[7])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seconds', type=int, default=600)
    ap.add_argument('--owners', default=','.join(str(x) for x in range(len(NAMES))))
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    owners = [int(value) for value in args.owners.split(',')]
    if args.seconds <= 0 or len(owners) != len(set(owners)) or any(i not in range(len(NAMES)) for i in owners):
        ap.error('positive duration and unique valid owner indices required')
    revision = command('git', '-C', str(ROOT), 'rev-parse', 'HEAD').stdout.strip()
    relevant = ('watchface', 'tools/run_native_stm_campaign.py', 'tests/test_native_stm_campaign.py',
                'tools/native_audit_025_qualification.py', 'tools/release.py', 'locales/catalog.json')
    dirty = command('git', '-C', str(ROOT), 'status', '--porcelain', '--', *relevant).stdout
    if dirty:
        raise SystemExit('native campaign source is not clean; commit and review before running:\n' + dirty)
    native = (ROOT / 'watchface/source/generated/NativeVersion.mc').read_text()
    identity = re.search(r'const BUILD = "([0-9.]+)"; const ID = "([0-9a-f]{8})";', native)
    if identity is None:
        raise SystemExit('invalid generated native identity')
    args.output.mkdir(parents=True, exist_ok=False)
    results = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        for pos in range(0, len(owners), 2):
            batch = owners[pos:pos+2]
            futures = [pool.submit(execute, owner, worker, args.seconds, args.output) for worker, owner in enumerate(batch)]
            try:
                pair = [future.result() for future in futures]
            except Exception as exc:
                (args.output / 'error.txt').write_text(repr(exc)+'\n')
                raise
            results.extend(pair)
            (args.output / 'progress.json').write_text(json.dumps(results, indent=2)+'\n')
            if any(item['status'] != 'GREEN' for item in pair):
                break
    overlaps = []
    for pos in range(0, len(results)-1, 2):
        a,b = results[pos:pos+2]
        if a['productive_begin'] is not None and b['productive_begin'] is not None:
            overlaps.append(max(0, min(a['productive_end'],b['productive_end'])-max(a['productive_begin'],b['productive_begin'])))
    complete = (len(results) == len(owners) and all(item['status']=='GREEN' for item in results)
                and all(overlap > 0 for overlap in overlaps))
    report = {'status': 'GREEN' if complete else 'RED', 'source_revision': revision,
              'version': identity[1], 'native_id': identity[2], 'required_seconds': args.seconds,
              'full_duration': args.seconds >= 600, 'overlap_seconds': overlaps, 'results': results}
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if not complete:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
