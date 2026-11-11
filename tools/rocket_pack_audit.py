"""MIT. File integrity, transparent PNG decoding and actual browser rocket-fit audit."""
import binascii
import hashlib
import json
import struct
import zlib
import xml.etree.ElementTree as ET

from tools.build_rocket_pack import PACK, manifest, validate_registry
from tools.focus_audit import ROOT, geography, layout, require

EVIDENCE = ROOT / 'openspec/changes/prepare-model-rocket-assets/evidence/browser.json'


def png_alpha(raw, require_transparency=True):
    require(raw[:8] == b'\x89PNG\r\n\x1a\n', 'PNG signature')
    pos, compressed, dims = 8, b'', None
    while pos < len(raw):
        require(pos + 12 <= len(raw), 'truncated PNG chunk')
        size = struct.unpack('>I', raw[pos:pos + 4])[0]
        kind = raw[pos + 4:pos + 8]
        data = raw[pos + 8:pos + 8 + size]
        require(pos + size + 12 <= len(raw), 'truncated PNG content')
        crc = struct.unpack('>I', raw[pos + 8 + size:pos + 12 + size])[0]
        require(binascii.crc32(kind + data) & 0xffffffff == crc, 'PNG CRC')
        if kind == b'IHDR':
            w, h, depth, color, comp, filt, interlace = struct.unpack('>IIBBBBB', data)
            require(depth == 8 and color == 6 and interlace == 0, 'expected noninterlaced RGBA8')
            dims = w, h
        elif kind == b'IDAT':
            compressed += data
        pos += size + 12
        if kind == b'IEND':
            break
    require(dims and pos == len(raw), 'PNG termination')
    w, h = dims
    require(0 < w <= 160 and 0 < h <= 160, 'PNG bounds')
    pixels = zlib.decompress(compressed)
    require(len(pixels) == (w * 4 + 1) * h, 'PNG scanline length')
    stride, previous, alpha = w * 4, bytearray(w * 4), []
    for y in range(h):
        offset = y * (stride + 1)
        mode, row = pixels[offset], bytearray(pixels[offset + 1:offset + 1 + stride])
        require(mode <= 4, 'PNG filter')
        for i in range(stride):
            a, b, c = row[i - 4] if i >= 4 else 0, previous[i], previous[i - 4] if i >= 4 else 0
            if mode == 1:
                prediction = a
            elif mode == 2:
                prediction = b
            elif mode == 3:
                prediction = (a + b) // 2
            elif mode == 4:
                p = a + b - c
                candidates = (abs(p - a), abs(p - b), abs(p - c))
                prediction = (a, b, c)[candidates.index(min(candidates))]
            else:
                prediction = 0
            row[i] = (row[i] + prediction) & 255
        alpha.extend(row[3::4])
        previous = row
    require(any(a > 0 for a in alpha), 'empty asset')
    require(not require_transparency or any(a == 0 for a in alpha), 'nontransparent model/mark')
    return w, h


def audit_pack():
    source = json.loads((PACK / 'registry.source.json').read_text())
    validate_registry(source)
    c = json.loads((PACK / 'catalog.json').read_text())
    require(c == manifest(source), 'manifest drift')
    for group in ('models', 'companies', 'countries'):
        for item in c[group]:
            require(list(png_alpha((PACK / item['png']['path']).read_bytes(), group != 'countries')) == item['exportSize'], 'PNG size')
            if group == 'models':
                require(list(png_alpha((PACK / item['decoratedPreview']['png']['path']).read_bytes())) == item['exportSize'],
                        'decorated PNG size')
    return c


def load_bound():
    data = json.loads(EVIDENCE.read_text())
    for path, digest in data['sourceSHA256'].items():
        require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, 'browser source drift: ' + path)
    require(len(data['rows']) == 56, 'incomplete observation count')
    scenes = [s['id'] for s in data['sourceScenes']]
    source_scenes = [*json.loads((ROOT / 'prototype/composition/scenes.json').read_text()),
                     *json.loads((ROOT / 'prototype/composition/additional-scenes.json').read_text())]
    require(data['sourceScenes'] == source_scenes and len(scenes) == len(set(scenes)) == 14, 'scene source drift')
    expected = {(v, s, 'rocket') for v in ('medium', 'large', 'oversize') for s in scenes}
    expected |= {('large', s, 'operator') for s in scenes}
    require({(r['variant'], r['scene'], r['originMode']) for r in data['rows']} == expected, 'missing/duplicate observation')
    for row in data['rows']:
        source = next(s for s in source_scenes if s['id'] == row['scene'])
        for key in ('fixture', 'fields', 'clock', 'countdown', 'flags'):
            require(row['fixture'][key] == source[key], 'source fixture changed: ' + key)
        require(row['fixture']['originMode'] == row['originMode'], 'origin input mismatch')
    control = data['retainedControl']
    require(hashlib.sha256((ROOT / control['file']).read_bytes()).hexdigest() == control['sha256'], 'control drift')
    return data


def accept(row):
    layout(row)
    geography(row)
    identity = row['rocket']['identity']
    names = {'Falcon 9': 'falcon-9', 'Falcon 9 Block 5': 'falcon-9', 'Electron': 'electron', 'Ariane 62': 'ariane-62'}
    companies = {'SpaceX': 'company-spacex', 'Rocket Lab': 'company-rocket-lab', 'Arianespace': 'company-arianespace'}
    model = names.get(row['fixture']['fixture']['rocket']['full'], 'generic')
    company = companies.get(row['fixture']['fixture']['operator']['full'])
    origin = ({'falcon-9': 'flag-us', 'electron': 'flag-nz', 'ariane-62': 'flag-europe'}.get(model)
              if row['originMode'] == 'rocket' else
              {'company-spacex': 'flag-us', 'company-rocket-lab': 'flag-us', 'company-arianespace': 'flag-fr'}.get(company))
    require(identity['modelId'] == model and identity['companyId'] == company and identity['countryId'] == origin,
            'wrong visible identity')
    expected = {('company', company)} if company else set()
    if origin:
        expected.add(('country', origin))
    require({(m['role'], m['asset']) for m in row['rocket']['marks']} == expected
            and len(row['rocket']['marks']) == len(expected), 'missing/false body mark')
    art = row['rocket']['box']
    catalog = json.loads((PACK / 'catalog.json').read_text())
    model_entry = next(m for m in catalog['models'] if m['id'] == model)
    svg = ET.parse(PACK / model_entry['svg']['path']).getroot()
    vx, vy, vw, vh = map(float, svg.get('viewBox').split())
    scale = min(art['w'] / vw, art['h'] / vh)
    bx, by, bw, bh = model_entry['bodyArea']
    body = {'x': art['x'] + (art['w'] - vw * scale) / 2 + (bx - vx) * scale,
            'y': art['y'] + (art['h'] - vh * scale) / 2 + (by - vy) * scale,
            'w': bw * scale, 'h': bh * scale}
    for mark in row['rocket']['marks']:
        b = mark['box']
        require(b['x'] >= art['x'] and b['y'] >= art['y'] and b['x'] + b['w'] <= art['x'] + art['w']
                and b['y'] + b['h'] <= art['y'] + art['h'], 'mark outside rocket')
        require(b['x'] >= body['x'] - .05 and b['y'] >= body['y'] - .05
                and b['x'] + b['w'] <= body['x'] + body['w'] + .05
                and b['y'] + b['h'] <= body['y'] + body['h'] + .05, 'mark outside registered body')
    return True
