"""Source-driven finite world context and exact-identity site-view producer.

Coordinates remain exact in manifests. Only artwork projection uses floats and
1/32-pixel quantization. This is not pad-accuracy or native qualification.
"""
from decimal import Decimal
import hashlib
import math
import re
from pathlib import Path

from .catalog import (CatalogError, _identity, _local_path, canonical_bytes, loads_json,
                      validate_catalog, validate_catalog_selection)
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
    """Equirectangular or orthographic projection; None is the back hemisphere."""
    lat, lon = position(latitude, longitude)
    lat0, lon0 = position(*center)
    _require(kind in ('map', 'globe') and type(size) is int and 8 <= size <= 256, 'unsupported projection/canvas')
    # One-pixel inset retains points at the poles/date line inside the canvas.
    extent = size - 2
    if kind == 'map':
        delta = (lon - lon0 + 180) % 360 - 180
        return (1 + (delta + 180) / 360 * extent, 1 + (90 - lat) / 180 * extent)
    phi, lam, phi0 = math.radians(lat), math.radians(lon - lon0), math.radians(lat0)
    z = math.sin(phi0)*math.sin(phi) + math.cos(phi0)*math.cos(phi)*math.cos(lam)
    if z < -1e-12:
        return None
    return (size/2 + extent/2*math.cos(phi)*math.sin(lam),
            size/2 - extent/2*(math.cos(phi0)*math.sin(phi)-math.sin(phi0)*math.cos(phi)*math.cos(lam)))


def load_world(root, catalog):
    validate_catalog(catalog)
    pin = catalog['source'].get('geography')
    _require(isinstance(pin, dict) and set(pin) == {'path', 'sha256'}, 'catalog has no pinned world geometry')
    data = _local_path(Path(root).resolve(), pin['path']).read_bytes()
    _require(len(data) <= 262144 and hashlib.sha256(data).hexdigest() == pin['sha256'], 'world digest/size mismatch')
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


def _xyz(lat, lon, center):
    phi, lam, phi0 = math.radians(lat), math.radians(lon-center[1]), math.radians(center[0])
    return (math.cos(phi)*math.sin(lam), math.cos(phi0)*math.sin(phi)-math.sin(phi0)*math.cos(phi)*math.cos(lam),
            math.sin(phi0)*math.sin(phi)+math.cos(phi0)*math.cos(phi)*math.cos(lam))


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
    u, v = _xyz(float(a[1]),float(a[0]),center), _xyz(float(b[1]),float(b[0]),center)
    if u[2] < 0 and v[2] < 0: return []
    if (u[2] < 0) != (v[2] < 0):
        t = u[2]/(u[2]-v[2]); h = tuple(u[i]+t*(v[i]-u[i]) for i in range(3))
        length = math.hypot(h[0],h[1]); h = (h[0]/length,h[1]/length,0)
        if u[2] < 0: u = h
        else: v = h
    return [((size/2+n/2*u[0],size/2-n/2*u[1]),(size/2+n/2*v[0],size/2-n/2*v[1]))]


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
        center = (pos['latitude'],pos['longitude']) if kind == 'globe' and pos else (0,0)
        marker = project(pos['latitude'],pos['longitude'],kind=kind,center=center) if pos else None
        world = load_world(root,catalog); objects = {}; layers = []
        for value in world_visuals(world,kind=kind,center=center):
            parts = []
            for data in split_visual(value):
                digest = hashlib.sha256(data).hexdigest(); objects[digest] = data
                parts.append({'sha256':digest,'decodedBytes':len(data)})
            layers.append({'sha256':hashlib.sha256(canonical_visual(value)).hexdigest(),'shards':parts})
        manifest = {'schemaVersion':1,'rendererVersion':1,'qualification':'producer-only-not-native-or-pad-accuracy',
                    'projection':{'kind':kind,'convention':'equirectangular-degrees-v1' if kind == 'map' else 'orthographic-visible-hemisphere-v1',
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
        row = {'id':identity,'sourcePosition':pos,'positionMode':mode,'map':None,'globe':None,
               'eventPointEligible':pos is not None and mode == 'fixed-source'}
        if pos:
            center = (pos['latitude'],pos['longitude'])
            row['map'] = [round(x*UNITS) for x in project(*center)]
            row['globe'] = [round(x*UNITS) for x in project(*center,kind='globe',center=center)]
            if render_contexts:
                values = world_visuals(world,kind='globe',center=center)
                shards = [part for value in values for part in split_visual(value)]
                row['globeContextSha256'] = hashlib.sha256(b''.join(canonical_visual(v) for v in values)).hexdigest()
                row['globeShards'] = len(shards); row['maxShardBytes'] = max(map(len,shards))
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
    _require(kind in ('map','globe') and projection['convention'] == ('equirectangular-degrees-v1' if kind == 'map' else 'orthographic-visible-hemisphere-v1'),'unsupported geography projection')
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
    expected_center=[active['latitude'],active['longitude']] if kind == 'globe' and active is not None else [0,0]
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


def _selection_files(selection, files):
    """Recheck delivered metadata and exact closure, including retained rights."""
    from .graphics import assemble_visual, loads_shard, _validate_shard_reference
    _require(isinstance(selection,dict) and set(selection) == {'visual','geography'} and isinstance(selection['geography'],list),'invalid bundle selection')
    roots = selection['geography']+([] if selection['visual'] is None else [selection['visual']])
    _require(bool(roots) and len(roots) == len(set(roots)),'empty/duplicate bundle selection')
    needed = set(roots)
    for path in roots:
        _require(isinstance(path,str) and path.startswith('manifests/') and path in files,'bundle selection dependency missing')
        record = loads_json(files[path]); is_visual = path == selection['visual']
        _require(isinstance(record,dict) and type(record.get('schemaVersion')) is int and record['schemaVersion'] == 1 and type(record.get('rendererVersion')) is int and record['rendererVersion'] == 1,'unsupported bundle manifest')
        if is_visual:
            _require(set(record) == {'schemaVersion','rendererVersion','catalogVersion','catalogSha256','qualification','selection','assets'},'invalid visual manifest envelope')
            _require(isinstance(record['catalogVersion'],str) and bool(record['catalogVersion'].strip()),'catalog version required')
            _require(isinstance(record['catalogSha256'],str) and re.fullmatch('[0-9a-f]{64}',record['catalogSha256']) is not None,'catalog digest required')
            _require(record.get('qualification') == 'producer-only-not-device-qualified' and isinstance(record.get('assets'),dict) and bool(record['assets']),'invalid retained visual manifest')
            if record['selection'] is not None:
                selected = record['selection']
                _require(isinstance(selected,dict) and isinstance(selected.get('roots'),list) and
                         1 <= len(selected['roots']) <= LIMITS['selectionRoots'],'invalid selected root count/shape')
            _require(len(files[path]) <= (LIMITS['selectionBytes'] if record.get('selection') is not None else LIMITS['artifactBytes']),'visual manifest byte limit')
            groups = list(record['assets'].items())
        else:
            _require(len(files[path]) <= 8192 and record.get('qualification') == 'producer-only-not-native-or-pad-accuracy','geography manifest byte limit/qualification')
            _validate_geography_metadata(record)
            projection=record['projection']
            _require(isinstance(record.get('layers'),list) and bool(record['layers']),'geography layers required')
            groups = [(None,g) for g in record['layers']]
        for identity,group in groups:
            _require(isinstance(group,dict) and isinstance(group.get('shards'),list) and bool(group['shards']),'bundle shard group required')
            if is_visual:
                _require(set(group) == {'sha256','shards','logicalDecodedBytes','animation','schemaVersion','rendererVersion','canvas','units','bounds','catalogRecord','rights'},'invalid bundle asset envelope')
                _require(isinstance(group['canvas'],list) and all(type(x) is int for x in group['canvas']) and
                         isinstance(group['bounds'],list) and all(type(x) is int for x in group['bounds']) and
                         type(group['units']) is int, 'invalid bundle asset canvas/bounds/units types')
            parts = []
            for ref in group['shards']:
                _require(isinstance(ref,dict) and isinstance(ref.get('sha256'),str) and re.fullmatch('[0-9a-f]{64}',ref['sha256']) is not None,'bundle shard pin required')
                name='objects/'+ref['sha256']+'.json'; needed.add(name)
                if is_visual:
                    _validate_shard_reference(ref)
                _require(name in files,'retained referenced object missing')
                data=files[name]
                _require(type(ref.get('decodedBytes')) is int and len(data) == ref['decodedBytes'] and hashlib.sha256(data).hexdigest() == ref['sha256'],'bundle geometry dependency mismatch')
                _require(canonical_visual(loads_shard(data)) == data,'noncanonical bundle shard')
                parts.append(data)
            value=assemble_visual(parts,group['animation'] if is_visual else [0,[]])
            encoded=canonical_visual(value)
            _require(hashlib.sha256(encoded).hexdigest() == group.get('sha256'),'bundle geometry digest mismatch')
            canvas=value[3]
            if is_visual:
                _require(group.get('canvas') == canvas and group.get('units') == UNITS and group.get('bounds') == [0,0,canvas[0]*UNITS,canvas[1]*UNITS] and type(group.get('logicalDecodedBytes')) is int and group['logicalDecodedBytes'] == len(encoded),'bundle visual metadata mismatch')
                _require(type(group.get('schemaVersion')) is int and group['schemaVersion'] == 1 and type(group.get('rendererVersion')) is int and group['rendererVersion'] == 1,'unsupported bundle asset')
                row=group.get('catalogRecord');facts=row.get('facts') if isinstance(row,dict) else None
                _require(isinstance(facts,dict) and identity == 'spacefox:asset:'+str(facts.get('id')) and row.get('kind') == 'asset','bundle asset identity mismatch')
                _require(facts.get('license') == 'MIT' and isinstance(facts.get('creator'),str) and bool(facts['creator'].strip()) and isinstance(facts.get('sources'),list) and facts['sources'] and all(isinstance(s,str) and bool(s.strip()) for s in facts['sources']),'bundle asset rights/attribution not admitted')
                rights={'license':'MIT','credit':facts.get('credit',facts['creator']),'admission':'explicit MIT source; local free default-pack admission only'}
                _require(isinstance(rights['credit'],str) and bool(rights['credit'].strip()) and group.get('rights') == rights,'bundle asset rights/credit mismatch')
            else:
                _require(canvas == projection['canvas'],'bundle geography canvas mismatch')
        if is_visual and record.get('selection') is not None:
            validate_catalog_selection(record['selection'],
                                       {key: group['catalogRecord'] for key, group in groups},
                                       expected_version=record.get('catalogVersion'))
    return needed


def _build_bundle(visual_pack, views, *, previous_directory=None):
    """Complete local Pages candidate with one previous compatible selection.

    The large normalized catalog remains publisher-side. All delivered current
    and retained manifests/objects count toward the unchanged 1MiB budget.
    """
    from .graphics import _validate_pack, loads_shard, assemble_visual
    _require(isinstance(views,list) and len(views) <= 4,'bounded site-view selection required')
    files = {}; current_files = set()
    def put(path,data):
        _require(path not in files or files[path] == data,'content-address collision')
        files[path] = data; current_files.add(path)
    def manifest(value):
        data = canonical_bytes(value); digest = hashlib.sha256(data).hexdigest()
        path = 'manifests/'+digest+'.json'; put(path,data); return path
    visual = None
    if visual_pack is not None:
        _validate_pack(visual_pack)
        visual = manifest(visual_pack['manifest'])
        for digest,data in visual_pack['objects'].items(): put('objects/'+digest+'.json',data)
    geography = []
    for view in views:
        _require(isinstance(view,dict) and set(view) == {'manifest','objects'},'invalid site view')
        m = view['manifest']
        _require(isinstance(m,dict) and type(m.get('schemaVersion')) is int and m['schemaVersion'] == 1 and type(m.get('rendererVersion')) is int and m['rendererVersion'] == 1,'unsupported geography schema/renderer')
        _require(len(canonical_bytes(m)) <= 8192 and m.get('world',{}).get('license') == 'public-domain','geography manifest/rights limit')
        _require(isinstance(m.get('layers'),list) and bool(m['layers']),'geography layers required')
        needed = set()
        for layer in m['layers']:
            fragments = []
            for part in layer['shards']:
                digest = part['sha256'];needed.add(digest)
                _require(digest in view['objects'],'missing geography object')
                data = view['objects'][digest]
                _require(type(part['decodedBytes']) is int and len(data) == part['decodedBytes'],'geography object byte mismatch')
                fragments.append(data)
            value = assemble_visual(fragments,[0,[]])
            _require(hashlib.sha256(canonical_visual(value)).hexdigest() == layer['sha256'],'geography logical digest mismatch')
        _require(set(view['objects']) == needed,'unreferenced geography object')
        geography.append(manifest(view['manifest']))
        for digest,data in view['objects'].items():
            loads_shard(data)
            _require(hashlib.sha256(data).hexdigest() == digest,'view shard digest mismatch')
            put('objects/'+digest+'.json',data)
    _require(visual is not None or geography, 'empty complete artifact')
    previous = None
    if previous_directory is not None:
        directory = Path(previous_directory).resolve(); old_path = directory/'manifest.json'
        _require(not old_path.is_symlink() and old_path.stat().st_size <= LIMITS['artifactBytes'],'retained root bound')
        old = loads_json(old_path.read_bytes())
        _require(isinstance(old,dict) and set(old) == {'schemaVersion','qualification','current','previous','currentFiles','files'}, 'unsupported retained bundle')
        _require(type(old['schemaVersion']) is int and old['schemaVersion'] == 1,'retained schema')
        _require(old['qualification'] == 'complete-local-producer-candidate-not-hosted-or-native','retained qualification')
        _require(isinstance(old['currentFiles'],list) and len(old['currentFiles']) <= 1024 and len(set(old['currentFiles'])) == len(old['currentFiles']),'invalid retained file list')
        _require(isinstance(old['files'],dict),'invalid retained index')
        for path in old['currentFiles']:
            _require(isinstance(path,str) and re.fullmatch(r'(objects|manifests)/[0-9a-f]{64}\.json',path) is not None,'invalid retained content path')
            info = old['files'].get(path);_require(isinstance(info,dict) and set(info) == {'sha256','bytes'},'invalid retained content pin')
            target = directory/path
            _require(not target.parent.is_symlink() and not target.is_symlink() and target.resolve().is_relative_to(directory),'retained path escape')
            _require(type(info['bytes']) is int and 1 <= info['bytes'] <= LIMITS['artifactBytes'] and target.stat().st_size == info['bytes'],'retained content bound')
            data = target.read_bytes();digest = hashlib.sha256(data).hexdigest()
            _require(digest == info['sha256'] == Path(path).stem and type(info['bytes']) is int and info['bytes'] == len(data),'retained content mismatch')
            if path.startswith('objects/'):
                loads_shard(data)
            else:
                record = loads_json(data)
                _require(isinstance(record,dict) and type(record.get('schemaVersion')) is int and record['schemaVersion'] == 1 and type(record.get('rendererVersion')) is int and record['rendererVersion'] == 1,'unsupported retained renderer/schema')
            _require(path not in files or files[path] == data,'retained collision');files[path] = data
        previous = old['current']
        retained_files={p:files[p] for p in old['currentFiles']}
        _require(_selection_files(previous,retained_files) == set(old['currentFiles']),'retained current file closure mismatch')
    index = {p:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for p,b in sorted(files.items())}
    envelope = {'schemaVersion':1,'qualification':'complete-local-producer-candidate-not-hosted-or-native',
                'current':{'visual':visual,'geography':geography},'previous':previous,
                'currentFiles':sorted(current_files),'files':index}
    _require(_selection_files(envelope['current'],files) == current_files,'bundle current file closure mismatch')
    total = len(canonical_bytes(envelope))+sum(map(len,files.values()))
    _require(total <= LIMITS['artifactBytes'],'complete current/retained publisher artifact exceeds 1048576 bytes')
    return {'manifest':envelope,'files':files,'artifactBytes':total}


def build_bundle(visual_pack, views, *, previous_directory=None):
    try:
        return _build_bundle(visual_pack, views, previous_directory=previous_directory)
    except (CatalogError, VisualError, OSError, KeyError, TypeError, AttributeError) as exc:
        raise GeographyError('invalid complete artifact: '+str(exc)) from exc


def _write_bundle(output, bundle):
    from .graphics import _atomic, _immutable, loads_shard
    _require(isinstance(bundle,dict) and set(bundle) == {'manifest','files','artifactBytes'},'invalid bundle candidate')
    manifest, files = bundle['manifest'], bundle['files']
    _require(isinstance(manifest,dict) and set(manifest) == {'schemaVersion','qualification','current','previous','currentFiles','files'},'invalid bundle envelope')
    _require(type(manifest['schemaVersion']) is int and manifest['schemaVersion'] == 1 and manifest['qualification'] == 'complete-local-producer-candidate-not-hosted-or-native','unsupported bundle')
    _require(isinstance(files,dict) and isinstance(manifest['files'],dict) and set(files) == set(manifest['files']),'bundle file index mismatch')
    for path,data in files.items():
        _require(isinstance(path,str) and re.fullmatch(r'(objects|manifests)/[0-9a-f]{64}\.json',path) is not None and isinstance(data,bytes),'invalid bundle content')
        digest = hashlib.sha256(data).hexdigest(); info = manifest['files'][path]
        _require(isinstance(info,dict) and set(info) == {'sha256','bytes'} and type(info['bytes']) is int and info['bytes'] == len(data) and digest == info['sha256'] == Path(path).stem,'bundle content pin mismatch')
        if path.startswith('objects/'):loads_shard(data)
    _require(isinstance(manifest['currentFiles'],list) and len(set(manifest['currentFiles'])) == len(manifest['currentFiles']) and set(manifest['currentFiles']) <= set(files),'bundle current index mismatch')
    current_files=_selection_files(manifest['current'],files)
    previous_files=set() if manifest['previous'] is None else _selection_files(manifest['previous'],files)
    _require(set(manifest['currentFiles']) == current_files,'bundle current file closure mismatch')
    _require(set(files) == current_files|previous_files,'unreferenced bundle file')
    total = len(canonical_bytes(manifest))+sum(map(len,files.values()))
    _require(type(bundle['artifactBytes']) is int and total == bundle['artifactBytes'] and total <= LIMITS['artifactBytes'],'bundle complete artifact byte mismatch/limit')
    output = Path(output).resolve(); output.mkdir(parents=True,exist_ok=True)
    _require(not (output/'manifest.json').is_symlink(),'bundle manifest symlink')
    for path,data in bundle['files'].items():
        target = output/path
        _require(target.parent.name in ('objects','manifests') and target.parent.parent == output,'invalid content destination')
        _require(not target.parent.is_symlink() and not target.is_symlink(),'bundle content symlink')
        target.parent.mkdir(exist_ok=True);_immutable(target,data)
    _atomic(output/'manifest.json',canonical_bytes(bundle['manifest']),'.bundle-')
    return {'qualification':bundle['manifest']['qualification'],'artifactBytes':bundle['artifactBytes'],
            'files':len(bundle['files']),'currentFiles':len(bundle['manifest']['currentFiles']),
            'retainedSelection':bundle['manifest']['previous'] is not None}


def write_bundle(output, bundle):
    try:
        return _write_bundle(output,bundle)
    except (CatalogError,VisualError,KeyError,TypeError,AttributeError) as exc:
        raise GeographyError('invalid complete artifact: '+str(exc)) from exc
