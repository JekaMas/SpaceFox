"""Finite local SVG-to-polygon producer; not Garmin transport qualification.

Only the documented original-art subset is accepted. Geometry JSON contains no
SVG, object keys, executable content, URLs or floating-point numbers. Standard
library only; the catalog remains the sole model/asset identity owner.
"""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import xml.etree.ElementTree as ET

from .catalog import CatalogError, canonical_bytes, dependency_closure, validate_catalog


class VisualError(ValueError):
    """Unsupported, corrupt or over-budget candidate; accepted output survives."""


UNITS = 32
PACK_BASE = 16384
SCALE_UNITS = 256
LIMITS = {'decodedBytes': 65536, 'commands': 512, 'vertices': 4096,
          'polygonVertices': 512, 'palette': 32, 'depth': 8, 'canvasPixels': 256,
          'sourceBytes': 65536, 'sourceNodes': 512, 'sourceTokens': 8192,
          'sourceCommands': 2048, 'keyframes': 16, 'animationMs': 3000,
          'shardBytes': 4096, 'shardsPerAsset': 32, 'selectionRoots': 16, 'selectionBytes': 65536, 'artifactBytes': 1048576}
TOL = 1 / 32  # analytic off-watch subdivision error in nominal export pixels
QUANT_ERROR_NANOPIXELS = math.ceil(math.sqrt(2) / (2 * UNITS) * 1_000_000_000)
NUMBER = r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?'
TOKEN = re.compile(r'[A-Za-z]|' + NUMBER)
SVG_NS = '{http://www.w3.org/2000/svg}'
WSP = ' \t\r\n'


def _require(condition, message):
    if not condition:
        raise VisualError(message)


def _integer(value, low, high, field):
    _require(type(value) is int and low <= value <= high, f'{field}: invalid integer/bound')
    return value


def _array(value, field, *, length=None, maximum=None):
    _require(isinstance(value, list), f'{field}: array required')
    _require(length is None or len(value) == length, f'{field}: invalid length')
    _require(maximum is None or len(value) <= maximum, f'{field}: count limit')
    return value


def validate_visual(value):
    """Strict integer-only v1 schema; no caller-configurable enlarged limits."""
    _array(value, 'visual', length=8)
    _require(value[0] == 'SFV', 'unsupported visual magic')
    _integer(value[1], 1, 1, 'renderer/schema'); _integer(value[2], UNITS, UNITS, 'units')
    _array(value[3], 'canvas', length=2)
    w,h=[_integer(x,1,LIMITS['canvasPixels'],'canvas') for x in value[3]]
    palette=_array(value[4],'palette',maximum=LIMITS['palette'])
    _require(bool(palette),'empty palette')
    for color in palette:_integer(color,0,0xffffff,'color')
    _require(palette == sorted(set(palette)),'palette must be unique and sorted')
    pool=_array(value[5],'vertex pool',maximum=LIMITS['vertices'])
    _require(bool(pool),'vertex pool must be nonempty')
    points=[]
    for packed in pool:
        _integer(packed,0,PACK_BASE*PACK_BASE-1,'packed vertex')
        x,y=packed%PACK_BASE,packed//PACK_BASE
        _require(x <= w*UNITS and y <= h*UNITS,'coordinate bound')
        points.append((x,y))
    _require(len(set(pool)) == len(pool),'vertex pool must be unique')
    commands=_array(value[6],'commands',maximum=LIMITS['commands'])
    _require(bool(commands),'empty drawing')
    references,used_colors,used_points=0,set(),set()
    for command in commands:
        _array(command,'command',length=3);_integer(command[0],0,0,'opcode')
        used_colors.add(_integer(command[1],0,len(palette)-1,'palette reference'))
        indices=_array(command[2],'vertex indices',maximum=LIMITS['polygonVertices'])
        _require(len(indices) >= 3,'polygon requires >=3 vertices')
        for index in indices:
            _integer(index,0,len(pool)-1,'vertex reference');used_points.add(index)
        poly=[points[index] for index in indices]
        _require(_area(poly) != 0,'zero-area wire polygon');_simple(poly)
        references+=len(indices)
    _require(references <= LIMITS['vertices'],'total vertex reference limit')
    _require(used_colors == set(range(len(palette))),'unused palette entry')
    _require(used_points == set(range(len(pool))),'unused vertex pool entry')
    # First-use pool order is normative and permits bounded incremental assembly.
    order=list(dict.fromkeys(i for command in commands for i in command[2]))
    _require(order == list(range(len(pool))),'noncanonical vertex pool order')
    _array(value[7],'animation',length=2)
    duration,frames=value[7]
    _integer(duration,0,LIMITS['animationMs'],'animation duration')
    _array(frames,'keyframes',maximum=LIMITS['keyframes'])
    if duration == 0:_require(frames == [],'still animation must have no frames')
    else:
        _require(duration >= 2000 and len(frames) >= 2,'animation must last 2-3 seconds')
        previous=-1
        for frame in frames:
            _array(frame,'keyframe',length=4)
            timestamp=_integer(frame[0],0,duration,'keyframe time')
            _require(timestamp > previous,'keyframe times must increase');previous=timestamp
            _integer(frame[1],-64*UNITS,64*UNITS,'animation X')
            _integer(frame[2],-64*UNITS,64*UNITS,'animation Y')
            _integer(frame[3],128,512,'animation scale')
        _require(frames[0] == [0,0,0,SCALE_UNITS] and frames[-1][0] == duration,'animation requires identity start and complete final time')
    _require(len(_encode(value)) <= LIMITS['decodedBytes'],'logical decoded byte limit')
    return value


def _encode(value):
    return json.dumps(value, ensure_ascii=True, separators=(',', ':'), allow_nan=False).encode('ascii')


def canonical_visual(value):
    """V1 digest preimage: canonical compact JSON of the fixed-position array.

    Decimal minimal signed integers, ASCII magic, no whitespace/newline. Array
    order is semantic (including painter order); there are no dictionary keys.
    """
    return _encode(validate_visual(value))


def visual_digest(value):
    return hashlib.sha256(canonical_visual(value)).hexdigest()


def loads_visual(data):
    """Check decoded UTF-8 bytes/depth before the standard JSON parser."""
    try:
        _require(isinstance(data, (bytes, str)), 'visual input must be bytes or text')
        raw = data.encode('utf-8') if isinstance(data, str) else data
        _require(len(raw) <= LIMITS['decodedBytes'], 'decoded byte limit')
        source = raw.decode('utf-8', errors='strict')
        depth, quoted, escaped = 0, False, False
        for ch in source:
            if quoted:
                if escaped: escaped = False
                elif ch == '\\': escaped = True
                elif ch == '"': quoted = False
            elif ch == '"': quoted = True
            elif ch in '[{':
                depth += 1; _require(depth <= LIMITS['depth'], 'JSON depth limit')
            elif ch in ']}': depth -= 1
        def invalid(value):
            raise VisualError('nonfinite JSON value ' + value)
        value = json.loads(source, parse_constant=invalid)
        return validate_visual(value)
    except (UnicodeError, ValueError, RecursionError, TypeError) as exc:
        raise VisualError(f'invalid visual JSON: {exc}') from exc


def metrics(value):
    data=canonical_visual(value)
    return {'logicalDecodedBytes':len(data),'commands':len(value[6]),
            'vertices':len(value[5]),'vertexReferences':sum(len(c[2]) for c in value[6]),
            'palette':len(value[4]),'keyframes':len(value[7][1])}


def _pooled(size,draw,animation=None):
    colors=sorted(set(c for c,points in draw));indices={c:i for i,c in enumerate(colors)}
    pool,positions,commands=[],{},[]
    for color,points in draw:
        references=[]
        for x,y in zip(points[::2],points[1::2]):
            packed=x+PACK_BASE*y
            if packed not in positions:positions[packed]=len(pool);pool.append(packed)
            references.append(positions[packed])
        commands.append([0,indices[color],references])
    return ['SFV',1,UNITS,list(size),colors,pool,commands,deepcopy(animation) if animation is not None else [0,[]]]


def _expanded(value):
    return [(value[4][command[1]],[coordinate for index in command[2]
             for coordinate in (value[5][index]%PACK_BASE,value[5][index]//PACK_BASE)]) for command in value[6]]


def loads_shard(data):
    raw=data.encode('utf-8') if isinstance(data,str) else data
    _require(isinstance(raw,bytes) and len(raw) <= LIMITS['shardBytes'],'shard decoded byte limit')
    value=loads_visual(raw)
    _require(value[7] == [0,[]],'geometry shard must be still')
    return value


def split_visual(value):
    """Deterministic greedy painter-order shards; each independently bounded."""
    validate_visual(value)
    shards,current=[],[]
    for command in _expanded(value):
        candidate=_pooled(value[3],current+[command])
        if len(_encode(candidate)) > LIMITS['shardBytes']:
            _require(bool(current),'single polygon exceeds shard byte limit')
            shards.append(canonical_visual(_pooled(value[3],current)));current=[command]
            _require(len(_encode(_pooled(value[3],current))) <= LIMITS['shardBytes'],'single polygon exceeds shard byte limit')
        else:current.append(command)
    if current:shards.append(canonical_visual(_pooled(value[3],current)))
    _require(len(shards) <= LIMITS['shardsPerAsset'],'asset shard count limit')
    return shards


def assemble_visual(shards,animation=None):
    """Producer reference assembly; native bounded agreement remains required."""
    _array(shards,'shards',maximum=LIMITS['shardsPerAsset']);_require(bool(shards),'empty shard list')
    draw=[];size=None
    for data in shards:
        value=loads_shard(data)
        if size is None:size=value[3]
        _require(value[3] == size,'shard canvas mismatch')
        draw.extend(_expanded(value))
        _require(len(draw) <= LIMITS['commands'],'assembled command limit')
    return validate_visual(_pooled(size,draw,animation))


def _number(text):
    _require(isinstance(text, str) and re.fullmatch(NUMBER, text) is not None, 'unsupported numeric syntax')
    value = float(text)
    _require(math.isfinite(value) and abs(value) <= 1_000_000, 'nonfinite/oversized source coordinate')
    return value


def _comma_wsp(text, *, optional=False):
    # SVG comma-wsp permits one comma, with optional surrounding whitespace.
    return (optional or bool(text)) and re.fullmatch(r'[ \t\r\n]*(?:,[ \t\r\n]*)?',text) is not None


def _numbers(text, *, points=False):
    result, end = [], 0
    for match in re.finditer(NUMBER, text):
        gap=text[end:match.start()]
        # General numeric lists require comma-wsp. Points additionally allow
        # an adjacent negative second coordinate within a coordinate pair.
        valid = not gap.strip(WSP) if not result else (
            _comma_wsp(gap) or (points and len(result)%2 == 1 and not gap and match.group().startswith('-')))
        _require(valid, 'invalid numeric list')
        result.append(_number(match.group())); end = match.end()
        _require(len(result) <= LIMITS['sourceTokens'], 'source token limit')
    _require(not text[end:].strip(WSP), 'invalid numeric list')
    return result


def _mul(a, b):
    # Uniform positive scale and translation only; order follows SVG CTM rules.
    result=(a[0]*b[0],a[0]*b[1]+a[1],a[0]*b[2]+a[2])
    _require(all(math.isfinite(x) and abs(x) <= 1024 for x in result) and result[0] > 0,'source transform bound')
    return result


def _transform(text):
    result, end = (1., 0., 0.), 0
    for match in re.finditer(r'([A-Za-z]+)[ \t\r\n]*\(([^()]*)\)', text):
        gap=text[end:match.start()]
        # The transform-list grammar uses comma-wsp+ between functions, but
        # only whitespace before the first and after the last function.
        _require((bool(gap) and not gap.strip(' ,\t\r\n')) if end else not gap.strip(WSP), 'unsupported transform syntax')
        name, args = match.group(1), _numbers(match.group(2))
        if name == 'translate' and len(args) in (1, 2):
            item = (1., args[0], args[1] if len(args) == 2 else 0.)
        elif name == 'scale' and len(args) in (1, 2):
            _require(args[0] > 0 and (len(args) == 1 or args[1] == args[0]), 'unsupported nonuniform/reflected scale')
            item = (args[0], 0., 0.)
        else:
            raise VisualError('unsupported source transform ' + name)
        result = _mul(result, item); end = match.end()
    _require(end > 0 and not text[end:].strip(WSP), 'unsupported transform syntax')
    return result


def _point(matrix, p):
    value = (matrix[0]*p[0]+matrix[1], matrix[0]*p[1]+matrix[2])
    _require(all(math.isfinite(x) and abs(x) <= 1024 for x in value), 'normalized preclip coordinate limit')
    return value


def _unit(vector):
    length = math.hypot(*vector)
    _require(length > 1e-12, 'unsupported zero/cusp tangent')
    return (vector[0]/length, vector[1]/length)


def _sub(a, b): return (a[0]-b[0], a[1]-b[1])
def _cross(a, b): return a[0]*b[1]-a[1]*b[0]
def _normal(u): return (-u[1], u[0])
def _offset(p, n, radius): return (p[0]+n[0]*radius, p[1]+n[1]*radius)
def _area(poly): return sum(_cross(a,b) for a,b in zip(poly,poly[1:]+poly[:1]))/2


@dataclass
class Segment:
    a: tuple
    b: tuple
    ua: tuple
    ub: tuple
    corner: bool = True


def _line(a, b):
    if a == b:
        return []
    u = _unit(_sub(b,a))
    return [Segment(a,b,u,u)]


class _Drawing:
    def __init__(self, size):
        _array(size, 'exportSize', length=2)
        self.w, self.h = [_integer(x,1,LIMITS['canvasPixels'],'exportSize') for x in size]
        self.draw = []
        self.vertices = self.commands = self.nodes = self.tokens = 0
        self.max_error = 0.

    def count_source_command(self):
        self.commands += 1
        _require(self.commands <= LIMITS['sourceCommands'], 'source command limit')

    def quadratic(self, a, b, c, radius, depth=0):
        # |Q(t)-linear(t)| <= |A-2B+C|/4. Unit tangent directions stay
        # inside the endpoint cone. 2r*|uA-uB| conservatively bounds offset
        # normal interpolation error; ribbons use exact endpoint normals.
        ua = _unit(_sub(b,a) if b != a else _sub(c,a))
        ub = _unit(_sub(c,b) if c != b else _sub(c,a))
        dot = ua[0]*ub[0]+ua[1]*ub[1]
        _require(dot > -0.999999, 'unsupported reversing quadratic cusp')
        error = math.hypot(a[0]-2*b[0]+c[0], a[1]-2*b[1]+c[1])/4 + 2*radius*math.hypot(ua[0]-ub[0], ua[1]-ub[1])
        if error <= TOL:
            self.max_error = max(self.max_error, error)
            return [Segment(a,c,ua,ub)]
        _require(depth < 16, 'quadratic subdivision depth limit')
        ab = ((a[0]+b[0])/2,(a[1]+b[1])/2)
        bc = ((b[0]+c[0])/2,(b[1]+c[1])/2)
        center = ((ab[0]+bc[0])/2,(ab[1]+bc[1])/2)
        first = self.quadratic(a,ab,center,radius,depth+1)
        second = self.quadratic(center,bc,c,radius,depth+1)
        second[0].corner = False
        _require(len(first)+len(second) <= LIMITS['polygonVertices'], 'quadratic vertex limit')
        return first+second

    def arc_points(self, center, radius, start, sweep, outer_radius=None):
        measure = max(radius, outer_radius or 0)
        _require(measure > 0, 'invalid arc radius')
        angle = 2*math.acos(max(-1,1-min(TOL/measure,1)))
        count = max(1, math.ceil(abs(sweep)/angle))
        _require(count <= LIMITS['polygonVertices'], 'arc vertex limit')
        self.max_error = max(self.max_error, measure*(1-math.cos(abs(sweep)/(2*count))))
        return [(center[0]+radius*math.cos(start+sweep*i/count),
                 center[1]+radius*math.sin(start+sweep*i/count)) for i in range(count+1)]

    def arc_segments(self, center, radius, start, sweep, stroke_radius):
        points = self.arc_points(center,radius,start,sweep,radius+stroke_radius)
        segments = []
        for i in range(len(points)-1):
            t0 = start+sweep*i/(len(points)-1); t1 = start+sweep*(i+1)/(len(points)-1)
            segments.append(Segment(points[i],points[i+1],(-math.sin(t0),math.cos(t0)),
                                    (-math.sin(t1),math.cos(t1)),i == 0))
        return segments

    def emit(self, poly, color, clip):
        # Convex rectangular clipping of each opaque polygon; no background fill.
        for axis, edge, sign in ((0,clip[0],1),(0,clip[2],-1),(1,clip[1],1),(1,clip[3],-1)):
            output = []
            if not poly: return
            a = poly[-1]; inside_a = sign*(a[axis]-edge) >= 0
            for b in poly:
                inside_b = sign*(b[axis]-edge) >= 0
                if inside_a != inside_b:
                    t = (edge-a[axis])/(b[axis]-a[axis])
                    p = [a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])];p[axis] = edge
                    output.append(tuple(p))
                if inside_b: output.append(b)
                a, inside_a = b, inside_b
            poly = output
        points = []
        for x,y in poly:
            p = (math.floor(x*UNITS+.5), math.floor(y*UNITS+.5))
            if not points or points[-1] != p: points.append(p)
        if len(points) > 1 and points[0] == points[-1]: points.pop()
        if len(points) < 3 or _area(points) == 0: return  # SVG zero-area fill, or <=quantization error
        _require(len(points) <= LIMITS['polygonVertices'], 'polygon vertex limit')
        self.vertices += len(points)
        _require(self.vertices <= LIMITS['vertices'], 'total vertex limit')
        _require(len(self.draw) < LIMITS['commands'], 'command limit')
        self.draw.append((color,[v for p in points for v in p]))

    def stroke(self, segments, closed, color, width, cap, join, miter, clip):
        if not segments: raise VisualError('unsupported zero-length stroked path')
        r = width/2
        for s in segments:
            na, nb = _normal(s.ua), _normal(s.ub)
            self.emit([_offset(s.a,na,r),_offset(s.b,nb,r),_offset(s.b,nb,-r),_offset(s.a,na,-r)],color,clip)
        pairs = list(zip(segments,segments[1:]))
        if closed: pairs.append((segments[-1],segments[0]))
        for before,after in pairs:
            if not after.corner: continue  # exact tangent ribbons share their complete edge
            u,v,p = before.ub,after.ua,after.a
            cross = _cross(u,v); dot = max(-1,min(1,u[0]*v[0]+u[1]*v[1]))
            if abs(cross) < 1e-12 and dot > 0: continue
            _require(dot > -0.999999, 'unsupported reversing stroke join')
            side = -1 if cross > 0 else 1
            n1,n2 = _normal(u),_normal(v)
            a,b = _offset(p,n1,r*side),_offset(p,n2,r*side)
            if join == 'round':
                sweep = math.atan2(cross,dot)
                self.emit([p]+self.arc_points(p,r,math.atan2(a[1]-p[1],a[0]-p[0]),sweep),color,clip)
            else:
                length = math.sqrt(2/(1+dot))
                if join == 'miter' and length <= miter:
                    tip = (p[0]+side*r*(n1[0]+n2[0])/(1+dot),p[1]+side*r*(n1[1]+n2[1])/(1+dot))
                    self.emit([p,a,tip,b],color,clip)
                else:
                    self.emit([p,a,b],color,clip)
        if closed or cap == 'butt': return
        for segment,start in ((segments[0],True),(segments[-1],False)):
            p,u = (segment.a,segment.ua) if start else (segment.b,segment.ub)
            n = _normal(u); direction = -1 if start else 1
            if cap == 'square':
                extension = _offset(p,u,r*direction)
                self.emit([_offset(p,n,r),_offset(extension,n,r),_offset(extension,n,-r),_offset(p,n,-r)],color,clip)
            else:
                angle = math.atan2(u[1],u[0]) + (math.pi/2 if start else -math.pi/2)
                self.emit([p]+self.arc_points(p,r,angle,math.pi),color,clip)


def _intersects(a,b,c,d):
    def orient(p,q,r): return _cross(_sub(q,p),_sub(r,p))
    def on(p,q,r): return min(p[0],q[0])-1e-9 <= r[0] <= max(p[0],q[0])+1e-9 and min(p[1],q[1])-1e-9 <= r[1] <= max(p[1],q[1])+1e-9
    o1,o2,o3,o4 = orient(a,b,c),orient(a,b,d),orient(c,d,a),orient(c,d,b)
    if o1*o2 < 0 and o3*o4 < 0: return True
    return any(abs(o) < 1e-9 and on(p,q,r) for o,p,q,r in ((o1,a,b,c),(o2,a,b,d),(o3,c,d,a),(o4,c,d,b)))


def _inside(p, poly):
    inside = False
    for a,b in zip(poly,poly[1:]+poly[:1]):
        if (a[1]>p[1]) != (b[1]>p[1]) and p[0] < (b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]: inside = not inside
    return inside


def _simple(poly):
    edges=list(zip(poly,poly[1:]+poly[:1]))
    _require(all(a != b for a,b in edges),'duplicate polygon vertex')
    for i,(a,b) in enumerate(edges):
        for j in range(i+1,len(edges)):
            if j == i+1 or (i == 0 and j == len(edges)-1): continue
            _require(not _intersects(a,b,*edges[j]), 'unsupported self-intersecting fill/polygon')


def _fill_contours(paths):
    polygons = []
    for segments,closed in paths:
        if not segments: continue
        poly = [segments[0].a]+[s.b for s in segments]
        if math.dist(poly[-1],poly[0]) < 1e-9: poly.pop()
        _require(len(poly) <= LIMITS['polygonVertices'], 'source polygon vertex limit')
        if len(poly) < 3: continue
        _simple(poly)
        if abs(_area(poly)) > 1e-12: polygons.append(poly)
    for i,p in enumerate(polygons):
        for q in polygons[i+1:]:
            overlap = _inside(p[0],q) or _inside(q[0],p)
            overlap = overlap or any(_intersects(a,b,c,d) for a,b in zip(p,p[1:]+p[:1]) for c,d in zip(q,q[1:]+q[:1]))
            _require(not overlap, 'unsupported overlapping/hole compound fill')
    return polygons


def _paths(data, matrix, drawing, radius):
    tokens,end = [],0
    for match in TOKEN.finditer(data):
        token=match.group();gap=data[end:match.start()]
        between_numbers = bool(tokens) and not tokens[-1].isalpha() and not token.isalpha()
        _require(_comma_wsp(gap,optional=True) if between_numbers else not gap.strip(WSP), 'unsupported path syntax')
        tokens.append(token);end=match.end()
    _require(not data[end:].strip(WSP), 'unsupported path syntax')
    drawing.tokens += len(tokens);_require(drawing.tokens <= LIMITS['sourceTokens'], 'source token limit')
    result,segments = [],[]
    current,start,command,index,has_start = (0.,0.),None,None,0,False
    while index < len(tokens):
        if tokens[index].isalpha():
            command=tokens[index];index+=1
            _require(command.upper() in ('M','L','H','V','Q','Z'), 'unsupported path operation '+command)
            if command.upper() == 'Z':
                drawing.count_source_command()
                _require(start is not None,'close before move')
                segments += _line(_point(matrix,current),_point(matrix,start))
                result.append((segments,True));segments=[];current=start;start=None;command=None
                continue
        _require(command is not None and command.upper() != 'Z', 'missing path command')
        op=command.upper();count={'M':2,'L':2,'H':1,'V':1,'Q':4}[op]
        _require(index+count <= len(tokens) and not any(t.isalpha() for t in tokens[index:index+count]), 'missing path parameters')
        values=[_number(t) for t in tokens[index:index+count]];index+=count
        drawing.count_source_command()
        relative=command.islower()
        def pair(x,y):return (x+current[0],y+current[1]) if relative else (x,y)
        if op == 'M':
            if start is not None:result.append((segments,False))
            current=pair(*values);start=current;has_start=True;segments=[]
            _point(matrix,current);command='l' if relative else 'L';continue
        _require(has_start,'path must begin with move')
        if start is None: start=current
        if op == 'H': end=(values[0]+current[0] if relative else values[0],current[1])
        elif op == 'V': end=(current[0],values[0]+current[1] if relative else values[0])
        else: end=pair(*values[-2:])
        if op == 'Q':
            control=pair(*values[:2]);segments += drawing.quadratic(_point(matrix,current),_point(matrix,control),_point(matrix,end),radius)
        else: segments += _line(_point(matrix,current),_point(matrix,end))
        current=end
    if start is not None:result.append((segments,False))
    return result


def _rectangle(node,matrix,drawing,radius):
    x,y = (_number(node.get(k,'0')) for k in ('x','y'))
    w,h = (_number(node.get(k,'0')) for k in ('width','height'))
    _require(w > 0 and h > 0,'nonpositive rectangle')
    rx=_number(node.get('rx',node.get('ry','0')));ry=_number(node.get('ry',node.get('rx','0')))
    _require(rx >= 0 and ry >= 0,'negative corner radius');rx=min(rx,w/2);ry=min(ry,h/2)
    _require(rx == ry,'unsupported elliptical rounded rectangle')
    left,top=_point(matrix,(x,y));right,bottom=_point(matrix,(x+w,y+h));r=rx*matrix[0]
    if r == 0:
        points=[(left,top),(right,top),(right,bottom),(left,bottom)]
        return [(sum((_line(a,b) for a,b in zip(points,points[1:]+points[:1])),[]),True)]
    _require(radius < r, 'unsupported stroke wider than rounded corner radius')
    segments=[]
    for center,start,edge in (((right-r,top+r),-math.pi/2,((left+r,top),(right-r,top))),((right-r,bottom-r),0,((right,top+r),(right,bottom-r))),((left+r,bottom-r),math.pi/2,((right-r,bottom),(left+r,bottom))),((left+r,top+r),math.pi,((left,bottom-r),(left,top+r)))):
        segments += _line(*edge)
        segments += drawing.arc_segments(center,r,start,math.pi/2,radius)
    return [(segments,True)]


STYLE = {'fill','stroke','stroke-width','stroke-linecap','stroke-linejoin','stroke-miterlimit','fill-rule'}
SHAPE_ATTRS = {'path':{'d','data-part'},'rect':{'x','y','width','height','rx','ry'},'polygon':{'points'}}
DEFAULT_STYLE = {'fill':'#000000','stroke':'none','stroke-width':'1','stroke-linecap':'butt','stroke-linejoin':'miter','stroke-miterlimit':'4','fill-rule':'nonzero'}


def _paint(text):
    if text == 'none': return None
    _require(re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?',text) is not None,'unsupported paint syntax')
    text=text[1:]
    if len(text) == 3:text=''.join(c*2 for c in text)
    return int(text,16)


def _export_svg(data,size,animation=None):
    drawing=_Drawing(size)
    try:
        _require(isinstance(data,bytes),'SVG source must be bytes')
        _require(len(data) <= LIMITS['sourceBytes'],'source byte limit')
        text=data.decode('utf-8',errors='strict')
        _require('<!' not in text and '<?' not in text,'unsupported XML declaration/entity/comment/instruction')
        root=ET.fromstring(text)
    except (UnicodeError,ET.ParseError) as exc:raise VisualError(f'invalid source XML: {exc}') from exc
    def visit(node,matrix,clip,style,depth,outer=False):
        drawing.nodes+=1
        _require(drawing.nodes <= LIMITS['sourceNodes'] and depth <= LIMITS['depth'],'source node/depth limit')
        _require(isinstance(node.tag,str) and (node.tag.startswith(SVG_NS) or '{' not in node.tag),'unsupported namespace')
        tag=node.tag.removeprefix(SVG_NS)
        _require(tag in ('svg','g','title','desc',*SHAPE_ATTRS),'unsupported source element '+tag)
        if outer:_require(tag == 'svg','source root must be SVG')
        if tag in ('title','desc'):
            _require(not node.attrib and not list(node),'unsupported metadata markup');return
        _require(not (node.text or '').strip(),'unsupported shape text')
        allowed=STYLE|{'transform'}|({'viewBox','x','y','width','height','preserveAspectRatio'} if tag == 'svg' else SHAPE_ATTRS.get(tag,set()))
        _require(set(node.attrib) <= allowed,'unsupported source attribute '+','.join(sorted(set(node.attrib)-allowed)))
        style=dict(style);style.update({k:v for k,v in node.attrib.items() if k in STYLE})
        _require(style['fill-rule'] == 'nonzero','unsupported fill rule')
        if 'transform' in node.attrib:matrix=_mul(matrix,_transform(node.attrib['transform']))
        if tag == 'svg':
            _require(node.get('preserveAspectRatio','xMidYMid meet') == 'xMidYMid meet','unsupported aspect fitting')
            box=_numbers(node.get('viewBox',''))
            _require(len(box) == 4 and box[2] > 0 and box[3] > 0,'viewBox required/invalid')
            if outer:
                x,y,w,h=0.,0.,float(drawing.w),float(drawing.h)
                _require(not {'x','y','width','height'} & node.attrib.keys(),'outer dimensions must come from catalog exportSize')
            else:
                x,y=(_number(node.get(k,'0')) for k in ('x','y'))
                w,h=(_number(node.get(k,'')) for k in ('width','height'))
                _require(w > 0 and h > 0,'invalid nested viewport')
            p,q=_point(matrix,(x,y)),_point(matrix,(x+w,y+h))
            clip=(max(clip[0],p[0]),max(clip[1],p[1]),min(clip[2],q[0]),min(clip[3],q[1]))
            _require(clip[0] < clip[2] and clip[1] < clip[3],'unsupported empty nested viewport')
            scale=min(w/box[2],h/box[3])
            fit=(scale,x+(w-scale*box[2])/2-scale*box[0],y+(h-scale*box[3])/2-scale*box[1])
            matrix=_mul(matrix,fit)
        if tag in ('svg','g'):
            for child in node:
                visit(child,matrix,clip,style,depth+1)
                _require(not (child.tail or '').strip(),'unsupported source tail text')
            return
        _require(not list(node),'shape children unsupported')
        fill,stroke=_paint(style['fill']),_paint(style['stroke'])
        width=_number(style['stroke-width'])*matrix[0]
        _require(0 < width <= 64,'stroke width limit')
        cap,join=style['stroke-linecap'],style['stroke-linejoin'];miter=_number(style['stroke-miterlimit'])
        _require(cap in ('butt','round','square') and join in ('miter','round','bevel') and 1 <= miter <= 8,'unsupported stroke style/miter bound')
        radius=width/2 if stroke is not None else 0
        if tag == 'path':paths=_paths(node.get('d',''),matrix,drawing,radius)
        elif tag == 'rect':paths=_rectangle(node,matrix,drawing,radius)
        else:
            points=_numbers(node.get('points',''),points=True);drawing.tokens+=len(points)
            _require(len(points) >= 6 and len(points)%2 == 0 and len(points)//2 <= LIMITS['polygonVertices'],'invalid polygon points')
            _require(drawing.tokens <= LIMITS['sourceTokens'],'source token limit')
            points=[_point(matrix,p) for p in zip(points[::2],points[1::2])]
            paths=[(sum((_line(a,b) for a,b in zip(points,points[1:]+points[:1])),[]),True)]
        # Restrict curved boundaries to the viewport interior. Tangent-clipped
        # curves can amplify set-distance error and need a separate source mode.
        margin=radius+TOL
        for segments,closed in paths:
            for segment in segments:
                if math.dist(segment.ua,segment.ub) > 1e-10:
                    _require(all(clip[0]+margin < p[0] < clip[2]-margin and clip[1]+margin < p[1] < clip[3]-margin for p in (segment.a,segment.b)), 'unsupported clipped/tangent curve boundary')
        if fill is not None:
            for poly in _fill_contours(paths):drawing.emit(poly,fill,clip)
        if stroke is not None:
            for segments,closed in paths:drawing.stroke(segments,closed,stroke,width,cap,join,miter,clip)
    visit(root,(1.,0.,0.),(0.,0.,float(drawing.w),float(drawing.h)),DEFAULT_STYLE,1,True)
    value=_pooled([drawing.w,drawing.h],drawing.draw,animation)
    validate_visual(value)
    stats=metrics(value)
    stats.update(sourceBytes=len(data),sourceNodes=drawing.nodes,sourceTokens=drawing.tokens,sourceCommands=drawing.commands,
                 maxAnalyticApproximationNanopixels=math.ceil(drawing.max_error*1_000_000_000),quantizationNanopixels=QUANT_ERROR_NANOPIXELS)
    return value,stats


def export_svg(data,size,animation=None):
    return _export_svg(data,size,animation)[0]


def _source_path(root,path):
    _require(isinstance(path,str) and path,'source path required')
    relative=Path(path)
    _require(not relative.is_absolute() and '..' not in relative.parts,'source path must stay relative')
    resolved=(root/relative).resolve()
    _require(resolved.is_relative_to(root),'source path resolves outside root')
    return resolved


def build_pack(root,catalog,*,roots=None):
    """Export every selected asset via catalog definitions; never a model switch.

    Returns a fully validated local candidate. No file output occurs here. Full
    publisher manifests are not watch downloads; selected metadata retains exact
    catalog decimals, including source site coordinates, without quantization.
    """
    root=Path(root).resolve()
    try:
        validate_catalog(catalog)
        selection=None
        if roots is not None:
            _array(roots,'selection roots',maximum=LIMITS['selectionRoots'])
            _require(bool(roots),'selection must be nonempty')
            selection=dependency_closure(catalog,roots,expected_revision=catalog['catalogVersion'])
        selected=selection if selection is not None else catalog
        if selection is not None:
            # Global source envelopes/import tables remain publisher-side. Every
            # selected row is retained exactly; the complete catalog has a pin.
            selection={k:deepcopy(selection[k]) for k in ('schemaVersion','catalogVersion','roots','dictionaries')}
            selection['dictionaries'].pop('assets')
        manifest={'schemaVersion':1,'rendererVersion':1,'catalogVersion':catalog['catalogVersion'],
                  'catalogSha256':hashlib.sha256(canonical_bytes(catalog)).hexdigest(),
                  'qualification':'producer-only-not-device-qualified','selection':selection,'assets':{}}
        objects,statistics={},{}
        for identity,row in sorted(selected['dictionaries']['assets'].items()):
            try:
                facts=row['facts']
                _require(facts.get('license') == 'MIT','default pack requires explicit admitted MIT license')
                for field in ('creator','sources'):
                    _require(bool(facts.get(field)),f'missing attribution {field}')
                credit=facts.get('credit',facts['creator'])
                _require(isinstance(credit,str) and bool(credit.strip()),'missing required credit')
                content=row.get('content')
                _require(isinstance(content,dict) and set(content) == {'path','sha256','bytes','format'},'catalog source content reference required')
                _require(content['format'] == 'source-svg','unsupported source format')
                pins=catalog.get('inputDigests',{})
                _require(pins.get(content['path']) == content['sha256'], 'catalog input/source digest mismatch')
                path=_source_path(root,content['path'])
                _require(path.is_file() and path.stat().st_size <= LIMITS['sourceBytes'],'source file/byte limit')
                with path.open('rb') as source_stream:data=source_stream.read(LIMITS['sourceBytes']+1)
                _require(type(content['bytes']) is int and len(data) == content['bytes'] and hashlib.sha256(data).hexdigest() == content['sha256'],'source digest/length mismatch')
                value,stats=_export_svg(data,facts.get('exportSize'),facts.get('visualAnimation'))
                encoded=canonical_visual(value);digest=hashlib.sha256(encoded).hexdigest()
                shards=split_visual(value);parts=[]
                for fragment in shards:
                    part_digest=hashlib.sha256(fragment).hexdigest();objects[part_digest]=fragment
                    parts.append({'sha256':part_digest,'path':f'objects/{part_digest}.json','decodedBytes':len(fragment)})
                stats.update(shards=len(parts),maxShardDecodedBytes=max(p['decodedBytes'] for p in parts))
                statistics[identity]=stats
                manifest['assets'][identity]={'sha256':digest,'shards':parts,'logicalDecodedBytes':len(encoded),'animation':value[7],
                    'schemaVersion':1,'rendererVersion':1,'canvas':value[3],'units':UNITS,
                    'bounds':[0,0,value[3][0]*UNITS,value[3][1]*UNITS],
                    'catalogRecord':deepcopy(row),
                    'rights':{'license':'MIT','credit':credit,'admission':'explicit MIT source; local free default-pack admission only'}}
            except (VisualError,OSError) as exc:
                raise VisualError(f'{identity}: {exc}') from exc
        _require(bool(objects),'selection contains no exportable assets')
        manifest_data=canonical_bytes(manifest)
        if roots is not None:_require(len(manifest_data) <= LIMITS['selectionBytes'],'selection manifest byte limit')
        _require(len(manifest_data)+sum(map(len,objects.values())) <= LIMITS['artifactBytes'],'publisher artifact byte limit')
        return {'manifest':manifest,'objects':objects,'statistics':statistics,'catalog':deepcopy(catalog)}
    except CatalogError as exc:raise VisualError(f'catalog: {exc}') from exc


def _atomic(path,data,prefix):
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix=prefix,delete=False) as stream:
            temporary=Path(stream.name);stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(temporary,path);temporary=None
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def _validate_shard_reference(part):
    """One visual-manifest reference contract for creation and re-admission."""
    _require(isinstance(part,dict) and set(part) == {'sha256','path','decodedBytes'},'invalid shard reference')
    key=part['sha256']
    _require(isinstance(key,str) and re.fullmatch('[0-9a-f]{64}',key) is not None,'invalid shard digest')
    _require(part['path'] == f'objects/{key}.json','missing/mismatched immutable shard')
    _integer(part['decodedBytes'],1,LIMITS['shardBytes'],'shard bytes')
    return key


def _validate_pack(pack):
    _require(isinstance(pack,dict) and set(pack) == {'manifest','objects','statistics','catalog'},'invalid pack envelope')
    manifest,objects=pack['manifest'],pack['objects']
    _require(isinstance(manifest,dict) and set(manifest) == {'schemaVersion','rendererVersion','catalogVersion','catalogSha256','qualification','selection','assets'},'invalid manifest envelope')
    for field in ('schemaVersion','rendererVersion'):_integer(manifest[field],1,1,field)
    _require(isinstance(manifest['catalogVersion'],str) and bool(manifest['catalogVersion'].strip()),'catalog version required')
    _require(manifest['qualification'] == 'producer-only-not-device-qualified','unsupported qualification')
    def digest_ok(value):return isinstance(value,str) and re.fullmatch('[0-9a-f]{64}',value) is not None
    _require(digest_ok(manifest['catalogSha256']),'catalog digest required')
    catalog=pack['catalog'];validate_catalog(catalog)
    _require(hashlib.sha256(canonical_bytes(catalog)).hexdigest() == manifest['catalogSha256'] and catalog['catalogVersion'] == manifest['catalogVersion'],'manifest/catalog pin mismatch')
    assets=manifest['assets']
    _require(isinstance(assets,dict) and bool(assets) and isinstance(objects,dict),'invalid assets/content tables')
    expected=set()
    for identity,row in assets.items():
        _require(isinstance(identity,str) and re.fullmatch(r'spacefox:asset:[A-Za-z0-9][A-Za-z0-9._-]*',identity) is not None,'invalid typed asset ID')
        _require(isinstance(row,dict) and set(row) == {'sha256','shards','logicalDecodedBytes','animation','schemaVersion','rendererVersion','canvas','units','bounds','catalogRecord','rights'},'invalid asset envelope')
        digest=row['sha256'];_require(digest_ok(digest),'invalid asset digest')
        parts=_array(row['shards'],'asset shards',maximum=LIMITS['shardsPerAsset'])
        _require(bool(parts),'asset shards required');fragment_data=[]
        for part in parts:
            key=_validate_shard_reference(part);expected.add(key)
            _require(key in objects,'missing/mismatched immutable shard')
            data=objects[key];fragment=loads_shard(data)
            _require(canonical_visual(fragment) == data and hashlib.sha256(data).hexdigest() == key,'candidate shard digest mismatch')
            _require(len(data) == part['decodedBytes'],'candidate shard byte mismatch');fragment_data.append(data)
        _array(row['animation'],'asset animation',length=2)
        value=assemble_visual(fragment_data,row['animation'])
        _require(hashlib.sha256(canonical_visual(value)).hexdigest() == digest,'complete asset digest mismatch')
        _integer(row['logicalDecodedBytes'],1,LIMITS['decodedBytes'],'logical decoded bytes')
        _require(len(canonical_visual(value)) == row['logicalDecodedBytes'],'logical decoded byte mismatch')
        for field in ('schemaVersion','rendererVersion'):_integer(row[field],1,1,field)
        _integer(row['units'],UNITS,UNITS,'units')
        _array(row['canvas'],'asset canvas',length=2)
        for dimension in row['canvas']:_integer(dimension,1,LIMITS['canvasPixels'],'asset canvas')
        _array(row['bounds'],'asset bounds',length=4)
        for coordinate in row['bounds']:_integer(coordinate,0,8192,'asset bounds')
        _require(row['canvas'] == value[3] and row['bounds'] == [0,0,value[3][0]*UNITS,value[3][1]*UNITS],'asset bounds/canvas mismatch')
        record=row['catalogRecord'];_require(isinstance(record,dict),'asset catalog record required')
        _require(identity in catalog['dictionaries']['assets'] and canonical_bytes(record) == canonical_bytes(catalog['dictionaries']['assets'][identity]),'asset source metadata mismatch')
        facts=record.get('facts');_require(isinstance(facts,dict),'asset facts required')
        _require(identity == 'spacefox:asset:'+str(facts.get('id')) and record.get('kind') == 'asset','asset identity mismatch')
        provenance = ([{'source':'curation','recordId':record['curation']['id']}] if 'curation' in record
                      else [{'source':'assetSeed','recordId':facts['id']}])
        _require(record.get('provenance') == provenance,'asset provenance mismatch')
        _require(facts.get('license') == 'MIT' and isinstance(facts.get('creator'),str) and bool(facts['creator'].strip()),'asset rights/creator not admitted')
        _require(isinstance(facts.get('sources'),list) and bool(facts['sources']) and all(isinstance(x,str) and bool(x.strip()) for x in facts['sources']),'asset sources required')
        rights={'license':'MIT','credit':facts.get('credit',facts['creator']),'admission':'explicit MIT source; local free default-pack admission only'}
        _require(isinstance(rights['credit'],str) and bool(rights['credit'].strip()) and row['rights'] == rights,'asset credit/admission mismatch')
    _require(set(objects) == expected,'unreferenced candidate object')
    selection=manifest['selection']
    if selection is not None:
        _require(isinstance(selection,dict) and set(selection) == {'schemaVersion','catalogVersion','roots','dictionaries'},'invalid selection envelope')
        _array(selection['roots'],'selection roots',maximum=LIMITS['selectionRoots'])
        _require(bool(selection['roots']),'empty selection roots')
        _integer(selection['schemaVersion'],1,1,'selection schema')
        _require(selection['catalogVersion'] == manifest['catalogVersion'],'selection version mismatch')
        _require(isinstance(selection['dictionaries'],dict) and set(selection['dictionaries']) == {'countries','organizations','configurations','sites'},'invalid selection dictionaries')
        # Source definitions are stored once in assets; selection rows refer by typed ID.
        all_ids=set(assets)|{key for table in selection['dictionaries'].values() for key in table}
        _require(all(isinstance(key,str) and key in all_ids for key in selection['roots']),'unknown selection root')
        for table in selection['dictionaries'].values():
            for record in table.values():
                for reference in record['references'].values():
                    for target in reference if isinstance(reference,list) else ([] if reference is None else [reference]):
                        _require(target in all_ids,'dangling selection reference')
    expected_catalog=dependency_closure(catalog,selection['roots'],expected_revision=catalog['catalogVersion']) if selection is not None else catalog
    _require(set(assets) == set(expected_catalog['dictionaries']['assets']),'catalog asset closure mismatch')
    if selection is not None:
        expected_tables={key:table for key,table in expected_catalog['dictionaries'].items() if key != 'assets'}
        _require(canonical_bytes(selection['dictionaries']) == canonical_bytes(expected_tables),'selection source metadata/reference mismatch')
    data=canonical_bytes(manifest)
    if selection is not None:_require(len(data) <= LIMITS['selectionBytes'],'selection manifest byte limit')
    _require(len(data)+sum(map(len,objects.values())) <= LIMITS['artifactBytes'],'publisher artifact byte limit')
    return data


def _immutable(path,data):
    # Link a complete fsynced temporary file without ever replacing this name.
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.object-',delete=False) as stream:
            temporary=Path(stream.name);stream.write(data);stream.flush();os.fsync(stream.fileno())
        try:os.link(temporary,path)
        except FileExistsError:
            _require(not path.is_symlink() and path.read_bytes() == data,'raced immutable content mismatch')
            return False
        return True
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def write_pack(output,pack,*,fault=None):
    """Immutable content first, atomic local manifest last. No hosted publication.

    Output must be a dedicated local directory. A failed attempt may leave verified
    unreferenced immutable objects; the active manifest is untouched until replace.
    This is a local file/process crash contract, not a power-loss/native-cache proof.
    """
    output=Path(output).resolve()
    try:data=_validate_pack(pack)
    except (CatalogError,KeyError,TypeError,AttributeError) as exc:raise VisualError(f'invalid candidate pack: {exc}') from exc
    manifest,objects=pack['manifest'],pack['objects']
    output.mkdir(parents=True,exist_ok=True);store=output/'objects'
    _require(not store.is_symlink(),'object directory may not be a symlink')
    store.mkdir(exist_ok=True)
    _require(not (output/'manifest.json').is_symlink(),'manifest may not be a symlink')
    written=reused=0
    for digest,content in sorted(objects.items()):
        target=store/(digest+'.json')
        _require(not target.is_symlink(),'immutable object may not be a symlink')
        if target.exists():
            _require(target.stat().st_size == len(content) and target.read_bytes() == content,'existing immutable content is corrupt');reused+=1
        elif _immutable(target,content):written+=1
        else:reused+=1
    if fault:fault('before-manifest-activation')
    _atomic(output/'manifest.json',data,'.manifest-')
    return {'qualification':manifest['qualification'],'manifestSha256':hashlib.sha256(data).hexdigest(),
            'manifestBytes':len(data),'objectBytes':sum(map(len,objects.values())),
            'objectsWritten':written,'objectsReused':reused,'assets':len(manifest['assets'])}
