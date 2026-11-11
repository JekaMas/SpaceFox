"""MIT. Build the report's vector/PNG contact sheet from accepted decorated previews."""
import json
import math
import subprocess
import xml.etree.ElementTree as ET

from tools.build_rocket_pack import NS, PACK, ROOT

ET.register_namespace('', NS)
catalog = json.loads((PACK / 'catalog.json').read_text())
models = catalog['models']
cols, row_height = 6, 330
root = ET.Element('{' + NS + '}svg', {'width': '1200', 'height': str(50 + row_height * math.ceil(len(models) / cols))})
ET.SubElement(root, '{' + NS + '}rect', {'width': '100%', 'height': '100%', 'fill': '#050a11'})
title = ET.SubElement(root, '{' + NS + '}text', {'x': '18', 'y': '29', 'fill': '#eef5f6', 'font-family': 'sans-serif', 'font-size': '20'})
title.text = 'SpaceFox · модели и происхождение · исходники ×2'
for i, model in enumerate(models):
    x, y = 12 + i % cols * 198, 44 + i // cols * row_height
    ET.SubElement(root, '{' + NS + '}rect', {'x': str(x), 'y': str(y), 'width': '186', 'height': '316', 'rx': '12', 'fill': '#0b1722', 'stroke': '#2d4558'})
    art = ET.parse(PACK / model['decoratedPreview']['svg']['path']).getroot()
    for key, value in {'x': x + 39, 'y': y + 12, 'width': 108, 'height': 248}.items(): art.set(key, str(value))
    root.append(art)
    label = ET.SubElement(root, '{' + NS + '}text', {'x': str(x + 93), 'y': str(y + 287), 'text-anchor': 'middle', 'fill': '#e0ebf0', 'font-family': 'sans-serif', 'font-size': '15'})
    label.text = model['name']
target = ROOT / 'docs/rocket-models-sheet.svg'
target.write_bytes(ET.tostring(root))
subprocess.run(['rsvg-convert', '-o', str(target.with_suffix('.png')), str(target)], check=True)
