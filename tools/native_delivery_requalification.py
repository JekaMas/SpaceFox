"""Validate the delivery delta while retaining prior locale evidence."""
import hashlib
import json
import re
import shutil
import tempfile
from pathlib import Path

BASE = 'openspec/changes/spacefox-watchface/evidence/delivery01/'
CASES = ('deliveryRejectedResponseRetainsScene', 'deliveryPendingDeadlineDoesNotMove',
         'deliverySceneEventsAndLateCompletion', 'deliveryVisualIdentityCases',
         'deliveryRealRegisteredDeadline', 'deliveryDuplicateCallbackDoesNotInvalidateBuild')

def validate(root, catalog):
    from tools.native_ux03_requalification import validate as prior_validate
    from tools.generate_native_version import validate as validate_identity
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    def checked(item):
        path = Path(item['path'])
        if path.is_absolute() or '..' in path.parts or not (root/path).is_file():
            raise ValueError('invalid delivery proof input')
        raw = (root/path).read_bytes()
        if hashlib.sha256(raw).hexdigest() != item['sha256']:
            raise ValueError('delivery proof input changed: '+str(path))
        return root/path
    record = json.loads(checked(proof['deliveryDeltaProof']).read_text())
    if record.get('scope') != 'delivery01-native-continuity' or record.get('status') != 'passed':
        raise ValueError('delivery proof incomplete')
    old = json.loads(checked(record['priorCatalog']).read_text())
    oldproof = old['supportPolicy']['softwareQualificationProof']
    if {k:v for k,v in proof.items() if k != 'deliveryDeltaProof'} != oldproof:
        raise ValueError('prior locale proof changed')
    comparable = json.loads(json.dumps(catalog))
    comparable['supportPolicy']['softwareQualificationProof'] = oldproof
    if comparable != old:
        raise ValueError('catalog outside delivery proof changed')
    for name,digest in record['sources'].items(): checked({'path':name,'sha256':digest})
    for item in record['evidence'].values(): checked(item)
    validate_identity(root)
    native = {str(p.relative_to(root)) for p in (root/'watchface/source').rglob('*.mc')}
    if not native <= set(record['sources']): raise ValueError('delivery native source closure incomplete')
    for name in ('native-unit-final','native-cold-final','native-retained-final','native-identity'):
        build = json.loads(checked(record['evidence'][name+'-build']).read_text())
        probe = checked(record['evidence'][name+'-probe'])
        if build['exitCode'] != 0 or hashlib.sha256(probe.read_bytes()).hexdigest() != build['probeSha256']:
            raise ValueError('delivery SDK build differs: '+name)
        for source,digest in {**build['productionSources'],**build['productionResources']}.items():
            if record['sources'].get(source) != digest: raise ValueError('delivery SDK input differs: '+source)
    unit = checked(record['evidence']['native-unit-final-log']).read_text()
    if parse_output(unit,1,CASES)['status'] != 'passed': raise ValueError('delivery native cases did not pass')
    identity = checked(record['evidence']['native-identity-log']).read_text()
    if parse_output(identity,1,('realPacketIdentityTransitions',))['status'] != 'passed':
        raise ValueError('delivery real-packet identity transition did not pass')
    cold = checked(record['evidence']['native-cold-final-log']).read_text()
    retained = checked(record['evidence']['native-retained-final-log']).read_text()
    version = (root/'watchface/source/generated/NativeVersion.mc').read_text()
    match = re.search(r'const BUILD = "([^"]+)"; const ID = "([0-9a-f]{8})";',version)
    if not match or ('DELIVERY_START version='+match.group(1)+' id='+match.group(2)+' detail='+match.group(1)+' '+match.group(2)) not in cold:
        raise ValueError('empty-face executing identity not observed')
    if 'NATIVE_RESPONSE feed code=200' not in cold or 'DELIVERY_RELOAD id=ll2:launch:' not in cold:
        raise ValueError('cold public-feed admission not observed')
    schedules = re.findall(r'NATIVE_SCHEDULE now=(\d+) requested=(\d+) registered=(\d+) last=(\d+)',cold)
    pending = next((row[2] for row in schedules if int(row[1])-int(row[0]) == 300 and row[1] == row[2]),None)
    if pending is None or cold.count(' registered='+pending) < 3:
        raise ValueError('pending deadline was not observed across reload')
    for token in ('DELIVERY_BUILD_FRAME normalRenderer=true rich=false',
                  'DELIVERY_DUPLICATE_RETAINED', 'DELIVERY_READY id=',
                  'DELIVERY_REJECTED_RETAINED id=', 'pendingRestore=true',
                  'DELIVERY_RESTORE_RETAINED id='):
        if token not in retained: raise ValueError('delivery native observation missing: '+token)
    if 'Out Of Memory' in cold or 'Out Of Memory' in retained:
        raise ValueError('delivery native memory failure')
    with tempfile.TemporaryDirectory(prefix='spacefox-delivery-prior-') as temporary:
        target = Path(temporary)
        for folder in ('watchface','locales','tools','tests'):
            shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for folder in ('openspec','corpus','assets','catalog','schemas'):
            (target/folder).symlink_to(root/folder,target_is_directory=True)
        for name,item in record['priorSnapshots'].items():
            dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(checked(item),dst)
        for name in record.get('priorAbsent', []):
            relative=Path(name)
            if relative.is_absolute() or '..' in relative.parts: raise ValueError('invalid prior absent path')
            path=target/relative
            if path.is_file(): path.unlink()
        (target/'locales/catalog.json').write_text(json.dumps(old,indent=2)+'\n')
        if prior_validate(target,old)!=old['supportPolicy']['softwareQualifiedLocales']:
            raise ValueError('retained UX03 proof failed')
    return catalog['supportPolicy']['softwareQualifiedLocales']
