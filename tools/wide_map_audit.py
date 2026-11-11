"""MIT. Bounded panel-free browser audit; contour color is not a legibility verdict."""
import hashlib
import json
import math
import re

from tools.focus_audit import ROOT, geography as marker_contract, overlap, require

EVIDENCE = ROOT / 'openspec/changes/expand-map-without-clock-panel/evidence/browser.json'


def rgba(value):
    rgb = list(map(float, re.findall(r'[\d.]+', value)))
    require(len(rgb) in (3, 4), 'unknown CSS color')
    return rgb + [1] if len(rgb) == 3 else rgb


def luminance(value):
    def channel(c):
        c /= 255
        return c / 12.92 if c <= .04045 else ((c + .055) / 1.055) ** 2.4
    r, g, b, _ = rgba(value)
    return .2126 * channel(r) + .7152 * channel(g) + .0722 * channel(b)


def expanded_boxes(row):
    styles = {x['role']: x for x in row['outline']['labels']}
    boxes = []
    for box in row['observation']['boxes'] + [dict(row['battery']['box'], role='device-battery')]:
        role = box['role']
        pad = styles[role]['strokeWidth'] / 2 if role in styles else 0 if role == 'rocket-art' else 1
        boxes.append(dict(box, x=box['x'] - pad, y=box['y'] - pad,
                          w=box['w'] + 2 * pad, h=box['h'] + 2 * pad))
    return boxes


def information(row):
    o, s = row['observation'], row['fixture']
    require(not o['semanticErrors'] and not o['geometryErrors'] and not row['extraErrors'], 'reported layout error')
    expected = {'time': s['clock'], 'rocket': s['fixture']['rocket']['displayLabel'],
                'operator': s['fixture']['operator']['displayLabel'], 'purpose': s['fixture']['purpose']['displayLabel'],
                'site': s['fixture']['site']['displayLabel'], 'countdown': s['countdown']['displayLabel']}
    expected.update({f'field{i}': f['displayLabel'] for i, f in enumerate(s['fields'])})
    texts = {t['role']: t for t in o['text']}
    require(len(o['text']) == len(texts) == 10 and set(texts) == set(expected), 'missing or duplicate text')
    for role, value in expected.items():
        require(texts[role]['value'] == value, 'changed value: ' + role)
    require(abs(o['clockInk'] - 58.5) < .1, 'clock changed')
    require(all(texts[f'field{i}']['fontSize'] >= 32 for i in range(4)), 'fitness too small')
    require(row['fields'] == [{'slot': i, 'role': f['role'], 'value': f['displayLabel']}
                             for i, f in enumerate(s['fields'])], 'slot identity changed')
    boxes = expanded_boxes(row)
    for b in boxes:
        require(all(math.hypot(x - 195, y - 195) <= 191 for x in (b['x'], b['x'] + b['w'])
                    for y in (b['y'], b['y'] + b['h'])), 'expanded ink outside circle')
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            require(not overlap(a, b, 0 if a['role'] == b['role'] else 4),
                    'expanded foreground collision: ' + a['role'] + '/' + b['role'])
    g = row['timeGrouping']
    require(g['countTop'] - g['clockBottom'] >= 4 and g['fieldsTop'] - g['countBottom'] >= 4,
            'time/countdown/fields order')
    require(row['battery']['display'] == ('—' if s['deviceBattery'] is None else str(s['deviceBattery']) + '%'),
            'battery fabricated')
    require(row['rocket']['box'] == {'x': 22, 'y': 118, 'w': 54, 'h': 124}, 'rocket geometry changed')
    require(row['statusPresentation']['badgeCount'] == 0, 'status badge returned')
    require(len(row['panels']) >= 10 and all(rgba(p['color'])[3] == 0 for p in row['panels']), 'background panel returned')
    require(not o['map']['opaquePanels'] and row['mapStructure']['backings'] == 0, 'map backing returned')
    return True


def geography(row, exposure_target=False):
    marker_contract(row)
    cfg, m, e = row['config'], row['mapStructure'], row['exposure']
    x, y, w, h = cfg['box']
    require(w >= 195 and h >= 260 and x >= 0 and y >= 0 and x + w <= 390 and y + h <= 390,
            'window too small or outside canvas')
    require(all(abs(e['window'][k] - v) < .01 for k, v in zip(('x', 'y', 'w', 'h'), cfg['box'])), 'window drift')
    if row['fixture']['fixture']['point'] is None:
        require(not m['masks'] and m['paths'] == 0 and e['visibleAreaFraction'] == 0, 'invented map location')
    else:
        mx, my = row['geography']['actual']
        require(min(math.hypot(max(b['x'] - mx, 0, mx - b['x'] - b['w']),
                               max(b['y'] - my, 0, my - b['y'] - b['h'])) - 13
                    for b in expanded_boxes(row)) >= 4, 'marker contour clearance')
        require(len(m['masks']) == 2 and {a['kind'] for a in m['masks']} == {cfg['fade'] if cfg['fade'] == 'radial' else 'horizontal', 'vertical'}, 'wrong fade masks')
        require(all(a['box'] == [0, 0, w, h] and a['rectangles'] == 1 for a in m['masks']), 'text-sized map hole')
        require(m['paths'] >= 3 and e['visibleAreaFraction'] > 0 and e['visibleReach'] is not None, 'empty map')
        if exposure_target:
            require(e['clock']['potentialFraction'] >= .2, 'clock exposure target missed')
    require(e['thresholds'] == {'reachY': .002, 'clockY': .004}, 'exposure threshold drift')
    return True


def outline(row):
    require(row['outline']['enabled'], 'outline disabled')
    labels = row['outline']['labels']
    require(len(labels) == 10 and len({s['role'] for s in labels}) == 10, 'missing contour observation')
    require({s['role'] for s in labels} == {s['role'] for s in row['observation']['text']}, 'contour role mismatch')
    for s in labels:
        require(float(s['opacity']) == 1 and s['visibility'] == 'visible' and s['display'] != 'none', 'hidden glyph')
        require(rgba(s['color'])[3] == rgba(s['fillColor'])[3] == 1 and s['color'] == s['fillColor'], 'transparent or changed fill')
        expected = 2 if s['role'] in ('time', 'countdown') or s['role'].startswith('field') else 1
        require(s['strokeWidth'] == expected and s['paintOrder'] == 'stroke', 'missing/thick/overpainted contour')
        require(s['strokeColor'] == 'rgb(0, 0, 0)', 'wrong contour color')
        a, b = luminance(s['color']), luminance(s['strokeColor'])
        require((max(a, b) + .05) / (min(a, b) + .05) >= (3 if s['role'] == 'time' else 4.5), 'low nominal fill/contour contrast')
    raw = row['exposure']['rawTextMapContrast']
    require(len(raw) == 10 and {t['role'] for t in raw} == {s['role'] for s in labels}
            and all(1 <= t['contrast'] <= 21 for t in raw), 'missing raw contrast diagnostic')
    require(all('contrast' in t for t in row['observation']['text']), 'retained diagnostic removed')
    return True


def load_bound():
    data = json.loads(EVIDENCE.read_text())
    for path, digest in data['sourceSHA256'].items():
        require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, 'source drift: ' + path)
    scenes = [*json.loads((ROOT / 'prototype/composition/scenes.json').read_text()),
              *json.loads((ROOT / 'prototype/composition/additional-scenes.json').read_text())]
    require(data['sourceScenes'] == scenes, 'source scenes drift')
    config = json.loads((ROOT / 'prototype/wide-map/variants.json').read_text())
    require(data['config'] == config and len(config['variants']) == 6, 'variant drift')
    require(len(data['rows']) == 84 and {(r['variant'], r['scene']) for r in data['rows']} ==
            {(v['id'], s['id']) for v in config['variants'] for s in scenes}, 'incomplete/duplicate observations')
    for row in data['rows']:
        s = next(s for s in scenes if s['id'] == row['scene'])
        for key in ('fixture', 'fields', 'clock', 'countdown', 'flags'):
            require(row['fixture'][key] == s[key], 'fixture changed: ' + key)
        require(row['config'] == next(v for v in config['variants'] if v['id'] == row['variant']), 'row variant drift')
    c = data['retainedControl']
    require(hashlib.sha256((ROOT / c['file']).read_bytes()).hexdigest() == c['sha256'], 'control drift')
    source = json.loads((ROOT / c['file']).read_text())
    require(c['row'] == next(r for r in source['rows'] if r['variant'] == 'large' and r['scene'] == 'compose-falcon-ru' and r['originMode'] == 'rocket'), 'control row drift')
    for row in data['rows']:
        prior = next(r for r in source['rows'] if r['variant'] == 'large' and r['scene'] == row['scene'] and r['originMode'] == 'rocket')
        require(row['rocket']['identity'] == prior['rocket']['identity'], 'rocket identity changed')
    return data


if __name__ == '__main__':
    data = load_bound()
    report = []
    for variant in data['config']['variants']:
        rows = [r for r in data['rows'] if r['variant'] == variant['id']]
        failures = []
        for row in rows:
            for name, check in [('information', information), ('geography', geography), ('outline', outline)]:
                try:
                    check(row)
                except ValueError as exc:
                    failures.append({'scene': row['scene'], 'contract': name, 'error': str(exc)})
        valid = [r for r in rows if r['fixture']['fixture']['point'] is not None]
        report.append({'id': variant['id'], 'window': variant['box'], 'failures': failures,
                       'exposure_target': all(r['exposure']['clock']['potentialFraction'] >= .2 for r in valid),
                       'clock_exposure_min': min(r['exposure']['clock']['potentialFraction'] for r in valid),
                       'clock_exposure_hero': rows[0]['exposure']['clock']['potentialFraction'],
                       'visible_area_hero': rows[0]['exposure']['visibleAreaFraction'],
                       'raw_contrast_min': min(t['contrast'] for r in rows for t in r['exposure']['rawTextMapContrast'])})
    print(json.dumps({'variants': report, 'control_exposure': data['retainedControl']['controlExposure'],
                      'scope': data['scope']}, indent=2))
