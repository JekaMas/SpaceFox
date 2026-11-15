"""Reconstruct DISPLAY03 admission while binding the integrated settings owners."""
import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def validate(root, catalog):
    from tools.native_display03_probe import inputs
    from tools.generate_native_version import validate as validate_version
    from tools.run_native_tests import parse_output
    from tools.verify_current_ui_batch import verify_rejection_menu

    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']

    def read(item):
        path = Path(item['path'])
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('invalid integration proof path')
        raw = (root / path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('integration proof changed: ' + str(path))
        return base64.b64decode(raw, validate=False) if item.get('encoding') == 'base64' else raw

    record = json.loads(read(proof['integration13DeltaProof']))
    old = json.loads(read(record['priorCatalog']))
    prior_proof = old['supportPolicy']['softwareQualificationProof']
    if record['scope'] != 'display03-integration-0.1.13' or record['status'] != 'passed':
        raise ValueError('integration proof incomplete')
    if {k: v for k, v in proof.items() if k != 'integration13DeltaProof'} != prior_proof:
        raise ValueError('prior proof changed')
    comparable = json.loads(json.dumps(catalog))
    comparable['supportPolicy']['softwareQualificationProof'] = prior_proof
    if comparable != old:
        raise ValueError('unrelated catalog change')
    verify_rejection_menu(root)
    if record['nativeInputs'] != inputs(root):
        raise ValueError('integration native closure changed')
    for name, digest in record['supportInputs'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('integration support changed: ' + name)
    prior_record = json.loads(read(prior_proof['exactMapDeltaProof']))
    before, after = prior_record['nativeInputs'], record['nativeInputs']
    changed = {key for key in before.keys() | after.keys() if before.get(key) != after.get(key)}
    allowed = {'watchface/manifest.xml', 'watchface/source/generated/NativeVersion.mc',
               'watchface/source/SettingsMenu.mc', 'watchface/source/SettingsMenuText.mc'}
    if changed != allowed:
        raise ValueError('unexpected native integration changes: ' + repr(sorted(changed)))
    build = json.loads(read(record['settingsBuild']))
    log = read(record['settingsLog']).decode()
    if parse_output(log, 1, ('releaseCurrentHostSchema',))['status'] != 'passed':
        raise ValueError('incoming settings test failed')
    for name in ('watchface/source/SettingsMenu.mc', 'watchface/source/SettingsMenuText.mc'):
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != build['productionSources'][name]:
            raise ValueError('settings owner differs from incoming native test: ' + name)
    prior_manifest = read(record['priorSnapshots']['watchface/manifest.xml'])
    if prior_manifest.count(b'version="0.1.12"') != 1 or (root / 'watchface/manifest.xml').read_bytes() != prior_manifest.replace(b'version="0.1.12"', b'version="0.1.13"'):
        raise ValueError('manifest changed beyond version')
    validate_version(root)
    with tempfile.TemporaryDirectory(prefix='spacefox-integration-prior-') as tmp:
        target = Path(tmp)
        for folder in ('watchface', 'locales', 'tools', 'tests'):
            shutil.copytree(root / folder, target / folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for folder in ('openspec', 'corpus', 'assets', 'catalog', 'schemas'):
            (target / folder).symlink_to(root / folder, target_is_directory=True)
        for name, item in record['priorSnapshots'].items():
            path = target / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(read(item))
        for name in record['priorAbsent']:
            path = Path(name)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('invalid absent path')
            (target / path).unlink(missing_ok=True)
        # Isolate module imports: the incoming release validator differs from the
        # one that established the prior DISPLAY03 chain.
        code = ('import json; from pathlib import Path; '
                'from tools.native_exact_map_requalification import validate; '
                'p=Path.cwd(); c=json.loads((p/"locales/catalog.json").read_text()); '
                'assert validate(p,c)==c["supportPolicy"]["softwareQualifiedLocales"]')
        env = dict(os.environ, PYTHONPATH=str(target), PYTHONDONTWRITEBYTECODE='1')
        run = subprocess.run([sys.executable, '-B', '-c', code], cwd=target, env=env,
                             capture_output=True, text=True, timeout=180)
        if run.returncode:
            raise ValueError('prior DISPLAY03 reconstruction failed: ' + run.stderr[-3000:])
    return catalog['supportPolicy']['softwareQualifiedLocales']
