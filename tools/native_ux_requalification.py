"""Bind the UX01 delta to SDK observations and replay the retained locale proof.

The prior five-language qualification is preserved at its original source bytes;
new display observations cover EN/RU only, not physical-device review.
"""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

BASE = 'openspec/changes/spacefox-watchface/evidence/ux01-016/'

def validate(root, catalog):
    from tools.native_incident_requalification import validate as prior_validate
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    def checked(path, sha256):
        name = Path(path)
        if name.is_absolute() or '..' in name.parts or not (root/name).is_file() or hashlib.sha256((root/name).read_bytes()).hexdigest() != sha256:
            raise ValueError('UX delta proof input changed: ' + path)
        return root/name
    reference = proof['uxDeltaProof']
    record = json.loads(checked(reference['path'], reference['sha256']).read_text())
    if record.get('scope') != 'native-ux01-en-ru' or record.get('status') != 'passed':
        raise ValueError('UX delta proof incomplete')
    old = json.loads(checked(**record['priorCatalog']).read_text())
    prior = old['supportPolicy']['softwareQualificationProof']
    if {k:v for k,v in proof.items() if k!='uxDeltaProof'} != prior:
        raise ValueError('prior qualification metadata changed')
    comparable = json.loads(json.dumps(catalog))
    comparable['supportPolicy']['softwareQualificationProof'] = prior
    if comparable != old:
        raise ValueError('catalog outside UX delta changed')
    for name,digest in record['sources'].items(): checked(name,digest)
    for name,digest in record['evidence'].items(): checked(name,digest)
    build = json.loads((root/BASE/'settings-build.json').read_text())
    if build.get('exitCode') != 0 or not build.get('tests'):
        raise ValueError('UX SDK build not observed')
    for name,digest in {**build['productionSources'],**build['productionResources']}.items():
        if record['sources'].get(name) != digest: raise ValueError('SDK source closure differs: '+name)
    for name in ('identity-build.json','rejection-build.json','battery-final-build.json'):
        observed=json.loads((root/BASE/name).read_text())
        if observed.get('exitCode') != 0 or any(observed.get(k) != build[k] for k in ('productionSources','productionResources')): raise ValueError('UX SDK observation source mismatch: '+name)
    if parse_output((root/BASE/'native-settings-version-green.log').read_text(),1,('uxSettingsCallbackAndReopen','uxCalendarCountdown','uxBackgroundVersionDiagnostic'))['status'] != 'passed':
        raise ValueError('UX settings/diagnostic assertions failed')
    for name in ('final-python-green.log','final-pixels-ru-green.log'):
        result=(root/BASE/name).read_text()
        for case in ('test_ux01_active_clock_ink','test_ux01_active_countdown_ink','test_ux01_active_field_ink','test_ux01_aod_time_ink_and_center','test_ux01_aod_visible_context','test_ux01_aod_lit_pixel_limit','test_ux01_no_standalone_battery'):
            if not any(line.startswith(case+' ') and line.endswith(' ... ok') for line in result.splitlines()): raise ValueError('UX pixel assertion missing: '+case)
        if '\nOK\n' not in result: raise ValueError('UX pixel run failed')
    reuse=(root/BASE/'reuse-green.log').read_text()
    for case in ('test_aod_paint_and_cadence_inputs','test_network_restore_owner_delta_only_low_battery'):
        if not any(line.startswith(case+' ') and line.endswith(' ... ok') for line in reuse.splitlines()): raise ValueError('retained proof reconciliation missing: '+case)
    battery=(root/BASE/'battery-final-green.log').read_text()
    for case in ('test_initial_low_battery','test_next_minute_battery'):
        if not any(line.startswith(case+' ') and line.endswith(' ... ok') for line in battery.splitlines()): raise ValueError('LOW battery assertion missing: '+case)
    if '\nOK\n' not in battery: raise ValueError('LOW battery run failed')
    identity=(root/BASE/'native-identity-after-restore-green.log').read_text()
    if parse_output(identity,1,('uxAcceptedSceneDuringRestore','uxNewIdentityAfterRestore'))['status'] != 'passed': raise ValueError('UX identity transition assertion failed')
    rejection=(root/BASE/'rejection-green.log').read_text()
    if 'test_accepted_scene_survives_rejected_candidate' not in rejection or '\nOK\n' not in rejection: raise ValueError('UX staged rejection assertion failed')
    restore=(root/BASE/'native-restore-final-green.log').read_text()
    if parse_output(restore,1,('uxAcceptedSceneDuringRestore',))['status'] != 'passed': raise ValueError('UX restore assertion failed')
    runtime=(root/BASE/'native-network-404-final.log').read_text()
    for token in ('UX_VALID_SCENE id=', 'NATIVE_RESPONSE feed code=404', 'UX_FAILURE_RETAINED id=', 'bitmap=true status=feedFailed'):
        if token not in runtime: raise ValueError('UX network recovery incomplete: '+token)
    required=('active-en.png','active-ru.png','aod-en.png','aod-ru.png','error-en.png','error-ru.png')
    for name in required:
        path=BASE+name
        if path not in record['evidence'] or (root/path).read_bytes()[:8] != b'\x89PNG\r\n\x1a\n': raise ValueError('UX native capture missing: '+name)
    with tempfile.TemporaryDirectory(prefix='spacefox-ux-prior-') as temporary:
        target=Path(temporary)
        for folder in ('watchface','locales','tools'):
            shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for folder in ('openspec','corpus','tests','assets','catalog','schemas'):
            (target/folder).symlink_to(root/folder,target_is_directory=True)
        for name,item in record['priorSnapshots'].items():
            destination=target/name;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(checked(**item),destination)
        for name in record['priorAbsent']:
            path=target/name
            if path.exists(): path.unlink()
        (target/'locales/catalog.json').write_text(json.dumps(old,indent=2)+'\n')
        if prior_validate(target,old) != old['supportPolicy']['softwareQualifiedLocales']:
            raise ValueError('retained five-language proof failed')
    return catalog['supportPolicy']['softwareQualifiedLocales']
