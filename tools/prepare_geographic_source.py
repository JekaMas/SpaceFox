#!/usr/bin/env python3
"""Derive immutable off-watch regional source clips from a pinned local GSHHG archive.

No network request or executable source is admitted. Re-run with a new output
revision after a catalog coordinate addition/correction; never overwrite a source.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.spacefox.catalog import build_catalog, canonical_bytes

ARCHIVE_SHA = '28600e8f7a08645aab43079326df6504212ec5ccb2b4bcf3b5f4f12ed60e82bc'
ARCHIVE_URL = 'https://github.com/GenericMappingTools/gshhg-gmt/releases/download/2.3.7/gshhg-bin-2.3.7.zip'
MEMBER_SHA = '380f585415006f2b648a1a99383f50bf06518728d62991d98d48e7c2de48ec8f'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def clips(blob, centers):
    """Keep exact consecutive vertices; window membership never uses a country/ID.

    A one-segment halo retains crossings of each 4 degree latitude / cos-lat
    longitude window. No vertex is fabricated or translated to agree with a pad.
    """
    offset = 0
    while offset < len(blob):
        header = struct.unpack_from('>11i', blob, offset)
        identity, count, flag = header[:3]
        offset += 44
        raw = memoryview(blob)[offset:offset + count * 8]
        offset += count * 8
        if flag & 255 != 1:
            continue
        points = [((x + 180000000) % 360000000 - 180000000, y)
                  for x, y in struct.iter_unpack('>ii', raw)]
        chunk = []
        start = None
        for number, (a, b) in enumerate(zip(points, points[1:])):
            dx = (b[0] - a[0] + 180000000) % 360000000 - 180000000
            mx, my = (a[0] + dx / 2) / 1e6, (a[1] + b[1]) / 2e6
            # Midpoint plus half-segment span is a conservative crossing test.
            near = any(abs(my-y) <= 2 + abs(b[1]-a[1])/2e6 and
                       abs((mx-x+180) % 360-180) * max(.05, math.cos(math.radians(y)))
                       <= 2 + abs(dx)/2e6 for x, y in centers)
            if near:
                if not chunk:
                    chunk, start = [list(a)], number
                chunk.append(list(b))
            elif chunk:
                yield {'feature': identity, 'startVertex': start, 'points': chunk}
                chunk = []
        if chunk:
            yield {'feature': identity, 'startVertex': start, 'points': chunk}


def prepare(archive, source, output, docs):
    data = archive.read_bytes()
    if sha(data) != ARCHIVE_SHA:
        raise ValueError('pinned original GSHHG archive digest mismatch')
    catalog = build_catalog(ROOT, source)
    centers = sorted({(float(s['position']['longitude']), float(s['position']['latitude']))
                      for s in catalog['dictionaries']['sites'].values() if s['position'] is not None})
    with zipfile.ZipFile(archive) as z:
        blob = z.read('gshhs_h.b')
        if sha(blob) != MEMBER_SHA:
            raise ValueError('pinned original GSHHG member digest mismatch')
        records = list(clips(blob, centers))
        notices = {n: z.read(n) for n in ('LICENSE.TXT', 'README.TXT', 'COPYING.LESSERv3')}
    notices['COPYINGv3'] = (docs / 'COPYINGv3').read_bytes()
    if sha(notices['COPYINGv3']) != '3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986':
        raise ValueError('GPL3 text digest mismatch')
    output.mkdir(parents=True, exist_ok=False)
    pins = []
    groups=[]; group=[]; vertices=0
    for record in records:
        if group and vertices + len(record['points']) > 12000:
            groups.append(group);group=[];vertices=0
        group.append(record);vertices+=len(record['points'])
    if group:groups.append(group)
    for number, group in enumerate(groups):
        raw = canonical_bytes({'format': 'gshhg-microdegree-clips-v1', 'records': group})
        encoded = gzip.compress(raw, mtime=0)
        name = 'clips-' + str(number).zfill(3) + '.json.gz'
        (output / name).write_bytes(encoded)
        pins.append({'path': str((output / name).relative_to(ROOT)), 'sha256': sha(encoded),
                     'decodedSha256': sha(raw), 'decodedBytes': len(raw)})
    rights = []
    for name, raw in notices.items():
        (output / name).write_bytes(raw)
        rights.append({'path': str((output / name).relative_to(ROOT)), 'sha256': sha(raw), 'bytes': len(raw)})
    index = {'schemaVersion': 2, 'format': 'offwatch-regional-context-v1',
             'license': 'LGPL-3.0-or-later',
             'sources': [ARCHIVE_URL, 'https://github.com/GenericMappingTools/gshhg-gmt',
                         'https://www.ngdc.noaa.gov/mgg/shorelines/shorelines.html'],
             'credit': 'GSHHG by Paul Wessel and Walter H. F. Smith; UH and NOAA. Modified regional source clips; no endorsement.',
             'sourceDate': '2017-06-15', 'derivedOn': '2026-11-12',
             'originalArchiveSha256': ARCHIVE_SHA, 'originalMember': 'gshhs_h.b', 'originalMemberSha256': MEMBER_SHA,
             'baseWorld': catalog['source']['geography'], 'notices': rights, 'clips': pins,
             'coverage': {'coordinateWindows': [[str(y), str(x)] for x,y in centers],
                          'halfLatitudeDegrees': 2, 'halfLongitudeCosLatitudeDegrees': 2,
                          'catalogSourcePositionSha256': sha(canonical_bytes({i:s['position'] for i,s in catalog['dictionaries']['sites'].items()})),
                          'qualification': 'finite-source-coordinate-windows-not-global-survey'},
             'derivation': 'Consecutive source vertices in microdegrees, level1 high-resolution land/ocean only. Generic coordinate-window segment intersection; source IDs/start-vertex preserved. No smoothing or pad substitution.',
             'sourceRecords': len(records), 'sourceVertices': sum(len(r['points']) for r in records)}
    (output / 'source.json').write_bytes(canonical_bytes(index))
    return index


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--catalog-source', type=Path, default=ROOT/'catalog/source.json')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--docs', type=Path, required=True)
    args = parser.parse_args()
    index = prepare(args.archive, args.catalog_source, args.output.resolve(), args.docs)
    print(json.dumps({k:index[k] for k in ('sourceRecords', 'sourceVertices', 'sourceDate', 'license')}))


if __name__ == '__main__':
    main()
