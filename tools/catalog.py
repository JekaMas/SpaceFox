#!/usr/bin/env python3
"""Validate/build publisher metadata locally; never fetch or publish."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

# Permit the documented `python3 -B tools/catalog.py` from a source checkout.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT / 'catalog/source.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    temporary = None
    try:
        catalog = build_catalog(ROOT, args.source)
        output = args.output.resolve()
        protected = {args.source.resolve(), *((ROOT / path).resolve() for path in catalog['inputDigests'])}
        if output in protected:
            raise CatalogError('output would overwrite a catalog source or frozen import')
        data = canonical_bytes(catalog)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=output.parent, prefix='.catalog-', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
        temporary = None
        print(json.dumps({'schemaVersion': 1, 'catalogVersion': catalog['catalogVersion'],
                          'qualification': catalog['qualification'], 'sha256': hashlib.sha256(data).hexdigest(),
                          'bytes': len(data), 'counts': {k: len(v) for k, v in catalog['dictionaries'].items()}}, sort_keys=True))
        return 0
    except (CatalogError, OSError) as exc:
        print(f'catalog: {exc}', file=sys.stderr)
        return 1
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    raise SystemExit(main())
