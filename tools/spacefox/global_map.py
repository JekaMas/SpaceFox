"""Source-driven finite world context and exact-identity site-view producer.

Coordinates remain exact in manifests. Only artwork projection uses floats and
1/32-pixel quantization. This is not pad-accuracy or native qualification.
"""
from decimal import Decimal
import hashlib
import math
import re
from pathlib import Path

from .catalog import (CatalogError, _identity, _local_path, _read_snapshot, canonical_bytes, loads_json,
                      validate_catalog)
from .graphics import (UNITS, VisualError, _pooled, canonical_visual, split_visual,
                       validate_visual, LIMITS)


class GeographyError(ValueError):
    """A source, projection or bounded candidate is unsupported."""


def _require(ok, message):
    if not ok:
        raise GeographyError(message)


def position(latitude, longitude):
    for name, value, bound in (('latitude', latitude, 90), ('longitude', longitude, 180)):
        _require(type(value) is int or isinstance(value, Decimal), name + ' must be exact numeric')
        _require(not isinstance(value, Decimal) or value.is_finite(), 'nonfinite coordinate')
        _require(-bound <= value <= bound, 'coordinate out of range')
    return float(latitude), float(longitude)


def project(latitude, longitude, *, kind='map', center=(0, 0), size=256):
    """The current flat equirectangular map projection."""
    lat, lon = position(latitude, longitude)
    _, lon0 = position(*center)
    _require(kind == 'map' and type(size) is int and 8 <= size <= 256, 'unsupported projection/canvas')
    extent = size - 2
    delta = (lon - lon0 + 180) % 360 - 180
    return (1 + (delta + 180) / 360 * extent, 1 + (90 - lat) / 180 * extent)


def load_world(root, catalog):
    validate_catalog(catalog)
    pin = catalog['source'].get('geography')
    _require(isinstance(pin, dict) and set(pin) == {'path', 'sha256'}, 'catalog has no pinned world geometry')
    try:data = _read_snapshot(_local_path(Path(root).resolve(), pin['path']), 262144)
    except (OSError, ValueError):_require(False, 'world digest/size mismatch')
    _require(hashlib.sha256(data).hexdigest() == pin['sha256'], 'world digest/size mismatch')
    world = loads_json(data)
    if isinstance(world, dict) and world.get('schemaVersion') == 2:
        from .geographic_context import load_source
        return load_source(root, pin)['index']
    _require(isinstance(world, dict) and set(world) == {'schemaVersion', 'license', 'sources', 'credit', 'derivation', 'lines'}, 'invalid world envelope')
    _require(type(world['schemaVersion']) is int and world['schemaVersion'] == 1 and world['license'] == 'public-domain', 'world schema/rights not admitted')
    _require(isinstance(world['sources'], list) and world['sources'] and all(isinstance(s, str) and s.startswith('https://') for s in world['sources']), 'world sources required')
    lines = world['lines']
    _require(isinstance(lines, list) and 1 <= len(lines) <= 1000, 'world line count')
    total = 0
    for line in lines:
        _require(isinstance(line, list) and 2 <= len(line) <= 1024, 'world line bound')
        for p in line:
            _require(isinstance(p, list) and len(p) == 2, 'world point required')
            position(p[1], p[0])
        total += len(line)
    _require(total <= 12000, 'world vertex bound')
    return world


def _segments(a, b, kind, center, size):
    """Clip each geographic source segment at the date line or visible limb."""
    n = size - 2
    if kind == 'map':
        x = (float(a[0])-center[1]+180) % 360-180
        dx = (float(b[0])-float(a[0])+180) % 360-180
        end = x+dx
        def screen(lon, lat): return (1+(lon+180)/360*n, 1+(90-lat)/180*n)
        if -180 <= end <= 180:
            return [(screen(x,float(a[1])), screen(end,float(b[1])))]
        edge = 180 if end > 180 else -180
        t = (edge-x)/dx; lat = float(a[1])+t*(float(b[1])-float(a[1]))
        return [(screen(x,float(a[1])),screen(edge,lat)),
                (screen(-edge,lat),screen(end-2*edge,float(b[1])))]
    raise GeographyError('unsupported projection')


def world_visuals(world, *, kind='map', center=(0, 0), size=256):
    """Project shared sourced lines into bounded coastline/border ribbons.

    Low-detail Natural Earth context may omit tiny islands. A valid site marker
    never depends on land coverage. No invented island/land dot is substituted.
    """
    _require(world.get('schemaVersion') == 1, 'schema2 regional source requires the offwatch context producer; native bridge remains unqualified')
    project(0, 0, kind=kind, center=center, size=size)
    center = tuple(float(x) for x in center)
    draws = []
    for line in world['lines']:
        for a, b in zip(line,line[1:]):
            for u, v in _segments(a,b,kind,center,size):
                dx,dy = v[0]-u[0],v[1]-u[1]; length = math.hypot(dx,dy)
                if length < 1/32: continue
                # Projection art only. Exact metadata never enters this pool.
                ox,oy = -dy/length*.16,dx/length*.16
                poly = [(u[0]+ox,u[1]+oy),(v[0]+ox,v[1]+oy),(v[0]-ox,v[1]-oy),(u[0]-ox,u[1]-oy)]
                q = [(round(min(size,max(0,x))*UNITS),round(min(size,max(0,y))*UNITS)) for x,y in poly]
                if len(set(q)) != 4: continue
                draws.append((0x3a6872,[c for p in q for c in p]))
    _require(bool(draws), 'world projected to empty context')
    values = []
    for offset in range(0,len(draws),180):
        value = _pooled([size,size],draws[offset:offset+180])
        validate_visual(value); values.append(value)
    return values


def build_site_view(root, catalog, site_id, *, kind='map', event_position=None):
    """A compact producer selection; no global dictionary is a watch input."""
    try:
        validate_catalog(catalog)
        _require(site_id in catalog['dictionaries']['sites'], 'unknown site identity')
        site = catalog['dictionaries']['sites'][site_id]
        pos = site['position']; mode = site['facts'].get('positionMode', 'fixed-source')
        _require(mode in ('fixed-source', 'mobile-reference-no-event'), 'invalid site position mode')
        if event_position is not None:
            _require(isinstance(event_position, dict) and set(event_position) == {'latitude','longitude','sources'}, 'event position requires explicit provenance')
            _require(isinstance(event_position['sources'], list) and event_position['sources'] and all(isinstance(x,str) and x.startswith('https://') for x in event_position['sources']), 'event source required')
            position(event_position['latitude'],event_position['longitude'])
            pos = event_position
        elif mode == 'mobile-reference-no-event': pos = None
        _require(kind == 'map', 'unsupported projection')
        center = (0,0)
        marker = project(pos['latitude'],pos['longitude'],kind=kind,center=center) if pos else None
        world = load_world(root,catalog); objects = {}; layers = []
        for value in world_visuals(world,kind=kind,center=center):
            parts = []
            for data in split_visual(value):
                digest = hashlib.sha256(data).hexdigest(); objects[digest] = data
                parts.append({'sha256':digest,'decodedBytes':len(data)})
            layers.append({'sha256':hashlib.sha256(canonical_visual(value)).hexdigest(),'shards':parts})
        manifest = {'schemaVersion':1,'rendererVersion':1,'qualification':'producer-only-not-native-or-pad-accuracy',
                    'projection':{'kind':kind,'convention':'equirectangular-degrees-v1',
                                  'center':list(center),'canvas':[256,256],'units':UNITS,'bounds':[0,0,8192,8192]},
                    'site':{'id':site_id,'name':site['facts']['name'],'sourcePosition':site['position'],
                            'positionMode':mode,'eventPosition':event_position,
                            'sourceUrl':site['facts']['sourceUrl'],
                            'definitionSha256':hashlib.sha256(canonical_bytes(site)).hexdigest()},
                    'marker':None if marker is None else [round(marker[0]*UNITS),round(marker[1]*UNITS)],
                    'world':{'sha256':catalog['source']['geography']['sha256'],'license':world['license'],'credit':world['credit']},
                    'objectPathTemplate':'objects/{sha256}.json',
                    'layers':layers}
        _require(len(canonical_bytes(manifest)) <= 8192, 'geography selection exceeds 8192 bytes')
        _require(len(canonical_bytes(manifest))+sum(map(len,objects.values())) <= LIMITS['artifactBytes'], 'geography publisher budget exceeded')
        return {'manifest':manifest,'objects':objects}
    except (CatalogError,VisualError,OSError,KeyError) as exc:
        raise GeographyError(str(exc)) from exc


def audit_sites(root, catalog, *, render_contexts=False):
    """Enumerate all source rows, distinguishing projection from point accuracy."""
    _require(bool(catalog['dictionaries']['sites']), 'site audit requires a nonempty explicit scope')
    world = load_world(root,catalog); rows = []; map_digest = None
    if render_contexts:
        base = world_visuals(world)
        map_digest = hashlib.sha256(b''.join(canonical_visual(v) for v in base)).hexdigest()
    for identity, site in sorted(catalog['dictionaries']['sites'].items()):
        pos = site['position']; mode = site['facts'].get('positionMode','fixed-source')
        row = {'id':identity,'sourcePosition':pos,'positionMode':mode,'map':None,
               'eventPointEligible':pos is not None and mode == 'fixed-source'}
        if pos:
            center = (pos['latitude'],pos['longitude'])
            row['map'] = [round(x*UNITS) for x in project(*center)]
            if render_contexts:
                row['sharedMapContextSha256'] = map_digest
        rows.append(row)
    return {'qualification':'source-coordinate-render-validity-not-pad-accuracy-or-native',
            'catalogVersion':catalog['catalogVersion'],'worldSha256':catalog['source']['geography']['sha256'],
            'siteRows':len(rows),'numericSourcePairs':sum(r['sourcePosition'] is not None for r in rows),
            'eventPointEligible':sum(r['eventPointEligible'] for r in rows),
            'unknownPositions':sum(r['sourcePosition'] is None for r in rows),
            'mobileReferenceOnly':sum(r['positionMode']=='mobile-reference-no-event' for r in rows),
            'mobileNumericPairs':sum(r['positionMode']=='mobile-reference-no-event' and r['sourcePosition'] is not None for r in rows),
            'mobileUnknownPositions':sum(r['positionMode']=='mobile-reference-no-event' and r['sourcePosition'] is None for r in rows),
            'fixedNumericPairs':sum(r['positionMode']=='fixed-source' and r['sourcePosition'] is not None for r in rows),
            'fixedUnknownPositions':sum(r['positionMode']=='fixed-source' and r['sourcePosition'] is None for r in rows),
            'independentlyVerifiedCoordinateAccuracy':None,'contextsRendered':render_contexts,'rows':rows}


def _validate_geography_metadata(record):
    """Admit the site/projection semantics as well as the addressed geometry.

    The optional source/binding fields were added within schema1; retained
    manifests from before that addition remain supported.
    """
    _require(set(record) == {'schemaVersion','rendererVersion','qualification','projection','site','marker','world','objectPathTemplate','layers'},'invalid geography manifest fields')
    projection, site = record.get('projection'), record.get('site')
    _require(isinstance(projection,dict) and set(projection) == {'kind','convention','center','canvas','units','bounds'},'invalid geography projection')
    kind=projection['kind']
    _require(kind == 'map' and projection['convention'] == 'equirectangular-degrees-v1','unsupported geography projection')
    _require(all(isinstance(projection[k],list) and all(type(x) is int for x in projection[k]) for k in ('canvas','bounds')) and projection['canvas'] == [256,256] and type(projection['units']) is int and projection['units'] == UNITS and projection['bounds'] == [0,0,8192,8192],'geography projection metadata mismatch')
    center=projection['center']
    _require(isinstance(center,list) and len(center) == 2,'invalid geography center')
    position(*center)
    fields={'id','name','sourcePosition','positionMode','eventPosition'}
    _require(isinstance(site,dict) and fields <= site.keys() <= fields|{'sourceUrl','definitionSha256'},'invalid geography site')
    _identity(site['id'],'site')
    _require(isinstance(site['name'],str) and bool(site['name'].strip()),'geography site name required')
    mode=site['positionMode']
    _require(mode in ('fixed-source','mobile-reference-no-event'),'invalid geography position mode')
    source, event = site['sourcePosition'], site['eventPosition']
    if source is not None:
        _require(isinstance(source,dict) and set(source) == {'latitude','longitude','units','qualification'} and source['units'] == 'degrees' and source['qualification'] == 'unverified-reference','invalid geography source position')
        position(source['latitude'],source['longitude'])
    if event is not None:
        _require(isinstance(event,dict) and set(event) == {'latitude','longitude','sources'},'invalid geography event position')
        _require(isinstance(event['sources'],list) and bool(event['sources']) and all(isinstance(x,str) and x.startswith('https://') for x in event['sources']),'geography event source required')
        position(event['latitude'],event['longitude'])
    if 'sourceUrl' in site:
        _require(isinstance(site['sourceUrl'],str) and site['sourceUrl'].startswith('https://'),'geography site source required')
    if 'definitionSha256' in site:
        _require(isinstance(site['definitionSha256'],str) and re.fullmatch('[0-9a-f]{64}',site['definitionSha256']) is not None,'invalid geography site binding')
    active=event if event is not None else source if mode == 'fixed-source' else None
    expected_center=[0,0]
    _require(center == expected_center,'geography center/position mismatch')
    point=None if active is None else project(active['latitude'],active['longitude'],kind=kind,center=center)
    expected=None if point is None else [round(x*UNITS) for x in point]
    marker=record.get('marker')
    _require(marker is None or isinstance(marker,list) and len(marker) == 2 and all(type(x) is int for x in marker),'invalid geography marker')
    _require(marker == expected,'geography marker/position mismatch')
    world=record.get('world')
    _require(isinstance(world,dict) and set(world) == {'sha256','license','credit'} and isinstance(world['sha256'],str) and re.fullmatch('[0-9a-f]{64}',world['sha256']) is not None,'invalid geography world binding')
    _require(world['license'] == 'public-domain' and isinstance(world['credit'],str) and bool(world['credit'].strip()),'geography rights required')
    _require(record.get('objectPathTemplate') == 'objects/{sha256}.json','invalid geography object path template')
