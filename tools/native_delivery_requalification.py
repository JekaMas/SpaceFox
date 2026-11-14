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
         'deliveryRealRegisteredDeadline', 'deliveryDuplicateCallbackDoesNotInvalidateBuild',
         'deliveryModeCallbacksAreIdempotent', 'deliveryVisualWaitsForMatchingBatch',
         'deliveryPendingAssetsAreNotIncomplete')

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
    for name in ('native-unit-final','native-cold-final','native-retained-final','native-identity','native-sleep-final'):
        build = json.loads(checked(record['evidence'][name+'-build']).read_text())
        probe = checked(record['evidence'][name+'-probe'])
        execution = json.loads(checked(record['evidence'][name+'-execution']).read_text())
        if build['exitCode'] != 0 or hashlib.sha256(probe.read_bytes()).hexdigest() != build['probeSha256']:
            raise ValueError('delivery SDK build differs: '+name)
        if (execution.get('programSha256') != build['packageSha256'] or
            execution.get('applicationUuid') != build['applicationUuid'] or
            execution.get('sourceSetSha256') != build['sourceSetSha256']):
            raise ValueError('delivery SDK launch binding differs: '+name)
        if name in ('native-cold-final','native-retained-final','native-sleep-final'):
            if execution.get('preLaunchCopiedSha256') != build['packageSha256'] or build['ownerTag'] not in checked(record['evidence'][name+'-log']).read_text():
                raise ValueError('delivery SDK executing owner differs: '+name)
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
    timed = [(int(m.group(1)),m.start()) for m in re.finditer(r'NATIVE_METRIC phase=temporal-start[^\n]* utc=(\d+)',cold)]
    due_event = next((pos for when,pos in timed if when >= int(pending)),None)
    build_at = cold.find('NATIVE_METRIC phase=sfr-build-start')
    ready_at = cold.find('DELIVERY_READY id=')
    if (due_event is None or build_at < due_event or ready_at < build_at or
        'NATIVE_GET path=descriptors/' not in cold[due_event:build_at] or
        'NATIVE_REJECTION' in cold[:ready_at] or 'Out Of Memory' in cold[:ready_at]):
        raise ValueError('natural pending batch did not produce its complete visual')
    for token in ('DELIVERY_BUILD_FRAME normalRenderer=true rich=false',
                  'DELIVERY_DUPLICATE_RETAINED', 'DELIVERY_READY id=',
                  'DELIVERY_REJECTED_RETAINED id=', 'pendingRestore=true',
                  'DELIVERY_RESTORE_RETAINED id='):
        if token not in retained: raise ValueError('delivery native observation missing: '+token)
    if 'Out Of Memory' in cold or 'Out Of Memory' in retained:
        raise ValueError('delivery native memory failure')
    sleep = checked(record['evidence']['native-sleep-final-log']).read_text()
    receipt = json.loads(checked(record['evidence']['native-sleep-final-receipt']).read_text())
    sleep_build = json.loads(checked(record['evidence']['native-sleep-final-build']).read_text())
    if receipt.get('inputProgramSha256') != sleep_build.get('packageSha256') or receipt.get('preLaunchCopiedSha256') != sleep_build.get('packageSha256'):
        raise ValueError('sleep launch input does not match compiled program')
    if ('SLEEP_START build='+match.group(1)+' id='+match.group(2)) not in sleep or sleep_build['ownerTag'] not in sleep:
        raise ValueError('sleep runtime source identity missing')
    events = ('SLEEP_READY launch=', 'SLEEP_CHECK event=sleep-callback mode=1',
              'SLEEP_CHECK event=low-frame mode=1', 'SLEEP_CHECK event=wake-callback mode=0',
              'SLEEP_CHECK event=display-mode mode=0')
    positions = [sleep.find(event) for event in events]
    if min(positions) < 0 or positions != sorted(positions) or 'SLEEP_CONTINUITY_FAILED' in sleep:
        raise ValueError('sleep round trip is incomplete')
    low = sleep[positions[1]:positions[3]]
    if 'NATIVE_RESPONSE' in low or 'sfr-step-enter' in low:
        raise ValueError('instrumented activity occurred during low mode')
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
