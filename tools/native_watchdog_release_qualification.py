"""Bind the retained devices020 proof and the independently verified watchdog delta.

This preserves the original 42-profile evidence at its exact historical source.
The new observation is limited to the reviewed FR165M simulator and does not
assert a physical-device result or new observations on the other profiles.
"""
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

ROOT_CHANGE = 'openspec/changes/fix-device-watchdog/evidence/release-020/'
EXPECTED_CHANGED = {
    'watchface/fields018-tests/Fields018Tests.mc', 'watchface/manifest.xml',
    'watchface/source/FeedScene.mc', 'watchface/source/LocalePresentation.mc',
    'watchface/source/NativeBridgeFeed.mc', 'watchface/source/NativeCache.mc',
    'watchface/source/NativeFeed.mc', 'watchface/source/NativeForegroundApp.mc',
    'watchface/source/NativeForegroundCache.mc', 'watchface/source/NativeImmutable.mc',
    'watchface/source/NativeIncoming.mc', 'watchface/source/NativeSfr.mc',
    'watchface/source/SceneRenderer.mc', 'watchface/source/SpaceFoxApp.mc',
    'watchface/source/SpaceFoxView.mc', 'watchface/source/generated/NativeAssets.mc',
    'watchface/source/generated/NativeVersion.mc',
}
EXPECTED_ADDED = {'watchface/source/NativeIncrementalJson.mc'}
WATCHFACE_EXTRA_CHANGED = {
    'watchface/current-recovery-tests/RecoveryTests.mc', 'watchface/display02-tests/Display02Tests.mc',
    'watchface/display03-tests/Display03Sequence.mc', 'watchface/display04-observer/CacheControl.mc',
    'watchface/display04-observer/PointObserver.mc', 'watchface/fields018-decode-tests/DecodeTick.mc',
    'watchface/incident-tests/DeliveryContinuityTests.mc', 'watchface/reminder-tests/ReminderTests.mc',
}
WATCHFACE_ADDED = EXPECTED_ADDED | {
    'watchface/current-recovery-tests/CurrentJobs.mc', 'watchface/display02-tests/CurrentJobs.mc',
    'watchface/display03-tests/CurrentJobs.mc', 'watchface/display04-observer/CurrentJobs.mc',
    'watchface/fields018-decode-tests/CurrentJobs.mc', 'watchface/incident-tests/CurrentJobs.mc',
    'watchface/reminder-tests/CurrentJobs.mc', 'watchface/runtime-b1-tests/ColdAcquisition.mc',
    'watchface/runtime-b1-tests/CurrentJobs.mc', 'watchface/runtime-b1-tests/PeerAdmission.mc',
}
SUPPORT_PRIOR = {'tools/native_language_policy.py', 'tools/release.py'}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def checked(root, name, expected):
    if not isinstance(name, str) or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
        raise ValueError('invalid watchdog evidence path')
    path = root / name
    if path.is_symlink() or not path.is_file() or sha(path) != expected:
        raise ValueError('watchdog proof input changed: ' + name)
    return path


def native_inputs(root):
    paths = list((root / 'watchface/source').rglob('*.mc'))
    paths += [p for p in (root / 'watchface/resources').rglob('*') if p.is_file()]
    paths += [p for d in (root / 'watchface').glob('resources-*') for p in d.rglob('*') if p.is_file()]
    paths += [root / 'watchface/manifest.xml', root / 'watchface/fields018-tests/Fields018Tests.mc',
              root / 'tools/fields018_native_probe.py']
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(paths) if p.is_file()}


# The independent peer bound these native bytes to the signed diagnostic.
# Only the release manifest version and generated BUILD/ID are normalized.
PEER_NATIVE_SOURCE_SHA256 = '8a7bff4e26035425412e52061e838aa1eee889e10ff780bbb152868c4153f931'


def diagnostic_source_digest(root, manifest_bytes, version_bytes):
    watch = root / 'watchface'
    paths = [watch / 'manifest.xml', watch / 'monkey.jungle']
    paths += [p for p in (watch / 'source').rglob('*') if p.is_file()]
    paths += [p for p in (watch / 'resources').rglob('*') if p.is_file()]
    for folder in watch.glob('resources-*'):
        if folder.is_dir():
            paths += [p for p in folder.rglob('*') if p.is_file()]
    digest = hashlib.sha256()
    for path in sorted(paths):
        name = path.relative_to(watch).as_posix()
        data = manifest_bytes if name == 'manifest.xml' else (version_bytes if name == 'source/generated/NativeVersion.mc' else path.read_bytes())
        digest.update(name.encode() + b'\0' + str(len(data)).encode() + b'\0' + data)
    return digest.hexdigest()


def require_peer_source_binding(root, manifest_bytes, version_bytes, candidate):
    if candidate.get('source_native_inputs_sha256') != PEER_NATIVE_SOURCE_SHA256:
        raise ValueError('peer diagnostic source identity changed')
    # Normalization may replace labels, never executable module content. The
    # generator is a separate tool dependency, so validating its current output
    # alone is not an independent bound on what this substitution can hide.
    current_version = (root / 'watchface/source/generated/NativeVersion.mc').read_bytes()
    identity = re.search(rb'const ID = "([0-9a-f]{8})";', current_version)
    expected_version = version_bytes.replace(b'const BUILD = "0.1.18";',
                                              b'const BUILD = "0.1.20";', 1)
    if identity is not None:
        expected_version = re.sub(rb'const ID = "[0-9a-f]{8}";',
                                  b'const ID = "' + identity[1] + b'";', expected_version, count=1)
    if identity is None or current_version != expected_version:
        raise ValueError('native version delta exceeds release BUILD/ID labels')
    if diagnostic_source_digest(root, manifest_bytes, version_bytes) != PEER_NATIVE_SOURCE_SHA256:
        raise ValueError('current native bytes differ from peer-verified diagnostic source')


def run_prior(root, catalog, snapshots):
    # Reconstruct only the changed predecessor inputs. Hardlinks retain all
    # other evidence bytes; replacements are unlinked before writing.
    with tempfile.TemporaryDirectory(prefix='spacefox-watchdog-prior-') as temporary:
        target = Path(temporary)
        for path in root.iterdir():
            if path.is_file():
                os.link(path, target / path.name)
        for name in ('tools', 'watchface', 'locales', 'openspec', 'tests', 'assets', 'corpus',
                     'catalog', 'schemas', 'docs', 'release', 'prototype', '.github', 'licenses'):
            source = root / name
            if source.is_dir():
                shutil.copytree(source, target / name, copy_function=os.link,
                                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name, item in snapshots.items():
            dst = target / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.unlink(missing_ok=True)
            shutil.copyfile(root / item['path'], dst)
        for name in WATCHFACE_ADDED:
            (target / name).unlink()
        previous = json.loads(json.dumps(catalog))
        previous['supportPolicy']['softwareQualificationProof'].pop('watchdogReleaseProof')
        dst = target / 'locales/catalog.json'
        dst.unlink()
        dst.write_text(json.dumps(previous, indent=2, ensure_ascii=False) + '\n')
        code = ('import json;from pathlib import Path;'
                'from tools.native_devices020_qualification import validate;'
                'p=Path.cwd();print(json.dumps(validate(p,json.loads((p/"locales/catalog.json").read_text()))))')
        result = subprocess.run([sys.executable, '-c', code], cwd=target,
                                env={**os.environ, 'PYTHONPATH': str(target)},
                                capture_output=True, text=True)
        if result.returncode:
            raise ValueError('original devices020 proof failed: ' + result.stderr[-3000:])
        return json.loads(result.stdout.strip().splitlines()[-1])


def validate(root, catalog):
    from tools.generate_native_version import validate as validate_version
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    validate_version(root)
    proof = catalog['supportPolicy']['softwareQualificationProof']
    ref = proof['watchdogReleaseProof']
    record = json.loads(checked(root, ref['path'], ref['sha256']).read_text())
    if record['scope'] != 'watchdog-fr165m-source-delta-over-devices020':
        raise ValueError('wrong watchdog proof scope')
    prior_ref = proof['devices020Proof']
    prior = json.loads(checked(root, prior_ref['path'], prior_ref['sha256']).read_text())
    old, current = prior['nativeInputs'], native_inputs(root)
    if current != record['nativeInputs']:
        raise ValueError('watchdog native source closure changed')
    if set(current) - set(old) != EXPECTED_ADDED or set(old) - set(current):
        raise ValueError('unexpected watchdog native input inventory')
    changed = {n for n in old.keys() & current.keys() if old[n] != current[n]}
    if changed != EXPECTED_CHANGED:
        raise ValueError('unexpected watchdog native input delta')
    compiled = json.loads((root / 'openspec/changes/spacefox-watchface/evidence/devices020/compile-final/results.json').read_text())
    previous_watchface = compiled['sourceHashes']
    current_watchface = {p.relative_to(root).as_posix(): sha(p) for p in sorted((root / 'watchface').rglob('*')) if p.is_file()}
    if current_watchface != record['watchfaceInputs']:
        raise ValueError('watchdog complete watchface input closure changed')
    if set(current_watchface) - set(previous_watchface) != WATCHFACE_ADDED or set(previous_watchface) - set(current_watchface):
        raise ValueError('unexpected watchdog watchface input inventory')
    watchface_changes = {n for n in previous_watchface.keys() & current_watchface.keys() if previous_watchface[n] != current_watchface[n]}
    if watchface_changes != EXPECTED_CHANGED - {'tools/fields018_native_probe.py'} | WATCHFACE_EXTRA_CHANGED:
        raise ValueError('unexpected watchdog watchface input delta')
    # The retained fields018 proof independently reconstructs its published
    # 0.1.17 parent. Restore the changed test/tool bytes that this older proof
    # reads outside its own already-authenticated parent delta.
    fields_ref = proof['fields018Proof']
    fields = json.loads(checked(root, fields_ref['path'], fields_ref['sha256']).read_text())
    parent_ref = fields['parentReceipt']; delta_ref = fields['parentDelta']
    parent = json.loads(gzip.decompress(checked(root, parent_ref['path'], parent_ref['sha256']).read_bytes()))['source_inputs_sha256']
    with tarfile.open(fileobj=io.BytesIO(checked(root, delta_ref['path'], delta_ref['sha256']).read_bytes()), mode='r:gz') as archive:
        parent_delta = {member.name for member in archive.getmembers()}
    additional = record['parentCurrent']
    for name, expected in additional.items():
        if name not in parent or name in parent_delta or name in prior['prior']:
            raise ValueError('invalid parent reconstruction input: ' + name)
        checked(root, name, expected)
    snapshots = record['priorSnapshots']
    if set(snapshots) != EXPECTED_CHANGED | WATCHFACE_EXTRA_CHANGED | SUPPORT_PRIOR | set(additional):
        raise ValueError('incomplete watchdog predecessor snapshots')
    for name, item in snapshots.items():
        checked(root, item['path'], item['sha256'])
        expected = old[name] if name in EXPECTED_CHANGED else (previous_watchface[name] if name in WATCHFACE_EXTRA_CHANGED else (prior['current'][name] if name in SUPPORT_PRIOR else parent[name]))
        if item['sha256'] != expected:
            raise ValueError('predecessor snapshot is not retained proof input: ' + name)
    for name, expected in record['currentSupport'].items():
        checked(root, name, expected)
    if set(record['currentSupport']) != {'tools/native_language_policy.py', 'tools/release.py',
                                         'tools/native_watchdog_release_qualification.py'}:
        raise ValueError('watchdog validator closure differs')
    evidence = {name: checked(root, item['path'], item['sha256']) for name, item in record['evidence'].items()}
    if set(evidence) != {'peer', 'peerLog', 'peerCompile', 'batch', 'integrity', 'field',
                         'warm', 'warmReadback', 'englishFrame', 'russianFrame', 'candidate'}:
        raise ValueError('watchdog evidence inventory differs')
    peer = json.loads(evidence['peer'].read_text())
    if (peer['author_source_commit'] != '62e90fd736a119322a3f7769e2f5ef04cdd3ee5a' or
        peer['base_commit'] != '29f3cfd067ff10690a9ba5163f25e04cd4b55b6f' or
        peer['production_source_modified'] or peer['device_profile'] != 'fr165m' or
        peer['failed'] or peer['errors'] or peer['cross_record_subcases'] != 9 or
        peer['native_log_sha256'] != sha(evidence['peerLog']) or
        peer['compile_log_sha256'] != sha(evidence['peerCompile']) or
        peer['test_sha256'] != sha(root / 'watchface/runtime-b1-tests/PeerAdmission.mc')):
        raise ValueError('independent watchdog observation differs')
    if parse_output(evidence['peerLog'].read_text(), peer['raw_launcher_exit'], ('peerCrossRecordAdmission',))['status'] != 'passed':
        raise ValueError('independent watchdog native test failed')
    batch = ('b1ColdAcquisition','b1IncrementalRefusals','b1PreparedPromotion','b1ShortWakeResume',
             'b1BatchCorruption','b1RejectedFeedCooldown','b1MissingCatalogWait','b1DuplicateAdmission')
    if parse_output(evidence['batch'].read_text(), 1, batch)['status'] != 'passed':
        raise ValueError('watchdog native batch failed')
    integrity = ('refreshColdCache','refreshCacheSequence','refreshCacheRefusals','refreshFeedCacheFaults',
                 'refreshParserRejects','refreshJsonRefusals','moreCurrentIntegrity','moreWidePolicy',
                 'moreCorruptRecovery','morePublisherFloor','moreSourceIdentity','moreRescheduledStale',
                 'moreStorageFull','moreSourceOnlyReuse')
    if parse_output(evidence['integrity'].read_text(), 1, integrity)['status'] != 'passed':
        raise ValueError('watchdog current-format integrity batch failed')
    if parse_output(evidence['field'].read_text(), 1, ('fields018SameSlotReplacement',))['status'] != 'passed':
        raise ValueError('watchdog field resume observation failed')
    if 'WD_WARM_MARKER_FLIPPED' not in evidence['warm'].read_text() or 'WD_RU_READY locale=ru slots=4' not in evidence['warm'].read_text() or 'publisher=57 incoming_processed=true' not in evidence['warmReadback'].read_text():
        raise ValueError('watchdog warm replacement observation missing')
    version_ref = record['authorVersion']
    author_version = checked(root, version_ref['path'], version_ref['sha256']).read_bytes()
    candidate = json.loads(evidence['candidate'].read_text())
    require_peer_source_binding(root, (root / snapshots['watchface/manifest.xml']['path']).read_bytes(), author_version, candidate)
    old_assets = (root / snapshots['watchface/source/generated/NativeAssets.mc']['path']).read_text()
    new_assets = (root / 'watchface/source/generated/NativeAssets.mc').read_text()
    if re.findall(r'new NativeMap\([^)]*\)', old_assets) != re.findall(r'new NativeMap\([^)]*\)', new_assets) or len(re.findall(r'new NativeMap\([^)]*\)', new_assets)) != 54:
        raise ValueError('bundled map identities or order changed')
    old_renderer = (root / snapshots['watchface/source/SceneRenderer.mc']['path']).read_text()
    new_renderer = (root / 'watchface/source/SceneRenderer.mc').read_text().replace('i < NativeAssets.mapCount', 'i < NativeAssets.maps.size()').replace('var view = NativeAssets.mapAt(i) as NativeMap;', 'var view = NativeAssets.maps[i];')
    if old_renderer != new_renderer:
        raise ValueError('renderer delta exceeds lazy map metadata')
    old_locale = (root / snapshots['watchface/source/LocalePresentation.mc']['path']).read_text()
    new_locale = (root / 'watchface/source/LocalePresentation.mc').read_text()
    if old_locale[old_locale.index('    function prepare(requested)'):] != new_locale[new_locale.index('    function prepare(requested)'):]:
        raise ValueError('locale preparation or strings changed')
    prior_manifest = (root / snapshots['watchface/manifest.xml']['path']).read_text()
    if prior_manifest.replace('version="0.1.18"', 'version="0.1.20"', 1) != (root / 'watchface/manifest.xml').read_text():
        raise ValueError('manifest delta exceeds release version')
    qualified = run_prior(root, catalog, snapshots)
    if qualified != catalog['supportPolicy']['softwareQualifiedLocales']:
        raise ValueError('prior qualified locale set differs')
    return qualified
