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
from .visual_bridge import build_source, read_ref, put, sha
from .graphics import assemble_visual
from . import native_globe

LAYOUT_REVISION = 'native-04-v1'
ROLE_CANVAS = {'map': (390,390), 'rocket': (54,124),
               'operator': (20,38), 'origin': (20,12)}
MAX_OBJECTS = 32
MAX_RASTER_BYTES = 98304


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


def _single_profile(files, old, old_catalog, *, globe=False):
    """Render one source selection into native raster primitives."""
    files=dict(files)
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
    feed=deepcopy(old);feed.update(visualSelection=root,nativeTransfer=transfer)
    catalog=deepcopy(old_catalog);catalog['visualSelection']=root
    return files,feed,catalog,rendered


def _view_paths(files, selection, transfer):
    paths={transfer['path']}
    if selection is not None:
        scene=loads_json(read_ref(selection,files));paths.add(selection['path'])
        for binding in scene['roles'].values():
            if binding is None:continue
            ref=binding['descriptor'];paths.add(ref['path'])
            paths.update(r['path'] for r in loads_json(read_ref(ref,files))['shards'])
    return paths


def build_artifact(*args,**kwargs):
    source,base,catalog=build_source(*args,**kwargs)
    files,feed,catalog,rendered=_single_profile(source,base,catalog)
    if feed['visualSelection'] is not None:
        alternate,globe,_,globe_rendered=_single_profile(source,base,catalog,globe=True)
        feed.update(globeSelection=globe['visualSelection'],globeTransfer=globe['nativeTransfer'])
        for path in _view_paths(alternate,feed['globeSelection'],feed['globeTransfer']):
            files[path]=alternate[path]
        rendered['globe']=globe_rendered.get('map')
    return files,feed,catalog
