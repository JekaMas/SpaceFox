"""Bind B3's focused observations to current native inputs and retained B2 proof."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from tools.native_b1_021_qualification import checked, native_inputs, sha, test_inputs
from tools.run_native_tests import parse_output
from tools.native_b2_022_qualification import validate as validate_prior

NATIVE_CHANGED = {'watchface/manifest.xml', 'watchface/source/generated/NativeVersion.mc',
    'watchface/source/SceneContext.mc', 'watchface/source/FeedScene.mc',
    'watchface/source/NativeUpcomingCache.mc', 'watchface/source/NativeForegroundApp.mc',
    'watchface/source/LaunchReminder.mc', 'watchface/source/LaunchReminderForeground.mc'}
SUPPORT_CHANGED = {'tools/native_language_policy.py', 'tools/release.py', 'tests/test_b1_021_admission.py'}
SNAPSHOTS = NATIVE_CHANGED | SUPPORT_CHANGED
REQUIRED_TESTS = {'b3QueueAndRollover', 'b3AdmissionAndUnknown', 'b3QuietProvider',
                  'b3OrdinaryReopen', 'b3RescheduleAndQuiet',
                  'b1LowHeapDefersOptionalDecode', 'b1ShortWakeResume'}
OWNERS = SUPPORT_CHANGED | {'tools/native_b3_023_qualification.py', 'tools/check_b3_evidence.py', 'watchface/runtime-b3-tests/B3Tests.mc'}

def run_prior(root, catalog, snapshots):
    with tempfile.TemporaryDirectory(prefix='spacefox-b3-prior-') as temporary:
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
        prior_catalog = json.loads(json.dumps(catalog))
        prior_catalog['supportPolicy']['softwareQualificationProof'].pop('b3Runtime023Proof')
        dst = target / 'locales/catalog.json'
        dst.unlink()
        dst.write_text(json.dumps(prior_catalog, indent=2, ensure_ascii=False) + '\n')
        command = ('import json;from pathlib import Path;'
                   'from tools.native_b2_022_qualification import validate;'
                   'p=Path.cwd();print(json.dumps(validate(p,json.loads((p/"locales/catalog.json").read_text()))))')
        result = subprocess.run([sys.executable, '-c', command], cwd=target,
                                env={**os.environ, 'PYTHONPATH': str(target)}, capture_output=True, text=True)
        if result.returncode:
            raise ValueError('original 0.1.22 proof failed: ' + result.stderr[-3000:])
        return json.loads(result.stdout.strip().splitlines()[-1])

def validate(root, catalog):
    from tools.generate_native_version import validate as validate_version
    root = Path(root).resolve()
    proofs = catalog['supportPolicy']['softwareQualificationProof']
    record = json.loads(checked(root, proofs['b3Runtime023Proof']).read_text())
    prior = json.loads(checked(root, proofs['b2Runtime022Proof']).read_text())
    if record['scope'] != 'b3-reminders-023-current-source' or record['version'] != '0.1.23':
        raise ValueError('wrong B3 scope/version')
    native = native_inputs(root)
    old = prior['nativeInputs']
    if native != record['nativeInputs'] or set(native) != set(old):
        raise ValueError('B3 native input closure changed')
    if {name for name in old if old[name] != native[name]} != NATIVE_CHANGED:
        raise ValueError('unexpected B3 native delta')
    tests = test_inputs(root)
    if tests != record['priorTestInputs'] or tests != prior['priorTestInputs']:
        raise ValueError('B3 prior test input closure changed')
    snapshots = record['priorSnapshots']
    if set(snapshots) != SNAPSHOTS:
        raise ValueError('B3 predecessor snapshot inventory changed')
    for name, ref in snapshots.items():
        expected = old.get(name) or prior['currentOwners'].get(name)
        if expected is None or ref['sha256'] != expected:
            raise ValueError('B3 predecessor snapshot differs from 0.1.22 proof: ' + name)
        checked(root, ref)
    if set(record['currentOwners']) != OWNERS:
        raise ValueError('B3 current owner inventory changed')
    for name, digest in record['currentOwners'].items():
        if sha(root / name) != digest:
            raise ValueError('B3 current owner changed: ' + name)
    validate_version(root)
    seen = set()
    for item in record['sdkCases']:
        if len(item['tests']) != 1 or item['tests'][0] in seen:
            raise ValueError('B3 SDK case inventory differs')
        seen.add(item['tests'][0])
        path = checked(root, item['log'])
        if parse_output(path.read_text(), item['rawExit'], tuple(item['tests']))['status'] != 'passed':
            raise ValueError('B3 SDK result incomplete: ' + str(path))
    if seen != REQUIRED_TESTS:
        raise ValueError('B3 SDK case inventory differs')
    qualified = run_prior(root, catalog, snapshots)
    if qualified != catalog['supportPolicy']['softwareQualifiedLocales']:
        raise ValueError('prior locale set differs')
    return qualified
