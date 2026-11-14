"""Replay the existing FR165 language proof with a bounded device-build delta.

This preserves the original observation boundary: it does not claim that a
new device has been observed or that compilation proves on-device rendering.
"""
import base64
import copy
import difflib
import hashlib
import json
from pathlib import Path
import shutil
import tempfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root, catalog):
    from tools.native_bootstrap_requalification import validate as prior_validate
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    def checked(name, sha256):
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or not (root / p).is_file() or sha(root / p) != sha256:
            raise ValueError('device delta proof input changed: ' + name)
        return root / p
    ref = proof['deviceDeltaProof']
    record = json.loads(checked(ref['path'], ref['sha256']).read_text())
    prior = json.loads(checked(**record['priorCatalog']).read_text())
    old = prior['supportPolicy']['softwareQualificationProof']
    if set(proof) != set(old) | {'deviceDeltaProof'} or any(proof[k] != old[k] for k in old if k != 'productionSources'):
        raise ValueError('prior language proof metadata changed')
    comparable = copy.deepcopy(catalog)
    comparable['supportPolicy']['softwareQualificationProof'] = old
    if comparable != prior:
        raise ValueError('catalog outside device delta changed')
    changed = {'tools/build_watchface.py', 'tools/native_language_policy.py', 'watchface/toolchain-lock.json'}
    sources = proof['productionSources']
    if set(sources) != set(old['productionSources']) or {n for n in sources if sources[n] != old['productionSources'][n]} != changed:
        raise ValueError('unexpected language source delta')
    for name, digest in sources.items():
        checked(name, digest)
    for name in changed:
        item = record['historical'][name]
        previous = checked(**item)
        if sha(previous) != old['productionSources'][name]:
            raise ValueError('historical source differs: ' + name)
        patch = ''.join(difflib.unified_diff(previous.read_text().splitlines(keepends=True),
                                            (root / name).read_text().splitlines(keepends=True),
                                            fromfile='prior/' + name, tofile='current/' + name))
        if patch != base64.b64decode(checked(**record['patches'][name]).read_bytes(), validate=True).decode():
            raise ValueError('unreviewed source delta: ' + name)
    with tempfile.TemporaryDirectory(prefix='spacefox-device-prior-') as tmp:
        oldroot = Path(tmp)
        for folder in ('watchface', 'locales', 'tools'):
            shutil.copytree(root / folder, oldroot / folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for folder in ('openspec', 'corpus', 'tests', 'assets', 'catalog', 'schemas'):
            (oldroot / folder).symlink_to(root / folder, target_is_directory=True)
        for name in changed:
            shutil.copyfile(root / record['historical'][name]['name'], oldroot / name)
        qualified = prior_validate(oldroot, prior)
        if qualified != prior['supportPolicy']['softwareQualifiedLocales']:
            raise ValueError('retained FR165 qualification failed')
    return qualified
