"""Validate DISPLAY02 delta without replacing the prior locale evidence."""
import hashlib,json,shutil,tempfile
from pathlib import Path

def validate(root,catalog):
    from tools.native_delivery_requalification import validate as prior_validate
    from tools.generate_native_version import validate as validate_identity
    from tools.run_native_tests import parse_output
    root=Path(root).resolve();proof=catalog['supportPolicy']['softwareQualificationProof']
    def checked(item):
        path=Path(item['path'])
        if path.is_absolute() or '..' in path.parts or not (root/path).is_file():raise ValueError('invalid DISPLAY02 proof input')
        data=(root/path).read_bytes()
        if hashlib.sha256(data).hexdigest()!=item['sha256']:raise ValueError('DISPLAY02 proof input changed: '+str(path))
        return root/path
    record=json.loads(checked(proof['display02DeltaProof']).read_text())
    if record['scope']!='display02-two-mode-current-source' or record['status']!='passed':raise ValueError('DISPLAY02 proof incomplete')
    old=json.loads(checked(record['priorCatalog']).read_text());oldproof=old['supportPolicy']['softwareQualificationProof']
    if {k:v for k,v in proof.items() if k!='display02DeltaProof'}!=oldproof:raise ValueError('prior proof changed')
    comparable=json.loads(json.dumps(catalog));comparable['supportPolicy']['softwareQualificationProof']=oldproof
    if comparable!=old:raise ValueError('locale catalog outside proof changed')
    for name,digest in record['inputs'].items():checked({'path':name,'sha256':digest})
    for item in record['evidence'].values():checked(item)
    validate_identity(root)
    receipt=json.loads(checked(record['evidence']['nativeReceipt']).read_text())
    for name,digest in receipt['inputHashes'].items():
        if record['inputs'].get(name)!=digest:raise ValueError('native receipt source differs: '+name)
    native={str(p.relative_to(root)) for p in (root/'watchface/source').rglob('*.mc')}
    resources={str(p.relative_to(root)) for d in [root/'watchface/resources',*root.glob('watchface/resources-*')] for p in d.rglob('*') if p.is_file()}
    observed=set(receipt['inputHashes'])
    actual={n for n in observed if n.startswith('watchface/source/') or n.startswith('watchface/resources/') or n.startswith('watchface/resources-')}
    if native|resources!=actual:raise ValueError('native source/resource closure differs')
    names=('displayEventSequence','displayRealSiteMarker','displayCapturedZhuqueMarker','displayAssetJobSequence','displayPairedInputs','displayBatchRetry','displayHighBeforeShow')
    log=checked(record['evidence']['nativeLog']).read_text()
    if parse_output(log,receipt['rawExit'],names)['status']!='passed':raise ValueError('DISPLAY02 native tests failed')
    for seed in (73,191,433,719):
        if 'DISPLAY02 seed='+str(seed)+' generated=' not in log:raise ValueError('missing generated seed')
    for value in ('T- 49:02:03','T- 00:00:59','T+ 00:00:00','T+ 00:00:01','T+ 00:15:01'):
        if 'active='+value+' low='+value+' oracle='+value not in log:raise ValueError('missing paired render boundary')
    with tempfile.TemporaryDirectory(prefix='spacefox-display02-prior-') as temporary:
        target=Path(temporary)
        for folder in ('watchface','locales','tools','tests'):shutil.copytree(root/folder,target/folder,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for folder in ('openspec','corpus','assets','catalog','schemas'):(target/folder).symlink_to(root/folder,target_is_directory=True)
        for name,item in record['priorSnapshots'].items():
            dst=target/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(checked(item),dst)
        for name in record['priorAbsent']:
            path=target/name
            if path.is_file():path.unlink()
        (target/'locales/catalog.json').write_bytes(checked(record['priorCatalog']).read_bytes())
        if prior_validate(target,old)!=old['supportPolicy']['softwareQualifiedLocales']:raise ValueError('prior delivery proof failed')
    return catalog['supportPolicy']['softwareQualifiedLocales']
