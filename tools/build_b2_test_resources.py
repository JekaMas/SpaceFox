#!/usr/bin/env python3
"""Extract existing captured/mutated schedule fixtures for native test resources."""
import json
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'watchface/runtime-b2-tests/resources'
data = json.loads((ROOT / 'tests/fixtures/watch_refresh_cache/packets.json').read_text())
values = {'B2Initial': data['packets']['initial'], 'B2InitialCatalog': data['catalogs']['initial']['catalog'], 'B2Moved': data['packets']['moved'], 'B2Different': data['packets']['different'],
          'B2DifferentCatalog': data['catalogs']['different']['catalog']}
integrity = json.loads((ROOT / 'tests/fixtures/watch_refresh_cache/integrity.json').read_text())
selected = (ROOT / 'tests/fixtures/basic_selected_scene/SelectedPackets.mc').read_text()
anchor = 'store.write("sf.obj.09d14343e538fc1e6abcbdd1add8f5a2883e77a9d99169218f91f53a569d891b",'
catalog, _ = json.JSONDecoder().raw_decode(selected[selected.index(anchor) + len(anchor):])
values.update(B2Ascent=integrity['packets']['ascentGood'], B2AscentCatalog=catalog)
files = {name + '.json': json.dumps({'raw': raw}, ensure_ascii=False, separators=(',', ':')) + '\n' for name, raw in values.items()}
files['data.xml'] = '<resources>' + ''.join('<jsonData id="%s" filename="%s.json"/>' % (n, n) for n in values) + '</resources>\n'
for name, expected in files.items():
    target = OUT / name
    if '--check' in sys.argv:
        if target.read_text() != expected: raise SystemExit('B2 fixture resource drift: ' + name)
    else:
        target.write_text(expected)
