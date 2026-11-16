"""Bound current B2 source to original 0.1.21 proof and focused SDK results."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from tools.native_b1_021_qualification import checked, native_inputs, sha, test_inputs
from tools.run_native_tests import parse_output

BASE = 'openspec/changes/restore-fr165-runtime-guarantees/evidence/'
NATIVE_CHANGED = {'watchface/manifest.xml', 'watchface/source/SceneRenderer.mc',
                  'watchface/source/SpaceFoxView.mc', 'watchface/source/generated/NativeVersion.mc'}
NATIVE_ADDED = {'watchface/source/generated/FallbackWorld.mc'}
TEST_CHANGED = {'watchface/runtime-b1-tests/ClockFirst021.mc', 'watchface/runtime-b1-tests/DecodePending.mc'}
SUPPORT_CHANGED = {'tools/native_language_policy.py', 'tools/release.py',
                   'tests/test_b1_021_admission.py', 'tests/test_release_020_predecessor.py'}
SNAPSHOTS = NATIVE_CHANGED | TEST_CHANGED | SUPPORT_CHANGED
REQUIRED_TESTS = {'b2ArithmeticAndRetention', 'b2AdmittedFactsWithoutArt',
                  'b2FailedAndInterruptedReplacement', 'b2CapturedHourAndMissingPoint',
                  'b2RescheduleAndNewSelection',
                  'b2LowUnmatchedPoint', 'b2SourcedAscentRetention',
                  'b2CrossVmSeedInterrupted', 'b2CrossVmObserveRestored',
                  'b1CapturedSuccessorTicksInFallback', 'b1RealDecodeTicksAndCancels',
                  'b1LowHeapDefersOptionalDecode', 'b1ShortWakeResume'}


def run_prior(root, catalog, snapshots):
    with tempfile.TemporaryDirectory(prefix='spacefox-b2-prior-') as temporary:
        target = Path(temporary)
        for path in root.iterdir():
            if path.is_file():
                os.link(path, target / path.name)
        for name in ('tools', 'watchface', 'locales', 'openspec', 'tests', 'assets', 'corpus',
                     'catalog', 'schemas', 'docs', 'release', 'prototype', '.github', 'licenses'):
            source = root / name
            if source.is_dir():
                shutil.copytree(source, target / name, copy_function=os.link,
                                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name, ref in snapshots.items():
            destination = target / name
            destination.unlink(missing_ok=True)
            shutil.copyfile(root / ref['path'], destination)
        for name in NATIVE_ADDED:
            (target / name).unlink()
        prior_catalog = json.loads(json.dumps(catalog))
        prior_catalog['supportPolicy']['softwareQualificationProof'].pop('b2Runtime022Proof')
        dst = target / 'locales/catalog.json'
        dst.unlink()
        dst.write_text(json.dumps(prior_catalog, indent=2, ensure_ascii=False) + '\n')
        command = ('import json;from pathlib import Path;'
                   'from tools.native_b1_021_qualification import validate;'
                   'p=Path.cwd();print(json.dumps(validate(p,json.loads((p/"locales/catalog.json").read_text()))))')
        result = subprocess.run([sys.executable, '-c', command], cwd=target,
                                env={**os.environ, 'PYTHONPATH': str(target)}, capture_output=True, text=True)
        if result.returncode:
            raise ValueError('original 0.1.21 proof failed: ' + result.stderr[-3000:])
        return json.loads(result.stdout.strip().splitlines()[-1])


def validate(root, catalog):
    from tools.generate_native_version import validate as validate_version
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    record = json.loads(checked(root, proof['b2Runtime022Proof']).read_text())
    prior = json.loads(checked(root, proof['b1Integration021Proof']).read_text())
    if record['scope'] != 'b2-runtime-022-current-source' or record['version'] != '0.1.22':
        raise ValueError('wrong B2 scope/version')
    native = native_inputs(root)
    old = prior['nativeInputs']
    if native != record['nativeInputs'] or set(native)-set(old) != NATIVE_ADDED or set(old)-set(native):
        raise ValueError('B2 native input closure changed')
    if {name for name in old if old[name] != native[name]} != NATIVE_CHANGED:
        raise ValueError('unexpected B2 native delta')
    tests = test_inputs(root)
    if tests != record['priorTestInputs'] or set(tests) != set(prior['testInputs']):
        raise ValueError('B2 prior test input closure changed')
    if {name for name in tests if tests[name] != prior['testInputs'][name]} != TEST_CHANGED:
        raise ValueError('unexpected B2 prior test delta')
    snapshots = record['priorSnapshots']
    if set(snapshots) != SNAPSHOTS:
        raise ValueError('B2 predecessor snapshot inventory changed')
    for name, ref in snapshots.items():
        expected = old.get(name) or prior['testInputs'].get(name) or prior['owners'].get(name)
        if expected is None or ref['sha256'] != expected:
            raise ValueError('B2 predecessor snapshot differs from 0.1.21 proof: ' + name)
        checked(root, ref)
    if set(record['currentOwners']) != SUPPORT_CHANGED | {'tools/native_b2_022_qualification.py',
            'tools/build_fallback_world.py', 'tools/build_b2_test_resources.py',
            'tools/check_b2_evidence.py',
            'watchface/runtime-b2-tests/B2Tests.mc',
            'watchface/runtime-b2-tests/resources/B2Ascent.json',
            'watchface/runtime-b2-tests/resources/B2AscentCatalog.json',
            'watchface/runtime-b2-tests/resources/B2Initial.json',
            'watchface/runtime-b2-tests/resources/B2InitialCatalog.json',
            'watchface/runtime-b2-tests/resources/B2Moved.json',
            'watchface/runtime-b2-tests/resources/B2Different.json',
            'watchface/runtime-b2-tests/resources/B2DifferentCatalog.json',
            'watchface/runtime-b2-tests/resources/data.xml',
            'tests/fixtures/watch_refresh_cache/packets.json',
            'tests/fixtures/watch_refresh_cache/integrity.json',
            'tests/fixtures/basic_selected_scene/SelectedPackets.mc', 'catalog/world.json'}:
        raise ValueError('B2 current owner inventory changed')
    for name, digest in record['currentOwners'].items():
        if sha(root / name) != digest:
            raise ValueError('B2 current owner changed: ' + name)
    validate_version(root)
    seen = set()
    for item in record['sdkCases']:
        if len(item['tests']) != 1 or item['tests'][0] in seen:
            raise ValueError('B2 SDK case inventory differs')
        seen.add(item['tests'][0])
        path = checked(root, item['log'])
        if parse_output(path.read_text(), item['rawExit'], tuple(item['tests']))['status'] != 'passed':
            raise ValueError('B2 SDK result incomplete: ' + str(path))
    if seen != REQUIRED_TESTS:
        raise ValueError('B2 SDK case inventory differs')
    if set(record['frameEvidence']) != {'frame', 'probe', 'compile', 'run'}:
        raise ValueError('B2 frame evidence inventory differs')
    for ref in record['frameEvidence'].values():
        checked(root, ref)
    frame_log = checked(root, record['frameEvidence']['run']).read_text()
    if 'B2_FRAME admitted=ll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b target=1794609900 point=[-97.15799, 25.99677] age=1794551192 optionalAssets=0' not in frame_log:
        raise ValueError('B2 fallback frame lacks its admitted fact marker')
    runs = json.loads(checked(root, record['crossVmProcesses']).read_text())
    if (len(runs) != 2 or runs[0]['case'] != 'b2CrossVmSeedInterrupted' or
        runs[1]['case'] != 'b2CrossVmObserveRestored' or not all(r['ready'] for r in runs) or
        runs[0]['simulatorPid'] == runs[1]['simulatorPid'] or
        set(runs[0]['after']) != {'B2.DAT', 'B2.IDX'} or runs[0]['after'] != runs[1]['before']):
        raise ValueError('B2 SDK process restart/storage continuity differs')
    qualified = run_prior(root, catalog, snapshots)
    if qualified != catalog['supportPolicy']['softwareQualifiedLocales']:
        raise ValueError('prior locale set differs')
    return qualified
