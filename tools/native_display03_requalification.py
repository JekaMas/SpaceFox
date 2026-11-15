"""Reconstruct the previous admitted build and check the DISPLAY03 delta.

This grants only finite software-language admission, not physical-device or
native-speaker approval. Receipts bind the actual SDK test inputs and outcomes.
"""
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path


def validate(root, catalog):
    from tools.generate_native_version import validate as validate_version
    from tools.native_display03_probe import inputs, NAMES
    from tools.native_release_version_requalification import validate as previous
    from tools.run_native_tests import parse_output
    from tools.verify_display03_pixels import verify as verify_pixels
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    def checked(item):
        path = Path(item['path'])
        if path.is_absolute() or '..' in path.parts or not (root/path).is_file():
            raise ValueError('invalid DISPLAY03 proof input')
        raw = (root/path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('DISPLAY03 proof input changed: '+str(path))
        return root/path
    record = json.loads(checked(proof['display03DeltaProof']).read_text())
    if record.get('scope') != 'display03-primary-native-software' or record.get('status') != 'passed':
        raise ValueError('DISPLAY03 proof incomplete')
    old = json.loads(checked(record['priorCatalog']).read_text())
    prior_proof = old['supportPolicy']['softwareQualificationProof']
    if {k:v for k,v in proof.items() if k != 'display03DeltaProof'} != prior_proof:
        raise ValueError('prior locale proof changed')
    comparable = json.loads(json.dumps(catalog))
    comparable['supportPolicy']['softwareQualificationProof'] = prior_proof
    if comparable != old:
        raise ValueError('catalog outside DISPLAY03 proof changed')
    support = ('tools/native_display03_requalification.py','tools/native_language_policy.py',
               'tools/verify_display03_pixels.py','tools/spacefox/native_profile.py',
               'tools/build_native_resources.py','tools/native_aod_map.py',
               'watchface/resource-inputs/map-views.json','watchface/resource-inputs/aod-map-views.json',
               'tests/test_display03_outline.py')
    if record['supportInputs'] != {name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in support}:
        raise ValueError('DISPLAY03 support input closure differs')
    if record['nativeInputs'] != inputs(root):
        raise ValueError('DISPLAY03 native input closure differs')
    for item in record['evidence'].values():
        checked(item)
    receipt = json.loads(checked(record['evidence']['nativeReceipt']).read_text())
    log = checked(record['evidence']['nativeLog']).read_text()
    if receipt.get('inputHashes') != record['nativeInputs'] or receipt.get('rawExit') != 1:
        raise ValueError('DISPLAY03 native receipt differs')
    if parse_output(log, receipt['rawExit'], NAMES)['status'] != 'passed':
        raise ValueError('DISPLAY03 native tests incomplete')
    for language in ('en','ru','de','fr','es'):
        if 'PRIMARY_DATE locale='+language+' ' not in log:
            raise ValueError('DISPLAY03 primary language observation missing')
    if json.loads(json.dumps(verify_pixels(root))) != json.loads(checked(record['evidence']['pixelReceipt']).read_text()):
        raise ValueError('DISPLAY03 native pixel observation differs')
    runtime=checked(record['evidence']['readyLog']).read_text()
    ready='D03_READY selection=77d4b3173b019ee84b7eb751e81ccb7a47edfba560a54166bfb47f441e8b7b37 map=true outline=true rocket=true flag=true'
    begin='D03_BG_BEGIN ready=true allowed=true';end='D03_BG_END ready=true context=true'
    if not (0 <= runtime.find(ready) < runtime.find(begin) < runtime.find(end)):
        raise ValueError('DISPLAY03 ready/refresh observation missing')
    cadence=checked(record['evidence']['cadenceLog']).read_text()
    wake=re.search(r'D03_WAKE ms=(\d+) display=0',cadence)
    if wake is None:raise ValueError('DISPLAY03 high wake callback missing')
    frame=re.search(r'D03_FRAME begin=(\d+) end=(\d+) utc=(\d+) display=0 mode=1 countdown=(T[+-] \d+:\d{2}:\d{2}).* wake='+wake.group(1),cadence[wake.end():])
    if frame is None or not 0 <= int(frame.group(2))-int(wake.group(1)) <= 1000:
        raise ValueError('DISPLAY03 wake frame latency missing')
    rows=[(int(a),int(u),v) for a,u,v in re.findall(r'D03_FRAME begin=(\d+) end=\d+ utc=(\d+) display=0 mode=1 countdown=(T[+-] \d+:\d{2}:\d{2})',cadence)]
    stable=False
    for start in range(len(rows)-4):
        segment=rows[start:start+5]
        if all(850<=segment[i+1][0]-segment[i][0]<=1150 and segment[i+1][1]-segment[i][1]==1 and segment[i+1][2]!=segment[i][2] for i in range(4)):
            stable=True;break
    if not stable:raise ValueError('DISPLAY03 automatic active cadence missing')
    validate_version(root)
    with tempfile.TemporaryDirectory(prefix='spacefox-display03-prior-') as temporary:
        target = Path(temporary)
        for folder in ('watchface','locales','tools','tests'):
            shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for folder in ('openspec','corpus','assets','catalog','schemas'):
            (target/folder).symlink_to(root/folder,target_is_directory=True)
        for name,item in record['priorSnapshots'].items():
            destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(checked(item),destination)
        for name in record['priorAbsent']:
            path=Path(name)
            if path.is_absolute() or '..' in path.parts:raise ValueError('invalid absent path')
            (target/path).unlink()
        if previous(target,old) != old['supportPolicy']['softwareQualifiedLocales']:
            raise ValueError('prior admitted build did not reconstruct')
    return catalog['supportPolicy']['softwareQualifiedLocales']
