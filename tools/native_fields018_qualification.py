"""Bind fields018 admission to the authenticated 0.1.17 parent and new evidence."""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

PARENT_SHA = '187c7a23fe2f87a5cf25a5ea9e4e16730d362e1ac6d01c6afd08b04353167be6'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(root, ref):
    path = Path(ref['path'])
    if path.is_absolute() or '..' in path.parts:
        raise ValueError('invalid fields018 proof path')
    resolved = (root / path).resolve()
    if not resolved.is_relative_to(root) or not resolved.is_file():
        raise ValueError('fields018 proof input unavailable: ' + str(path))
    data = resolved.read_bytes()
    if sha(data) != ref['sha256']:
        raise ValueError('fields018 proof input changed: ' + str(path))
    return data

def validate(root, catalog):
    from tools.generate_native_version import validate as validate_version
    from tools.fields018_native_probe import inputs, NAMES
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    record = json.loads(read(root, proof['fields018Proof']))
    if record['scope'] != 'fields-0.1.18-primary-software':
        raise ValueError('wrong fields018 admission scope')
    parent = gzip.decompress(read(root, record['parentReceipt']))
    if sha(parent) != PARENT_SHA:
        raise ValueError('published 0.1.17 receipt differs')
    inventory = json.loads(parent)['source_inputs_sha256']
    with tarfile.open(fileobj=io.BytesIO(read(root, record['parentDelta'])), mode='r:gz') as archive:
        members = archive.getmembers()
        if len({m.name for m in members}) != len(members) or any(not m.isfile() or m.name not in inventory for m in members):
            raise ValueError('invalid published parent delta')
        delta = {m.name: archive.extractfile(m).read() for m in members}
    with tempfile.TemporaryDirectory(prefix='spacefox-018-parent-') as temporary:
        target = Path(temporary)
        for name, expected in inventory.items():
            path = Path(name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('invalid parent source path')
            src = root / path
            data = delta.get(name)
            if data is None:
                data = src.read_bytes()
            if sha(data) != expected:
                raise ValueError('published 0.1.17 source differs: ' + name)
            dst = target / path
            dst.parent.mkdir(parents=True, exist_ok=True)
            if name not in delta:
                try:
                    os.link(src, dst)
                    continue
                except OSError:
                    pass
            dst.write_bytes(data)
        prior = json.loads((target / 'locales/catalog.json').read_text())
        current = json.loads(json.dumps(catalog))
        current['supportPolicy']['softwareQualificationProof'].pop('fields018Proof')
        if current != prior:
            raise ValueError('fields018 catalog differs beyond proof')
        command = [sys.executable, '-c', 'import json; from pathlib import Path; from tools.native_rollover017_qualification import validate; p=Path.cwd(); print(json.dumps(validate(p,json.loads((p/"locales/catalog.json").read_text()))))']
        run = subprocess.run(command, cwd=target, env={**os.environ, 'PYTHONPATH':str(target)}, capture_output=True, text=True)
        if run.returncode:
            raise ValueError('published 0.1.17 admission failed: ' + run.stderr[-3000:])
        qualified = json.loads(run.stdout.strip().splitlines()[-1])
    if qualified != catalog['supportPolicy']['softwareQualifiedLocales']:
        raise ValueError('parent locales differ')
    validate_version(root)
    if record['nativeInputs'] != inputs():
        raise ValueError('fields018 native closure changed')
    files = {name: read(root, ref) for name, ref in record['evidence'].items()}
    font = json.loads(files['fontReport'])
    if font['status'] != 'passed' or {row['locale'] for row in font['rows']} != {'en','ru','de','fr','es'} or any(row['missingCodepoints'] for row in font['rows']):
        raise ValueError('fields018 primary font report differs')
    for name, expected in font['inputs'].items():
        if sha((root / name).read_bytes()) != expected:
            raise ValueError('fields018 font input changed: ' + name)
    if sha((root / 'tools/native_fields018_qualification.py').read_bytes()) != record['validatorSha256']:
        raise ValueError('fields018 validator changed')
    for profile in ('fr165', 'fr170'):
        receipt = json.loads(files[profile+'Receipt'])
        if receipt['profile'] != profile or receipt['compileExit'] != 0 or not receipt['inputsUnchanged'] or receipt['inputHashes'] != record['nativeInputs']:
            raise ValueError('fields018 native input binding differs')
        if sha(gzip.decompress(files[profile+'Program'])) != receipt['packageSha256']:
            raise ValueError('fields018 native program differs')
        if receipt['rawExit'] != 1 or parse_output(files[profile+'Log'].decode(), receipt['rawExit'], NAMES)['status'] != 'passed':
            raise ValueError('fields018 native test failed')
    from tools.fields018_extra_probe import inputs as extra_inputs, NAMES as EXTRA_NAMES
    extra = json.loads(files['emptyReceipt'])
    if (extra['profile'] != 'fr165' or extra['compileExit'] != 0 or not extra['inputsUnchanged']
            or extra['inputHashes'] != extra_inputs() or extra['rawExit'] != 1
            or sha(gzip.decompress(files['emptyProgram'])) != extra['packageSha256']
            or parse_output(files['emptyLog'].decode(), extra['rawExit'], EXTRA_NAMES)['status'] != 'passed'):
        raise ValueError('fields018 empty selection evidence differs')
    # Reconcile all 25 DISPLAY03 identities. The first 12 selected cases
    # retain ten passes and two preserved errors; the next eight retain seven
    # passes and one error. Those three errors have direct focused reruns.
    from tools.native_display03_probe import NAMES as ALL_DISPLAY_NAMES
    groups = {
        'display03-red': {'display03ForegroundReloadDuringBuild', 'display03CurrentBodyBatteryLifecycle'},
        'display03-green': set(),
        'display03-extra-red': {'display03FailedSameDigestRetry'},
        'display03-extra-green': set(),
    }
    observed_groups = {}
    for case, errors in groups.items():
        refs = record['displayFiles'][case]
        artifacts = {name: read(root, ref) for name, ref in refs.items()}
        receipt = json.loads(artifacts['receipt.json']); pre = json.loads(artifacts['precompile.json'])
        if pre['inputHashes'] != receipt['inputHashes'] or sha(gzip.decompress(artifacts['program.prg.gz'])) != receipt['packageSha256']:
            raise ValueError('fields018 display program binding differs')
        for name, expected in pre['generatedInputs'].items():
            if name not in artifacts or sha(artifacts[name]) != expected:
                raise ValueError('fields018 display generated input differs: ' + name)
        for name, expected in receipt['inputHashes'].items():
            snapshot = Path(name).name + '.input.txt'
            data = artifacts[snapshot] if snapshot in artifacts else (root / name).read_bytes()
            if sha(data) != expected:
                raise ValueError('fields018 display source differs: ' + name)
        names = tuple(receipt['tests']['expected_tests']); raw = artifacts['native.log'].decode()
        parsed = parse_output(raw, receipt['rawExit'], names)
        if receipt['rawExit'] != 1 or parsed['observed_tests'] != {name: ('ERROR' if name in errors else 'PASS') for name in names}:
            raise ValueError('fields018 display observed table differs: ' + case)
        if not errors and parsed['status'] != 'passed':
            raise ValueError('fields018 display focused rerun failed: ' + case)
        observed_groups[case] = set(names)
    first = observed_groups['display03-red']; extra = observed_groups['display03-extra-red']
    if len(first) != 12 or len(extra) != 8 or first & extra or observed_groups['display03-green'] != groups['display03-red'] or observed_groups['display03-extra-green'] != groups['display03-extra-red']:
        raise ValueError('fields018 affected display inventory differs')
    # The subsequent shared-render and code-paging repair invalidated sixteen
    # lifecycle/render cases. Both tables came from the same current binary.
    from tools.native_display03_probe import inputs as display_inputs
    live = {name: read(root, ref) for name, ref in record['lifecycleFiles'].items()}
    current = json.loads(live['receipt.json']); pre = json.loads(live['precompile.json'])
    if current['inputHashes'] != display_inputs(root) or pre['inputHashes'] != current['inputHashes'] or sha(gzip.decompress(live['program.prg.gz'])) != current['packageSha256']:
        raise ValueError('fields018 current lifecycle source or binary differs')
    for name, expected in pre['generatedInputs'].items():
        if name not in live or sha(live[name]) != expected:
            raise ValueError('fields018 current lifecycle fixture differs: ' + name)
    refreshed = set()
    for filename, logname in [('receipt.json','native.log'),('additional-receipt.json','additional-native.log')]:
        receipt = json.loads(live[filename]); names = tuple(receipt['tests']['expected_tests'])
        parsed = parse_output(live[logname].decode(), receipt['rawExit'], names)
        if receipt['rawExit'] != 1 or parsed['status'] != 'passed' or refreshed.intersection(names):
            raise ValueError('fields018 current lifecycle result differs')
        refreshed.update(names)
    required = {'display03RepeatedLowCallbacks','display03SleepThenHighObservation','display03WakeThenLowObservation','display03CausalSequence','display03ReadyAndErrorOnWake','display03FailedSameDigestRetry','display03WarmAodResources','display03MetricRolesAndAge','display03OffStopsWork','display03ForegroundReloadDuringBuild','display03BackgroundBeforeFrame','display03SameBatchJob','display03SameSceneRefreshKeepsJob','display03CurrentBodyBatteryLifecycle','display03LowDoesNotSample','display03LocaleResume'}
    if refreshed != required:
        raise ValueError('fields018 current lifecycle inventory differs')
    import re
    retained = record['retainedDisplay']
    if len(retained) != 5 or set(ALL_DISPLAY_NAMES) != first | extra | set(retained):
        raise ValueError('fields018 complete display inventory differs')
    for name, ref in retained.items():
        if inventory.get(ref['path']) != ref['sha256']:
            raise ValueError('fields018 retained display evidence is not parent-bound')
        raw = read(root, ref).decode()
        if not re.search(r'^' + re.escape(name) + r'\s+PASS$', raw, re.MULTILINE):
            raise ValueError('fields018 retained display case missing: ' + name)
    for dimension, profile in ((390,'fr165m'), (454,'fr965')):
        prefix = 'stock'+str(dimension)
        observed = json.loads(files[prefix+'Observation'])
        seed = json.loads(files[prefix+'Gate'])
        restore = json.loads(files[prefix+'Restore'])
        if observed['nativeId'] != record['nativeId'] or observed['version'] != '0.1.18' or observed['profile'] != profile or observed['dimensions'] != [dimension,dimension] or observed['peakKiB'] > observed['limitKiB'] or observed['currentKiB'] > observed['limitKiB']:
            raise ValueError('fields018 stock observation differs')
        if not observed['downloadedBitmapMapAndFlagNonNull'] or not observed['cacheReady'] or observed['selectedActualComplicationTypes'] != [4,5,6,8] or observed['upcomingIds'] != ['ll2:launch:76617033-4dc0-4448-b50c-e5b0d5a18539', 'll2:launch:0f867f0c-5422-4d44-93b8-d7faaae7019b']:
            raise ValueError('fields018 stock predicates missing')
        if sha(gzip.decompress(files[prefix+'Program'])) != observed['stockProgramSha256']:
            raise ValueError('fields018 stock program differs')
        import struct
        image = files[prefix+'Image']
        if not image.startswith(b'\x89PNG\r\n\x1a\n') or struct.unpack('>II', image[16:24]) != (dimension, dimension):
            raise ValueError('fields018 stock image missing')
        if not restore['restored'] or restore['files'] != 563 or not restore['ini']:
            raise ValueError('fields018 lane not restored')
        log = files[prefix+'SeedLog'].decode()
        if 'PASSED (passed=1, failed=0, errors=0)' not in log or 'SELECTED_ACTUAL_TYPES 4,5,6,8' not in log or 'FUTURE_SEED' not in log or seed['actualTypes'] != [4,5,6,8] or not seed['fixtureUrl'] or seed['ble'] != 2:
            raise ValueError('fields018 stock seed invalid')
        with tarfile.open(fileobj=io.BytesIO(files[prefix+'Seed']), mode='r:gz') as archive:
            members = archive.getmembers()
            if {m.name for m in members} != set(seed['hashes']) or any(not m.isfile() for m in members):
                raise ValueError('fields018 seed inventory differs')
            for member in members:
                if sha(archive.extractfile(member).read()) != seed['hashes'][member.name]:
                    raise ValueError('fields018 seed differs')
    return qualified
