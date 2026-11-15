"""Exercise retained internal source assembly for catalog tests, without a public exporter."""
import json
import shutil
from pathlib import Path

from tools.spacefox.catalog import build_catalog
from tools.spacefox.graphics import build_pack, write_pack

ROOT = Path(__file__).resolve().parents[1]


def source_pack(source, output, roots):
    # Resolve every recipe input and SVG against the same isolated owner.
    root = Path(source).resolve().parent.parent
    catalog = build_catalog(root, source)
    pack = build_pack(root, catalog, roots=roots)
    write_pack(output, pack)
    return json.loads((output / 'manifest.json').read_bytes())


def add_historical_inputs(root, historical_source):
    """Copy the old recipe closure absent from the current temporary catalog."""
    for relative in build_catalog(ROOT, historical_source)['inputDigests']:
        target = root / relative
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
