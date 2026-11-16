"""Authenticate the current B1/version delta without rewriting historic receipts."""
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

CHANGED = frozenset('''watchface/source/FeedScene.mc watchface/source/FieldSources.mc
watchface/source/LocalePresentation.mc watchface/source/NativeBridgeFeed.mc
watchface/source/NativeCache.mc watchface/source/NativeFeed.mc
watchface/source/NativeForegroundApp.mc watchface/source/NativeForegroundCache.mc
watchface/source/NativeIncoming.mc watchface/source/NativeJson.mc
watchface/source/NativeSfr.mc watchface/source/SceneRenderer.mc
watchface/source/SpaceFoxApp.mc watchface/source/SpaceFoxView.mc
watchface/source/generated/NativeVersion.mc watchface/manifest.xml'''.split())
ROOT = 'openspec/changes/restore-fr165-runtime-guarantees/evidence/'
EVIDENCE = {
    'author21': 'b1-current-21-tests.log', 'wake5': 'wake-progress-tests.log',
    'provider4': 'provider-icon-tests.log', 'peer4': 'peer-deferred-fitness-green.log',
    'peerReview': 'PEER-B1.md', 'rootStatus': '../ROOT-STATUS.md',
    'ledger': 'VERIFICATION.md', 'graphics': 'GRAPHICS-LEDGER.md',
    'timer': 'current-timer-min.log', 'cold': 'current-static-feed.txt',
    'wakeCycles': 'ordinary-off-high-cycles.log',
}
# ROOT-STATUS is an orchestration record that may evolve independently; the
# peer review and actual receipts are the immutable behavioral admission inputs.
EVIDENCE.pop('rootStatus')
TABLES = {
 'author21': '''b1ClockWithUnavailableSettings b1ClockWithUnavailableHealth b1ActualColdViewDefersCache b1ClockAfterDrawingFailure b1ClockAfterLoaderFailure b1ClockBeforeLoader b1LowBeforeLoader b1ClockWithUnavailableRenderer b1CapturedSuccessorTicksInFallback b1ColdAcquisition b1AdmissionFitnessLifecycle b1RealDecodeTicksAndCancels b1MeasureCapturedCallbacks b1StagedLiveFeedAdmission b1StagedSupersededToken b1StagedRestoreExactAndRecovery b1CompactingProjectionEquality b1PreparedSupersededToken b1PreparedFailureKeepsOldCommit b1GraphemeReleaseAndRebind b1LowHeapDefersOptionalDecode''',
 'wake5': 'b1RealDecodeTicksAndCancels b1LowHeapDefersOptionalDecode b1GraphemeReleaseAndRebind b1StagedLiveFeedAdmission b1StagedRestoreExactAndRecovery',
 'provider4': 'b1ProviderIconBudget b1AdmissionFitnessLifecycle b1ClockWithUnavailableHealth b1GraphemeReleaseAndRebind',
 'peer4': 'b1LowHeapDefersOptionalDecode b1RealDecodeTicksAndCancels b1AdmissionFitnessLifecycle b1ClockWithUnavailableHealth',
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read_checked(root, ref):
    rel = Path(ref['path'])
    if rel.is_absolute() or '..' in rel.parts:
        raise ValueError('unsafe B1 proof path')
    target = (root / rel).resolve()
    if not target.is_relative_to(root) or not target.is_file() or sha(target) != ref['sha256']:
        raise ValueError('B1 qualification input changed: ' + str(rel))
    return target

def validate(root, catalog):
    from tools.generate_native_version import validate as validate_version
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    record = json.loads(read_checked(root, proof['b1Runtime019Proof']).read_text())
    if record['scope'] != 'b1-runtime-019-current-source' or record['version'] != '0.1.19':
        raise ValueError('unexpected B1 release scope/version')
    baseline = json.loads(read_checked(root, record['baselineCatalog']).read_text())
    current = json.loads(json.dumps(catalog))
    current['supportPolicy']['softwareQualificationProof'].pop('b1Runtime019Proof')
    if current != baseline:
        raise ValueError('locale policy changed outside B1 qualification')
    original = baseline['supportPolicy']['softwareQualificationProof']['devices020Proof']
    prior = json.loads(read_checked(root, original).read_text())
    if prior['scope'] != 'devices020-bounded-compatibility':
        raise ValueError('prior device qualification changed')
    for ref in prior['evidence'].values():
        read_checked(root, ref)
    for name, digest in prior['current'].items():
        if name not in ('tools/release.py', 'tools/native_language_policy.py') and sha(root / name) != digest:
            raise ValueError('prior qualification owner changed: ' + name)
    old = prior['nativeInputs']
    files = [p for p in (root/'watchface/source').rglob('*.mc') if p.is_file()]
    files += [p for p in (root/'watchface/resources').rglob('*') if p.is_file()]
    files += [p for d in (root/'watchface').glob('resources-*') for p in d.rglob('*') if p.is_file()]
    files += [root/'watchface/manifest.xml',root/'watchface/fields018-tests/Fields018Tests.mc',root/'tools/fields018_native_probe.py']
    native = {p.relative_to(root).as_posix():sha(p) for p in sorted(files)}
    if native != record['nativeInputs'] or set(native) != set(old):
        raise ValueError('B1 current native source closure changed')
    if {name for name in native if native[name] != old[name]} != CHANGED:
        raise ValueError('B1 native source delta differs from reviewed scope')
    for name, digest in record['owners'].items():
        if sha(root/name) != digest:
            raise ValueError('B1 admission owner changed: '+name)
    if set(record['owners']) != {'tools/native_b1_019_qualification.py','tools/native_language_policy.py','tools/release.py'}:
        raise ValueError('B1 admission owner set changed')
    app = ET.parse(root/'watchface/manifest.xml').getroot().find('{http://www.garmin.com/xml/connectiq}application')
    if app.get('id') != 'ec8b7c8a8ea54ee9ac91ee6e7a674d15' or app.get('version') != '0.1.19':
        raise ValueError('B1 release identity/version changed')
    validate_version(root)
    if set(record['evidence']) != set(EVIDENCE):
        raise ValueError('B1 evidence inventory changed')
    evidence = {}
    for name, filename in EVIDENCE.items():
        ref = record['evidence'][name]
        if ref['path'] != ROOT + filename:
            raise ValueError('B1 evidence path changed')
        evidence[name] = read_checked(root, ref).read_text()
    for name, names in TABLES.items():
        if parse_output(evidence[name], 1, tuple(names.split()))['status'] != 'passed':
            raise ValueError('B1 native receipt failed: ' + name)
    if 'software GREEN for the scoped B1 scenarios' not in evidence['peerReview']:
        raise ValueError('B1 independent peer acceptance missing')
    if 'physical P1–P3 acceptance is still open' not in evidence['peerReview']:
        raise ValueError('B1 peer physical boundary missing')
    return catalog['supportPolicy']['softwareQualifiedLocales']
