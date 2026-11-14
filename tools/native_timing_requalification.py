"""Retain the original finite font/corpus proof and qualify a bounded source delta.

The immutable original proof is validated against its retained historical input
bytes. Current native EN/RU observations qualify timing/color changes separately.
No historical receipt is assigned a new source hash or claimed freshly executed.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(root, catalog):
    from tools.native_language_policy import input_paths, _validate_bound_files
    from tools.qualify_native_finite import validate_bound_observation
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    ref = proof['sourceDeltaProof']
    def checked(name, digest):
        if not isinstance(name, str) or Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('unsafe timing requalification path')
        p = root/name
        if not p.is_file() or sha(p) != digest:
            raise ValueError('timing requalification input changed: '+name)
        return p
    record = json.loads(checked(ref['path'], ref['sha256']).read_text())
    if record['schemaVersion'] != 1 or record['status'] != 'passed' or record['scope'] != 'retained-font-corpus-plus-native-en-ru-timing-settings':
        raise ValueError('incomplete timing requalification')
    original = json.loads(checked(record['originalProof']['path'], record['originalProof']['sha256']).read_text())
    if set(proof) != set(original)|{'sourceDeltaProof'} or any(proof[k]!=original[k] for k in original if k!='productionSources'):
        raise ValueError('retained finite proof metadata changed')
    if set(proof['productionSources']) != set(input_paths(catalog, root)):
        raise ValueError('timing requalification source closure differs')
    for name, digest in proof['productionSources'].items():
        checked(name, digest)
    current = record['currentSources']
    if current != proof['productionSources']:
        raise ValueError('timing requalification current sources disagree')
    # Only these inspected changes leave retained proper-name fonts, grapheme
    # fitting and the complete captured display corpus unchanged. A new owner
    # needs a new explicit review and current observation, never a hash refresh.
    allowed = {'tools/build_native_localization.py','tools/native_language_policy.py',
               'watchface/source/ScheduleState.mc','watchface/source/SceneSettings.mc',
               'watchface/source/SceneRenderer.mc','watchface/source/SpaceFoxView.mc',
               'watchface/resources/settings/settings.xml','watchface/resources/settings/properties.xml'}
    allowed.update('watchface/'+folder+'/strings/strings.xml' for folder in ('resources','resources-rus','resources-deu','resources-fre','resources-spa'))
    changed = {name for name in original['productionSources'] if original['productionSources'][name] != current.get(name)}
    if changed != set(record['reviewedChanges']) or not changed <= allowed:
        raise ValueError('unreviewed timing/layout source delta')
    if set(current)-set(original['productionSources']) != {'tools/native_timing_requalification.py','tools/native_timing_settings.py','tools/spacefox/native_profile.py','watchface/tests/NativeClockTests.mc','tests/fixtures/final_native_timing_settings/Assertions.mc','watchface/source/NativeFeed.mc','watchface/source/NativeJson.mc','tests/fixtures/sourced_ascent_end/Assertions.mc'}:
        raise ValueError('unexpected new qualification owner')
    for name in changed:
        row = record['reviewedChanges'][name]
        if row['beforeSha256'] != original['productionSources'][name] or row['afterSha256'] != current[name] or not row['reason']:
            raise ValueError('invalid timing source review: '+name)
    # Stronger than accepting booleans: exact source-bound compiled native run,
    # full assertion identities, emitted geometry, cold Properties reopen and
    # actual SDK screenshot bytes are reconciled by the unit evidence validator.
    from tools.native_timing_settings import validate_evidence
    checked(record['nativeEvidence'].rstrip('/')+'/native-result.json',record['nativeResultSha256'])
    # The earlier screenshots and settings observation used the prior parser.
    # Validate those bytes as historical inputs; a separate native framework
    # receipt proves the only new parser branch against the actual current tree.
    evidence = root/record['nativeEvidence']
    old_build = json.loads((evidence/'observer/build.json').read_text())
    changed_parser_paths = ('watchface/source/NativeFeed.mc','watchface/source/NativeJson.mc')
    old_parsers = {name:evidence/'observer/production-snapshot'/Path(name+'.txt') for name in changed_parser_paths}
    if any(sha(path) != old_build['productionSources'][name] for name,path in old_parsers.items()):
        raise ValueError('historical parser snapshot changed')
    with tempfile.TemporaryDirectory(prefix='spacefox-retained-timing-') as tmp:
        old_root = Path(tmp)
        for name in {**old_build['productionSources'], **old_build['productionResources']}:
            src = root/name
            dest = old_root/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(old_parsers.get(name,src),dest)
        for name in ('watchface/tests/NativeClockTests.mc','tests/fixtures/final_native_timing_settings/Assertions.mc'):
            dest=old_root/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/name,dest)
        validate_evidence(evidence, root=old_root, require_clean=True)
    ascent = record['ascentProof']
    native = root/ascent['directory']
    for relative,digest in ascent['files'].items():
        checked(ascent['directory']+'/'+relative,digest)
    build=json.loads((native/'build.json').read_text())
    execution=json.loads((native/'native-tests-execution.json').read_text())
    from tools.run_native_tests import parse_output
    expected=('ascentAdmissionPositive','ascentAdmissionNegative')
    parsed=parse_output((native/'native-tests.log').read_text(),execution['exitCode'],expected)
    if (build['exitCode'] != 0 or build['tests'] is not True or build['productionSourceScope'] != 'all-native'
            or parsed['status'] != 'passed' or execution['framework'] != parsed
            or build['expectedTests'] != list(expected) or '-d' not in build['command']
            or build['command'][build['command'].index('-d')+1] != 'fr165'):
        raise ValueError('current ascent native framework receipt failed')
    for name,digest in {**build['productionSources'], **build['productionResources']}.items():
        if sha(root/name)!=digest:raise ValueError('current ascent native source changed: '+name)
    probe=(root/'tests/fixtures/sourced_ascent_end/Assertions.mc').read_bytes()
    if (native/'Probe.mc').read_bytes()!=probe or sha(native/'Probe.mc')!=build['probeSha256']:
        raise ValueError('current ascent native assertions changed')
    # Check literal mutated inputs, not a rehashed report's claim about them.
    packets=json.loads((native/'probe-resources/packets.json').read_text())
    original_packets=json.loads((evidence/'packets.json').read_text())
    base=json.loads(original_packets['exact'])
    fact={'launch_id':base['launch']['launch_id'],'target_utc':1794583543,'end_utc':1794585343,
          'source_url':'https://example.invalid/mission/?missionId=technical','reviewed_utc':1794576344}
    base['launch']['ascent_end']=fact
    base['publisher']['generation']+=1
    from tools.spacefox.catalog import canonical_bytes
    if packets['ascentGood'] != canonical_bytes(base).decode():raise ValueError('ascent positive fixture differs')
    for label,mutation in (('ascentBadId',{'launch_id':'ll2:launch:wrong'}),('ascentBadTarget',{'target_utc':1794583544}),('ascentBadEnd',{'end_utc':1794583542}),('ascentBadUrl',{'source_url':'https://example.invalid:abc/'}),('ascentBadFuture',{'reviewed_utc':1794576346})):
        row=json.loads(packets['ascentGood']);row['launch']['ascent_end'].update(mutation)
        if packets[label] != canonical_bytes(row).decode():raise ValueError('ascent negative fixture differs: '+label)
    for name, digest in record['baselineFiles'].items():
        checked(name, digest)
    # A local historical tree lets the original strict checker inspect the old
    # inputs verbatim. Files are copied, never modifying the working tree.
    with tempfile.TemporaryDirectory(prefix='spacefox-retained-finite-') as temporary:
        old = Path(temporary)
        for folder in ('watchface', 'locales'):
            shutil.copytree(root/folder, old/folder, copy_function=os.link)
        for name in original['productionSources']:
            target = old/name
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():shutil.copyfile(root/name, target)
        for relative in (Path(original['corpusPath']).parent, Path(original['receiptPath']).parent):
            target = old/relative
            if not target.exists():shutil.copytree(root/relative, target, copy_function=os.link)
        prefix = record['baselineDirectory'].rstrip('/')+'/'
        for name in record['baselineFiles']:
            if not name.startswith(prefix):raise ValueError('baseline snapshot outside retained directory')
            target = old/name[len(prefix):]
            target.parent.mkdir(parents=True, exist_ok=True)
            # Unlink a hardlink before overwrite.
            if target.exists():target.unlink()
            shutil.copyfile(root/name, target)
        # The finite receipt also binds the old JSON owner even though it was
        # outside the former typography input_paths. Preserve its actual bytes.
        json_target=old/'watchface/source/NativeJson.mc'
        json_target.unlink()
        shutil.copyfile(old_parsers['watchface/source/NativeJson.mc'],json_target)
        old_catalog = json.loads((old/'locales/catalog.json').read_text())
        old_catalog['supportPolicy']['softwareQualificationProof'] = original
        p = old/'locales/catalog.json';p.unlink();p.write_text(json.dumps(old_catalog))
        _validate_bound_files(old, old_catalog)
        validate_bound_observation(old, old_catalog)
    return catalog['supportPolicy']['softwareQualifiedLocales']
