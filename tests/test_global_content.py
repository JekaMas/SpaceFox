"""Current large publisher revision and literal curation admission witnesses.
No native, provider-network, official-logo or worldwide completeness substitute.
"""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tools.catalog import amend_recipe, validate_artwork_sources
from tools.spacefox.catalog import CatalogError, build_catalog, canonical_bytes, coverage_report, loads_json, validate_catalog
from tools.spacefox.graphics import VisualError, LIMITS, build_pack
from tests.test_global_catalog import temporary_catalog, supplement, save_revision

ROOT=Path(__file__).resolve().parents[1]
HISTORICAL=ROOT/'tests/fixtures/catalog/global-before-content-source.json'
URL='https://official.example/independent-review'

def lifecycle(state='retired'):
    return {'officialLifecycle':state,'officialLifecycleSource':URL,
            'officialLifecycleReviewedAt':'2026-11-12','officialLifecycleNote':'Literal independently sourced state assertion.'}

def mark_revision(root, identity='literal-jp-revision', code='JP', country='ll2:country:28', kind='original-national-flag'):
    value=supplement(identity)
    file=root/(identity+'.svg')
    file.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 8"><rect width="12" height="8" fill="#fff"/><path d="M6 2L8 4L6 6L4 4Z" fill="#c00"/></svg>')
    value['assets']=[{'collection':'countries','facts':{'id':identity,'name':'Literal immutable review mark',
        'file':file.name,'exportSize':[12,8],'creator':'Literal test author','license':'MIT','sources':[URL],
        'sourceSha256':hashlib.sha256(file.read_bytes()).hexdigest(),'codes':[code],
        'kind':kind,'jurisdictionId':country}}]
    value['updates']=[{'identity':country,'changes':{'currentPackFlagId':identity},'sources':[URL]}]
    return value


class GlobalContentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=build_catalog(ROOT)
        cls.old=build_catalog(ROOT,HISTORICAL)
        cls.baseline=build_catalog(ROOT,ROOT/'tests/fixtures/catalog/global-before-remaining-art-source.json')

    def test_reviewed_extensions_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp); source=root/'catalog/source.json'
            before=build_catalog(root)['dictionaries']['configurations']['ll2:configuration:164']
            revision=supplement('literal-typed-review')
            revision['updates']=[{'identity':'ll2:configuration:164','changes':lifecycle(),'sources':[URL]},
                {'identity':'ll2:country:50','changes':{'jurisdictionKind':'territory'},'sources':[URL]}]
            c=amend_recipe(root,source,save_revision(root,revision),'typed.1')
            row=c['dictionaries']['configurations']['ll2:configuration:164']
            self.assertEqual(row['facts']['officialLifecycle'],'retired')
            self.assertEqual(row['facts']['providerActive'],before['facts']['providerActive'])
            self.assertEqual(canonical_bytes(row['originalFacts']),canonical_bytes(before.get('originalFacts',before['facts'])))
            self.assertEqual(row['curationHistory'][-1]['sources'],[URL])
            self.assertNotIn('officialLifecycle',row['originalFacts'])
            self.assertIn('ll2:configuration:164',coverage_report(c)['lifecycle']['providerConflictIds'])
            self.assertEqual(c['dictionaries']['countries']['ll2:country:50']['jurisdictionKind'],'territory')
            next_value=supplement('literal-typed-review-2');next_url=URL+'/second'
            next_facts=lifecycle('operating');next_facts['officialLifecycleSource']=next_url
            next_value['updates']=[{'identity':'ll2:configuration:164','changes':next_facts,'sources':[next_url]}]
            c2=amend_recipe(root,source,save_revision(root,next_value,'next.json'),'typed.2')
            row2=c2['dictionaries']['configurations']['ll2:configuration:164']
            self.assertEqual([e['sources'] for e in row2['curationHistory'][-2:]],[[URL],[next_url]])
            self.assertEqual(canonical_bytes(row2['originalFacts']),canonical_bytes(row['originalFacts']))
            validate_catalog(c2)

    def test_reviewed_extensions_negative(self):
        cases=[('ll2:configuration:164',{'imaginedFact':True},[URL]),
            ('ll2:organization:37',lifecycle(),[URL]),
            ('ll2:configuration:164',{'officialLifecycle':True},[URL]),
            ('ll2:configuration:164',dict(lifecycle(),officialLifecycleSource=URL+'/unlisted'),[URL]),
            ('ll2:configuration:164',dict(lifecycle(),officialLifecycleReviewedAt='2026-11-13'),[URL]),
            ('ll2:configuration:164',lifecycle(),None),
            ('ll2:configuration:164',lifecycle(),[]),
            ('ll2:country:28',{'jurisdictionKind':1},[URL]),
            ('ll2:country:17',{'jurisdictionKind':'country'},[URL]),
            ('ll2:configuration:164',{'jurisdictionKind':'country'},[URL])]
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp);source=root/'catalog/source.json';before=source.read_bytes()
            for index,(identity,changes,sources) in enumerate(cases):
                value=supplement('typed-negative-'+str(index));value['updates']=[{'identity':identity,'changes':changes,'sources':sources}]
                with self.subTest(index=index),self.assertRaises(CatalogError):
                    amend_recipe(root,source,save_revision(root,value),'typed.bad')
                self.assertEqual(source.read_bytes(),before)
            value=supplement('typed-unsourced');value['updates']=[{'identity':'ll2:configuration:164','changes':lifecycle()}]
            with self.assertRaisesRegex(CatalogError,'explicit operation sources'):
                amend_recipe(root,source,save_revision(root,value),'typed.bad')

    def test_immutable_mark_revisions_positive(self):
        old=self.old['dictionaries']['countries']['ll2:country:28']['references']['mark']
        current=self.catalog['dictionaries']['countries']['ll2:country:28']['references']['mark']
        self.assertNotEqual(old,current)
        self.assertEqual(self.catalog['dictionaries']['assets'][old],self.old['dictionaries']['assets'][old])
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp);source=root/'catalog/source.json'
            value=mark_revision(root)
            c=amend_recipe(root,source,save_revision(root,value),'mark.1')
            self.assertEqual(c['dictionaries']['countries']['ll2:country:28']['references']['mark'],'spacefox:asset:literal-jp-revision')
            for identity in (old,current):self.assertEqual(c['dictionaries']['assets'][identity],self.catalog['dictionaries']['assets'][identity])
            rollback=supplement('literal-mark-rollback')
            rollback['updates']=[{'identity':'ll2:country:28','changes':{'currentPackFlagId':current.removeprefix('spacefox:asset:')},'sources':[URL]}]
            c2=amend_recipe(root,source,save_revision(root,rollback,'rollback.json'),'mark.2')
            self.assertEqual(c2['dictionaries']['countries']['ll2:country:28']['references']['mark'],current)
            self.assertIn('spacefox:asset:literal-jp-revision',c2['dictionaries']['assets'])
            self.assertEqual(c2['dictionaries']['countries']['ll2:country:28']['curationHistory'][-2]['sources'],[URL])

    def test_immutable_mark_revisions_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp);source=root/'catalog/source.json';before=source.read_bytes()
            for index,kwargs in enumerate([{'country':'ll2:country:34'}, {'code':'ZZ','country':'ll2:country:28'},
                    {'code':'??','country':'ll2:country:17'}, {'kind':'original-informational-country-code'}]):
                value=mark_revision(root,'literal-bad-'+str(index),**kwargs)
                with self.subTest(kwargs=kwargs),self.assertRaises(CatalogError):
                    amend_recipe(root,source,save_revision(root,value),'mark.bad')
                self.assertEqual(source.read_bytes(),before)
            value=supplement('literal-unknown-asset');value['updates']=[{'identity':'ll2:country:28','changes':{'currentPackFlagId':'nonexistent-flag'}}]
            with self.assertRaises(CatalogError):amend_recipe(root,source,save_revision(root,value),'mark.bad')
            self.assertEqual(source.read_bytes(),before)

    def test_current_all_asset_bounded_admission_positive(self):
        # Both immutable global.3 and current global.14 archive cohorts execute
        # the same bounded real-art admission and all original assertions.
        for catalog, asset_count, mapping_counts, missing_origins in (
                (self.baseline, 562, (108, 63), 336), (self.catalog, 638, (174, 19), 335)):
            seen=set();actual=build_pack
            def observe(root,catalog,**kwargs):
                pack=actual(root,catalog,**kwargs);seen.update(pack['manifest']['assets'])
                self.assertLessEqual(len(kwargs['roots']),LIMITS['selectionRoots'])
                self.assertLessEqual(len(canonical_bytes(pack['manifest']))+sum(map(len,pack['objects'].values())),1048576)
                for statistic in pack['statistics'].values():self.assertLessEqual(statistic['maxShardDecodedBytes'],4096)
                return pack
            with patch('tools.spacefox.graphics.build_pack',side_effect=observe):
                validate_artwork_sources(ROOT,catalog)
            self.assertEqual(seen,set(catalog['dictionaries']['assets']))
            self.assertEqual(len(seen),asset_count)
            report=coverage_report(catalog)
            self.assertEqual((report['configurations']['mappedArt'],len(report['configurations']['missingArtIds'])),mapping_counts)
            self.assertEqual(report['organizations']['mappedKnownBadges'],349)
            self.assertEqual(len(report['origins']['organizations']['missingOriginIds']),missing_origins)
            self.assertIsNone(catalog['dictionaries']['organizations']['ll2:organization:183']['references']['badge'])

    def test_current_full_pack_and_atomic_invalid_asset_negative(self):
        with self.assertRaisesRegex(VisualError,'publisher artifact byte limit'):
            build_pack(ROOT,self.catalog)
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(tmp);source=root/'catalog/source.json';before=source.read_bytes()
            value=mark_revision(root,'literal-invalid-source')
            p=root/'literal-invalid-source.svg';p.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 12 8"><image href="https://evil.example/a"/></svg>')
            value['assets'][0]['facts']['sourceSha256']=hashlib.sha256(p.read_bytes()).hexdigest()
            with self.assertRaises(VisualError):amend_recipe(root,source,save_revision(root,value),'invalid.asset')
            self.assertEqual(source.read_bytes(),before)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_current_selected_closure_invariance_positive(self):
        roots=['ll2:configuration:164','ll2:site:65']
        before=build_pack(ROOT,self.old,roots=roots);current=build_pack(ROOT,self.catalog,roots=roots)
        self.assertEqual(before['objects'],current['objects'])
        # Reviewed jurisdiction metadata and version legitimately changed; the
        # same selected model/site/operator facts and immutable visuals survive.
        for table in ('configurations','sites','organizations'):
            self.assertEqual(before['manifest']['selection']['dictionaries'][table],
                             current['manifest']['selection']['dictionaries'][table])
        grown=copy.deepcopy(self.catalog)
        unrelated=copy.deepcopy(grown['dictionaries']['assets']['spacefox:asset:generic'])
        unrelated['facts']['id']='literal-unrelated-growth'
        unrelated['provenance'][0]['recordId']='literal-unrelated-growth'
        grown['dictionaries']['assets']['spacefox:asset:literal-unrelated-growth']=unrelated
        grown['inputDigests']['literal-unrelated-input.json']='0'*64
        after=build_pack(ROOT,grown,roots=roots)
        self.assertEqual(current['objects'],after['objects'])
        self.assertEqual(current['manifest']['selection'],after['manifest']['selection'])
        self.assertLessEqual(len(canonical_bytes(current['manifest']))+sum(map(len,current['objects'].values())),1048576)
        # The current newly added Japanese model closes over its own flag/label;
        # the French-Guiana site never becomes the European vehicle's origin.
        selected=build_pack(ROOT,self.catalog,roots=['ll2:configuration:498','ll2:configuration:553','ll2:configuration:26','ll2:site:67'])
        rows=selected['manifest']['selection']['dictionaries']
        self.assertEqual(rows['configurations']['ll2:configuration:498']['references']['origin'],'ll2:country:28')
        self.assertEqual(rows['configurations']['ll2:configuration:553']['references']['origin'],'spacefox:country:EUROPE')
        self.assertEqual(rows['sites']['ll2:site:67']['references']['country'],'ll2:country:50')
        self.assertEqual(rows['countries']['ll2:country:50']['jurisdictionKind'],'territory')
        self.assertEqual(rows['configurations']['ll2:configuration:26']['references']['origin'],'ll2:country:51')
        self.assertEqual(rows['organizations']['ll2:organization:147']['references']['origin'],'ll2:country:2')
        self.assertNotIn('ll2:configuration:522',rows['configurations'])

    def test_current_geometry_and_flags_positive(self):
        import xml.etree.ElementTree as ET
        new=loads_json((ROOT/'assets/global/curation-20261112-content-r1.json').read_bytes())
        vehicles={a['facts']['id']:a['facts'] for a in new['assets'] if a['collection']=='models'}
        def tree(name):return ET.parse(ROOT/'assets/global'/vehicles['content-r1-vehicle-'+name]['file'])
        for name,count in [('lm5',4),('lm5b',4),('lm8',2),('lm8-core',0),('kinetica2',2)]:
            self.assertEqual(len(tree(name).findall('.//*[@data-part="booster"]')),count)
        self.assertNotEqual(vehicles['content-r1-vehicle-minotaurc3110']['sourceSha256'],vehicles['content-r1-vehicle-minotaurc3210']['sourceSha256'])
        self.assertEqual(vehicles['content-r1-vehicle-minotaur-ivplus-v']['coverage']['configurationIds'],['ll2:configuration:85','ll2:configuration:13'])
        self.assertEqual(len(tree('miura1').findall('.//*[@data-part="fin"]')),2)
        for token in ('terrier-improved-orion','terrier-improved-malemute'):
            row=self.catalog['dictionaries']['configurations']['spacefox:configuration:'+token]
            self.assertIsNone(row['references']['origin']);self.assertIsNone(row['references']['manufacturer'])
            self.assertIsNone(row['facts']['providerActive']);self.assertIsNone(row['facts']['overallLengthMetres'])
        miura9=self.baseline['dictionaries']['configurations']['spacefox:configuration:miura9']
        self.assertIsNone(miura9['references']['visual']);self.assertIsNone(miura9['references']['origin'])
        self.assertIsNone(miura9['facts']['providerActive'])
        self.assertFalse(self.baseline['dictionaries']['configurations']['ll2:configuration:509']['facts']['currentPackSpecific'])
        for identity, asset in (('spacefox:configuration:miura9', 'spacefox:asset:remaining-r1-miura9'),
                                ('ll2:configuration:509', 'spacefox:asset:remaining-r1-miura5-current')):
            row=self.catalog['dictionaries']['configurations'][identity]
            self.assertEqual(row['references']['visual'],asset)
            self.assertTrue(row['facts']['currentPackSpecific'])
            self.assertIsNone(row['references']['origin'])
        self.assertEqual(len(tree('themis-t1h').findall('.//*[@data-part="fairing"]')),0)
        flags={a['facts']['depictedCode']:a['facts'] for a in new['assets'] if a['collection']=='countries'}
        india=ET.parse(ROOT/'assets/global'/flags['IN']['file'])
        self.assertEqual(len(india.findall('.//*[@data-part="chakra-spoke"]')),24)
        china=ET.parse(ROOT/'assets/global'/flags['CN']['file'])
        self.assertEqual(len(china.findall('.//*[@data-part="small-star"]')),4)
        self.assertEqual(flags['AU']['exportSize'],[48,24]);self.assertEqual(flags['DE']['exportSize'],[40,24])
        labels=[a['facts'] for a in new['assets'] if a['collection']=='companies']
        self.assertEqual(len({a['sourceSha256'] for a in labels}),len(labels))
        self.assertTrue(all(a['officialLogo'] is False for a in labels))


if __name__=='__main__':unittest.main()
