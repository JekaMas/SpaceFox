#!/usr/bin/env python3
"""Build and run scoped current refresh/cache native assertions.

`build` invokes only the existing compiler helper, never a simulator. `run`
requires the shared simulator lease, uses a newly generated test UUID, and
rejects source/toolchain drift. Neither mode establishes phone/device behavior.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from pathlib import Path
from unittest.mock import patch
from xml.etree import ElementTree as ET

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.build_watchface import ROOT, discover
from tools.native_full_visual_runtime import GROUPS, IMPORTS, build_probe
from tools.run_native_tests import parse_output

GROUP = 'refresh-cache-whole'
NAMES = ('refreshColdCache', 'refreshCacheSequence', 'refreshCacheRefusals',
         'refreshSourceAge', 'refreshNearAndClock', 'refreshNamespaces',
         'refreshFeedCacheFaults', 'refreshParserRejects', 'refreshSdkStorage',
         'refreshUnresolvedSequence', 'refreshUnresolvedScene', 'refreshJsonRefusals',
         'refreshTransferBoundaries', 'refreshNotModifiedCallback', 'refreshOfflineView')
FIXTURE = ROOT / 'tests/fixtures/watch_refresh_cache'
FINAL_PACKETS = ROOT / 'openspec/changes/spacefox-watchface/evidence/final-native-timing-settings/packets.json'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inputs():
    paths = (Path(__file__).resolve(), FIXTURE/'Assertions.mc', FIXTURE/'packets.json', FIXTURE/'oracle.json',
             FIXTURE/'unresolved.json', FIXTURE/'unresolved-oracle.json', FIXTURE/'build_unresolved.py',
             FIXTURE/'build_packets.py', FINAL_PACKETS)
    return {str(path.relative_to(ROOT)): sha(path) for path in paths}


def build(output, diagnostic_unqualified=False):
    # A fresh UUID isolates actual SDK Storage from every other test/app.
    GROUPS[GROUP] = (uuid.uuid4().hex, 'SpaceFoxRefreshCacheTests.prg')
    source = IMPORTS + '(:background) class SfrRuntimeApp extends SpaceFoxApp {function initialize(){SpaceFoxApp.initialize();}}\n'
    source += (FIXTURE/'Assertions.mc').read_text()
    refresh = json.loads((FIXTURE/'packets.json').read_bytes())
    final = json.loads(FINAL_PACKETS.read_bytes())
    unresolved = json.loads((FIXTURE/'unresolved.json').read_bytes())
    for name, value in refresh['catalogs'].items():
        reference = refresh['catalogs']['different' if name == 'different' else 'initial']
        if value != reference:
            raise ValueError('unexpected per-packet catalog divergence: '+name)
    rows = {
        'RefreshCatalogInitial': refresh['catalogs']['initial'],
        'RefreshCatalogDifferent': refresh['catalogs']['different'],
        'FinalCatalog': {'catalog': final['catalog'], 'catalogDigest': final['catalogDigest']},
        **{name: {'raw': refresh['packets'][key]} for name, key in (
            ('RefreshInitial', 'initial'), ('RefreshUnchanged', 'unchanged'),
            ('RefreshMoved', 'moved'), ('RefreshRefresh', 'refresh'),
            ('RefreshWithdrawn', 'withdrawn'), ('RefreshWithdrawnRefresh', 'withdrawn_refresh'),
            ('RefreshDifferent', 'different'))},
        'FinalExact': {'raw': final['exact']}, 'FinalInvalid': {'raw': final['invalid']},
        **{name: {'raw': unresolved[key]} for name, key in (
            ('UnresolvedEmptyCatalog', 'emptyCatalog'), ('UnresolvedRealCatalog', 'realCatalog'),
            ('UnresolvedTechnicalCatalog', 'technicalCatalog'), ('UnresolvedEmpty1', 'empty1'),
            ('UnresolvedReal2', 'real2'), ('UnresolvedEmpty3', 'empty3'),
            ('UnresolvedReal4', 'real4'), ('UnresolvedTechnical1', 'technical1'),
            ('UnresolvedRealScene', 'realScene'), ('UnresolvedTechnicalScene', 'technicalScene'))},
    }
    resources = {}
    xml = ['<resources>']
    for name, value in rows.items():
        filename = name+'.json'
        raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
        if len(raw) > 8192:
            raise ValueError('test resource exceeds 8192 bytes: '+name)
        resources[filename] = raw
        xml.append('<jsonData id="'+name+'" filename="'+filename+'"/>')
    xml.append('</resources>')
    resources['refresh.xml'] = ''.join(xml).encode('utf-8')
    before = inputs()
    if diagnostic_unqualified:
        # Same explicit bootstrap boundary as native_timing_settings.py. The
        # unqualified manifest is never a language or release admission result.
        with patch('tools.native_full_visual_runtime.validate_manifest',
                   lambda root, lock: ET.parse(root/'watchface/manifest.xml')):
            result = build_probe(output, source, group=GROUP, tests=True, probe_resources=resources)
    else:
        result = build_probe(output, source, group=GROUP, tests=True, probe_resources=resources)
    if before != inputs():
        raise RuntimeError('test inputs changed during compile')
    context = discover()
    result['admissionValidation'] = 'bypassed-diagnostic-only' if diagnostic_unqualified else 'strict-current-proof'
    result['testInputs'] = before
    result['expectedTests'] = list(NAMES)
    result['toolchain'] = {'compilerSha256': sha(context['compiler']),
                           'profileSha256': sha(context['profile']),
                           'simulatorProfileSha256': sha(context['simulator_profile'])}
    result['proofBoundary'] = 'Compiler only; no test, simulator, phone or physical pass.'
    (output/'build.json').write_text(json.dumps(result, indent=2)+'\n')
    if result['exitCode'] != 0:
        raise RuntimeError('native compiler failed; see compile.log')
    return result


def run(output):
    record = json.loads((output/'build.json').read_text())
    if record['exitCode'] != 0 or record['expectedTests'] != list(NAMES) or record['testInputs'] != inputs():
        raise RuntimeError('compiled test inputs are missing, failed or stale')
    for name, digest in {**record['productionSources'], **record['productionResources']}.items():
        path = ROOT/name
        if not path.is_file() or sha(path) != digest:
            raise RuntimeError('production source/resource changed: '+name)
    if set(record['productionSources']) != {str(p.relative_to(ROOT)) for p in (ROOT/'watchface/source').rglob('*.mc')}:
        raise RuntimeError('native production source set changed')
    for name, digest in record['probeResources'].items():
        if sha(output/'probe-resources'/name) != digest:
            raise RuntimeError('probe resource changed: '+name)
    context = discover()
    actual_tools = {'compilerSha256': sha(context['compiler']), 'profileSha256': sha(context['profile']),
                    'simulatorProfileSha256': sha(context['simulator_profile'])}
    if record['toolchain'] != actual_tools or sha(output/record['packageName']) != record['packageSha256']:
        raise RuntimeError('compiler/profile/package changed')
    command = [str(context['java']), '-Dfile.encoding=UTF-8', '-classpath', str(context['compiler']),
               'com.garmin.monkeybrains.monkeydodeux.MonkeyDoDeux', '-f', str(output/record['packageName']),
               '-d', 'fr165', '-s', str(context['sdk']/'bin/shell'), '-t']
    stdout_path, stderr_path = output/'native-stdout.log', output/'native-stderr.log'
    try:
        with stdout_path.open('w') as stdout, stderr_path.open('w') as stderr:
            completed = subprocess.run(command, stdout=stdout, stderr=stderr, text=True, timeout=180, check=False)
        code, timed_out = completed.returncode, False
    except subprocess.TimeoutExpired:
        code, timed_out = None, True
    raw = stdout_path.read_text()
    errors = stderr_path.read_text()
    parsed = parse_output(raw, code, NAMES) if code is not None and not errors else {'status': 'failed'}
    result = {'command': command, 'exitCode': code, 'timedOut': timed_out,
              'framework': parsed, 'stderrEmpty': not errors,
              'applicationUuid': record['applicationUuid'],
              'buildSourceHead': record['sourceHead'],
              'admissionValidation': record['admissionValidation'],
              'proofBoundary': 'SDK simulator plus controlled clock/fault storage; actual SDK Storage separately. No paired phone, physical watch or OS-liveness proof.'}
    (output/'execution.json').write_text(json.dumps(result, indent=2)+'\n')
    if parsed['status'] != 'passed':
        raise RuntimeError('native test execution did not pass; inspect raw logs and execution.json')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('build', 'run'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--diagnostic-unqualified', action='store_true', help='build only with explicitly unqualified manifest admission')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.mode == 'run' and args.diagnostic_unqualified:
        parser.error('--diagnostic-unqualified is build-only')
    result = build(output, args.diagnostic_unqualified) if args.mode == 'build' else run(output)
    print(json.dumps({'mode': args.mode, 'status': 'completed',
                      'applicationUuid': result['applicationUuid']}, sort_keys=True))


if __name__ == '__main__':
    main()
