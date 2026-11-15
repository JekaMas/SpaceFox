"""Reconstruct the reviewed UI input for a strictly version-only release delta.

The original observations remain bound to 0.1.10 inputs; this does not claim
that the new signed program was run or that another native edit is qualified.
"""
import hashlib
import shutil
import tempfile
from pathlib import Path

PRIOR = 'openspec/changes/spacefox-watchface/evidence/current-signed-release/prior/'
SNAPSHOTS = {
    'manifest.xml': ('watchface/manifest.xml', '0becfb38f9ad878271ddd172e491f2a588998511ed022e86c302fcccd25ec41f'),
    'NativeVersion.mc': ('watchface/source/generated/NativeVersion.mc', '4796f8f9567d7eec90cb9adb3e4c693614c72ad457ab50e9a73d6ef72addee97'),
    'native_language_policy.py': ('tools/native_language_policy.py', '1739a16f2e60bec963cdbaacc34bd2032bdcd148fddd044cbc75e867ea55a157'),
}

def validate(root, catalog):
    from tools.generate_native_version import validate as validate_version
    from tools.native_display02_requalification import validate as validate_reviewed
    root = Path(root).resolve()
    snapshots = {}
    for filename, (destination, expected) in SNAPSHOTS.items():
        data = (root / PRIOR / filename).read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('release prior input changed: ' + filename)
        snapshots[destination] = data
    prior_policy = snapshots['tools/native_language_policy.py']
    before = b'  from tools.native_display02_requalification import validate\n  return validate(root,catalog)'
    after = b'  from tools.native_release_version_requalification import validate\n  return validate(root,catalog)'
    if prior_policy.count(before) != 1 or (root/'tools/native_language_policy.py').read_bytes() != prior_policy.replace(before, after):
        raise ValueError('release language policy differs beyond approved dispatch')
    old = snapshots['watchface/manifest.xml']
    if old.count(b'version="0.1.10"') != 1 or (root/'watchface/manifest.xml').read_bytes() != old.replace(b'version="0.1.10"', b'version="0.1.11"'):
        raise ValueError('release manifest differs beyond approved version')
    with tempfile.TemporaryDirectory(prefix='spacefox-release-version-') as tmp:
        target = Path(tmp)
        for folder in ('watchface', 'locales', 'tools', 'tests'):
            shutil.copytree(root/folder, target/folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for folder in ('openspec', 'corpus', 'assets', 'catalog', 'schemas'):
            (target/folder).symlink_to(root/folder, target_is_directory=True)
        for name, data in snapshots.items():
            (target/name).write_bytes(data)
        qualified = validate_reviewed(target, catalog)
    validate_version(root)
    return qualified
