#!/usr/bin/env python3
"""Observe one captured current Starbase scene through the actual native renderer."""
import json
import sys
from pathlib import Path
if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.native_full_visual_runtime import GROUPS, build_probe
from tools.native_current_runtime import observe

identity = json.loads(Path(sys.argv[1]).read_text())
GROUPS['basic-map'] = (identity['uuid'], identity['basename'])
source = observe(identity['url'])
anchor = 'var elapsed=System.getTimer()-requested;'
assert source.count(anchor) == 1
source = source.replace(anchor, '''System.println("BASIC_MAP_CONTEXT site="+view.context.site+" rocket="+view.context.rocket);ensure(view.context.site.equals("US · SpaceX Starbase, TX, USA")&&view.context.rocket.equals("Starship V3"),"captured context mismatch");ensure(rich.scene["position"]!=null&&rich.mapBitmap!=null&&rich.bitmap!=null,"captured map/rocket mismatch");System.println("BASIC_MAP site="+view.context.site+" rocket="+view.context.rocket+" siteId="+feed.packet.document["launch"]["site_id"]+" modelId="+feed.packet.document["launch"]["configuration_id"]+" position="+rich.scene["position"]+" mapBitmap=true rocketBitmap=true markerAnchor=335,165 sourceSelection="+rich.selectionHash);''' + anchor)
result = build_probe(Path(sys.argv[2]), source, group='basic-map')
print(json.dumps({key: result[key] for key in ('exitCode', 'packageName', 'packageSha256')}))
raise SystemExit(result['exitCode'])
