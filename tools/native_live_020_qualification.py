"""Bind the reviewed 0.2.0 integration to the retained B3 qualification.

The predecessor and its locale proof remain unchanged. New observations are
limited to the FR165M SDK interaction; physical acceptance is not inferred.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from xml.etree import ElementTree as ET

from tools.native_b1_021_qualification import checked, native_inputs, test_inputs, sha
from tools.generate_native_version import validate as validate_version

BASE = 'openspec/changes/fix-device-watchdog/evidence/release-0.2.0/'
NATIVE_CHANGED = set('''watchface/manifest.xml watchface/source/FeedScene.mc watchface/source/FeedService.mc
watchface/source/LocalePresentation.mc watchface/source/NativeForegroundApp.mc
watchface/source/NativeForegroundCache.mc watchface/source/NativeImmutable.mc
watchface/source/NativeSfr.mc watchface/source/NativeUpcomingCache.mc
watchface/source/SceneContext.mc watchface/source/SceneRenderer.mc
watchface/source/SpaceFoxApp.mc watchface/source/SpaceFoxView.mc
watchface/source/generated/FallbackWorld.mc watchface/source/generated/NativeVersion.mc'''.split())
TEST_CHANGED = set('''watchface/runtime-b1-tests/ClockFirst021.mc watchface/runtime-b1-tests/ColdAcquisition.mc
watchface/runtime-b1-tests/DecodePending.mc watchface/runtime-b1-tests/IntegrationAdmission021.mc'''.split())
OWNER_CHANGED = {'tools/build_fallback_world.py','watchface/runtime-b2-tests/B2Tests.mc','watchface/runtime-b3-tests/B3Tests.mc',
                 'tools/b1_cold_probe.py','tools/native_language_policy.py','tools/release.py'}
SNAPSHOTS = NATIVE_CHANGED | TEST_CHANGED | OWNER_CHANGED
CURRENT_OWNERS = OWNER_CHANGED | {'tools/native_live_020_qualification.py','tests/test_live_020_admission.py'}
# A peer reviews this exact native closure; the record alone cannot repin it.
REVIEWED_NATIVE_SHA256 = 'e980fe90905ac41347838e082131f550b6f84e0ba4c77d0078a2244db5d2a879'


def native_digest(inputs):
    return hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def run_prior(root, catalog, snapshots):
    with tempfile.TemporaryDirectory(prefix='spacefox-live-023-prior-') as directory:
        target=Path(directory)
        for p in root.iterdir():
            if p.is_file(): os.link(p,target/p.name)
        for name in ('tools','watchface','locales','openspec','tests','assets','corpus','catalog','schemas','docs','release','prototype','.github','licenses'):
            source=root/name
            if source.is_dir(): shutil.copytree(source,target/name,copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name,ref in snapshots.items():
            destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.unlink(missing_ok=True);shutil.copyfile(root/ref['path'],destination)
        (target/'tools/native_live_020_qualification.py').unlink(missing_ok=True)
        prior=json.loads(json.dumps(catalog));prior['supportPolicy']['softwareQualificationProof'].pop('liveRuntime020Proof')
        destination=target/'locales/catalog.json';destination.unlink();destination.write_text(json.dumps(prior,indent=2,ensure_ascii=False)+'\n')
        command=('import json;from pathlib import Path;from tools.native_b3_023_qualification import validate;'
                 'p=Path.cwd();print(json.dumps(validate(p,json.loads((p/"locales/catalog.json").read_text()))))')
        result=subprocess.run([sys.executable,'-c',command],cwd=target,env={**os.environ,'PYTHONPATH':str(target)},capture_output=True,text=True)
        if result.returncode: raise ValueError('retained B3 proof failed: '+result.stderr[-3000:])
        return json.loads(result.stdout.strip().splitlines()[-1])


def validate(root,catalog):
    root=Path(root).resolve();proof=catalog['supportPolicy']['softwareQualificationProof']
    record=json.loads(checked(root,proof['liveRuntime020Proof']).read_text())
    prior=json.loads(checked(root,proof['b3Runtime023Proof']).read_text())
    b1=json.loads(checked(root,proof['b1Integration021Proof']).read_text())
    b2=json.loads(checked(root,proof['b2Runtime022Proof']).read_text())
    if record['scope']!='live-b3-020-reviewed-sdk' or record['version']!='0.2.0': raise ValueError('wrong live integration scope')
    native=native_inputs(root);old=prior['nativeInputs']
    if native!=record['nativeInputs'] or set(native)!=set(old) or {n for n in native if native[n]!=old[n]}!=NATIVE_CHANGED: raise ValueError('unexpected live native delta')
    if native_digest(native)!=REVIEWED_NATIVE_SHA256: raise ValueError('live native closure differs from reviewed source')
    tests=test_inputs(root);old_tests=prior['priorTestInputs']
    if tests!=record['testInputs'] or set(tests)!=set(old_tests) or {n for n in tests if tests[n]!=old_tests[n]}!=TEST_CHANGED: raise ValueError('unexpected live test delta')
    snapshots=record['priorSnapshots']
    if set(snapshots)!=SNAPSHOTS: raise ValueError('predecessor snapshot inventory changed')
    for name,ref in snapshots.items():
        expected=old.get(name) or old_tests.get(name) or prior['currentOwners'].get(name) or b2['currentOwners'].get(name) or b1['owners'].get(name)
        if expected is None or ref['sha256']!=expected: raise ValueError('predecessor snapshot does not match B2 proof: '+name)
        checked(root,ref)
    if set(record['currentOwners'])!=CURRENT_OWNERS or any(sha(root/name)!=digest for name,digest in record['currentOwners'].items()): raise ValueError('integration owner changed')
    old_manifest=checked(root,snapshots['watchface/manifest.xml']).read_bytes()
    if old_manifest.replace(b'version="0.1.23"',b'version="0.2.0"',1)!=(root/'watchface/manifest.xml').read_bytes(): raise ValueError('manifest delta exceeds version')
    app=ET.parse(root/'watchface/manifest.xml').getroot().find('{http://www.garmin.com/xml/connectiq}application')
    if app.get('id')!='ec8b7c8a8ea54ee9ac91ee6e7a674d15' or app.get('version')!='0.2.0': raise ValueError('integration version or UUID changed')
    validate_version(root)
    expected={'b3roll':'b3QueueAndRollover','net':'b1AnnouncedNetDisplayAndReopen','binding':'b3EstimatedQueueBinding','eligibility':'b3AdmissionAndUnknown','selection':'b3DisplayRetainedSelection','checkpoint':'b1QueueCheckpointFailure021','low':'b2LowUnmatchedPoint','facts':'b2AdmittedFactsWithoutArt','hour':'b2CapturedHourAndMissingPoint','decode':'b1RealDecodeTicksAndCancels','reserve':'b1LowHeapDefersOptionalDecode','rollover':'b1CapturedSuccessorTicksInFallback','cold':'b1ColdAcquisition'}
    if set(record['evidence'])!=set(expected)|{'replacement','frame','peer'}: raise ValueError('integration evidence inventory changed')
    from tools.run_native_tests import parse_output
    for key,case in expected.items():
        raw=checked(root,record['evidence'][key]).read_text()
        clean='\n'.join(line for line in raw.splitlines() if not re.fullmatch(r'(?:SF_VIEW mode=(?:HIGH|LOW) pending=(?:true|false)|SF_FG admission_begin)',line.strip()))
        if parse_output(clean,1,(case,))['status']!='passed': raise ValueError('SDK case failed: '+case)
    replacement=checked(root,record['evidence']['replacement']).read_text()
    if not all(v in replacement for v in ('REAL_REPLACEMENT marker_flip_during_sfr=true','REAL_REPLACEMENT admission_after_cancel=true','SF_FG admission_accepted','REAL_REPLACEMENT visual_complete=true')): raise ValueError('replacement witness incomplete')
    checked(root,record['evidence']['frame']);checked(root,record['evidence']['peer'])
    qualified=run_prior(root,catalog,snapshots)
    if qualified!=catalog['supportPolicy']['softwareQualifiedLocales']: raise ValueError('prior locale set changed')
    return qualified
