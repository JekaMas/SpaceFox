"""Literal island/context controls, exact facts, camera, and bounded source closure."""
import copy
from decimal import Decimal
import hashlib
import tempfile
from pathlib import Path
import unittest

from tools.spacefox.catalog import build_catalog, canonical_bytes as exact_bytes, loads_json
from tools.spacefox.global_map import GeographyError, load_world, build_site_view
from tools.spacefox.geographic_context import (load_source, build_view, build_artifact,
    canonical_bytes, project_profile, dependencies)
from tools.build_geographic_context import write_artifact, read_artifact
from tools.spacefox.graphics import assemble_visual, PACK_BASE

ROOT=Path(__file__).resolve().parents[1]
RECIPE=ROOT/'catalog/geography/context-candidate-20261112.json'


def contains(ring,x,y):
    """Independent even-odd crossing oracle on the original source polygon."""
    result=False
    for a,b in zip(ring,ring[1:]):
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            result=not result
    return result


class GeographicContextTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=build_catalog(ROOT,RECIPE)
        cls.source=load_source(ROOT,cls.catalog['source']['geography'])

    def test_source_and_literal_island_context(self):
        source=self.source
        self.assertEqual((source['index']['sourceRecords'],source['index']['sourceVertices']),(12763,149103))
        self.assertEqual(len(source['supplements']),731)
        self.assertEqual(len({r['feature'] for r in source['supplements']}),731)
        island=next(r for r in source['supplements'] if r['feature']=='mh_spc_all_shoreline.482')
        self.assertEqual(len(island['coordinates']),23)
        self.assertTrue(contains(island['coordinates'],Decimal('167.743'),Decimal('9.047861')))
        # An actual original vertex, independently fixed before producer rendering.
        self.assertEqual(island['coordinates'][0],[Decimal('167.742292'),Decimal('9.046696')])
        self.assertEqual(source['index']['sourceDate'],'2017-06-15')
        self.assertEqual(source['supplementNotices'][0]['sourceDate'],'2016-01-25')
        for name in ('LICENSE.TXT','COPYINGv3','COPYING.LESSERv3','README.TXT'):
            self.assertTrue(source['notices'][name])
        for pin in dependencies(source):
            self.assertEqual(hashlib.sha256((ROOT/pin['path']).read_bytes()).hexdigest(),pin['sha256'])
        # Current source facts and recipe remain untouched; candidate is explicit.
        old=build_catalog(ROOT)
        self.assertEqual({i:r['position'] for i,r in old['dictionaries']['sites'].items()},
                         {i:r['position'] for i,r in self.catalog['dictionaries']['sites'].items()})
        self.assertEqual(len(load_world(ROOT,old)['lines']),594)
        with self.assertRaisesRegex(GeographyError,'offwatch context producer'):
            build_site_view(ROOT,self.catalog,'ll2:site:107')

    def test_all_required_source_context_and_marker_visibility(self):
        # Every current row is visited; mobiles are diagnostic source-centered
        # context only, with no invented event position or marker.
        numeric=fixed=mobile=unknown=0
        observations=[]
        for identity,site in self.catalog['dictionaries']['sites'].items():
            if site['position'] is None:
                unknown+=1
                v=build_view(ROOT,self.catalog,identity)
                self.assertIsNone(v['manifest']['marker'])
                continue
            numeric+=1
            eligible=site['facts'].get('positionMode','fixed-source')=='fixed-source'
            if eligible:fixed+=1
            else:mobile+=1
            for kind in ('map','globe'):
                with self.subTest(identity=identity,kind=kind):
                    v=build_view(ROOT,self.catalog,identity,kind=kind,reference_context=not eligible)
                    self.assertEqual(v['manifest']['marker'],[335,165] if eligible else None)
                    self.assertEqual(v['manifest']['site']['sourcePosition'],site['position'])
                    self.assertEqual(exact_bytes(v['manifest']['site']['sourcePosition']),exact_bytes(site['position']))
                    self.assertTrue(v['segments'])
                    # Suitable-local-context discriminator: actual clipped line
                    # within 60px of literal anchor; finite bounds alone cannot pass.
                    ink=[]
                    for layer in v['manifest']['layers']:
                        value=assemble_visual([v['files']['objects/'+p['sha256']+'.json'] for p in layer['shards']],[0,[]])
                        for command in value[6]:
                            points=[((value[5][i]%PACK_BASE)/32*390/256,(value[5][i]//PACK_BASE)/32*390/256) for i in command[2]]
                            for a,b in zip(points,points[1:]+points[:1]):
                                dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
                                t=0 if den==0 else max(0,min(1,((335-a[0])*dx+(165-a[1])*dy)/den))
                                x,y=a[0]+t*dx,a[1]+t*dy
                                if (x-195)**2+(y-195)**2 < 194**2:ink.append(((x-335)**2+(y-165)**2)**.5)
                    self.assertTrue(ink)
                    self.assertLess(min(ink),60)
                    observations.append({'id':identity,'kind':kind,'marker':v['manifest']['marker'],'minimumVisibleInkDistancePx':Decimal(str(min(ink))),
                                         'manifestBytes':len(canonical_bytes(v['manifest'])),'sourcePosition':site['position'],
                                         'artifactBytes':build_artifact([v])['artifactBytes'],'context':v['manifest']['context']})
                    self.assertTrue(all(0<=p[0]<=390 and 0<=p[1]<=390 for segment in v['segments'] for p in segment))
                    self.assertLessEqual(len(canonical_bytes(v['manifest'])),8192)
                    self.assertTrue(all(len(raw)<=4096 for path,raw in v['files'].items() if path.startswith('objects/')))
                    self.assertLessEqual(build_artifact([v])['artifactBytes'],1048576)
        self.assertEqual((numeric,fixed,mobile,unknown),(213,185,28,5))
        output=ROOT/'build/geographic-context/all-required-observations.json'
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_bytes(canonical_bytes({'qualification':'offwatch-regional-SFV-visible-ink-not-native-or-pad-survey','numericPairs':numeric,'fixedMarkers':fixed,'mobileNumericNoMarker':mobile,'unknownNoMarker':unknown,'rows':observations}))

    def test_old_source_control_and_mobile_omission(self):
        old=load_world(ROOT,build_catalog(ROOT))
        for identity in ('ll2:site:59','ll2:site:104','ll2:site:107'):
            pos=self.catalog['dictionaries']['sites'][identity]['position'];x,y=pos['longitude'],pos['latitude']
            # Literal R1 control: zero old source segments even in a 2° square.
            intersect=sum(not(max(a[0],b[0])<x-1 or min(a[0],b[0])>x+1 or max(a[1],b[1])<y-1 or min(a[1],b[1])>y+1)
                          for line in old['lines'] for a,b in zip(line,line[1:]))
            self.assertEqual(intersect,0)
            v=build_view(ROOT,self.catalog,identity,reference_context=True)
            self.assertGreater(v['manifest']['context']['selectedSourceClips'],0)
            self.assertLess(v['manifest']['context']['nearestHighResolutionCoastDegrees'],Decimal('.03'))
            if identity!='ll2:site:107':
                self.assertIsNone(v['manifest']['marker'])
                self.assertIsNone(v['manifest']['site']['eventPosition'])
                self.assertIsNone(build_view(ROOT,self.catalog,identity)['manifest']['marker'])
        for lat,lon in [(90,180),(-90,-180),(0,Decimal('179.999999999999999999')),(Decimal('-0.0000'),0)]:
            for kind in ('map','globe'):
                self.assertEqual(project_profile(lat,lon,kind=kind,center=(lat,lon),scale=145),(335,165))
        # The accepted full camera is an actual separate profile, not a 256-square
        # projection relabeled as owner/native acceptance.
        accepted=build_view(ROOT,self.catalog,'ll2:site:107',profile='accepted04-full')
        with self.assertRaisesRegex(GeographyError,'map only'):
            build_view(ROOT,self.catalog,'ll2:site:107',profile='accepted04-full',kind='globe')
        self.assertEqual(accepted['manifest']['camera']['scale'],145)
        self.assertEqual(accepted['manifest']['marker'],[335,165])
        self.assertLess((335-195)**2+(165-195)**2,(195-10)**2)

    def test_source_validation_negatives(self):
        pin=self.catalog['source']['geography']
        bad=copy.deepcopy(pin);bad['sha256']='0'*64
        with self.assertRaises(GeographyError):load_source(ROOT,bad)
        # Cached decode must not bypass an actual changed dependency.
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for p in [pin,*dependencies(self.source)]:
                target=root/p['path'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/p['path']).read_bytes())
            load_source(root,pin)
            first=self.source['index']['clips'][0]['path'];(root/first).write_bytes(b'corrupt')
            with self.assertRaisesRegex(GeographyError,'digest mismatch'):load_source(root,pin)
        for lat,lon in [(True,0),(Decimal('NaN'),0),(91,0),(0,181),(0.0,0)]:
            with self.assertRaises(GeographyError):project_profile(lat,lon,kind='map',center=(0,0),scale=145)
        with self.assertRaises(GeographyError):build_view(ROOT,self.catalog,'ll2:site:999999')
        with self.assertRaises(GeographyError):build_view(ROOT,self.catalog,'ll2:site:107',event_position={'latitude':0,'longitude':0,'sources':[]})
        with self.assertRaisesRegex(GeographyError,'outside derived source coverage'):
            build_view(ROOT,self.catalog,'ll2:site:107',event_position={'latitude':90,'longitude':0,'sources':['https://example.org/explicit-test-event']})

    def test_complete_current_retained_bounds(self):
        views=[build_view(ROOT,self.catalog,s,kind=k,reference_context=s!='ll2:site:107')
               for s in ('ll2:site:107','ll2:site:104') for k in ('map','globe')]
        first=build_artifact(views)
        next_views=[build_view(ROOT,self.catalog,s,kind=k,reference_context=s=='ll2:site:59')
                    for s in ('ll2:site:65','ll2:site:59') for k in ('map','globe')]
        second=build_artifact(next_views,first)
        self.assertLessEqual(second['artifactBytes'],1048576)
        self.assertEqual(second['artifactBytes'],len(canonical_bytes(second['manifest']))+sum(map(len,second['files'].values())))
        self.assertEqual(second['manifest']['previous'],first['manifest']['current'])
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);write_artifact(path,second)
            read_artifact(path)
            before=(path/'preview-artifact.json').read_bytes()
            bad=copy.deepcopy(second);p=next(p for p in bad['files'] if p.startswith('sources/'));bad['files'][p]=b'corrupt'
            with self.assertRaises(GeographyError):write_artifact(path,bad)
            self.assertEqual((path/'preview-artifact.json').read_bytes(),before)

    def test_descriptor_and_closure_negatives(self):
        view=build_view(ROOT,self.catalog,'ll2:site:107')
        for defect in ('marker','camera','missing-source','missing-shard','rights','budget'):
            with self.subTest(defect=defect):
                bad=copy.deepcopy(view)
                if defect=='marker':bad['manifest']['marker']=[0,0]
                elif defect=='camera':bad['manifest']['camera']['center']=[0,0]
                elif defect=='missing-source':bad['files'].pop(bad['manifest']['source']['path'])
                elif defect=='missing-shard':bad['files'].pop(next(p for p in bad['files'] if p.startswith('objects/')))
                elif defect=='rights':
                    p=bad['manifest']['source']['path'];proof=loads_json(bad['files'][p]);bad['files'].pop(proof['common']['path'])
                else:bad['manifest']['padding']='x'*8192
                with self.assertRaises(GeographyError):build_artifact([bad])
        # Recompute all digests: valid byte integrity must not bypass semantic
        # profile/rights admission when importing an otherwise complete preview.
        for defect in ('accepted-globe','unknown-supplement-rights','missing-supplement-rights','empty-notice'):
            with self.subTest(defect=defect):
                bad=copy.deepcopy(view)
                proof_pin=bad['manifest']['source']
                proof=loads_json(bad['files'][proof_pin['path']])
                common_pin=proof['common']
                common=loads_json(bad['files'][common_pin['path']])
                if defect=='accepted-globe':
                    bad['manifest']['camera'].update(kind='globe',profile='accepted04-full',scale=145)
                elif defect=='unknown-supplement-rights':common['supplementNotices'][0]['license']='unknown'
                elif defect=='missing-supplement-rights':common['supplementNotices']=[]
                else:common['notices']['LICENSE.TXT']=''
                for value,pin in ((common,common_pin),(proof,proof_pin)):
                    raw=canonical_bytes(value);bad['files'].pop(pin['path'])
                    digest=hashlib.sha256(raw).hexdigest()
                    pin.update(path='sources/'+digest+'.json',sha256=digest,decodedBytes=len(raw))
                    bad['files'][pin['path']]=raw
                with self.assertRaises(GeographyError):build_artifact([bad])
                accepted=build_artifact([view])
                # Simulate a complete external artifact with internally correct
                # digests, bypassing the producer to test both persisted ports.
                files=dict(bad['files']);raw=canonical_bytes(bad['manifest'])
                descriptor='manifests/'+hashlib.sha256(raw).hexdigest()+'.json';files[descriptor]=raw
                envelope=copy.deepcopy(accepted['manifest'])
                envelope.update(current=[descriptor],currentFiles=sorted(files),
                                files={p:{'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b)} for p,b in files.items()})
                forged={'manifest':envelope,'files':files}
                with tempfile.TemporaryDirectory() as tmp:
                    directory=Path(tmp);write_artifact(directory,accepted)
                    before=(directory/'preview-artifact.json').read_bytes()
                    with self.assertRaises(GeographyError):write_artifact(directory,forged)
                    self.assertEqual((directory/'preview-artifact.json').read_bytes(),before)
                    for p,raw in files.items():
                        target=directory/p;target.parent.mkdir(exist_ok=True);target.write_bytes(raw)
                    (directory/'preview-artifact.json').write_bytes(canonical_bytes(envelope))
                    with self.assertRaises(GeographyError):read_artifact(directory)
