"""Off-watch regional geography and accepted-camera previews, never native wire.

Source schema2 is separate from legacy schema1. SFV1 limits are unchanged. The
preview descriptor is an explicit next native interface, not an FR165 transport.
"""
from decimal import Decimal
from functools import lru_cache
import gzip
import hashlib
import math
from pathlib import Path
import re

from .catalog import _local_path, canonical_bytes as _exact_bytes, loads_json, validate_catalog
from .global_map import _require, position
from .graphics import (UNITS, _pooled, canonical_visual, split_visual, loads_shard,
                       assemble_visual, LIMITS)

QUALIFICATION = 'offwatch-context-preview-not-native-wire-or-pad-survey'
# These are the original notices for the already pinned GSHHG archive/member.
# A rehashed nonempty replacement is not a copy of the corresponding license.
ORIGINAL_NOTICE_HASHES = {
    'LICENSE.TXT':'dc53a4833bf9121360a5286917683f041439327353ffe0231206c6b746005b81',
    'README.TXT':'8c83b0d9e861c3cf9390ccfcc28d57dd484b192e1767524e094c988ee9f84ac7',
    'COPYING.LESSERv3':'ea7d049c7705dc13afc202dd18e1827f3484f8212fd3fa7b82fc4a0c363432c9',
    'COPYINGv3':'3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986',
}


def canonical_bytes(value):
    # Only derived camera/art metrics are floats; source facts remain Decimal.
    def exact(v):
        if type(v) is float:
            _require(math.isfinite(v), 'nonfinite preview metric')
            return Decimal(str(v))
        if isinstance(v,dict):return {k:exact(x) for k,x in v.items()}
        if isinstance(v,(list,tuple)):return [exact(x) for x in v]
        return v
    return _exact_bytes(exact(value))


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _validate_original_notices(notices):
    _require(isinstance(notices,dict) and set(notices) == set(ORIGINAL_NOTICE_HASHES) and
             all(isinstance(text,str) and _sha(text.encode('utf-8')) == ORIGINAL_NOTICE_HASHES[name]
                 for name,text in notices.items()),'original corresponding license texts required')


def _read_pin(root, pin, maximum):
    _require(isinstance(pin, dict) and {'path', 'sha256'} <= pin.keys(), 'source pin required')
    path = _local_path(Path(root).resolve(), pin['path'])
    _require(path.stat().st_size <= maximum, 'offwatch input bound')
    data = path.read_bytes()
    _require(_sha(data) == pin['sha256'], 'source dependency digest mismatch')
    return data


@lru_cache(maxsize=4)
def _load_source_cached(root, data):
    source = loads_json(data)
    _require(source.get('schemaVersion') == 2 and source.get('format') == 'offwatch-regional-context-v1', 'unsupported regional source')
    _require(source.get('license') == 'LGPL-3.0-or-later' and source.get('sourceDate') == '2017-06-15', 'regional source rights/date')
    _require(source.get('originalArchiveSha256') == '28600e8f7a08645aab43079326df6504212ec5ccb2b4bcf3b5f4f12ed60e82bc' and
             source.get('originalMemberSha256') == '380f585415006f2b648a1a99383f50bf06518728d62991d98d48e7c2de48ec8f', 'unreviewed original geography source')
    _require(isinstance(source.get('sources'), list) and source['sources'] and all(isinstance(s,str) and s.startswith('https://') for s in source['sources']), 'source URLs required')
    base_data = _read_pin(root, source['baseWorld'], 262144)
    base = loads_json(base_data)
    _require(base.get('schemaVersion') == 1 and base.get('license') == 'public-domain', 'legacy base required')
    # Reuse the unchanged schema1 owner to enforce its existing complete bounds.
    _require(len(base['lines']) <= 1000 and sum(map(len,base['lines'])) <= 12000, 'base geometry bound')
    for line in base['lines']:
        _require(isinstance(line,list) and 2 <= len(line) <= 1024, 'base line bound')
        for p in line: position(p[1],p[0])
    notices = {}
    _require(isinstance(source.get('notices'),list) and len(source['notices']) == 4, 'four original notices required')
    for pin in source['notices']:
        raw = _read_pin(root,pin,65536)
        _require(pin.get('bytes') == len(raw), 'notice byte mismatch')
        notices[Path(pin['path']).name] = raw.decode('utf-8')
    _validate_original_notices(notices)
    records = []; total = 0
    _require(isinstance(source.get('clips'),list) and 1 <= len(source['clips']) <= 64, 'offwatch clip count')
    for pin in source['clips']:
        encoded = _read_pin(root,pin,262144)
        _require(type(pin.get('decodedBytes')) is int and 1 <= pin['decodedBytes'] <= 2097152, 'decoded source chunk bound')
        # Bound expansion before materializing untrusted decompressed bytes.
        import io
        with gzip.GzipFile(fileobj=io.BytesIO(encoded)) as stream:
            raw = stream.read(pin['decodedBytes'] + 1)
        _require(len(raw) == pin['decodedBytes'] and _sha(raw) == pin.get('decodedSha256'), 'decoded source chunk mismatch')
        total += len(raw); _require(total <= 8388608, 'offwatch selected source corpus bound')
        chunk = loads_json(raw)
        _require(set(chunk) == {'format','records'} and chunk['format'] == 'gshhg-microdegree-clips-v1', 'invalid source clip envelope')
        for record in chunk['records']:
            _require(isinstance(record,dict) and set(record) == {'feature','startVertex','points'}, 'invalid source clip')
            _require(type(record['feature']) is int and record['feature'] >= 0 and type(record['startVertex']) is int and record['startVertex'] >= 0, 'invalid original feature/index')
            points = record['points']
            _require(isinstance(points,list) and 2 <= len(points) <= 100000, 'source clip vertices')
            for p in points:
                _require(isinstance(p,list) and len(p) == 2 and all(type(v) is int for v in p) and -180000000 <= p[0] <= 180000000 and -90000000 <= p[1] <= 90000000, 'microdegree source coordinate')
            points_f = [(p[0]/1e6,p[1]/1e6) for p in points]
            record = dict(record)
            record['_line'] = points_f
            record['_box'] = (min(p[0] for p in points_f),min(p[1] for p in points_f),max(p[0] for p in points_f),max(p[1] for p in points_f))
            records.append(record)
    _require(len(records) == source['sourceRecords'] and sum(len(r['points']) for r in records) == source['sourceVertices'], 'source corpus denominator mismatch')
    coverage=source.get('coverage',{})
    _require(coverage.get('halfLatitudeDegrees') == 2 and coverage.get('halfLongitudeCosLatitudeDegrees') == 2 and isinstance(coverage.get('coordinateWindows'),list), 'source window contract')
    for center in coverage['coordinateWindows']:
        _require(isinstance(center,list) and len(center) == 2 and all(isinstance(x,str) for x in center), 'source coverage coordinate')
        from decimal import Decimal
        position(*map(Decimal,center))
    supplements=[]; supplement_notices=[]
    for spec in source.get('supplements',[]):
        _require(spec.get('license') == 'LicenseRef-PacIOOS-free-redistribution' and isinstance(spec.get('sources'),list) and spec['sources'] and all(x.startswith('https://') for x in spec['sources']), 'unreviewed supplement rights/provenance')
        encoded=_read_pin(root,spec,262144)
        _require(type(spec.get('decodedBytes')) is int and 1 <= spec['decodedBytes'] <= 2097152, 'supplement decoded bound')
        import io
        with gzip.GzipFile(fileobj=io.BytesIO(encoded)) as stream:raw=stream.read(spec['decodedBytes']+1)
        _require(len(raw)==spec['decodedBytes'] and _sha(raw)==spec['decodedSha256'], 'supplement source digest/size mismatch')
        metadata=_read_pin(root,spec['metadata'],65536).decode('iso-8859-1')
        _require(spec.get('useLimitation') == 'The data may be used and redistributed for free but is not intended for legal use, since it may contain inaccuracies.' and 'redistributed for free' in metadata, 'supplement redistribution terms missing')
        geo=loads_json(raw)
        _require(geo.get('type') == 'FeatureCollection' and geo.get('numberMatched') == geo.get('numberReturned') == geo.get('totalFeatures') == len(geo['features']) and geo['numberMatched'] == 731, 'supplement enumeration incomplete')
        identities=set()
        for feature in geo['features']:
            _require(isinstance(feature.get('id'),str) and feature['id'] not in identities, 'supplement identity duplicate/missing')
            identities.add(feature['id']);geom=feature['geometry']
            _require(geom['type'] in ('Polygon','MultiPolygon'), 'unsupported supplement geometry')
            rings=geom['coordinates'] if geom['type']=='Polygon' else [r for poly in geom['coordinates'] for r in poly]
            for number,ring in enumerate(rings):
                _require(isinstance(ring,list) and 4 <= len(ring) <= 10000 and ring[0] == ring[-1], 'supplement ring bound/closure')
                for point in ring:
                    _require(isinstance(point,list) and len(point)==2, 'supplement 2D coordinate')
                    position(point[1],point[0])
                line=[(float(x),float(y)) for x,y in ring]
                supplements.append({'sourceSha256':spec['decodedSha256'],'feature':feature['id'],'ring':number,'coordinates':ring,
                                    '_line':line,'_box':(min(x for x,y in line),min(y for x,y in line),max(x for x,y in line),max(y for x,y in line))})
        supplement_notices.append({'sourceSha256':spec['decodedSha256'],'license':spec['license'],'sourceDate':spec['sourceDate'],
                                   'sources':spec['sources'],'credit':spec['credit'],'useLimitation':spec['useLimitation'],
                                   'originalMetadata':metadata,'originalMetadataEncoding':'iso-8859-1','originalMetadataSha256':spec['metadata']['sha256'],'featureCount':len(identities)})
    return {'index':source, 'base':base, 'baseBytes':base_data, 'records':records, 'supplements':supplements,
            'supplementNotices':supplement_notices,'notices':notices, 'indexSha256':_sha(data)}


def load_source(root, pin):
    """Verify every transitive immutable input; returned data stay publisher-side."""
    data = _read_pin(root,pin,65536)
    # A cached decoded corpus never exempts dependency bytes from fresh admission.
    index=loads_json(data)
    extra=[p for spec in index.get('supplements',[]) for p in (spec,spec['metadata'])]
    for dependency in [index['baseWorld'],*index['clips'],*index['notices'],*extra]:
        _read_pin(root,dependency,262144)
    return _load_source_cached(str(Path(root).resolve()),data)


def dependencies(source):
    """Explicit materializer boundary: all immutable offwatch pins, never implicit."""
    index=source['index']
    return [index['baseWorld'],*index['clips'],*index['notices'],*[p for spec in index.get('supplements',[]) for p in (spec,spec['metadata'])]]


def _rotated(lon,lat,center):
    lon,lat=float(lon),float(lat)
    p,l,p0 = map(math.radians,(lat,(lon-center[1]+180)%360-180,center[0]))
    x=math.cos(p)*math.sin(l)
    y=math.cos(p0)*math.sin(p)-math.sin(p0)*math.cos(p)*math.cos(l)
    z=math.sin(p0)*math.sin(p)+math.cos(p0)*math.cos(p)*math.cos(l)
    return math.degrees(math.atan2(x,z)),math.degrees(math.asin(max(-1,min(1,y)))),x,y,z


def project_profile(latitude,longitude,*,kind,center,scale):
    position(latitude,longitude); position(*center)
    _require(kind in ('map','globe') and type(scale) in (int,float) and math.isfinite(scale) and 1 <= scale <= 500000, 'invalid preview camera')
    x,y,gx,gy,z=_rotated(float(longitude),float(latitude),tuple(map(float,center)))
    if kind == 'globe' and z < -1e-12:return None
    if kind == 'globe':return (335+gx*scale,165-gy*scale)
    return (335+math.radians(x)*scale,165-math.radians(y)*scale)


def _near(record,center,radius=2.1):
    west,south,east,north=record['_box'];lat,lon=map(float,center)
    if north < lat-radius or south > lat+radius:return False
    cos=max(.05,math.cos(math.radians(lat)))
    return any(west-radius/cos <= lon+turn <= east+radius/cos for turn in (-360,0,360))


def _point_distance(a,b):
    x,y=a;u,v=b;den=u*u+v*v
    t=0 if not den else max(0,min(1,-(x*u+y*v)/den))
    return math.hypot(x+t*u,y+t*v)


def _nearest(lines,center):
    nearest=180
    for line in lines:
        prior=None
        for lon,lat in line:
            x,y,*_=_rotated(lon,lat,center)
            if prior is not None and abs(x-prior[0]) < 180:
                nearest=min(nearest,_point_distance(prior,(x-prior[0],y-prior[1])))
            prior=(x,y)
    return nearest


def _clip(a,b):
    x,y=a;dx,dy=b[0]-x,b[1]-y;lo,hi=0,1
    for p,q in [(-dx,x),(dx,390-x),(-dy,y),(dy,390-y)]:
        if p == 0:
            if q < 0:return None
        elif p < 0:lo=max(lo,q/p)
        else:hi=min(hi,q/p)
        if lo > hi:return None
    return tuple((max(0,min(390,x+t*dx)),max(0,min(390,y+t*dy))) for t in (lo,hi))


def _simplify(points,tolerance):
    if len(points) <= 2:return points
    a,b=points[0],points[-1];dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
    best=(-1,0)
    for i,p in enumerate(points[1:-1],1):
        t=0 if not den else max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den))
        d=math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
        if d > best[0]:best=(d,i)
    if best[0] <= tolerance:return [a,b]
    i=best[1]
    return _simplify(points[:i+1],tolerance)[:-1]+_simplify(points[i:],tolerance)


def _segments(lines,center,kind,scale,tolerance):
    result=[]
    for line in lines:
        projected=[]
        for lon,lat in line:
            p=project_profile(Decimal(str(lat)),Decimal(str(lon)),kind=kind,center=center,scale=scale)
            # Splitting at limb/discontinuity avoids false cross-screen coasts.
            if p is None or (projected and math.dist(p,projected[-1]) > scale*math.pi):
                if len(projected)>1:result.extend(zip(_simplify(projected,tolerance),_simplify(projected,tolerance)[1:]))
                projected=[]
            if p is not None:projected.append(p)
        if len(projected)>1:
            simple=_simplify(projected,tolerance);result.extend(zip(simple,simple[1:]))
    return [p for a,b in result if (p:=_clip(a,b)) is not None and math.dist(*p) >= .05]


def _objects(segments):
    draws=[]
    from .graphics import VisualError
    for a,b in segments:
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        ox,oy=-dy/length*.3,dx/length*.3
        points=[(a[0]+ox,a[1]+oy),(b[0]+ox,b[1]+oy),(b[0]-ox,b[1]-oy),(a[0]-ox,a[1]-oy)]
        quant=[(round(max(0,min(390,x))*256/390*UNITS),round(max(0,min(390,y))*256/390*UNITS)) for x,y in points]
        if len(set(quant)) != 4:continue
        # Quantization can collapse a clipped ribbon; reject that primitive only.
        draw=(0x84bad0,[c for p in quant for c in p])
        try:_pooled([256,256],[draw])
        except VisualError:continue
        draws.append(draw)
    _require(bool(draws),'empty projected context')
    objects={};layers=[]
    for start in range(0,len(draws),180):
        value=_pooled([256,256],draws[start:start+180]);parts=[]
        for data in split_visual(value):
            digest=_sha(data);objects['objects/'+digest+'.json']=data
            parts.append({'sha256':digest,'decodedBytes':len(data)})
        layers.append({'sha256':_sha(canonical_visual(value)),'shards':parts})
    return objects,layers


def build_view(root,catalog,site_id,*,source_pin=None,kind='map',profile='regional',event_position=None,reference_context=False):
    """Build a source-backed preview; mobile references never activate a marker."""
    validate_catalog(catalog)
    _require(site_id in catalog['dictionaries']['sites'],'unknown site identity')
    _require(profile in ('regional','accepted04-full'),'unsupported preview profile')
    _require(profile != 'accepted04-full' or kind == 'map','owner accepted04 profile is map only; globe is a separate regional study')
    source=load_source(root,source_pin or catalog['source']['geography'])
    site=catalog['dictionaries']['sites'][site_id];mode=site['facts'].get('positionMode','fixed-source')
    active=site['position'] if mode == 'fixed-source' else None
    if event_position is not None:
        _require(isinstance(event_position,dict) and set(event_position) == {'latitude','longitude','sources'} and isinstance(event_position['sources'],list) and event_position['sources'] and all(isinstance(s,str) and s.startswith('https://') for s in event_position['sources']),'event provenance required')
        position(event_position['latitude'],event_position['longitude']);active=event_position
    _require(type(reference_context) is bool and not(reference_context and event_position is not None), 'invalid reference diagnostic')
    reference=site['position'] if reference_context else None
    camera_position=active or reference
    center=(camera_position['latitude'],camera_position['longitude']) if camera_position else (0,0)
    coverage=source['index']['coverage']['coordinateWindows']
    _require(not camera_position or any(abs(float(a)-float(center[0])) <= 2 and abs((float(b)-float(center[1])+180)%360-180)*max(.05,math.cos(math.radians(float(center[0])))) <= 2 for a,b in coverage),'coordinate outside derived source coverage; regenerate immutable source revision')
    nearby=[r for r in source['records'] if _near(r,center)] if camera_position else []
    extra=[r for r in source['supplements'] if _near(r,center)] if camera_position else []
    # Prefer the newer source where actual polygon extents overlap a historical
    # contour, with a declared 0.02-degree matching halo. A dataset-wide bbox
    # would wrongly suppress unrelated islands between disconnected polygons.
    def superseded(record):
        a,b,c,d=record['_box']
        return any(not(c < w-.02 or a > e+.02 or d < s-.02 or b > n+.02) for w,s,e,n in (r['_box'] for r in extra))
    nearby=[r for r in nearby if not superseded(r)]+extra
    high_lines=[r['_line'] for r in nearby]
    base_lines=source['base']['lines']
    near_high=_nearest(high_lines,tuple(map(float,center))) if high_lines else 180
    near_base=_nearest(base_lines,tuple(map(float,center)))
    nearest=min(near_high,near_base)
    radius=max(.003,min(45,nearest*3+.003))
    scale=145 if profile == 'accepted04-full' else min(500000,110/math.radians(radius))
    # Source proof contains exact selected input, independent of simplification.
    used=[r for r in nearby if _near(r,center,radius*2)] if profile=='regional' else nearby
    lines=base_lines+[r['_line'] for r in used]
    tolerance=.3
    for attempt in range(5):
        segments=_segments(lines,center,kind,scale,tolerance)
        objects,layers=_objects(segments)
        if len(canonical_bytes(layers)) < 5400:break
        tolerance*=2
    common={'format':'corresponding-geography-common-v1','sourceIndexSha256':source['indexSha256'],
            'originalArchiveSha256':source['index']['originalArchiveSha256'],'originalMemberSha256':source['index']['originalMemberSha256'],
            'sourceDate':source['index']['sourceDate'],'sources':source['index']['sources'],
            'license':'LGPL-3.0-or-later','credit':source['index']['credit'],'notices':source['notices'],
            'baseWorld':source['base'],'supplementNotices':source['supplementNotices']}
    common_data=canonical_bytes(common);common_path='sources/'+_sha(common_data)+'.json';objects[common_path]=common_data
    proof={'format':'corresponding-selected-geographic-source-v1',
           'common':{'path':common_path,'sha256':_sha(common_data),'decodedBytes':len(common_data)},
           'clips':[{k:v for k,v in r.items() if not k.startswith('_')} for r in used],
           'derivation':{'rotation':'spherical-site-centered-v1','ribbonWidthPx':Decimal('.6'),
                         'finalCanvas':[390,390],'sfvCanvas':[256,256],'sfvToFinalScale':'390/256',
                         'markerAnchor':[335,165],'sourcePriorityMatchHaloDegrees':Decimal('.02')}}
    proof_data=canonical_bytes(proof);proof_path='sources/'+_sha(proof_data)+'.json';objects[proof_path]=proof_data
    marker=[335,165] if active else None
    manifest={'schemaVersion':2,'rendererVersion':1,'qualification':QUALIFICATION,
              'source':{'path':proof_path,'sha256':_sha(proof_data),'decodedBytes':len(proof_data)},
              'site':{'id':site_id,'sourcePosition':site['position'],'positionMode':mode,'eventPosition':event_position,
                      'definitionSha256':_sha(canonical_bytes(site)),'sourceUrl':site['facts']['sourceUrl'],'referenceContextOnly':reference_context},
              'camera':{'kind':kind,'profile':profile,'center':list(center),'scale':scale,'canvas':[390,390],'sfvCanvas':[256,256],'markerAnchor':[335,165],'simplificationTolerancePx':tolerance},
              'marker':marker,'context':{'nearestHighResolutionCoastDegrees':near_high,'nearestBaseLineDegrees':near_base,
                                        'selectedSourceClips':len(used),'projectedSegments':len(segments),
                                        'contextSuitability':'source-lines-in-selected-camera-not-independent-cartographic-or-pad-acceptance'},
              'layers':layers}
    _require(len(canonical_bytes(manifest)) <= 8192,'context selection exceeds 8192 bytes')
    return {'manifest':manifest,'files':objects,'segments':segments}


def validate_view(manifest,files):
    _require(isinstance(manifest,dict) and manifest.get('schemaVersion') == 2 and manifest.get('rendererVersion') == 1 and manifest.get('qualification') == QUALIFICATION,'unsupported preview descriptor')
    _require(len(canonical_bytes(manifest)) <= 8192,'context selection limit')
    source=manifest.get('source');_require(isinstance(source,dict) and set(source)=={'path','sha256','decodedBytes'},'selected source pin')
    needed={source['path']}
    _require(source['path'] == 'sources/'+source['sha256']+'.json' and source['path'] in files,'corresponding source missing')
    raw=files[source['path']];_require(type(source['decodedBytes']) is int and len(raw)==source['decodedBytes'] and _sha(raw)==source['sha256'],'corresponding source corrupt')
    proof=loads_json(raw);common=proof.get('common',{})
    _require(common.get('path') == 'sources/'+str(common.get('sha256'))+'.json' and common['path'] in files, 'common corresponding source missing')
    needed.add(common['path']);common_data=files[common['path']]
    _require(type(common.get('decodedBytes')) is int and len(common_data)==common['decodedBytes'] and _sha(common_data)==common.get('sha256'), 'common corresponding source corrupt')
    common_record=loads_json(common_data)
    notices=common_record.get('notices',{})
    _require(common_record.get('license') == 'LGPL-3.0-or-later','corresponding rights incomplete')
    _validate_original_notices(notices)
    supplement_notices=common_record.get('supplementNotices')
    _require(isinstance(supplement_notices,list),'corresponding supplement rights missing')
    supplement_sources=set()
    for notice in supplement_notices:
        _require(isinstance(notice,dict) and notice.get('license') == 'LicenseRef-PacIOOS-free-redistribution' and
                 notice.get('useLimitation') == 'The data may be used and redistributed for free but is not intended for legal use, since it may contain inaccuracies.' and
                 isinstance(notice.get('originalMetadata'),str) and 'redistributed for free' in notice['originalMetadata'],
                 'corresponding supplement rights incomplete')
        metadata=notice['originalMetadata']
        _require(notice.get('originalMetadataEncoding') == 'iso-8859-1' and
                 all(ord(c) <= 255 for c in metadata) and
                 _sha(metadata.encode('iso-8859-1')) == notice.get('originalMetadataSha256'),
                 'corresponding supplement metadata digest/encoding mismatch')
        supplement_sources.add(notice.get('sourceSha256'))
    _require(proof.get('format') == 'corresponding-selected-geographic-source-v1' and isinstance(proof.get('clips'),list) and
             all('sourceSha256' not in clip or clip['sourceSha256'] in supplement_sources for clip in proof['clips']),
             'selected source lacks corresponding supplement rights')
    camera=manifest['camera'];site=manifest['site']
    _require(isinstance(site,dict) and site.get('positionMode') in ('fixed-source','mobile-reference-no-event') and
             type(site.get('referenceContextOnly')) is bool,'invalid preview position mode/reference')
    source_position=site['sourcePosition'];event_position=site['eventPosition']
    if source_position is not None:
        _require(isinstance(source_position,dict) and set(source_position) == {'latitude','longitude','units','qualification'} and
                 source_position['units'] == 'degrees' and source_position['qualification'] == 'unverified-reference',
                 'invalid preview source position')
        position(source_position['latitude'],source_position['longitude'])
    if event_position is not None:
        _require(isinstance(event_position,dict) and set(event_position) == {'latitude','longitude','sources'} and
                 isinstance(event_position['sources'],list) and bool(event_position['sources']) and
                 all(isinstance(s,str) and s.startswith('https://') for s in event_position['sources']),
                 'preview event provenance required')
        position(event_position['latitude'],event_position['longitude'])
    _require(not(site['referenceContextOnly'] and event_position is not None),'invalid reference diagnostic')
    active=event_position if event_position is not None else source_position if site['positionMode']=='fixed-source' else None
    camera_position=active or (site['sourcePosition'] if site.get('referenceContextOnly') is True else None)
    center=[camera_position['latitude'],camera_position['longitude']] if camera_position else [0,0]
    _require(camera['center']==center and camera['markerAnchor']==[335,165] and camera['canvas']==[390,390] and camera['sfvCanvas']==[256,256],'preview camera/source mismatch')
    _require(manifest['marker'] == ([335,165] if active else None),'mobile/unknown/point alignment mismatch')
    _require(proof.get('derivation',{}).get('rotation') == 'spherical-site-centered-v1', 'unsupported corresponding derivation')
    _require(camera['kind'] in ('map','globe') and camera['profile'] in ('regional','accepted04-full') and 1 <= camera['scale'] <= 500000 and (camera['profile'] != 'accepted04-full' or camera['scale'] == 145), 'preview camera contract')
    _require(camera['profile'] != 'accepted04-full' or camera['kind'] == 'map','owner accepted04 profile is map only; globe is a separate regional study')
    _require(isinstance(manifest.get('layers'),list) and bool(manifest['layers']), 'preview layers required')
    for layer in manifest['layers']:
        parts=[]
        for pin in layer['shards']:
            path='objects/'+pin['sha256']+'.json';needed.add(path)
            _require(path in files and type(pin['decodedBytes']) is int and len(files[path])==pin['decodedBytes'] and _sha(files[path])==pin['sha256'],'preview shard pin mismatch')
            loads_shard(files[path]);parts.append(files[path])
        _require(_sha(canonical_visual(assemble_visual(parts,[0,[]])))==layer['sha256'],'preview layer digest mismatch')
    return needed


def build_artifact(views,previous=None):
    """All source/license/descriptor/shard bytes count, including prior current."""
    _require(1 <= len(views) <= 4,'one to four bounded previews required')
    files={};current=[];current_files=set()
    for view in views:
        m=view['manifest'];needed=validate_view(m,view['files'])
        _require(needed==set(view['files']),'unreferenced preview files')
        raw=canonical_bytes(m);path='manifests/'+_sha(raw)+'.json'
        _require(path not in current,'duplicate preview descriptor')
        current.append(path);files.update(view['files']);files[path]=raw
        current_files.update(needed|{path})
    prior=[]
    if previous:
        validate_artifact(previous)
        prior=previous['manifest']['current']
        for path in previous['manifest']['currentFiles']:
            _require(path not in files or files[path]==previous['files'][path],'immutable preview collision')
            files[path]=previous['files'][path]
    envelope={'schemaVersion':2,'qualification':QUALIFICATION,'current':current,'previous':prior,
              'currentFiles':sorted(current_files),'files':{p:{'sha256':_sha(b),'bytes':len(b)} for p,b in sorted(files.items())}}
    artifact={'manifest':envelope,'files':files}
    validate_artifact(artifact)
    artifact['artifactBytes']=len(canonical_bytes(envelope))+sum(map(len,files.values()))
    return artifact


def validate_artifact(artifact):
    _require(isinstance(artifact,dict) and {'manifest','files'} <= artifact.keys(),'invalid preview artifact')
    m,files=artifact['manifest'],artifact['files']
    _require(isinstance(m,dict) and {'schemaVersion','qualification','current','previous','currentFiles','files'} <= m.keys() and
             type(m['schemaVersion']) is int and m['schemaVersion']==2 and m['qualification']==QUALIFICATION and
             isinstance(files,dict) and isinstance(m['files'],dict) and set(m['files'])==set(files),'invalid preview artifact')
    # Importing an external or retained envelope has the same selection contract
    # as the producer. Current/prior overlap remains valid across an update.
    for name,minimum in (('current',1),('previous',0)):
        paths=m[name]
        _require(isinstance(paths,list) and minimum <= len(paths) <= 4 and
                 all(isinstance(path,str) for path in paths) and len(set(paths))==len(paths),
                 'invalid preview '+name+' selection')
    _require(isinstance(m['currentFiles'],list) and all(isinstance(path,str) for path in m['currentFiles']),
             'invalid preview current file list')
    for path,raw in files.items():
        _require(isinstance(path,str) and re.fullmatch(r'(objects|manifests|sources)/[0-9a-f]{64}\.json',path) is not None and isinstance(raw,bytes),'invalid preview path')
        pin=m['files'][path]
        _require(isinstance(pin,dict) and type(pin.get('bytes')) is int and 0 < pin['bytes'] <= LIMITS['artifactBytes'] and
                 pin=={'sha256':_sha(raw),'bytes':len(raw)} and Path(path).stem==_sha(raw),'preview file digest/size mismatch')
    def closure(paths):
        needed=set(paths)
        for path in paths:
            _require(path.startswith('manifests/') and path in files,'preview descriptor missing')
            needed.update(validate_view(loads_json(files[path]),files))
        return needed
    current=closure(m['current']);previous=closure(m['previous'])
    _require(set(m['currentFiles'])==current and len(m['currentFiles'])==len(current) and current|previous==set(files),'preview file closure mismatch')
    _require(len(canonical_bytes(m))+sum(map(len,files.values())) <= LIMITS['artifactBytes'],'complete current/retained preview artifact exceeds 1048576 bytes')
    return artifact
