"""Explicit wire3 / SFR1 finite lossless native profile.

The source bridge/SFV files stay unchanged and delivered. Rasterization uses the
existing public rsvg-convert; PNG reading and the finite codec use only stdlib.
No image request object, executable drawing recipe or lossy palette is persisted.
"""
from copy import deepcopy
import base64
import re
import struct
import subprocess
import zlib

from .catalog import canonical_bytes, loads_json
from .visual_bridge import (build_artifact as build_v2, validate_artifact as validate_v2,
    validate_feed as validate_feed_v2, read_ref, put, sha, TRANSITION)
from .graphics import assemble_visual
from . import native_globe

FEED_PATH = 'wire3/feed.json'
PROFILE = 'native-raster-v3'
LAYOUT_REVISION = 'native-04-v1'
ROLE_CANVAS = {'map': (390,390), 'rocket': (54,124),
               'operator': (20,38), 'origin': (20,12)}
MAX_OBJECTS = 32
MAX_RASTER_BYTES = 98304
TRANSITION3 = dict(currentMajor=3, previousMajor=2, announcedUtc=1794441600,
                   retainPreviousThroughUtc=1802217600)


def require(ok, message):
    if not ok:
        raise ValueError('native profile: ' + message)


def png_pixels(raw):
    """Read the bounded RGBA8 PNG produced by the pinned local rsvg renderer."""
    require(raw.startswith(b'\x89PNG\r\n\x1a\n'), 'PNG signature')
    at = 8; compressed = bytearray(); width = height = None
    while at < len(raw):
        size = struct.unpack('>I', raw[at:at+4])[0]
        kind = raw[at+4:at+8]; body = raw[at+8:at+8+size]
        require(len(body) == size and zlib.crc32(kind+body) & 0xffffffff == struct.unpack('>I', raw[at+8+size:at+12+size])[0], 'PNG CRC')
        if kind == b'IHDR':
            width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', body)
            require(1 <= width <= 390 and 1 <= height <= 390 and depth==8 and color in (2,6) and (compression,filtering,interlace)==(0,0,0), 'RGB/RGBA8 PNG required')
            channels=3 if color==2 else 4
        elif kind == b'IDAT': compressed.extend(body)
        elif kind == b'IEND': break
        at += size + 12
    require(width is not None and len(compressed) <= 1048576, 'PNG bound')
    stride = width*channels
    dec = zlib.decompressobj(); scan = dec.decompress(compressed, (stride+1)*height+1)
    require(dec.eof and not dec.unconsumed_tail and len(scan)==(stride+1)*height, 'PNG inflate bound')
    result = bytearray(); previous = bytearray(stride)
    for y in range(height):
        mode=scan[y*(stride+1)]; row=bytearray(scan[y*(stride+1)+1:(y+1)*(stride+1)])
        require(mode <= 4, 'PNG filter')
        for x in range(stride):
            a=row[x-channels] if x>=channels else 0; b=previous[x]; c=previous[x-channels] if x>=channels else 0
            if mode==1: delta=a
            elif mode==2: delta=b
            elif mode==3: delta=(a+b)//2
            elif mode==4:
                p=a+b-c; pa=abs(p-a); pb=abs(p-b); pc=abs(p-c)
                delta=a if pa<=pb and pa<=pc else b if pb<=pc else c
            else: delta=0
            row[x]=(row[x]+delta)&255
        result.extend(row); previous=row
    if channels==3:result=bytearray(c for x in range(width*height) for c in (*result[x*3:x*3+3],255))
    return width,height,bytes(result)


def rasterize(visuals, width, height, *, opaque=False):
    draws=[]
    if opaque: draws.append('<defs><clipPath id="round"><circle cx="195" cy="195" r="195"/></clipPath></defs><rect width="390" height="390" fill="black"/><g clip-path="url(#round)">')
    for v in visuals:
        require(v[7]==[0,[]], "SFR1 static source only; motion needs explicit sourceCanvas/new revision")
        scale=min(width/v[3][0],height/v[3][1])
        dx=(width-v[3][0]*scale)/2;dy=(height-v[3][1]*scale)/2
        for op in v[6]:
            points=' '.join(f'{dx+(v[5][i]%16384)*scale/32:.4f},{dy+(v[5][i]//16384)*scale/32:.4f}' for i in op[2])
            draws.append(f'<polygon fill="#{v[4][op[1]]:06x}" points="{points}"/>')
    if opaque:draws.append('</g>')
    svg=(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'+''.join(draws)+'</svg>').encode()
    proc=subprocess.run(['rsvg-convert'],input=svg,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30)
    require(proc.returncode==0,'rsvg-convert failed')
    w,h,pixels=png_pixels(proc.stdout)
    require((w,h)==(width,height),'raster dimensions')
    png=proc.stdout
    return pixels,png,svg


def _row_tokens(row, previous, channels):
    width=len(row)//channels; x=0; out=bytearray()
    while x<width:
        copy=0
        while copy<128 and x+copy<width and row[(x+copy)*channels:(x+copy+1)*channels]==previous[(x+copy)*channels:(x+copy+1)*channels]: copy+=1
        run=1; color=row[x*channels:(x+1)*channels]
        while run<128 and x+run<width and row[(x+run)*channels:(x+run+1)*channels]==color: run+=1
        if copy and copy*4>=run:
            out.append(127+copy);x+=copy
        else:
            out.append(run-1);out.extend(color);x+=run
    return out


def encode_raster(pixels,width,height,channels=4):
    require(type(width) is int and type(height) is int and 1<=width<=390 and 1<=height<=390,'canvas bound')
    require(channels in (3,4) and len(pixels)==width*height*channels,'pixel length')
    chunks=[];start=0;row=0;data=bytearray();previous=bytes(width*channels)
    while row<height:
        current=pixels[row*width*channels:(row+1)*width*channels]
        encoded=_row_tokens(current,previous,channels)
        header=f'SFR1:{start}:{row-start+1}:'
        if data and len(header)+4*((len(data)+len(encoded)+2)//3)>4096:
            chunks.append(f'SFR1:{start}:{row-start}:'.encode()+base64.b64encode(data))
            start=row;data=bytearray();previous=bytes(width*channels)
            continue
        data.extend(encoded);require(len(header)+4*((len(data)+2)//3)<=4096,'single row bound')
        previous=current;row+=1
    if data: chunks.append(f'SFR1:{start}:{row-start}:'.encode()+base64.b64encode(data))
    require(len(chunks)<=MAX_OBJECTS and sum(map(len,chunks))<=MAX_RASTER_BYTES,'raster capacity')
    return chunks


def decode_raster(chunks,width,height,channels):
    """Strict reference decoder. Test oracle independently reconstructs tokens."""
    require(type(width) is int and type(height) is int and 1<=width<=390 and 1<=height<=390 and channels in (3,4),'canvas bound')
    output=bytearray();next_y=0
    for raw in chunks:
        require(type(raw) is bytes and 1<=len(raw)<=4096,'chunk byte bound')
        fields=raw.split(b':',3)
        require(len(fields)==4 and fields[0]==b'SFR1' and re.fullmatch(b'0|[1-9][0-9]*',fields[1]) and re.fullmatch(b'[1-9][0-9]*',fields[2]),'chunk grammar')
        start,rows=int(fields[1]),int(fields[2]);require(start==next_y and rows<=390 and start+rows<=height,'row order')
        data=base64.b64decode(fields[3],validate=True);require(base64.b64encode(data)==fields[3],'base64 canonical')
        at=0;previous=bytes(width*channels)
        for y in range(rows):
            row=bytearray();x=0
            while x<width:
                require(at<len(data),'truncated token');token=data[at];at+=1;length=(token&127)+1
                require(x+length<=width,'row overflow')
                if token>=128:row.extend(previous[x*channels:(x+length)*channels])
                else:
                    require(at+channels<=len(data),'truncated color')
                    row.extend(data[at:at+channels]*length);at+=channels
                x+=length
            previous=bytes(row);output.extend(row)
        require(at==len(data),'trailing token');next_y+=rows
    require(next_y==height,'incomplete raster')
    return bytes(output)


def _asset(files,ref):
    d=loads_json(read_ref(ref,files))
    require(d['type']=='sfv','SFV source')
    parts=[read_ref(r,files,prefix='objects') for r in d['shards']]
    return assemble_visual(parts,d['animation']),d


def _map_visuals(files,desc):
    out=[]
    for page in desc['layers']:
        for ref in loads_json(read_ref(page,files))['layers']:
            out.append(_asset(files,ref)[0])
    return out


def _single_profile(files, *, globe=False):
    """Append wire3 to an already valid exact dual producer closure."""
    validate_v2(files);files=dict(files)
    old=loads_json(files['wire2/feed.json']); old_catalog=loads_json(files[old['catalogPath']])
    sel=None if old['visualSelection'] is None else loads_json(read_ref(old['visualSelection'],files))
    root=None;rendered={}
    if sel is not None:
        raster_roles={k:None for k in ('map','rocket','operator','origin')};map_source=None
        for role in raster_roles:
            source_role='geography' if role=='map' else role
            binding=sel['roles'][source_role]
            if binding is None:continue
            desc=loads_json(read_ref(binding['descriptor'],files))
            if role=='map':
                map_source=desc
                if desc['position'] is None:continue
                visuals=native_globe.visuals(files,desc) if globe else _map_visuals(files,desc);width=height=390;channels=3
            else:
                visual,desc=_asset(files,binding['descriptor']);visuals=[visual]
                width,height=ROLE_CANVAS[role];channels=4
            rgba,png,svg=rasterize(visuals,width,height,opaque=role=='map')
            pixels=bytes(c for i,c in enumerate(rgba) if channels==4 or i%4!=3)
            chunks=encode_raster(pixels,width,height,channels);refs=[]
            for raw in chunks:
                digest=sha(raw);path=f'rasters/{digest}.sfr';files[path]=raw;refs.append(dict(path=path,sha256=digest,decodedBytes=len(raw)))
            value=dict(type='raster',schemaVersion=1,rendererProfile='SFR1',canvas=[width,height],channels=channels,
                pixelSha256=sha(pixels),sourceDescriptor=binding['descriptor'],sourceSemanticSha256=None if role=='map' else desc['sha256'],animation=[0,[]] if role=='map' else desc['animation'],shards=refs)
            raster_roles[role]=dict(entityId=binding['entityId'],descriptor=put(files,value))
            rendered[role]=dict(png=png,svg=svg,pixels=pixels)
        root=put(files,dict(type='native-scene',schemaVersion=3,rendererProfile='SFR1',layoutRevision=native_globe.LAYOUT if globe else LAYOUT_REVISION,
            sourceSelection=old['visualSelection'],launchId=sel['launchId'],modelId=sel['modelId'],operatorId=sel['operatorId'],siteId=sel['siteId'],countryId=sel['countryId'],originMode=sel['originMode'],originId=sel['originId'],
            sourcePosition=None if map_source is None else map_source['sourcePosition'],position=None if map_source is None else map_source['position'],positionMode=None if map_source is None else map_source['positionMode'],
            mapDefinitionSha256=None if map_source is None else map_source['definitionSha256'],mapSource=None if map_source is None else map_source['source'],marker=None if map_source is None else map_source['marker'],roles=raster_roles))
    refs=[]
    if root is not None:
        refs.append(root)
        for role in ('map','rocket','operator','origin'):
            binding=raster_roles[role]
            if binding is None:continue
            refs.append(binding['descriptor'])
            refs.extend(loads_json(files[binding['descriptor']['path']])['shards'])
    unique={r['path']:r for r in refs}
    transfer=put(files,dict(type='native-transfer',schemaVersion=1,rendererProfile='SFR1',scene=root,objects=[[1 if r['path'].startswith('rasters/') else 0,r['sha256'],r['decodedBytes']] for r in unique.values()]))
    feed=deepcopy(old);feed.update(schemaVersion=3,rendererProfile='SFR1',compatibility=TRANSITION3,visualSelection=root,nativeTransfer=transfer)
    catalog=deepcopy(old_catalog);catalog.update(schemaVersion=3,projection='selected-display-v3',visualSelection=root)
    raw=canonical_bytes(catalog);feed['catalogDigest']=sha(raw);feed['catalogPath']=f'wire3/catalogs/{sha(raw)}.json';files[feed['catalogPath']]=raw
    files[FEED_PATH]=canonical_bytes(feed)
    require(len(files[FEED_PATH])<=8192,'wire3 feed bound')
    _validate_single(files)
    return files,rendered


def build_artifact(*args,**kwargs):
    files,digest=build_v2(*args,**kwargs)
    files,_=add_profile(files,include_globe=True)
    return files,digest


def validate_feed(raw,*,now=None):
    d=loads_json(raw)
    require(type(raw) is bytes and len(raw)<=8192 and canonical_bytes(d)==raw,'canonical feed bound')
    require(type(d.get('schemaVersion')) is int and d['schemaVersion']==3 and d.get('rendererProfile')=='SFR1' and canonical_bytes(d.get('compatibility'))==canonical_bytes(TRANSITION3),'wire3 profile')
    require(d.get('catalogPath')==f'wire3/catalogs/{d.get("catalogDigest")}.json','wire3 catalog path')
    old=deepcopy(d);old.pop('rendererProfile');old.pop('nativeTransfer');old.pop('globeSelection',None);old.pop('globeTransfer',None);old.update(schemaVersion=2,compatibility=TRANSITION,catalogPath=f'wire2/catalogs/{d["catalogDigest"]}.json')
    from .visual_bridge import validate_ref
    validate_ref(d['nativeTransfer'])
    require(('globeSelection' in d)==('globeTransfer' in d),'complete optional globe selection')
    if 'globeSelection' in d:
        require(d['visualSelection'] is not None,'globe needs selected scene')
        validate_ref(d['globeSelection']);validate_ref(d['globeTransfer'])
        require(d['globeSelection']!=d['visualSelection'] and d['globeTransfer']!=d['nativeTransfer'],'alternate view references must differ')
    validate_feed_v2(canonical_bytes(old),now=now)
    return d


def _validate_single(files):
    """Admit complete old closure and source-bound exact pixels for wire3."""
    old_files={p:r for p,r in files.items() if not p.startswith(('wire3/','rasters/'))}
    # Raster and native-scene descriptors are new; old v2 requires exact closure.
    old_refs=set()
    def visit(ref):
        if not isinstance(ref,dict):return
        if set(ref)=={'path','sha256','decodedBytes'}:
            path=ref['path']
            if path in old_refs:return
            old_refs.add(path)
            if path.endswith('.json'):
                try:walk(loads_json(files[path]))
                except (ValueError,KeyError):pass
        else:
            for v in ref.values():walk(v)
    def walk(v):
        if isinstance(v,dict):visit(v)
        elif isinstance(v,list):
            for x in v:walk(x)
    feed2=loads_json(files['wire2/feed.json']);walk(loads_json(files[feed2['catalogPath']]));walk(feed2)
    old_files={p:r for p,r in old_files.items() if not p.startswith('descriptors/') or p in old_refs}
    validate_v2(old_files)
    feed=validate_feed(files.get(FEED_PATH));catraw=files.get(feed['catalogPath'])
    require(type(catraw) is bytes and len(catraw)<=4096 and sha(catraw)==feed['catalogDigest'],'catalog raw pin')
    loads_json(catraw);expected=loads_json(old_files[feed2['catalogPath']]);expected.update(schemaVersion=3,projection='selected-display-v3',visualSelection=feed['visualSelection'])
    require(catraw==canonical_bytes(expected),'catalog agreement')
    expected_feed=deepcopy(feed2);expected_feed.update(schemaVersion=3,rendererProfile='SFR1',compatibility=TRANSITION3,visualSelection=feed['visualSelection'],nativeTransfer=feed['nativeTransfer'],catalogDigest=feed['catalogDigest'],catalogPath=feed['catalogPath'])
    require(canonical_bytes(expected_feed)==files[FEED_PATH],'old/new schedule agreement')
    new_paths={FEED_PATH,feed['catalogPath'],feed['nativeTransfer']['path']};total=0;objects=0
    if feed['visualSelection'] is not None:
        ref=feed['visualSelection'];new_paths.add(ref['path']);scene=loads_json(read_ref(ref,files))
        require(set(scene)=={'type','schemaVersion','rendererProfile','layoutRevision','sourceSelection','launchId','modelId','operatorId','siteId','countryId','originMode','originId','sourcePosition','position','positionMode','mapDefinitionSha256','mapSource','marker','roles'} and scene['type']=='native-scene' and type(scene['schemaVersion']) is int and scene['schemaVersion']==3 and scene['rendererProfile']=='SFR1' and scene['layoutRevision'] in (LAYOUT_REVISION,native_globe.LAYOUT),'scene grammar/layout revision')
        original=loads_json(read_ref(feed2['visualSelection'],old_files))
        require(scene['sourceSelection']==feed2['visualSelection'],'source selection pin')
        for key in ('launchId','modelId','operatorId','siteId','countryId','originMode','originId'):require(scene[key]==original[key],'selected identity')
        map_role=original['roles']['geography'];md=None if map_role is None else loads_json(read_ref(map_role['descriptor'],old_files))
        for a,b in [('sourcePosition','sourcePosition'),('position','position'),('positionMode','positionMode'),('mapDefinitionSha256','definitionSha256'),('mapSource','source'),('marker','marker')]:require(scene[a]==(None if md is None else md[b]),'map source agreement')
        require(set(scene['roles'])=={'map','rocket','operator','origin'},'roles grammar')
        for role,binding in scene['roles'].items():
            src=original['roles']['geography' if role=='map' else role]
            if binding is None:
                require(src is None or role=='map' and md['position'] is None,'missing selected role');continue
            require(set(binding)=={'entityId','descriptor'} and src is not None and binding['entityId']==src['entityId'],'role identity')
            rd=loads_json(read_ref(binding['descriptor'],files));new_paths.add(binding['descriptor']['path'])
            require(set(rd)=={'type','schemaVersion','rendererProfile','canvas','channels','pixelSha256','sourceDescriptor','sourceSemanticSha256','animation','shards'} and rd['type']=='raster' and type(rd['schemaVersion']) is int and rd['schemaVersion']==1 and rd['rendererProfile']=='SFR1','raster grammar')
            require(rd['canvas']==list(ROLE_CANVAS[role]) and rd['channels']==(3 if role=='map' else 4) and type(rd['channels']) is int and rd['sourceDescriptor']==src['descriptor'],'raster role/source')
            visuals=(native_globe.visuals(old_files,md) if scene['layoutRevision']==native_globe.LAYOUT else _map_visuals(old_files,md)) if role=='map' else [_asset(old_files,src['descriptor'])[0]]
            sd=None if role=='map' else _asset(old_files,src['descriptor'])[1]['sha256'];require(rd['sourceSemanticSha256']==sd,'semantic source pin')
            require(rd['animation']==[0,[]] and (role=='map' or _asset(old_files,src['descriptor'])[1]['animation']==[0,[]]),'SFR1 static animation/source agreement')
            chunks=[]
            require(type(rd['shards']) is list and 1<=len(rd['shards'])<=MAX_OBJECTS,'shard count')
            for r in rd['shards']:
                require(type(r) is dict and set(r)=={'path','sha256','decodedBytes'} and type(r['decodedBytes']) is int and 1<=r['decodedBytes']<=4096 and r['path']==f'rasters/{r["sha256"]}.sfr','raster reference')
                raw=files.get(r['path']);require(type(raw) is bytes and len(raw)==r['decodedBytes'] and sha(raw)==r['sha256'],'raster raw pin');chunks.append(raw);new_paths.add(r['path']);total+=len(raw);objects+=1
            pixels=decode_raster(chunks,*rd['canvas'],rd['channels']);require(sha(pixels)==rd['pixelSha256'],'pixel digest')
            expected,_,_=rasterize(visuals,*rd['canvas'],opaque=role=='map')
            if role=='map':expected=bytes(c for i,c in enumerate(expected) if i%4!=3)
            require(pixels==expected,'source pixel equality')
    index=loads_json(read_ref(feed['nativeTransfer'],files));refs=[]
    require(set(index)=={'type','schemaVersion','rendererProfile','scene','objects'} and index['type']=='native-transfer' and type(index['schemaVersion']) is int and index['schemaVersion']==1 and index['rendererProfile']=='SFR1' and index['scene']==feed['visualSelection'],'transfer index grammar')
    if feed['visualSelection'] is not None:
        refs.append(feed['visualSelection'])
        for role in ('map','rocket','operator','origin'):
            binding=scene['roles'][role]
            if binding is not None:
                refs.append(binding['descriptor']);refs.extend(loads_json(files[binding['descriptor']['path']])['shards'])
    require(index['objects']==[[1 if r['path'].startswith('rasters/') else 0,r['sha256'],r['decodedBytes']] for r in {r['path']:r for r in refs}.values()],'exact transfer closure')
    require(len(index['objects'])<=40 and sum(r[2] for r in index['objects'])<=114688,'transfer bounds')
    require(total<=MAX_RASTER_BYTES and objects<=MAX_OBJECTS,'complete raster bounds')
    require(set(files)==set(old_files)|new_paths,'complete profile file closure')
    require(len(files)<=256 and sum(map(len,files.values()))<=1048576,'complete artifact bound')
    return feed


def _view_paths(files, selection, transfer):
    paths={transfer['path']}
    if selection is not None:
        scene=loads_json(read_ref(selection,files));paths.add(selection['path'])
        for binding in scene['roles'].values():
            if binding is None:continue
            ref=binding['descriptor'];paths.add(ref['path'])
            paths.update(r['path'] for r in loads_json(read_ref(ref,files))['shards'])
    return paths


def add_profile(files, *, include_globe=False):
    """Opt-in typed alternate view; legacy calls retain every frozen SFR1 byte."""
    primary,rendered=_single_profile(files)
    feed=loads_json(primary[FEED_PATH])
    if not include_globe or feed['visualSelection'] is None:return primary,rendered
    alternate,globe_rendered=_single_profile(files,globe=True)
    globe_feed=loads_json(alternate[FEED_PATH])
    feed.update(globeSelection=globe_feed['visualSelection'],globeTransfer=globe_feed['nativeTransfer'])
    for path in _view_paths(alternate,feed['globeSelection'],feed['globeTransfer']):
        primary[path]=alternate[path]
    primary[FEED_PATH]=canonical_bytes(feed)
    require(len(primary[FEED_PATH])<=8192,'wire3 feed bound')
    validate_artifact(primary)
    rendered['globe']=globe_rendered.get('map')
    return primary,rendered


def validate_artifact(files):
    """Both optional view closures must independently pass, before publication."""
    feed=validate_feed(files.get(FEED_PATH))
    if 'globeSelection' not in feed:
        result=_validate_single(files)
        if feed['visualSelection'] is not None:
            require(loads_json(read_ref(feed['visualSelection'],files))['layoutRevision']==LAYOUT_REVISION,'default must remain flat')
        return result
    primary=_view_paths(files,feed['visualSelection'],feed['nativeTransfer'])
    alternate=_view_paths(files,feed['globeSelection'],feed['globeTransfer'])
    oldfeed=deepcopy(feed);oldfeed.pop('globeSelection');oldfeed.pop('globeTransfer')
    flat={p:r for p,r in files.items() if p not in alternate-primary}
    flat[FEED_PATH]=canonical_bytes(oldfeed);_validate_single(flat)
    globe={p:r for p,r in files.items() if p not in primary-alternate and p!=feed['catalogPath']}
    cat=loads_json(files[feed['catalogPath']]);cat['visualSelection']=feed['globeSelection']
    raw=canonical_bytes(cat);oldfeed.update(visualSelection=feed['globeSelection'],nativeTransfer=feed['globeTransfer'],catalogDigest=sha(raw),catalogPath=f'wire3/catalogs/{sha(raw)}.json')
    globe[oldfeed['catalogPath']]=raw;globe[FEED_PATH]=canonical_bytes(oldfeed);_validate_single(globe)
    flat_scene=loads_json(read_ref(feed['visualSelection'],files));globe_scene=loads_json(read_ref(feed['globeSelection'],files))
    require(flat_scene['layoutRevision']==LAYOUT_REVISION and globe_scene['layoutRevision']==native_globe.LAYOUT,'typed view layout')
    for key in flat_scene:
        if key not in ('layoutRevision','roles'):require(flat_scene[key]==globe_scene[key],'view source identity agreement')
    for role in ('rocket','operator','origin'):require(flat_scene['roles'][role]==globe_scene['roles'][role],'shared artwork agreement')
    require(len(files)<=256 and sum(map(len,files.values()))<=1048576,'complete artifact bound')
    return feed
