"""Actual maintained input/CLI/export tests; no provider or device substitution."""
import copy
from decimal import Decimal
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.spacefox.catalog import (CatalogError, build_catalog, canonical_bytes,
                                     coverage_report, loads_json, validate_catalog)
from tools.spacefox.graphics import assemble_visual, build_pack, VisualError

ROOT = Path(__file__).resolve().parents[1]


def temporary_catalog(directory):
    root = Path(directory); catalog = build_catalog(ROOT)
    for relative in ['catalog/source.json', *catalog['inputDigests']]:
        target = root/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/relative,target)
    return root


def supplement(identity='test-revision'):
    return {'schemaVersion':1,'id':identity,'reviewedAt':'2026-11-12',
            'sources':['https://www.isas.jaxa.jp/en/missions/sounding_rockets/'],
            'reason':'Independent literal data-only authoring regression; not an accuracy assertion.',
            'assets':[],'updates':[],'additions':[]}


def save_revision(root, value, name='candidate.json'):
    path = root/name;path.write_bytes(canonical_bytes(value));return path


class GlobalCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_catalog(ROOT)

    def test_curation_positive(self):
        c = self.catalog;d = c['dictionaries']
        self.assertEqual({k:len(v) for k,v in d.items()},
                         {'countries':104,'organizations':350,'configurations':176,'sites':218,'assets':562})
        reference = loads_json((ROOT/'openspec/changes/spacefox-watchface/evidence/global-catalog/reference-inventory.json').read_bytes())
        # Every one of the 839 original entities retains its exact source facts.
        for source,table,kind in [('countries','countries','country'),('organizations','organizations','organization'),('models','configurations','configuration'),('sites','sites','site')]:
            for facts in reference[source]:
                row = d[table][f'll2:{kind}:{facts["sourceId"]}']
                self.assertEqual(canonical_bytes(row.get('originalFacts',row['facts'])),canonical_bytes(facts))
        for token,stages in [('s310',1),('s520',1),('ss520',2)]:
            row = d['configurations']['spacefox:configuration:'+token]
            self.assertEqual(row['facts']['stages'],stages)
            self.assertIsNone(row['facts']['providerActive'])
            self.assertEqual(row['facts']['officialLifecycle'],'operating-listed')
            self.assertEqual(row['references']['origin'],'ll2:country:28')
        self.assertIsNone(d['sites']['spacefox:site:esrange-sounding-area']['position'])
        self.assertEqual(d['sites']['spacefox:site:esrange-sounding-area']['references']['agencies'],['ll2:organization:151'])
        self.assertEqual(d['sites']['ll2:site:13']['position']['latitude'].as_tuple(),Decimal('0.0').as_tuple())
        self.assertEqual(d['sites']['ll2:site:13']['facts']['positionMode'],'mobile-reference-no-event')
        # Marks do not invent model or operator origin from source countries.
        self.assertIsNone(d['configurations']['ll2:configuration:30']['references']['origin'])
        self.assertEqual(d['organizations']['ll2:organization:37']['references']['origin'],'ll2:country:28')

    def test_curation_negative(self):
        for field,value in [('sourceId','different'),('latitude',Decimal('91')),('longitude',Decimal('NaN'))]:
            with tempfile.TemporaryDirectory() as tmp:
                root = temporary_catalog(tmp);before = (root/'catalog/source.json').read_bytes()
                value_file = supplement();value_file['updates']=[{'identity':'ll2:site:65','changes':{field:value}}]
                with self.assertRaises((CatalogError,VisualError)):
                    path=save_revision(root,value_file);amend_recipe(root,root/'catalog/source.json',path,'test.bad')
                self.assertEqual((root/'catalog/source.json').read_bytes(),before)
        bad = copy.deepcopy(self.catalog)
        bad['dictionaries']['configurations']['spacefox:configuration:s310']['references']['manufacturer']='ll2:organization:121'
        with self.assertRaises(CatalogError):validate_catalog(bad)
        bad = copy.deepcopy(self.catalog)
        bad['dictionaries']['sites']['spacefox:site:esrange-sounding-area']['curation']['reviewedAt']='2026-11-31'
        with self.assertRaises(CatalogError):validate_catalog(bad)
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp);path=root/'assets/global/svg/vehicle-s520.svg';path.write_text(path.read_text().replace('#e8eef1','#abcdef'))
            with self.assertRaisesRegex(CatalogError,'source digest'):build_catalog(root)

    def test_maintenance_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp);source=root/'catalog/source.json'
            first=supplement('literal-correction-1')
            first['updates']=[{'identity':'ll2:site:65','changes':{'latitude':Decimal('-0.0000'),'longitude':Decimal('179.9999999999999999')}}]
            first['updates'][0]['sources']=['https://official.example/survey/first-exact-point']
            # A jurisdiction absent from the provider dictionary is admitted by
            # data, with an explicit kind and exact typed mark relationship.
            country_svg=root/'country.svg';country_svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10" fill="#123456"/></svg>')
            first['assets']=[{'collection':'countries','facts':{'id':'literal-country-mark','name':'Literal code mark','file':'country.svg','exportSize':[10,10],
                'creator':'Literal test author','license':'MIT','sources':first['sources'],'codes':['ZX'],'kind':'original-informational-country-code',
                'sourceSha256':hashlib.sha256(country_svg.read_bytes()).hexdigest()}}]
            first['additions']=[{'identity':'spacefox:country:literal-jurisdiction','facts':{'sourceId':'literal-jurisdiction','name':'Literal test territory',
                'alpha2':'ZX','alpha3':'ZXX','sourceUrl':first['sources'][0],'currentPackFlagId':'literal-country-mark','jurisdictionKind':'territory'},
                'references':{'mark':'spacefox:asset:literal-country-mark'}}]
            command=[sys.executable,'-B',str(ROOT/'tools/catalog.py'),'--repo',str(root),'--amend',str(save_revision(root,first)),
                     '--catalog-version','literal.1','--output',str(root/'build/catalog.json')]
            completed=subprocess.run(command,cwd=tempfile.gettempdir(),capture_output=True,text=True,timeout=60)
            self.assertEqual(completed.returncode,0,completed.stderr)
            c=build_catalog(root)
            self.assertEqual((root/'build/catalog.json').read_bytes(),canonical_bytes(c))
            row=c['dictionaries']['sites']['ll2:site:65']
            self.assertEqual(row['position']['latitude'].as_tuple(),Decimal('-0.0000').as_tuple())
            self.assertEqual(row['position']['longitude'],Decimal('179.9999999999999999'))
            self.assertEqual(row['curation']['sources'],first['updates'][0]['sources'])
            self.assertNotEqual(row['originalFacts']['latitude'],row['facts']['latitude'])
            original=canonical_bytes(row['originalFacts'])
            # A second correction and immutable image replacement are data only.
            next_value=supplement('literal-correction-2')
            path=root/'replacement.svg';path.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 20"><polygon points="5 1 8 7 8 19 2 19 2 7" fill="#abcdef"/></svg>')
            facts={'id':'literal-replacement','name':'Literal original replacement','file':'replacement.svg','exportSize':[10,20],
                   'creator':'Literal test author','license':'MIT','sources':next_value['sources'],'sourceSha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                   'kind':'specific','coverage':{'type':'specific','configurationIds':['ll2:configuration:164'],
                   'features':['Explicit independent pointed, narrow reference fixture'],'limitations':'Test drawing only; not product art acceptance.'}}
            next_value['assets']=[{'collection':'models','facts':facts}]
            next_value['updates']=[{'identity':'ll2:configuration:164','changes':{'currentPackAssetId':'literal-replacement','currentPackSpecific':True}},
                                   {'identity':'ll2:site:65','changes':{'latitude':Decimal('1.2300'),'longitude':0},'sources':['https://official.example/survey/second-exact-point']},
                                   {'identity':'spacefox:site:esrange-sounding-area','changes':{'name':'Esrange independently named pad unresolved'}}]
            c2=amend_recipe(root,source,save_revision(root,next_value,'next.json'),'literal.2')
            row=c2['dictionaries']['sites']['ll2:site:65']
            self.assertEqual(canonical_bytes(row['originalFacts']),original)
            self.assertEqual(len(row['curationHistory']),2)
            self.assertEqual([x['sources'] for x in row['curationHistory']],
                             [first['updates'][0]['sources'],next_value['updates'][1]['sources']])
            self.assertIn(b'https://official.example/survey/first-exact-point',canonical_bytes(c2))
            bad=copy.deepcopy(c2);bad['dictionaries']['sites']['ll2:site:65']['curationHistory'][0]['sources']=[]
            with self.assertRaises(CatalogError):validate_catalog(bad)
            self.assertEqual(row['position']['latitude'].as_tuple(),Decimal('1.2300').as_tuple())
            self.assertEqual(type(row['position']['longitude']),int)
            self.assertEqual(c2['dictionaries']['configurations']['ll2:configuration:164']['references']['visual'],'spacefox:asset:literal-replacement')
            changed=c2['dictionaries']['sites']['spacefox:site:esrange-sounding-area']
            self.assertEqual(changed['originalFacts']['name'],'Esrange sounding-rocket launch area (pad unresolved)')
            self.assertEqual(changed['creationCuration'],'global-curation-20261112')
            self.assertEqual(changed['provenance'],[{'source':'curation','recordId':'global-curation-20261112'}])
            self.assertIsNone(changed['position'])
            country=c2['dictionaries']['countries']['spacefox:country:literal-jurisdiction']
            self.assertEqual(country['jurisdictionKind'],'territory')
            self.assertEqual(country['references']['mark'],'spacefox:asset:literal-country-mark')

    def test_maintenance_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp);source=root/'catalog/source.json';before=source.read_bytes()
            value=supplement('bad-role');value['updates']=[{'identity':'ll2:organization:37','changes':{'currentPackBadgeId':'operator-label-34'}}]
            with self.assertRaisesRegex(CatalogError,'different organization'):
                amend_recipe(root,source,save_revision(root,value),'bad.role')
            self.assertEqual(source.read_bytes(),before)
            value=supplement('bad-legacy-art');value['updates']=[{'identity':'ll2:configuration:30','changes':{'currentPackAssetId':'falcon-9','currentPackSpecific':True}}]
            with self.assertRaisesRegex(CatalogError,'legacy specific-art'):amend_recipe(root,source,save_revision(root,value),'bad.legacy')
            self.assertEqual(source.read_bytes(),before)
            value=supplement('bad-position-mode');value['updates']=[{'identity':'ll2:site:65','changes':{'positionMode':'headquarters-fallback'}}]
            with self.assertRaises(CatalogError):amend_recipe(root,source,save_revision(root,value),'bad.mode')
            self.assertEqual(source.read_bytes(),before)
            value=supplement('bad-rights');asset=copy.deepcopy(loads_json((root/'assets/global/curation-20261112.json').read_bytes())['assets'][-1])
            asset['facts'].update(id='unlicensed-new',license='unknown');value['assets']=[asset]
            with self.assertRaisesRegex(CatalogError,'MIT'):amend_recipe(root,source,save_revision(root,value),'bad.rights')
            self.assertEqual(source.read_bytes(),before)
            with self.assertRaises(CatalogError):amend_recipe(root,source,root/'assets/global/curation-20261112.json','bad.repin')
            self.assertEqual(source.read_bytes(),before)
            value=supplement('overwrite-attempt');path=save_revision(root,value)
            completed=subprocess.run([sys.executable,'-B',str(ROOT/'tools/catalog.py'),'--repo',str(root),'--amend',str(path),
                '--catalog-version','bad.overwrite','--output',str(source)],capture_output=True,text=True,timeout=60)
            self.assertNotEqual(completed.returncode,0)
            self.assertEqual(source.read_bytes(),before)

    def test_coverage_positive(self):
        report=coverage_report(self.catalog);models=report['configurations']
        self.assertEqual((models['providerRequiredNonPlaceholder'],models['providerMappedArt']),(165,103))
        self.assertEqual((models['requiredNonPlaceholder'],models['mappedArt'],len(models['missingArtIds'])),(171,108,63))
        self.assertEqual(report['countries']['markKindsByCountryRecord']['original-informational-country-code'],90)
        self.assertEqual(report['organizations']['mappedBadges'],349)
        self.assertIsNone(report['sites']['independentlyVerifiedPadAccuracy'])
        # Retained global.2 geometry witnesses are explicitly historical, while
        # current coverage counts above and new all-asset checks use global.3.
        historical=build_catalog(ROOT,ROOT/'tests/fixtures/catalog/global-before-content-source.json')
        pack=build_pack(ROOT,historical)
        self.assertEqual(len(pack['statistics']),218)
        current=self.catalog['dictionaries']['configurations']['ll2:configuration:465']['references']['visual']
        self.assertEqual(current,'spacefox:asset:vehicle-spaceshiptwo-twinboom-r2')
        drawing=pack['manifest']['assets'][current]
        value=assemble_visual([pack['objects'][s['sha256']] for s in drawing['shards']],drawing['animation'])
        # Literal geometry witnesses from the reviewed normal-flight top view:
        # both outboard booms continue aft; the center behind the engine is open.
        def covered(x,y):
            for op in value[6]:
                vertices=[(value[5][i]%16384/32,value[5][i]//16384/32) for i in op[2]]
                inside=False
                for a,b in zip(vertices,vertices[1:]+vertices[:1]):
                    if (a[1]>y)!=(b[1]>y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:inside=not inside
                if inside:return True
            return False
        self.assertTrue(covered(18,108));self.assertTrue(covered(72,108));self.assertFalse(covered(45,108))
        self.assertIn('spacefox:asset:vehicle-spaceshiptwo',self.catalog['dictionaries']['assets'])
        self.assertTrue(all(x['maxShardDecodedBytes']<=4096 for x in pack['statistics'].values()))
        # Shape differences are observable geometry, not filenames or counts.
        for names in [('s310','s520','ss520'),('pslv-ca','pslv-dl','pslv-ql','pslv-xl'),('h3-30','h3-22','h3-24'),('vulcan-2s','vulcan-4s','vulcan-4l','vulcan-6l'),('spaceshiptwo','ravn-x','superheavy-prototype')]:
            digests=[pack['manifest']['assets']['spacefox:asset:vehicle-'+n]['sha256'] for n in names]
            self.assertEqual(len(set(digests)),len(names))
        for identity in ['ll2:configuration:463','ll2:configuration:465','ll2:configuration:206']:
            asset=self.catalog['dictionaries']['assets'][self.catalog['dictionaries']['configurations'][identity]['references']['visual']]
            self.assertIn(identity,asset['facts']['coverage']['configurationIds'])

    def test_coverage_negative(self):
        self.assertIn('ll2:configuration:522',coverage_report(self.catalog)['configurations']['missingArtIds'])
        bad=copy.deepcopy(self.catalog)
        bad['dictionaries']['assets']['spacefox:asset:vehicle-s520']['facts']['coverage']['configurationIds']=['ll2:configuration:522']
        with self.assertRaisesRegex(CatalogError,'not reviewed'):validate_catalog(bad)
        bad=copy.deepcopy(self.catalog);row=bad['dictionaries']['configurations']['spacefox:configuration:s310']
        row['facts']['currentPackAssetId']='generic';row['references'].update(visual='spacefox:asset:generic',origin=None);row['originSources']=[]
        with self.assertRaisesRegex(CatalogError,'specific-art flag'):validate_catalog(bad)
        bad=copy.deepcopy(self.catalog)
        bad['dictionaries']['sites']['ll2:site:65']['curation']={'id':'fake','reviewedAt':'2026-11-12','sources':['https://example.com/'],'reason':'fake','changes':{}}
        with self.assertRaises(CatalogError):validate_catalog(bad)
        # Country-code mark availability never closes an unknown origin.
        self.assertIsNone(self.catalog['dictionaries']['configurations']['ll2:configuration:30']['references']['origin'])


if __name__ == '__main__':unittest.main()
