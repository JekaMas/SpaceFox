"""Preserve UX03 admission while binding the measured immutable-cache port.

Prior visuals and cache probes retain their original source boundaries. This
validator does not claim a current device or phone observation.
"""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate(root, catalog):
    from tools.native_ux03_requalification import validate as previous_validate
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']

    def checked(row):
        path = Path(row['path'])
        if path.is_absolute() or '..' in path.parts or not (root / path).is_file() or digest(root / path) != row['sha256']:
            raise ValueError('cache port proof input changed: ' + str(path))
        return root / path

    record = json.loads(checked(proof['cachePortDeltaProof']).read_text())
    if record['scope'] != 'public-ux03-cache-port' or record['status'] != 'passed':
        raise ValueError('cache port proof incomplete')
    prior = json.loads(checked(record['priorCatalog']).read_text())
    oldproof = prior['supportPolicy']['softwareQualificationProof']
    if {k: v for k, v in proof.items() if k != 'cachePortDeltaProof'} != oldproof:
        raise ValueError('prior UX03 proof changed')
    comparable = json.loads(json.dumps(catalog))
    comparable['supportPolicy']['softwareQualificationProof'] = oldproof
    if comparable != prior:
        raise ValueError('unrelated language policy changed')
    for row in record['sources'].values():
        checked(row)
    for row in record['evidence'].values():
        checked(row)
    baseline = json.loads(checked(oldproof['ux03DeltaProof']).read_text())
    replaced = set(record['priorSnapshots'])
    if replaced != {'watchface/source/NativeImmutable.mc', 'watchface/manifest.xml', 'tools/native_language_policy.py', 'watchface/source/generated/NativeVersion.mc'}:
        raise ValueError('unexpected cache port source changes')
    for name, expected in baseline['sources'].items():
        path = checked(record['priorSnapshots'][name]) if name in replaced else root / name
        if not path.is_file() or digest(path) != expected:
            raise ValueError('UX03 source outside cache port changed: ' + name)
    observed = json.loads(checked(record['cacheObservation']).read_text())
    if observed['scope'] != 'native-cache-budget-delta' or observed['status'] != 'passed':
        raise ValueError('cache observation incomplete')
    if observed['sources']['watchface/source/NativeImmutable.mc'] != digest(root / 'watchface/source/NativeImmutable.mc'):
        raise ValueError('cache implementation differs from measured source')
    if observed['priorSnapshots']['watchface/source/NativeImmutable.mc']['sourceSha256'] != digest(checked(record['priorSnapshots']['watchface/source/NativeImmutable.mc'])):
        raise ValueError('cache baseline differs from public source')
    for name, expected in observed['evidence'].items():
        if name not in record['evidence'] or record['evidence'][name]['sha256'] != expected:
            raise ValueError('cache observation evidence differs: ' + name)
    base = observed['base'] + '/'
    for subdir in ('abc', 'sdk-storage'):
        build = json.loads((root / base / subdir / 'build.json').read_text())
        if build['exitCode'] != 0 or build['productionSources']['watchface/source/NativeImmutable.mc'] != observed['sources']['watchface/source/NativeImmutable.mc']:
            raise ValueError('cache observed build mismatch')
        if build['probeSha256'] != digest(root / base / subdir / 'Probe.mc'):
            raise ValueError('cache probe changed')
    if b'ABC_COMPLETE stage=41 objects=50 scene=true recovery=true' not in (root / base / 'abc/stable-c.log').read_bytes():
        raise ValueError('cache activation observation missing')
    if b'STORAGE_COMPLETE entries=56 objectBytes=229376' not in (root / base / 'sdk-storage/final-r2.log').read_bytes():
        raise ValueError('cache storage observation missing')
    with tempfile.TemporaryDirectory(prefix='spacefox-public-cache-prior-') as tmp:
        target = Path(tmp)
        for folder in ('watchface', 'locales', 'tools', 'tests'):
            shutil.copytree(root / folder, target / folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for folder in ('openspec', 'corpus', 'assets', 'catalog', 'schemas'):
            (target / folder).symlink_to(root / folder, target_is_directory=True)
        for name, item in record['priorSnapshots'].items():
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(checked(item), destination)
        (target / 'locales/catalog.json').write_text(json.dumps(prior, indent=2) + '\n')
        if previous_validate(target, prior) != prior['supportPolicy']['softwareQualifiedLocales']:
            raise ValueError('retained UX03 proof failed')
    return catalog['supportPolicy']['softwareQualifiedLocales']
