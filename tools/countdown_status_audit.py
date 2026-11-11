"""MIT. Check compact status using actual browser observations and a literal truth table."""
import hashlib
import json

from tools.focus_audit import ROOT, geography, layout, overlap, require

EVIDENCE = ROOT / 'openspec/changes/enlarge-relay-fields/evidence/countdown-status/browser.json'
BASELINE = ROOT / 'openspec/changes/enlarge-relay-fields/evidence/browser.json'


def load_bound():
    data = json.loads(EVIDENCE.read_text())
    for path, digest in data['sourceSHA256'].items():
        require(hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, 'source drift: ' + path)
    require(len(data['rows']) == 30, 'incomplete status matrix')
    expected = {(v, 'compose-falcon-ru', bg, s, 'truth-table')
                for v in ('fade', 'window', 'globe') for bg in ('#000000', '#050a11')
                for s in ('normal', 'rescheduled', 'stale', 'both')}
    expected |= {('fade', s, bg, 'both', 'long-or-unknown')
                 for s in ('author3-07-ru', 'author3-07-en', 'author3-01-ru')
                 for bg in ('#000000', '#050a11')}
    actual = {(r['variant'], r['scene'], r['background'], r['statusPresentation']['state'], r['kind'])
              for r in data['rows']}
    require(actual == expected, 'missing or duplicate state combination')
    return data, json.loads(BASELINE.read_text())


def check(row, baseline):
    layout(row)
    geography(row)
    p, s, o = row['statusPresentation'], row['fixture'], row['observation']
    truth = {'normal': (False, False), 'rescheduled': (True, False),
             'stale': (False, True), 'both': (True, True)}
    require((s['flags']['rescheduled'], s['flags']['stale']) == truth[p['state']], 'wrong state inputs')
    require(p['badgeCount'] == 0, 'service badge remains')
    require(p['color'] == ('rgb(243, 195, 122)' if s['flags']['rescheduled'] else 'rgb(113, 228, 192)'),
            'wrong countdown color')
    if s['flags']['stale']:
        require(p['borderStyle'] == 'dotted' and p['borderWidth'] == '2px'
                and p['borderColor'] == p['color'] and p['underline'] is not None, 'missing stale underline')
        line = p['underline']
        require(all(not overlap(line, b, 4) for b in o['boxes'] if b['role'] != 'countdown'),
                'underline collides with foreground')
        require(min(b['y'] for b in o['boxes'] if b['role'].startswith('field')) - line['y'] - line['h'] >= 4,
                'underline too close to fields')
    else:
        require(p['borderStyle'] == 'none' and p['underline'] is None, 'false stale underline')
    require(p['clockColor'] == 'rgb(127, 231, 198)', 'current-time color changed')
    require(abs(row['battery']['box']['x'] + row['battery']['box']['w'] / 2 - 195) < .01,
            'battery not centered')
    old = next(r for r in baseline['rows'] if r['scene'] == row['scene'] and r['variant'] == row['variant']
               and r['background'] == row['background'] and r['kind'] == 'source')
    by_role = {t['role']: t for t in old['observation']['text']}
    for t in o['text']:
        require(t['value'] == by_role[t['role']]['value'], 'source string changed')
        if t['role'] != 'countdown':
            require(all(t[k] == by_role[t['role']][k] for k in ('value', 'x', 'y', 'w', 'h', 'font', 'fontSize')),
                    'unchanged foreground moved or changed')
    require(row['geography']['source'] == old['geography']['source'] if 'geography' in old
            else row['geography']['source'] == old['fixture']['fixture']['point'], 'geography changed')
    return True
