#!/usr/bin/env python3
"""Static hash/read count over the unchanged retained real native batch."""
import hashlib
import json
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parents[5]
FIXTURE=ROOT/'openspec/changes/spacefox-watchface/evidence/fields018/peer-stock390/Probe.mc'
found={}
for match in re.finditer(r'"(?:[^"\\]|\\.)*"',FIXTURE.read_text()):
    try:value=json.loads(match.group())
    except (ValueError,TypeError):continue
    if not isinstance(value,str) or not value.startswith('{'):continue
    try:document=json.loads(value)
    except ValueError:continue
    if isinstance(document,dict) and document.get('type')=='native-transfer':
        found[hashlib.sha256(value.encode()).hexdigest()]=document
if len(found)!=1:raise ValueError('expected one exact retained transfer')
digest,document=next(iter(found.items()));sizes=[r[2]for r in document['objects']];n=len(sizes)
result={'transfer':digest,'objects':n,'uniqueObjectBytes':sum(sizes),'nextPrefixReadCount':n*(n+1)//2,'nextPrefixHashBytes':sum((n-i)*v for i,v in enumerate(sizes)),'boundary':'Static source-derived operation count over retained real stock fixture, no HTTP or watch execution'}
Path(__file__).with_name('BATCH-COST.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
