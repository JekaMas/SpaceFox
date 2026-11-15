#!/usr/bin/env python3
"""Check an explicit current redraw receipt against source; does not run the SDK."""
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('--public-root',type=Path,required=True)
p.add_argument('--receipt',type=Path,required=True)
a=p.parse_args()
r=json.loads(a.receipt.read_text())
assert r['status']=='passed' and r['tests']['status']=='passed'
inputs=r['inputHashes']
for path,digest in inputs.items():
    f=a.public_root/path
    assert f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest()==digest,path
native={str(f.relative_to(a.public_root)) for f in (a.public_root/'watchface/source').rglob('*.mc')}
resources={str(f.relative_to(a.public_root)) for d in (a.public_root/'watchface').glob('resources*') if d.is_dir() for f in d.rglob('*') if f.is_file()}
recorded={n for n in inputs if n.startswith('watchface/source/') or n.startswith('watchface/resources/') or n.startswith('watchface/resources-')}
assert native|resources==recorded,'native source/resource inventory changed'
print('PASS current native source/resource and directed-test inputs match supplied receipt; no SDK execution or runtime comparison')
