"""MIT. Validate the single authored registry and build deterministic SVG/PNG manifest."""
import argparse
import copy
import hashlib
import json
import re
import shutil
import struct
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / 'assets/rocket-pack'
NS = 'http://www.w3.org/2000/svg'
ET.register_namespace('', NS)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def validate_registry(data, pack=PACK):
    require(data.get('schemaVersion') == 1 and data.get('license') == 'MIT', 'unsupported registry/license')
    require(data.get('creator') and data.get('version'), 'missing creator/version')
    ids, aliases = set(), set()
    allowed = {'svg', 'g', 'path', 'rect', 'circle', 'line', 'polyline', 'polygon', 'title', 'desc'}
    for category in ('models', 'companies', 'countries'):
        require(isinstance(data.get(category), list) and data[category], 'missing asset category')
        for item in data[category]:
            key = item['id']
            require(re.fullmatch(r'[a-z][a-z0-9-]*', key), 'unsafe asset id')
            require(key not in ids, 'duplicate asset id')
            ids.add(key)
            require(item.get('name') and item.get('sources'), 'missing name/provenance')
            require(item.get('license') == 'MIT' and item.get('creator'), 'missing compatible rights')
            path = Path(item['file'])
            require(not path.is_absolute() and '..' not in path.parts and path.suffix == '.svg', 'unsafe SVG reference')
            require((pack / path).is_file(), 'missing SVG file')
            el = ET.parse(pack / path).getroot()
            require(el.tag == '{' + NS + '}svg' and el.get('viewBox'), 'missing SVG viewport')
            for node in el.iter():
                require(node.tag.rsplit('}', 1)[-1] in allowed, 'unsupported SVG element')
                for k, v in node.attrib.items():
                    require(not k.lower().startswith('on') and 'href' not in k and 'url(' not in v
                            and 'javascript:' not in v, 'external/active SVG content')
            w, h = item['exportSize']
            require(isinstance(w, int) and isinstance(h, int) and 1 <= w <= 160 and 1 <= h <= 160,
                    'invalid export bounds')
            if category == 'models':
                require(item.get('kind') in ('specific', 'generic'), 'invalid model kind')
                for alias in item.get('aliases', []):
                    normalized = ' '.join(alias.lower().split())
                    require(normalized and normalized not in aliases, 'ambiguous model alias')
                    aliases.add(normalized)
                for anchor in item['anchors'].values():
                    x, y, aw, ah = anchor
                    bx, by, bw, bh = item['bodyArea']
                    require(aw > 0 and ah > 0 and x >= bx and y >= by
                            and x + aw <= bx + bw and y + ah <= by + bh, 'decoration outside body')
    require(any(m['id'] == 'generic' and m['kind'] == 'generic' for m in data['models']), 'missing generic fallback')
    codes = [code for country in data['countries'] for code in country['codes']]
    require(len(codes) == len(set(codes)), 'duplicate origin code')
    company_ids = {item['companyId'] for item in data['companies']}
    for item in data['models'] + data['companies']:
        if item.get('originCode'):
            require(item['originCode'] in codes and item.get('originSources'), 'unverified origin reference')
    for item in data['models']:
        require(not item.get('companyForAssetSheet') or item['companyForAssetSheet'] in company_ids,
                'unknown asset-sheet company')
    return True


def manifest(data, pack=PACK):
    validate_registry(data, pack)
    receipt = json.loads((pack / 'rendered.json').read_text())
    require(receipt['registrySHA256'] == hashlib.sha256((pack / 'registry.source.json').read_bytes()).hexdigest(),
            'stale raster registry; rebuild with --render')
    require(receipt['builderSHA256'] == hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'stale raster builder; rebuild with --render')
    for group in data['models'], data['companies'], data['countries']:
        for item in group:
            require(receipt['svgInputs'][item['file']] == hashlib.sha256((pack / item['file']).read_bytes()).hexdigest(),
                    'stale SVG/PNG association; rebuild with --render')
    for path, digest in receipt['outputs'].items():
        require(hashlib.sha256((pack / path).read_bytes()).hexdigest() == digest, 'rendered output drift')
    result = copy.deepcopy(data)
    for category in ('models', 'companies', 'countries'):
        for item in result[category]:
            svg_path = pack / item.pop('file')
            item['svg'] = {'path': svg_path.relative_to(pack).as_posix(),
                           'sha256': hashlib.sha256(svg_path.read_bytes()).hexdigest()}
            png_path = pack / 'png' / (item['id'] + '.png')
            raw = png_path.read_bytes()
            require(raw[:8] == b'\x89PNG\r\n\x1a\n', 'invalid PNG')
            w, h = struct.unpack('>II', raw[16:24])
            require([w, h] == item['exportSize'], 'PNG dimensions do not match registry')
            item['png'] = {'path': png_path.relative_to(pack).as_posix(), 'width': w, 'height': h,
                           'sha256': hashlib.sha256(raw).hexdigest()}
            if category == 'models':
                item['decoratedPreview'] = {}
                for suffix in ('svg', 'png'):
                    preview = pack / 'previews' / (item['id'] + '.' + suffix)
                    item['decoratedPreview'][suffix] = {'path': preview.relative_to(pack).as_posix(),
                                                        'sha256': hashlib.sha256(preview.read_bytes()).hexdigest()}
    result['sourceSHA256'] = hashlib.sha256((pack / 'registry.source.json').read_bytes()).hexdigest()
    result['rasterizationSHA256'] = hashlib.sha256((pack / 'rendered.json').read_bytes()).hexdigest()
    return result


def build(render=False, check=False):
    data = json.loads((PACK / 'registry.source.json').read_text())
    validate_registry(data)
    if render:
        renderer = shutil.which('rsvg-convert')
        require(renderer, 'rsvg-convert is required for --render; no automatic installation')
        (PACK / 'png').mkdir(exist_ok=True)
        for category in ('models', 'companies', 'countries'):
            for item in data[category]:
                w, h = item['exportSize']
                outer = ET.Element('{' + NS + '}svg', {'width': str(w), 'height': str(h), 'viewBox': f'0 0 {w} {h}'})
                source = ET.parse(PACK / item['file']).getroot()
                source.set('width', str(w)); source.set('height', str(h))
                outer.append(source)
                subprocess.run([renderer, '-o', str(PACK / 'png' / (item['id'] + '.png'))],
                               input=ET.tostring(outer), check=True, capture_output=True)
        (PACK / 'previews').mkdir(exist_ok=True)
        for model in data['models']:
            art = ET.parse(PACK / model['file']).getroot()
            company = next((c for c in data['companies'] if c['companyId'] == model.get('companyForAssetSheet')), None)
            country = next((c for c in data['countries'] if model.get('originCode') in c['codes']), None)
            for role, item in [('country', country), ('company', company)]:
                if item is not None:
                    mark = ET.parse(PACK / item['file']).getroot()
                    x, y, w, h = model['anchors'][role]
                    for k, v in {'x': x, 'y': y, 'width': w, 'height': h}.items():
                        mark.set(k, str(v))
                    mark.set('data-decoration', role)
                    mark.set('data-asset-id', item['id'])
                    art.append(mark)
            (PACK / 'previews' / (model['id'] + '.svg')).write_bytes(ET.tostring(art))
            w, h = model['exportSize']
            outer = ET.Element('{' + NS + '}svg', {'width': str(w), 'height': str(h)})
            art.set('width', str(w)); art.set('height', str(h)); outer.append(art)
            subprocess.run([renderer, '-o', str(PACK / 'previews' / (model['id'] + '.png'))],
                           input=ET.tostring(outer), check=True, capture_output=True)
        entries = [item for category in ('models', 'companies', 'countries') for item in data[category]]
        outputs = [PACK / 'png' / (item['id'] + '.png') for item in entries]
        outputs += [PACK / 'previews' / (item['id'] + '.' + ext) for item in data['models'] for ext in ('svg', 'png')]
        receipt = {'renderer': subprocess.check_output([renderer, '--version'], text=True).strip(),
                   'builderSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   'registrySHA256': hashlib.sha256((PACK / 'registry.source.json').read_bytes()).hexdigest(),
                   'svgInputs': {item['file']: hashlib.sha256((PACK / item['file']).read_bytes()).hexdigest() for item in entries},
                   'outputs': {file.relative_to(PACK).as_posix(): hashlib.sha256(file.read_bytes()).hexdigest() for file in outputs}}
        (PACK / 'rendered.json').write_text(json.dumps(receipt, indent=2) + '\n')
    value = json.dumps(manifest(data), ensure_ascii=False, indent=2) + '\n'
    target = PACK / 'catalog.json'
    if check:
        require(target.read_text() == value, 'generated manifest drift')
    else:
        target.write_text(value)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    build(args.render, args.check)
