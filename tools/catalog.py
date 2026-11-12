#!/usr/bin/env python3
"""Validate/build publisher metadata locally; never fetch or publish."""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

# Permit the documented `python3 -B tools/catalog.py` from a source checkout.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes, coverage_report, loads_json


def validate_artwork_sources(root, catalog):
    """Check every publisher asset through bounded existing delivery selections.

    Catalog maintenance is not an instruction to deliver a full-global pack.
    Each selection still obeys the unchanged root, metadata, shard and 1MiB caps.
    """
    from tools.spacefox.graphics import LIMITS, build_pack
    identities = sorted(catalog['dictionaries']['assets'])
    for offset in range(0, len(identities), LIMITS['selectionRoots']):
        build_pack(root, catalog, roots=identities[offset:offset+LIMITS['selectionRoots']])


def amend_recipe(root, source, supplement, version, *, output_paths=(), contexts=None):
    """Append a new pinned data revision; validate all inputs before activation."""
    root, source, supplement = Path(root).resolve(), Path(source).resolve(), Path(supplement).resolve()
    if not supplement.is_relative_to(root) or not supplement.is_file():
        raise CatalogError('curation must be a file inside the repository')
    recipe = loads_json(source.read_bytes())
    if not isinstance(version, str) or not version.strip() or version == recipe['catalogVersion']:
        raise CatalogError('a distinct nonempty catalog version is required')
    from tools.spacefox.current_catalog import load_registry, validate_registry
    previous = build_catalog(root, source)
    previous_registry = load_registry(root, previous, source_path=source)
    recipe.pop('eligibility', None)
    recipe.update(producerVersion=2, catalogVersion=version)
    relative = supplement.relative_to(root).as_posix()
    if relative in {x['path'] for x in recipe.setdefault('curations', [])}:
        raise CatalogError('append a new curation file; accepted pinned supplements are immutable')
    recipe['curations'].append({'path': relative, 'sha256': hashlib.sha256(supplement.read_bytes()).hexdigest()})
    if contexts is not None:
        context_path = Path(contexts).resolve()
        if not context_path.is_relative_to(root) or not context_path.is_file():
            raise CatalogError('current contexts must be a file inside the repository')
        recipe['currentContexts'] = {'path': context_path.relative_to(root).as_posix(),
                                     'sha256': hashlib.sha256(context_path.read_bytes()).hexdigest()}
    candidate = None
    registry_created = None
    try:
        with tempfile.NamedTemporaryFile(dir=source.parent, prefix='.recipe-', delete=False) as stream:
            candidate = Path(stream.name); stream.write(canonical_bytes(recipe)); stream.flush(); os.fsync(stream.fileno())
        catalog = build_catalog(root, candidate, _strict_creation_path=relative)
        if previous_registry is not None:
            registry = deepcopy(previous_registry)
            registry['catalogVersion'] = version
            registry['dictionaryDigest'] = hashlib.sha256(canonical_bytes(catalog['dictionaries'])).hexdigest()
            old_models = previous['dictionaries']['configurations']
            new_models = catalog['dictionaries']['configurations']
            records = {}
            for identity, row in new_models.items():
                facts = row['facts']
                old_facts = old_models.get(identity, {}).get('facts')
                def lifecycle_facts(value):
                    return None if value is None else {k: v for k, v in value.items()
                            if k not in ('currentPackAssetId', 'currentPackSpecific', 'curatedOriginId',
                                         'curatedOriginSources', 'curatedOriginReviewedAt', 'curatedOriginNote')}
                if identity in registry['records'] and lifecycle_facts(old_facts) == lifecycle_facts(facts):
                    records[identity] = registry['records'][identity]
                else:
                    placeholder = facts['placeholder']
                    records[identity] = {
                        'state': 'unknown-reference' if placeholder else 'needs-review',
                        'reason': 'New or changed configuration needs a dated lifecycle review.',
                        'sources': [facts['sourceUrl']],
                        'asOf': datetime.now(timezone.utc).date().isoformat(),
                        'uncertainty': 'No current or retired decision is inferred from this revision.'}
            registry['records'] = records
            validate_registry(catalog, registry)
            registry_bytes = canonical_bytes(registry)
            digest = hashlib.sha256(registry_bytes).hexdigest()
            registry_path = root / 'catalog' / ('current-eligibility-' + digest + '.json')
            if registry_path.exists():
                if registry_path.read_bytes() != registry_bytes:
                    raise CatalogError('eligibility object collision')
            else:
                with registry_path.open('xb') as stream:
                    stream.write(registry_bytes); stream.flush(); os.fsync(stream.fileno())
                registry_created = registry_path
            recipe['eligibility'] = {'path': registry_path.relative_to(root).as_posix(), 'sha256': digest}
            candidate.write_bytes(canonical_bytes(recipe))
            catalog = build_catalog(root, candidate, _strict_creation_path=relative)
        # Geometry/rights/export admission precedes source activation.
        validate_artwork_sources(root, catalog)
        protected = {source, supplement, *((root/p).resolve() for p in catalog['inputDigests'])}
        if any(p is not None and Path(p).resolve() in protected for p in output_paths):
            raise CatalogError('output would overwrite a catalog source or frozen import')
        os.replace(candidate, source); candidate = None
        registry_created = None
        return catalog
    finally:
        if candidate is not None:
            candidate.unlink(missing_ok=True)
        if registry_created is not None:
            registry_created.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT, help='explicit source checkout root; independent of working directory')
    parser.add_argument('--source', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--amend', type=Path, help='append a new curation file and atomically activate its recipe pin')
    parser.add_argument('--contexts', type=Path, help='pin source-dated current context data with --amend')
    parser.add_argument('--catalog-version', help='new version required with --amend')
    parser.add_argument('--report', type=Path, help='write finite coverage report')
    parser.add_argument('--check', action='store_true', help='validate without writing catalog output')
    args = parser.parse_args(argv)
    root = args.repo.resolve()
    args.source = args.source if args.source is not None else root/'catalog/source.json'
    temporary = None
    try:
        if not (args.output or args.check or args.amend or args.report):
            raise CatalogError('choose --output, --check, --report or --amend')
        for target in (args.output, args.report):
            if target is not None and target.resolve().is_relative_to(root) and not target.resolve().is_relative_to(root/'build'):
                raise CatalogError('in-checkout derived output must stay under build/')
        if args.contexts and not args.amend:
            raise CatalogError('--contexts requires --amend')
        if args.amend:
            previous = build_catalog(root, args.source)
            protected_before = {args.source.resolve(), *((root / p).resolve() for p in previous['inputDigests'])}
            if any(p is not None and p.resolve() in protected_before for p in (args.output, args.report)):
                raise CatalogError('output would overwrite a catalog source or frozen import')
        catalog = amend_recipe(root, args.source, args.amend, args.catalog_version, output_paths=(args.output,args.report), contexts=args.contexts) if args.amend else build_catalog(root, args.source)
        output = args.output.resolve() if args.output else None
        protected = {args.source.resolve(), *((root / path).resolve() for path in catalog['inputDigests'])}
        if output in protected or (args.report and args.report.resolve() in protected):
            raise CatalogError('output would overwrite a catalog source or frozen import')
        from tools.spacefox.current_catalog import current_coverage, current_view, load_registry
        eligibility = load_registry(root, catalog, source_path=args.source)
        product = catalog if eligibility is None else current_view(catalog, eligibility)['catalog']
        report = coverage_report(catalog) if eligibility is None else current_coverage(catalog, eligibility)
        data = canonical_bytes(product)
        for target, payload in [(output, data), (args.report, canonical_bytes(report))]:
            if target is None:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix='.catalog-', delete=False) as stream:
                temporary = Path(stream.name); stream.write(payload); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, target); temporary = None
        print(json.dumps({'schemaVersion': 1, 'catalogVersion': catalog['catalogVersion'],
                          'currentScope': None if eligibility is None else report['qualification'],
                          'eligibilityReviewCount': None if eligibility is None else len(report['reviewIds']),
                          'qualification': catalog['qualification'], 'sha256': hashlib.sha256(data).hexdigest(),
                          'bytes': len(data), 'counts': {k: len(v) for k, v in product['dictionaries'].items()}}, sort_keys=True))
        return 0
    except (CatalogError, OSError, ValueError) as exc:
        print(f'catalog: {exc}', file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    raise SystemExit(main())
