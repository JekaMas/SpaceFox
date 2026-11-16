#!/usr/bin/env python3
"""File-level static resource classification only; never executes project code."""
import ast
import base64
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT=Path(__file__).resolve().parents[5]
OUT=Path(__file__).resolve().parent
rows=list(csv.DictReader((OUT/'FILE-INVENTORY.csv').open()))
scan=json.loads((OUT/'PYTHON-RESOURCE-SCAN.json').read_text())
py={r['path']:r for r in scan}
resource=[];scripts=[];tools=[]
js_pattern=re.compile(r'fetch\s*\(|XMLHttpRequest|https?\.(?:get|request)|exec(?:Sync|File)?\s*\(|spawn(?:Sync)?\s*\(|readFile(?:Sync)?\s*\(|writeFile(?:Sync)?\s*\(|setInterval\s*\(|setTimeout\s*\(|requestAnimationFrame\s*\(|cancelAnimationFrame\s*\(|clearInterval\s*\(|clearTimeout\s*\(|(?:Resize|Mutation|Intersection)Observer|\.disconnect\s*\(|addEventListener\s*\(|removeEventListener\s*\(|new\s+(?:Image|Map|Set|Worker)|(?:drawImage|toDataURL|toBlob)\s*\(')
for r in rows:
 p=ROOT/r['path']
 if r['package']=='native-resources':
  raw=p.read_bytes();item={'path':r['path'],'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'kind':p.suffix,'dimension':'','details':''}
  if p.suffix=='.png':
   if raw[:8]!=b'\x89PNG\r\n\x1a\n':raise ValueError(str(p))
   w,h,depth,color=struct.unpack('>IIBB',raw[16:26]);item['dimension']=f'{w}x{h}';item['details']=f'PNG depth={depth},colorType={color}; compressed bytes not GPU allocation'
  elif p.suffix=='.fnt':
   text=raw.decode();common=next((s for s in text.splitlines()if s.startswith('common ')),'');item['details']=common
  elif p.suffix=='.json':
   value=json.loads(raw);item['details']=f'JSON {type(value).__name__}; load-on-demand, not all dictionaries resident'
   if p.name=='GraphemeProperties.json':item['details']=f'base64 property bytes={len(base64.b64decode(value))}; retained once by LocaleGraphemes'
  resource.append(item)
 if p.suffix in ('.js','.mjs','.html','.sh','.java') and r['package']!='historical-evidence':
  raw=p.read_bytes();text=raw.decode('utf-8',errors='replace');hits=[{'line':n,'text':s.strip()[:320]}for n,s in enumerate(text.splitlines(),1)if js_pattern.search(s)]
  vendor='vendor/'in r['path'];scripts.append({'path':r['path'],'package':r['package'],'vendor':vendor,'resource_sites':[]if vendor else hits,'boundary':'Pinned vendor dependency, invocation/bounds reviewed at caller; minified implementation not manually re-reviewed'if vendor else 'Text resource-site index, not JS/Java call-graph or runtime evidence'})
 if r['package']=='engineering-tools':
  row=py.get(r['path']);doc=''
  if p.suffix=='.py':
   tree=ast.parse(p.read_text());doc=(ast.get_docstring(tree)or'').split('\n')[0]
  calls=[]if row is None else [c for f in row['functions']for c in f['resource_calls']]
  names=collections.Counter(c['call']for c in calls)
  command_kind='Offline diagnostic/research/build command; not compiled into watchface or scheduled unless explicitly invoked'
  if r['path']in ('tools/cloud_feed.py','tools/cloud_inputs.py','tools/update_feed.py','tools/refresh_catalog.py'):command_kind='Scheduled host pipeline owner; resource-path review in SOURCE-REVIEW.json'
  tools.append({'path':r['path'],'bytes':int(r['bytes']),'boundary':command_kind,'module_doc':doc,'functions':0 if row is None else len(row['functions']),'resource_call_sites':len(calls),'calls':dict(names)})
with (OUT/'RESOURCE-INVENTORY.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(resource[0]),lineterminator="\n");w.writeheader();w.writerows(resource)
(OUT/'SUPPORTING-SCRIPT-SCAN.json').write_text(json.dumps(scripts,indent=2)+'\n')
(OUT/'TOOL-INVENTORY.json').write_text(json.dumps(tools,indent=2)+'\n')
summary={'native_resources':len(resource),'bytes':sum(x['bytes']for x in resource),'suffixes':dict(collections.Counter(x['kind']for x in resource)),'png_dimensions':dict(collections.Counter(x['dimension']for x in resource if x['kind']=='.png')),'supporting_scripts_scanned':len(scripts),'engineering_tools':len(tools),'proof_boundary':'File metadata and static resource call sites; no SDK/HTTP/CI/test execution'}
(OUT/'RESOURCE-SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
