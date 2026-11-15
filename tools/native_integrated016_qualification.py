"""Bridge both immutable software-qualification histories to candidate 0.1.16.

Historical validators run against exact reconstructed parent inputs. The bridge
binds the integrated source and records a separately executed decoder seam; it
makes no device, package signing, or publication claim.
"""
import hashlib
import gzip
import io
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def _read(root, ref):
    name = Path(ref['path'])
    if name.is_absolute() or '..' in name.parts:
        raise ValueError('invalid integrated016 proof path')
    data = (root / name).read_bytes()
    if digest(data) != ref['sha256']:
        raise ValueError('integrated016 evidence changed: ' + str(name))
    return data


def _record(root, catalog):
    proof = catalog['supportPolicy']['softwareQualificationProof']
    return json.loads(_read(root, proof['integrated016Proof']))


def _snapshot(root, spec):
    inventory = json.loads(_read(root, spec['inventory']))
    with tarfile.open(fileobj=io.BytesIO(_read(root, spec['delta'])), mode='r:gz') as tar:
        members = tar.getmembers()
        names = [member.name for member in members]
        if len(names) != len(set(names)) or any(not member.isfile() or member.name not in inventory for member in members):
            raise ValueError('invalid historical source archive')
        delta = {member.name: tar.extractfile(member).read() for member in members}
    def source(name):
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or path.parts[0] not in ('watchface', 'locales', 'tools', 'tests'):
            raise ValueError('invalid historical source name')
        data = delta[name] if name in delta else (root / path).read_bytes()
        if digest(data) != inventory[name]:
            raise ValueError('historical source changed: ' + name)
        return data
    return inventory, source


def historical_input(root, name, expected):
    root = Path(root).resolve()
    path = root / name
    if path.is_file() and digest(path.read_bytes()) == expected:
        return path.read_bytes()
    catalog = json.loads((root / 'locales/catalog.json').read_bytes())
    record = _record(root, catalog)
    inventory, source = _snapshot(root, record['parents']['display04'])
    if inventory.get(name) != expected:
        raise ValueError('DISPLAY04 historical source identity differs: ' + name)
    return source(name)


def validate(root, catalog):
    from tools.generate_native_version import validate as validate_version
    from tools.native_display03_probe import inputs
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    record = _record(root, catalog)
    if record['scope'] != 'integrated-0.1.16-primary-software':
        raise ValueError('unexpected integrated016 scope')
    prior = json.loads(_read(root, record['mainCatalog']))
    compare = json.loads(json.dumps(catalog))
    compare['supportPolicy']['softwareQualificationProof'].pop('integrated016Proof')
    if compare != prior:
        raise ValueError('integrated016 catalog differs beyond proof')
    if record['nativeInputs'] != inputs(root):
        raise ValueError('integrated016 native closure changed')
    validate_version(root)
    for name, expected, message in (('menu-warning-glyphs.json', '6468fa659cc0ad18b2fdb99375ea7ec4ffa214b619f927a752a4dfafaca306a8', 'rejection menu glyph observation changed'), ('run.log', '10be30feb2c55fabe58fffc5d6f87f6bda27bffa7e0f363315e5851ae160a2f0', 'rejection menu observation changed')):
        if digest((root / 'openspec/changes/spacefox-watchface/evidence/release-update-native' / name).read_bytes()) != expected:
            raise ValueError(message)
    if 'stockReady' not in record:
        raise ValueError('integrated016 stock READY observation pending')
    ready = record['stockReady']
    pre = json.loads(_read(root, ready['precompile']))
    for name, expected in pre['sourceInputs'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or digest((root / path).read_bytes()) != expected:
            raise ValueError('integrated016 stock source changed: ' + name)
    required = {str(p.relative_to(root)) for directory in ('watchface/source', 'watchface/resources', 'watchface/resources-rus') for p in (root / directory).rglob('*') if p.is_file()}
    if required != set(pre['sourceInputs']):
        raise ValueError('integrated016 stock source inventory changed')
    report = json.loads(_read(root, ready['observation']))
    if report['result'] != 'READY' or report['nativeId'] != 'e513cc6d' or report['fixture'] != 'offline-cape-seeded':
        raise ValueError('integrated016 stock READY observation invalid')
    if digest(gzip.decompress(_read(root, ready['program']))) != report['programSha256']:
        raise ValueError('integrated016 stock program changed')
    if digest(_read(root, ready['manifest'])) != pre['manifest'] or digest(_read(root, ready['jungle'])) != pre['jungle']:
        raise ValueError('integrated016 stock generated inputs changed')
    if not _read(root, ready['image']).startswith(b'\x89PNG\r\n\x1a\n'):
        raise ValueError('integrated016 stock READY image invalid')
    _read(root, ready['compileLog'])
    seed_manifest = json.loads(_read(root, ready['seedManifest']))
    with tarfile.open(fileobj=io.BytesIO(_read(root, ready['seedArchive'])), mode='r:gz') as archive:
        files = archive.getmembers()
        expected_seed = {row['path']: row['sha256'] for row in seed_manifest}
        if len(files) != len(expected_seed) or {item.name for item in files} != set(expected_seed) or any(not item.isfile() for item in files):
            raise ValueError('integrated016 stock seed inventory changed')
        for item in files:
            if digest(archive.extractfile(item).read()) != expected_seed[item.name]:
                raise ValueError('integrated016 stock seed changed: ' + item.name)

    for item in record['supportInputs']:

        _read(root, item)
    for row in record['nativeChecks']:
        receipt = json.loads(_read(root, row['receipt']))
        log = _read(root, row['log']).decode()
        package = gzip.decompress(_read(root, row['program']))
        if digest(package) != receipt['packageSha256']:
            raise ValueError('integrated016 native program differs')
        old = receipt['inputHashes']
        current = record['nativeInputs']
        changes = {name for name in old.keys() | current.keys() if old.get(name) != current.get(name)}
        if changes:
            prior = row.get('placementPrior', {})
            if changes != set(prior):
                raise ValueError('integrated016 native execution inputs differ')
            for name in changes:
                before = _read(root, prior[name]).decode()
                if digest(before.encode()) != old[name]:
                    raise ValueError('retained placement source differs: ' + name)
                if name.endswith('/FeedService.mc'):
                    after = before.replace('(:background)\nclass FeedService', '(:background, :extendedCode)\nclass FeedService').replace('(:background, :typecheck(false))\nfunction armFeed', '(:background, :extendedCode, :typecheck(false))\nfunction armFeed')
                elif name.endswith('/LaunchReminder.mc'):
                    after = before.replace('(:background, :typecheck(false))\nmodule LaunchReminder', '(:background, :extendedCode, :typecheck(false))\nmodule LaunchReminder')
                elif name.endswith('/NativeFeed.mc'):
                    after = before.replace('(:typecheck(false))\nclass NativeFeed', '(:extendedCode, :typecheck(false))\nclass NativeFeed').replace('(:typecheck(false))\nclass NativeCachedPacket', '(:extendedCode, :typecheck(false))\nclass NativeCachedPacket').replace('    function reminderProjection(){', '    (:extendedCode) function reminderProjection(){')
                elif name.endswith('/NativeVersion.mc'):
                    after = re.sub(r'const ID = "[0-9a-f]{8}"', 'const ID = "e513cc6d"', before)
                else:
                    raise ValueError('unexpected native placement delta: ' + name)
                if after == before or digest(after.encode()) != current[name]:
                    raise ValueError('unqualified native placement delta: ' + name)
        if parse_output(log, receipt['rawExit'], tuple(row['names']))['status'] != 'passed':
            raise ValueError('integrated016 native test did not pass')
    reminder = record['reminder']
    reminder_binding = json.loads(_read(root, reminder['binding']))
    for name, expected in reminder_binding['inputs'].items():
        if digest((root / name).read_bytes()) != expected:
            raise ValueError('integrated016 reminder source changed: ' + name)
    reminder_log = _read(root, reminder['log']).decode()
    if digest(reminder_log.encode()) != reminder_binding['logSha256']:
        raise ValueError('integrated016 reminder log changed')
    from tests.test_launch_reminders import NAMES as reminder_names
    if parse_output(reminder_log, reminder_binding['rawExit'], reminder_names)['status'] != 'passed':
        raise ValueError('integrated016 reminder SDK result incomplete')
    if digest(gzip.decompress(_read(root, reminder['program']))) != reminder['programSha256']:
        raise ValueError('integrated016 reminder program changed')
    reminder_pre = json.loads(_read(root, reminder['precompile']))
    for name, expected in reminder_pre['inputs'].items():
        if digest((root / name).read_bytes()) != expected:
            raise ValueError('integrated016 reminder compiled input changed: ' + name)
    generated = Path(reminder['precompile']['path']).parent
    for name, expected in reminder_pre['generated'].items():
        if digest((root / generated / name).read_bytes()) != expected:
            raise ValueError('integrated016 reminder generated input changed: ' + name)
    _read(root, reminder['compileLog'])
    # Validate the original chains in isolated source trees. No original proof,
    # receipt, catalog, or captured source is modified or renamed.
    for label, module in (('display04', 'tools.native_display04_requalification'),
                          ('main015', 'tools.native_reminder_qualification')):
        inventory, source = _snapshot(root, record['parents'][label])
        with tempfile.TemporaryDirectory(prefix='spacefox-integrated016-') as tmp:
            target = Path(tmp)
            for name in inventory:
                path = target / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(source(name))
            for folder in ('openspec', 'corpus', 'assets', 'catalog', 'schemas', 'prototype'):
                (target / folder).symlink_to(root / folder, target_is_directory=True)
            code = ('import json;from pathlib import Path;from '+module+' import validate;'
                    'p=Path.cwd();c=json.loads((p/"locales/catalog.json").read_text());'
                    'assert validate(p,c)==c["supportPolicy"]["softwareQualifiedLocales"]')
            result = subprocess.run([sys.executable, '-B', '-c', code], cwd=target,
                                    env=dict(os.environ, PYTHONPATH=str(target), PYTHONDONTWRITEBYTECODE='1'),
                                    capture_output=True, text=True, timeout=360)
            if result.returncode:
                raise ValueError(label + ' original qualification failed: ' + result.stderr[-3000:])
    return catalog['supportPolicy']['softwareQualifiedLocales']
