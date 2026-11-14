"""Source-bound extension of the retained timing/finite-text admission.

It validates historical bytes in a reconstructed local tree, not by changing
historical hashes. Current native tests and EN/RU frame logs prove the changed
scene. This is software-only evidence and makes no physical-device claim.
"""
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import struct
import tempfile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(root, catalog):
    from tools.native_language_policy import input_paths
    from tools.native_timing_requalification import validate as prior_validate
    from tools.run_native_tests import parse_output
    root=Path(root).resolve(); proof=catalog['supportPolicy']['softwareQualificationProof']; ref=proof['visualDeltaProof']
    def checked(name,digest):
        path=Path(name)
        if path.is_absolute() or '..' in path.parts or not (root/path).is_file() or sha(root/path)!=digest:
            raise ValueError('site visual proof input changed: '+name)
        return root/path
    record=json.loads(checked(ref['path'],ref['sha256']).read_text())
    if record['status']!='passed' or record['scope']!='retained-timing-finite-plus-native-site-visual-en-ru':
        raise ValueError('incomplete site visual proof')
    prior=json.loads(checked(record['priorCatalog']['path'],record['priorCatalog']['sha256']).read_text())
    prior_proof=prior['supportPolicy']['softwareQualificationProof']
    if set(proof)!=set(prior_proof)|{'visualDeltaProof'} or any(proof[k]!=prior_proof[k] for k in prior_proof if k!='productionSources'):
        raise ValueError('retained proof metadata changed')
    current=proof['productionSources']
    if current!=record['currentSources'] or set(current)!=set(input_paths(catalog,root)):
        raise ValueError('current qualification closure differs')
    for name,digest in current.items():checked(name,digest)
    old=prior_proof['productionSources']
    changed={name for name,digest in old.items() if current.get(name)!=digest}
    allowed={'tools/build_native_localization.py','tools/native_language_policy.py','tools/spacefox/native_profile.py',
             'watchface/source/FeedScene.mc','watchface/source/LocalePresentation.mc','watchface/source/NativeFeed.mc',
             'watchface/source/NativeJson.mc','watchface/source/SceneRenderer.mc','watchface/source/SceneContext.mc'} | {'watchface/resources/json/Locale'+str(i)+'.json' for i in range(5)}
    if changed!=set(record['reviewedChanges']) or changed!=allowed:raise ValueError('unreviewed qualification source delta')
    for name in changed:
        row=record['reviewedChanges'][name]
        if row['beforeSha256']!=old[name] or row['afterSha256']!=current.get(name) or not row['reason']:
            raise ValueError('invalid source comparison: '+name)
    # Reconstruct old source/resource files from the committed-byte snapshots;
    # old receipts keep their original hashes and actual execution boundaries.
    snapshots=record['priorSnapshots']
    with tempfile.TemporaryDirectory(prefix='spacefox-site-prior-') as temporary:
        oldroot=Path(temporary)
        for folder in ('watchface','locales','tools'):
            shutil.copytree(root/folder,oldroot/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for folder in ('openspec','corpus','tests','assets','catalog','schemas'):
            (oldroot/folder).symlink_to(root/folder,target_is_directory=True)
        for name,item in snapshots.items():
            target=oldroot/name;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(checked(item['path'],item['sha256']),target)
        if prior_validate(oldroot,prior)!=prior['supportPolicy']['softwareQualifiedLocales']:
            raise ValueError('retained timing/finite admission failed')
    for name,digest in record['evidenceFiles'].items():checked(name,digest)
    # The metadata-admission repair does not change renderer/layout inputs. The
    # original visual observations remain bound to their exact earlier source;
    # a separate current SDK assertion proves the changed admission owner.
    delta=record.get('metadataDelta')
    historical={}
    header_historical={}
    header=record.get('headerDelta')
    if header is not None:
        for name,item in header['previousSources'].items():header_historical[name]=sha(checked(item['path'],item['sha256']))
        if set(header_historical)!={'watchface/source/FeedScene.mc','watchface/source/SceneContext.mc','watchface/source/SceneRenderer.mc'}:raise ValueError('unexpected header source delta')
        for item in header['evidence'].values():checked(item['path'],item['sha256'])
        target=root/header['nativeUnit']; hb=json.loads((target/'build.json').read_text()); he=json.loads((target/'native-execution.json').read_text())
        if hb['exitCode']!=0 or not hb['tests'] or hb['productionSourceScope']!='all-native':raise ValueError('header native build incomplete')
        for name,digest in {**hb['productionSources'],**hb['productionResources']}.items():checked(name,digest)
        parsed_header=parse_output((target/'native.log').read_text(),he['exitCode'],('capturedHeaderChoice',))
        if parsed_header['status']!='passed' or parsed_header!=he['framework'] or ('HEADER_CHOICE_PASS captured=2 languages=2 fullFieldsRetained=true' not in (target/'native.log').read_text() or 'HEADER_CORPUS_BOUNDS headers=170 languages=2 valid=true' not in (target/'native.log').read_text()):raise ValueError('header native assertion failed')
        if sha(target/'Probe.mc')!=hb['probeSha256']:raise ValueError('header assertion source differs')
    if delta is not None:
        for name,item in delta['previousSources'].items():
            historical[name]=sha(checked(item['path'],item['sha256']))
        if set(historical)!={'watchface/source/NativeFeed.mc','watchface/source/NativeJson.mc'}:
            raise ValueError('unexpected metadata source delta')
        for item in delta['evidence'].values():checked(item['path'],item['sha256'])
        target=root/delta['nativeUnit']; mb=json.loads((target/'build.json').read_text()); me=json.loads((target/'native-execution.json').read_text())
        if mb['exitCode']!=0 or not mb['tests'] or mb['productionSourceScope']!='all-native':raise ValueError('metadata native build incomplete')
        for name,digest in {**mb['productionSources'],**mb['productionResources']}.items():
            if name in header_historical:
                if header_historical[name]!=digest:raise ValueError('historical metadata source differs: '+name)
            else:checked(name,digest)
        parsed_metadata=parse_output((target/'native.log').read_text(),me['exitCode'],('enrichmentAdmission',))
        if parsed_metadata['status']!='passed' or parsed_metadata!=me['framework'] or 'ENRICH PASS fiveTransitions=true fourContradictions=true cacheReopen=true staleRetained=true fullDigestsChanged=true' not in (target/'native.log').read_text():raise ValueError('metadata native assertion failed')
        if sha(target/'Probe.mc')!=mb['probeSha256']:raise ValueError('metadata assertion source differs')
    def checked_visual_build(build):
        for name,digest in {**build['productionSources'],**build['productionResources']}.items():
            if name in historical or name in header_historical:
                expected=historical[name] if name in historical else header_historical[name]
                if expected!=digest:raise ValueError('historical visual source differs: '+name)
            else:checked(name,digest)
    native=root/record['nativeUnit']; build=json.loads((native/'build.json').read_text()); execution=json.loads((native/'execution.json').read_text())
    if build['exitCode']!=0 or build['productionSourceScope']!='all-native' or build['tests'] is not True:
        raise ValueError('native unit build incomplete')
    checked_visual_build(build)
    expected=('siteFlagPositive','siteFlagNegative','siteCorpusBounds')
    parsed=parse_output((native/'native-tests.log').read_text(),execution['rawExitCode'],expected)
    if parsed['status']!='passed' or parsed!=execution['framework'] or 'SITE_CORPUS_BOUNDS rows=' not in (native/'native-tests.log').read_text():
        raise ValueError('native site assertion failure')
    # Reconstruct every distinct header/footer tuple from the hash-bound raw
    # finite pages. These are source strings; synthetic identity/position tests
    # do not introduce display names.
    from tools.spacefox.provider import _country_code
    collection=json.loads((root/'corpus/real-schedule-basic-five-20261113/collection.json').read_text())
    headers={};sites={};seen=set()
    if not collection['complete'] or collection['next'] is not None or len(collection['pages'])!=19:
        raise ValueError('finite corpus pagination incomplete')
    for page in collection['pages']:
        raw=gzip.decompress((root/'corpus/real-schedule-basic-five-20261113'/page['raw']).read_bytes())
        if hashlib.sha256(raw).hexdigest()!=page['responseSha256']:raise ValueError('finite corpus source changed')
        for item in json.loads(raw)['results']:
            if item['id'] in seen:raise ValueError('duplicate finite launch')
            seen.add(item['id']);config=(item.get('rocket') or {}).get('configuration') or {};org=item.get('launch_service_provider') or {};pad=item.get('pad') or {};loc=pad.get('location') or {};country=pad.get('country') or {}
            values=[config.get('full_name') or config.get('name') or '',org.get('name') or '',org.get('abbrev') or '',loc.get('name') or pad.get('name') or '',_country_code(country) or '',(item.get('mission') or {}).get('type') or '']
            values=[v if len(v)<=64 else v[:63]+'…' for v in values]
            headers.setdefault((values[0],values[1],values[2]),values);sites.setdefault((values[1],values[3],values[4]),values)
    corpus=json.loads(checked(record['layoutCorpus']['path'],record['layoutCorpus']['sha256']).read_text())
    if (len(seen)!=1822 or corpus!={'sourceLaunches':1822,'headerCases':len(headers),'footerCases':len(sites),'rows':sorted(list(headers.values())+list(sites.values()))}):
        raise ValueError('finite layout corpus differs from source')
    if 'SITE_CORPUS_BOUNDS rows='+str(len(corpus['rows']))+' languages=2 sourceLaunches=1822 valid=true' not in (native/'native-tests.log').read_text():
        raise ValueError('native layout case count differs')
    for i,row in enumerate(catalog['locales']):
        payload=json.loads((root/'watchface/resources/json'/('Locale'+str(i)+'.json')).read_text())
        locale=json.loads((root/'locales'/(row['id']+'.json')).read_text())
        if payload['communications']!=locale['communications']:raise ValueError('category resource differs: '+row['id'])
    if header is not None:
        header_rows={}
        for row in corpus['rows']:header_rows.setdefault(tuple(row[:3]),row)
        if len(header_rows)!=170 or json.dumps(list(header_rows.values()),ensure_ascii=False,separators=(',',':')) not in (root/header['nativeUnit']/'Probe.mc').read_text():
            raise ValueError('header native rows differ from source corpus')
    assertion=checked(record['assertions']['path'],record['assertions']['sha256'])
    if json.dumps(corpus['rows'],ensure_ascii=False,separators=(',',':')) not in assertion.read_text():
        raise ValueError('native layout rows differ from source corpus')
    if sha(native/'Probe.mc')!=sha(assertion) or sha(assertion)!=build['probeSha256']:
        raise ValueError('native assertions differ from compiled probe')
    gallery=root/record['gallery']; gb=json.loads((gallery/'build.json').read_text())
    if gb['exitCode']!=0 or gb['productionSourceScope']!='all-native' or gb['tests'] is not False:
        raise ValueError('native gallery build incomplete')
    checked_visual_build(gb)
    from tools.native_site_flag_observer import source as observer_source
    expected_observer=observer_source().replace('SpaceFoxApp.initialize();',
        'SpaceFoxApp.initialize();NativeMetrics.ownerTag='+json.dumps(gb['ownerTag'])+';System.println("SFR_PROBE owner="+NativeMetrics.ownerTag);',1)
    if (gallery/'Probe.mc').read_text()!=expected_observer or hashlib.sha256(expected_observer.encode()).hexdigest()!=gb['probeSha256']:
        raise ValueError('native gallery probe differs from source generator')
    text=(gallery/'run.log').read_text()
    if 'SFR_PROBE owner='+gb['ownerTag'] not in text:raise ValueError('native gallery owner missing')
    for token in ('FINAL_FRAME_READY label=en-long','FINAL_FRAME_READY label=ru-long',
                  '|en-long|vector|195|70|144|22|13950955|Communications',
                  '|ru-long|vector|195|70|53|22|13950955|Связь',
                  '|en-long|vector|208|319|206|22|13950955|US · Cape Canaveral SFS',
                  '|ru-long|vector|208|319|206|22|13950955|US · Cape Canaveral SFS'):
        if token not in text:raise ValueError('missing native visual observation: '+token)
    for image in record['frames']:
        raw=checked(image['path'],image['sha256']).read_bytes()
        if raw[:8]!=b'\x89PNG\r\n\x1a\n' or struct.unpack('>II',raw[16:24])!=(390,390):raise ValueError('native frame dimensions')
    return catalog['supportPolicy']['softwareQualifiedLocales']
