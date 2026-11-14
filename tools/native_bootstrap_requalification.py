"""Validate a URL-default-only delta while retaining the original visual proof."""
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import xml.etree.ElementTree as ET


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate(root, catalog):
    from tools.native_site_flag_requalification import validate as prior_validate
    root = Path(root).resolve()
    proof = catalog['supportPolicy']['softwareQualificationProof']
    ref = proof['bootstrapDeltaProof']
    def checked(name, digest):
        p = Path(name)
        if p.is_absolute() or '..' in p.parts or not (root / p).is_file() or sha(root / p) != digest:
            raise ValueError('bootstrap proof input changed: ' + name)
        return root / p
    record = json.loads(checked(ref['path'], ref['sha256']).read_text())
    prior = json.loads(checked(record['priorCatalog']['path'], record['priorCatalog']['sha256']).read_text())
    old = prior['supportPolicy']['softwareQualificationProof']
    if set(proof) != set(old) | {'bootstrapDeltaProof'} or any(proof[k] != old[k] for k in old if k != 'productionSources'):
        raise ValueError('prior qualification metadata changed')
    sources = proof['productionSources']
    changed = {name for name in old['productionSources'] if old['productionSources'][name] != sources.get(name)}
    expected = {'watchface/resources/settings/properties.xml', 'tools/native_language_policy.py'}
    if set(sources) != set(old['productionSources']) or changed != expected:
        raise ValueError('unexpected bootstrap source delta')
    for name, digest in sources.items():
        checked(name, digest)
    previous = checked(record['properties']['path'], record['properties']['sha256'])
    previous_policy = checked(record['policy']['path'], record['policy']['sha256'])
    if sha(previous) != old['productionSources']['watchface/resources/settings/properties.xml'] or sha(previous_policy) != old['productionSources']['tools/native_language_policy.py']:
        raise ValueError('historical bootstrap inputs differ')
    old_policy = previous_policy.read_text()
    needle = " if isinstance(proof,dict) and 'visualDeltaProof' in proof:\n  from tools.native_site_flag_requalification import validate\n  return validate(root,catalog)"
    replacement = " if isinstance(proof,dict) and 'bootstrapDeltaProof' in proof:\n  from tools.native_bootstrap_requalification import validate\n  return validate(root,catalog)\n" + needle
    if old_policy.count(needle) != 1 or (root / 'tools/native_language_policy.py').read_text() != old_policy.replace(needle, replacement):
        raise ValueError('unexpected language policy change')
    old_xml = ET.parse(previous).getroot()
    new_xml = ET.parse(root / 'watchface/resources/settings/properties.xml').getroot()
    old_prop = old_xml.find("property[@id='FeedBaseUrl']")
    new_prop = new_xml.find("property[@id='FeedBaseUrl']")
    if old_prop is None or new_prop is None or (old_prop.text or '') != '' or new_prop.text != 'https://jekamas.github.io/SpaceFox':
        raise ValueError('unexpected URL default')
    new_prop.text = old_prop.text
    if ET.tostring(new_xml) != ET.tostring(old_xml):
        raise ValueError('other settings defaults changed')
    # Revalidate old proof against exact historical inputs, never rewrite its receipts.
    with tempfile.TemporaryDirectory(prefix='spacefox-bootstrap-prior-') as tmp:
        oldroot = Path(tmp)
        for folder in ('watchface', 'locales', 'tools'):
            shutil.copytree(root / folder, oldroot / folder, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for folder in ('openspec', 'corpus', 'tests', 'assets', 'catalog', 'schemas'):
            (oldroot / folder).symlink_to(root / folder, target_is_directory=True)
        shutil.copyfile(previous, oldroot / 'watchface/resources/settings/properties.xml')
        shutil.copyfile(previous_policy, oldroot / 'tools/native_language_policy.py')
        if prior_validate(oldroot, prior) != prior['supportPolicy']['softwareQualifiedLocales']:
            raise ValueError('retained visual qualification failed')
    return catalog['supportPolicy']['softwareQualifiedLocales']
