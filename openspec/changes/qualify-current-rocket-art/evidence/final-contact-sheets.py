"""Inspection sheets of actual generated resources; no private reference input."""
import base64,html,json,re,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[4];out=Path(__file__).resolve().parent
source=(root/'watchface/source/generated/NativeModels.mc').read_text()
mapping=dict(re.findall(r'id\.equals\("([^\"]+)"\)\)\{return Rez\.Drawables\.(BundledModel\d+);\}',source))
main=json.loads((out/'model-matrix.json').read_text())['rows'];aux=json.loads((out/'auxiliary-matrix.json').read_text())['rows']
def sheet(rows,label,page,columns,cellw=150):
 width=columns*cellw;height=((len(rows)+columns-1)//columns)*180
 data=[f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}"><rect width="{width}" height="{height}" fill="#152432"/>']
 for i,row in enumerate(rows):
  identity=row.get('configuration_id',row.get('id'));name=mapping.get(identity);x=(i%columns)*cellw;y=(i//columns)*180
  if name:
   raw=(root/'watchface/resources/drawables'/(name+'.png')).read_bytes();encoded=base64.b64encode(raw).decode();data.append(f'<image x="{x+48}" y="{y+10}" width="54" height="124" xlink:href="data:image/png;base64,{encoded}"/>')
  else:data.append(f'<text x="{x+75}" y="{y+80}" text-anchor="middle" fill="white" font-size="12">no binding</text>')
  data.append(f'<text x="{x+75}" y="{y+149}" text-anchor="middle" fill="white" font-size="11">{html.escape(row["name"][:23])}</text>')
  data.append(f'<text x="{x+75}" y="{y+164}" text-anchor="middle" fill="#b8c9d8" font-size="9">{html.escape(identity)}</text>')
 data.append('</svg>');(out/f'{label}-{page:02}.png').write_bytes(subprocess.check_output(['rsvg-convert'],input=''.join(data).encode()))
for page in range(4):sheet(main[page*50:(page+1)*50],'bundled-current',page+1,10)
sheet(aux,'bundled-auxiliary',1,8)
print('required identities',len(main),'auxiliary identities',len(aux),'auxiliary unbound',sum(x['id'] not in mapping for x in aux))
