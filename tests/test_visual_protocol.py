"""Literal/analytic producer vectors; public tests use only standard library."""
import copy
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.spacefox.catalog import build_catalog, canonical_bytes
from tools.spacefox.graphics import (
    VisualError, export_svg, validate_visual, loads_visual, canonical_visual,
    visual_digest, build_pack, write_pack, metrics, split_visual, assemble_visual, loads_shard,
)

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests/fixtures/visual'
HISTORICAL_SOURCE = ROOT/'tests/fixtures/catalog/global-before-content-source.json'

def historical_catalog():
    # Frozen global.2 full-export witnesses retain their 218-asset proof boundary.
    # Current catalogs are tested by test_global_content and selected-root cases.
    return build_catalog(ROOT, HISTORICAL_SOURCE)


def svg(body, box='0 0 10 10'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{box}">{body}</svg>'.encode()


def point_distance(p, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    t = max(0, min(1, ((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dy)


class VisualProtocolTest(unittest.TestCase):
    def literal(self):
        return ['SFV', 1, 32, [10,10], [0x112233], [0,320,5243200,5242880], [[0,0,[0,1,2,3]]], [0,[]]]

    def assert_curve(self, value):
        # Exact independent quadratic: (x,y)=(1+10t,11-20t+20t²).
        op=value[6][0]
        points=[(value[5][i]%16384/32,value[5][i]//16384/32) for i in op[2]]
        edges = list(zip(points, points[1:]+points[:1]))
        error = max(min(point_distance((1+10*t/1000, 11-20*t/1000+20*(t/1000)**2), a,b) for a,b in edges) for t in range(1001))
        self.assertLessEqual(error, 1/32 + math.sqrt(2)/64)
        return error



    def test_geometry_positive(self):
        self.assertEqual(export_svg((FIX/'literal.svg').read_bytes(), [10,10]), self.literal())
        # SVG comma-wsp is optional between path numbers, including implicit
        # arguments. Maximal numeric tokens retain sign/decimal/exponent forms.
        for data in ('M0,0 10,0 10,10 0,10z',
                     ' M 0 , 0 L 10 ,0 ,10,10 , 0,10 Z ',
                     'M0+0 10+0 10+10 0+10z',
                     'M0.0.0 10.0.0 10.0.1e2 0.0.1e2z',
                     'M0e0,0E+0H1e1V1E1H0e0z',
                     'm0,0 10,0 0,10 -10,0z'):
            with self.subTest(valid_path_grammar=data):
                self.assertEqual(export_svg(svg('<path fill="#123" d="'+data+'"/>'), [10,10]), self.literal())
        self.assertEqual(export_svg(svg('<path d=""/><path d="  "/><polygon fill="#123" points="0,0 10,0 10,10 0,10" transform="translate(.0,+0), scale(1e0,1.)"/>', '0,0,10,10'), [10,10]), self.literal())
        # Unlike numeric comma-wsp, transform-list uses comma-wsp+.
        self.assertEqual(export_svg(svg('<polygon fill="#123" points="0 0 10 0 10 10 0 10" transform="translate(0),,scale(1)"/>'),[10,10]),self.literal())
        # SVG points allow a negative second coordinate without a separator.
        triangle = ['SFV',1,32,[10,10],[0],[524320,524576,4718624],[[0,0,[0,1,2]]],[0,[]]]
        self.assertEqual(export_svg(svg('<polygon points="1-1 9-1 1,7" transform="translate(0 2)"/>'),[10,10]),triangle)
        line = export_svg(svg('<path d="M2 5H8" fill="none" stroke="#123" stroke-width="2"/>'), [10,10])
        self.assertEqual(line[5], [3145792,3145984,2097408,2097216])
        self.assertEqual(line[6], [[0,0,[0,1,2,3]]])
        curves = export_svg((FIX/'curves.svg').read_bytes(), [12,14])
        self.assert_curve(curves)
        self.assertGreater(len(curves[6]), 10)  # real filled curve and expanded stroke
        nested = export_svg(svg('<g transform="translate(1 1) scale(2)"><svg width="4" height="4" viewBox="0 0 4 4"><rect x="-1" y="-1" width="6" height="6" fill="#123"/></svg></g>'), [10,10])
        self.assertEqual({(p%16384,p//16384) for p in nested[5]}, {(32,32),(288,32),(288,288),(32,288)})
        rounded = export_svg(svg('<rect x="1" y="1" width="8" height="8" rx="2" fill="#123"/>'), [10,10])
        self.assertGreater(len(rounded[6][0][2]), 16)
        self.assertNotIn(32+16384*32,rounded[5])

    def test_geometry_negative(self):
        # Invalid comma placement must reject the whole source, rather than
        # silently repairing malformed supported SVG syntax into geometry.
        for body in ('<path d="M,1 1H9V9H1Z"/>', '<path d="M1,,1H9V9H1Z"/>',
                     '<path d="M1 1H9V9H1Z,"/>', '<path d="M1 1H9V9H1,Z"/>',
                     '<path d="M1 1,H9V9H1Z"/>', '<path d=",M1 1H9V9H1Z"/>',
                     '<polygon points=",1 1 9 1 1 9"/>', '<polygon points="1 1,,9 1 1 9"/>',
                     '<polygon points="1 1 9 1 1 9,"/>',
                     '<rect width="8" height="8" transform="translate(,0)"/>',
                     '<rect width="8" height="8" transform="translate(0,,0)"/>',
                     '<rect width="8" height="8" transform="translate(0,)"/>',
                     '<rect width="8" height="8" transform=",translate(0)"/>',
                     '<rect width="8" height="8" transform="translate(0),"/>',
                     '<rect width="8" height="8" transform="translate(0)scale(1)"/>',
                     '<rect width="8" height="8" transform="translate(0+0)"/>',
                     '<polygon points="1+1 9,1 1,9"/>',
                     '<polygon points="1 1+9 1 1 9"/>',
                     '<polygon points="1.0.1e1 9 1 1 9"/>',
                     '<path d="M١ ١H9V9H1Z"/>'):
            with self.subTest(malformed_source_grammar=body), self.assertRaises(VisualError):
                export_svg(svg(body), [10,10])
        for box in (',0 0 10 10','0 0 10 10,','0 0,,10 10','0+0 10 10'):
            with self.subTest(malformed_viewbox=box), self.assertRaises(VisualError):
                export_svg(svg('<rect width="8" height="8"/>', box),[10,10])
        for body in ('<rect width="10" height="10" rx="2"/>','<path d="M0 0L10 10L0 10L10 0Z"/>', '<path d="M0 0H10V10H0Z M2 2V8H8V2Z"/>', '<rect width="10" height="10" fill-rule="evenodd"/>', '<rect width="10" height="10" transform="scale(1 2)"/>', '<rect width="10" height="10" rx="2" ry="3"/>'):
            with self.subTest(body=body), self.assertRaises(VisualError):
                export_svg(svg(body), [10,10])
        # Control: the independent curve oracle rejects a flattened-to-line fault.
        bad = self.literal(); bad[3] = [10,12]; bad[5]=[5242880,5243200,6291776,6291456]
        with self.assertRaises(AssertionError):
            self.assert_curve(bad)

    def test_codec_positive(self):
        expected = b'["SFV",1,32,[10,10],[1122867],[0,320,5243200,5242880],[[0,0,[0,1,2,3]]],[0,[]]]'
        self.assertEqual(canonical_visual(self.literal()), expected)
        self.assertEqual(visual_digest(self.literal()), hashlib.sha256(expected).hexdigest())
        self.assertEqual(loads_visual(json.dumps(self.literal(), indent=3).encode()), self.literal())
        animated = self.literal(); animated[7] = [2500, [[0,0,0,256],[2500,0,-1024,256]]]
        self.assertEqual(loads_visual(canonical_visual(animated)), animated)

    def test_codec_negative(self):
        for mutate in (lambda x:x.__setitem__(0,'SVG'), lambda x:x.__setitem__(1,2), lambda x:x.__setitem__(2,1), lambda x:x[6][0].__setitem__(0,99), lambda x:x[6][0].__setitem__(1,1), lambda x:x[5].__setitem__(0,False), lambda x:x[5].__setitem__(0,[]), lambda x:x[4].append(x[4][0]), lambda x:x.append({}), lambda x:x.__setitem__(7,[2500,[[1,0,0,256],[2500,0,0,256]]])):
            v=self.literal(); mutate(v)
            with self.subTest(value=v), self.assertRaises(VisualError):validate_visual(v)
        for data in (b'[]', b'{}', b'[NaN]', b'['*9+b'0'+b']'*9, canonical_visual(self.literal()).replace(b'5243200',b'5243200.0'), b'\xff'):
            with self.subTest(data=data[:30]), self.assertRaises(VisualError):loads_visual(data)

    def test_limits_positive(self):
        v=self.literal(); v[6] = [copy.deepcopy(v[6][0]) for _ in range(512)]
        self.assertEqual(metrics(validate_visual(v))['commands'],512)
        ring=[(160,0),(260,30),(320,140),(290,240),(200,320),(100,310),(20,240),(0,140)]
        v=self.literal();v[5]=[x+16384*y for x,y in ring];v[6]=[[0,0,list(range(8))] for _ in range(512)]
        self.assertEqual(metrics(validate_visual(v))['vertexReferences'],4096)
        v=self.literal(); v[7]=[3000,[[i*200,0,0,256] for i in range(16)]]
        validate_visual(v)
        # Independent operation counts: M/H/V/H/Z=5, M/H/L/Z=4.
        # Exact2048 must work when the final operation closes a path or is an
        # implicit repeated line argument after M (which changes to L).
        for body in ('<path d="M1 1H9V9H1Z"/>'*408+'<path d="M1 1H9L1 9Z"/>'*2,
                     '<path d="M1 1H9V9H1Z"/>'*409+'<path d="M1 1 9 1 9 9"/>'):
            with self.subTest(source_command_boundary=body[-60:]):
                self.assertEqual(len(export_svg(svg(body),[10,10])[6]),410)

    def test_limits_negative(self):
        for body in ('<path d="M1 1H9V9H1Z"/>'*409+'<path d="M1 1H9L1 9Z"/>',
                     '<path d="M1 1H9V9H1Z"/>'*409+'<path d="M1 1 9 1 9 9 1 9"/>'):
            with self.subTest(source_commands=2049,final=body[-50:]),self.assertRaisesRegex(VisualError,'source command limit'):
                export_svg(svg(body),[10,10])
        for mutate in (lambda x:x[6].extend([x[6][0]]*512), lambda x:x[6][0].__setitem__(2,[0,1,2]*171), lambda x:x[4].extend(range(32)), lambda x:x[5].__setitem__(0,321), lambda x:x.__setitem__(7,[3001,[[0,0,0,256],[3001,0,0,256]]])):
            v=self.literal();mutate(v)
            with self.subTest(value=str(v)[:40]),self.assertRaises(VisualError):validate_visual(v)
        ring=[(160,0),(260,30),(320,140),(290,240),(200,320),(100,310),(20,240),(0,140),(50,40)]
        v=self.literal();v[5]=[x+16384*y for x,y in ring];v[6]=[[0,0,list(range(8))] for _ in range(512)];v[6][0][2]=list(range(9))
        with self.assertRaisesRegex(VisualError,'total vertex reference'):validate_visual(v)
        for data in (b' '*65537, svg(' '*65536), svg('<path d="'+('M1 1 '*2049)+'"/>'), svg('<g>'*9+'<rect width="1" height="1"/>'+'</g>'*9), svg('<path d="M0 0Q1e99 1 2 2"/>'), svg('<rect width="1" height="1" stroke="#000" stroke-miterlimit="100000"/>')):
            with self.subTest(data=data[:50]), self.assertRaises(VisualError):
                if data.startswith(b' '):loads_visual(data)
                else:export_svg(data,[10,10])

    def test_historical_global2_sources_positive(self):
        c=historical_catalog();before=canonical_bytes(c);pack=build_pack(ROOT,c)
        self.assertEqual(len(pack['manifest']['assets']),218)
        self.assertEqual(pack['manifest']['qualification'],'producer-only-not-device-qualified')
        self.assertEqual(canonical_bytes(c),before)
        for identity,row in c['dictionaries']['assets'].items():
            record=pack['manifest']['assets'][identity]
            self.assertEqual(canonical_bytes(record['catalogRecord']),canonical_bytes(row))
            value=assemble_visual([pack['objects'][part['sha256']] for part in record['shards']],record['animation'])
            data=canonical_visual(value)
            self.assertTrue(all(part['decodedBytes'] <= 4096 for part in record['shards']))
            self.assertEqual(hashlib.sha256(data).hexdigest(),record['sha256'])
            self.assertEqual(canonical_visual(loads_visual(data)),data)
        counts={i:metrics(assemble_visual([pack['objects'][part['sha256']] for part in r['shards']],r['animation']))['commands'] for i,r in pack['manifest']['assets'].items()}
        self.assertGreater(counts['spacefox:asset:ariane-64'],counts['spacefox:asset:ariane-62'])
        self.assertGreater(counts['spacefox:asset:falcon-heavy'],counts['spacefox:asset:falcon-9'])

    def test_all_sources_negative(self):
        # Current selected-source producer guards survive removal of the old
        # registry recipe. Use the actual catalog and one isolated source asset.
        with tempfile.TemporaryDirectory() as directory:
            catalog = build_catalog(ROOT)
            identity = 'spacefox:asset:generic'
            row = catalog['dictionaries']['assets'][identity]
            path = Path(directory) / row['content']['path']
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes((ROOT / row['content']['path']).read_bytes())
            self.assertIn(identity, build_pack(directory, catalog, roots=[identity])['manifest']['assets'])
            path.write_bytes(svg('<path d="M0 0C1 1 2 2 3 3"/>'))
            with self.assertRaisesRegex(VisualError, 'digest'):
                build_pack(directory, catalog, roots=[identity])
            data = path.read_bytes()
            row['content'].update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
            catalog['inputDigests'][row['content']['path']] = row['content']['sha256']
            with self.assertRaisesRegex(VisualError, 'generic.*unsupported|unsupported.*generic'):
                build_pack(directory, catalog, roots=[identity])
        for body in ('<script>alert(1)</script>','<image href="https://x/y"/>','<rect width="1" height="1" onclick="x"/>','<rect width="1" height="1" fill="url(#x)"/>','<style>path{fill:red}</style>'):
            with self.subTest(body=body),self.assertRaises(VisualError):export_svg(svg(body),[10,10])
        with self.assertRaises(VisualError):export_svg(b'<!DOCTYPE svg [<!ENTITY x "abc">]><svg viewBox="0 0 1 1">&x;</svg>',[10,10])

    def test_shards_positive(self):
        literal=self.literal();parts=split_visual(literal)
        self.assertEqual(parts,[canonical_visual(literal)])
        self.assertEqual(assemble_visual(parts),literal)
        source=(ROOT/'assets/rocket-pack/svg/falcon-heavy.svg').read_bytes()
        value=export_svg(source,[54,124]);parts=split_visual(value)
        self.assertGreater(len(parts),1)
        self.assertTrue(all(len(part) <= 4096 for part in parts))
        self.assertEqual(canonical_visual(assemble_visual(parts)),canonical_visual(value))
        # Local shard pools/palettes are independently valid; no global pool parse.
        for part in parts:self.assertEqual(loads_shard(part)[7],[0,[]])

    def test_shards_negative(self):
        with self.assertRaises(VisualError):loads_shard(b' '*4097)
        value=self.literal();value[7]=[2500,[[0,0,0,256],[2500,0,0,256]]]
        with self.assertRaises(VisualError):loads_shard(canonical_visual(value))
        p=build_pack(ROOT,historical_catalog())
        for mode in ('missing','reordered','repeated','canvas','animation'):
            bad=copy.deepcopy(p);row=bad['manifest']['assets']['spacefox:asset:falcon-heavy']
            if mode == 'missing':row['shards'].pop()
            elif mode == 'reordered':row['shards'].reverse()
            elif mode == 'repeated':row['shards'][1]=copy.deepcopy(row['shards'][0])
            elif mode == 'canvas':row['canvas']=[55,124]
            else:row['animation']=None
            with tempfile.TemporaryDirectory() as d, self.subTest(mode=mode), self.assertRaises(VisualError):write_pack(d,bad)

    def test_rights_positive(self):
        p=build_pack(ROOT,historical_catalog());r=p['manifest']['assets']['spacefox:asset:company-spacex']
        self.assertEqual(r['rights']['license'],'MIT')
        self.assertEqual(r['rights']['credit'],r['catalogRecord']['facts']['creator'])
        self.assertIn('sources',r['catalogRecord']['facts'])
        self.assertNotIn('Garmin',r['rights']['admission'])

    def test_rights_negative(self):
        for value in ('',None,'unknown','CC-BY-NC-4.0','MIT OR Proprietary'):
            c=build_catalog(ROOT);c['dictionaries']['assets']['spacefox:asset:generic']['facts']['license']=value
            with self.subTest(license=value),self.assertRaises(VisualError):build_pack(ROOT,c)
        c=build_catalog(ROOT);c['dictionaries']['assets']['spacefox:asset:generic']['facts']['creator']=''
        with self.assertRaises(VisualError):build_pack(ROOT,c)

    def test_selection_positive(self):
        c=historical_catalog();roots=['ll2:configuration:164','ll2:site:65']
        p=build_pack(ROOT,c,roots=roots)
        self.assertNotIn('spacefox:asset:electron',p['manifest']['assets'])
        self.assertEqual(p['manifest']['selection']['dictionaries']['sites']['ll2:site:65']['position']['longitude'],Decimal('177.864469'))
        extra=copy.deepcopy(c);asset=copy.deepcopy(extra['dictionaries']['assets']['spacefox:asset:generic']);asset['facts']['id']='unrelated';asset['provenance'][0]['recordId']='unrelated';extra['dictionaries']['assets']['spacefox:asset:unrelated']=asset
        extra['inputDigests']['unrelated-global-import.json']='0'*64
        extra['source']['reference']['unrelatedGlobalNote']='x'*10000
        self.assertEqual(p['objects'],build_pack(ROOT,extra,roots=roots)['objects'])
        self.assertEqual(p['manifest']['selection'],build_pack(ROOT,extra,roots=roots)['manifest']['selection'])
        p=build_pack(ROOT,extra)
        self.assertEqual(p['manifest']['assets']['spacefox:asset:generic']['sha256'],p['manifest']['assets']['spacefox:asset:unrelated']['sha256'])
        self.assertEqual(p['objects'],build_pack(ROOT,c)['objects'])

    def test_selection_negative(self):
        for roots in ([],['ll2:configuration:999999'],['ll2:configuration:164']*17):
            with self.subTest(roots=roots),self.assertRaises(VisualError):build_pack(ROOT,build_catalog(ROOT),roots=roots)
        c=build_catalog(ROOT);c['dictionaries']['configurations']['ll2:configuration:164']['references']['visual']='ll2:site:65'
        with self.assertRaises(VisualError):build_pack(ROOT,c)


    def test_data_only_negative(self):
        c=build_catalog(ROOT);row=c['dictionaries']['assets']['spacefox:asset:generic'];row['content']['path']='../outside.svg'
        with self.assertRaises(VisualError):build_pack(ROOT,c)

    def test_atomic_positive(self):
        with tempfile.TemporaryDirectory() as d:
            p=build_pack(ROOT,historical_catalog());s=write_pack(d,p)
            manifest=(Path(d)/'manifest.json').read_bytes()
            self.assertEqual(s['objectsWritten'],len(p['objects']))
            s=write_pack(d,p);self.assertEqual(s['objectsReused'],len(p['objects']))
            self.assertEqual((Path(d)/'manifest.json').read_bytes(),manifest)
            command=[sys.executable,'-B',str(ROOT/'tools/export_visuals.py'),'--output',str(Path(d)/'cli'),'--root','ll2:configuration:164']
            run=subprocess.run(command,cwd=d,capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertEqual(json.loads(run.stdout)['qualification'],'producer-only-not-device-qualified')

    def test_atomic_negative(self):
        with tempfile.TemporaryDirectory() as d:
            p=build_pack(ROOT,historical_catalog());write_pack(d,p);path=Path(d)/'manifest.json';old=path.read_bytes()
            def fail(stage):raise OSError('injected before local activation')
            with self.assertRaises(OSError):write_pack(d,p,fault=fail)
            self.assertEqual(path.read_bytes(),old)
            bad=copy.deepcopy(p);key=next(iter(bad['objects']));bad['objects'][key]=b'corrupt'
            with self.assertRaises(VisualError):write_pack(d,bad)
            self.assertEqual(path.read_bytes(),old)
            bad=copy.deepcopy(p);bad['manifest']['assets']['spacefox:asset:generic']['rights']['license']='unknown'
            with self.assertRaises(VisualError):write_pack(d,bad)
            self.assertEqual(path.read_bytes(),old)
            bad=copy.deepcopy(p);bad['manifest']['assets']['spacefox:asset:generic']['catalogRecord']['facts']['creator']='different creator'
            with self.assertRaises(VisualError):write_pack(d,bad)
            self.assertEqual(path.read_bytes(),old)
            object_path=Path(d)/'objects'/(key+'.json');object_path.write_bytes(b'corrupt existing')
            with self.assertRaises(VisualError):write_pack(d,p)
            self.assertEqual(path.read_bytes(),old)
            self.assertFalse(list(Path(d).glob('.manifest-*')))
