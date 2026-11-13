#!/usr/bin/env python3
"""Offline qualification of frozen static native/globe producer inputs.

This never opens a provider, Publisher, Pages or SDK. A differing renderer is a
review candidate, not permission to rewrite a reference or activate production.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
LOCK = '.github/native-linux-static-lock.json'
PROFILE = 'native-raster-v3'
ROOTS = {'feed.json', 'wire2/feed.json', 'wire3/feed.json'}
CAPS = dict(artifactFiles=256, artifactBytes=1048576, feedBytes=8192,
            objectBytes=4096, transferObjects=40, transferBytes=114688,
            rasterObjects=32, rasterBytes=98304)


class QualificationError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise QualificationError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def pin(raw):
    return dict(bytes=len(raw), sha256=digest(raw))


def run(argv, *, cwd=None):
    return subprocess.check_output(argv, cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()


def tree(root):
    require(root.is_dir() and not root.is_symlink(), f'missing/plain directory required: {root}')
    result = {}
    for path in sorted(root.rglob('*')):
        require(not path.is_symlink(), f'symlink refused: {path}')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def safe_path(root, name):
    p = PurePosixPath(name)
    require(not p.is_absolute() and str(p) == name and all(x not in ('', '.', '..') for x in p.parts), 'unsafe lock path')
    path = root / name
    require(path.resolve().is_relative_to(root.resolve()) and not path.is_symlink(), 'escaped lock path')
    return path


def checked_tree(root, name, expected):
    data = tree(safe_path(root, name))
    require({p: pin(raw) for p, raw in data.items()} == expected, f'frozen tree mismatch: {name}')
    return data


def preflight(root, profile, *, require_linux):
    require(profile == PROFILE, 'unsupported profile; motion is not qualified')
    require(not require_linux or platform.system() == 'Linux', 'actual Linux execution required')
    raw = (root / LOCK).read_bytes()
    lock = json.loads(raw)
    require(lock['schemaVersion'] == 1 and lock['profile'] == profile and lock['caps'] == CAPS, 'lock profile/cap contract')
    require(run(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=root) == '', 'clean source checkout required')
    for name, expected in {**lock['sourceFiles'], **lock['qualificationFiles']}.items():
        require(pin(safe_path(root, name).read_bytes()) == expected, f'production source mismatch: {name}')
    inputs = {}
    references = {}
    for label, fixture in lock['fixtures'].items():
        inputs[label] = checked_tree(root, fixture['inputRoot'], fixture['inputs'])
        delta = checked_tree(root, fixture['referenceRoot'], fixture['referenceFiles'])
        require(not set(inputs[label]) & set(delta), 'reference must be additive')
        references[label] = {**inputs[label], **delta}
    require(set(inputs) == {'a', 'b'}, 'exact A/B fixture cohort required')
    return lock, pin(raw), inputs, references


def toolchain():
    renderer = shutil.which('rsvg-convert')
    require(renderer is not None, 'rsvg-convert prerequisite missing; do not install implicitly')
    renderer = str(Path(renderer).resolve())
    info = dict(system=platform.system(), machine=platform.machine(), platform=platform.platform(),
                python=dict(version=sys.version, executable=sys.executable, sha256=digest(Path(sys.executable).resolve().read_bytes())),
                renderer=dict(path=renderer, version=run([renderer, '--version']), **pin(Path(renderer).read_bytes())),
                runner={k: os.environ.get(k) for k in ('ImageOS', 'ImageVersion', 'RUNNER_OS', 'RUNNER_ARCH', 'GITHUB_SHA', 'GITHUB_RUN_ID', 'GITHUB_RUN_ATTEMPT')})
    if platform.system() == 'Linux':
        require(platform.machine() == 'x86_64', 'qualification runner must be Linux AMD64')
        info['osRelease'] = Path('/etc/os-release').read_text()
        info['packages'] = run(['dpkg-query', '-W', '-f=${binary:Package}\t${Version}\t${Architecture}\n'])
        info['rendererPackage'] = run(['dpkg-query', '-W', '-f=${Version}', 'librsvg2-bin'])
        require(info['rendererPackage'] == '2.58.0+dfsg-1ubuntu0.1', 'unreviewed Linux renderer package')
        require(info['renderer']['version'] == 'rsvg-convert version 2.58.0', 'unreviewed Linux renderer version')
        require(info['runner']['ImageOS'] == 'ubuntu24' and info['runner']['ImageVersion'], 'runner image identity required')
        info['linker'] = run(['ldd', renderer])
        libraries = re.findall(r'(?:=>\s+)?(/\S+)\s+\(', info['linker'])
        require(libraries, 'resolved renderer libraries required')
        info['libraries'] = {name: pin(Path(name).read_bytes()) for name in sorted(set(libraries))}
    elif platform.system() == 'Darwin':
        info['linker'] = run(['otool', '-L', renderer])
        names = re.findall(r'^\s+(/\S+)\s+\(', info['linker'], re.MULTILINE)
        info['libraries'] = {name: pin(Path(name).read_bytes()) for name in names if Path(name).is_file()}
        info['dyldCacheOrUnresolvedLibraries'] = [name for name in names if not Path(name).is_file()]
        info['dependencyBoundary'] = 'Direct dylibs only; transitive dependencies and dyld-cache bytes not independently frozen'
    return info


def pixels(data, scene_key):
    """Independent literal SFR1 token interpreter, separate from production codec."""
    feed = json.loads(data['wire3/feed.json'])
    scene = json.loads(data[feed[scene_key]['path']])
    out = {}
    for role, binding in scene['roles'].items():
        if binding is None:
            continue
        desc = json.loads(data[binding['descriptor']['path']])
        width, height = desc['canvas']; channels = desc['channels']; rows = []
        for ref in desc['shards']:
            raw = data[ref['path']]
            signature, start, count, encoded = raw.split(b':', 3)
            require(signature == b'SFR1' and int(start) == len(rows), 'SFR1 reference row order')
            stream = iter(base64.b64decode(encoded, validate=True)); previous = [bytes(channels)] * width
            for _ in range(int(count)):
                row = []
                while len(row) < width:
                    try:
                        token = next(stream); length = (token % 128) + 1
                        require(len(row) + length <= width, 'SFR1 reference row bound')
                        # A list comprehension preserves StopIteration here;
                        # a generator expression wraps early EOF in RuntimeError.
                        color = bytes([next(stream) for _ in range(channels)]) if token < 128 else None
                    except StopIteration as exc:
                        raise QualificationError('SFR1 truncated token/color') from exc
                    row += previous[len(row):len(row)+length] if token >= 128 else [color] * length
                require(len(row) == width, 'SFR1 reference row bound')
                rows.append(row); previous = row
            require(list(stream) == [], 'SFR1 reference trailing bytes')
        require(len(rows) == height, 'SFR1 reference height')
        raw = b''.join(value for row in rows for value in row)
        require(digest(raw) == desc['pixelSha256'], 'SFR1 independent pixel hash')
        out[role] = dict(canvas=desc['canvas'], channels=channels, raw=raw)
    return out


def budgets(data):
    require(len(data) <= CAPS['artifactFiles'] and sum(map(len, data.values())) <= CAPS['artifactBytes'], 'complete artifact budget')
    for name in ROOTS:
        require(name in data and len(data[name]) <= CAPS['feedBytes'], 'feed budget/root')
    feed = json.loads(data['wire3/feed.json']); result = {}
    for selection, transfer, layout in [('visualSelection', 'nativeTransfer', 'native-04-v1'), ('globeSelection', 'globeTransfer', 'native-04-globe-v1')]:
        scene = json.loads(data[feed[selection]['path']])
        require(scene['layoutRevision'] == layout, 'typed flat/globe scene required')
        index = json.loads(data[feed[transfer]['path']]); refs = index['objects']
        require(len(refs) <= CAPS['transferObjects'] and sum(r[2] for r in refs) <= CAPS['transferBytes'], 'transfer budget')
        rasters = [r for r in refs if r[0] == 1]
        require(len(rasters) <= CAPS['rasterObjects'] and sum(r[2] for r in rasters) <= CAPS['rasterBytes'], 'raster budget')
        for kind, sha, size in refs:
            path = f'rasters/{sha}.sfr' if kind == 1 else f'descriptors/{sha}.json'
            require(type(size) is int and 0 < size <= CAPS['objectBytes'] and pin(data[path]) == dict(bytes=size, sha256=sha), 'indexed raw object pin/budget')
        result[selection] = dict(objects=len(refs), bytes=sum(r[2] for r in refs), rasterObjects=len(rasters), rasterBytes=sum(r[2] for r in rasters), layout=layout)
    return dict(files=len(data), bytes=sum(map(len, data.values())), feeds={name: pin(data[name]) for name in sorted(ROOTS)}, views=result)


def prior_union(current, prior):
    union = {p: raw for p, raw in prior.items() if p not in ROOTS}
    for path, raw in current.items():
        require(path not in union or union[path] == raw, f'immutable current/prior collision: {path}')
        union[path] = raw
    require(len(union) <= CAPS['artifactFiles'] and sum(map(len, union.values())) <= CAPS['artifactBytes'], 'current/prior artifact budget')
    return dict(files=len(union), bytes=sum(map(len, union.values())), manifest={p: pin(raw) for p, raw in sorted(union.items())})


def comparison(candidate, reference):
    changed = {p: dict(candidate=None if p not in candidate else pin(candidate[p]), reference=None if p not in reference else pin(reference[p]))
               for p in sorted(set(candidate) | set(reference)) if candidate.get(p) != reference.get(p)}
    differences = {}
    for view in ('visualSelection', 'globeSelection'):
        expected = pixels(reference, view)
        try:
            actual = pixels(candidate, view)
        except (QualificationError, ValueError, KeyError, TypeError, IndexError, StopIteration) as exc:
            # The reference must be interpretable; a bad candidate is itself a
            # raw difference to preserve for review, not a reason to lose it.
            differences[view] = {'candidateDecodeError': f'{type(exc).__name__}: {exc}'}
            continue
        differences[view] = {}
        for role in sorted(set(actual) | set(expected)):
            a, b = actual.get(role), expected.get(role)
            if a is None or b is None:
                differences[view][role] = dict(candidate=None if a is None else dict(canvas=a['canvas'], channels=a['channels'], **pin(a['raw'])),
                                               reference=None if b is None else dict(canvas=b['canvas'], channels=b['channels'], **pin(b['raw'])),
                                               difference='role-presence')
                continue
            if (a['canvas'], a['channels']) != (b['canvas'], b['channels']):
                differences[view][role] = dict(candidate=dict(canvas=a['canvas'], channels=a['channels'], **pin(a['raw'])),
                                               reference=dict(canvas=b['canvas'], channels=b['channels'], **pin(b['raw'])),
                                               difference='pixel-shape')
                continue
            ar, br, channels = a['raw'], b['raw'], a['channels']
            count = sum(ar[i:i+channels] != br[i:i+channels] for i in range(0, len(ar), channels))
            differences[view][role] = dict(canvas=a['canvas'], channels=channels, candidate=pin(ar), reference=pin(br),
                differentPixels=count, maxChannelDelta=max((abs(x-y) for x, y in zip(ar, br)), default=0))
    return dict(exactFiles=not changed, files=changed, pixels=differences)


def qualify(root, output, *, profile=PROFILE, require_linux=False):
    root, output = root.resolve(), output.resolve()
    require(not output.is_relative_to(root) and not root.is_relative_to(output), 'output must be outside source checkout')
    require(not output.exists(), 'output must be new; retained evidence is never overwritten')
    start_head = run(['git', 'rev-parse', 'HEAD'], cwd=root)
    lock, lock_pin, inputs, references = preflight(root, profile, require_linux=require_linux)
    identity = toolchain()
    # Import only after all source and fixture pins pass. No environment credentials
    # are read, logged or passed explicitly to an operational owner.
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from tools.spacefox.native_profile import add_profile
    started = time.monotonic(); candidates = {}; observations = {}; renderings = {}
    for label, old in inputs.items():
        candidate, rendered = add_profile(old, include_globe=True)
        require(all(candidate.get(p) == raw for p, raw in old.items()), 'legacy v1/v2 bytes changed')
        observations[label] = dict(budgets=budgets(candidate), legacyFilesUnchanged=len(old),
                                   comparison=comparison(candidate, references[label]))
        candidates[label] = candidate
        renderings[label] = rendered
    loaded = {Path(m.__file__).resolve().relative_to(root).as_posix() for m in list(sys.modules.values())
              if getattr(m, '__file__', None) and Path(m.__file__).resolve().is_relative_to(root) and m.__name__.startswith('tools.spacefox')}
    require(loaded <= set(lock['sourceFiles']), 'unfrozen imported producer source')
    union = prior_union(candidates['b'], candidates['a'])
    final_lock_pin = preflight(root, profile, require_linux=require_linux)[1]
    require(final_lock_pin == lock_pin and run(['git', 'rev-parse', 'HEAD'], cwd=root) == start_head, 'source revision changed during qualification')
    equal = all(v['comparison']['exactFiles'] for v in observations.values())
    report = dict(schemaVersion=1, profile=profile, gitHead=start_head, cleanSource=True,
                  lock=lock_pin, sourceFiles=lock['sourceFiles'], toolchain=identity,
                  retainedReference=lock['retainedReference'], caps=CAPS, fixtures=observations,
                  currentPrior=union, elapsedSeconds=round(time.monotonic()-started, 3),
                  result='exact-reference-match' if equal else 'candidate-differences-require-review',
                  actualLinux=platform.system() == 'Linux', productionActivated=False,
                  proofBoundary='Frozen A/B static flat+globe offline producer only; no live catalog/provider/publication/device/latency/SLA acceptance')
    # Validate the complete write set before creating even the output directory.
    # Diagnostic intermediates have their own bound; production caps above are
    # unchanged and continue to cover each complete artifact and its union.
    writes = {}
    for label, data in candidates.items():
        for path, raw in data.items():
            require(isinstance(raw, bytes), 'candidate must contain raw bytes')
            safe_path(output / label, path)
            writes[f'{label}/{path}'] = raw
    diagnostic_count = diagnostic_bytes = 0
    for label, rendered in renderings.items():
        for role, values in rendered.items():
            if values is None:
                continue
            for kind in ('svg', 'png'):
                require(isinstance(role, str) and re.fullmatch(r'[A-Za-z0-9_-]+', role), 'unsafe render role')
                raw = values[kind]
                require(isinstance(raw, bytes), 'render must contain raw bytes')
                diagnostic_count += 1; diagnostic_bytes += len(raw)
                writes[f'renders/{label}/{role}.{kind}'] = raw
    require(diagnostic_count <= 64 and diagnostic_bytes <= 16777216, 'render diagnostics budget')
    writes['receipt.json'] = (json.dumps(report, indent=2, sort_keys=True) + '\n').encode()
    for name in writes:
        safe_path(output, name)
        require(not any('/'.join(name.split('/')[:i]) in writes for i in range(1, len(name.split('/')))), 'write path collision')
    output.mkdir(parents=True)
    for name, raw in writes.items():
        dest = safe_path(output, name); dest.parent.mkdir(parents=True, exist_ok=True); dest.write_bytes(raw)
    require(run(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=root) == '', 'source changed during qualification')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--profile', required=True, choices=[PROFILE])
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--require-linux', action='store_true')
    args = parser.parse_args()
    try:
        report = qualify(ROOT, args.output, profile=args.profile, require_linux=args.require_linux)
    except (QualificationError, ValueError, KeyError, OSError, subprocess.SubprocessError) as exc:
        print(f'native-linux qualification refused: {exc}', file=sys.stderr)
        return 1
    print(json.dumps(dict(result=report['result'], actualLinux=report['actualLinux'], output=str(args.output))))
    return 0 if report['result'] == 'exact-reference-match' else 3


if __name__ == '__main__':
    sys.exit(main())
