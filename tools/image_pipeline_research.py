#!/usr/bin/env python3
"""Inspect current SpaceFox image sources and compare bounded SFR1 token choices.

This is a host study: it does not install a codec on the watch. Inputs are
source-derived PNG resources and the retained publisher pixel references.
"""
import argparse
import base64
import csv
import gzip
import hashlib
import json
import sys
from pathlib import Path
import time
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.spacefox import native_profile as native

RES = 'watchface/resources/drawables/'
# Partition by actual asset identity, frozen before selecting thresholds.
CORPUS = [
    ('current-map', 'map', 'train', 'tests/fixtures/sfr1m-current/map.rgba.gz', 390, 390, 3),
    ('current-rocket', 'rocket', 'train', 'tests/fixtures/sfr1m-current/rocket.rgba.gz', 54, 124, 4),
    ('current-flag', 'flag', 'train', 'tests/fixtures/sfr1m-current/siteCountry.rgba.gz', 20, 12, 4),
] + [(f'map-{i}', 'map', 'eval' if i in (8, 15) else 'train', RES+f'MapView{i}.png', 195, 195, 3) for i in (0, 1, 4, 8, 12, 15)] \
  + [(f'low-{i}', 'low', 'eval' if i == 8 else 'train', RES+f'AodMap{i}.png', 390, 390, 3) for i in (0, 1, 4, 8)] \
  + [(name, 'flag' if name.startswith('flag-') else 'rocket', 'eval' if name in ('electron','ariane-64','flag-nz') else 'train', RES+'art_'+name+'.png', 20 if name.startswith('flag-') else 54, 12 if name.startswith('flag-') else 124, 4) for name in ('falcon-9','falcon-heavy','ariane-62','ariane-64','electron','generic','flag-us','flag-fr','flag-nz','flag-europe')]


def digest(b):
    return hashlib.sha256(b).hexdigest()


def inventory():
    """Include all retained map tiles, LOW outlines and role artwork resources."""
    rows=list(CORPUS)
    known={row[3] for row in rows}
    for path in sorted((ROOT / RES).glob('*.png')):
        name=path.name
        if name.startswith('MapView') or name.startswith('MapExtra'):
            kind='map'
        elif name.startswith('AodMap'):
            kind='low'
        elif name.startswith('art_flag-'):
            kind='flag'
        elif name.startswith('art_') and not name.startswith('art_company-'):
            kind='rocket'
        else:
            continue
        rel=path.relative_to(ROOT).as_posix()
        if rel in known: continue
        w,h,rgba=native.png_pixels(path.read_bytes())
        channels=3 if kind in ('map','low') else 4
        rows.append((path.stem,kind,'eval',rel,w,h,channels))
    return rows


def load(row):
    name, kind, split, path, w, h, ch = row
    raw = (ROOT / path).read_bytes()
    if path.endswith('.gz'):
        pixels = gzip.decompress(raw)
    else:
        pw, ph, rgba = native.png_pixels(raw)
        if (pw, ph) != (w, h):
            raise ValueError('unexpected dimensions: '+path)
        pixels = rgba if ch == 4 else bytes(v for i, v in enumerate(rgba) if i % 4 != 3)
    if len(pixels) != w*h*ch:
        raise ValueError('unexpected pixel length: '+path)
    return dict(name=name, kind=kind, split=split, path=path, width=w, height=h,
                channels=ch, input_sha256=digest(raw), pixel_sha256=digest(pixels), pixels=pixels)


def row_tokens(row, previous, channels, numerator, denominator):
    width = len(row)//channels
    x = 0
    out = bytearray()
    while x < width:
        copy = 0
        while copy < 128 and x+copy < width and row[(x+copy)*channels:(x+copy+1)*channels] == previous[(x+copy)*channels:(x+copy+1)*channels]:
            copy += 1
        color = row[x*channels:(x+1)*channels]
        run = 1
        while run < 128 and x+run < width and row[(x+run)*channels:(x+run+1)*channels] == color:
            run += 1
        if copy and copy*numerator >= run*denominator:
            out.append(127+copy); x += copy
        else:
            out.append(run-1); out.extend(color); x += run
    return out


def pack(pixels, width, height, channels, numerator=4, denominator=1):
    if not (1 <= width <= 390 and 1 <= height <= 390 and channels in (3, 4) and len(pixels) == width*height*channels and numerator > 0 and denominator > 0):
        raise ValueError('invalid input')
    chunks=[]; start=0; y=0; data=bytearray(); previous=bytes(width*channels)
    while y < height:
        current=pixels[y*width*channels:(y+1)*width*channels]
        encoded=row_tokens(current, previous, channels, numerator, denominator)
        header=f'SFR1:{start}:{y-start+1}:'
        if data and len(header)+4*((len(data)+len(encoded)+2)//3)>4096:
            chunks.append(f'SFR1:{start}:{y-start}:'.encode()+base64.b64encode(data))
            start=y; data=bytearray(); previous=bytes(width*channels); continue
        data.extend(encoded)
        if len(header)+4*((len(data)+2)//3)>4096:
            raise ValueError('single row exceeds shard')
        previous=current; y+=1
    if data:
        chunks.append(f'SFR1:{start}:{y-start}:'.encode()+base64.b64encode(data))
    if len(chunks)>32 or sum(map(len,chunks))>98304:
        raise ValueError('raster capacity')
    return chunks



def optimal_row(row, previous, channels):
    """Minimum token bytes then token count for the exact RUN/COPY grammar."""
    a=list(zip(*(iter(row),)*channels)); b=list(zip(*(iter(previous),)*channels))
    width=len(a); runs=[0]*(width+1); copies=[0]*(width+1)
    for x in range(width-1,-1,-1):
        runs[x]=min(128,1+(runs[x+1] if x+1<width and a[x]==a[x+1] else 0))
        copies[x]=min(128,1+copies[x+1]) if a[x]==b[x] else 0
    cost=[(0,0)]*(width+1); choice=[None]*width
    for x in range(width-1,-1,-1):
        best=None
        for tag, maximum, byte_cost in ((0,runs[x],1+channels),(1,copies[x],1)):
            for length in range(1,maximum+1):
                suffix=cost[x+length]; key=(byte_cost+suffix[0],1+suffix[1],tag,-length)
                if best is None or key<best:best=key
        cost[x]=best[:2];choice[x]=(best[2],-best[3])
    out=bytearray();x=0
    while x<width:
        tag,length=choice[x]
        if tag:out.append(127+length)
        else:out.append(length-1);out.extend(a[x])
        x+=length
    return out


def pack_optimal(pixels,width,height,channels):
    chunks=[];start=0;y=0;data=bytearray();previous=bytes(width*channels)
    while y<height:
        current=pixels[y*width*channels:(y+1)*width*channels]
        encoded=optimal_row(current,previous,channels)
        header=f'SFR1:{start}:{y-start+1}:'
        if data and len(header)+4*((len(data)+len(encoded)+2)//3)>4096:
            chunks.append(f'SFR1:{start}:{y-start}:'.encode()+base64.b64encode(data))
            start=y;data=bytearray();previous=bytes(width*channels);continue
        data.extend(encoded)
        if len(header)+4*((len(data)+2)//3)>4096:raise ValueError('single row exceeds shard')
        previous=current;y+=1
    if data:chunks.append(f'SFR1:{start}:{y-start}:'.encode()+base64.b64encode(data))
    if len(chunks)>32 or sum(map(len,chunks))>98304:raise ValueError('raster capacity')
    return chunks


def optimal_study(out):
    out.mkdir(parents=True,exist_ok=True);rows=[]
    for item in CORPUS:
        a=load(item);p=a['pixels'];w=a['width'];h=a['height'];c=a['channels']
        row={k:a[k] for k in ('name','kind','split','pixel_sha256')}
        for name,fn in [('baseline',lambda:pack(p,w,h,c)),('optimal',lambda:pack_optimal(p,w,h,c))]:
            start=time.perf_counter_ns()
            try:
                chunks=fn(); elapsed=(time.perf_counter_ns()-start)/1e6
                if independent_decode(chunks,w,h,c)!=p:raise ValueError('pixel mismatch')
                row[name]={'wire_bytes':sum(map(len,chunks)),'shards':len(chunks),'encode_ms':round(elapsed,3)}
            except ValueError as e:
                if str(e) not in ('single row exceeds shard','raster capacity'):raise
                row[name]={'filtered':str(e)}
        rows.append(row)
    (out/'optimal.json').write_text(json.dumps(rows,indent=2)+'\n')

def independent_decode(chunks, width, height, channels):
    """Independent cursor decoder; reject malformed/noncanonical/trailing input."""
    output=bytearray(); expected_y=0
    for chunk in chunks:
        parts=chunk.split(b':')
        if len(parts)!=4 or parts[0]!=b'SFR1' or not parts[1].isdigit() or not parts[2].isdigit():
            raise ValueError('header')
        start=int(parts[1]); nrows=int(parts[2])
        if str(start).encode()!=parts[1] or str(nrows).encode()!=parts[2] or start!=expected_y or nrows<1 or start+nrows>height or len(chunk)>4096:
            raise ValueError('bounds')
        data=base64.b64decode(parts[3], validate=True)
        if base64.b64encode(data)!=parts[3]: raise ValueError('base64')
        pos=0; prev=bytes(width*channels)
        for _ in range(nrows):
            row=bytearray()
            while len(row)<width*channels:
                if pos>=len(data): raise ValueError('truncated token')
                token=data[pos]; pos+=1; count=(token&127)+1; at=len(row)
                if at+count*channels>width*channels: raise ValueError('row overflow')
                if token&128:
                    row.extend(prev[at:at+count*channels])
                else:
                    color=data[pos:pos+channels]
                    if len(color)!=channels: raise ValueError('truncated color')
                    pos+=channels; row.extend(color*count)
            output.extend(row); prev=bytes(row)
        if pos!=len(data): raise ValueError('trailing data')
        expected_y+=nrows
    if expected_y!=height: raise ValueError('incomplete')
    return bytes(output)


def evaluate(asset, n, d):
    start=time.perf_counter_ns()
    chunks=pack(asset['pixels'],asset['width'],asset['height'],asset['channels'],n,d)
    encode_ns=time.perf_counter_ns()-start
    start=time.perf_counter_ns()
    reconstructed=independent_decode(chunks,asset['width'],asset['height'],asset['channels'])
    decode_ns=time.perf_counter_ns()-start
    if reconstructed!=asset['pixels']: raise ValueError('pixel mismatch '+asset['name'])
    return dict(wire_bytes=sum(map(len,chunks)), shards=len(chunks), token_bytes=sum(len(base64.b64decode(c.split(b':')[3])) for c in chunks), encode_ms=round(encode_ns/1e6,3), decode_ms=round(decode_ns/1e6,3))



def qoi_encode(pixels, channels):
    """QOI data stream, with RGBA semantics and standard 64-entry index."""
    previous=(0,0,0,255); index=[(0,0,0,0)]*64; out=bytearray(); run=0
    tuples=list(zip(*(iter(pixels),)*channels))
    for i,p in enumerate(tuples):
        px=p if channels==4 else p+(255,)
        if px==previous:
            run+=1
            if run==62 or i==len(tuples)-1: out.append(0xc0|(run-1));run=0
            continue
        if run: out.append(0xc0|(run-1));run=0
        slot=(px[0]*3+px[1]*5+px[2]*7+px[3]*11)%64
        if index[slot]==px: out.append(slot)
        else:
            index[slot]=px
            if px[3]==previous[3]:
                dr=px[0]-previous[0];dg=px[1]-previous[1];db=px[2]-previous[2]
                if -2<=dr<=1 and -2<=dg<=1 and -2<=db<=1: out.append(0x40|((dr+2)<<4)|((dg+2)<<2)|(db+2))
                elif -32<=dg<=31 and -8<=dr-dg<=7 and -8<=db-dg<=7:
                    out.extend((0x80|(dg+32),((dr-dg+8)<<4)|(db-dg+8)))
                else: out.append(0xfe);out.extend(px[:3])
            else: out.append(0xff);out.extend(px)
        previous=px
    return bytes(out)


def qoi_decode(data, count, channels):
    index=[(0,0,0,0)]*64; px=(0,0,0,255); out=bytearray(); at=0; produced=0
    while produced<count:
        if at>=len(data): raise ValueError('truncated QOI')
        op=data[at];at+=1;run=1
        if op==0xfe:
            if at+3>len(data):raise ValueError('truncated QOI RGB')
            px=tuple(data[at:at+3])+(px[3],);at+=3
        elif op==0xff:
            if at+4>len(data):raise ValueError('truncated QOI RGBA')
            px=tuple(data[at:at+4]);at+=4
        elif op&0xc0==0: px=index[op]
        elif op&0xc0==0x40: px=((px[0]+((op>>4)&3)-2)&255,(px[1]+((op>>2)&3)-2)&255,(px[2]+(op&3)-2)&255,px[3])
        elif op&0xc0==0x80:
            if at>=len(data):raise ValueError('truncated QOI luma')
            delta=(op&63)-32; v=data[at];at+=1
            px=((px[0]+delta+(v>>4)-8)&255,(px[1]+delta)&255,(px[2]+delta+(v&15)-8)&255,px[3])
        else: run=(op&63)+1
        if produced+run>count: raise ValueError('QOI overflow')
        index[(px[0]*3+px[1]*5+px[2]*7+px[3]*11)%64]=px
        for _ in range(run):out.extend(px[:channels])
        produced+=run
    if at!=len(data): raise ValueError('QOI trailing data')
    return bytes(out)


def family_sizes(a):
    raw=a['pixels'];w=a['width'];h=a['height'];ch=a['channels']
    # Exact lossless row-up filter with an independent reversal.
    stride=w*ch; filt=bytearray();prev=bytes(stride)
    for y in range(h):
        row=raw[y*stride:(y+1)*stride]
        filt.extend((v-prev[i])&255 for i,v in enumerate(row));prev=row
    c=zlib.compress(raw,9); cf=zlib.compress(filt,9)
    if zlib.decompress(c)!=raw: raise ValueError('zlib mismatch')
    decoded=zlib.decompress(cf);back=bytearray();prev=bytes(stride)
    for y in range(h):
        r=decoded[y*stride:(y+1)*stride];row=bytes((v+prev[i])&255 for i,v in enumerate(r));back.extend(row);prev=row
    if bytes(back)!=raw:raise ValueError('row predictor mismatch')
    q=qoi_encode(raw,ch)
    if qoi_decode(q,w*h,ch)!=raw:raise ValueError('QOI mismatch')
    pixels=list(zip(*(iter(raw),)*ch)); palette=sorted(set(pixels)); packed=None
    if len(palette)<=256:
        bits=max(1,(len(palette)-1).bit_length()); lookup={p:i for i,p in enumerate(palette)}; acc=0; nbits=0; encoded=bytearray()
        for p in pixels:
            acc=(acc<<bits)|lookup[p];nbits+=bits
            while nbits>=8:
                nbits-=8;encoded.append((acc>>nbits)&255);acc &= (1<<nbits)-1
        if nbits:encoded.append(acc<<(8-nbits))
        # Independent bit cursor and exact palette byte reconstruction.
        recovered=bytearray()
        for i in range(len(pixels)):
            bit=i*bits;v=0
            for j in range(bits):v=(v<<1)|((encoded[(bit+j)//8]>>(7-(bit+j)%8))&1)
            recovered.extend(palette[v])
        if bytes(recovered)!=raw:raise ValueError('palette mismatch')
        packed=len(encoded)+len(palette)*ch
    return dict(name=a['name'],kind=a['kind'],split=a['split'],raw_bytes=len(raw),unique_colors=len(palette),packed_palette_bytes=packed,zlib_bytes=len(c),row_up_deflate_bytes=len(cf),qoi_file_estimate_bytes=len(q)+22,qoi_file_base64_estimate_bytes=len(base64.b64encode(bytes(len(q)+22))),native_decoder='not implemented',source_png_bytes=(ROOT/a['path']).stat().st_size if a['path'].endswith('.png') else None)

def study(out):
    out.mkdir(parents=True,exist_ok=True)
    assets=[load(x) for x in inventory()]
    search_names={x[0] for x in CORPUS}
    search_assets=[a for a in assets if a['name'] in search_names]
    rows=[]; cache={}
    def run(gen, configs, subset):
        for n,d in configs:
            for a in subset:
                key=(a['pixel_sha256'],a['width'],a['height'],a['channels'],n,d)
                if key not in cache:
                    try: cache[key]=evaluate(a,n,d)
                    except ValueError as e:
                        if str(e) not in ('single row exceeds shard','raster capacity'): raise
                        cache[key]={'filtered':str(e)}
                rows.append(dict(generation=gen,config=f'{n}/{d}',name=a['name'],kind=a['kind'],split=a['split'],**cache[key]))
    train=[a for a in search_assets if a['split']=='train']
    # Baseline is executed and recorded before any ranking.
    run('baseline',[(4,1)],assets)
    # Diverse local decision weights, followed by perturbations around best weights.
    first=[(i,2) for i in (1,2,3,4,5,6,8,10,12,16,20,24,32,40,48,64)]
    run('generation-1',first,train)
    def rank(gen):
        totals={}
        for r in rows:
            if r['generation']==gen:
                k=r['config']; t=totals.setdefault(k,[0,0]);t[0]+=r.get('wire_bytes',0);t[1]+=int('filtered' in r)
        return sorted(totals,key=lambda k:(totals[k][1],totals[k][0],k))
    best=rank('generation-1')[:4]
    second=[]
    for v in best:
        n,d=map(int,v.split('/'))
        for delta in (-1,1):
            pair=(max(1,4*n+delta),4*d)
            if pair not in second: second.append(pair)
    run('generation-2',second,train)
    finalists=[]
    for v in rank('generation-1')[:2]+rank('generation-2')[:2]:
        pair=tuple(map(int,v.split('/')))
        if pair not in finalists: finalists.append(pair)
    run('generation-3-finalists',finalists,assets)
    alternatives=[family_sizes(a) for a in assets]
    manifest=[{k:v for k,v in a.items() if k!='pixels'} for a in assets]
    result=dict(schema=1,description='Host-only SFR1 greedy parameter search; source identities and independent exact decode',assets=manifest,rows=rows,host_families=alternatives,configuration_counts={'generation-1':len(first),'generation-2':len(second),'generation-3-finalists':len(finalists)},filtered=sum('filtered' in r for r in rows))
    (out/'study.json').write_text(json.dumps(result,indent=2)+'\n')
    fields=['generation','config','name','kind','split','wire_bytes','token_bytes','shards','encode_ms','decode_ms','filtered']
    with (out/'study.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
    (out/'report.md').write_text('# Image representation study\n\n'+f"{len(assets)} retained assets; training {len(train)}, held out {len(assets)-len(train)} (including all additional inventory). Configurations: {result['configuration_counts']}; filtered asset/config pairs: {result['filtered']}. Exact decode succeeded for each unfiltered pair.\n\n"+'Training ranking, generation 1: '+', '.join(rank('generation-1'))+'\n\nTraining ranking, generation 2: '+', '.join(rank('generation-2'))+'\n\nQOI is a tested pixel-stream implementation with an independently decoded stream; the reported file size adds 22 standard header/end bytes as an estimate, without emitting a full conforming file. Source PNG size is a separate file measurement, not a watch allocation or transfer cost. Host timings and alternative codecs are not watch performance or supported native formats. CSV records each measured asset/configuration.\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--optimal',action='store_true',help='Run the bounded minimum-token-cost candidate on the frozen search corpus')
    parser.add_argument('--pack-png',type=Path,help='Pack a source-derived RGB/RGBA8 PNG as current SFR1 shards')
    parser.add_argument('--channels',type=int,choices=(3,4),default=4,help='Output RGB or RGBA pixel channels')
    args=parser.parse_args()
    if args.pack_png:
        if args.optimal: parser.error('--optimal and --pack-png are mutually exclusive')
        raw=args.pack_png.read_bytes();w,h,rgba=native.png_pixels(raw)
        if args.channels==3 and any(rgba[i]!=255 for i in range(3,len(rgba),4)):
            raise ValueError('RGB packing would discard alpha')
        pixels=rgba if args.channels==4 else bytes(v for i,v in enumerate(rgba) if i%4!=3)
        chunks=native.encode_raster(pixels,w,h,args.channels)
        if independent_decode(chunks,w,h,args.channels)!=pixels:raise ValueError('independent decode mismatch')
        args.output.mkdir(parents=True,exist_ok=True)
        refs=[]
        for chunk in chunks:
            sha=digest(chunk);(args.output/(sha+'.sfr')).write_bytes(chunk)
            refs.append(dict(sha256=sha,bytes=len(chunk)))
        (args.output/'manifest.json').write_text(json.dumps(dict(source_sha256=digest(raw),pixel_sha256=digest(pixels),width=w,height=h,channels=args.channels,shards=refs),indent=2)+'\n')
    else:
        (optimal_study if args.optimal else study)(args.output)

if __name__=='__main__': main()
