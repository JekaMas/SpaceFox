"""Authenticate the prior locale proof and a bounded compatibility delta.

The old proof runs against reconstructed original source; its receipts are not
repinned. The current delta has its own source and simulator/compiler evidence.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(root, catalog):
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    ref = proof['devices020Proof']
    def checked(path, expected):
        path = Path(path)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('invalid devices020 proof path')
        actual = (root/path).resolve()
        if not actual.is_relative_to(root) or not actual.is_file() or sha(actual) != expected:
            raise ValueError('devices020 proof input changed: '+str(path))
        return actual
    record = json.loads(checked(ref['path'], ref['sha256']).read_text())
    if record['scope'] != 'devices020-bounded-compatibility':
        raise ValueError('wrong devices020 scope')
    prior_dir = Path(record['priorDir'])
    prior_catalog = json.loads(checked(str(prior_dir/'locales/catalog.json'), record['prior']['locales/catalog.json']).read_text())
    oldproof = prior_catalog['supportPolicy']['softwareQualificationProof']
    current = json.loads(json.dumps(catalog))
    current['supportPolicy']['softwareQualificationProof'].pop('devices020Proof')
    if current != prior_catalog or any(proof.get(k) != v for k,v in oldproof.items()):
        raise ValueError('locale policy changed outside compatibility proof')
    for name, digest in record['prior'].items():
        checked(str(prior_dir/name),digest)
    for name,digest in record['current'].items():
        checked(name,digest)
    native_files=[p for p in (root/'watchface/source').rglob('*.mc') if p.is_file()]
    native_files += [p for p in (root/'watchface/resources').rglob('*') if p.is_file()]
    native_files += [p for d in (root/'watchface').glob('resources-*') for p in d.rglob('*') if p.is_file()]
    native_files += [root/'watchface/manifest.xml',root/'watchface/fields018-tests/Fields018Tests.mc',root/'tools/fields018_native_probe.py']
    if record['nativeInputs'] != {str(p.relative_to(root)):sha(p) for p in sorted(native_files)}:
        raise ValueError('devices020 native source closure changed')
    files = {name:checked(item['path'],item['sha256']) for name,item in record['evidence'].items()}
    font = json.loads(files['condensedFonts'].read_text())
    if font['status'] != 'passed' or {x['locale'] for x in font['rows']} != {'en','ru','de','fr','es'} or any(x['missingCodepoints'] or x['notdef'] for x in font['rows']):
        raise ValueError('condensed font evidence failed')
    finite=json.loads(files['condensedFinite'].read_text())
    corpus=root/finite['corpusPath']
    if (finite['status']!='passed' or finite['missing'] or finite['notdefIndices'] or
        finite['corpusPath']!=oldproof['corpusPath'] or sha(corpus)!=oldproof['corpusSha256'] or
        finite['corpusSha256']!=oldproof['corpusSha256'] or finite['fontSha256']!=font['fontSha256'] or
        finite['shapedStringCount']<1):
        raise ValueError('condensed finite-name coverage failed')
    lock = json.loads((root/'watchface/toolchain-lock.json').read_text())
    compiled = json.loads(files['compileResults'].read_text())
    native_now = {str(p.relative_to(root)): sha(p) for p in (root/'watchface').rglob('*') if p.is_file()}
    if (compiled['sourceHashes'] != native_now or not compiled['inputsUnchanged'] or compiled['flags'] != ['-l','3','-O','2','-w','-r'] or
        [x['device'] for x in compiled['results']] != list(lock['profiles']) or
        any(x['exit'] != 0 or not x['programSha256'] for x in compiled['results'])):
        raise ValueError('profile compiler evidence failed')
    exported = json.loads(files['exportReceipt'].read_text())
    if exported['exit'] != 0 or not exported['inputsUnchanged'] or exported['inputs'] != native_now or not exported['sha256']:
        raise ValueError('IQ export evidence failed')
    required = {'approachEn','approachEnLow','approachRu','approachRuLow','venux1En','venux1EnLow','venux1Ru','venux1RuLow','smallEn','smallEnLow','smallRu','smallRuLow','viewportPixels','exportInspection'}
    if not required.issubset(files):raise ValueError('missing required visual or export evidence')
    pixel=json.loads(files['viewportPixels'].read_text())
    if pixel['status']!='passed' or len(pixel['rows'])!=5:raise ValueError('rectangle red/green pixels differ')
    inspection=json.loads(files['exportInspection'].read_text())
    expected_parts={p['number'] for row in lock['profiles'].values() for p in row['parts']}
    if (inspection['status']!='passed' or inspection['iqSha256']!=exported['sha256'] or not inspection['iq_signature_verified'] or
        not inspection['prg_signature_verified'] or not inspection['prg_public_key_matches'] or
        set(inspection['products'])!=expected_parts or inspection['verified_programs']!=len(lock['profiles'])+len(expected_parts)):
        raise ValueError('IQ inspection failed')
    names=('devices020ViewportAndModes','devices020PrimaryFonts')
    family=json.loads(files['familyRun'].read_text())
    expected_family={'fr165','fr965','fr265s','fr265','epix2','approachs7047mm','fenix9pro51mm','venux1'}
    if {row['profile'] for row in family}!=expected_family:raise ValueError('device observer inventory differs')
    for row in family:
        name=row['profile'];actual=parse_output(files['native-'+name].read_text(),row['result']['raw_exit_code'],names)
        if actual['status']!='passed':raise ValueError('native device observer failed: '+name)
    if parse_output(files['native-approachs7042mm'].read_text(),1,names)['status']!='passed':
        raise ValueError('condensed 390 observer failed')
    rect=json.loads(files['rectangleRun'].read_text())
    if len(rect)!=1 or rect[0]['profile']!='venux1' or parse_output(files['native-rectangle-final'].read_text(),rect[0]['result']['raw_exit_code'],names)['status']!='passed':
        raise ValueError('final rectangle observer failed')
    for name in ('stockApproach','stockRectangle','stockSmall'):
        row=json.loads(files[name].read_text())
        if row['status']!='passed':raise ValueError('visual/stock evidence failed: '+name)
        if name!='stockApproach' and row['nativeInputs']!=record['nativeInputs']:
            raise ValueError('current stock source differs: '+name)
        for restoration in row.get('restoration',{}).values():
            if not restoration['restored'] or not restoration['ini']:
                raise ValueError('simulator state not restored: '+name)
    approach=json.loads(files['stockApproach'].read_text())
    old_inputs=approach['inputs']; new_inputs=record['nativeInputs']
    differences={name for name in new_inputs if new_inputs[name]!=old_inputs.get(name)}
    expected={'watchface/source/SpaceFoxView.mc','watchface/source/generated/NativeVersion.mc'}
    if set(old_inputs)!=set(new_inputs) or differences!=expected:
        raise ValueError('unreviewed approach stock source delta')
    old_view=files['preMarginView'].read_text();new_view=(root/'watchface/source/SpaceFoxView.mc').read_text()
    clear='if(sceneX!=0||sceneY!=0){dc.setColor(Graphics.COLOR_BLACK,Graphics.COLOR_BLACK);dc.clear();}'
    if new_view.count(clear)!=1 or new_view.replace(clear,'')!=old_view:
        raise ValueError('approach source delta exceeds rectangle margin clear')
    for name,key in [('watchface/source/SpaceFoxView.mc','preMarginView'),('watchface/source/generated/NativeVersion.mc','preMarginVersion')]:
        if sha(files[key])!=old_inputs[name]:raise ValueError('old approach source mismatch')
    # The original validator checks every historical source and evidence hash.
    # Hardlinks avoid copying large immutable inputs; every replacement is
    # unlinked before writing, so this reconstruction never mutates originals.
    with tempfile.TemporaryDirectory(prefix='spacefox-devices020-prior-') as temporary:
        target=Path(temporary)
        for path in root.iterdir():
            if path.is_file(): os.link(path,target/path.name)
        for name in ('tools','watchface','locales','openspec','tests','assets','corpus','catalog','schemas','docs','release','prototype','.github','licenses'):
            source=root/name
            if source.is_dir():
                shutil.copytree(source,target/name,copy_function=os.link,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for name in record['prior']:
            dst=target/name
            dst.parent.mkdir(parents=True,exist_ok=True)
            dst.unlink(missing_ok=True)
            shutil.copyfile(root/prior_dir/name,dst)
        code=('import json;from pathlib import Path;from tools.native_fields018_qualification import validate;'
              'p=Path.cwd();print(json.dumps(validate(p,json.loads((p/"locales/catalog.json").read_text()))))')
        result=subprocess.run([sys.executable,'-c',code],cwd=target,env={**os.environ,'PYTHONPATH':str(target)},capture_output=True,text=True)
        if result.returncode:
            raise ValueError('original fields018 proof failed: '+result.stderr[-3000:])
        qualified=json.loads(result.stdout.strip().splitlines()[-1])
    if qualified != catalog['supportPolicy']['softwareQualifiedLocales']:
        raise ValueError('prior qualified locale set differs')
    return qualified
