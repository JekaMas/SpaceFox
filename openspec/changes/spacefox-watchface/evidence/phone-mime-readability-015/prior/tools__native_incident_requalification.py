"""Validate the first-install delta against retained, source-bound locale evidence.

The retained five-language corpus is replayed on its original bytes. New
observations cover the changed first-install UI in EN/RU and the actual SDK
delivery path; they do not claim physical-device or other-language review.
"""
import hashlib
import gzip
import json
import re
from pathlib import Path
import shutil
import tempfile

SOURCES = {
    'watchface/source/FeedService.mc', 'watchface/source/NativeTransfer.mc',
    'watchface/source/NativeCache.mc', 'watchface/source/NativeIncoming.mc',
    'watchface/source/NativeForegroundApp.mc', 'watchface/source/SpaceFoxApp.mc',
    'watchface/source/SpaceFoxView.mc', 'watchface/source/SceneRenderer.mc',
    'watchface/source/LocalePresentation.mc', 'watchface/resources/drawables/drawables.xml',
    'watchface/resource-inputs/art-unknown.svg', 'watchface/resources/drawables/art_unknown.png',
    'watchface/incident-tests/FirstInstallTests.mc', 'tools/native_language_policy.py',
    'tools/native_incident_requalification.py',
}
EVIDENCE = {
    'unit.log', 'isolate.log.gz', 'observer.mc', 'offline-en.png', 'offline-ru.png',
    'selected-en.png', 'selected-ru.png', 'asset-failure-en.png', 'asset-failure-ru.png',
    'visual-review.json', 'build.json', 'prior/LocalePresentation-before-primary-status.mc',
}
BASE = 'openspec/changes/spacefox-watchface/evidence/first-install-incident/'


def validate(root, catalog):
    from tools.native_device_requalification import validate as prior_validate
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']

    def checked(path, sha256):
        name = Path(path)
        if name.is_absolute() or '..' in name.parts or not (root / name).is_file():
            raise ValueError('invalid first-install proof path: ' + path)
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != sha256:
            raise ValueError('first-install proof input changed: ' + path)
        return root / name

    ref = proof['incidentDeltaProof']
    record = json.loads(checked(ref['path'], ref['sha256']).read_text())
    if record['scope'] != 'first-install-scene-en-ru' or record['status'] != 'passed':
        raise ValueError('first-install proof incomplete')
    old = json.loads(checked(**record['priorCatalog']).read_text())
    prior = old['supportPolicy']['softwareQualificationProof']
    if {k: v for k, v in proof.items() if k != 'incidentDeltaProof'} != prior:
        raise ValueError('retained qualification metadata changed')
    comparable = json.loads(json.dumps(catalog))
    comparable['supportPolicy']['softwareQualificationProof'] = prior
    if comparable != old:
        raise ValueError('catalog outside incident proof changed')
    if set(record['sources']) != SOURCES:
        raise ValueError('first-install source closure differs')
    for name, digest in record['sources'].items():
        checked(name, digest)
    if set(record['evidence']) != {BASE + name for name in EVIDENCE}:
        raise ValueError('first-install evidence closure differs')
    for name, digest in record['evidence'].items():
        checked(name, digest)
    build = json.loads((root / BASE / 'build.json').read_text())
    if build['profile'] != 'fr165m' or build['sdk'] != '9.3.0' or build['status'] != 'compiled':
        raise ValueError('first-install SDK build not observed')
    baseline_path = BASE + 'prior/LocalePresentation-before-primary-status.mc'
    baseline = (root / baseline_path).read_text()
    for name, digest in build['nativeSources'].items():
        if name == 'watchface/source/LocalePresentation.mc':
            if hashlib.sha256(baseline.encode()).hexdigest() != digest:
                raise ValueError('original compiled locale source changed')
        else:
            checked(name, digest)
    # The new primary-language status labels are the only delta from the
    # observed EN/RU source; remove those exact branches before comparison.
    current = (root / 'watchface/source/LocalePresentation.mc').read_text()
    normalized = re.sub(r'        if\(locale\.equals\("(?:de|fr|es)"\)\)\{\n.*?\n        \}\n', '', current, flags=re.S)
    normalized = re.sub(r' if\(locale\.equals\("(?:de|fr|es)"\)\)\{return "[^"\n]*";\}', '', normalized)
    normalized = re.sub(r' if\(locale\.equals\("(?:de|fr|es)"\)\)\{return "[^"\n]*"\+suffix;\}', '', normalized)
    normalized = normalized.replace('if(stage.equals("incomplete")){if(locale.equals("ru")){return "Загрузка прервана";} return "Artwork interrupted";}', 'if(stage.equals("incomplete")){return locale.equals("ru")?"Загрузка прервана":"Artwork interrupted";}')
    normalized = normalized.replace('if(locale.equals("ru")){return "Изображение: "+suffix;} return "Artwork: "+suffix;', 'return (locale.equals("ru")?"Изображение: ":"Artwork: ")+suffix;')
    if normalized != baseline:
        raise ValueError('unreviewed change outside primary status labels')
    for lang in ('de', 'fr', 'es'):
        if current.count('locale.equals("' + lang + '")') < 3:
            raise ValueError('missing primary status translation: ' + lang)

    # Normal/offline observations predate the short asset-only error label.
    # Verify the precise conditional delta and retain the earlier build hashes.
    for name, item in build['previousVisualSources'].items():
        old_source = checked(item['path'], item['sha256']).read_text()
        if item['sha256'] != build['observedNativeSources'][name]:
            raise ValueError('earlier observed source changed: ' + name)
        current = baseline if name.endswith('LocalePresentation.mc') else (root / name).read_text()
        if name.endswith('SceneRenderer.mc'):
            expected = old_source.replace('presentation.syncStatus(syncStatus)+" · "+syncDetail', 'presentation.assetStatus(syncStatus,syncDetail)')
        elif name.endswith('LocalePresentation.mc'):
            expected = old_source.replace('    function mission(value as String) as String {', item['addition'] + '    function mission(value as String) as String {')
        else:
            raise ValueError('unexpected visual source delta')
        if expected != current:
            raise ValueError('unreviewed post-observation visual delta: ' + name)
    log = (root / BASE / 'unit.log').read_text()
    if parse_output(log, 1, ('firstInstallDefaultsAndRetry',))['status'] != 'passed':
        raise ValueError('native first-install unit did not pass')
    runtime = gzip.decompress((root / BASE / 'isolate.log.gz').read_bytes()).decode()
    for token in ('INCIDENT_SCHEDULE', 'NATIVE_RESPONSE feed code=200',
                  'wire3/catalogs/', 'NATIVE_SCHEDULE', 'sfr-full-scene-active'):
        if token not in runtime:
            raise ValueError('missing actual SDK observation: ' + token)
    review = json.loads((root / BASE / 'visual-review.json').read_text())
    if (review.get('scope') != 'first-install-scene' or
            set(review.get('observed', {})) != {'offline-en', 'offline-ru', 'selected-en', 'selected-ru', 'asset-failure-en', 'asset-failure-ru'} or
            not all(isinstance(v, str) and len(v) >= 30 for v in review['observed'].values())):
        raise ValueError('EN/RU visual review incomplete')
    for name in ('offline-en.png', 'offline-ru.png', 'selected-en.png', 'selected-ru.png', 'asset-failure-en.png', 'asset-failure-ru.png'):
        png = (root / BASE / name).read_bytes()
        if png[:8] != b'\x89PNG\r\n\x1a\n' or png[16:24] != (390).to_bytes(4, 'big') * 2:
            raise ValueError('invalid native screenshot: ' + name)
    with tempfile.TemporaryDirectory(prefix='spacefox-incident-prior-') as temporary:
        target = Path(temporary)
        for folder in ('watchface', 'locales', 'tools'):
            shutil.copytree(root / folder, target / folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for folder in ('openspec', 'corpus', 'tests', 'assets', 'catalog', 'schemas'):
            (target / folder).symlink_to(root / folder, target_is_directory=True)
        for name, item in record['priorSnapshots'].items():
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            saved = checked(item['path'], item['sha256'])
            if str(saved).endswith('.gz'):
                destination.write_bytes(gzip.decompress(saved.read_bytes()))
            else:
                shutil.copyfile(saved, destination)
        for name in ('watchface/resource-inputs/art-unknown.svg',
                     'watchface/resources/drawables/art_unknown.png'):
            (target / name).unlink()
        shutil.rmtree(target / 'watchface/incident-tests')
        if prior_validate(target, old) != old['supportPolicy']['softwareQualifiedLocales']:
            raise ValueError('retained device qualification failed')
    return catalog['supportPolicy']['softwareQualifiedLocales']
