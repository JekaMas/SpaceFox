"""Sourced accepted04/full producer map, immutable SFV1 geometry and no layout list.

Offwatch raster-to-rectangle fill uses pinned D3 projection of original polygons.
Source2 context ribbons remain separate; no open clipped coastline is filled.
"""
import json
import math
import subprocess
from pathlib import Path

from .catalog import _local_path, canonical_bytes, loads_json
from .graphics import _pooled, canonical_visual, split_visual, UNITS
from .global_map import position
from .wire import _source_position, _validate_source_position
from .visual_bridge import put, sha, _require, asset_descriptor

ORIGINAL_MAP_NOTICES = {'licenses/d3-LICENSE.txt': '3e6849627f74ff73c257a3ae1efb574015d94fc1035c05ec3c15805165efcbc4', 'licenses/topojson-client-LICENSE.txt': '4c4d15b635e04e691825a76db7d33f7f2033b55669a7430011694f31e6c65999', 'licenses/d3-maps-atlas-LICENSE.txt': '587159f997588631bfb26798c78cc1be03260ae05dafdff1ff11976eb53bc18b'}

STYLE = {'profile':'accepted04-full','canvas':[390,390],'sfvCanvas':[256,256],
         'projection':'spherical-site-centered-equirectangular-v1','scale':145,
         'anchor':[335,165],'clip':'circle-390','timeBackground':'transparent',
         'ocean':0x102c43,'land':0x397f9a,'coast':0x84bad0,
         'horizontalFade':[[0,6],[25,22],[60,68],[100,100]],
         'verticalFade':[[0,6],[18,55],[40,100],[65,90],[100,4]],
         'opacityPercent':85,'markerDiameter':28,'markerFade':False,
         'fillSamplingPixels':3,'fillColorQuantum':8}


def dependencies(index):
    return [index[k] for k in ('topology','d3','topojson','regional')]+index['notices']


def load_source(root,pin):
    def read(item,maximum):
        raw=_local_path(Path(root).resolve(),item['path']).read_bytes()
        _require(len(raw)<=maximum and sha(raw)==item['sha256'],'map source digest/bound')
        return raw
    index=loads_json(read(pin,65536))
    _require(set(index)=={'schemaVersion','format','license','sources','credit','originalTopologySha256','topology','d3','topojson','regional','derivation','notices'}
             and index['schemaVersion']==1 and index['format']=='accepted04-map-source-v1'
             and index['license']=='public-domain' and index['originalTopologySha256']=='c3791187af0ef51b0d238c156058399fc9603c9974f960eb2889cdbee268a736', 'map source schema/rights')
    _require(type(index['notices']) is list and {x['path']:x['sha256'] for x in index['notices']}==ORIGINAL_MAP_NOTICES,'original map notices required')
    notices=[]
    for pin in index['notices']:
        raw=read(pin,65536);notices.append({'path':pin['path'],'sha256':pin['sha256'],'text':raw.decode('utf-8')})
    topology=read(index['topology'],262144)
    _require(sha(topology)==index['originalTopologySha256'],'original polygon source changed')
    # Separate MIT/BSD runtime source notices remain in repository, distinct from
    # public-domain cartography and LGPL/SPC/PacIOOS geographic context.
    d3=read(index['d3'],524288);topojson=read(index['topojson'],65536)
    from .geographic_context import load_source as regional_source
    regional=regional_source(root,index['regional'])
    return {'index':index,'topology':json.loads(topology),'d3':d3.decode(),'topojson':topojson.decode(),'regional':regional,'notices':notices}


def _fade(x,y):
    def lerp(stops,t):
        for a,b in zip(stops,stops[1:]):
            if t<=b[0]:return (a[1]+(b[1]-a[1])*(t-a[0])/(b[0]-a[0]))/100
        return stops[-1][1]/100
    return .85*lerp(STYLE['horizontalFade'],x/3.9)*lerp(STYLE['verticalFade'],y/3.9)


def _layers(files,draws,label):
    result=[];chunk=[];palette=set()
    def flush():
        if not chunk:return
        visual=_pooled([256,256],chunk);raw=canonical_visual(visual);parts=[]
        for fragment in split_visual(visual):
            digest=sha(fragment);path='objects/'+digest+'.json';files[path]=fragment
            parts.append(dict(path=path,sha256=digest,decodedBytes=len(fragment)))
        result.append(asset_descriptor(files,'spacefox:map-layer:'+label+'-'+str(len(result)),
            {'sha256':sha(raw),'canvas':[256,256],'animation':[0,[]],'shards':parts}))
    for color,coords in draws:
        if len(chunk)>=180 or color not in palette and len(palette)>=32:
            flush();chunk=[];palette=set()
        chunk.append((color,coords));palette.add(color)
    flush()
    return result


def build_map(root,catalog,site_id,files):
    site=catalog['dictionaries']['sites'][site_id]
    mode=site['facts'].get('positionMode','fixed-source')
    source_position=_source_position(site['position'])
    active=source_position if mode=='fixed-source' else None
    descriptor={'type':'map','schemaVersion':2,'rendererVersion':1,'siteId':site_id,
                'definitionSha256':sha(canonical_bytes(site)),'sourcePosition':source_position,
                'position':active,'positionMode':mode,'style':STYLE,'center':None,
                'marker':None,'layers':[],'source':None,'contextLimits':[]}
    if active is None:
        descriptor['contextLimits']=['mobile-event-position-unavailable' if mode!='fixed-source' else 'source-position-unavailable']
        return put(files,descriptor)
    pin=catalog['source'].get('visualBridge')
    _require(pin is not None,'accepted04 source recipe required')
    source=load_source(root,pin)
    center=[site['position']['latitude'],site['position']['longitude']]
    position(*center)
    data={'center':list(map(float,center)),**{k:source[k] for k in ('topology','d3','topojson')}}
    script=Path(__file__).with_name('bridge_map_render.js')
    proc=subprocess.run(['node',str(script)],input=json.dumps(data,separators=(',',':')).encode(),
                        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=60)
    _require(proc.returncode==0 and len(proc.stdout)<=1048576,'pinned D3 map renderer failed/bound')
    rendered=json.loads(proc.stdout)
    _require(all(abs(a-b)<1e-7 for a,b in zip(rendered['anchor'],[335,165])),'D3 source-point anchor mismatch')
    def q(x):return round(max(0,min(390,x))*256/390*UNITS)
    draws=[(color,[q(x0),q(y0),q(x1),q(y0),q(x1),q(y1),q(x0),q(y1)])
           for color,x0,y0,x1,y1 in rendered['rectangles']]
    layers=_layers(files,draws,'fill')
    # Reuse the owning source2 view for exact source selection/proofs, camera and
    # safe mobile semantics; its old technical object bytes are not republished.
    from .geographic_context import build_view,validate_view
    view=build_view(root,catalog,site_id,source_pin=source['index']['regional'],profile='accepted04-full')
    validate_view(view['manifest'],view['files'])
    coast=[]
    for a,b in view['segments']:
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length<.1:continue
        ox,oy=-dy/length*.325,dx/length*.325
        coords=[q(c) for p in ((a[0]+ox,a[1]+oy),(b[0]+ox,b[1]+oy),(b[0]-ox,b[1]-oy),(a[0]-ox,a[1]-oy)) for c in p]
        alpha=_fade((a[0]+b[0])/2,(a[1]+b[1])/2)
        rgb=[round(v*alpha) for v in (0x84,0xba,0xd0)];color=rgb[0]*65536+rgb[1]*256+rgb[2]
        # Quantization can collapse a subpixel coastline strip. _pooled only
        # assembles indices; validate the resulting wire polygon before adding
        # it to a layer so an invisible degenerate strip cannot abort the map.
        try: canonical_visual(_pooled([256,256],[(color,coords)]))
        except ValueError as error:
            if str(error) in ('zero-area wire polygon', 'duplicate polygon vertex', 'unsupported self-intersecting fill/polygon'):
                continue
            raise
        coast.append((color,coords))
    layers.extend(_layers(files,coast,'coast'))
    # Corresponding source and exact original notices are delivered offwatch.
    for path,raw in view['files'].items():
        if path.startswith('sources/'):files[path]=raw
    pages=[put(files,{'type':'map-layers','schemaVersion':2,'layers':layers[i:i+12]}) for i in range(0,len(layers),12)]
    notice_raw=canonical_bytes({'format':'accepted04-source-notices-v1','worldSha256':source['index']['originalTopologySha256'],'credit':source['index']['credit'],'sources':source['index']['sources'],'notices':source['notices']})
    notice_ref={'path':'sources/'+sha(notice_raw)+'.json','sha256':sha(notice_raw),'decodedBytes':len(notice_raw)}
    files[notice_ref['path']]=notice_raw
    descriptor.update(center=[str(v) for v in center],marker={'anchor':[335,165],'diameter':28,'colors':[0x000000,0xf7f9fc,0xffd166]},
                      layers=pages,source={'recipeSha256':pin['sha256'],'worldSha256':source['index']['originalTopologySha256'],
                                           'corresponding':view['manifest']['source'],'notices':notice_ref},
                      contextLimits=['source-reference-not-independent-pad-survey','full-camera-small-islands-may-be-subpixel','native-full-scene-not-observed'])
    validate_map(descriptor)
    return put(files,descriptor)


def validate_map(value):
    _require(set(value)=={'type','schemaVersion','rendererVersion','siteId','definitionSha256','sourcePosition','position','positionMode','style','center','marker','layers','source','contextLimits'}
             and type(value['schemaVersion']) is int and value['schemaVersion']==2
             and type(value['rendererVersion']) is int and value['rendererVersion']==1
             and canonical_bytes(value['style'])==canonical_bytes(STYLE),'unsupported map descriptor/style')
    from .catalog import _identity
    _identity(value['siteId'],'site')
    _require(type(value['definitionSha256']) is str and len(value['definitionSha256'])==64 and all(c in '0123456789abcdef' for c in value['definitionSha256']),'site definition digest')
    _validate_source_position(value['sourcePosition']);_validate_source_position(value['position'])
    _require(value['positionMode'] in ('fixed-source','mobile-reference-no-event')
             and value['position']==(value['sourcePosition'] if value['positionMode']=='fixed-source' else None), 'map active source mismatch')
    _require(type(value['layers']) is list and len(value['layers'])<=64,'map layer bound')
    _require(type(value['contextLimits']) is list and all(type(x) is str for x in value['contextLimits']), 'map context limits type')
    if value['position'] is None:
        _require(value['center'] is None and value['marker'] is None and not value['layers'] and value['source'] is None,'unavailable map must have no point')
        _require(value['contextLimits']==['source-position-unavailable' if value['positionMode']=='fixed-source' else 'mobile-event-position-unavailable'],'unavailable map context reason')
    else:
        _require(value['center']==[value['position']['latitude'],value['position']['longitude']]
                 and canonical_bytes(value['marker'])==canonical_bytes({'anchor':[335,165],'diameter':28,'colors':[0x000000,0xf7f9fc,0xffd166]})
                 and bool(value['layers']) and type(value['source']) is dict
                 and set(value['source'])=={'recipeSha256','worldSha256','corresponding','notices'},'map camera/marker mismatch')
        _require(value['contextLimits']==['source-reference-not-independent-pad-survey','full-camera-small-islands-may-be-subpixel','native-full-scene-not-observed'], 'map context limits')
        from .publisher import _digest
        _digest(value['source']['recipeSha256'])
        _require(value['source']['worldSha256']=='c3791187af0ef51b0d238c156058399fc9603c9974f960eb2889cdbee268a736','unsupported original map source')
