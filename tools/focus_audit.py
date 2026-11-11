"""MIT. Audit bounded, actual browser evidence; no native/human claims."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / 'openspec/changes/enlarge-relay-fields/evidence/browser.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def overlap(a, b, gap=4):
    return (a['x'] < b['x'] + b['w'] + gap and b['x'] < a['x'] + a['w'] + gap
            and a['y'] < b['y'] + b['h'] + gap and b['y'] < a['y'] + a['h'] + gap)


def layout(row):
    o, s = row['observation'], row['fixture']
    require(not o['semanticErrors'] and not o['geometryErrors'] and not row['extraErrors'], 'reported layout error')
    expected = {'time': s['clock'], 'rocket': s['fixture']['rocket']['displayLabel'],
                'operator': s['fixture']['operator']['displayLabel'], 'purpose': s['fixture']['purpose']['displayLabel'],
                'site': s['fixture']['site']['displayLabel'], 'countdown': s['countdown']['displayLabel']}
    expected.update({f'field{i}': f['displayLabel'] for i, f in enumerate(s['fields'])})
    texts = {t['role']: t for t in o['text']}
    require(len(texts) == 10 and set(texts) == set(expected), 'missing or duplicate text')
    for role, value in expected.items():
        t = texts[role]
        require(t['value'] == value, 'changed value: ' + role)
        require(t['contrast'] >= (3 if role == 'time' else 4.5), 'low contrast: ' + role)
    require(abs(o['clockInk'] - 58.5) < .1, 'clock changed')
    require(all(texts[f'field{i}']['fontSize'] >= 32 for i in range(4)), 'fitness too small')
    require(row['fields'] == [{'slot': i, 'role': f['role'], 'value': f['displayLabel']}
                             for i, f in enumerate(s['fields'])], 'slot identity changed')
    # An independent numeric geometry check, not only the renderer's error list.
    boxes = o['boxes'] + [dict(row['battery']['box'], role='device-battery')]
    for b in boxes:
        require(all(math.hypot(x - 195, y - 195) <= 191 for x in (b['x'], b['x'] + b['w'])
                    for y in (b['y'], b['y'] + b['h'])), 'outside circle')
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            require(not overlap(a, b, 0 if a['role'] == b['role'] else 4), 'foreground collision')
    g = row['timeGrouping']
    require(g['countTop'] - g['clockBottom'] >= 4 and g['fieldsTop'] - g['countBottom'] >= 4,
            'time/countdown/fields order')
    require(row['battery']['display'] == ('—' if s['deviceBattery'] is None else str(s['deviceBattery']) + '%'),
            'battery fabricated')
    return True


def geography(row):
    o, s, g = row['observation'], row['fixture'], row['geography']
    point = s['fixture']['point']
    require(row['status'] == {k: s['flags'][k] for k in ('rescheduled', 'stale')}, 'wrong status flags')
    require(g['source'] == point, 'source point changed')
    if point is None:
        require(g['markerCount'] == 0 and o['marker'] is None and g['actual'] is None, 'invented point')
    else:
        require(g['markerCount'] == 1 and g['visible'] and g['markerUnfaded'], 'hidden/faded marker')
        m = o['marker']
        require(m and m['identity'] and m['sourcePoint'] == point and m['inside'] and m['gap'] >= 4,
                'marker identity or clearance')
        require(g['actual'] is not None and math.dist(g['actual'], g['projected']) < .01,
                'marker displaced from projection')
    return True


def load_bound():
    data = json.loads(EVIDENCE.read_text())
    for path, digest in data['sourceSHA256'].items():
        require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, 'source drift: ' + path)
    scenes = [*json.loads((ROOT / 'prototype/composition/scenes.json').read_text()),
              *json.loads((ROOT / 'prototype/composition/additional-scenes.json').read_text())]
    require(data['sourceScenes'] == scenes, 'source scenes drift')
    rows = data['rows']
    require(len(rows) == 96, 'incomplete observations')
    expected = {(v, s['id'], b, 'source') for v in ('fade', 'window', 'globe')
                for s in scenes for b in ('#000000', '#050a11')}
    expected |= {(v, scenes[0]['id'], '#000000', 'configured-' + r)
                 for v in ('fade', 'window', 'globe') for r in ('stress', 'calories', 'heart', 'steps')}
    require({(r['variant'], r['scene'], r['background'], r['kind']) for r in rows} == expected,
            'missing/duplicate scene combination')
    for row in rows:
        source = next(s for s in scenes if s['id'] == row['scene'])
        device = next((f['value'] for f in source['fields'] if f['role'] == 'battery'), None)
        require(row['fixture']['deviceBattery'] == device, 'battery source mismatch')
        expected_fields = source['fields'].copy()
        if row['kind'].startswith('configured-'):
            role = row['kind'].removeprefix('configured-')
            expected_fields[3] = next((f for f in source['fields'] if f['role'] == role),
                                      {'role': role, 'value': None, 'displayLabel': '—'})
        require(row['fixture']['fields'] == expected_fields, 'configured fixture mismatch')
    return data


if __name__ == '__main__':
    data = load_bound()
    for row in data['rows']:
        layout(row)
        geography(row)
    summary = {'rows': len(data['rows']), 'layout': 'passed', 'geography': 'passed',
               'font_size': 32, 'field_size_gain_percent': (32 / 22.2 - 1) * 100,
               'clock_ink': sorted(set(r['observation']['clockInk'] for r in data['rows'])),
               'minimum_marker_gap': min(r['observation']['marker']['gap'] for r in data['rows'] if r['observation']['marker']),
               'minimum_text_contrast': min(t['contrast'] for r in data['rows'] for t in r['observation']['text']),
               'scope': 'Actual browser diagnostics and self-review; no human/native/independent/power acceptance.'}
    print(json.dumps(summary, indent=2))
