"""One current five-primary admission, retaining original finite observation scope.

The finite corpus and SDK/font observations are historical facts, not new
measurements. Current text/resource bytes are separately bound by one reviewed
applicability record; the release peer/source fence remains independent.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

PRIMARY = ['en', 'ru', 'de', 'fr', 'es']
# Updated only with the reviewed canonical record; it is not derived from an
# untrusted caller-provided catalog, so a repinned manifest cannot grant access.
CURRENT_PROOF_SHA256 = '4e9185ca5491c13ddecbae968be3512e4eade52bf85e1f355ca2b756d60657f7'


UI_KEYS = ('hour', 'minute', 'day', 'second', 'noSchedule', 'dateOnly', 'window',
           'timeUnknown', 'awaitUpdate', 'companyUnknown', 'missionUnknown', 'communications')
CALENDAR_DAYS = (('Sun','Mon','Tue','Wed','Thu','Fri','Sat'), ('Вс','Пн','Вт','Ср','Чт','Пт','Сб'),
                 ('So','Mo','Di','Mi','Do','Fr','Sa'), ('dim','lun','mar','mer','jeu','ven','sam'),
                 ('dom','lun','mar','mié','jue','vie','sáb'))


def native_semantic_paths(current_inputs):
    paths = {'tools/display_corpus.py', 'tools/current_language_probe.py',
             'watchface/current-language-tests/CurrentUi.mc',
             'watchface/source/LocalePresentation.mc', 'watchface/source/SceneRenderer.mc',
             'watchface/source/SceneContext.mc', 'watchface/source/SceneSettings.mc',
             'watchface/source/Fitness.mc', 'watchface/source/SpaceFoxView.mc',
             'watchface/source/generated/LocaleGraphemes.mc',
             'watchface/source/generated/SceneStrings.mc'}
    paths.update(name for name in current_inputs if name.startswith('watchface/resources/fonts/'))
    paths.update('watchface/resources/json/Locale'+str(i)+'.json' for i in range(5))
    return paths


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def checked(root, ref):
    require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'}, 'invalid qualification reference')
    name, expected = ref['path'], ref['sha256']
    require(isinstance(name, str) and name and not PurePosixPath(name).is_absolute()
            and '..' not in PurePosixPath(name).parts and re.fullmatch(r'[0-9a-f]{64}', expected or ''),
            'unsafe qualification reference')
    path = root / name
    require(not path.is_symlink() and path.resolve().is_relative_to(root) and path.is_file(),
            'missing qualification input: ' + name)
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == expected, 'qualification input changed: ' + name)
    return data


def validate(root, catalog):
    root = Path(root).resolve()
    policy = catalog['supportPolicy']
    require(policy.get('primaryLocales') == PRIMARY and policy.get('softwareQualifiedLocales') == PRIMARY,
            'current admission requires exactly five primary locales')
    pointer = policy.get('softwareQualificationProof')
    require(isinstance(pointer, dict) and set(pointer) == {'currentProof'}, 'one current qualification required')
    ref = pointer['currentProof']
    require(isinstance(ref, dict) and ref.get('sha256') == CURRENT_PROOF_SHA256,
            'current qualification differs from reviewed closure')
    proof = json.loads(checked(root, ref))
    require(proof.get('schema') == 1 and proof.get('scope') == 'current-five-primary-retained-finite'
            and proof.get('primaryLocales') == PRIMARY and proof.get('referenceVersion') == '0.2.9'
            and proof.get('referenceSource') == '1f53420a5af7c4479aca537a12197d10980e1c07',
            'current qualification scope differs')
    require(proof.get('physicalDeviceObserved') is False and proof.get('nativeSpeakerReviewed') is False,
            'qualification exceeds observed boundary')
    from tools.native_language_policy import input_paths, validate_generated_locale_source
    current = proof.get('currentInputs')
    require(isinstance(current, dict) and set(current) == set(input_paths(catalog, root)),
            'current text/resource input closure differs')
    for name, expected in current.items():
        checked(root, {'path': name, 'sha256': expected})
    validate_generated_locale_source(root, catalog, PRIMARY)
    peer = json.loads(checked(root, proof['referencePeer']))
    require(peer.get('kind') == 'stm-event-sequence-independent-peer' and peer.get('status') == 'GREEN'
            and peer.get('version') == '0.2.9' and peer.get('native_id') == 'd13aa334'
            and peer.get('software_review_source_revision') == proof['referenceSource'],
            'retained current-source peer boundary differs')
    gate = checked(root, proof['referenceGate']).decode('utf-8')
    require('ACTUAL_RELEASE_COMBINED_PEER_GATE PASS' in gate and 'version=0.2.9' in gate,
            'retained current-source admission observation absent')
    receipt = json.loads(checked(root, proof['finiteReceipt']))
    corpus_ref = proof['corpus']
    corpus_bytes = checked(root, corpus_ref)
    require(receipt.get('status') == 'passed' and receipt.get('evidenceSchemaVersion') == 1
            and receipt.get('qualifiedLocales') == PRIMARY and receipt.get('corpusSha256') == corpus_ref['sha256']
            and receipt.get('physicalDeviceObserved') is False and receipt.get('nativeSpeakerReviewed') is False
            and receipt.get('phoneSettingsRendered') is False, 'finite observation boundary differs')
    observations = receipt.get('observations')
    require(isinstance(observations, dict), 'finite observation set missing')
    base = PurePosixPath(proof['finiteReceipt']['path']).parent
    names = ('ui/build.json','ui/ui.log','ui/ui-execution.json','ui/compile.log','ui/Probe.mc.txt',
             'common/build.json','common/corpus.log','common/corpus-execution.json','common/compile.log',
             'common/Probe.mc.txt','fonts.json')
    require(set(observations) == {str(base / name) for name in names}, 'finite observation inventory differs')
    for name, digest in observations.items():
        checked(root, {'path': name, 'sha256': digest})
    from tools.display_corpus import load_complete_corpus
    corpus = load_complete_corpus(root / corpus_ref['path'], root)
    require(corpus['coverage']['sourceCount'] == receipt['nativeCommonRecords'] == 1822
            and corpus['coverage']['pageCount'] == 19 and corpus['coverage']['terminalNext'] is None,
            'finite corpus denominator differs')
    def observation(name):
        return root / str(base / name)
    fonts = json.loads(observation('fonts.json').read_text())
    require(fonts.get('status') == 'passed' and fonts.get('corpusSha256') == corpus_ref['sha256']
            and fonts.get('commonRoleMissingCodepoints') == []
            and {row['locale'] for row in fonts['ui']} == set(PRIMARY)
            and all(not row['missingCodepoints'] for row in fonts['ui']), 'finite font observation incomplete')
    require(set(fonts['fonts']) == {'RobotoRegular', 'NotoNaskhArabicRegular', 'NotoSansHebrewRegular',
            'NotoSansSCMedium', 'KosugiRegular', 'NanumGothicBold', 'PridiRegular'}
            and all(row.get('shaping') == [] for row in fonts['ui']), 'finite font/shaping scope differs')
    lock = json.loads((root / 'watchface/toolchain-lock.json').read_bytes())
    historical_lock_bytes = checked(root, proof['historicalToolchainLock'])
    historical_lock = json.loads(historical_lock_bytes)
    sdk = receipt.get('sdkBinding', {})
    # Device/profile additions and the accepted permission extension do not
    # erase measured compiler, SDK API, original profile or option identities.
    require(set(lock) == set(historical_lock) | {'profiles'}
            and all(historical_lock[k] == lock[k] for k in historical_lock if k != 'permissions')
            and set(historical_lock['permissions']) <= set(lock['permissions'])
            and len(set(lock['permissions'])) == len(lock['permissions'])
            and sdk.get('toolchainLockSha256') == hashlib.sha256(historical_lock_bytes).hexdigest()
            and sdk.get('product') == lock['product'] == 'fr165'
            and sdk.get('profileApi') == lock['profile_api']
            and sdk.get('sdkVersion') == lock['sdk_version']
            and sdk.get('compilerSha256') == lock['compiler_sha256'], 'finite SDK lock binding differs')
    for label, log_name in (('ui','ui.log'), ('common','corpus.log')):
        folder = observation(label)
        build = json.loads((folder/'build.json').read_text())
        execution = json.loads((folder/('ui-execution.json' if label == 'ui' else 'corpus-execution.json')).read_text())
        require(build.get('exitCode') == 0 and build.get('tests') is False and build.get('productionSourceScope') == 'all-native'
                and execution.get('exitCode') == 0 and execution.get('vmOutputObserved') is True,
                'finite SDK execution incomplete')
        require(hashlib.sha256((folder/'Probe.mc.txt').read_bytes()).hexdigest() == build['probeSha256'],
                'finite observed probe differs from compiled source')
        command = build['command']
        require(command[command.index('-d') + 1] == 'fr165', 'finite profile differs')
        jar = Path(command[command.index('-jar') + 1])
        require(jar.name == 'monkeybrains.jar' and jar.parent.parent.name == lock['sdk_directory'],
                'finite compiler path differs')
        compile_log = (folder/'compile.log').read_text()
        require('BUILD SUCCESSFUL' in compile_log and 'ERROR:' not in compile_log, 'finite compiler observation incomplete')
        log = (folder/log_name).read_text()
        require(not any(x in log for x in ('Error:', 'Unhandled Exception', 'Out Of Memory', 'Stack Overflow', 'FINITE_UI FAILED', 'FINITE_CORPUS FAILED')),
                'finite observation contains failure')
        owned = [line for line in log.splitlines() if 'owner='+build['ownerTag'] in line]
        if label == 'ui':
            ready = [dict(re.findall(r'(\w+)=([^\s]+)', line)) for line in owned if 'FINITE_UI READY locale=' in line]
            require(len(ready) == 5 and {row['locale'] for row in ready} == set(PRIMARY)
                    and all(row['words'] == '0' and row['renderedStates'] == '10' and row['sameBitmap'] == 'true' for row in ready)
                    and any('FINITE_UI COMPLETE locales=5' in line for line in owned), 'finite UI observations incomplete')
        else:
            done = [line for line in owned if 'FINITE_CORPUS COMPLETE ' in line]
            require(len(done) == 1 and 'records=1822' in done[0]
                    and ('compositions='+str(receipt['nativeCommonCompositions'])) in done[0]
                    and 'ordinaryBytes=126784' in done[0] and 'sameBitmap=true' in done[0],
                    'finite common corpus observation incomplete')
    # The newer observation is a separate, real current-source qualification;
    # historical SDK results above remain historical and are never repinned.
    import gzip
    from tools.run_native_tests import parse_output
    current_native = json.loads(checked(root, proof['currentNativeObservation']))
    require(current_native.get('schema') == 2 and current_native.get('status') == 'passed'
            and current_native.get('profile') == 'fr165m' and current_native.get('sdk') == '9.3.0-linux'
            and current_native.get('compilerSha256') == '082b2fd3f50578204e01d44313f43f2ce52a60dbfd6221f6b259b2687239de3f'
            and current_native.get('profileInputs') == lock['profiles']['fr165m']['files_sha256']
            and current_native.get('sourceRecords') == 1822 and current_native.get('uniqueCompositions') == 413
            and current_native.get('selectorCounts') == [1035,377,298,112]
            and current_native.get('selectorCompositions') == [128,128,128,29]
            and current_native.get('rawLauncherExit') == 1, 'current native observation incomplete')
    command = current_native['compilerCommand']
    require(command[0].endswith('/connectiq-sdk-lin-9.3.0-2026-10-20-95888f262/bin/monkeyc')
            and command[command.index('-d')+1] == 'fr165m' and '-t' in command,
            'current native compiler command differs')
    compiled = current_native.get('compiledNativeInputs')
    require(isinstance(compiled,dict) and compiled and all(isinstance(n,str)
            and isinstance(v,str) and re.fullmatch(r'[0-9a-f]{64}',v) for n,v in compiled.items()),
            'native compiled-input record missing')
    relevant = current_native.get('semanticInputs')
    require(isinstance(relevant,dict) and set(relevant) == native_semantic_paths(current),
            'native semantic input closure differs')
    for name, expected in relevant.items():
        checked(root, {'path':name,'sha256':expected})
        if name.startswith('watchface/'):
            require(compiled.get(name) == expected, 'native semantic source was not compiled: '+name)
    from tools.current_language_probe import build_resource_plan, probe_source
    rows, names, payloads = build_resource_plan(corpus)
    counts = [sum(row[4] for row in rows[i:i+128]) for i in range(0,len(rows),128)]
    compositions = [len(rows[i:i+128]) for i in range(0,len(rows),128)]
    resource_inputs = {name:hashlib.sha256(raw).hexdigest() for name,raw in payloads.items()}
    plan = json.loads(checked(root,current_native['resourcePlan']))
    require(plan == {'schema':1,'sourceRecords':1822,'uniqueCompositions':413,
                     'selectorCounts':counts,'selectorCompositions':compositions,'resourceInputs':resource_inputs}
            and current_native['resourceInputs'] == resource_inputs,
            'native resources differ from complete captured corpus projection')
    probe = checked(root,current_native['probe'])
    ui_probe = checked(root,current_native['uiProbe'])
    require(probe == probe_source(rows,names).encode()
            and ui_probe == (root/'watchface/current-language-tests/CurrentUi.mc').read_bytes()
            and current_native['privateSourceInputs'] == {
                'source/CurrentFinite.mc':hashlib.sha256(probe).hexdigest(),
                'source/CurrentUi.mc':hashlib.sha256(ui_probe).hexdigest()},
            'current native probe differs from canonical qualification plan')
    program = gzip.decompress(checked(root,current_native['program']))
    require(hashlib.sha256(program).hexdigest() == current_native['programSha256'],
            'current native program differs')
    require('BUILD SUCCESSFUL' in checked(root,current_native['compile']).decode(),
            'current native compile missing')
    refs = current_native['logs'];require(len(refs)==5,'current native selector set differs')
    for i,ref in enumerate(refs):
        selector = 'currentFivePrimaryAndBitmapFonts' if i==0 else 'currentRenderer'+str(i-1)
        raw = checked(root,ref).decode('utf-8')
        require(parse_output(raw,1,(selector,))['status']=='passed','current native selector failed: '+selector)
        if i==0:
            require('CURRENT_PRIMARY_COMPLETE locales=5 bitmapFonts=3 uiWords=60 calendarStates=35' in raw,
                    'current primary UI cohort missing')
        else:
            n=i-1
            require('CURRENT_JOINED records='+str(counts[n])+' expected='+str(counts[n])
                    +' compositions='+str(compositions[n])+' header_paints='+str(compositions[n])
                    +' nonempty=true projection=true' in raw,'current joined-header cohort differs')
    glyphs=json.loads(checked(root,current_native['uiGlyphReport']))
    require(glyphs.get('status')=='passed' and glyphs.get('fontSha256')==current_native['robotoSha256']
            and glyphs.get('LC_ALL')=='en_US.UTF-8' and len(glyphs['rows'])==5,
            'current UI glyph observation differs')
    for i,row in enumerate(glyphs['rows']):
        dictionary=json.loads((root/('watchface/resources/json/Locale'+str(i)+'.json')).read_text())
        texts=[dictionary[k] for k in UI_KEYS]+[day+' 17.11' for day in CALENDAR_DAYS[i]]
        require(row['locale']==PRIMARY[i] and row['count']==19 and row['missingCodepoints']==[]
                and [x['text'] for x in row['shapes']]==texts
                and all(x['glyphs'] and all(g.get('g') not in (None,0,'gid0','.notdef')
                        for g in x['glyphs']) for x in row['shapes']),
                'current UI glyph coverage incomplete')
    fields = json.loads(checked(root, current_native['fieldsFontReport']))
    require(fields.get('status') == 'passed' and {r['locale'] for r in fields['rows']} == set(PRIMARY)
            and all(not r['missingCodepoints'] and r['count'] == 55 and len(r['shapes']) == 55
                    and all(shape['glyphs'] and all(glyph.get('g') not in (None, 0, 'gid0', '.notdef')
                            for glyph in shape['glyphs']) for shape in r['shapes']) for r in fields['rows'])
            and fields['fonts']['RobotoRegular'] == current_native['robotoSha256'],
            'retained field glyph coverage differs')
    for name, expected in fields['inputs'].items():
        checked(root, {'path': name, 'sha256': expected})
    return list(PRIMARY)
