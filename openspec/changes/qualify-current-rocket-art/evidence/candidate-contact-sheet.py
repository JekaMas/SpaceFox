"""Inspection-only source render; final binding proof uses generated resources."""
import base64
import html
import json
from pathlib import Path
import subprocess
from tools.spacefox.graphics import export_svg, fit_model_visual
from tools.spacefox.native_profile import rasterize

root=Path(__file__).resolve().parents[4]
out=Path(__file__).resolve().parent
manifest=json.loads((root/'catalog/source.json').read_text())
seed=json.loads((root/manifest['assetSeed']['path']).read_text())
facts={x['id']:x for x in seed['models']}
for c in manifest['curations']:
 for a in json.loads((root/c['path']).read_text())['assets']:
  if a['collection']=='models':facts[a['facts']['id']]=a['facts']
rows=json.loads((out/'model-matrix.json').read_text())['rows']
cache={}
for page in range(4):
 elems=['<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="1500" height="900"><rect width="1500" height="900" fill="#152432"/>']
 for i,row in enumerate(rows[page*50:(page+1)*50]):
  f=facts[row['asset_id'].split(':')[-1]];path=root/row['svg'];k=(str(path),tuple(f['exportSize']))
  if k not in cache:
   visual=fit_model_visual(export_svg(path.read_bytes(),f['exportSize']));_,png,_=rasterize([visual],54,124);cache[k]=base64.b64encode(png).decode()
  x,y=(i%10)*150,(i//10)*180
  elems.append(f'<image x="{x+48}" y="{y+10}" width="54" height="124" xlink:href="data:image/png;base64,{cache[k]}"/>')
  elems.append(f'<text x="{x+75}" y="{y+149}" text-anchor="middle" fill="white" font-size="11">{html.escape(row["name"][:23])}</text>')
  elems.append(f'<text x="{x+75}" y="{y+164}" text-anchor="middle" fill="#b8c9d8" font-size="9">{html.escape(row["configuration_id"])}</text>')
 elems.append('</svg>');data=subprocess.check_output(['rsvg-convert'],input=''.join(elems).encode());(out/f'candidate-current-{page+1:02}.png').write_bytes(data)
print('inspection renders:',len(rows),'unique_source_render_inputs:',len(cache),'sheets: 4')
