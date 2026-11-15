"""Qualify a source-bound finite native map capture set; never launch the SDK."""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json
from tools.spacefox.native_profile import decode_raster, png_pixels

# Retained immutable observations are checked once per qualification, shared by
# the 12 cases through evidence_data(). Code and these pins are Git-bound.
PROOF_INPUTS_SHA256 = '49d9995d2692da01b8b33f29e673c0c8c0d62f08baf293c0d434837753c9e312'
HOST_SOURCE_SHA256 = 'fe0eacfaa5cd8c5bc22670f9adb4f0de179964386d65eb2aed86c9bc7621e922'


def verify_file_digests(root, files, boundary):
    for name, digest in files.items():
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts, boundary + ' input path')
        target = Path(root) / path
        require(target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == digest,
                boundary + ' input changed: ' + name)


def verify_evidence_inputs(root, evidence):
    # The manifest pin also protects the all-black index-zero barcode: zero
    # alone cannot distinguish absent diagnostic squares from black squares.
    # Its captured bytes, first-frame log/probe, and map content jointly bind it.
    for name, expected, directory, boundary in (
        ('proof-input-digests.json', PROOF_INPUTS_SHA256, evidence, 'native proof'),
        ('host-source-applicability.json', HOST_SOURCE_SHA256, root, 'host map source'),
    ):
        raw = (Path(evidence) / name).read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, boundary + ' manifest changed')
        manifest = json.loads(raw)
        require(manifest['schema'] == 1 and bool(manifest['files']), boundary + ' manifest schema')
        verify_file_digests(directory, manifest['files'], boundary)


FRAME = re.compile(r'SITE_FRAME index=(\d+) id=(\S+) digest=([0-9a-f]{64}) heap=(\d+)')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def verify_required_ids(sites, rows):
    require(len(rows) == len(sites) and {r['id'] for r in rows} == set(sites), 'missing/duplicate required ID')


def verify_barcode(index, rgba, width):
    observed = 0
    for bit in range(8):
        pos = (364 * width + 127 + bit * 7) * 4
        color = rgba[pos:pos+3]
        if all(v > 200 for v in color):
            observed |= 1 << bit
        else:
            require(all(v < 40 for v in color), 'unreadable native frame barcode')
    require(observed == index, 'native frame/barcode identity mismatch')


def expected_position(source):
    if source is None:
        return None
    return {'encoding': 'decimal-text-v1', 'latitude': str(source['latitude']),
            'longitude': str(source['longitude']), 'units': source['units'],
            'qualification': source['qualification']}


def expected_anchor(lat, lon, center, scale=145):
    """Independent spherical rotation of a source point about a camera center."""
    lam = math.radians(lon - center[1])
    phi = math.radians(lat)
    delta = -math.radians(center[0])
    x, y, z = math.cos(lam) * math.cos(phi), math.sin(lam) * math.cos(phi), math.sin(phi)
    return (335 + scale * math.atan2(y, x * math.cos(delta) - z * math.sin(delta)),
            165 - scale * math.asin(max(-1, min(1, z * math.cos(delta) + x * math.sin(delta)))))


def verify_descriptor(identity, site, row, pin):
    d, ref = row['descriptor'], row['descriptorRef']
    raw = canonical_bytes(d)
    require(hashlib.sha256(raw).hexdigest() == ref['sha256'] and len(raw) == ref['decodedBytes'], 'descriptor bytes')
    require(d['siteId'] == identity and d['definitionSha256'] == hashlib.sha256(canonical_bytes(site)).hexdigest(), 'site identity/provenance')
    position = expected_position(site['position'])
    mode = site['facts'].get('positionMode', 'fixed-source')
    require(d['sourcePosition'] == position and d['positionMode'] == mode, 'source position/mode')
    active = position if mode == 'fixed-source' else None
    require(d['position'] == active, 'event position is not sourced')
    if active is None:
        require(d['center'] is None and d['marker'] is None and d['layers'] == [] and d['source'] is None, 'false pin')
        require(d['contextLimits'] == [('source-position-unavailable' if mode == 'fixed-source' else 'mobile-event-position-unavailable')], 'unavailable reason')
        return False
    lat, lon = float(active['latitude']), float(active['longitude'])
    center = [float(v) for v in d['center']]
    require(center == [lat, lon], 'camera not source-centered')
    x, y = expected_anchor(lat, lon, center)
    require(abs(x-335) < 1e-7 and abs(y-165) < 1e-7, 'independent anchor mismatch')
    require(d['marker'] == {'anchor': [335, 165], 'diameter': 28, 'colors': [0, 0xf7f9fc, 0xffd166]}, 'marker mismatch')
    require(d['source']['recipeSha256'] == pin and bool(d['layers']), 'missing geography source/context')
    return True


def verify_frame(identity, index, digest, log, image, chunks):
    found = [m for m in FRAME.finditer(log) if int(m[1]) == index]
    require(len(found) == 1 and found[0][2] == identity and found[0][3] == digest, 'native frame identity/digest')
    heap = int(found[0][4])
    require(heap > 0, 'native heap absent')
    expected = decode_raster(chunks, 390, 390, 3)
    require(hashlib.sha256(expected).hexdigest() == digest, 'raster digest')
    width, height, rgba = png_pixels(image)
    require((width, height) == (390, 390), 'frame dimensions')
    verify_barcode(index, rgba, width)
    def pixel(x, y):
        i = (y * width + x) * 4
        return rgba[i:i+3]
    marker = pixel(335, 165)
    require(marker[0] > 220 and marker[1] > 170 and marker[2] < 160, 'native marker absent/misaligned')
    compared = matched = 0
    for y in range(90, 215):
        for x in range(275, 360):
            if (x-195)**2 + (y-195)**2 > 185**2 or (x-335)**2 + (y-165)**2 < 18**2:
                continue
            pos = (y * width + x) * 3
            target = expected[pos:pos+3]
            if max(target) < 16:
                continue
            compared += 1
            matched += max(abs(target[k]-pixel(x, y)[k]) for k in range(3)) <= 8
    require(compared >= 500 and matched / compared >= .6, 'native geography pixels missing/mismatched')
    return {'heap': heap, 'marker': list(marker), 'mapCompared': compared, 'mapMatched': matched}


def verify_unavailable_frame(identity, index, log, image):
    found = [m for m in FRAME.finditer(log) if int(m[1]) == index]
    require(len(found) == 1 and found[0][2] == identity and found[0][3] == '0' * 64, 'unavailable native frame identity')
    width, height, rgba = png_pixels(image)
    require((width, height) == (390, 390), 'unavailable frame dimensions')
    verify_barcode(index, rgba, width)
    for y in range(148, 182):
        for x in range(318, 353):
            i = (y * width + x) * 4
            color = rgba[i:i+3]
            require(not (color[0] > 220 and color[1] > 170 and color[2] < 160), 'false native marker')
    return {'heap': int(found[0][4]), 'status': 'event-position-unavailable'}


def verify_detail(descriptor, probe, source_records, image):
    matches=[row for row in source_records if row['feature']==probe['feature'] and row['sourceSha256']==probe['sourceSha256']]
    require(len(matches)==1 and probe['coordinate'] in matches[0]['coordinates'], 'regional source vertex/provenance')
    scale=probe['scale']
    require('source-centered-regional-inset-scale:'+str(scale) in descriptor['contextLimits'], 'regional inset absent')
    lon,lat=map(float,probe['coordinate'])
    center=list(map(float,descriptor['center']))
    x,y=expected_anchor(lat,lon,center,scale)
    require(306<x<364 and 136<y<194 and math.hypot(x-335,y-165)>16, 'source vertex outside visible inset')
    w,h,rgba=png_pixels(image)
    require((w,h)==(390,390),'detail frame dimensions')
    def pixel(x,y):
        at=(y*w+x)*4
        return rgba[at:at+3]
    point=pixel(round(x),round(y))
    background=pixel(*probe['oceanSample'])
    require(point[0]-background[0]>=25 and point[1]-background[1]>=30 and point[2]-background[2]>=30, 'sourced regional detail missing from native frame')
    return {'sourceVertexPixel':[round(x),round(y)],'detailColor':list(point)}


def verify_native_builds(root, evidence, bindings):
    builds=evidence/'native-builds'
    common=json.loads((builds/'production-inputs.json').read_text())
    for path in ('watchface/source/NativeSfr.mc','watchface/source/NativeImmutable.mc',
                 'watchface/source/NativeVisualRenderer.mc','watchface/source/SceneRenderer.mc',
                 'watchface/source/SceneContext.mc','watchface/source/SceneSettings.mc',
                 'watchface/source/LocalePresentation.mc','watchface/source/Fitness.mc',
                 'watchface/source/generated/NativeAssets.mc'):
        require(hashlib.sha256((root/path).read_bytes()).hexdigest()==common['productionSources'][path], 'native rendering source changed: '+path)
    marker='watchface/resources/drawables/LaunchMarker.png'
    require(hashlib.sha256((root/marker).read_bytes()).hexdigest()==common['productionResources'][marker], 'native marker resource changed')
    for name in set(bindings.values()):
        part=name.removeprefix('native-').removesuffix('.log')
        require(len(part)==3 and part.isdigit(),'invalid native log binding')
        directory=builds/part
        build=json.loads((directory/'build-binding.json').read_text())
        require(build['exitCode']==0 and build['sourceSetSha256']==common['sourceSetSha256'], 'native build/source binding')
        require(hashlib.sha256((directory/'Probe.mc').read_bytes()).hexdigest()==build['probeSha256'], 'native probe source changed')
        owner=build['applicationUuid']+'|native-build-'+part+'|'+common['sourceSetSha256'][:12]
        require('SFR_PROBE owner='+owner in (evidence/'native-logs'/name).read_text(), 'native log owner/binary binding')


def qualify(root, evidence):
    root, evidence = Path(root), Path(evidence)
    verify_evidence_inputs(root, evidence)
    catalog = build_catalog(root)
    sites = catalog['dictionaries']['sites']
    rows = loads_json((evidence/'producer-rows.json').read_bytes())
    verify_required_ids(sites, rows)
    require(all(r['status'] == 'producer-pass' for r in rows), 'producer failure')
    frame_logs = {}
    bindings=json.loads((evidence/'frame-bindings.json').read_text())
    verify_native_builds(root,evidence,bindings)
    for key,name in bindings.items():
        index=int(key)
        require(str(index)==key and index not in frame_logs and Path(name).name==name,'invalid frame binding')
        text=(evidence/'native-logs'/name).read_text()
        matches=[m.group(0) for m in FRAME.finditer(text) if int(m[1])==index]
        require(len(matches)==1,'missing/duplicate selected native frame')
        frame_logs[index]=matches[0]
    probes=loads_json((root/'tests/fixtures/global_geography/required-regional-details.json').read_bytes())
    require(set(probes)<=set(sites),'regional review references unknown site')
    survey=loads_json((evidence/'context-survey.json').read_bytes())
    fixed_ids={row['id'] for row in rows if row['position'] is not None}
    require(len(survey)==len(fixed_ids) and {row['id'] for row in survey}==fixed_ids,'context survey missing/duplicate site')
    omitted={row['id'] for row in survey if float(row['nearestHighDegrees'])*math.pi/180*145<5 and (row['nearestSegmentPx'] is None or row['nearestSegmentPx']>5)}
    require(omitted==set(probes),'regional omissions require independent source review')
    from tools.spacefox.bridge_map import load_source as load_bridge_source
    from tools.spacefox.geographic_context import load_source as load_regional_source
    regional=load_regional_source(root,load_bridge_source(root,catalog['source']['visualBridge'])['index']['regional'])
    fixed_index = 0
    unavailable_index = sum(item['position'] is not None for item in rows)
    result = []
    pin = catalog['source']['visualBridge']['sha256']
    for item in sorted(rows, key=lambda r: r['id']):
        identity = item['id']
        binding = loads_json((evidence/'rebind'/f"{identity.replace(':', '_')}.json").read_bytes())
        active = verify_descriptor(identity, sites[identity], binding, pin)
        if active:
            require(item['pixelSha256'] == binding['pixelSha256'], 'source/raster binding')
            base = evidence/'generated'/identity.replace(':', '_')
            chunks = [(base/f'{i}.sfr').read_bytes() for i in range(len(item['shards']))]
            require([hashlib.sha256(c).hexdigest() for c in chunks] == item['shards'], 'raster shard provenance')
            image=(evidence/'captures'/f'{fixed_index:03}.png').read_bytes()
            checked=verify_frame(identity, fixed_index, item['pixelSha256'], frame_logs.get(fixed_index, ''), image, chunks)
            has_detail=any(x.startswith('source-centered-regional-inset-scale:') for x in binding['descriptor']['contextLimits'])
            require(has_detail == (identity in probes), 'regional detail review missing/extra')
            if has_detail:
                checked.update(verify_detail(binding['descriptor'],probes[identity],regional['supplements'],image))
            result.append({'id': identity, 'index': fixed_index, **checked})
            fixed_index += 1
        else:
            result.append({'id': identity, 'index': unavailable_index, **verify_unavailable_frame(identity, unavailable_index, frame_logs.get(unavailable_index, ''), (evidence/'captures'/f'{unavailable_index:03}.png').read_bytes())})
            unavailable_index += 1
    require(set(frame_logs) == set(range(unavailable_index)), 'missing/extra frame')
    return result


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--evidence', type=Path, required=True)
    args = p.parse_args()
    result = qualify(args.root, args.evidence)
    print(json.dumps({'total': len(result), 'positionedFrames': sum('mapCompared' in x for x in result), 'unavailableFrames': sum(x.get('status') == 'event-position-unavailable' for x in result), 'rows': result}, indent=2))
