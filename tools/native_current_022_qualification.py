"""Bind the 0.2.2 merge to retained parent proofs and the focused SDK receipts.

Parent observations remain historical; this check does not claim that they ran
on the merged bytes or establish phone/device/Store acceptance.
"""
import gzip
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET
from tools.native_b1_021_qualification import checked, native_inputs, test_inputs, sha
from tools.run_native_tests import parse_output
from tools.generate_native_version import validate as validate_version

PARENTS = {
    'liveRuntime020Proof': 'c40f00937f481615fe576b25f9e3f2fa625d75a1bdc82327537dcaa2d48bbad2',
    'integration022Proof': '5098f4de838eddbb4a16cefa3607a398a29442003aaede43be4d90d653eed6f6',
}
CASES = ('b1QueueCheckpointFailure021','b1TailCleanupRechecksOwnership',
         'b1OwnerStopReleasesPendingWork','b2LowUnmatchedPoint',
         'b2AdmittedFactsWithoutArt','b1RealDecodeTicksAndCancels','b1LowHeapDefersOptionalDecode',
         'b1ColdAcquisition','integrationBatchCorruptPrefixBeforeCompletion',
         'b1MissingChunkRecovery022','b1ReboundQueueRead022',
         'b1DecodingTextCacheRu022','b3EstimatedQueueBinding','deliveryPackedMapIdentity')

def body_digest(record):
    body=json.loads(json.dumps(record));body['owners'].pop('tools/release.py')
    return hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()

def validate(root,catalog):
    from tools.release import CURRENT_INTEGRATION_PROOF_BODY_SHA256
    root=Path(root).resolve();proof=catalog['supportPolicy']['softwareQualificationProof']
    rec=json.loads(checked(root,proof['currentIntegration022Proof']).read_text())
    if rec['scope']!='live-performance-current-022' or rec['version']!='0.2.2':raise ValueError('wrong current integration scope')
    if body_digest(rec)!=CURRENT_INTEGRATION_PROOF_BODY_SHA256:raise ValueError('current integration differs from reviewed closure')
    policy=json.loads(json.dumps(catalog));policy['supportPolicy']['softwareQualificationProof'].pop('currentIntegration022Proof')
    encoded=json.dumps(policy,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    if hashlib.sha256(encoded).hexdigest()!=rec['catalogSha256']:raise ValueError('current locale policy changed')
    for name,digest in PARENTS.items():
        if proof[name]['sha256']!=digest:raise ValueError('historical parent proof changed: '+name)
        checked(root,proof[name])
    if 'Status: independent software review GREEN' not in checked(root,rec['historicalPeer']).read_text():raise ValueError('historical peer evidence absent')
    parent=json.loads(checked(root,rec['peerReviewedProof']).read_text())
    if rec['peerReviewedProof']['sha256'] != '9838392688273e99b88e3808b4a4a24e7f549e4a97d418386ba461aa2243592c':raise ValueError('peer-reviewed proof changed')
    original=checked(root,rec['preTypeView']).read_text()
    if hashlib.sha256(original.encode()).hexdigest()!=parent['nativeInputs']['watchface/source/SpaceFoxView.mc']:raise ValueError('peer-reviewed view changed')
    old='var decodingText=null;var decodingMetricInput=null;var decodingMetricText=null;'
    new='var decodingText as Array or Null=null;var decodingMetricInput as Array or Null=null;var decodingMetricText as Array or Null=null;'
    expected_view=original.replace(old,new)
    app_version=ET.parse(root/'watchface/manifest.xml').getroot().find('{http://www.garmin.com/xml/connectiq}application').get('version')
    if app_version in ('0.2.4','0.2.5'):
        before='var remaining=_schedule.remainingSeconds(now);var estimated=context!=null&&context.displayTarget!=null;'
        after='var remaining=_schedule.remainingSeconds(now);'
        if expected_view.count(before)!=1:raise ValueError('historical countdown owner changed')
        expected_view=expected_view.replace(before,after).replace('(estimated?"~":"")+CountdownFormat.format(remaining)','CountdownFormat.format(remaining)').replace('(estimated?"~":"")+CountdownFormat.minutes(remaining)','CountdownFormat.minutes(remaining)')
    if original.count(old)!=1 or (app_version!='0.2.5' and (root/'watchface/source/SpaceFoxView.mc').read_text()!=expected_view):raise ValueError('view source exceeds reviewed type and countdown changes')
    changed={n for n in parent['nativeInputs'] if parent['nativeInputs'][n]!=rec['nativeInputs'].get(n)}
    if changed!={'watchface/source/SpaceFoxView.mc','watchface/source/generated/NativeVersion.mc'} or set(parent['nativeInputs'])!=set(rec['nativeInputs']):raise ValueError('compiler fix native delta changed')
    app=ET.parse(root/'watchface/manifest.xml').getroot().find('{http://www.garmin.com/xml/connectiq}application')
    current=native_inputs(root);old=rec['nativeInputs']
    if app.get('version') in ('0.2.3','0.2.4','0.2.5'):
        # The original 0.2.2 locale/renderer proof remains historical. The
        # current trusted-snapshot change is independently reviewed at release;
        # require its exact file-level scope and retain unchanged test inputs.
        allowed=set('''watchface/manifest.xml watchface/source/generated/NativeVersion.mc
          watchface/source/FeedScene.mc watchface/source/FeedService.mc
          watchface/source/LaunchReminder.mc watchface/source/LaunchReminderForeground.mc
          watchface/source/NativeBridgeFeed.mc watchface/source/NativeCache.mc
          watchface/source/NativeFeed.mc watchface/source/NativeForegroundApp.mc
          watchface/source/NativeForegroundCache.mc watchface/source/NativeIncoming.mc
          watchface/source/NativeIncrementalJson.mc watchface/source/NativeJson.mc
          watchface/source/NativeTransfer.mc watchface/source/NativeUpcomingCache.mc
          watchface/source/SpaceFoxApp.mc watchface/source/NativeAssetHelpers.mc
          watchface/source/NativeTrustedSnapshot.mc'''.split())
        if app.get('version') in ('0.2.4','0.2.5'): allowed.add('watchface/source/SpaceFoxView.mc')
        if app.get('version')=='0.2.5': allowed.update({'watchface/source/NativeDisplayLifecycle.mc','watchface/source/SceneLifecycle.mc'})
        changed={n for n in set(current)|set(old) if current.get(n)!=old.get(n)}
        if changed!=allowed:raise ValueError('trusted snapshot native delta differs')
        changedOwners={'tools/native_current_022_qualification.py','tools/release.py',
                       'tools/cloud_feed.py','tools/spacefox/cloud.py','tools/spacefox/native_motion.py',
                       'tests/test_release_020_predecessor.py','tests/test_current_022_admission.py','release/signing-identity.json'}
        if app.get('version') in ('0.2.4','0.2.5'):
            changedOwners.update({'.github/workflows/update-feed.yml','tools/update_feed.py','tools/spacefox/publisher.py','tools/spacefox/provider.py','tools/spacefox/schedule.py','tools/spacefox/wire.py','tests/test_performance021_a.py','watchface/runtime-b2-tests/B2Tests.mc','watchface/runtime-b3-tests/B3Tests.mc'})
    else:
        if current!=old:raise ValueError('current native inputs changed')
        changedOwners=set()
    current_tests=test_inputs(root);historical_tests=rec['testInputs']
    changed_tests={n for n in set(current_tests)|set(historical_tests) if current_tests.get(n)!=historical_tests.get(n)}
    allowed_tests={'watchface/runtime-b1-tests/ClockFirst021.mc','watchface/runtime-b1-tests/ColdAcquisition.mc','watchface/runtime-b1-tests/DecodePending.mc'} if app.get('version') in ('0.2.4','0.2.5') else set()
    if changed_tests!=allowed_tests:raise ValueError('current test input delta changed')
    for name,digest in rec['owners'].items():
        if name not in changedOwners and sha(root/name)!=digest:raise ValueError('current integration owner changed: '+name)
    if set(rec['cases'])!=set(CASES):raise ValueError('current SDK case inventory changed')
    for name in CASES:
        raw=checked(root,rec['cases'][name]).read_text()
        clean='\n'.join(x for x in raw.splitlines() if not re.fullmatch(r'(?:SF_VIEW mode=(?:HIGH|LOW) pending=(?:true|false)|SF_FG admission_begin|SF_FG chunk_wait|SF_FG admission_failed)',x.strip()))
        if parse_output(clean,1,(name,))['status']!='passed':raise ValueError('current SDK case failed: '+name)
    if hashlib.sha256(gzip.decompress(checked(root,rec['program']).read_bytes())).hexdigest()!=rec['programSha256']:raise ValueError('replacement SDK program changed')
    checked(root,rec['fixtureArchive'])
    for ref in rec['probeSources'].values():checked(root,ref)
    seed=checked(root,rec['seed']).read_text();seed='\n'.join(x for x in seed.splitlines() if not re.fullmatch(r'SF_VIEW mode=(?:HIGH|LOW) pending=(?:true|false)',x.strip()))
    if parse_output(seed,1,('seedCapturedPair',))['status']!='passed':raise ValueError('replacement seed failed')
    run=checked(root,rec['replacementRun']).read_text()
    if "DATA_BEFORE_SEED []" not in run or "DATA_AFTER_SEED ['SINGLE.DAT', 'SINGLE.IDX']" not in run or 'PROGRAM_SHA256 '+rec['programSha256'] not in run or 'PAIR_COMPLETE_STABLE_30S' not in run:raise ValueError('replacement run incomplete')
    raw=checked(root,rec['replacement']).read_text()
    if any(x in raw for x in ('Encountered an app crash','Out Of Memory Error','PAIR_PRECONDITION_FAILED','SF_BG feed_http=')):raise ValueError('current replacement witness contaminated')
    if not all(x in raw for x in ('PAIR_PRECONDITION gen=56 sfr=true','REAL_REPLACEMENT marker_flip_during_sfr=true','REAL_REPLACEMENT admission_after_cancel=true','SF_FG admission_accepted','PAIR_ACCEPTED gen=57','REAL_REPLACEMENT visual_complete=true')):raise ValueError('current replacement lifecycle incomplete')
    for name in ('fr165m','fr265s'):
        if 'BUILD SUCCESSFUL' not in checked(root,rec[name]).read_text():raise ValueError(name+' compile failed')
    for name,count in (('host',3),('predecessor',2)):
        text=checked(root,rec[name]).read_text()
        if 'Ran '+str(count)+' tests' not in text or not text.rstrip().endswith('OK'):raise ValueError(name+' checks failed')
    validate_version(root)
    return catalog['supportPolicy']['softwareQualifiedLocales']
