"""Check source-bound current FR165 field, scene and AOD observations.

This reads retained simulator evidence; it does not execute Garmin software or
establish physical display, battery, phone, or Store behavior.
"""
import gzip
import hashlib
import json
import math
import re
import subprocess
from pathlib import Path
from tools.run_native_tests import parse_output
from tools.spacefox.native_profile import png_pixels

CLOCK_NAMES = ('currentClockPositive','currentClockNegative','currentClockAdapter','currentClockFormatting','currentColorStates')
NAMES = ('currentLayoutEnglish','currentLayoutRussianLong','basicFieldsPositive',
         'basicFieldsNegative','basicUnavailablePositive','basicUnavailableNegative',
         'basicBatteryPositive','basicBatteryNegative')
OWNERS = ('Fitness.mc','LocalePresentation.mc','SceneRenderer.mc','SpaceFoxApp.mc',
          'SpaceFoxView.mc','SceneSettings.mc','SceneContext.mc','ScheduleState.mc',
          'WatchClock.mc','NativeAnimation.mc','NativeVisualRenderer.mc','SceneLifecycle.mc',
          'SettingsMenu.mc','SettingsMenuText.mc')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def validate_circle_box(box):
    if any((px-195)**2+(py-195)**2 > 195**2 for px in (box[0],box[2]) for py in (box[1],box[3])):
        raise ValueError('current rendered text outside circular bounds')


def validate_vertical_gap(upper_last, lower_first):
    if upper_last+1 >= lower_first:
        raise ValueError('actual Russian lower field and footer overlap')


def validate_aod_masks(sets):
    if len(sets) != 4 or any(not pixels for pixels in sets):
        raise ValueError('AOD four nonempty phases required')
    if any(len(pixels)/(math.pi*195**2) >= 0.1 for pixels in sets):
        raise ValueError('AOD sampled pixel budget exceeded')
    if set.intersection(*sets):
        raise ValueError('AOD four-phase interior rest failed')


def verify(root):
    root = Path(root).resolve()
    base = root/'openspec/changes/spacefox-watchface/evidence/current-native-ui'
    record = json.loads((base/'batch.json').read_text())
    if record['scope'] != 'current-ui-directed-frames-and-fields':
        raise ValueError('wrong current UI batch')
    required = {'frames/en-face.png','frames/ru-face.png','frames/runtime.log','frames/build.json',
                'fields/native.log','fields/receipt.json','clock/native.log','clock/receipt.json',
                'lifecycle/native.log','lifecycle/receipt.json','recovery/native.log','recovery/receipt.json',
                'settings-reopen/reopen.log','settings-reopen/build.json'} | {'frames/aod-'+str(i)+'-face.png' for i in range(4)}
    if not required <= set(record['files']):
        raise ValueError('required current UI evidence missing')
    for name, expected in record['files'].items():
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or digest((base/p).read_bytes()) != expected:
            raise ValueError('current UI evidence changed: '+name)
    fields = json.loads((base/'fields/receipt.json').read_text())
    log = (base/'fields/native.log').read_text()
    field_result = parse_output(log, fields['rawExit'], NAMES)
    if field_result['status'] != 'passed':
        raise ValueError('current field assertions failed')
    clock = json.loads((base/'clock/receipt.json').read_text())
    clock_result = parse_output((base/'clock/native.log').read_text(), clock['rawExit'], CLOCK_NAMES)
    if clock_result['status'] != 'passed':
        raise ValueError('current clock or color assertions failed')
    clock_path='watchface/current-clock-tests/ClockTests.mc'
    if digest((root/clock_path).read_bytes()) != clock['inputHashes'][clock_path]:
        raise ValueError('current clock assertions changed')
    field_path = 'watchface/current-fields-tests/FieldsTests.mc'
    if digest((root/field_path).read_bytes()) != fields['inputHashes'][field_path]:
        raise ValueError('current field assertions changed')
    build = json.loads((base/'frames/build.json').read_text())
    if build['exitCode'] != 0 or build['device'] != 'fr165' or build['tests']:
        raise ValueError('current UI observer build failed')
    probe = (base/'frames/Probe.mc').read_bytes()
    if digest(probe) != build['probeSha256']:
        raise ValueError('current UI observer probe changed')
    portable = (root/'tests/native_scene_diagnostics/current-508/CurrentUiFrames.mc').read_text()
    expected_probe = portable.replace('function initialize(){SpaceFoxApp.initialize();}',
        'function initialize(){SpaceFoxApp.initialize();System.println("SFR_PROBE owner='+build['ownerTag']+'");}')
    if probe.decode() != expected_probe:
        raise ValueError('portable UI observer differs from executed probe')
    for owner in OWNERS:
        name = 'watchface/source/'+owner
        actual = digest((root/name).read_bytes())
        if fields['inputHashes'][name] != actual or clock['inputHashes'][name] != actual or build['productionSources'][name] != actual:
            raise ValueError('current UI semantic owner changed: '+name)
    for name, expected in build['productionResources'].items():
        if name.startswith(('watchface/resources/fonts/', 'watchface/resources/drawables/',
                            'watchface/resources/settings/', 'watchface/resources-rus/')):
            if digest((root/name).read_bytes()) != expected or fields['inputHashes'].get(name) != expected:
                raise ValueError('current UI font, art or settings resource changed: '+name)
    from tools.native_language_policy import software_locales
    if software_locales(root) != ['en','ru','de','fr','es']:
        raise ValueError('retained finite/site qualification not admitted')
    visual = base/'visual-applicability'
    old_build=json.loads((visual/'old-build.json').read_text())
    for name in ('SceneRenderer.mc','LocalePresentation.mc','FeedScene.mc','NativeSfr.mc','NativeVisualRenderer.mc','SettingsMenu.mc','SceneSettings.mc','SpaceFoxApp.mc'):
        old_bytes=(visual/name).read_bytes()
        if digest(old_bytes) != old_build['productionSources']['watchface/source/'+name]:
            raise ValueError('retained visual source differs: '+name)
    for name in ('watchface/source/SceneContext.mc',):
        if digest((root/name).read_bytes()) != old_build['productionSources'][name]:
            raise ValueError('retained visual context owner changed')
    for name in ('watchface/resources/json/Locale0.json','watchface/resources/json/Locale1.json','watchface/resources/drawables/LaunchMarker.png'):
        if digest((root/name).read_bytes()) != old_build['productionResources'][name]:
            raise ValueError('retained header or marker resource changed')
    old_assets=(visual/'NativeAssets.mc').read_bytes()
    if digest(old_assets) != old_build['productionSources']['watchface/source/generated/NativeAssets.mc']:
        raise ValueError('retained generated art mapping differs')
    current_assets=(root/'watchface/source/generated/NativeAssets.mc').read_text()
    for model in ('falcon-9','falcon-heavy','electron','ariane-62','ariane-64'):
        pattern=r'"'+re.escape(model)+r'" => new NativeModel\((Rez\.Drawables\.[A-Za-z0-9_]+)\)'
        before=re.search(pattern,old_assets.decode());after=re.search(pattern,current_assets)
        if not before or not after or before.group(1)!=after.group(1):
            raise ValueError('retained model-art mapping changed: '+model)
    if (visual/'SceneSettings.mc').read_bytes() != (root/'watchface/source/SceneSettings.mc').read_bytes():
        raise ValueError('retained settings persistence owner changed')
    old_menu=(visual/'SettingsMenu.mc').read_text();current_menu=(root/'watchface/source/SettingsMenu.mc').read_text()
    expected_menu=old_menu.replace(':title=>"SpaceFox"', ':title=>"SpaceFox "+NativeVersion.BUILD+" "+NativeVersion.ID')
    if expected_menu != current_menu:
        raise ValueError('retained menu binding changed beyond version title')
    old_app=(visual/'SpaceFoxApp.mc').read_text();current_app=(root/'watchface/source/SpaceFoxApp.mc').read_text()
    callback='    function onSettingsChanged() as Void {if(view!=null){view.setSettings(new SceneSettings(null).load());reloadFeed();WatchUi.requestUpdate();}}'
    if callback not in old_app or callback not in current_app:
        raise ValueError('retained settings callback changed')
    if (visual/'NativeVisualRenderer.mc').read_bytes() != (root/'watchface/source/NativeVisualRenderer.mc').read_bytes():
        raise ValueError('rocket renderer semantic input changed')
    old_renderer=(visual/'SceneRenderer.mc').read_text();current_renderer=(root/'watchface/source/SceneRenderer.mc').read_text()
    start='        var context = fullContext;'
    if old_renderer[old_renderer.index(start):old_renderer.index('        dc.setColor(0xB2C3CE')] != current_renderer[current_renderer.index(start):current_renderer.index('        if(context==null && art!=null)')]:
        raise ValueError('header, purpose, rocket or footer drawing changed')
    old_locale=(visual/'LocalePresentation.mc').read_text();current_locale=(root/'watchface/source/LocalePresentation.mc').read_text()
    if (old_locale[old_locale.index('    function number('):] != current_locale[current_locale.index('    function number('):]
            or old_locale[old_locale.index('    function mission('):old_locale.index('    function countdown(')] != current_locale[current_locale.index('    function mission('):current_locale.index('    function number(')]):
        raise ValueError('retained name fitting or mission mapping changed')
    old_sfr=(visual/'NativeSfr.mc').read_text();current_sfr=(root/'watchface/source/NativeSfr.mc').read_text()
    for name, next_name in (('sceneField','sceneKeys'),('admitOrigins','begin'),('prepareRole','checkIndex'),('checkIndex','checkRaw'),('checkRaw','closure')):
        start='    function '+name+'(';end='    function '+next_name+'('
        if old_sfr[old_sfr.index(start):old_sfr.index(end)] != current_sfr[current_sfr.index(start):current_sfr.index(end)]:
            raise ValueError('retained native scene identity guard changed: '+name)
    old_tree=(visual/'old-catalog-assets.git-tree').read_text().splitlines()
    current_tree=(visual/'current-catalog-assets.git-tree').read_text().splitlines()
    def entries(lines):
        return {line.split('\t',1)[1]:line.split('\t',1)[0] for line in lines}
    before_tree=entries(old_tree);after_tree=entries(current_tree)
    changed={name for name in set(before_tree)|set(after_tree) if before_tree.get(name)!=after_tree.get(name)}
    if changed != {'catalog/README.md'}:
        raise ValueError('retained asset or catalog content changed')
    live_tree=subprocess.check_output(['git','-C',str(root),'ls-tree','-r','HEAD','--','assets','catalog'],text=True).splitlines()
    if live_tree != current_tree:
        raise ValueError('current asset or catalog Git tree differs')
    for name, expected in record['siteControlInputs'].items():
        if digest((root/name).read_bytes()) != expected:
            raise ValueError('current site control input changed: '+name)
    for name, expected in record['siteControlGitTrees'].items():
        tree=subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD:'+name],text=True).strip()
        if tree != expected:
            raise ValueError('current catalog or asset tree changed: '+name)
    for file, test in (('selected-flag.log','test_selected_country_and_mismatch'),('corrected-site.log','test_corrected_site_rebuilds_the_projected_point')):
        raw=(visual/file).read_text()
        if test not in raw or 'Ran 1 test' not in raw or not raw.rstrip().endswith('OK'):
            raise ValueError('current site or flag control failed')
    fallback=base/'fallback'; fallback_build=json.loads((fallback/'build.json').read_text())
    if fallback_build['exitCode'] != 0 or digest((fallback/'Probe.mc').read_bytes()) != fallback_build['probeSha256']:
        raise ValueError('fallback draw build changed')
    for owner in (*OWNERS,'NativeSfr.mc','NativeBridgeFeed.mc','NativeFeed.mc','NativeCache.mc'):
        name='watchface/source/'+owner
        if fallback_build['productionSources'][name] != digest((root/name).read_bytes()):
            raise ValueError('fallback draw semantic owner changed: '+name)
    fallback_log=(fallback/'run.log').read_text()
    if fallback_build['ownerTag'] not in fallback_log or 'Bpoint=26.99677 matchingProjection=false marker=false oldRaster=false' not in fallback_log:
        raise ValueError('fallback nonmatching projection observation missing')
    realview=base/'real-view';real_build=json.loads((realview/'build.json').read_text())
    if real_build['exitCode'] != 0 or digest((realview/'Probe.mc').read_bytes()) != real_build['probeSha256']:
        raise ValueError('current selected-scene build differs')
    for owner in (*OWNERS,'NativeSfr.mc','NativeBridgeFeed.mc','NativeFeed.mc','NativeCache.mc'):
        name='watchface/source/'+owner
        if real_build['productionSources'][name] != digest((root/name).read_bytes()):
            raise ValueError('selected scene semantic owner changed: '+name)
    real_log=(realview/'run.log').read_text()
    if ((realview/'run.exit').read_text().strip() != '0' or real_build['ownerTag'] not in real_log or 'NEG_COMPLETE corruptRejected=true missingRefused=true priorPointerPreserved=true freshBContext=true noOldBitmap=true retryB=true recoveryA=true actualOldBitmapCleared=true' not in real_log):
        raise ValueError('current selected-scene recovery observation missing')
    inflight=base/'inflight';inflight_build=json.loads((inflight/'build.json').read_text())
    if inflight_build['exitCode'] != 0 or digest((inflight/'Probe.mc').read_bytes()) != inflight_build['probeSha256']:
        raise ValueError('in-flight lifecycle build changed')
    for owner in (*OWNERS,'NativeSfr.mc','NativeBridgeFeed.mc','NativeFeed.mc','NativeCache.mc'):
        name='watchface/source/'+owner
        if inflight_build['productionSources'][name] != digest((root/name).read_bytes()):
            raise ValueError('in-flight lifecycle semantic owner changed: '+name)
    inflight_log=(inflight/'inflight.log').read_text()
    if (inflight_build['ownerTag'] not in inflight_log or
        not re.search(r'event=display mode=1 buildTimer=false build=false requested=false.*animation=false',inflight_log) or
        not re.search(r'event=display mode=2 buildTimer=false build=false requested=false.*animation=false',inflight_log) or
        'HIDE_BEFORE timer=true build=true pending=true' not in inflight_log or
        'HIDE_AFTER timer=false build=false pending=false animation=false fitness=false' not in inflight_log or
        'bitmap=true sameBitmap=true' not in inflight_log):
        raise ValueError('in-flight LOW/OFF/hide or resume observation missing')
    lifecycle = json.loads((base/'lifecycle/receipt.json').read_text())
    lifecycle_names=('finalAnimationLifecycle','finalAnimationBounds','finalAodMinuteGuard','finalLocalCalendar')
    lifecycle_result = parse_output((base/'lifecycle/native.log').read_text(), lifecycle['rawExit'], lifecycle_names)
    if lifecycle_result['status'] != 'passed':
        raise ValueError('current lifecycle assertions failed')
    life_path='watchface/current-lifecycle-tests/LifecycleTests.mc'
    if digest((root/life_path).read_bytes()) != lifecycle['inputHashes'][life_path]:
        raise ValueError('current lifecycle assertions changed')
    for owner in OWNERS:
        name='watchface/source/'+owner
        if lifecycle['inputHashes'][name] != digest((root/name).read_bytes()):
            raise ValueError('current lifecycle semantic owner changed: '+name)
    reopen = base/'settings-reopen'
    reopen_build = json.loads((reopen/'build.json').read_text())
    reopen_probe=(reopen/'Probe.mc').read_bytes()
    if reopen_build['exitCode'] != 0 or digest(reopen_probe) != reopen_build['probeSha256']:
        raise ValueError('settings reopen build failed')
    reopen_source=(root/'tests/native_scene_diagnostics/current-508/CurrentSettingsReopen.mc').read_text()
    expected_reopen=reopen_source.replace('function initialize(){SpaceFoxApp.initialize();}',
        'function initialize(){SpaceFoxApp.initialize();System.println("SFR_PROBE owner='+reopen_build['ownerTag']+'");}')
    if reopen_probe.decode() != expected_reopen:
        raise ValueError('settings reopen source differs')
    for owner in OWNERS:
        name='watchface/source/'+owner
        if reopen_build['productionSources'][name] != digest((root/name).read_bytes()):
            raise ValueError('settings reopen semantic owner changed: '+name)
    seed=(reopen/'seed.log').read_text(); again=(reopen/'reopen.log').read_text()
    if ((reopen/'seed.exit').read_text().strip() != '124' or 'SETTINGS_SEEDED ru=true fields=4 colors=6 url=true' not in seed
            or (reopen/'reopen.exit').read_text().strip() != '0' or 'push=false' not in again
            or 'SETTINGS_COLD_REOPEN ru=true fields=4 colors=6 url=true' not in again
            or reopen_build['ownerTag'] not in seed or reopen_build['ownerTag'] not in again):
        raise ValueError('settings same-package reopen incomplete')
    def installed_hashes(name):
        return {line.split()[-1].rsplit('/',1)[-1]:line.split()[0] for line in (reopen/name).read_text().splitlines()}
    before=installed_hashes('pre.sha256');after=installed_hashes('post.sha256')
    if not {'USR.PRG','USR.DAT','USR.IDX','USR.SET'} <= set(before) or set(before) != set(after):
        raise ValueError('settings installed inventory incomplete')
    if any(before[name] != after[name] for name in ('USR.PRG','USR.DAT','USR.IDX')):
        raise ValueError('installed package or data changed across reopen')
    runtime_binding=json.loads((root/'tests/native_scene_diagnostics/runtime-binding.json').read_text())
    if digest((root/'tests/native_scene_diagnostics/RunInstalled.class').read_bytes()) != runtime_binding['retainedRunnerSha256']['RunInstalled.class']:
        raise ValueError('direct reopen runner changed')
    setting_controls={}
    for folder, names, testpath in (
        ('settings',('finalSettingsPositive','finalSettingsNegative'),'watchface/current-ui-tests/SettingsTests.mc'),
        ('menu',('currentMenuSettings',),'watchface/current-menu-tests/MenuTests.mc')):
        folder_path=base/folder; receipt=json.loads((folder_path/'receipt.json').read_text())
        result=parse_output((folder_path/'native.log').read_text(),receipt['rawExit'],names)
        if result['status'] != 'passed' or digest((root/testpath).read_bytes()) != receipt['inputHashes'][testpath]:
            raise ValueError('current settings or menu control differs: '+folder)
        for owner in OWNERS:
            name='watchface/source/'+owner
            if receipt['inputHashes'][name] != digest((root/name).read_bytes()):
                raise ValueError('current settings semantic owner changed: '+name)
        setting_controls.update(result['observed_tests'])
    retained = base/'retained-fitness'
    metrics=json.loads((retained/'metrics-observation.json').read_text())
    metric_names=('metricAvailable','metricDenied','metricUnsupported','metricMissing')
    metric_result=parse_output((retained/'native-tests.log').read_text(),metrics['raw_exit_code'],metric_names)
    if metrics['build']['exit_code'] != 0 or metric_result['status'] != 'passed':
        raise ValueError('retained Fitness boundary receipt failed')
    for name, expected in metrics['build']['source_sha256'].items():
        if digest((root/name).read_bytes()) != expected:
            raise ValueError('retained Fitness semantic input changed: '+name)
    if digest((retained/'Fitness.mc').read_bytes()) != metrics['build']['transformed_fitness_sha256']:
        raise ValueError('retained transformed Fitness fixture changed')
    from xml.etree import ElementTree as ET
    manifest=ET.parse(root/'watchface/manifest.xml').getroot()
    permissions={node.attrib['id'] for node in manifest.iter() if node.tag.endswith('uses-permission')}
    if permissions != {'SensorHistory','Communications','Background'}:
        raise ValueError('current declared permission scope differs')
    recovery = json.loads((base/'recovery/receipt.json').read_text())
    recovery_log = (base/'recovery/native.log').read_text()
    recovery_result = parse_output(recovery_log, recovery['rawExit'], ('currentLowRecovery',))
    if recovery_result['status'] != 'passed' or 'actualStore=true malformedRejected=true laterGenerationOlderSourceRejected=true sealStable=true minuteGuard=true highReopen=true countdown=T- 16:38:17' not in recovery_log:
        raise ValueError('current LOW recovery assertions failed')
    recovery_path='watchface/current-recovery-tests/RecoveryTests.mc'
    fixture_path='tests/fixtures/watch_refresh_cache/packets.json'
    for name in (recovery_path, fixture_path, *('watchface/source/'+n for n in OWNERS),
                 'watchface/source/NativeCache.mc','watchface/source/NativeFeed.mc',
                 'watchface/source/NativeBridgeFeed.mc','watchface/source/NativeJson.mc'):
        if recovery['inputHashes'][name] != digest((root/name).read_bytes()):
            raise ValueError('current LOW recovery input changed: '+name)
    fixture=json.loads((root/fixture_path).read_text());initial=json.loads(fixture['packets']['initial']);moved=json.loads(fixture['packets']['moved'])
    stale=json.loads((base/'recovery/DisplayStale.json').read_text())['raw'];stale=json.loads(stale)
    expected=json.loads(fixture['packets']['initial']);expected['publisher']['generation']=3
    if stale != expected or not (stale['publisher']['generation'] > moved['publisher']['generation'] and stale['publisher']['selectionValidatedUtc'] < moved['publisher']['selectionValidatedUtc']):
        raise ValueError('regressive source fixture differs')
    runtime = (base/'frames/runtime.log').read_text()
    natural = re.search(r'UI_NATURAL_DONE elapsedMs=(\d+) frames=(\d+) running=false progress=0\.000000', runtime)
    if 'UI_NATURAL_START running=true' not in runtime or not natural or not 2000 <= int(natural[1]) <= 3000 or int(natural[2]) < 2:
        raise ValueError('natural current animation incomplete')
    if 'UI_ACTIVE_EN' not in runtime or 'UI_ACTIVE_RU' not in runtime or 'UI_AOD_COMPLETE phases=4' not in runtime:
        raise ValueError('current frame sequence incomplete')
    for phase, countdown in enumerate(('T- 49:02:03','T- 49:01:03','T- 49:00:03','T- 48:59:03')):
        marker = 'UI_AOD phase='+str(phase)+' minute='+str(30000000+phase)+' countdown='+countdown+' running=false'
        if marker not in runtime:
            raise ValueError('current AOD phase missing: '+str(phase))
    if digest((root/'tests/test_display_corpus.py').read_bytes()) != record['currentCorpusTestSha256']:
        raise ValueError('current corpus harness changed')
    corpus = json.loads((root/'corpus/real-schedule-basic-five-20261113/display-corpus.json').read_text())
    strings = json.loads((root/'corpus/real-schedule-basic-five-20261113/display-texts.json').read_text())
    selected = next(row for row in corpus['launches'] if row[0] == 'fcd23739-8135-43bb-9524-a5dba87d40ac')
    if [strings[i] if i is not None else '' for i in selected[3]] != ['Long March 4B','China Aerospace Science and Technology Corporation','Earth Science',"CN · Taiyuan Satellite Launch Center, People's Republic of China"]:
        raise ValueError('real long-name source record changed')
    font_tables = {}
    for name in ('Time80','Metric32'):
        entries = {}
        for line in (root/('watchface/resources/fonts/'+name+'.fnt')).read_text().splitlines():
            if line.startswith('char '):
                entry = {k:int(v) for k,v in re.findall(r'(\w+)=(-?\d+)',line)}
                entries[entry['id']] = entry
        font_tables[name] = entries
    for name, expected_date in (('currentLayoutEnglish','Sat 14.11'),('currentLayoutRussianLong','Сб 14.11')):
        start = log.index('Executing test '+name+'...')
        end = log.index('\nPASS', start)
        rows = []
        for line in log[start:end].splitlines():
            if 'BASIC_TEXT|' not in line:
                continue
            _,kind,x,y,width,height,value = line[line.index('BASIC_TEXT|'):].split('|',6)
            x,y,width,height = map(int,(x,y,width,height))
            if kind in ('time','metric'):
                table = font_tables['Time80' if kind == 'time' else 'Metric32']
                cursor = x-width/2; boxes = []
                for char in value:
                    glyph = table[ord(char)]
                    boxes.append((cursor+glyph['xoffset'], y+glyph['yoffset'], cursor+glyph['xoffset']+glyph['width'], y+glyph['yoffset']+glyph['height']))
                    cursor += glyph['xadvance']
                box = (min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes))
            else:
                box = (x-width/2,y,x+width/2,y+height)
            validate_circle_box(box)
            rows.append((kind,x,y,value))
        if len(rows) != 12 or expected_date not in [r[3] for r in rows] or len([r for r in rows if r[0]=='metric']) != 4:
            raise ValueError('current date or four field draw calls missing')
    sets=[]
    for label in ('en','ru','aod-0','aod-1','aod-2','aod-3'):
        raw = gzip.decompress((base/('frames/'+label+'.ppm.gz')).read_bytes())
        header = b'P6\n1200 1200\n255\n'
        if not raw.startswith(header) or len(raw) != len(header)+1200*1200*3:
            raise ValueError('bad raw screen capture')
        width,height,pixels = png_pixels((base/('frames/'+label+'-face.png')).read_bytes())
        if (width,height)!=(390,390):
            raise ValueError('bad face crop')
        stride=len(pixels)//(width*height);lit=set()
        if label == 'ru':
            pink=[]; footer=[]
            for yy in range(280,341):
                for xx in range(45,320):
                    at=(yy*390+xx)*stride; rr,gg,bb=pixels[at:at+3]
                    if rr>150 and gg>80 and bb>120 and rr>gg*1.15 and bb>gg*1.1:
                        pink.append(yy)
                    if yy>=321 and rr>120 and abs(rr-gg)<25 and abs(gg-bb)<25:
                        footer.append(yy)
            if not pink or not footer:
                raise ValueError('Russian lower field or footer not observed')
            validate_vertical_gap(max(pink),min(footer))
        for y in range(390):
            for x in range(390):
                at=(y*390+x)*stride; raw_at=len(header)+((y+255)*1200+x+87)*3
                rgb=bytes(pixels[at:at+3])
                if rgb != raw[raw_at:raw_at+3]:
                    raise ValueError('face crop differs from raw screen')
                if label.startswith('aod-') and (x-195)**2+(y-195)**2 < 190**2 and any(rgb):
                    lit.add(y*390+x)
        if label.startswith('aod-'):
            bands = ((103,137),(146,250),(253,287),(292,330))
            if any(not any(lo <= pixel//390 <= hi for lo,hi in bands) for pixel in lit):
                raise ValueError('AOD lit pixels outside four sparse text bands')
            sets.append(lit)
    validate_aod_masks(sets)
    return {'settingsResults':setting_controls,'siteControls':['selected-country-mismatch','corrected-site-point'],
            'fieldResults':field_result['observed_tests'],'clockResults':clock_result['observed_tests'],
            'lifecycleResults':lifecycle_result['observed_tests'],'metricResults':metric_result['observed_tests'],'recoveryResults':recovery_result['observed_tests'],'reopenSetHashChanged':before['USR.SET'] != after['USR.SET'],
            'naturalMs':int(natural[1]),'frames':int(natural[2]),'aodLit':[len(s) for s in sets],
            'aodIntersection':0,'circleDenominator':'pi*195^2','screenInteriorRadius':190}
