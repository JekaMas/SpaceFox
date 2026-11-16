#!/usr/bin/env python3
"""Check audit inventory/evidence identities, not product performance or tests."""
import ast
import collections
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
ROOT=Path(__file__).resolve().parents[5];OUT=Path(__file__).resolve().parent
BASE='943f320c33b253b913eb8276d1c09b65d51a6c8a'
rows=list(csv.DictReader((OUT/'FILE-INVENTORY.csv').open()));by_path={r['path']:r for r in rows}
raw=subprocess.run(['git','ls-tree','-rlz','--full-tree',BASE],cwd=ROOT,capture_output=True,check=True).stdout
expected={}
for entry in raw.split(b'\0'):
    if not entry:continue
    header,path=entry.split(b'\t',1);mode,kind,blob,size=header.decode().split();expected[path.decode()]=(blob,int(size))
assert len(rows)==len(by_path)==18772 and set(by_path)==set(expected)
for path,row in by_path.items():
    assert (row['git_blob'],int(row['bytes']))==expected[path],path
    assert row['audit_note'] and 'PENDING'not in row['review_state'],path
for p in OUT.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
for p in OUT.glob('*.json'):json.loads(p.read_bytes())
reviews=json.loads((OUT/'SOURCE-REVIEW.json').read_bytes())
assert {p for p,r in by_path.items()if r['package']in('native-runtime','publisher-package','scheduler-workflows')}<=set(reviews)
resources=list(csv.DictReader((OUT/'RESOURCE-INVENTORY.csv').open()))
assert len(resources)==275
for row in resources:assert hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
scan=json.loads((OUT/'PYTHON-RESOURCE-SCAN.json').read_bytes());assert len(scan)==431 and not any('error'in r for r in scan)
assert all(r['path']in by_path for r in scan)
assert len(json.loads((OUT/'TOOL-INVENTORY.json').read_bytes()))==163
assert len(json.loads((OUT/'SUPPORTING-SCRIPT-SCAN.json').read_bytes()))==94
batch=json.loads((OUT/'BATCH-COST.json').read_bytes());assert (batch['objects'],batch['uniqueObjectBytes'],batch['nextPrefixReadCount'],batch['nextPrefixHashBytes'])==(17,50005,153,527343)
host=json.loads((OUT/'HOST-MEASUREMENT.json').read_bytes());assert host['artifact_files']==106 and host['artifact_bytes']==606276
cache=json.loads((OUT/'CACHE-RELEASE-MEASUREMENT.json').read_bytes());assert cache['phases'][2]['python_traced_current']==63975174 and cache['phases'][3]['python_traced_current']==8615
findings=set()
for name in ('NATIVE.md','HOST-AND-REQUESTS.md','RESOURCES-AND-TOOLS.md'):findings.update(re.findall(r'\*\*([A-Z]+-\d+)\b',(OUT/name).read_text()))
assert len(findings)==27,findings
# New audit files/task link must not quietly alter a production owner or test.
scopes=['watchface','tools','tests','catalog','schemas','assets','locales','prototype','.github','deploy','release']
product_diff=subprocess.run(['git','diff','--exit-code',BASE,'--',*scopes],cwd=ROOT,capture_output=True,check=False)
assert product_diff.returncode==0,'product inputs changed'
changed=subprocess.run(['git','diff','--name-only',BASE],cwd=ROOT,capture_output=True,text=True,check=True).stdout.splitlines()
assert all(p=='openspec/changes/spacefox-watchface/tasks.md'or p.startswith(str(OUT.relative_to(ROOT))+'/')for p in changed),changed
# Preserve source identities from actual completed measurements.
env=json.loads((OUT/'MEASUREMENT-ENVIRONMENT.json').read_bytes())
for name,digest in env['source_sha256'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
encoding=[]
for entry in json.loads((OUT/'SUPPORTING-SCRIPT-SCAN.json').read_bytes()):
    p=ROOT/entry['path']
    try:p.read_bytes().decode('utf-8')
    except UnicodeDecodeError as e:encoding.append({'path':entry['path'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'error':str(e)})
(OUT/'TEXT-ENCODING-NOTES.json').write_text(json.dumps(encoding,indent=2)+'\n')
result={'status':'PASS','base':BASE,'tracked_file_rows':len(rows),'tracked_bytes':sum(int(r['bytes'])for r in rows),'native_source_files':38,'publisher_modules':19,'python_files_ast_parsed':len(scan),'native_resource_rows':len(resources),'supporting_scripts':94,'engineering_commands':163,'findings':len(findings),'review_methods':dict(collections.Counter(r['review_state']for r in rows)),'product_or_test_diff':False,'product_tests_rerun':False,'paid_or_provider_calls':False,'proof_boundary':'Audit artifact consistency/source identity only, not independent semantic review, native runtime, physical memory, battery, CI performance or release acceptance'}
(OUT/'AUDIT-CHECK.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
