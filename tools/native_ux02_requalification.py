"""Reconcile the UX02 native observations with the retained UX01 admission.

This is a bounded software qualification, not physical or Store acceptance.
"""
import hashlib
import json
import shutil
import tempfile
from pathlib import Path

BASE='openspec/changes/spacefox-watchface/evidence/ux02/'

def validate(root,catalog):
    from tools.native_ux_requalification import validate as prior_validate
    from tools.run_native_tests import parse_output
    root=Path(root).resolve();proof=catalog['supportPolicy']['softwareQualificationProof']
    def checked(path,sha256):
        p=Path(path)
        if p.is_absolute() or '..' in p.parts or not (root/p).is_file() or hashlib.sha256((root/p).read_bytes()).hexdigest()!=sha256:
            raise ValueError('UX02 proof input changed: '+path)
        return root/p
    r=json.loads(checked(**proof['ux02DeltaProof']).read_text())
    if r.get('scope')!='native-ux02-en-ru-fr165m-fr965' or r.get('status')!='passed':raise ValueError('UX02 software proof incomplete')
    old=json.loads(checked(**r['priorCatalog']).read_text());oldproof=old['supportPolicy']['softwareQualificationProof']
    if {k:v for k,v in proof.items() if k!='ux02DeltaProof'}!=oldproof:raise ValueError('prior locale proof metadata changed')
    comparable=json.loads(json.dumps(catalog));comparable['supportPolicy']['softwareQualificationProof']=oldproof
    if comparable!=old:raise ValueError('catalog outside UX02 proof changed')
    for name,digest in r['sources'].items():checked(name,digest)
    for name,digest in r['evidence'].items():checked(name,digest)
    expected_sources={str(p.relative_to(root)) for p in (root/'watchface/source').rglob('*.mc')}
    if not expected_sources<=set(r['sources']):raise ValueError('UX02 production source closure incomplete')
    for name in ('phase-checker-build.json','phase-checker-454-build.json','hosted-timing-build.json','hosted-timing-454-build.json'):
        observed=json.loads((root/BASE/name).read_text())
        if observed.get('exitCode') != 0: raise ValueError('UX02 SDK build failed: '+name)
        for source,digest in {**observed['productionSources'],**observed['productionResources']}.items():
            if r['sources'].get(source)!=digest: raise ValueError('UX02 final SDK closure differs: '+source)
    required=('fr165m-pixels-green.log','geometry-green.log','battery-grid-green.log','asset-detail-green.log','handoff-old-015.log','handoff-current-success.log','handoff-old-cached-400.log','handoff-cached-retry.log','lifecycle-fr965.log','pixel-rest-green.log','hosted-timing-green.log','hosted-wake-green.log','hosted-timing-454-green.log','cleanup.log','reuse-green.log')
    for name in required:
        if BASE+name not in r['evidence']:raise ValueError('UX02 evidence missing: '+name)
    for name,cases in [('fr165m-pixels-green.log',('test_clock_keeps_selected_mint','test_countdown_keeps_selected_mint','test_calendar_grows','test_battery_grows')),('geometry-green.log',('test_real_time_variants_have_gutters_center_and_budget','test_status_color_gaps_and_budget','test_finite_real_countdowns_fit_and_preserve_gutters')),('battery-grid-green.log',('test_each_battery_slot_fits_circle_and_keeps_icon_gap','test_lower_row_100_percent_and_12345_steps_do_not_overlap'))]:
        text=(root/BASE/name).read_text()
        if '\nOK\n' not in text or any(not any(line.startswith(c+' ') and line.endswith(' ... ok') for line in text.splitlines()) for c in cases):raise ValueError('UX02 pixel assertion missing: '+name)
    reuse=(root/BASE/'reuse-green.log').read_text()
    if 'test_callback_admission_and_resume_owners_retained' not in reuse or '\nOK\n' not in reuse: raise ValueError('UX01 owner reuse reconciliation failed')
    rest=(root/BASE/'pixel-rest-green.log').read_text()
    if 'test_four_phases_fit_and_every_pixel_rests' not in rest or '\nOK\n' not in rest: raise ValueError('four-phase pixel rest failed')
    priorbuild=json.loads((root/BASE/'upgrade-final-build.json').read_text())
    for name in ('watchface/source/NativeTransfer.mc','watchface/source/LocalePresentation.mc'):
        if priorbuild['productionSources'][name]!=r['sources'][name]: raise ValueError('upgrade assertion owner changed: '+name)
    import re
    for name in ('hosted-timing-green.log','hosted-timing-454-green.log'):
        raw=(root/BASE/name).read_text()
        match=re.search(r'requestToFullUpperMs=(\d+).*complete=true.*storeWriteDelta=0',raw)
        if 'metrics=false trace=false' not in raw or match is None or int(match.group(1))>8000: raise ValueError('hosted reopen deadline failed: '+name)
    wake=(root/BASE/'hosted-wake-green.log').read_text()
    for token in ('mode=1 sameBitmap=true decoding=false animation=false','mode=0 sameBitmap=true decoding=false'):
        if token not in wake: raise ValueError('hosted wake continuity failed: '+token)
    cleanup=(root/BASE/'cleanup.log').read_text()
    if 'newTemporal=null blank=true' not in cleanup or 'preserved=true' not in cleanup: raise ValueError('task cleanup failed')
    sdk=(root/BASE/'asset-detail-green.log').read_text()
    if parse_output(sdk,1,('uxUpgradeAttemptVersion','uxAssetErrorDetailsFit'))['status']!='passed':raise ValueError('UX02 native assertions failed')
    oldlog=(root/BASE/'handoff-old-015.log').read_text();newlog=(root/BASE/'handoff-current-success.log').read_text();cached=(root/BASE/'handoff-cached-retry.log').read_text();oldcached=(root/BASE/'handoff-old-cached-400.log').read_text()
    for token in ('HANDOFF_OLD startup=0.1.5','NATIVE_RESPONSE feed code=-400'):
        if token not in oldlog or token not in oldcached:raise ValueError('old-version failure witness incomplete: '+token)
    for text in (newlog,cached):
        for token in ('HANDOFF_NEW prior_status=', 'code=>-400','field4=5','clock=3','countdown=4','NATIVE_RESPONSE feed code=200','build=>0.1.6','stage=>received'):
            if token not in text:raise ValueError('upgrade witness incomplete: '+token)
    lifecycle=(root/BASE/'lifecycle-fr965.log').read_text()
    for token in ('NATIVE_LIFECYCLE sleep','NATIVE_LIFECYCLE wake','UX_TICK mode=1'):
        if token not in lifecycle:raise ValueError('FR965 lifecycle witness incomplete: '+token)
    import re
    ticks=sorted({int(m.group(1))//60 for m in re.finditer(r'UX_TICK mode=1 now=(\d+)',lifecycle)})
    if len(ticks)<3 or ticks[-1]-ticks[0]<2:raise ValueError('FR965 LOW minute observations incomplete')
    with tempfile.TemporaryDirectory(prefix='spacefox-ux02-prior-') as d:
        target=Path(d)
        for folder in ('watchface','locales','tools'):shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for folder in ('openspec','corpus','tests','assets','catalog','schemas'):(target/folder).symlink_to(root/folder,target_is_directory=True)
        for name,item in r['priorSnapshots'].items():
            dest=target/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(checked(**item),dest)
        (target/'locales/catalog.json').write_text(json.dumps(old,indent=2)+'\n')
        if prior_validate(target,old)!=old['supportPolicy']['softwareQualifiedLocales']:raise ValueError('retained UX01 proof failed')
    return catalog['supportPolicy']['softwareQualifiedLocales']
