"""Validate the retained DISPLAY02 proof plus the reviewed current native delta.

The historical checker runs on its exact retained inputs, not on relabelled
current bytes. Current controls cover the two changed production owners and
the directed replacement for the retired generated test tail.
"""
import copy
import hashlib
import importlib.util
import json
import shutil
import tempfile
from pathlib import Path


def validate(root, catalog):
    from tools.run_native_tests import parse_output
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    ref = proof.get('currentNativeUiDeltaProof')
    if not isinstance(ref, dict):
        raise ValueError('current native UI proof missing')

    def checked(item):
        path = Path(item['path'])
        if path.is_absolute() or '..' in path.parts or not (root/path).is_file():
            raise ValueError('invalid current native UI proof input')
        data = (root/path).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('DISPLAY02 proof input changed: '+str(path))
        return root/path

    record = json.loads(checked(ref).read_text())
    if record['scope'] != 'display02-current-map-wake-directed' or record['status'] != 'passed':
        raise ValueError('current native UI proof incomplete')
    expected = {'watchface/source/SceneRenderer.mc', 'watchface/source/SpaceFoxView.mc',
                'watchface/display02-tests/Display02Tests.mc', 'tools/native_display02_requalification.py'}
    if set(record['reviewedCurrent']) != expected or set(record['historicalSnapshots']) != expected:
        raise ValueError('current native UI reviewed delta differs')
    for name, digest in record['reviewedCurrent'].items():
        checked({'path': name, 'sha256': digest})
    for item in record['historicalSnapshots'].values():
        checked(item)
    for item in record['evidence'].values():
        checked(item)
    directed = json.loads(checked(record['evidence']['directedReceipt']).read_text())
    names = ('displayEventSequence','displayRealSiteMarker','displayCapturedZhuqueMarker',
             'displayAssetJobSequence','displayPairedInputs','displayBatchRetry','displayHighBeforeShow')
    if directed['status'] != 'passed' or directed['compileExit'] != 0 or parse_output(checked(record['evidence']['directedLog']).read_text(), directed['rawExit'], names)['status'] != 'passed':
        raise ValueError('directed current display tests failed')
    directed_log = checked(record['evidence']['directedLog']).read_text()
    for value in ('T- 49:02:03', 'T- 00:00:59', 'T+ 00:00:00', 'T+ 00:00:01', 'T+ 00:15:01'):
        if 'active='+value+' low='+value+' oracle='+value not in directed_log:
            raise ValueError('current paired countdown boundary missing')
    redraw = json.loads(checked(record['evidence']['redrawReceipt']).read_text())
    if parse_output(checked(record['evidence']['redrawLog']).read_text(), redraw['rawExit'], ('displayDrawDefersResume',))['status'] != 'passed':
        raise ValueError('current redraw test failed')
    native = {str(p.relative_to(root)) for p in (root/"watchface/source").rglob("*.mc")}
    resources = {str(p.relative_to(root)) for d in [root/"watchface/resources", *root.glob("watchface/resources-*")] for p in d.rglob("*") if p.is_file()}
    for receipt in (directed, redraw):
        observed = {n for n in receipt["inputHashes"] if n.startswith(("watchface/source/", "watchface/resources/", "watchface/resources-"))}
        if observed != native | resources:
            raise ValueError("current native UI source closure differs")
        for name, digest in receipt['inputHashes'].items():
            if name.startswith(('watchface/source/', 'watchface/resources/', 'watchface/resources-')):
                checked({'path':name, 'sha256':digest})
    if directed['inputHashes'].get('watchface/display02-tests/Display02Tests.mc') != record['reviewedCurrent']['watchface/display02-tests/Display02Tests.mc']:
        raise ValueError('directed assertions differ')
    for language in ('english', 'russian'):
        build = json.loads(checked(record['evidence'][language+'MapBuild']).read_text())
        if build['exitCode'] != 0 or build['device'] != 'fr165' or build['tests'] or build['productionSourceScope'] != 'all-native':
            raise ValueError('current map build incomplete')
        for name, digest in {**build['productionSources'], **build['productionResources']}.items():
            checked({'path':name, 'sha256':digest})
        if hashlib.sha256(checked(record['evidence'][language+'MapProbe']).read_bytes()).hexdigest() != build['probeSha256']:
            raise ValueError('current map probe differs')
        marker = 'CURRENT_SELECTED_DRAW complete=true' if language == 'english' else 'CURRENT_SELECTED_RU_DRAW complete=true'
        if marker not in checked(record['evidence'][language+'MapLog']).read_text():
            raise ValueError('current map draw marker missing')
    # Restore only the four reviewed historical bytes, and remove only this
    # supplement from the catalog before invoking its original strict checker.
    old_catalog = copy.deepcopy(catalog)
    del old_catalog['supportPolicy']['softwareQualificationProof']['currentNativeUiDeltaProof']
    with tempfile.TemporaryDirectory(prefix='spacefox-display02-current-') as temporary:
        target = Path(temporary)
        for folder in ('watchface','locales','tools','tests'):
            shutil.copytree(root/folder, target/folder, ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
        for folder in ('openspec','corpus','assets','catalog','schemas'):
            (target/folder).symlink_to(root/folder, target_is_directory=True)
        for name, item in record['historicalSnapshots'].items():
            shutil.copyfile(checked(item), target/name)
        (target/'locales/catalog.json').write_text(json.dumps(old_catalog,ensure_ascii=False,indent=2)+'\n')
        module_path = target/'tools/native_display02_requalification.py'
        spec = importlib.util.spec_from_file_location('spacefox_historical_display02',module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.validate(target, old_catalog)
