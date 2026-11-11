"""SPDX-License-Identifier: MIT. Saved composition evidence reconciliation."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'openspec/changes/compose-brighter-geography/evidence'

def read(path):
    return json.loads(Path(path).read_text())

def observation_errors(observation, scene):
    expected = {'time': scene['clock'], 'countdown': scene['countdown']['displayLabel']}
    expected.update({k: scene['fixture'][k]['displayLabel'] for k in ['rocket','operator','purpose','site']})
    expected.update({'field'+str(i): f['displayLabel'] for i,f in enumerate(scene['fields'])})
    actual = {t['role']:t['value'] for t in observation['text']}
    errors=[role for role,value in expected.items() if actual.get(role) != value]
    errors.extend('duplicate:'+role for role in expected if sum(t['role']==role for t in observation['text'])!=1)
    return errors

def final_errors(data, final_ids):
    errors=[]
    rows=data['observations']; wanted={(c,s['id']) for c in final_ids for s in data['scenes']}
    if {(o['candidate'],o['scene']) for o in rows} != wanted or len(rows)!=len(wanted):
        errors.append('incomplete-observations')
    for o in rows:
        scene=next(s for s in data['scenes'] if s['id']==o['scene'])
        if observation_errors(o,scene) or o['semanticErrors'] or o['geometryErrors'] or not o['verdict']['passed'] or o['verdict']['failures']:
            errors.append(o['candidate']+'/'+o['scene'])
    return errors

def generation_errors(banks):
    errors=[];known={'M2-11','M3-21','M2-31','M2-41','M2-51'};seen=set()
    for i,(bank,expected) in enumerate(zip(banks,[18,12,6]),1):
        if len(bank)!=expected:errors.append('count')
        for c in bank:
            signature=json.dumps([c['layout'],c['paint'],c.get('params',{})],sort_keys=True)
            if c['generation']!=i or c['id'] in seen or any(p not in known for p in c['parents']):errors.append('ancestry')
            if signature in seen:errors.append('duplicate')
            seen.update([signature,c['id']])
        known.update(c['id'] for c in bank)
    return errors
