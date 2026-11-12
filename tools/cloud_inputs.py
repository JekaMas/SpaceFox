#!/usr/bin/env python3
"""Materialize the tracked catalog recipe closure after the sparse runtime seed.

No network, external package or second data inventory. The unchanged catalog
builder validates the complete result before any provider/deployment operation.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.spacefox.catalog import CatalogError, build_catalog, loads_json


def materialize(root):
    root = Path(root).resolve()

    def git(*args, data=None):
        return subprocess.run(['git', '-C', str(root), *args], input=data,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout

    # Index checkout must reproduce the authenticated revision, never staged or
    # locally edited replacement data. No untracked file is a catalog authority.
    git('diff', '--quiet', 'HEAD', '--')
    loaded = set()
    loading = set()

    def checkout(relative):
        path = Path(relative)
        if path.is_absolute() or '..' in path.parts or not path.parts:
            raise CatalogError('catalog input must stay relative to repository')
        name = path.as_posix()
        if name not in loaded:
            if name in loading:
                raise CatalogError('catalog input symlink cycle')
            loading.add(name)
            # Index assume-unchanged bits can conceal existing local bytes from
            # git diff. Authenticate each path before forced index checkout;
            # a declaration never grants authority to replace a local edit or
            # use an untracked source/dependency.
            entry = git('ls-tree', '-z', 'HEAD', '--', name).split(b'\0')
            if len(entry) != 2 or not entry[0]:
                raise CatalogError('catalog input must be tracked at HEAD')
            header, tracked = entry[0].split(b'\t', 1)
            mode, kind, digest = header.split()
            if tracked.decode('utf-8') != name or kind != b'blob':
                raise CatalogError('catalog input must be a tracked file')
            expected = git('cat-file', 'blob', digest.decode('ascii'))
            for parent in reversed(path.parents):
                if parent != Path('.') and (root / parent).is_symlink():
                    checkout(parent.as_posix())
            local = root / path
            if local.exists() or local.is_symlink():
                if mode == b'120000':
                    if not local.is_symlink() or os.fsencode(os.readlink(local)) != expected:
                        raise CatalogError('catalog input has local edits')
                elif local.is_symlink() or not local.is_file() or local.read_bytes() != expected:
                    raise CatalogError('catalog input has local edits')
            if not local.parent.resolve().is_relative_to(root):
                raise CatalogError('catalog input resolves outside repository')
            git('checkout-index', '--force', '--ignore-skip-worktree-bits', '-z', '--stdin',
                data=name.encode('utf-8') + b'\0')
            loaded.add(name)
            loading.remove(name)
        target = (root / path).resolve()
        if not target.is_relative_to(root):
            raise CatalogError('catalog input resolves outside repository')
        # Catalog inputs may use a repository-local symlink. Its tracked target
        # is part of the closure too; an absent/untracked target fails closed.
        if target != root / path:
            checkout(target.relative_to(root).as_posix())
        return target.read_bytes()

    def pin_bytes(item):
        raw = checkout(item['path'])
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise CatalogError('tracked catalog input digest mismatch')
        return raw

    def pin(item):
        return loads_json(pin_bytes(item))

    recipe = loads_json(checkout('catalog/source.json'))
    pin(recipe['reference'])
    registry = pin(recipe['assetSeed'])
    geography_inputs = set()
    if 'geography' in recipe:
        geography = pin(recipe['geography'])
        if geography.get('schemaVersion') == 2:
            from tools.spacefox.geographic_context import dependencies, load_source
            # The accepted geography owner enumerates every immutable input.
            # Binary clips/notices are hashed as bytes, then load_source verifies
            # complete decoding, source provenance, bounds and distinct rights.
            for item in dependencies({'index': geography}):
                pin_bytes(item)
                geography_inputs.add(item['path'])
            load_source(root, recipe['geography'])
    if 'visualBridge' in recipe:
        from tools.spacefox.bridge_map import dependencies as map_dependencies, load_source as map_source
        from tools.spacefox.geographic_context import dependencies as regional_dependencies
        bridge = pin(recipe['visualBridge'])
        for item in map_dependencies(bridge):
            pin_bytes(item)
        regional = pin(bridge['regional'])
        for item in regional_dependencies({'index': regional}):
            pin_bytes(item)
        map_source(root, recipe['visualBridge'])
    sources = [(recipe['assetSeed']['path'], [row for kind in ('models', 'companies', 'countries')
                                            for row in registry[kind]])]
    for item in recipe.get('curations', []):
        supplement = pin(item)
        sources.append((item['path'], [asset['facts'] for asset in supplement['assets']]))
    for source, assets in sources:
        for facts in assets:
            asset = Path(facts['file'])
            if asset.is_absolute() or '..' in asset.parts:
                raise CatalogError('source SVG must stay relative to its registry')
            checkout((Path(source).parent / asset).as_posix())
    catalog = build_catalog(root)
    expected = {'catalog/source.json', *catalog['inputDigests'], *geography_inputs}
    if not expected <= loaded:
        raise CatalogError('materialized catalog closure is incomplete')
    return {'catalogVersion': catalog['catalogVersion'], 'catalogInputs': len(loaded)}


def main():
    try:
        print(json.dumps(materialize(ROOT), sort_keys=True))
        return 0
    except (CatalogError, OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError):
        print('cloud-inputs: tracked catalog closure could not be materialized', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
