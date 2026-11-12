#!/usr/bin/env python3
"""Build finite original-art geometry locally from the single active catalog."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.spacefox.catalog import CatalogError, build_catalog
from tools.spacefox.graphics import VisualError, build_pack, write_pack


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,default=ROOT/'catalog/source.json')
    parser.add_argument('--output',type=Path,required=True,help='dedicated local build directory')
    parser.add_argument('--root',action='append',dest='roots',help='typed catalog ID; repeat for bounded selection')
    args=parser.parse_args(argv)
    try:
        catalog=build_catalog(ROOT,args.source)
        from tools.spacefox.current_catalog import load_registry, current_view
        eligibility = load_registry(ROOT, catalog, source_path=args.source)
        if eligibility is not None:
            catalog = current_view(catalog, eligibility, referenced_ids=args.roots or [])['catalog']
        output=args.output.resolve()
        protected=[args.source.resolve(),*((ROOT/p).resolve() for p in catalog['inputDigests'])]
        for path in protected:
            if path == output or path.is_relative_to(output):
                raise VisualError('output must not contain catalog sources/imports')
        # Never use an existing source-controlled directory as the build store.
        if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT/'build'):
            raise VisualError('in-checkout output must stay under build/')
        pack=build_pack(ROOT,catalog,roots=args.roots)
        summary=write_pack(output,pack)
        summary['statistics']=pack['statistics']
        print(json.dumps(summary,sort_keys=True))
        return 0
    except (CatalogError,VisualError,OSError) as exc:
        print(f'export_visuals: {exc}',file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
