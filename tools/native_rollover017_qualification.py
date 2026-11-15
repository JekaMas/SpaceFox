"""Reconstruct immutable 0.1.16 admission and bind the 0.1.17 native delta."""
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

PARENT_SHA = '09e3ed20e5c7964b8d0907fe94a49c4c3ee8627bd82ab47fddfd07c2dbdd7ca7'
NAMES = ('queueSequence', 'successorNearWake', 'forwardJumpAndPending', 'sourcedAscentWindowAndReschedule', 'realStorageQueue', 'longIdentityCache')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def read(root, ref):
    name = Path(ref['path'])
    if name.is_absolute() or '..' in name.parts:
        raise ValueError('invalid rollover proof path')
    data = (root / name).read_bytes()
    if sha(data) != ref['sha256']:
        raise ValueError('rollover proof changed: ' + str(name))
    return data

def parent_input(root, name, expected):
    """Return only the receipt-authenticated published parent bytes, if matching."""
    root = Path(root).resolve()
    catalog = json.loads((root / 'locales/catalog.json').read_bytes())
    record = json.loads(read(root, catalog['supportPolicy']['softwareQualificationProof']['rollover017Proof']))
    parent = gzip.decompress(read(root, record['parentReceipt']))
    if sha(parent) != PARENT_SHA:
        raise ValueError('published parent receipt differs')
    if json.loads(parent)['source_inputs_sha256'].get(name) != expected:
        return None
    with tarfile.open(fileobj=io.BytesIO(read(root, record['parentDelta'])), mode='r:gz') as archive:
        try:
            member = archive.getmember(name)
        except KeyError:
            data = (root / name).read_bytes()
        else:
            if not member.isfile():
                raise ValueError('invalid parent source')
            data = archive.extractfile(member).read()
    if sha(data) != expected:
        raise ValueError('published parent source differs: ' + name)
    return data

def validate(root, catalog):
    from tools.generate_native_version import validate as validate_version
    from tools.native_display03_probe import inputs
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    record = json.loads(read(root, proof['rollover017Proof']))
    if record['scope'] != 'rollover-0.1.17-primary-software':
        raise ValueError('wrong rollover admission scope')
    parent = gzip.decompress(read(root, record['parentReceipt']))
    if sha(parent) != PARENT_SHA:
        raise ValueError('published parent receipt differs')
    inventory = json.loads(parent)['source_inputs_sha256']
    with tarfile.open(fileobj=io.BytesIO(read(root, record['parentDelta'])), mode='r:gz') as archive:
        members = archive.getmembers()
        if len({m.name for m in members}) != len(members) or any(not m.isfile() or m.name not in inventory for m in members):
            raise ValueError('invalid parent delta')
        delta = {m.name: archive.extractfile(m).read() for m in members}
    with tempfile.TemporaryDirectory(prefix='spacefox-017-parent-') as temporary:
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
                raise ValueError('published parent source differs: ' + name)
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
        current['supportPolicy']['softwareQualificationProof'].pop('rollover017Proof')
        if current != prior:
            raise ValueError('rollover catalog differs beyond proof')
        command = [sys.executable, '-c', 'import json; from pathlib import Path; from tools.native_integrated016_qualification import validate; p=Path.cwd(); print(json.dumps(validate(p,json.loads((p/"locales/catalog.json").read_text()))))']
        run = subprocess.run(command, cwd=target, env={**os.environ, 'PYTHONPATH':str(target)}, capture_output=True, text=True)
        if run.returncode:
            raise ValueError('published parent admission failed: ' + run.stderr[-3000:])
        qualified = json.loads(run.stdout.strip().splitlines()[-1])
    if qualified != catalog['supportPolicy']['softwareQualifiedLocales']:
        raise ValueError('parent locales differ')
    if record['nativeInputs'] != inputs(root):
        raise ValueError('rollover native closure changed')
    validate_version(root)
    files = {key: read(root, ref) for key, ref in record['evidence'].items()}
    build = json.loads(files['nativeBuild'])
    if build['exitCode'] != 0 or sha(gzip.decompress(files['nativeProgram'])) != build['packageSha256']:
        raise ValueError('rollover test program differs')
    for name, expected in {**build['productionSources'], **build['productionResources']}.items():
        if sha((root / name).read_bytes()) != expected:
            raise ValueError('rollover executed input changed: ' + name)
    if parse_output(files['nativeLog'].decode(), json.loads(files['nativeObservation'])['rawExit'], NAMES)['status'] != 'passed':
        raise ValueError('rollover native tests failed')
    photo = json.loads(files['photoBuild'])
    if photo['exitCode'] != 0 or sha(gzip.decompress(files['photoProgram'])) != photo['packageSha256'] or sha(files['photoProbe']) != photo['probeSha256']:
        raise ValueError('rollover photo program differs')
    for name, expected in {**photo['productionSources'], **photo['productionResources']}.items():
        if sha((root / name).read_bytes()) != expected:
            raise ValueError('rollover photo input changed: ' + name)
    if photo['probeResources']['packets.json'] != sha(files['nativePackets']) or photo['probeResources']['variants.json'] != sha(files['nativeVariants']):
        raise ValueError('rollover photo fixtures differ')
    if parse_output(files['photoLog'].decode(), json.loads(files['photoObservation'])['rawExit'], ('photoExactGreen',))['status'] != 'passed' or 'PHOTO_3584 Starship Starbase active=T- 00:40:16 low=T- 00:41' not in files['photoLog'].decode():
        raise ValueError('rollover exact photo witness failed')
    stock = json.loads(files['stockBuild'])
    observed = json.loads(files['stockObservation'])
    if stock['exitCode'] != 0 or sha(gzip.decompress(files['stockProgram'])) != stock['packageSha256'] or stock['packageSha256'] != observed['programSha256']:
        raise ValueError('rollover stock program differs')
    for name, expected in stock['sources'].items():
        if sha((root / name).read_bytes()) != expected:
            raise ValueError('rollover stock source changed: ' + name)
    if observed['result'] != 'READY' or observed['nativeId'] != 'cad2f4d3' or observed['memoryKiB'] > observed['limitKiB'] or observed['peakKiB'] > observed['limitKiB'] or len(observed['loadedSuccessorIds']) != 2 or observed['physicalDeviceObserved'] is not False:
        raise ValueError('rollover stock observation invalid')
    if not files['stockImage'].startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('rollover stock image invalid')
    for key in ('nativeLane', 'stockLane', 'photoLane'):
        lane = json.loads(files[key])
        if lane['files'] != 563 or not lane['hashes_restored'] or lane['owned_processes_remaining']:
            raise ValueError('rollover SDK lane not restored')
    pre = json.loads(files['stockPrelaunch'])
    with tarfile.open(fileobj=io.BytesIO(files['stockSeed']), mode='r:gz') as archive:
        members = archive.getmembers()
        if {m.name for m in members} != set(pre['changedDataFiles']) or any(not m.isfile() for m in members):
            raise ValueError('rollover seed inventory differs')
        for member in members:
            if sha(archive.extractfile(member).read()) != pre['changedDataFiles'][member.name]:
                raise ValueError('rollover seed differs')
    if pre['seedStatus'] != 'passed' or len(pre['fixtureUrlPresentIn']) != 2:
        raise ValueError('rollover seed not ready')
    return qualified
