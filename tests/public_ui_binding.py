"""Read original UI evidence and separately qualify current changed seams.

The retained 2557ms/sparse-layout measurements describe their original source.
Current DISPLAY03/full-map/source14 composition is checked independently below;
none of those old numbers is relabelled as a new full-map or signed14 run.
"""
import hashlib
import json
from pathlib import Path
import re

from tests.public_proof_inputs import recorded_input, verify_current_closure
from tools.run_native_tests import parse_output
from tools.spacefox.native_profile import png_pixels
from tools.verify_current_ui_batch import NAMES, CLOCK_NAMES, validate_aod_masks

ROOT = Path(__file__).resolve().parents[1]
BASE = 'openspec/changes/spacefox-watchface/evidence/current-native-ui'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def verify(root):
    root = Path(root)
    base = root / BASE
    record = json.loads((base/'batch.json').read_text())
    required = {'frames/en-face.png', 'frames/ru-face.png', 'frames/runtime.log', 'frames/build.json',
                'fields/native.log', 'fields/receipt.json', 'clock/native.log', 'clock/receipt.json',
                'lifecycle/native.log', 'lifecycle/receipt.json', 'recovery/native.log', 'recovery/receipt.json',
                'settings-reopen/reopen.log', 'settings-reopen/build.json'} | {
                    'frames/aod-'+str(i)+'-face.png' for i in range(4)}
    if not required <= set(record['files']):
        raise ValueError('required current UI evidence missing')
    # Retain the original immutable record. A rehashed edited record cannot
    # redefine its closure, and individual raw corruption is checked explicitly.
    from tests.public_proof_inputs import manifest
    bundle = manifest()
    expected = bundle['uiBatchSha256']
    if sha((base/'batch.json').read_bytes()) != expected:
        raise ValueError('current UI evidence changed: batch.json')
    for name, expected in record['files'].items():
        path = Path(name)
        if path.is_absolute() or '..' in path.parts or sha((base/path).read_bytes()) != expected:
            raise ValueError('current UI evidence changed: '+name)
    try:
        verify_current_closure(root)
    except AssertionError as error:
        raise ValueError('current UI semantic owner changed: '+str(error)) from error

    # Every historical source byte is exported and hash-bound. It is read as
    # historical data; no private Git lookup, SDK install or fake Git tree occurs.
    for relative in ('frames/build.json','fallback/build.json','real-view/build.json',
                     'inflight/build.json','settings-reopen/build.json',
                     'fields/receipt.json','clock/receipt.json','lifecycle/receipt.json',
                     'recovery/receipt.json','settings/receipt.json','menu/receipt.json'):
        build = json.loads((base/relative).read_text())
        for field in ('productionSources', 'productionResources', 'inputHashes'):
            for name, expected in build.get(field, {}).items():
                if sha(recorded_input(name, expected)) != expected:
                    raise ValueError('retained UI source changed: '+name)
        if 'probeSha256' in build and sha((base/Path(relative).parent/'Probe.mc').read_bytes()) != build['probeSha256']:
            raise ValueError('retained UI probe changed: '+relative)
    def result(folder, names, receipt='receipt.json', log='native.log', code='rawExit'):
        r = json.loads((base/folder/receipt).read_text())
        parsed = parse_output((base/folder/log).read_text(), r[code], names)
        if parsed['status'] != 'passed':
            raise ValueError('retained UI named assertion incomplete: '+folder)
        return parsed['observed_tests']
    fields = result('fields', NAMES)
    clock = result('clock', CLOCK_NAMES)
    lifecycle = result('lifecycle', ('finalAnimationLifecycle','finalAnimationBounds','finalAodMinuteGuard','finalLocalCalendar'))
    recovery = result('recovery', ('currentLowRecovery',))
    settings = result('settings', ('finalSettingsPositive','finalSettingsNegative'))
    settings.update(result('menu', ('currentMenuSettings',)))
    metrics = result('retained-fitness', ('metricAvailable','metricDenied','metricUnsupported','metricMissing'),
                     receipt='metrics-observation.json', log='native-tests.log', code='raw_exit_code')
    runtime = (base/'frames/runtime.log').read_text()
    natural = re.search(r'UI_NATURAL_DONE elapsedMs=(\d+) frames=(\d+) running=false progress=0\.000000', runtime)
    if not natural or not 2000 <= int(natural[1]) <= 3000:
        raise ValueError('retained natural animation incomplete')
    masks = []
    for phase in range(4):
        width, height, pixels = png_pixels((base/f'frames/aod-{phase}-face.png').read_bytes())
        if (width, height) != (390,390):
            raise ValueError('retained face dimensions changed')
        stride = len(pixels)//(width*height)
        masks.append({y*390+x for y in range(390) for x in range(390)
                      if (x-195)**2+(y-195)**2 < 190**2 and any(pixels[(y*390+x)*stride:(y*390+x)*stride+3])})
    validate_aod_masks(masks)
    reopen = base/'settings-reopen'
    def hashes(name):
        return {line.split()[-1].rsplit('/',1)[-1]:line.split()[0] for line in (reopen/name).read_text().splitlines()}
    before, after = hashes('pre.sha256'), hashes('post.sha256')
    if not {'USR.PRG','USR.DAT','USR.IDX','USR.SET'} <= set(before) or set(before) != set(after):
        raise ValueError('retained installed inventory incomplete')
    if any(before[name] != after[name] for name in ('USR.PRG','USR.DAT','USR.IDX')):
        raise ValueError('retained installed package or data changed')
    for name, test in [('selected-flag.log','test_selected_country_and_mismatch'),
                       ('corrected-site.log','test_corrected_site_rebuilds_the_projected_point')]:
        log = (base/'visual-applicability'/name).read_text()
        if test not in log or not log.rstrip().endswith('OK'):
            raise ValueError('retained site/flag control incomplete')

    # These existing source-specific compositions cover the changed current
    # owners, their actual newer observations, and the deliberately bounded
    # connection to original field/settings/geography/mode observations.
    from tests.test_display03_receipt_binding import (
        Display03ReceiptBindingTest, CurrentCoreCompositionTest,
        CurrentSettingsCompositionTest, CurrentGeographyCompositionTest)
    Display03ReceiptBindingTest.setUpClass()
    Display03ReceiptBindingTest('test_modes_positive').test_modes_positive()
    CurrentCoreCompositionTest('test_display_positive').test_display_positive()
    CurrentSettingsCompositionTest('test_settings_positive').test_settings_positive()
    CurrentGeographyCompositionTest('test_geography_positive').test_geography_positive()
    return dict(settingsResults=settings, siteControls=['selected-country-mismatch','corrected-site-point'],
                fieldResults=fields, clockResults=clock, lifecycleResults=lifecycle,
                metricResults=metrics, recoveryResults=recovery,
                reopenSetHashChanged=before['USR.SET'] != after['USR.SET'],
                naturalMs=int(natural[1]),frames=int(natural[2]),aodLit=[len(m) for m in masks],
                aodIntersection=len(set.intersection(*masks)),
                scope='Original UI values with separately authenticated current DISPLAY03/version14 composition; no fresh SDK result.')
