"""Qualify the scoped RGB streaming/bundled-outline repair over prior proofs."""
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
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    def read(item):
        path = Path(item['path'])
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('invalid decoder proof path')
        data = (root/path).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('decoder proof changed: '+str(path))
        return data
    record = json.loads(read(proof['decoderStreamProof']))
    prior = json.loads(read(record['priorCatalog']))
    oldproof = prior['supportPolicy']['softwareQualificationProof']
    if {k:v for k,v in proof.items() if k != 'decoderStreamProof'} != oldproof:
        raise ValueError('prior qualification proof changed')
    current = json.loads(json.dumps(catalog)); current['supportPolicy']['softwareQualificationProof'] = oldproof
    if current != prior:
        raise ValueError('unrelated locale catalog changed')
    if record['scope'] != 'rgb-stream-qualified-bundled-outline-0.1.13' or record['status'] != 'passed':
        raise ValueError('decoder qualification incomplete')
    # Preserve the original in-process tamper controls when the predecessor is
    # reconstructed in a subprocess; patched reads must still fail closed.
    base=root/'openspec/changes/spacefox-watchface/evidence/release-update-native'
    for name,expected,message in (('menu-warning-glyphs.json','6468fa659cc0ad18b2fdb99375ea7ec4ffa214b619f927a752a4dfafaca306a8','rejection menu glyph observation changed'),('run.log','10be30feb2c55fabe58fffc5d6f87f6bda27bffa7e0f363315e5851ae160a2f0','rejection menu observation changed')):
        if hashlib.sha256((base/name).read_bytes()).hexdigest()!=expected: raise ValueError(message)
    if record['nativeInputs'] != inputs(root):
        raise ValueError('decoder native closure changed')
    old = json.loads(read(oldproof['settingsReadabilityProof']))['nativeInputs']
    changed = {k for k in old.keys() | record['nativeInputs'].keys() if old.get(k) != record['nativeInputs'].get(k)}
    expected = {'watchface/source/NativeSfr.mc','watchface/source/SpaceFoxView.mc','watchface/source/SceneRenderer.mc','watchface/source/generated/NativeVersion.mc'}
    if changed != expected:
        raise ValueError('unexpected decoder source delta: '+repr(sorted(changed)))
    for name,item in record['priorSnapshots'].items():
        if hashlib.sha256(read(item)).hexdigest() != old[name]:
            raise ValueError('prior native owner mismatch: '+name)
    validate_version(root)
    for item in record['observations'].values(): read(item)
    resources = {name:read(item) for name,item in record['sdkResources'].items()}
    descriptor = json.loads(resources['D03MapDescriptor.json'])
    if descriptor['canvas'] != [390,390] or descriptor['channels'] != 3 or len(descriptor['shards']) != 11:
        raise ValueError('SDK retained map descriptor changed')
    for index,(expected,size) in enumerate(descriptor['shards']):
        data=json.loads(resources['D03MapShard'+str(index)+'.json'])['raw'].encode()
        if len(data)!=size or hashlib.sha256(data).hexdigest()!=expected:
            raise ValueError('SDK retained shard changed: '+str(index))
    bad=json.loads(resources['BadShard.json'])['raw'].encode()
    if hashlib.sha256(bad).hexdigest().encode() not in read(record['observations']['sdk-Probe.mc.txt']):
        raise ValueError('noncanonical SDK fixture not bound')
    log = read(record['sdkLog']).decode()
    if parse_output(log, record['sdkRawExit'], ('peerCurrentMapDecode','peerBundledStreaming'))['status'] != 'passed':
        raise ValueError('streaming SDK cases incomplete')
    for marker in ('CURRENT_MAP checksum=true outline=true complete=true','CURRENT_MAP wrong_pixel_hash_refused=true','STREAM_MATCH bitmap=true outlineDeferred=true','STREAM_NONCANONICAL refused=true'):
        if marker not in log: raise ValueError('streaming observation missing: '+marker)
    observed_view = read(record['observations']['ordinary-SpaceFoxView.mc.txt']).decode()
    observed_view = observed_view.replace('System.println("BUNDLE_MATCH value="+sfrBuild.preferBundled);', '')
    observed_view = observed_view.replace('if(PeerTiming.start>0&&result.mapBitmap!=null&&result.selectionHash.equals(packet.bridge["selection"]["sha256"])){System.println("ORDINARY_COMPLETE elapsedMs="+(System.getTimer()-PeerTiming.start)+" map=true selection=true totalMemory="+System.getSystemStats().totalMemory);PeerTiming.start=0;}', '')
    if observed_view != (root/'watchface/source/SpaceFoxView.mc').read_text():
        raise ValueError('ordinary observer changed production view')
    timed = read(record['ordinaryLog']).decode()
    if 'OPEN_INSTALLED' not in timed or 'push=false' not in timed or 'BUNDLE_MATCH value=true' not in timed or 'ORDINARY_COMPLETE elapsedMs=5703 map=true selection=true totalMemory=126784' not in timed:
        raise ValueError('ordinary full-scene observation missing')
    # Restore the prior source and catalog to validate the actual predecessor
    # proof; this does not relabel any earlier SDK run as a current execution.
    with tempfile.TemporaryDirectory(prefix='spacefox-decoder-prior-') as tmp:
        target=Path(tmp)
        for folder in ('watchface','locales','tools','tests'):
            shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for folder in ('openspec','corpus','assets','catalog','schemas'):
            (target/folder).symlink_to(root/folder,target_is_directory=True)
        for name,item in record['priorSnapshots'].items():
            path=target/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(read(item))
        (target/'locales/catalog.json').write_bytes(read(record['priorCatalog']))
        code=('import json;from pathlib import Path;from tools.native_settings_readability import validate;'
              'p=Path.cwd();c=json.loads((p/"locales/catalog.json").read_text());'
              'assert validate(p,c)==c["supportPolicy"]["softwareQualifiedLocales"]')
        result=subprocess.run([sys.executable,'-B','-c',code],cwd=target,env={'PATH':str(Path(sys.executable).parent)+':/usr/bin:/bin','PYTHONPATH':str(target),'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True,timeout=180)
        if result.returncode: raise ValueError('prior settings reconstruction failed: '+result.stderr[-3000:])
    return catalog['supportPolicy']['softwareQualifiedLocales']
