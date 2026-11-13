"""Exact BLK3 data/art boundary; no primary-source, SDK or deployment inference."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tools.spacefox.catalog import build_catalog, canonical_bytes, loads_json
from tools.spacefox.current_catalog import current_coverage, load_registry
from tools.spacefox.current_context import load_contexts
from tools.spacefox.graphics import assemble_visual, build_pack
from tools.spacefox.native_profile import rasterize, encode_raster, decode_raster
from tests.test_current_catalog_next import filesystem
from tests.test_global_catalog import temporary_catalog

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'openspec/changes/spacefox-watchface/evidence/blk3-art-whole'
MODEL='spacefox:configuration:exos-blk3'
ASSET='spacefox:asset:exos-blk3-july2026-r1'
CURATION='assets/global/curation-20261113-blk3-r1.json'






def independent_pixels(chunks,width,height,channels):
    # Deliberately separate decoder: materialize rows from literal token semantics,
    # never call the producer decoder/encoder or derive expected pixels from hash.
    allrows=[]
    for blob in chunks:
        signature,start,count,encoded=blob.split(b':',3)
        assert signature==b'SFR1' and int(start)==len(allrows)
        stream=iter(base64.b64decode(encoded,validate=True));prior=[tuple([0]*channels)]*width
        for _ in range(int(count)):
            line=[]
            while len(line)<width:
                token=next(stream);length=(token%128)+1
                if token>=128:line+=prior[len(line):len(line)+length]
                else:line += [tuple(next(stream) for _ in range(channels))]*length
            assert len(line)==width;allrows.append(line);prior=line
        assert list(stream)==[]
    assert len(allrows)==height
    return bytes(c for line in allrows for pixel in line for c in pixel)

class Blk3ArtWholeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before=build_catalog(ROOT,HERE/'global20-source.json')
        cls.after=build_catalog(ROOT)

    def test_exact_current_mapping_geometry_and_counts(self):
        c=self.after;report=current_coverage(c,load_registry(ROOT,c))
        self.assertEqual((len(c['dictionaries']['configurations']),len(c['dictionaries']['assets']),len(c['dictionaries']['sites'])),(211,657,218))
        self.assertEqual((report['currentConfigurations'],report['specificArtMapped'],len(report['missingSpecificArtIds'])),(152,147,5))
        self.assertEqual(set(report['missingSpecificArtIds']),{'ll2:configuration:30','ll2:configuration:152','ll2:configuration:200','spacefox:configuration:nglv-solid-strap-ons','spacefox:configuration:sls-centaur-exploration'})
        self.assertIsNone(self.before['dictionaries']['configurations'][MODEL]['references']['visual'])
        self.assertEqual(c['dictionaries']['configurations'][MODEL]['references']['visual'],ASSET)
        facts=c['dictionaries']['assets'][ASSET]['facts']
        self.assertEqual(facts['coverage']['configurationIds'],[MODEL])
        self.assertEqual((facts['license'],facts['exportSize']),('MIT',[64,128]))
        self.assertEqual(facts['geometryReference']['representativeDate'],'2026-07')
        import xml.etree.ElementTree as ET
        svg=ET.fromstring((ROOT/c['dictionaries']['assets'][ASSET]['content']['path']).read_bytes())
        parts={n.attrib['data-part']:n.attrib for n in svg}
        self.assertEqual(set(parts),{'nose-recovery','cylindrical-body','neutral-shade','payload-computer-boundary','computer-pressure-boundary','pressure-lox-boundary','lox-fuel-boundary','fuel-fin-boundary','visible-fin-left','visible-fin-right'})
        self.assertIn('M32 6',parts['nose-recovery']['d'])
        self.assertIn('L35.4 122L28.6 122',parts['cylindrical-body']['d'])
        # Independent dimensional arithmetic: source116px=10.82m,635mm width.
        self.assertAlmostEqual(6.8/116,.635/10.82,delta=.0002)
        for length,endpoint in zip((1.68,3.08,3.46,5.11,7.36,9.62),(24.01,39.02,43.09,60.78,84.90,109.13)):
            self.assertAlmostEqual(6+116*length/10.82,endpoint,delta=.01)

    def test_all_old_rows_bytes_eligibility_roles_context_and_falcon9_retained(self):
        a,b=self.before,self.after
        self.assertEqual(load_registry(ROOT,a)['records'],load_registry(ROOT,b)['records'])
        self.assertEqual(len(load_registry(ROOT,b)['records']),211)
        for path,digest in a['inputDigests'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest,path)
        for table in a['dictionaries']:
            for identity,row in a['dictionaries'][table].items():
                new=b['dictionaries'][table][identity]
                if identity!=MODEL:self.assertEqual(new,row,identity);continue
                self.assertEqual(new['references'],dict(row['references'],visual=ASSET))
                self.assertEqual(new.get('originalFacts'),row.get('originalFacts'))
                self.assertEqual(new['facts'],dict(row['facts'],currentPackAssetId='exos-blk3-july2026-r1',currentPackSpecific=True))
                self.assertEqual(new['curationHistory'][:-1],row['curationHistory'])
                self.assertEqual(set(new['curationHistory'][-1]['changes']),{'currentPackAssetId','currentPackSpecific'})
        self.assertEqual(load_contexts(ROOT,a),load_contexts(ROOT,b))
        self.assertEqual(len(load_contexts(ROOT,b)['records']),7)
        x,y=[build_pack(ROOT,c,roots=['ll2:configuration:164']) for c in (a,b)]
        self.assertEqual(x['objects'],y['objects']);self.assertEqual(x['manifest']['assets'],y['manifest']['assets'])
        self.assertEqual({k:v for k,v in x['manifest']['selection'].items() if k!='catalogVersion'},
                         {k:v for k,v in y['manifest']['selection'].items() if k!='catalogVersion'})
        self.assertLessEqual(abs(len(canonical_bytes(x['manifest']))-len(canonical_bytes(y['manifest']))),40)


    def test_wrong_model_rights_digest_source_uncurated_atomic_cli_refusals(self):
        candidate=loads_json((ROOT/CURATION).read_bytes())
        for defect in ('wrong-model','rights','digest','source','uncurated'):
            with self.subTest(defect=defect),tempfile.TemporaryDirectory() as directory:
                root=temporary_catalog(directory);v=copy.deepcopy(candidate);v['id']='blk3-negative-'+defect
                f=v['assets'][0]['facts'];f['id']='blk3-negative-'+defect
                v['updates'][0]['changes']['currentPackAssetId']=f['id']
                if defect=='wrong-model':v['updates'][0]['identity']='ll2:configuration:197';expected='exact configuration'
                elif defect=='rights':f['license']='CC0';expected='MIT'
                elif defect=='digest':f['sourceSha256']='0'*64;expected='digest'
                elif defect=='source':f['sources']=[];expected='source'
                else:v['assets']=[];v['updates'][0]['changes']['currentPackAssetId']='unadmitted-blk3';expected='asset'
                path=root/'assets/global/blk3-negative.json';path.write_bytes(canonical_bytes(v))
                output=root/'build/accepted.json';output.parent.mkdir();output.write_bytes(b'accepted output sentinel')
                accepted=root/'state/accepted.json';accepted.parent.mkdir();accepted.write_bytes(b'accepted state sentinel')
                before=filesystem(root)
                command=[sys.executable,'-B',str(ROOT/'tools/catalog.py'),'--repo',str(root),'--amend',str(path),'--catalog-version','blk3.negative.'+defect,'--output',str(output)]
                p=subprocess.run(command,capture_output=True,text=True,timeout=180);after=filesystem(root)
                print(json.dumps(dict(defect=defect,command=command,exitCode=p.returncode,stdout=p.stdout,stderr=p.stderr,files=len(before),beforeSha256=hashlib.sha256(canonical_bytes(before)).hexdigest(),afterSha256=hashlib.sha256(canonical_bytes(after)).hexdigest(),allBytesUnchanged=before==after)))
                self.assertEqual(p.returncode,1,p.stdout+p.stderr);self.assertIn(expected,p.stderr)
                self.assertEqual(after,before)

    def test_actual_production_raster_static_sfr1_bounds_and_legacy(self):
        pack=build_pack(ROOT,self.after,roots=[MODEL]);entry=pack['manifest']['assets'][ASSET]
        visual=assemble_visual([pack['objects'][r['sha256']] for r in entry['shards']],entry['animation'])
        self.assertEqual(visual[7],[0,[]])
        pixels,png,svg=rasterize([visual],54,124)
        chunks=encode_raster(pixels,54,124,4)
        self.assertEqual(independent_pixels(chunks,54,124,4),pixels)
        self.assertEqual(decode_raster(chunks,54,124,4),pixels)
        self.assertLessEqual(max(map(len,chunks)),4096)
        self.assertLessEqual(sum(map(len,chunks)),98304)
        lit=[(x,y) for y in range(124) for x in range(54) if pixels[(y*54+x)*4+3]>0]
        bounds=[min(x for x,y in lit),min(y for x,y in lit),max(x for x,y in lit),max(y for x,y in lit)]
        # Uniform fit has dy=8, scale=54/64; source tip6 lands at13.0625.
        self.assertEqual(bounds,[20,13,33,110])
        self.assertGreater(min(sum(pixels[(y*54+x)*4+3]>0 for x in range(54)) for y in range(28,95)),4)
        self.assertTrue(all(0<x<53 and 0<y<123 for x,y in lit))
        # Old source recipe continues exporting SARGE197 unchanged and cannot acquire BLK3.
        old,new=[build_pack(ROOT,c,roots=['ll2:configuration:197']) for c in (self.before,self.after)]
        self.assertEqual(old['objects'],new['objects']);self.assertEqual(old['manifest']['assets'],new['manifest']['assets'])
        self.assertNotIn(ASSET,old['manifest']['assets'])
        print(json.dumps(dict(observation='production-raster-static-sfr1',canvas=[54,124],bounds=bounds,pixelSHA256=hashlib.sha256(pixels).hexdigest(),pngSHA256=hashlib.sha256(png).hexdigest(),sfrChunks=len(chunks),sfrBytes=sum(map(len,chunks)))))



if __name__=='__main__':unittest.main()
