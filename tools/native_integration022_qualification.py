"""Bind the combined current source to both authenticated historical qualifications.

Historical inputs are reconstructed only in isolated hardlinked temporary trees;
this does not reinstate retired product files or claim old receipts test this merge.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

BASE = 'openspec/changes/spacefox-watchface/evidence/performance021/integration/'
ROOTS = ('tools', 'watchface', 'locales', 'openspec', 'tests', 'assets', 'corpus',
         'catalog', 'schemas', 'docs', 'release', 'prototype', '.github', 'licenses')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(root, name, expected):
    rel = Path(name)
    if rel.is_absolute() or '..' in rel.parts or not rel.parts:
        raise ValueError('unsafe combined qualification path: ' + name)
    path = (root / rel).resolve()
    if not path.is_relative_to(root) or not path.is_file() or sha(path) != expected:
        raise ValueError('combined qualification input changed: ' + name)
    return path


def watch_inputs(root):
    watch = root / 'watchface'
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(watch.rglob('*')) if p.is_file()}


def validate(root, catalog):
    root = Path(root).resolve()
    ref = catalog['supportPolicy']['softwareQualificationProof']['integration022Proof']
    record = json.loads(checked(root, ref['path'], ref['sha256']).read_text())
    if record['scope'] != 'performance021-b1-current-source-022' or record['version'] != '0.1.22':
        raise ValueError('wrong combined qualification scope/version')
    catalog_body = json.loads(json.dumps(catalog))
    catalog_body['supportPolicy']['softwareQualificationProof'].pop('integration022Proof', None)
    normalized = json.dumps(catalog_body, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()
    if hashlib.sha256(normalized).hexdigest() != record['catalogWithoutIntegrationSha256']:
        raise ValueError('combined locale policy changed outside proof binding')
    if watch_inputs(root) != record['watchInputs']:
        raise ValueError('combined watch input closure changed')
    from tools.native_performance021_qualification import REQUIRED_CURRENT
    from tools.native_b1_021_qualification import OWNERS, COMBINED, PEER_REPAIR
    from tools.run_native_tests import parse_output
    expected_owners = set(REQUIRED_CURRENT) | set(OWNERS) | {
        'tools/native_integration022_qualification.py', 'tools/native_language_policy.py',
        'tools/build_native_resources.py', 'tools/native_display03_probe.py',
        'tools/fields018_native_probe.py', 'tools/native_other_batch.py',
    }
    if set(record['owners']) != expected_owners:
        raise ValueError('combined qualification owner inventory differs')
    for name, digest in record['owners'].items():
        checked(root, name, digest)
    native = record['b1Native']
    if set(native) != set(COMBINED + PEER_REPAIR + ['b1TailCleanupRechecksOwnership', 'b1OwnerStopReleasesPendingWork']):
        raise ValueError('combined B1 case inventory differs')
    for name, item in native.items():
        log = checked(root, item['path'], item['sha256']).read_text()
        if parse_output(log, item['rawExit'], (name,))['status'] != 'passed':
            raise ValueError('combined B1 native case failed: ' + name)
    required_evidence = {'b1Results', 'b1Restore', 'batchLinear', 'batchCorruption',
                         'batchRestore', 'scene', 'fields', 'incidentFirst',
                         'incidentRepairPrefix', 'incidentRepairFragments', 'display',
                         'b1Build', 'b1RepairBuild', 'b1StopBuild', 'b1Program', 'b1RepairProgram', 'b1StopProgram',
                         'batchSource', 'batchBuild', 'batchProgram', 'batchFinalBuild', 'batchFinalProgram',
                         'b1StopRestore', 'incidentFinalProjection', 'incidentFinalStop'}
    if set(record['evidence']) != required_evidence:
        raise ValueError('combined observation inventory differs')
    checked_evidence = {name: checked(root, item['path'], item['sha256'])
                        for name, item in record['evidence'].items()}
    binaries = {'b1Program', 'b1RepairProgram', 'b1StopProgram', 'batchProgram', 'batchFinalProgram'}
    observed = {name: path.read_text() for name, path in checked_evidence.items() if name not in binaries}
    initial_build = json.loads(observed['b1Build'])
    repair_build = json.loads(observed['b1RepairBuild'])
    stop_build = json.loads(observed['b1StopBuild'])
    for label, build in [('b1Program', initial_build), ('b1RepairProgram', repair_build), ('b1StopProgram', stop_build)]:
        if hashlib.sha256(gzip.decompress(checked_evidence[label].read_bytes())).hexdigest() != build['programSha256']:
            raise ValueError('combined SDK program differs: ' + label)
    current_b1 = repair_build['inputHashes']
    final_b1 = stop_build['inputHashes']
    for name, expected in final_b1.items():
        checked(root, name, expected)
    changed_b1 = {name for name in set(initial_build['inputHashes']) | set(current_b1)
                  if initial_build['inputHashes'].get(name) != current_b1.get(name)}
    if changed_b1 != {'watchface/source/NativeForegroundCache.mc',
                      'watchface/source/generated/NativeVersion.mc',
                      'watchface/runtime-b1-tests/IntegrationAdmission021.mc'}:
        raise ValueError('combined B1 retained-source boundary differs')
    changed_stop = {name for name in set(current_b1) | set(final_b1)
                    if current_b1.get(name) != final_b1.get(name)}
    if changed_stop != {'watchface/source/SpaceFoxApp.mc',
                        'watchface/source/generated/NativeVersion.mc',
                        'watchface/runtime-b1-tests/IntegrationAdmission021.mc'}:
        raise ValueError('combined stop retained-source boundary differs')
    for build_key, program_key in [('batchBuild', 'batchProgram'), ('batchFinalBuild', 'batchFinalProgram')]:
        batch_build = json.loads(observed[build_key])
        if (hashlib.sha256(gzip.decompress(checked_evidence[program_key].read_bytes())).hexdigest() != batch_build['packageSha256'] or
            sha(checked_evidence['batchSource']) != batch_build['sourceSha256']):
            raise ValueError('combined batch program or source differs')
    for key, test in [('batchLinear', 'integrationBatchLinearAndTerminal'),
                      ('batchCorruption', 'integrationBatchCorruptPrefixBeforeCompletion'),
                      ('incidentRepairPrefix', 'deliveryBatchPrefixLifetime'),
                      ('incidentRepairFragments', 'deliveryProvisionalFragmentCleanup'),
                      ('incidentFinalProjection', 'deliveryRawProjectionIntegrity'),
                      ('incidentFinalStop', 'deliveryOwnerStopReleasesCycle')]:
        if parse_output(observed[key], 1, (test,))['status'] != 'passed':
            raise ValueError('combined native case failed: ' + test)
    if ('prefix=17 terminal=17 checks=34 hashedBytes=100010' not in observed['batchLinear'] or
        'terminalScanRefused=true repaired=true acceptedAndRasterUnchanged=true' not in observed['batchCorruption']):
        raise ValueError('combined batch observation differs')
    for key in ('batchRestore', 'b1Restore', 'b1StopRestore'):
        restoration = json.loads(observed[key])
        if not restoration['restored'] or not restoration['ini']:
            raise ValueError('combined simulator runtime restoration differs')
    from tools.native_other_batch import EXPECTED
    incident_names = EXPECTED['watchface/incident-tests/DeliveryContinuityTests.mc']
    incident = parse_output(observed['incidentFirst'], 1, tuple(incident_names))
    repaired = {'deliveryBatchPrefixLifetime', 'deliveryProvisionalFragmentCleanup'}
    if set(incident['observed_tests']) != set(incident_names) or any(
        status != ('ERROR' if name in repaired else 'PASS')
        for name, status in incident['observed_tests'].items()
    ):
        raise ValueError('combined incident first-run outcomes differ')
    if 'PASSED (passed=21, failed=0, errors=0)' not in observed['scene'] or \
       'PASSED (passed=10, failed=0, errors=0)' not in observed['fields']:
        raise ValueError('combined scene or field suite differs')
    if (parse_output(observed['display'], 1, ('display03RealMapDecode', 'display03BundledOutlineDecode'))['status'] != 'passed' or
        'pixelShaVerified=true noDiscardedOutline=true' not in observed['display']):
        raise ValueError('combined decoder observations differ')
    from tools.generate_native_version import validate as validate_version
    validate_version(root)
    locales = None
    for side in ('performance', 'runtime'):
        recipe = record['historical'][side]
        if recipe['revision'] not in ('f955c6022ddabeb0153b71006ae1fa4bba4ad179', 'c410eb4e5d86bbbe28d100996abf6bf5beb0607d'):
            raise ValueError('unexpected combined parent revision')
        for item in recipe['restore'].values():
            checked(root, item['path'], item['sha256'])
        with tempfile.TemporaryDirectory(prefix='spacefox-022-history-') as temporary:
            target = Path(temporary)
            for path in root.iterdir():
                if path.is_file() and not path.is_symlink():
                    os.link(path, target / path.name)
            for name in ROOTS:
                source = root / name
                if source.is_dir():
                    shutil.copytree(source, target / name, copy_function=os.link,
                                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            for name in recipe['remove']:
                rel = Path(name)
                if rel.is_absolute() or '..' in rel.parts or not rel.parts:
                    raise ValueError('unsafe historical removal')
                path = target / rel
                if path.is_file() or path.is_symlink():
                    path.unlink()
            for name, item in recipe['restore'].items():
                rel = Path(name)
                if rel.is_absolute() or '..' in rel.parts or not rel.parts:
                    raise ValueError('unsafe historical restoration')
                dst = target / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.unlink(missing_ok=True)
                shutil.copyfile(root / item['path'], dst)
            code = ('import json;from pathlib import Path;from tools.native_language_policy import software_locales;'
                    'print(json.dumps(software_locales(Path.cwd())))')
            run = subprocess.run([sys.executable, '-B', '-c', code], cwd=target,
                                 env={**os.environ, 'PYTHONPATH': str(target)},
                                 capture_output=True, text=True, timeout=300)
            if run.returncode:
                raise ValueError('historical ' + side + ' qualification failed: ' + run.stderr[-3000:])
            observed = json.loads(run.stdout.strip().splitlines()[-1])
        if observed != ['en', 'ru', 'de', 'fr', 'es']:
            raise ValueError('historical locale set differs: ' + side)
        locales = observed
    return locales
