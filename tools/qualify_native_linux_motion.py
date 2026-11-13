#!/usr/bin/env python3
"""Offline current-catalog SFR1M qualification; never deploy or contact a provider."""
import argparse
import json
import platform
from pathlib import Path
import re
import sys
import time

from tools.qualify_native_linux import (QualificationError, require, pin, tree, safe_path,
    checked_tree, toolchain, pixels, run)
from tools.native_motion_qualification_fixture import inputs, NOW, GENERATIONS, TIMELINE_A, TIMELINE_B

ROOT = Path(__file__).resolve().parents[1]
LOCK = '.github/native-linux-motion-lock.json'
PROFILE = 'native-motion-v3'
FEEDS = ('feed.json', 'wire2/feed.json', 'wire3/feed.json', 'wire3/motion/feed.json')
CATALOG = dict(version='2026-11-12.global.21.blk3-whole1', recipeSha256='ef8b7e021ecfc94210b1b2f26e1de5741efc2ddb976ca44c1f2a7627e6f404eb', catalogInputsIncludingRecipe=710)
CAPS = dict(feedBytes=8192, objectBytes=4096, rasterObjects=32, rasterBytes=98304,
            transferObjects=40, transferBytes=114688, cacheObjects=96, cacheBytes=393216,
            artifactFiles=256, artifactBytes=1048576)


def preflight(root, require_linux=False):
    require(not require_linux or platform.system() == 'Linux', 'actual Linux required')
    raw = (root / LOCK).read_bytes()
    lock = json.loads(raw)
    require(lock['schemaVersion'] == 1 and lock['profile'] == PROFILE and lock['caps'] == CAPS and lock['catalog'] == CATALOG, 'lock contract')
    require(pin((root/'catalog/source.json').read_bytes())['sha256'] == CATALOG['recipeSha256'], 'catalog recipe pin')
    require(run(['git', 'status', '--porcelain', '--untracked-files=all'], cwd=root) == '', 'clean source checkout required')
    for name, expected in lock['sourceFiles'].items():
        require(pin(safe_path(root, name).read_bytes()) == expected, 'source mismatch: ' + name)
    require(set(lock['references']) == set(GENERATIONS), 'reference cohort mismatch')
    references = {label: checked_tree(root, ref['root'], ref['files']) for label, ref in lock['references'].items()}
    return lock, pin(raw), references


def read_ref(data, ref):
    require(type(ref) is dict and set(ref) == {'path', 'sha256', 'decodedBytes'}, 'reference grammar')
    name = ref['path']; require(type(name) is str and re.fullmatch(r'(?:descriptors|sources|rasters)/[0-9a-f]{64}\.(?:json|sfr)', name) is not None, 'reference path')
    raw = data[name]; require(pin(raw) == {'bytes': ref['decodedBytes'], 'sha256': ref['sha256']}, 'reference bytes')
    require(name.split('/')[1].split('.')[0] == ref['sha256'], 'content address')
    return raw


def inspect(data, label):
    require(type(data) is dict and len(data) <= CAPS['artifactFiles'] and sum(map(len, data.values())) <= CAPS['artifactBytes'], 'artifact bound')
    for path in FEEDS:
        require(path in data and len(data[path]) <= CAPS['feedBytes'], 'feed bound: ' + path)
    feed = json.loads(data[FEEDS[3]]); old = json.loads(data[FEEDS[2]])
    require(feed['rendererProfile'] == 'SFR1M' and old['rendererProfile'] == 'SFR1', 'profile')
    require(feed['launch'] == old['launch'] and feed['publisher'] == old['publisher'], 'source age/legacy equality')
    require(feed['launch']['source_validated_utc'] == NOW-3600 and feed['publisher']['selectionValidatedUtc'] == NOW-3600 and feed['publisher']['generation'] == GENERATIONS[label], 'literal age/generation')
    cache = {}; summaries = {}; rocket = None
    for view, transfer, layout in [('visualSelection','nativeTransfer','native-04-motion-v1'), ('globeSelection','globeTransfer','native-04-globe-motion-v1')]:
        scene = json.loads(read_ref(data, feed[view])); index = json.loads(read_ref(data, feed[transfer]))
        require(scene['layoutRevision'] == layout and scene['rendererProfile'] == 'SFR1M', 'scene profile/layout')
        require(set(scene['roles']) == {'map','rocket','operator','modelOrigin','operatorOrigin'}, 'roles')
        require(scene['siteId'] == 'll2:site:80' and scene['countryId'] == 'll2:country:2', 'site origin')
        if label not in ('shared', 'missing'):
            require(scene['modelId'] == 'll2:configuration:26' and scene['operatorId'] == 'll2:organization:115', 'distinct owners')
            require(scene['origins']['model']['countryId'] == 'll2:country:51' and scene['origins']['operator']['countryId'] == 'll2:country:1', 'distinct origins')
        if label == 'missing': require(scene['roles']['operatorOrigin'] is None, 'missing origin')
        if label == 'shared': require(scene['roles']['modelOrigin'] == scene['roles']['operatorOrigin'] and scene['origins']['model']['ownerId'] != scene['origins']['operator']['ownerId'], 'shared dedup')
        for origin in scene['origins'].values(): read_ref(data, origin['sourceRecord'])
        for role, binding in scene['roles'].items():
            if binding is None: continue
            desc = json.loads(read_ref(data, binding['descriptor']))
            for ref in desc['shards']: read_ref(data, ref)
            if role == 'rocket':
                require(desc['rendererProfile'] == 'SFR1M' and desc['animation'] == (TIMELINE_B if label in ('timeline-b','image-b') else TIMELINE_A), 'timeline')
                read_ref(data, desc['motionSource'])
                observed = dict(pixelSha256=desc['pixelSha256'], animation=desc['animation'], motionSource=desc['motionSource']['sha256'])
                require(rocket is None or rocket == observed, 'cross-view rocket mismatch')
                rocket = observed
        refs = index['objects']; require(type(refs) is list and len(refs) <= CAPS['transferObjects'], 'transfer count')
        seen = set(); total = raster_count = raster_bytes = 0
        for kind, digest, size in refs:
            require(kind in (0,1) and type(size) is int and 0 < size <= CAPS['objectBytes'] and digest not in seen, 'transfer entry')
            path = ('rasters/' if kind == 1 else 'descriptors/') + digest + ('.sfr' if kind == 1 else '.json')
            require(pin(data[path]) == dict(bytes=size, sha256=digest), 'transfer bytes')
            seen.add(digest); total += size; raster_count += kind; raster_bytes += size * kind; cache[digest] = size
        require(total <= CAPS['transferBytes'] and raster_count <= CAPS['rasterObjects'] and raster_bytes <= CAPS['rasterBytes'], 'transfer/raster budget')
        # Independent literal decoder from the static qualification; no production codec.
        decoded = pixels(dict(data, **{'wire3/feed.json': data[FEEDS[3]]}), view)
        summaries[view] = {role: dict(canvas=value['canvas'], channels=value['channels'], **pin(value['raw'])) for role,value in decoded.items()}
    require(len(cache) <= CAPS['cacheObjects'] and sum(cache.values()) <= CAPS['cacheBytes'], 'cache budget')
    return dict(pixels=summaries, rocket=rocket, cache=cache, files=len(data), bytes=sum(map(len,data.values())))


def compare(candidate, reference, label):
    expected = inspect(reference, label)
    try:
        actual = inspect(candidate, label)
        error = None
    except (QualificationError, ValueError, KeyError, TypeError, IndexError, StopIteration) as exc:
        actual = None
        error = type(exc).__name__ + ': ' + str(exc)[:300]
    diff = {p: dict(candidate=pin(candidate[p]) if p in candidate else None, reference=pin(reference[p]) if p in reference else None)
            for p in sorted(set(candidate) | set(reference)) if candidate.get(p) != reference.get(p)}
    return dict(exact=not diff and actual is not None and actual['pixels'] == expected['pixels'], differences=diff, candidateDecodeError=error, actual=actual, referencePixels=expected['pixels'])


def cache_union(current, prior):
    union = dict(prior)
    for digest, size in current.items():
        require(digest not in union or union[digest] == size, 'cache digest size collision')
        union[digest] = size
    require(len(union) <= CAPS['cacheObjects'] and sum(union.values()) <= CAPS['cacheBytes'], 'current/prior cache budget')
    return dict(objects=len(union), bytes=sum(union.values()))


def qualify(root, output, require_linux=False):
    root, output = root.resolve(), output.resolve()
    require(not output.exists() and not output.is_relative_to(root) and not root.is_relative_to(output), 'new external output required')
    head = run(['git','rev-parse','HEAD'], cwd=root); lock, lock_pin, refs = preflight(root, require_linux)
    identity = toolchain(); started = time.monotonic(); results = {}; artifacts = {}
    from tools.spacefox import native_motion, native_profile
    for label in GENERATIONS:
        with inputs(root, label) as (state, catalog, source, publisher, eligibility):
            require(catalog['catalogVersion'] == CATALOG['version'] and len(catalog['inputDigests']) in (710, 711), 'current catalog and fixture input count')
            kwargs = dict(publisher=publisher, root=source, eligibility=eligibility)
            candidate, _ = native_motion.build_artifact(state, catalog, NOW+publisher['generation'], **kwargs)
            legacy, _ = native_profile.build_artifact(state, catalog, NOW+publisher['generation'], **kwargs)
        require(all(candidate.get(p) == raw for p,raw in legacy.items()), 'legacy actual streams changed')
        artifacts[label] = candidate; results[label] = compare(candidate, refs[label], label)
    if all(results[label]['actual'] is not None for label in ('a','timeline-b','image-b','rollback')):
        sequence = [results[label]['actual']['rocket'] for label in ('a','timeline-b','image-b','rollback')]
        require(sequence[0]['pixelSha256'] == sequence[1]['pixelSha256'] and sequence[1]['pixelSha256'] != sequence[2]['pixelSha256'] and sequence[0] == sequence[3], 'timeline/image/rollback witness')
        require(sequence[0]['animation'] == TIMELINE_A and sequence[1]['animation'] == TIMELINE_B and sequence[2]['animation'] == TIMELINE_B, 'timeline update witness')
    unions = {}
    for label in ('timeline-b','image-b','rollback'):
        prior = artifacts['a'] if label == 'timeline-b' else artifacts['timeline-b'] if label == 'image-b' else artifacts['image-b']
        merged = {p:v for p,v in prior.items() if p not in FEEDS}
        for p,v in artifacts[label].items():
            require(p not in merged or merged[p] == v, 'immutable prior collision')
            merged[p] = v
        require(len(merged) <= CAPS['artifactFiles'] and sum(map(len,merged.values())) <= CAPS['artifactBytes'], 'prior union bound')
        previous_label = 'a' if label == 'timeline-b' else 'timeline-b' if label == 'image-b' else 'image-b'
        cache = None
        if results[label]['actual'] is not None and results[previous_label]['actual'] is not None:
            cache = cache_union(results[label]['actual']['cache'], results[previous_label]['actual']['cache'])
        unions[label] = dict(files=len(merged), bytes=sum(map(len,merged.values())), cache=cache)
    loaded = {Path(m.__file__).resolve().relative_to(root).as_posix() for m in list(sys.modules.values()) if getattr(m,'__file__',None) and Path(m.__file__).resolve().is_relative_to(root) and m.__name__.startswith('tools.')}
    require(loaded <= set(lock['sourceFiles']), 'unfrozen imported source')
    require(preflight(root, require_linux)[1] == lock_pin and run(['git','rev-parse','HEAD'], cwd=root) == head, 'source changed')
    exact = all(r['exact'] for r in results.values())
    report = dict(profile=PROFILE, gitHead=head, lock=lock_pin, toolchain=identity, fixtures=results,
        priorUnions=unions, elapsedSeconds=round(time.monotonic()-started,3), actualLinux=platform.system()=='Linux',
        result='exact-reference-match' if exact else 'raw-difference-refused', productionActivated=False,
        proofBoundary='Offline frozen current G21 fixtures only; no live provider, SDK, device, hosted or operational qualification')
    raw = (json.dumps(report, indent=2, sort_keys=True)+'\n').encode()
    require(len(raw) <= 1048576, 'diagnostic bound')
    output.mkdir(parents=True); (output/'receipt.json').write_bytes(raw)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--output',required=True,type=Path); p.add_argument('--require-linux',action='store_true')
    args = p.parse_args()
    try: report = qualify(ROOT,args.output,args.require_linux)
    except (QualificationError, ValueError, KeyError, TypeError, IndexError, OSError) as exc:
        print('motion qualification refused: ' + str(exc),file=sys.stderr); return 1
    print(json.dumps(dict(result=report['result'],actualLinux=report['actualLinux'],output=str(args.output))))
    return 0 if report['result']=='exact-reference-match' else 3

if __name__ == '__main__': sys.exit(main())
