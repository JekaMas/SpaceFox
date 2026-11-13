"""Orthographic selected source contours; no catalog, invented island or device I/O."""
import math
from decimal import Decimal

from .catalog import loads_json
from .global_map import position
from .graphics import _pooled, UNITS
from .bridge_map import _fade
from .visual_bridge import sha

LAYOUT = 'native-04-globe-v1'
RADIUS = 190
CENTER = (195, 195)
ANCHOR = (335, 165)
# Rotate the site-centered frame so the actual point lands at the accepted pin.
_SIN_Y = (ANCHOR[0]-CENTER[0])/RADIUS
_COS_Y = math.sqrt(1-_SIN_Y**2)
_SIN_X = (CENTER[1]-ANCHOR[1])/RADIUS/_COS_Y
_COS_X = math.sqrt(1-_SIN_X**2)


def camera(latitude, longitude, center):
    """Unit vector in camera axes (east, north, toward viewer)."""
    latitude, longitude = position(latitude, longitude)
    lat0, lon0 = position(*center)
    p, l, p0 = map(math.radians, (latitude, longitude-lon0, lat0))
    x = math.cos(p)*math.sin(l)
    y = math.cos(p0)*math.sin(p)-math.sin(p0)*math.cos(p)*math.cos(l)
    z = math.sin(p0)*math.sin(p)+math.cos(p0)*math.cos(p)*math.cos(l)
    x, z = _COS_Y*x+_SIN_Y*z, -_SIN_Y*x+_COS_Y*z
    return x, _COS_X*y+_SIN_X*z, -_SIN_X*y+_COS_X*z


def project(latitude, longitude, center):
    x,y,z = camera(latitude, longitude, center)
    return None if z < -1e-12 else (CENTER[0]+RADIUS*x,CENTER[1]-RADIUS*y)


def segments(lines, center):
    """Great-circle source edges clipped at the visible limb, not joined across it.

    Densification bounds curvature error below .03px at190px radius. Antipodal
    endpoints have no unique short arc and are refused rather than fabricated.
    """
    for line in lines:
        for a,b in zip(line,line[1:]):
            u=camera(Decimal(str(a[1])),Decimal(str(a[0])),center)
            v=camera(Decimal(str(b[1])),Decimal(str(b[0])),center)
            dot=max(-1,min(1,sum(x*y for x,y in zip(u,v))))
            angle=math.acos(dot)
            if angle < 1e-12:continue
            if math.pi-angle < 1e-8:raise ValueError('ambiguous antipodal source edge')
            count=max(1,math.ceil(angle/math.radians(2)))
            previous=u
            for step in range(1,count+1):
                t=step/count
                current=tuple((math.sin((1-t)*angle)*x+math.sin(t*angle)*y)/math.sin(angle) for x,y in zip(u,v))
                start,end=previous,current;previous=current
                if start[2]<0 and end[2]<0:continue
                if (start[2]<0)!=(end[2]<0):
                    t=start[2]/(start[2]-end[2])
                    h=tuple(start[i]+t*(end[i]-start[i]) for i in range(3))
                    length=math.hypot(h[0],h[1]);h=(h[0]/length,h[1]/length,0)
                    if start[2]<0:start=h
                    else:end=h
                yield tuple((CENTER[0]+RADIUS*p[0],CENTER[1]-RADIUS*p[1]) for p in (start,end))


def source_lines(files, descriptor):
    """Reuse the admitted v2 corresponding source, including selected supplements."""
    def read(ref):
        raw=files.get(ref['path'])
        if type(raw) is not bytes or len(raw)!=ref['decodedBytes'] or sha(raw)!=ref['sha256']:
            raise ValueError('globe corresponding source pin')
        return loads_json(raw)
    proof=read(descriptor['source']['corresponding']);common=read(proof['common'])
    lines=list(common['baseWorld']['lines'])
    lines.extend([[Decimal(p[0])/1000000,Decimal(p[1])/1000000] for p in clip['points']] for clip in proof['clips'])
    return lines


def visuals(files, descriptor):
    """Finite shaded ocean and actual source contours; point is a native overlay."""
    if descriptor['position'] is None:return []
    center=tuple(Decimal(descriptor['position'][key]) for key in ('latitude','longitude'))
    draws=[]
    def color(rgb,x,y):
        # Globe contours retain a35% visibility floor; flat-map fade is untouched.
        alpha=max(.35,_fade(x,y)) if rgb==(0x84,0xba,0xd0) else _fade(x,y)
        values=[min(255,round(v*alpha/8)*8) for v in rgb]
        return values[0]*65536+values[1]*256+values[2]
    def polygon(rgb,points,x,y):
        coords=[round(max(0,min(390,c))*256/390*UNITS) for p in points for c in p]
        if len(set(zip(coords[::2],coords[1::2])))<3:return
        draws.append((color(rgb,x,y),coords))
    # Row spans end on the sphere. Quantized fade keeps lossless SFR bounded;
    # geography vertices are never replaced by a fake site-centered land disk.
    for y in range(6,384,3):
        dy=y+1.5-CENTER[1];half=math.sqrt(max(0,RADIUS**2-dy**2))
        left,right=CENTER[0]-half,CENTER[0]+half
        for x in range(int(left),math.ceil(right),3):
            x0,x1=max(left,x),min(right,x+3)
            if x1<=x0:continue
            polygon((0x10,0x2c,0x43),[(x0,y),(x1,y),(x1,y+3),(x0,y+3)],(x0+x1)/2,y+1.5)
    for a,b in segments(source_lines(files,descriptor),center):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length<.05:continue
        ox,oy=-dy/length*.325,dx/length*.325
        polygon((0x84,0xba,0xd0),[(a[0]+ox,a[1]+oy),(b[0]+ox,b[1]+oy),(b[0]-ox,b[1]-oy),(a[0]-ox,a[1]-oy)],(a[0]+b[0])/2,(a[1]+b[1])/2)
    # Each pool has <=32 palette entries even with source-driven ocean/coasts.
    result=[];chunk=[];palette=set()
    for draw in draws:
        if len(chunk)>=180 or draw[0] not in palette and len(palette)>=32:
            result.append(_pooled([256,256],chunk));chunk=[];palette=set()
        chunk.append(draw);palette.add(draw[0])
    if chunk:result.append(_pooled([256,256],chunk))
    return result
