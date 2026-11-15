#!/usr/bin/env python3
"""Build a sparse LOW outline from the same fixed-site map geometry.

The 390px image uses the exact ACTIVE map geometry and coordinate system.
"""
from PIL import Image, ImageDraw
import json, subprocess, tempfile

def outline(mapping):
    # Draw the original ACTIVE projection at its native 390px coordinates.
    image=Image.new('RGB',(390,390),(0,0,0))
    draw=ImageDraw.Draw(image)
    for polygon in mapping['polygons']:
        if len(polygon)>=3:
            points=[(round(x),round(y)) for x,y in polygon]
            draw.line(points+[points[0]],fill=(190,225,240),width=1)
    return image

def additional_maps(root):
    sites=json.loads((root/'watchface/resource-inputs/aod-map-views.json').read_text())['sites']
    with tempfile.NamedTemporaryFile('w',suffix='.json') as f:
        json.dump([site['point'] for site in sites],f);f.flush()
        maps=json.loads(subprocess.check_output(['node',str(root/'tools/native_map_paths.js'),f.name]))
    return maps
