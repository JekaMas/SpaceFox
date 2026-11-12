#!/usr/bin/env python3
"""Build source-driven finite map/globe selections; never fetch or publish."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes
from tools.spacefox.global_map import GeographyError, audit_sites, build_bundle, build_site_view, write_bundle
from tools.spacefox.graphics import VisualError, build_pack


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'catalog/source.json')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--site',action='append',default=[])
    parser.add_argument('--root',action='append',dest='roots')
    parser.add_argument('--kind',choices=('map','globe','both'),default='both')
    parser.add_argument('--retain-directory',type=Path,help='retain exactly previous current selection')
    parser.add_argument('--audit',action='store_true',help='render source coordinate contexts for every finite site')
    args = parser.parse_args(argv)
    try:
        catalog = build_catalog(ROOT,args.source); output = args.output.resolve()
        if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT/'build'):
            raise GeographyError('in-checkout output must stay under build/')
        if args.audit:
            if output == args.source.resolve() or output in {(ROOT/p).resolve() for p in catalog['inputDigests']}:
                raise GeographyError('audit would overwrite catalog input')
            output.parent.mkdir(parents=True,exist_ok=True)
            report = audit_sites(ROOT,catalog,render_contexts=True)
            from tools.spacefox.graphics import _atomic
            _atomic(output,canonical_bytes(report),'.audit-')
            print(json.dumps({k:v for k,v in report.items() if k != 'rows'},sort_keys=True));return 0
        if not 1 <= len(args.site) <= 2 or len(set(args.site)) != len(args.site):
            raise GeographyError('choose one or two distinct site IDs')
        kinds = ('map','globe') if args.kind == 'both' else (args.kind,)
        views = [build_site_view(ROOT,catalog,site,kind=kind) for site in args.site for kind in kinds]
        visuals = build_pack(ROOT,catalog,roots=args.roots) if args.roots else None
        bundle = build_bundle(visuals,views,previous_directory=args.retain_directory)
        print(json.dumps(write_bundle(output,bundle),sort_keys=True));return 0
    except (CatalogError,VisualError,GeographyError,OSError,ValueError) as exc:
        print('global_map: '+str(exc),file=sys.stderr);return 1


if __name__ == '__main__':
    raise SystemExit(main())
