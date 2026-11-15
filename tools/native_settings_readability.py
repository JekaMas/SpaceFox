"""Qualify the focused 0.1.13 settings-text repair without rewriting prior proofs."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def validate(root, catalog):
    from tools.native_display03_probe import inputs
    from tools.generate_native_version import validate as validate_version
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    ref = proof['settingsReadabilityProof']
    def read(item):
        p = Path(item['path'])
        if p.is_absolute() or '..' in p.parts:
            raise ValueError('invalid settings proof path')
        data = (root / p).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('settings proof changed: ' + str(p))
        return data
    record = json.loads(read(ref))
    # Keep original glyph and SDK observations independently tamper-evident,
    # including when a caller injects an in-process read fault.
    base = root/'openspec/changes/spacefox-watchface/evidence/release-update-native'
    for name, expected, message in (('menu-warning-glyphs.json','6468fa659cc0ad18b2fdb99375ea7ec4ffa214b619f927a752a4dfafaca306a8','rejection menu glyph observation changed'),('run.log','10be30feb2c55fabe58fffc5d6f87f6bda27bffa7e0f363315e5851ae160a2f0','rejection menu observation changed')):
        if hashlib.sha256((base/name).read_bytes()).hexdigest() != expected:
            raise ValueError(message)
    prior = json.loads(read(record['priorCatalog']))
    oldproof = prior['supportPolicy']['softwareQualificationProof']
    if {k:v for k,v in proof.items() if k != 'settingsReadabilityProof'} != oldproof:
        raise ValueError('prior language proof changed')
    current = json.loads(json.dumps(catalog)); current['supportPolicy']['softwareQualificationProof'] = oldproof
    if current != prior:
        raise ValueError('unrelated language catalog changed')
    if record['scope'] != 'settings-readability-0.1.13' or record['status'] != 'passed':
        raise ValueError('settings readability qualification incomplete')
    oldrecord = json.loads(read(oldproof['integration13DeltaProof']))
    if record['nativeInputs'] != inputs(root):
        raise ValueError('settings readability native closure changed')
    before, after = oldrecord['nativeInputs'], record['nativeInputs']
    changed = {k for k in before.keys() | after.keys() if before.get(k) != after.get(k)}
    if changed != {'watchface/source/SettingsMenu.mc','watchface/source/SettingsMenuText.mc','watchface/source/generated/NativeVersion.mc'}:
        raise ValueError('unexpected settings delta: ' + repr(sorted(changed)))
    for name, item in record['priorSnapshots'].items():
        if hashlib.sha256(read(item)).hexdigest() != before[name]:
            raise ValueError('prior settings input mismatch: ' + name)
    for name, item in record['priorSupport'].items():
        if hashlib.sha256(read(item)).hexdigest() != oldrecord['supportInputs'][name]:
            raise ValueError('prior support input mismatch: ' + name)
    oldmenu = read(record['priorSnapshots']['watchface/source/SettingsMenu.mc'])
    newmenu = oldmenu.replace(b'"SpaceFox "+NativeVersion.BUILD+" "+NativeVersion.ID', b'"SpaceFox "+NativeVersion.BUILD')
    if oldmenu == newmenu or (root/'watchface/source/SettingsMenu.mc').read_bytes() != newmenu:
        raise ValueError('settings menu changed beyond readable title')
    oldtext = read(record['priorSnapshots']['watchface/source/SettingsMenuText.mc']).decode()
    replacements = {
        '["Данные отклонены", "Проверьте URL или обновите SpaceFox"]':'["Ошибка данных", "URL / обновить"]',
        '["Daten abgelehnt", "URL prüfen oder SpaceFox aktualisieren"]':'["Daten abgelehnt", "URL / App-Update"]',
        '["Données refusées", "Vérifiez l’URL ou mettez SpaceFox à jour"]':'["Données refusées", "URL / mise à jour"]',
        '["Datos rechazados", "Compruebe la URL o actualice SpaceFox"]':'["Datos rechazados", "URL / actualizar"]',
        '["Feed rejected", "Check URL or update SpaceFox"]':'["Feed rejected", "Check URL / update"]',
    }
    for a,b in replacements.items():
        if oldtext.count(a) != 1: raise ValueError('prior warning text changed')
        oldtext = oldtext.replace(a,b)
    if (root/'watchface/source/SettingsMenuText.mc').read_text() != oldtext:
        raise ValueError('settings text changed beyond readable warnings')
    validate_version(root)
    glyph = json.loads(read(record['glyphs']))
    if glyph['font_sha256'] != '31d218ca177e4c2191134f9c14fb43027f8a38622476db14038fd8ff186f875e':
        raise ValueError('settings font differs')
    labels = [x for x in re.findall(r'"([^\"]*)"', oldtext.split('function values')[0]) if x not in ('ru','de','fr','es')]
    points = sorted({ord(c) for text in labels for c in text}); coverage = set()
    for part in glyph['fontconfig_charset'].split():
        a,*b=part.split('-'); lo=int(a,16); hi=int(b[0],16) if b else lo; coverage.update(range(lo,hi+1))
    if glyph['labels'] != labels or glyph['codepoints'] != points or glyph['missing'] or not set(points) <= coverage:
        raise ValueError('settings warning glyph coverage incomplete')
    log = read(record['nativeLog']).decode()
    if parse_output(log, record['rawExit'], ('peerSettingsFiveLocales',))['status'] != 'passed':
        raise ValueError('settings SDK table incomplete')
    for i in range(5):
        if 'WARNING locale='+str(i)+' title='+labels[(i*2 if i else 8)] not in log:
            # Source order is RU, DE, FR, ES, default EN.
            expected = [labels[8],labels[0],labels[2],labels[4],labels[6]][i]
            if 'WARNING locale='+str(i)+' title='+expected not in log:
                raise ValueError('settings SDK locale missing: '+str(i))
    read(record['nativeTest'])
    if b'BUILD SUCCESSFUL' not in read(record['hostCompile']) or b'BUILD SUCCESSFUL' not in read(record['testCompile']):
        raise ValueError('settings SDK compile incomplete')
    if not re.fullmatch(r'[0-9a-f]{64}',record['testProgramSha256']) or not re.fullmatch(r'[0-9a-f]{64}',record['hostProgramSha256']):
        raise ValueError('settings SDK program identity missing')
    for item in record['screenshots'].values(): read(item)
    # Validate the prior proof against its exact prior native owners and catalog.
    with tempfile.TemporaryDirectory(prefix='spacefox-settings-prior-') as tmp:
        target=Path(tmp)
        for folder in ('watchface','locales','tools','tests'):
            shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for folder in ('openspec','corpus','assets','catalog','schemas'):
            (target/folder).symlink_to(root/folder,target_is_directory=True)
        for name,item in record['priorSnapshots'].items():
            path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(read(item))
        for name,item in record['priorSupport'].items():
            path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(read(item))
        (target/'locales/catalog.json').write_bytes(read(record['priorCatalog']))
        code=('import json; from pathlib import Path; from tools.native_integration13_requalification import validate; '
              'p=Path.cwd(); c=json.loads((p/"locales/catalog.json").read_text()); '
              'assert validate(p,c)==c["supportPolicy"]["softwareQualifiedLocales"]')
        result=subprocess.run([sys.executable,'-B','-c',code],cwd=target,env={'PATH':str(Path(sys.executable).parent)+':/usr/bin:/bin','PYTHONPATH':str(target),'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=180)
        if result.returncode: raise ValueError('prior integration reconstruction failed: '+result.stderr[-3000:])
    return catalog['supportPolicy']['softwareQualifiedLocales']
