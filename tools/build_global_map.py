#!/usr/bin/env python3
"""Audit finite source-driven flat-map geography; never fetch or publish."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes
from tools.spacefox.global_map import GeographyError, audit_sites
from tools.spacefox.graphics import VisualError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'catalog/source.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--audit', action='store_true', required=True, help='render source coordinate contexts for every finite site')
    parser.add_argument('--scope', choices=('current', 'archive'), default='current',
                        help='audit source-dated current context roots or explicit full archive')
    args = parser.parse_args(argv)
    try:
        catalog = build_catalog(ROOT,args.source); output = args.output.resolve()
        from tools.spacefox.current_catalog import load_registry
        eligibility = load_registry(ROOT, catalog, source_path=args.source)
        context_report = None
        if args.audit and args.scope == 'current':
            from tools.spacefox.current_context import load_contexts, context_view, context_coverage
            if eligibility is None:
                raise GeographyError('current audit requires eligibility registry')
            contexts = load_contexts(ROOT, catalog)
            context_report = context_coverage(catalog, eligibility, contexts)
            catalog = context_view(catalog, eligibility, contexts)['catalog']
        if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT/'build'):
            raise GeographyError('in-checkout output must stay under build/')
        if args.audit:
            if output == args.source.resolve() or output in {(ROOT/p).resolve() for p in catalog['inputDigests']}:
                raise GeographyError('audit would overwrite catalog input')
            output.parent.mkdir(parents=True,exist_ok=True)
            report = audit_sites(ROOT,catalog,render_contexts=True)
            report['scope'] = args.scope
            if context_report is not None:
                report['currentContextCoverage'] = context_report
            from tools.spacefox.graphics import _atomic
            _atomic(output,canonical_bytes(report),'.audit-')
            print(json.dumps({k:v for k,v in report.items() if k != 'rows'},sort_keys=True));return 0
    except (CatalogError,VisualError,GeographyError,OSError,ValueError) as exc:
        print('global_map: '+str(exc),file=sys.stderr);return 1


if __name__ == '__main__':
    raise SystemExit(main())
