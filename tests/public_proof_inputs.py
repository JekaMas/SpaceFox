"""Read authenticated original build inputs without private Git or SDK access.

This broker proves the exact bytes of a retained source observation. It does not
prove Git ancestry, an installed toolchain, a new execution, or equivalence with a
changed current owner. Current applicability remains in the named seam readers.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIRECTORY = ROOT / 'tests/fixtures/public-proof-inputs'
MANIFEST_SHA256 = 'b973337b6892fdddfe770cc2ed45fd5c93f60127087a903c2c7dc4432fce371c'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def manifest():
    raw = (DIRECTORY / 'manifest.json').read_bytes()
    if digest(raw) != MANIFEST_SHA256:
        raise AssertionError('public proof input manifest changed')
    return json.loads(raw)


def recorded_input(source, expected):
    """Require the named source and digest; never search a private checkout."""
    source_path = Path(source)
    if source_path.is_absolute() or '..' in source_path.parts:
        raise AssertionError('invalid public proof source path')
    item = manifest()['inputs'].get(source + '@' + expected)
    if item is None:
        current = ROOT / source
        if not current.resolve().is_relative_to(ROOT.resolve()):
            raise AssertionError('invalid public proof source path')
        if current.is_file() and digest(current.read_bytes()) == expected:
            return current.read_bytes()
        raise AssertionError('historical build input unavailable or changed: ' + source)
    relative = Path(item['path'])
    if relative.is_absolute() or '..' in relative.parts or item['source'] != source or item['sha256'] != expected:
        raise AssertionError('invalid public proof input binding: ' + source)
    target = ROOT / relative
    if not target.resolve().is_relative_to(ROOT.resolve()):
        raise AssertionError('invalid public proof input binding: ' + source)
    raw = target.read_bytes()
    if digest(raw) != expected:
        raise AssertionError('historical build input unavailable or changed: ' + source)
    return raw


def original_source(spec, *, text=False):
    """Resolve only the exact source refs explicitly exported in the manifest."""
    key = manifest()['gitObjects'].get(spec)
    if key is None:
        raise AssertionError('private Git dependency is not exported: ' + spec)
    source, expected = key.rsplit('@', 1)
    raw = recorded_input(source, expected)
    return raw.decode() if text else raw


def verify_current_closure(root=ROOT):
    """Authenticate all current native inputs against the accepted latest proof.

    This establishes current input identity, not a fresh SDK run or equivalence
    of every changed owner with a historical observation.
    """
    root = Path(root)
    proof = json.loads((root / 'locales/catalog.json').read_bytes())['supportPolicy']['softwareQualificationProof']
    ref = proof.get('integrated016Proof', proof.get('version14Proof', proof.get('decoderStreamProof', proof.get('settingsReadabilityProof'))))
    relative = Path(ref['path'])
    if relative.is_absolute() or '..' in relative.parts:
        raise AssertionError('invalid current proof path')
    raw = (root / relative).read_bytes()
    if digest(raw) != ref['sha256']:
        raise AssertionError('current integration proof changed')
    inputs = json.loads(raw)['nativeInputs']
    paths = {str(p.relative_to(root)) for p in (root/'watchface/source').rglob('*.mc') if p.is_file()}
    paths |= {str(p.relative_to(root)) for d in (root/'watchface').glob('resources*') for p in d.rglob('*') if p.is_file()}
    if not paths <= set(inputs):
        raise AssertionError('current native proof inventory incomplete')
    for name, expected in inputs.items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or digest((root/path).read_bytes()) != expected:
            raise AssertionError('current integration source changed: ' + name)
    return inputs


def verify_original_evidence(root=ROOT):
    """Authenticate immutable raw records without translating their scope."""
    root = Path(root)
    files = manifest()['evidenceFiles']
    for name, expected in files.items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or digest((root/path).read_bytes()) != expected:
            raise AssertionError('retained original evidence changed: ' + name)
    return len(files)
