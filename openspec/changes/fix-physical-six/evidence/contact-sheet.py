"""Contact sheets for the catalog's current-evidence configurations."""
import base64
import html
import json
from pathlib import Path
import re
import subprocess
from tools.spacefox.catalog import build_catalog

root = Path(__file__).resolve().parents[4]
catalog = build_catalog(root)
registry = json.loads((root / catalog['source']['eligibility']['path']).read_text())['records']
source = (root / 'watchface/source/generated/NativeModels.mc').read_text()
lookup = dict(re.findall(r'id\.equals\("([^"]+)"\)\)\{return Rez\.Drawables\.(BundledModel\d+);\}', source))
rows = [(identity, entry['facts']['name']) for identity, entry in catalog['dictionaries']['configurations'].items()
        if registry[identity]['state'] == 'current-evidence']
rows.sort()
assert len(rows) == 175 and all(identity in lookup for identity, _ in rows)
out = Path(__file__).resolve().parent
for start in range(0, len(rows), 50):
    page = rows[start:start + 50]
    elements = ['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1500" height="900">', '<rect width="1500" height="900" fill="#152432"/>']
    for n, (identity, name) in enumerate(page):
        x, y = (n % 10) * 150, (n // 10) * 180
        raw = (root / 'watchface/resources/drawables' / (lookup[identity] + '.png')).read_bytes()
        uri = base64.b64encode(raw).decode('ascii')
        elements.append(f'<image x="{x + 48}" y="{y + 10}" width="54" height="124" xlink:href="data:image/png;base64,{uri}"/>')
        elements.append(f'<text x="{x + 75}" y="{y + 149}" text-anchor="middle" fill="white" font-size="11">{html.escape(name[:23])}</text>')
        elements.append(f'<text x="{x + 75}" y="{y + 164}" text-anchor="middle" fill="#b8c9d8" font-size="9">{html.escape(identity)}</text>')
    elements.append('</svg>')
    image = subprocess.check_output(['rsvg-convert'], input=''.join(elements).encode())
    (out / ('contact-current-%02d.png' % (start // 50 + 1))).write_bytes(image)
print('current-evidence rows:', len(rows), 'sheets:', (len(rows) + 49) // 50)
