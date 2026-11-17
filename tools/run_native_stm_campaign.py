#!/usr/bin/env python3
"""Run isolated native STM campaigns; no Python business model or live services."""
from __future__ import annotations
import argparse
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time
import traceback
from xml.etree import ElementTree as ET

try:
    from tools.run_native_tests import parse_output
except ModuleNotFoundError:
    from run_native_tests import parse_output

ROOT = Path(__file__).resolve().parents[1]
SDK = '/sdk/Sdks/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262/bin'
LANES = (('spacefox-event-pbt-20261117', Path('/Users/jekamas/.codex/tmp/spacefox-stm-pbt-20261117')),
         ('spacefox-event-pbt-pilot-1', Path('/Users/jekamas/.codex/tmp/spacefox-stm-pbt-pilot-1')),
         ('spacefox-event-pbt-peer-2', Path('/Users/jekamas/.codex/tmp/spacefox-stm-pbt-peer-2')),
         ('spacefox-event-pbt-peer-3', Path('/Users/jekamas/.codex/tmp/spacefox-stm-pbt-peer-3')),
         ('spacefox-event-pbt-peer-4', Path('/Users/jekamas/.codex/tmp/spacefox-stm-pbt-peer-4')),
         ('spacefox-event-pbt-peer-5', Path('/Users/jekamas/.codex/tmp/spacefox-stm-pbt-peer-5')))
COMPILES = threading.BoundedSemaphore(2)
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


def execute(owner, worker, seconds, output, ready=None):
    container, task = LANES[worker]
    isolated = task / 'isolated'
    sources=list((ROOT / 'watchface/stm-property-tests').glob('*.mc'))
    expected={p.name for p in sources}
    unexpected={p.relative_to(isolated).as_posix() for p in isolated.rglob('*.mc')}-expected
    if unexpected:
        raise RuntimeError('unreviewed private native inputs: '+', '.join(sorted(unexpected)))
    for src in sources:
        shutil.copyfile(src, isolated / src.name)
    template=(task/'test.jungle').read_text().splitlines()
    if template != ['project.manifest = /task/pbt-manifest.xml',
                    'base.sourcePath = /source/watchface/source;/task/isolated',
                    'base.resourcePath = /source/watchface/resources',
                    'base.lang.rus = /source/watchface/resources-rus']:
        raise RuntimeError('private SDK jungle differs from reviewed source closure')
    tree=ET.parse(ROOT/'watchface/manifest.xml')
    app=tree.getroot().find('{http://www.garmin.com/xml/connectiq}application')
    app.set('entry','PbtApp');app.set('id',format(int('c0d8e48b8f1445a3b9b93b9f700cf505',16)+worker,'032x'))
    tree.write(task/'pbt-manifest.xml',encoding='utf-8',xml_declaration=True)
    native=(ROOT/'watchface/source/generated/NativeVersion.mc').read_text()
    identity=re.search(r'const BUILD = "([0-9.]+)"; const ID = "([0-9a-f]{8})";',native)
    if identity is None:
        raise RuntimeError('invalid native source identity')
    execution_ms=seconds*1000+max(1000,seconds*10) # margin; real requested wall fence stays strict
    (isolated / 'PbtConfig.mc').write_text(
        f'(:test) module PbtConfig {{ const WORKER={worker}; const OWNER={owner}; const FIRST_SEED={1+worker*400000}; const DURATION_MS={execution_ms}; }}\n')
    compile_cmd = ('docker', 'exec', container, f'{SDK}/monkeyc', '-f', '/task/test.jungle',
                   '-o', f'/task/campaign-{owner}.prg', '-d', 'fr165m', '-y', '/task/test.der', '-t', '-l', '3')
    try:
        with COMPILES:
            if ready is not None and ready.broken:
                raise threading.BrokenBarrierError()
            compiled = command(*compile_cmd, timeout=180)
        program=task/f'campaign-{owner}.prg'
        program_sha=hashlib.sha256(program.read_bytes()).hexdigest()
        (output / f'{NAMES[owner]}-compile.log').write_text(compiled.stdout)
        # Dedicated task containers only; each VM/config/port namespace is private.
        command('docker', 'exec', container, 'sh', '-c',
                f'pkill -f "[/]bin/simulator" || true; DISPLAY=:99 {SDK}/connectiq > /task/campaign-simulator.log 2>&1 &')
        if ready is not None:
            ready.wait(timeout=180*((ready.parties+1)//2)+60)
    except BaseException:
        if ready is not None:
            ready.abort()
        try:
            command('docker','exec',container,'sh','-c','pkill -f "[/]bin/simulator" || true',timeout=20)
        except Exception as cleanup:
            (output/f'{NAMES[owner]}-cleanup-error.txt').write_text(repr(cleanup)+'\n')
        raise
    cmd = ('docker', 'exec', container, 'env', 'DISPLAY=:99', f'{SDK}/monkeydo',
           f'/task/campaign-{owner}.prg', 'fr165m', '-t', 'campaignPilot')
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
        try:
            command('docker','exec',container,'sh','-c','pkill -f "[/]bin/simulator" || true',timeout=20)
            cleanup_ok=True
        except Exception as error:
            (output/f'{NAMES[owner]}-cleanup-error.txt').write_text(repr(error)+'\n')
            cleanup_ok=False
    raw = ''.join(lines)
    begin_markers=re.findall(r'PBT_CAMPAIGN_BEGIN worker=(\d+) owner=(\d+) first=(\d+) version=([0-9.]+) native_id=([0-9a-f]{8}) budget_ms=(\d+)',raw)
    marker = re.search(r'PBT_CAMPAIGN_END worker=(\d+) owner=(\d+) first=(\d+) next=(\d+) batches=(\d+) events=(\d+) productive_ms=(\d+) wall_ms=(\d+)', raw)
    cov = re.search(r'PBT_CAMPAIGN_COVERAGE (.+) assertions=(\d+) skipped=(\d+)', raw)
    parsed = parse_output(raw, rc, ('campaignPilot',))
    counts = None if cov is None else coverage_counts(cov[1])
    good = (cleanup_ok and parsed['status'] == 'passed' and len(begin_markers)==1 and
            begin_markers[0]==(str(worker),str(owner),str(1+worker*400000),identity[1],identity[2],str(execution_ms)) and
            raw.count('PBT_CAMPAIGN_END ')==1 and raw.count('PBT_CAMPAIGN_COVERAGE ')==1 and marker is not None and cov is not None and counts is not None and
            int(marker[1]) == worker and int(marker[2]) == owner and int(marker[3]) == 1+worker*400000 and
            int(marker[4])-int(marker[3]) == int(marker[5])*8 and
            int(marker[5]) > 0 and int(marker[6]) > 0 and int(marker[7]) >= execution_ms and
            int(cov[2]) > int(marker[6]) and int(marker[8]) >= int(marker[7]) and
            begin is not None and end is not None and end-begin >= seconds)
    return {'owner': NAMES[owner], 'worker': worker, 'status': 'GREEN' if good else 'RED',
            'configured_budget_ms': execution_ms, 'requested_seconds': seconds,
            'thread_id': threading.get_ident(), 'container': container, 'cleanup_ok': cleanup_ok,
            'program': str(program), 'program_sha256': program_sha,
            'test_uuid': app.get('id'), 'entry': 'PbtApp', 'version': identity[1], 'native_id': identity[2],
            'raw_exit': rc, 'launcher': parsed, 'host_start': started, 'productive_begin': begin,
            'productive_end': end, 'coverage': counts,
            'assertions': None if cov is None else int(cov[2]), 'skipped': None if cov is None else int(cov[3]),
            'first_seed': None if marker is None else int(marker[3]),
            'next_seed': None if marker is None else int(marker[4]),
            'traces': None if marker is None else int(marker[4])-int(marker[3]),
            'events': None if marker is None else int(marker[6]),
            'productive_ms': None if marker is None else int(marker[7]),
            'native_wall_ms': None if marker is None else int(marker[8]),
            'observed_wall_seconds': None if begin is None or end is None else end-begin}


def run_batches(owners, workers, seconds, output):
    results=[]
    def invoke(owner,worker,ready):
        try:
            return execute(owner,worker,seconds,output,ready)
        except BaseException as error:
            ready.abort()
            details=traceback.format_exc()
            captured=getattr(error,'stdout',None) or getattr(error,'output',None)
            if captured:
                details+='\nCAPTURED COMMAND OUTPUT\n'+(captured.decode(errors='replace') if isinstance(captured,bytes) else captured)
            (output/f'{NAMES[owner]}-error.txt').write_text(details)
            raise
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for pos in range(0,len(owners),workers):
            batch=owners[pos:pos+workers];ready=threading.Barrier(len(batch));rows={};errors=[]
            futures={pool.submit(invoke,owner,worker,ready):owner for worker,owner in enumerate(batch)}
            for future in as_completed(futures):
                try:rows[futures[future]]=future.result()
                except BaseException as error:errors.append((futures[future],error))
            if errors:
                # A peer waiting on the aborted barrier must not hide the
                # original preparation/compiler failure in another worker.
                owner,error=next(((owner,e) for owner,e in errors if not isinstance(e,threading.BrokenBarrierError)),errors[0])
                (output/'error.txt').write_text('causal_owner='+NAMES[owner]+'\n'+repr(error)+'\n'+
                    '\n'.join(NAMES[n]+': '+repr(e) for n,e in errors)+'\n')
                raise error
            pair=[rows[owner] for owner in batch];results.extend(pair)
            (output/'progress.json').write_text(json.dumps(results,indent=2)+'\n')
            if any(item['status']!='GREEN' for item in pair):break
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seconds', type=int, default=600)
    ap.add_argument('--owners', default=','.join(str(x) for x in range(len(NAMES))))
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--workers', type=int, choices=range(1, len(LANES)+1), default=6)
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
    results = run_batches(owners, args.workers, args.seconds, args.output)
    final_dirty=command('git','-C',str(ROOT),'status','--porcelain','--',*relevant).stdout
    source_delta=command('git','-C',str(ROOT),'diff','--name-only',revision,'HEAD','--',*relevant).stdout
    if final_dirty or source_delta:
        raise SystemExit('native campaign source changed during execution; receipts retained')
    overlaps = []
    distinct_threads = True
    for pos in range(0, len(results), args.workers):
        batch=results[pos:pos+args.workers]
        distinct_threads = distinct_threads and len({r['thread_id'] for r in batch})==len(batch)
        if len(batch)>1 and all(r['productive_begin'] is not None and r['productive_end'] is not None for r in batch):
            overlaps.append(max(0,min(r['productive_end'] for r in batch)-max(r['productive_begin'] for r in batch)))
    complete = (len(results) == len(owners) and all(item['status']=='GREEN' for item in results)
                and distinct_threads and all(overlap > 0 for overlap in overlaps))
    report = {'status': 'GREEN' if complete else 'RED', 'source_revision': revision,
              'version': identity[1], 'native_id': identity[2], 'required_seconds': args.seconds,
              'workers_per_batch': args.workers, 'compile_concurrency_limit': 2,
              'full_duration': args.seconds >= 600, 'overlap_seconds': overlaps, 'results': results}
    (args.output / 'summary.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    if not complete:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
