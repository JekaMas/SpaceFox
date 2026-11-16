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
    if record['scope'] != 'performance021-b1-b2-b3-current-source-024' or record['version'] != '0.1.24':
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
        'tools/native_b2_022_qualification.py', 'tools/native_b3_023_qualification.py',
        'tools/check_b2_evidence.py', 'tools/check_b3_evidence.py',
        'tools/build_fallback_world.py',
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
    # These exact owners changed in the subsequent B2/B3 merge. The retained
    # earlier cases still have their original binary; affected cases execute
    # separately on the source-bound current binary below.
    merged_changes = {'watchface/manifest.xml', 'watchface/runtime-b1-tests/ClockFirst021.mc',
        'watchface/runtime-b1-tests/DecodePending.mc', 'watchface/source/FeedScene.mc',
        'watchface/source/LaunchReminder.mc', 'watchface/source/LaunchReminderForeground.mc',
        'watchface/source/NativeForegroundApp.mc', 'watchface/source/NativeUpcomingCache.mc',
        'watchface/source/SceneContext.mc', 'watchface/source/SceneRenderer.mc',
        'watchface/source/SpaceFoxView.mc', 'watchface/source/generated/NativeVersion.mc'}
    actual_changes = {name for name, expected in final_b1.items()
                      if not (root / name).is_file() or sha(root / name) != expected}
    if actual_changes != merged_changes:
        raise ValueError('combined retained B1 source boundary differs')
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
    required_current = {'peer024WorldAndDownloadedOwnership', 'b2ArithmeticAndRetention',
        'b2AdmittedFactsWithoutArt', 'b2CapturedHourAndMissingPoint', 'b2LowUnmatchedPoint',
        'b2FailedAndInterruptedReplacement', 'b2RescheduleAndNewSelection', 'b2SourcedAscentRetention',
        'b3QueueAndRollover', 'b3AdmissionAndUnknown', 'b3QuietProvider', 'b3OrdinaryReopen',
        'b3RescheduleAndQuiet', 'b3DisplayRetainedSelection', 'b1ColdAcquisition',
        'b1PreparedPromotion', 'b1TailCleanupRechecksOwnership', 'b1OwnerStopReleasesPendingWork',
        'b1LowHeapDefersOptionalDecode', 'b1ShortWakeResume', 'b1RealDecodeTicksAndCancels',
        'b1FailedPromotionRecovery021', 'b1SupersededDuringAdmission021',
        'peerSourceChangeDefersRenderer021', 'b1CapturedSuccessorTicksInFallback'}
    if set(record['currentNative']) != required_current:
        raise ValueError('combined current B1/B2/B3 case inventory differs')
    for name, item in record['currentNative'].items():
        log = checked(root, item['path'], item['sha256']).read_text()
        if parse_output(log, item['rawExit'], (name,))['status'] != 'passed':
            raise ValueError('combined current SDK case failed: ' + name)
    build = json.loads(checked(root, record['currentBuild']['path'], record['currentBuild']['sha256']).read_text())
    program = checked(root, record['currentProgram']['path'], record['currentProgram']['sha256'])
    if hashlib.sha256(gzip.decompress(program.read_bytes())).hexdigest() != build['programSha256']:
        raise ValueError('combined current SDK program differs')
    old_sources = {
        'watchface/source/generated/FallbackWorld.mc': 'FallbackWorld-before.mc.txt',
        'watchface/source/generated/NativeVersion.mc': 'NativeVersion-before.mc.txt',
    }
    old_dir = 'openspec/changes/spacefox-watchface/evidence/performance021/integration/stock-024-first-red/'
    for name, digest in build['sourceHashes'].items():
        checked(root, old_dir + old_sources[name] if name in old_sources else name, digest)
    fixture = checked(root, record['currentFixture']['path'], record['currentFixture']['sha256'])
    test = checked(root, record['currentTest']['path'], record['currentTest']['sha256'])
    checked(root, record['currentRestore']['path'], record['currentRestore']['sha256'])
    if sha(fixture) != build['fixtureArchiveSha256'] or sha(test) != build['testSourceSha256']:
        raise ValueError('combined current SDK fixture or test differs')
    restored = json.loads((root / record['currentRestore']['path']).read_text())
    if not restored['restored'] or not restored['ini']:
        raise ValueError('combined current SDK runtime restoration differs')
    packed_cases = {'peer024WorldAndDownloadedOwnership', 'b2AdmittedFactsWithoutArt',
        'b2LowUnmatchedPoint', 'b1ColdAcquisition', 'b1LowHeapDefersOptionalDecode',
        'b1RealDecodeTicksAndCancels', 'b1CapturedSuccessorTicksInFallback',
        'b3DisplayRetainedSelection'}
    if set(record['packedNative']) != packed_cases:
        raise ValueError('packed current SDK case inventory differs')
    for name, item in record['packedNative'].items():
        log = checked(root, item['path'], item['sha256']).read_text()
        if parse_output(log, item['rawExit'], (name,))['status'] != 'passed':
            raise ValueError('packed current SDK case failed: ' + name)
    for prefix in ('packed', 'packedBatch'):
        packed_build = json.loads(checked(root, record[prefix + 'Build']['path'], record[prefix + 'Build']['sha256']).read_text())
        packed_program = checked(root, record[prefix + 'Program']['path'], record[prefix + 'Program']['sha256'])
        if hashlib.sha256(gzip.decompress(packed_program.read_bytes())).hexdigest() != packed_build['programSha256']:
            raise ValueError('packed current SDK program differs')
        if set(packed_build['sourceHashes']) != set(build['sourceHashes']):
            raise ValueError('packed SDK source inventory differs')
        for name, digest in packed_build['sourceHashes'].items():
            checked(root, name, digest)
        packed_restore = json.loads(checked(root, record[prefix + 'Restore']['path'], record[prefix + 'Restore']['sha256']).read_text())
        if not packed_restore['restored'] or not packed_restore['ini']:
            raise ValueError('packed SDK runtime restoration differs')
        if prefix == 'packed':
            if (packed_build['fixtureArchiveSha256'] != sha(fixture) or
                packed_build['testSourceSha256'] != sha(test)):
                raise ValueError('packed current SDK fixture or test differs')
        else:
            for suffix, field in (('Test', 'testSourceSha256'), ('Fixture', 'fixtureArchiveSha256')):
                item = record[prefix + suffix]
                if sha(checked(root, item['path'], item['sha256'])) != packed_build[field]:
                    raise ValueError('packed batch fixture or test differs')
    batch = checked(root, record['packedBatchLog']['path'], record['packedBatchLog']['sha256']).read_text()
    if (parse_output(batch, 1, ('integrationBatchCorruptPrefixBeforeCompletion',))['status'] != 'passed' or
        'terminalScanRefused=true repaired=true acceptedAndRasterUnchanged=true' not in batch):
        raise ValueError('current terminal corruption/repair failed')
    stock = record['packedStock']
    required_stock = {'active-region.png', 'low-region.png', 'wake-region.png',
        'check-readiness.py', 'frame-003.png', 'frame-012.png', 'frame-054.png',
        'gate.json', 'memory-observation.json', 'restore.json', 'seed.log',
        'seed.prg.gz', 'stock.prg.gz', 'samples.json', 'rebase.json', 'build.json', 'fixtures.tar.gz'}
    if not required_stock <= set(stock):
        raise ValueError('packed stock readiness evidence missing')
    stock_paths = {name: checked(root, item['path'], item['sha256']) for name, item in stock.items()}
    gate = json.loads(stock_paths['gate.json'].read_text())
    stock_build = json.loads(stock_paths['build.json'].read_text())
    if (stock_build['sourceHashes'] != packed_build['sourceHashes'] or
        stock_build['fixtureArchiveSha256'] != sha(stock_paths['fixtures.tar.gz'])):
        raise ValueError('packed stock source or fixture differs')
    for kind in ('seed', 'stock'):
        if hashlib.sha256(gzip.decompress(stock_paths[kind + '.prg.gz'].read_bytes())).hexdigest() != gate[kind + 'Sha256']:
            raise ValueError('packed stock program differs')
    restored = json.loads(stock_paths['restore.json'].read_text())
    if not restored['restored'] or not restored['ini']:
        raise ValueError('packed stock runtime restoration differs')
    incident_build = json.loads(checked(root, record['currentIncidentBuild']['path'],
                                        record['currentIncidentBuild']['sha256']).read_text())
    incident_program = checked(root, record['currentIncidentProgram']['path'],
                               record['currentIncidentProgram']['sha256'])
    if hashlib.sha256(gzip.decompress(incident_program.read_bytes())).hexdigest() != incident_build['packageSha256']:
        raise ValueError('combined current incident program differs')
    for name in ('watchface/incident-tests/DeliveryContinuityTests.mc', 'watchface/source/SceneRenderer.mc',
                 'watchface/source/FeedScene.mc', 'watchface/source/NativeForegroundCache.mc'):
        checked(root, name, incident_build['inputHashes'][name])
    incident_names = {'deliveryBundledFallbackTransitions', 'deliveryWarmLayoutIdentity',
                      'deliveryRawProjectionIntegrity'}
    if set(record['currentIncident']) != incident_names:
        raise ValueError('combined current incident case inventory differs')
    for name, item in record['currentIncident'].items():
        log = checked(root, item['path'], item['sha256']).read_text()
        if parse_output(log, item['rawExit'], (name,))['status'] != 'passed':
            raise ValueError('combined current incident case failed: ' + name)
    restored = json.loads(checked(root, record['currentIncidentRestore']['path'],
                                  record['currentIncidentRestore']['sha256']).read_text())
    if not restored['restored'] or not restored['ini']:
        raise ValueError('combined current incident restoration differs')
    from tools.generate_native_version import validate as validate_version
    validate_version(root)
    locales = None
    for side in ('performance', 'runtime'):
        recipe = record['historical'][side]
        expected_parent = {'performance': 'f955c6022ddabeb0153b71006ae1fa4bba4ad179',
                           'runtime': 'c222b705f2ad7deff86e6d49f39119baa0748f3f'}
        if recipe['revision'] != expected_parent[side]:
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
