#!/usr/bin/env python3
"""Build a sparse LOW outline from the same fixed-site map geometry.

The 130px image uses the center-right active projection at twice its prior
horizontal scale. SceneRenderer applies the same projection to the point.
"""
from PIL import Image, ImageDraw
import json, subprocess, tempfile

def outline(mapping):
    image=Image.new('RGBA',(130,130),(0,0,0,0))
    draw=ImageDraw.Draw(image)
    for polygon in mapping['polygons']:
        if len(polygon)>=3:
            points=[(round(2*x/3)-130,round(y/3)) for x,y in polygon]
            draw.line(points+[points[0]],fill=(190,225,240,255),width=1)
    # Keep the outline within the round screen at its fixed placement.
    pixels=image.load()
    for y in range(130):
        for x in range(130):
            if y+20>=100 or (x+190-195)**2+(y+20-195)**2 > 190**2:
                pixels[x,y]=(0,0,0,0)
    return image

def additional_maps(root):
    sites=json.loads((root/'watchface/resource-inputs/aod-map-views.json').read_text())['sites']
    with tempfile.NamedTemporaryFile('w',suffix='.json') as f:
        json.dump([site['point'] for site in sites],f);f.flush()
        maps=json.loads(subprocess.check_output(['node',str(root/'tools/native_map_paths.js'),f.name]))
    return maps
