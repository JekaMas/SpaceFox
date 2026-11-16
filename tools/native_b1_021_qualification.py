"""Bind the 0.1.20 watchdog proof and directly observed B1 integration delta."""
import hashlib
import json
import re
from pathlib import Path
from xml.etree import ElementTree as ET

BASE = 'openspec/changes/restore-fr165-runtime-guarantees/evidence/'
CHANGED = frozenset('''watchface/manifest.xml watchface/source/FieldSources.mc
watchface/source/LocalePresentation.mc watchface/source/NativeForegroundApp.mc
watchface/source/NativeJson.mc watchface/source/SceneRenderer.mc
watchface/source/SpaceFoxApp.mc watchface/source/SpaceFoxView.mc
watchface/source/generated/NativeVersion.mc'''.split())
EVIDENCE = {'combined':'integration021-tests.log', 'startup':'integration021-startup-fix-tests.log',
            'primary':'integration021-primary-receipt.json', 'stock':'integration021-stock-observation.json',
            'peerRepair':'integration021-peer-source-switch-green.log',
            'peerRed':'integration021-peer-source-switch-red.log', 'peerReview':'INTEGRATION-021-PEER.md',
            'peerPrimary':'integration021-peer-primary-receipt.json',
            'b1peer':'PEER-B1.md', 'graphics':'GRAPHICS-LEDGER.md'}
COMBINED = '''b1ClockWithUnavailableSettings b1ClockWithUnavailableHealth b1ActualColdViewDefersCache b1ClockAfterDrawingFailure b1ClockAfterLoaderFailure b1ClockBeforeLoader b1LowBeforeLoader b1ClockWithUnavailableRenderer b1CapturedSuccessorTicksInFallback b1AdmissionFitnessLifecycle b1GraphemeReleaseAndRebind b1ProviderIconBudget b1ShortWakeResume b1IncrementalRefusals b1PreparedPromotion b1ColdAcquisition peerCrossRecordAdmission b1RealDecodeTicksAndCancels b1LowHeapDefersOptionalDecode b1SupersededDuringAdmission021 b1FailedPromotionRecovery021'''.split()
STARTUP = '''b1ActualColdViewDefersCache b1ClockBeforeLoader b1ClockAfterLoaderFailure b1ClockWithUnavailableHealth b1ShortWakeResume b1AdmissionFitnessLifecycle'''.split()
PEER_REPAIR = '''peerSourceChangeDefersRenderer021 b1ActualColdViewDefersCache b1ClockAfterLoaderFailure b1ShortWakeResume b1AdmissionFitnessLifecycle b1GraphemeReleaseAndRebind'''.split()
OWNERS = {'tools/native_b1_021_qualification.py','tools/native_language_policy.py','tools/release.py',
          'tools/run_native_tests.py','tools/generate_native_version.py','tools/b1_cold_probe.py',
          'tests/test_b1_021_admission.py','tests/test_release_020_predecessor.py'}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def checked(root, ref):
    rel=Path(ref['path'])
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('unsafe B1 integration proof path')
    path=(root/rel).resolve()
    if not path.is_relative_to(root) or not path.is_file() or sha(path)!=ref['sha256']:
        raise ValueError('B1 integration input changed: '+str(rel))
    return path

def native_inputs(root):
    files=[p for p in (root/'watchface/source').rglob('*.mc') if p.is_file()]
    files += [p for p in (root/'watchface/resources').rglob('*') if p.is_file()]
    files += [p for d in (root/'watchface').glob('resources-*') for p in d.rglob('*') if p.is_file()]
    files += [root/'watchface/manifest.xml',root/'watchface/fields018-tests/Fields018Tests.mc',root/'tools/fields018_native_probe.py']
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(files)}

def test_inputs(root):
    dirs=('watchface/runtime-b1-tests','tests/fixtures/fr165-runtime-20261116',
          'tests/fixtures/typed_operator','tests/native_scene_diagnostics/profile-a',
          'tests/native_scene_diagnostics/profile-b')
    files=[p for d in dirs for p in (root/d).rglob('*') if p.is_file()]
    return {p.relative_to(root).as_posix():sha(p) for p in sorted(files)}

def validate(root,catalog):
    from tools.generate_native_version import validate as validate_version
    from tools.run_native_tests import parse_output
    root=Path(root).resolve();proof=catalog['supportPolicy']['softwareQualificationProof']
    record=json.loads(checked(root,proof['b1Integration021Proof']).read_text())
    if record['scope']!='b1-watchdog-021-current-source' or record['version']!='0.1.21':
        raise ValueError('wrong B1 integration scope/version')
    baseline=json.loads(checked(root,record['baselineCatalog']).read_text());current=json.loads(json.dumps(catalog))
    current['supportPolicy']['softwareQualificationProof'].pop('b1Integration021Proof')
    if current!=baseline:raise ValueError('locale policy changed outside integration proof')
    ref=baseline['supportPolicy']['softwareQualificationProof']['watchdogReleaseProof']
    prior=json.loads(checked(root,ref).read_text())
    if prior['scope']!='watchdog-fr165m-source-delta-over-devices020':raise ValueError('published watchdog qualification changed')
    for value in prior['priorSnapshots'].values():checked(root,value)
    for value in prior['evidence'].values():checked(root,value)
    checked(root,prior['authorVersion'])
    for name,expected in prior['parentCurrent'].items():
        if sha(root/name)!=expected:raise ValueError('watchdog parent input changed: '+name)
    for name,expected in prior['currentSupport'].items():
        if name not in ('tools/native_language_policy.py','tools/release.py') and sha(root/name)!=expected:
            raise ValueError('watchdog qualification owner changed: '+name)
    native=native_inputs(root);old=prior['nativeInputs']
    if native!=record['nativeInputs'] or set(native)!=set(old):raise ValueError('integrated native input closure changed')
    if {n for n in native if native[n]!=old[n]}!=CHANGED:raise ValueError('integrated source delta differs')
    if test_inputs(root)!=record['testInputs']:raise ValueError('integration test input closure changed')
    if set(record['owners'])!=OWNERS or any(sha(root/n)!=h for n,h in record['owners'].items()):raise ValueError('integration admission owner changed')
    app=ET.parse(root/'watchface/manifest.xml').getroot().find('{http://www.garmin.com/xml/connectiq}application')
    if app.get('id')!='ec8b7c8a8ea54ee9ac91ee6e7a674d15' or app.get('version')!='0.1.21':raise ValueError('integration version/identity changed')
    validate_version(root)
    if (not re.fullmatch(r'[0-9a-f]{8}',record['nativeId']) or
        'const ID = "'+record['nativeId']+'"' not in (root/'watchface/source/generated/NativeVersion.mc').read_text()):
        raise ValueError('integration native ID differs from generated source')
    if set(record['evidence'])!=set(EVIDENCE):raise ValueError('integration evidence inventory changed')
    evidence={}
    for name,filename in EVIDENCE.items():
        r=record['evidence'][name]
        if r['path']!=BASE+filename:raise ValueError('integration evidence path changed')
        evidence[name]=checked(root,r).read_text()
    if parse_output(evidence['combined'],1,tuple(COMBINED))['status']!='passed':raise ValueError('integration combined receipt failed')
    if parse_output(evidence['startup'],1,tuple(STARTUP))['status']!='passed':raise ValueError('integration startup receipt failed')
    if parse_output(evidence['peerRepair'],1,tuple(PEER_REPAIR))['status']!='passed':raise ValueError('integration peer repair receipt failed')
    p=json.loads(evidence['primary'])
    if p['version']!='0.1.21' or p['uuid']!=app.get('id') or p['profile']!='fr165' or p['native_id']!=record['authorNativeId'] or p['key_spki_sha256']!='84e95bea4f3052a7c93f297e25605dc374a02f946b8011c65eec950b284146cc' or not p['verification']['prg_public_key_matches'] or not p['verification']['prg_signature_verified']:
        raise ValueError('historical author compile/identity evidence changed')
    stock=json.loads(evidence['stock'])
    if (stock['native_id']!=record['authorNativeId'] or stock['raw_exit']!=124 or
        stock['network']!='none' or stock['elapsed_seconds']<55 or
        stock['ciq_log_delta']!='unchanged' or not stock['clock_date_observed'] or
        stock['app_errors']):
        raise ValueError('stock observation changed')
    peer=json.loads(evidence['peerPrimary'])
    if (peer['version']!='0.1.21' or peer['native_id']!=record['nativeId'] or
        peer['uuid']!='8bfb35b035764c14856ed684585d3ffd' or peer['profile']!='fr165' or
        peer['entry']!='SpaceFoxApp' or peer['key_boundary']!='disposable-test-key-not-production' or
        peer['key_spki_sha256']!='40bf1220604f7268b5557e480949d860a9514e35061d0b5749b28181dc24045e' or
        peer['compiler_sha256']!='082b2fd3f50578204e01d44313f43f2ce52a60dbfd6221f6b259b2687239de3f' or
        peer['compiler_profile_sha256']!='ed45eb28ba928e2d2bda1bf8c567401232ab226889b87712fef5713e7f9a4fa8' or
        peer['flags']!=['-l','3','-O','2','-w','-r','-d','fr165'] or
        not re.fullmatch(r'[0-9a-f]{64}',peer['program_sha256']) or
        peer['clock']!='real system clock; no fixture injection' or
        not peer['verification']['prg_public_key_matches'] or not peer['verification']['prg_signature_verified'] or
        peer['verification']['rsa_bits']!=4096):
        raise ValueError('current disposable primary compile evidence changed')
    checked(root,record['stockImage'])
    if 'software GREEN for the scoped B1 scenarios' not in evidence['b1peer']:
        raise ValueError('integration peer evidence missing')
    if ('source/integration GREEN' not in evidence['peerReview'] or
        'physical acceptance remains open' not in evidence['peerReview']):
        raise ValueError('current integration peer boundary missing')
    return catalog['supportPolicy']['softwareQualifiedLocales']
