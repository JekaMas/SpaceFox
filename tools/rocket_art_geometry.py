"""Create bounded MIT schematics from dimensions in the existing asset facts.

No configuration-to-art mapping is maintained here: canonical asset facts own
source dimensions and catalogue bindings. Booster circles are radially arranged;
this side projection intentionally overlaps near/far motors rather than laying
all motors flat beside the core.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def render(facts):
    p = facts['geometryReference']['radialProjection']
    h = float(p['heightMetres']); core = float(p['coreDiameterMetres'])
    fair = float(p['fairingDiameterMetres']); fair_len = float(p['fairingLengthMetres'])
    count = int(p['boosters']); bd = float(p['boosterDiameterMetres']); bl = float(p['boosterLengthMetres'])
    if not (h > 0 and core > 0 and fair > 0 and 0 < fair_len < h and count in (0, 2, 4, 6)
            and bd >= 0 and bl >= 0 and (count == 0 or (bd > 0 and 0 < bl < h))):
        raise ValueError('invalid radial source dimensions')
    scale = 108.0 / h
    cw, fw, bw = core * scale, fair * scale, bd * scale
    if max(cw, fw, cw + 2*bw) > 54:
        raise ValueError('radial projected width exceeds source canvas')
    tower = float(p.get('escapeTowerLengthMetres', 0))
    if tower < 0 or tower + fair_len >= h:
        raise ValueError('invalid escape tower dimensions')
    tip, base = 8.0 + tower * scale, 116.0
    shoulder = tip + fair_len * scale
    left, right = 32-cw/2, 32+cw/2
    fl, fr = 32-fw/2, 32+fw/2
    booster_tip = base - bl * scale
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 128"><title>{facts["name"]}</title>',
             '<desc>Original SpaceFox MIT schematic. Radial boosters overlap in a representative launch projection; dimensions and reference are recorded in source asset facts.</desc>']
    # Far-side and near-side projected boosters are displaced slightly to
    # preserve distinguishable silhouette without falsely widening the stack.
    def booster(side, position):
        edge = left if side < 0 else right
        offset = (0.5 - position*0.42)*bw
        center = edge + side*offset
        a, b = center-bw/2, center+bw/2
        fill = ('#b9cad3', '#dce6ea', '#a4b9c5')[position]
        if p.get('tapered', False):
            # Soyuz boosters flare away from the core towards their bases.
            # A sourced overall base span may exceed core + two diameters.
            spread=float(p.get('maximumProjectedWidthMetres', core+2*bd))*scale/2
            if side<0:a=min(a,32-spread+position*bw*0.25)
            else:b=max(b,32+spread-position*bw*0.25)
            path=f'M{edge:.4f} {booster_tip:.4f}L{a:.4f} {base-5:.4f}V{base:.4f}H{b:.4f}L{b:.4f} {base-10:.4f}Z'
        else:
            cone=min(bw*1.5,bl*scale*0.25)
            path=f'M{a:.4f} {base:.4f}V{booster_tip+cone:.4f}L{center:.4f} {booster_tip:.4f}L{b:.4f} {booster_tip+cone:.4f}V{base:.4f}Z'
        return f'<path data-part="booster" d="{path}" fill="{fill}" stroke="#7894a4" stroke-width="0.30"/>'
    if count:
        parts.extend((booster(-1,0),booster(1,0)))
    parts.append(f'<path data-part="core" d="M{left:.4f} {shoulder:.4f}H{right:.4f}V{base:.4f}H{left:.4f}Z" fill="{p.get("coreColor", "#e4ebee")}" stroke="#829baa" stroke-width="0.35"/>')
    parts.append(f'<path data-part="fairing" d="M{fl:.4f} {shoulder:.4f}V{tip+(shoulder-tip)*0.4:.4f}Q{fl:.4f} {tip+3:.4f} 32 {tip:.4f}Q{fr:.4f} {tip+3:.4f} {fr:.4f} {tip+(shoulder-tip)*0.4:.4f}V{shoulder:.4f}Z" fill="#f2f5f5" stroke="#8da6b5" stroke-width="0.35"/>')
    if tower:
        parts.append(f'<path data-part="escape-tower" d="M31.2 {tip:.4f}V8.8L32 8L32.8 8.8V{tip:.4f}Z" fill="#c5d4dc" stroke="#7894a4" stroke-width="0.25"/>')
    # Near motors are visible in front of the centre core; the total footprint
    # remains the diameter of the core plus one radial motor on each side.
    for k in range(1,count//2):parts.extend((booster(-1,k),booster(1,k)))
    for y in (shoulder+5, tip+108*0.52):
        if y < booster_tip-1:parts.append(f'<path d="M{left:.4f} {y:.4f}H{right:.4f}" fill="none" stroke="#496372" stroke-width="0.5"/>')
    parts.append(f'<path data-part="nozzle" d="M{left+cw*.2:.4f} {base:.4f}L{left+cw*.1:.4f} 120H{right-cw*.1:.4f}L{right-cw*.2:.4f} {base:.4f}Z" fill="#718a9b"/></svg>\n')
    return ''.join(parts)


def sources():
    source=json.loads((ROOT/'catalog/source.json').read_text())
    for entry in source['curations']:
        doc=json.loads((ROOT/entry['path']).read_text())
        for asset in doc['assets']:
            facts=asset['facts']
            if 'radialProjection' in facts.get('geometryReference', {}):
                yield facts


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--write',action='store_true');args=parser.parse_args()
    count=0
    for facts in sources():
        path=ROOT/'assets/global'/facts['file']; data=render(facts)
        if args.write:path.write_text(data)
        elif not path.is_file() or path.read_text()!=data:raise SystemExit('geometry drift: '+str(path))
        count+=1
    print(f'radial geometry assets: {count}')

if __name__=='__main__':main()
