"""Literal projection vectors and complete current/retained artifact boundary."""
import copy
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json, validate_catalog
from tools.spacefox.global_map import (GeographyError, build_bundle, build_site_view,
                                      load_world, project, write_bundle)
from tools.spacefox.graphics import build_pack, loads_shard

ROOT=Path(__file__).resolve().parents[1]


class GlobalMapTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=build_catalog(ROOT)

    def test_projection_positive(self):
        self.assertEqual(project(0,0),(128,128))
        self.assertEqual(project(90,-180),(1,1))
        self.assertEqual(project(-90,180),(1,255))
        self.assertEqual(project(0,90,kind='globe'),(255,128))
        self.assertIsNone(project(0,180,kind='globe'))
        for lat,lon in [(90,180),(-90,-180),(Decimal('0.00000000000001'),Decimal('179.99999999999999'))]:
            x,y=project(lat,lon,kind='globe',center=(lat,lon))
            self.assertAlmostEqual(x,128);self.assertAlmostEqual(y,128)
        # Explicit archive scope renders map/globe contexts for every numeric source row.
        # Current event/program scope has a separate source-dated nonempty oracle.
        # The file is reusable evidence, not a fixed image chosen for five sites.
        target=ROOT/'build/global-site-audit.json'
        completed=subprocess.run([sys.executable,'-B',str(ROOT/'tools/build_global_map.py'),'--audit','--scope','archive','--output',str(target)],cwd=tempfile.gettempdir(),capture_output=True,text=True,timeout=180)
        self.assertEqual(completed.returncode,0,completed.stderr)
        report=loads_json(target.read_bytes())
        self.assertEqual((report['siteRows'],report['numericSourcePairs'],report['unknownPositions']),(218,213,5))
        self.assertEqual((report['mobileReferenceOnly'],report['eventPointEligible']),(29,185))
        self.assertEqual((report['fixedNumericPairs'],report['mobileNumericPairs'],report['fixedUnknownPositions'],report['mobileUnknownPositions']),(185,28,4,1))
        self.assertEqual({r['id'] for r in report['rows'] if r['positionMode']=='mobile-reference-no-event' and r['sourcePosition'] is None},{'ll2:site:101'})
        self.assertTrue(report['contextsRendered'])
        self.assertIsNone(report['independentlyVerifiedCoordinateAccuracy'])
        source_ids={r['id'] for r in report['rows'] if r['sourcePosition'] is not None}
        self.assertEqual(len(source_ids),213)
        self.assertTrue(all(r['maxShardBytes']<=4096 and r['globe']==[4096,4096] for r in report['rows'] if r['sourcePosition'] is not None))
        for identity in ['ll2:site:65','ll2:site:80','ll2:site:13']:
            view=build_site_view(ROOT,self.catalog,identity,kind='globe')
            self.assertEqual(view['manifest']['site']['id'],identity)
            if identity!='ll2:site:13':self.assertEqual(view['manifest']['marker'],[4096,4096])
        view=build_site_view(ROOT,self.catalog,'ll2:site:13')
        self.assertIsNone(view['manifest']['marker'])
        self.assertEqual(canonical_bytes(view['manifest']['site']['sourcePosition']),canonical_bytes(self.catalog['dictionaries']['sites']['ll2:site:13']['position']))
        row=self.catalog['dictionaries']['sites']['ll2:site:13']
        self.assertEqual(view['manifest']['site']['sourceUrl'],row['facts']['sourceUrl'])
        self.assertEqual(view['manifest']['site']['definitionSha256'],hashlib.sha256(canonical_bytes(row)).hexdigest())
        # An explicit, sourced event position is separate from the reference.
        event={'latitude':Decimal('0.0000'),'longitude':Decimal('-154.1234567890123456789'),'sources':['https://example.org/official-event-position']}
        moving=build_site_view(ROOT,self.catalog,'ll2:site:13',event_position=event)
        self.assertIsNotNone(moving['manifest']['marker'])
        self.assertEqual(moving['manifest']['site']['eventPosition'],event)
        self.assertIsNone(build_site_view(ROOT,self.catalog,'ll2:site:101')['manifest']['marker'])

    def test_projection_negative(self):
        for a,b in [(Decimal('NaN'),0),(0,Decimal('Infinity')),(True,0),(0,False),(91,0),(0,-181),(0.0,0)]:
            with self.assertRaises(GeographyError):project(a,b)
        with self.assertRaises(GeographyError):project(0,0,kind='mercator-guessed')
        with self.assertRaises(GeographyError):build_site_view(ROOT,self.catalog,'ll2:site:999999')
        for event in [{'latitude':0,'longitude':0}, {'latitude':0,'longitude':0,'sources':[]}, {'latitude':91,'longitude':0,'sources':['https://example.org/a']}]:
            with self.assertRaises(GeographyError):build_site_view(ROOT,self.catalog,'ll2:site:13',event_position=event)
        bad=copy.deepcopy(self.catalog);bad['source']['geography']['sha256']='0'*64
        with self.assertRaises(GeographyError):load_world(ROOT,bad)

    def test_selection_positive(self):
        catalog=self.catalog;site='ll2:site:65'
        view=build_site_view(ROOT,catalog,site)
        visuals=build_pack(ROOT,catalog,roots=['ll2:configuration:164','ll2:site:65'])
        c=copy.deepcopy(catalog)
        # An unrelated curated site with a real typed country is valid growth.
        row=copy.deepcopy(c['dictionaries']['sites']['spacefox:site:esrange-sounding-area'])
        row['facts']['sourceId']='unrelated-new-global-site';row['facts']['name']='Unrelated source addition';row['references']={'country':'ll2:country:15','agencies':['ll2:organization:151']}
        c['dictionaries']['sites']['spacefox:site:unrelated-new-global-site']=row
        validate_catalog(c)
        after=build_site_view(ROOT,c,site)
        self.assertEqual(canonical_bytes(after['manifest']),canonical_bytes(view['manifest']))
        self.assertEqual(after['objects'],view['objects'])
        grown=build_pack(ROOT,c,roots=['ll2:configuration:164','ll2:site:65'])
        self.assertEqual(len(canonical_bytes(visuals['manifest'])),len(canonical_bytes(grown['manifest'])))
        self.assertEqual(visuals['objects'],grown['objects'])
        self.assertLessEqual(len(canonical_bytes(view['manifest'])),8192)
        self.assertTrue(all(len(b)<=4096 and loads_shard(b) for b in view['objects'].values()))
        mobile=build_site_view(ROOT,catalog,'ll2:site:13')
        unknown=build_site_view(ROOT,catalog,'ll2:site:101')
        event={'latitude':Decimal('0.0000'),'longitude':Decimal('-179.9999999999999999'),
               'sources':['https://example.org/literal-event-point']}
        moving=build_site_view(ROOT,catalog,'ll2:site:13',kind='globe',event_position=event)
        self.assertIsNone(mobile['manifest']['marker']);self.assertIsNone(unknown['manifest']['marker'])
        self.assertEqual(moving['manifest']['marker'],[4096,4096])
        build_bundle(None,[mobile,unknown,moving])
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)/'first';first=build_bundle(visuals,[view]);write_bundle(directory,first)
            # A replacement selection retains exactly the previous required closure.
            globe=build_site_view(ROOT,catalog,'ll2:site:80',kind='globe')
            next_bundle=build_bundle(None,[globe],previous_directory=directory)
            self.assertLessEqual(next_bundle['artifactBytes'],1048576)
            self.assertEqual(next_bundle['manifest']['previous'],first['manifest']['current'])
            self.assertTrue(set(first['files'])<=set(next_bundle['files']))
            self.assertEqual(next_bundle['artifactBytes'],len(canonical_bytes(next_bundle['manifest']))+sum(map(len,next_bundle['files'].values())))
            next_dir=Path(tmp)/'second';write_bundle(next_dir,next_bundle)
            third=build_bundle(None,[view],previous_directory=next_dir)
            self.assertEqual(third['manifest']['previous'],next_bundle['manifest']['current'])
            # One prior selection, rather than an indefinitely growing chain.
            self.assertEqual(set(third['files']),set(build_bundle(None,[view])['files'])|set(next_bundle['manifest']['currentFiles']))

    def test_selection_negative(self):
        view=build_site_view(ROOT,self.catalog,'ll2:site:65')
        for change in ('schema','missing','digest','orphan','oversize'):
            bad=copy.deepcopy(view)
            if change=='schema':bad['manifest']['rendererVersion']=2
            elif change=='missing':bad['objects'].pop(next(iter(bad['objects'])))
            elif change=='digest':bad['manifest']['layers'][0]['sha256']='0'*64
            elif change=='orphan':bad['objects']['0'*64]=next(iter(bad['objects'].values()))
            else:bad['manifest']['padding']='x'*8192
            with self.subTest(change=change),self.assertRaises(GeographyError):build_bundle(None,[bad])
        with self.assertRaises(GeographyError):build_bundle(None,[view]*5)
        for defect in ('marker-range','marker-alignment','site-position','projection-kind','site-identity',
                       'missing-position','mobile-reference','event-source','projection-center','site-binding'):
            bad=copy.deepcopy(view)
            if defect=='marker-range':bad['manifest']['marker']=[999999,-1]
            elif defect=='marker-alignment':bad['manifest']['marker']=[128,128]
            elif defect=='site-position':bad['manifest']['site']['sourcePosition']['latitude']=999
            elif defect=='projection-kind':bad['manifest']['projection']['kind']='not-a-map'
            elif defect=='site-identity':bad['manifest']['site']['id']='ll2:organization:65'
            elif defect=='missing-position':bad['manifest']['site']['sourcePosition']=None
            elif defect=='mobile-reference':bad['manifest']['site']['positionMode']='mobile-reference-no-event'
            elif defect=='event-source':bad['manifest']['site']['eventPosition']={'latitude':0,'longitude':0,'sources':[]}
            elif defect=='projection-center':bad['manifest']['projection']['center']=[0,90]
            else:bad['manifest']['site']['definitionSha256']='not-a-digest'
            with self.subTest(metadata=defect),self.assertRaises(GeographyError):build_bundle(None,[bad])
        # Fresh content addresses do not exempt current or retained site metadata
        # from admission, and no candidate failure changes the accepted output.
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);good=build_bundle(None,[view]);write_bundle(path,good)
            accepted={p:p.read_bytes() for p in path.rglob('*.json')}
            bad=copy.deepcopy(good);old=bad['manifest']['current']['geography'][0]
            record=loads_json(bad['files'].pop(old));record['marker']=[999999,-1]
            data=canonical_bytes(record);new='manifests/'+hashlib.sha256(data).hexdigest()+'.json'
            bad['files'][new]=data;bad['manifest']['files'].pop(old)
            bad['manifest']['files'][new]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
            bad['manifest']['current']['geography']=[new]
            bad['manifest']['currentFiles'].remove(old);bad['manifest']['currentFiles'].append(new)
            bad['artifactBytes']=len(canonical_bytes(bad['manifest']))+sum(map(len,bad['files'].values()))
            with self.assertRaises(GeographyError):write_bundle(path,bad)
            self.assertTrue(all(p.read_bytes()==data for p,data in accepted.items()))
            (path/new).write_bytes(data);(path/'manifest.json').write_bytes(canonical_bytes(bad['manifest']))
            with self.assertRaises(GeographyError):build_bundle(None,[view],previous_directory=path)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);bundle=build_bundle(None,[view]);write_bundle(path,bundle);before=(path/'manifest.json').read_bytes()
            tampered=copy.deepcopy(bundle);name=next(p for p in tampered['files'] if p.startswith('objects/'));tampered['files'][name]=b'corrupt'
            with self.assertRaises(GeographyError):write_bundle(path,tampered)
            self.assertEqual((path/'manifest.json').read_bytes(),before)
            object_path=next(p for p in bundle['files'] if p.startswith('objects/'))
            (path/object_path).write_bytes(b'corrupt')
            with self.assertRaises(GeographyError):build_bundle(None,[view],previous_directory=path)
            self.assertEqual((path/'manifest.json').read_bytes(),before)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);bundle=build_bundle(None,[view]);write_bundle(path,bundle)
            # A self-consistent index that omits a referenced object is incomplete.
            root=json.loads((path/'manifest.json').read_text());missing=next(p for p in root['currentFiles'] if p.startswith('objects/'));root['currentFiles'].remove(missing)
            (path/'manifest.json').write_text(json.dumps(root))
            with self.assertRaisesRegex(GeographyError,'referenced object missing'):build_bundle(None,[view],previous_directory=path)
        # Metadata with freshly recomputed file pins must still satisfy rights,
        # geometry metadata and exact current-file closure before activation.
        visuals=build_pack(ROOT,self.catalog,roots=['ll2:configuration:164'])
        bundle=build_bundle(visuals,[view])
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);write_bundle(path,bundle);before=(path/'manifest.json').read_bytes()
            for defect in ('rights','canvas','path-missing','path-mismatch','path-external','current-index','orphan'):
                with self.subTest(defect=defect):
                    write_bundle(path,bundle)
                    bad=copy.deepcopy(bundle)
                    if defect in ('rights','canvas','path-missing','path-mismatch','path-external'):
                        old=bad['manifest']['current']['visual'];record=loads_json(bad['files'].pop(old))
                        asset=next(iter(record['assets'].values()))
                        if defect=='rights':asset['rights']['license']='unknown'
                        elif defect=='canvas':asset['canvas']=[1,1]
                        elif defect=='path-missing':asset['shards'][0].pop('path')
                        elif defect=='path-mismatch':asset['shards'][0]['path']='objects/'+'0'*64+'.json'
                        else:asset['shards'][0]['path']='https://example.invalid/geometry.json'
                        data=canonical_bytes(record);new='manifests/'+hashlib.sha256(data).hexdigest()+'.json'
                        bad['files'][new]=data;bad['manifest']['files'].pop(old)
                        bad['manifest']['files'][new]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
                        bad['manifest']['current']['visual']=new
                        bad['manifest']['currentFiles'].remove(old);bad['manifest']['currentFiles'].append(new)
                    elif defect=='current-index':bad['manifest']['currentFiles']=[]
                    else:
                        new='manifests/'+hashlib.sha256(b'{}').hexdigest()+'.json';bad['files'][new]=b'{}'
                        bad['manifest']['files'][new]={'sha256':hashlib.sha256(b'{}').hexdigest(),'bytes':2}
                    bad['artifactBytes']=len(canonical_bytes(bad['manifest']))+sum(map(len,bad['files'].values()))
                    with self.assertRaises(GeographyError):write_bundle(path,bad)
                    self.assertEqual((path/'manifest.json').read_bytes(),before)
            # A self-consistent retained index is not an exemption from admission.
            for defect in ('rights','path-missing','path-mismatch','path-external'):
                with self.subTest(retained=defect):
                    old=bundle['manifest']['current']['visual'];record=loads_json(bundle['files'][old])
                    asset=next(iter(record['assets'].values()))
                    if defect=='rights':asset['rights']['license']='unknown'
                    elif defect=='path-missing':asset['shards'][0].pop('path')
                    elif defect=='path-mismatch':asset['shards'][0]['path']='objects/'+'0'*64+'.json'
                    else:asset['shards'][0]['path']='https://example.invalid/geometry.json'
                    data=canonical_bytes(record);new='manifests/'+hashlib.sha256(data).hexdigest()+'.json'
                    root=copy.deepcopy(bundle['manifest']);root['current']['visual']=new
                    root['currentFiles'].remove(old);root['currentFiles'].append(new);root['files'].pop(old)
                    root['files'][new]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
                    (path/new).write_bytes(data);(path/'manifest.json').write_bytes(canonical_bytes(root))
                    with self.assertRaises(GeographyError):build_bundle(None,[view],previous_directory=path)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp);write_bundle(path,bundle)
            accepted={p:p.read_bytes() for p in path.rglob('*.json')}
            with patch('tools.spacefox.graphics.os.replace',side_effect=OSError('literal activation fault')):
                with self.assertRaises(OSError):write_bundle(path,build_bundle(None,[view]))
            self.assertTrue(all(p.read_bytes()==data for p,data in accepted.items()))
        # Both individual global packs fit, but retaining two complete global
        # manifests exceeds the real 1MiB artifact even with object reuse.
        # The bounded selected route above remains admissible.
        historical=build_catalog(ROOT,ROOT/'tests/fixtures/catalog/global-before-content-source.json')
        full=build_pack(ROOT,historical)
        with tempfile.TemporaryDirectory() as tmp:
            first=build_bundle(full,[]);self.assertLessEqual(first['artifactBytes'],1048576);write_bundle(tmp,first)
            changed=copy.deepcopy(historical);changed['catalogVersion']=historical['catalogVersion']+'.next'
            replacement=build_pack(ROOT,changed)
            self.assertNotEqual(hashlib.sha256(canonical_bytes(full['manifest'])).hexdigest(),
                                hashlib.sha256(canonical_bytes(replacement['manifest'])).hexdigest())
            self.assertEqual(full['objects'],replacement['objects'])
            self.assertLessEqual(build_bundle(replacement,[])['artifactBytes'],1048576)
            # Even before the root envelope/index is counted, the two distinct
            # manifests plus their shared objects exceed the artifact allowance.
            self.assertGreater(len(canonical_bytes(full['manifest']))+
                               len(canonical_bytes(replacement['manifest']))+
                               sum(map(len,full['objects'].values())),1048576)
            with self.assertRaisesRegex(GeographyError,'1048576'):
                build_bundle(replacement,[],previous_directory=tmp)


if __name__=='__main__':unittest.main()
