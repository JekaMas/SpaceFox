# SPDX-License-Identifier: MIT
"""Freeze actual browser render/measure/font/map dependencies before packet disclosure."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('selection');p.add_argument('output');a=p.parse_args();x=json.load(open(a.selection));files=[]
for root in ['prototype/features','prototype/qualification','prototype/fonts','prototype/vendor']:
 files +=[p for p in Path(root).rglob('*')if p.is_file()]
files +=[Path('prototype/layout-data.js')]+[p for p in Path('prototype/marker').iterdir() if p.is_file() and p.suffix in ('.js','.json','.html')]
out={**x,'sourceSHA256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(set(files))},'screenNativeRule':'For each locale ru,en select first non-null scene in bank order, then widest operator by grapheme count over locale (ID lexical tiebreak), excluding selected scene; deterministic lexical fallback if needed. Exactly four; never pick by render result.'}
Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2));print(len(files),'sources')
