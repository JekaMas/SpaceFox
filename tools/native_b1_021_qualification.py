"""Bind the 0.1.20 watchdog proof and directly observed B1 integration delta."""
import hashlib
import json
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
            'b1peer':'PEER-B1.md', 'graphics':'GRAPHICS-LEDGER.md'}
COMBINED = '''b1ClockWithUnavailableSettings b1ClockWithUnavailableHealth b1ActualColdViewDefersCache b1ClockAfterDrawingFailure b1ClockAfterLoaderFailure b1ClockBeforeLoader b1LowBeforeLoader b1ClockWithUnavailableRenderer b1CapturedSuccessorTicksInFallback b1AdmissionFitnessLifecycle b1GraphemeReleaseAndRebind b1ProviderIconBudget b1ShortWakeResume b1IncrementalRefusals b1PreparedPromotion b1ColdAcquisition peerCrossRecordAdmission b1RealDecodeTicksAndCancels b1LowHeapDefersOptionalDecode b1SupersededDuringAdmission021 b1FailedPromotionRecovery021'''.split()
STARTUP = '''b1ActualColdViewDefersCache b1ClockBeforeLoader b1ClockAfterLoaderFailure b1ClockWithUnavailableHealth b1ShortWakeResume b1AdmissionFitnessLifecycle'''.split()
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
    if set(record['evidence'])!=set(EVIDENCE):raise ValueError('integration evidence inventory changed')
    evidence={}
    for name,filename in EVIDENCE.items():
        r=record['evidence'][name]
        if r['path']!=BASE+filename:raise ValueError('integration evidence path changed')
        evidence[name]=checked(root,r).read_text()
    if parse_output(evidence['combined'],1,tuple(COMBINED))['status']!='passed':raise ValueError('integration combined receipt failed')
    if parse_output(evidence['startup'],1,tuple(STARTUP))['status']!='passed':raise ValueError('integration startup receipt failed')
    p=json.loads(evidence['primary'])
    if p['version']!='0.1.21' or p['uuid']!=app.get('id') or p['profile']!='fr165' or p['native_id']!=record['nativeId'] or p['key_spki_sha256']!='84e95bea4f3052a7c93f297e25605dc374a02f946b8011c65eec950b284146cc' or not p['verification']['prg_public_key_matches'] or not p['verification']['prg_signature_verified']:
        raise ValueError('primary integration compile/identity evidence changed')
    stock=json.loads(evidence['stock'])
    if (stock['native_id']!=record['nativeId'] or stock['raw_exit']!=124 or
        stock['network']!='none' or stock['elapsed_seconds']<55 or
        stock['ciq_log_delta']!='unchanged' or not stock['clock_date_observed'] or
        stock['app_errors']):
        raise ValueError('stock observation changed')
    checked(root,record['stockImage'])
    if 'software GREEN for the scoped B1 scenarios' not in evidence['b1peer']:
        raise ValueError('integration peer evidence missing')
    return catalog['supportPolicy']['softwareQualifiedLocales']
