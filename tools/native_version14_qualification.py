"""Bind version 0.1.14 to retained 0.1.13 software evidence."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def validate(root, catalog):
    from tools.native_display03_probe import inputs
    from tools.generate_native_version import validate as validate_version
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    def read(item):
        path = Path(item['path'])
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('invalid version proof path')
        data = (root/path).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('version proof input changed: '+str(path))
        return data
    record = json.loads(read(proof['version14Proof']))
    prior = json.loads(read(record['priorCatalog']))
    oldproof = prior['supportPolicy']['softwareQualificationProof']
    if {k:v for k,v in proof.items() if k != 'version14Proof'} != oldproof:
        raise ValueError('prior qualification proof changed')
    current = json.loads(json.dumps(catalog)); current['supportPolicy']['softwareQualificationProof'] = oldproof
    if current != prior or record['scope'] != 'version-only-0.1.14':
        raise ValueError('unqualified version catalog change')
    old = json.loads(read(oldproof['decoderStreamProof']))['nativeInputs']
    base=root/'openspec/changes/spacefox-watchface/evidence/release-update-native'
    for name,expected,message in (('menu-warning-glyphs.json','6468fa659cc0ad18b2fdb99375ea7ec4ffa214b619f927a752a4dfafaca306a8','rejection menu glyph observation changed'),('run.log','10be30feb2c55fabe58fffc5d6f87f6bda27bffa7e0f363315e5851ae160a2f0','rejection menu observation changed')):
        if hashlib.sha256((base/name).read_bytes()).hexdigest()!=expected:
            raise ValueError(message)
    if record['nativeInputs'] != inputs(root):
        raise ValueError('version native closure changed')
    changed = {k for k in old.keys() | record['nativeInputs'].keys() if old.get(k) != record['nativeInputs'].get(k)}
    expected = {'watchface/manifest.xml','watchface/source/generated/NativeVersion.mc'}
    if changed != expected:
        raise ValueError('unexpected version delta: '+repr(sorted(changed)))
    for name, item in record['priorSnapshots'].items():
        data = read(item)
        if hashlib.sha256(data).hexdigest() != old[name]:
            raise ValueError('prior version input changed: '+name)
    previous = read(record['priorSnapshots']['watchface/manifest.xml'])
    if previous.count(b'version="0.1.13"') != 1 or previous.replace(b'version="0.1.13"',b'version="0.1.14"') != (root/'watchface/manifest.xml').read_bytes():
        raise ValueError('manifest changed beyond version')
    validate_version(root)
    # Retained Roboto cmap already covers the only new version glyph, 4.
    glyph=json.loads(read(record['glyphs']))
    ranges=glyph['fontconfig_charset'].split()
    if not any(int(x.split('-')[0],16)<=ord('4')<=int(x.split('-')[-1],16) for x in ranges):
        raise ValueError('version glyph not covered')
    metrics=json.loads(read(record['headerMetrics']));read(record['measurementMethod'])
    if metrics['sha256'] != glyph['font_sha256'] or metrics['glyphAdvance']['3'] != metrics['glyphAdvance']['4']:
        raise ValueError('version header glyph advance differs')
    if b'\"SpaceFox \"+NativeVersion.BUILD' not in (root/'watchface/source/SettingsMenu.mc').read_bytes():
        raise ValueError('version header source changed')
    with tempfile.TemporaryDirectory(prefix='spacefox-version14-prior-') as tmp:
        target=Path(tmp)
        for folder in ('watchface','locales','tools','tests'):
            shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for folder in ('openspec','corpus','assets','catalog','schemas'):
            (target/folder).symlink_to(root/folder,target_is_directory=True)
        for group in ('priorSnapshots','priorSupport'):
            for name,item in record[group].items():
                path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(read(item))
        (target/'locales/catalog.json').write_bytes(read(record['priorCatalog']))
        code=('import json;from pathlib import Path;from tools.native_decoder_stream_qualification import validate;'
              'p=Path.cwd();c=json.loads((p/"locales/catalog.json").read_text());'
              'assert validate(p,c)==c["supportPolicy"]["softwareQualifiedLocales"]')
        result=subprocess.run([sys.executable,'-B','-c',code],cwd=target,env={'PATH':str(Path(sys.executable).parent)+':/usr/bin:/bin','PYTHONPATH':str(target),'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=240)
        if result.returncode:
            raise ValueError('prior decoder reconstruction failed: '+result.stderr[-3000:])
    return catalog['supportPolicy']['softwareQualifiedLocales']
