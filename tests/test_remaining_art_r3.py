"""R3 actual data/CLI/store witnesses. Factual/visual review is separate.

All fixtures are tracked and portable; no reference-cache path, remote fetch,
Garmin runtime or host-private acquisition file is required.
"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_global_catalog import temporary_catalog
from tools.spacefox.catalog import build_catalog, canonical_bytes, coverage_report, loads_json
from tools.spacefox.graphics import assemble_visual, build_pack, canonical_visual, export_svg

ROOT = Path(__file__).resolve().parents[1]
BEFORE = ROOT/'tests/fixtures/catalog/global-before-remaining-art-r3-source.json'
FACTS = ROOT/'tests/fixtures/catalog/remaining-art-r3-factual-review.json'
CURATION = Path('assets/global/curation-20261112-remaining-r3.json')
EVIDENCE = ROOT/'tests/fixtures/remaining-art-r3'
EXPECTED = {
    'll2:configuration:44': ('Shavit', 'spacefox:asset:remaining-r3-shavit-nasa1996', '1996-04'),
    'll2:configuration:139': ('Vector-R', 'spacefox:asset:remaining-r3-vector-r-faa2017', '2017-01'),
    'll2:configuration:142': ('Simorgh', 'spacefox:asset:remaining-r3-simorgh-mod2021', '2021-12-30'),
    'll2:configuration:495': ('Chollima-1', 'spacefox:asset:remaining-r3-chollima1-kcna2023', '2023-11-21'),
}
GAPS = {f'll2:configuration:{n}' for n in (30,39,74,86,94,96,152,196,200,502,505)}
FAMILIES = {f'll2:configuration:{n}' for n in (30,39,86,96,152,200)}


def execute(*args):
    return subprocess.run([sys.executable,'-B',*map(str,args)],cwd=tempfile.gettempdir(),
                          capture_output=True,text=True,timeout=180)


def inventory(root):
    return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}


class RemainingArtR3Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = build_catalog(ROOT,BEFORE)
        cls.after = build_catalog(ROOT)

    def export(self,source,output,*identities):
        args=[ROOT/'tools/export_visuals.py','--source',source,'--output',output]
        for identity in identities:
            args.extend(['--root',identity])
        result=execute(*args)
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads((output/'manifest.json').read_bytes())

    def test_exact4_preservation_and_unmapped_uncertainty(self):
        old,new=coverage_report(self.before),coverage_report(self.after)
        self.assertEqual((old['counts']['assets'],old['configurations']['mappedArt']),(611,156))
        self.assertEqual((new['counts']['assets'],new['configurations']['mappedArt']),(615,160))
        self.assertEqual(new['configurations']['requiredNonPlaceholder'],171)
        self.assertEqual(set(old['configurations']['missingArtIds']),GAPS|set(EXPECTED))
        self.assertEqual(set(new['configurations']['missingArtIds']),GAPS)
        for table in ('countries','organizations','sites','assets'):
            for identity,row in self.before['dictionaries'][table].items():
                self.assertEqual(self.after['dictionaries'][table][identity],row,(table,identity))
        for identity,oldrow in self.before['dictionaries']['configurations'].items():
            row=self.after['dictionaries']['configurations'][identity]
            self.assertEqual(row.get('originalFacts',row['facts']),oldrow.get('originalFacts',oldrow['facts']))
            for k,value in oldrow['facts'].items():
                if k not in ('currentPackAssetId','currentPackSpecific'):
                    self.assertEqual(row['facts'][k],value,(identity,k))
            for k,value in oldrow['references'].items():
                if k!='visual':
                    self.assertEqual(row['references'][k],value,(identity,k))
            if identity not in EXPECTED:
                self.assertEqual(row,oldrow)
        fixture=json.loads(FACTS.read_bytes())
        self.assertEqual({r['identity']:(r['fullName'],'spacefox:asset:'+r['assetId'],r['representativeDate'])
                          for r in fixture['candidates']},EXPECTED)
        self.assertEqual({f'll2:configuration:{n}' for n in fixture['remaining']},GAPS)
        reviews=json.loads((EVIDENCE/'research-review.json').read_text())['reviews']
        self.assertEqual(len(reviews),15)
        self.assertEqual({r['identity'] for r in reviews if r['status']=='candidate-mapped'},set(EXPECTED))
        self.assertEqual({r['identity'] for r in reviews if r['status']=='open'},GAPS)
        # A reviewed experimental family drawing cannot silently become a
        # complete/exact variant mapping or contribute to specific coverage.
        experiments=json.loads((EVIDENCE/'family-experiments.json').read_text())
        self.assertEqual(experiments['mappedFamilies'],0)
        self.assertEqual(len(experiments['experiments']),12)
        self.assertEqual({r['identity'] for r in experiments['experiments']},FAMILIES)
        selected=build_pack(ROOT,self.after,roots=sorted(FAMILIES))['manifest']['selection']['dictionaries']['configurations']
        for identity in FAMILIES:
            self.assertEqual(selected[identity]['references']['visual'],'spacefox:asset:generic')
            self.assertFalse(selected[identity]['facts']['currentPackSpecific'])
            self.assertIsNone(selected[identity]['references']['origin'])
        # Freeze recipe history rather than repin or erase accepted curations.
        recipe=json.loads((ROOT/'catalog/source.json').read_bytes())
        before=json.loads(BEFORE.read_bytes())
        self.assertEqual(recipe['curations'][:-1],before['curations'])
        self.assertEqual(recipe['curations'][-1]['path'],str(CURATION))
        for k in ('reference','assetSeed','geography','visualBridge'):
            self.assertEqual(recipe[k],before[k])

    def test_public_cli_admit_reopen_export_and_atomic_wrong_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(Path(tmp)/'owner');source=root/'catalog/source.json'
            source.write_bytes(BEFORE.read_bytes())
            output=Path(tmp)/'objects';catalog_output=root/'build/catalog.json'
            old=self.export(source,output,*EXPECTED)
            prior=inventory(output)
            self.assertTrue(all(r['references']['visual']=='spacefox:asset:generic'
                                for r in old['selection']['dictionaries']['configurations'].values()))
            result=execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,
                           '--amend',root/CURATION,'--catalog-version','literal.remaining.r3','--output',catalog_output)
            self.assertEqual(result.returncode,0,result.stderr)
            reopened=build_catalog(root)
            self.assertEqual(catalog_output.read_bytes(),canonical_bytes(reopened))
            self.assertEqual(coverage_report(reopened)['configurations']['mappedArt'],160)
            current=self.export(source,output,*EXPECTED,'ll2:configuration:30','ll2:configuration:511')
            for identity,(name,asset,date) in EXPECTED.items():
                row=current['selection']['dictionaries']['configurations'][identity]
                self.assertEqual(row['facts']['fullName'],name)
                self.assertEqual(row['references']['visual'],asset)
                self.assertIsNone(row['references']['origin'])
                entry=current['assets'][asset]
                self.assertEqual(entry['catalogRecord']['facts']['geometryReference']['representativeDate'],date)
            for n in (30,511):
                row=current['selection']['dictionaries']['configurations'][f'll2:configuration:{n}']
                self.assertEqual(row['references']['visual'],'spacefox:asset:generic')
                self.assertFalse(row['facts']['currentPackSpecific'])
            for path,data in prior.items():
                if path!='manifest.json':self.assertEqual((output/path).read_bytes(),data)
            accepted=(source.read_bytes(),catalog_output.read_bytes(),inventory(output))
            bad={'schemaVersion':1,'id':'r3-wrong-exact-model','reviewedAt':'2026-11-12',
                 'sources':['https://www.ulalaunch.com/rockets/vulcan-centaur'],
                 'reason':'Atomic valid-first/wrong-model-last discriminator.', 'assets':[],'additions':[],
                 'updates':[{'identity':'ll2:configuration:142','changes':{'name':'MUST NOT ACTIVATE'}},
                            {'identity':'ll2:configuration:200','changes':{'currentPackAssetId':'remaining-r3-vector-r-faa2017','currentPackSpecific':True}}]}
            path=root/'invalid.json';path.write_bytes(canonical_bytes(bad))
            result=execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,'--amend',path,
                           '--catalog-version','invalid.r3','--output',catalog_output)
            self.assertEqual(result.returncode,1)
            self.assertIn('art not reviewed for this exact configuration',result.stderr)
            self.assertEqual((source.read_bytes(),catalog_output.read_bytes(),inventory(output)),accepted)
            self.assertEqual(build_catalog(root),reopened)
            again=self.export(source,output,*EXPECTED,'ll2:configuration:30','ll2:configuration:511')
            self.assertEqual(again,current)
            self.assertEqual(inventory(output),accepted[2])

    def test_original_rights_geometry_and_atomic_invalid_source(self):
        digests=set()
        for identity,(_,asset,_) in EXPECTED.items():
            pack=build_pack(ROOT,self.after,roots=[identity]);entry=pack['manifest']['assets'][asset]
            wire=assemble_visual([pack['objects'][s['sha256']] for s in entry['shards']],entry['animation'])
            self.assertEqual(wire[3],[64,128])
            self.assertLessEqual(len(wire[5]),4096)
            self.assertLessEqual(len(wire[6]),512)
            self.assertTrue(all(len(v)<=4096 for v in pack['objects'].values()))
            self.assertEqual(hashlib.sha256(canonical_visual(wire)).hexdigest(),entry['sha256'])
            self.assertEqual(entry['rights']['license'],'MIT')
            self.assertIn('SpaceFox',entry['rights']['credit'])
            self.assertEqual(entry['catalogRecord']['facts']['coverage']['configurationIds'],[identity])
            digests.add(entry['sha256'])
        self.assertEqual(len(digests),4)
        experiments=json.loads((EVIDENCE/'family-experiments.json').read_text())['experiments']
        for row in experiments:
            wire=export_svg((EVIDENCE/row['path']).read_bytes(),[64,128])
            self.assertEqual(wire[3],[64,128])
            self.assertLessEqual(len(wire[5]),4096)
            self.assertLessEqual(len(wire[6]),512)
            self.assertEqual(row['status'],'UNADMITTED_EXPERIMENT_ZERO_COVERAGE')
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(Path(tmp)/'owner');source=root/'catalog/source.json'
            output=Path(tmp)/'objects';catalog_output=root/'build/catalog.json'
            self.export(source,output,'ll2:configuration:139')
            catalog_output.parent.mkdir(parents=True,exist_ok=True)
            catalog_output.write_bytes(canonical_bytes(build_catalog(root)))
            accepted=(source.read_bytes(),catalog_output.read_bytes(),inventory(output))
            template=loads_json((root/CURATION).read_bytes())
            for mode in ('unknown-rights','external-image'):
                candidate=copy.deepcopy(template)
                candidate['id']='r3-rejected-'+mode
                candidate['assets']=[candidate['assets'][0]]
                candidate['updates']=[candidate['updates'][0]]
                facts=candidate['assets'][0]['facts'];facts['id']='rejected-'+mode
                candidate['updates'][0]['changes']['currentPackAssetId']=facts['id']
                if mode=='unknown-rights':
                    facts['license']='unknown'
                    expected='MIT'
                else:
                    svg=root/'assets/global/rejected-image.svg'
                    svg.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 128"><image href="https://invalid.example/photo.jpg"/></svg>')
                    # Explicit relative asset paths are resolved from the repo
                    # root; the rejected file must exist at that actual port.
                    facts['file']='assets/global/rejected-image.svg'
                    facts['sourceSha256']=hashlib.sha256(svg.read_bytes()).hexdigest()
                    expected='unsupported source element image'
                path=root/'invalid.json';path.write_bytes(canonical_bytes(candidate))
                result=execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,
                               '--amend',path,'--catalog-version','invalid.r3.'+mode,'--output',catalog_output)
                self.assertEqual(result.returncode,1)
                self.assertIn(expected,result.stderr)
                self.assertEqual((source.read_bytes(),catalog_output.read_bytes(),inventory(output)),accepted)
                self.assertEqual(canonical_bytes(build_catalog(root)),catalog_output.read_bytes())
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_false_generic_specific_claim_is_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(Path(tmp)/'owner');source=root/'catalog/source.json'
            output=Path(tmp)/'objects';catalog_output=root/'build/catalog.json'
            self.export(source,output,'ll2:configuration:30')
            catalog_output.parent.mkdir(parents=True,exist_ok=True)
            catalog_output.write_bytes(canonical_bytes(build_catalog(root)))
            accepted=(source.read_bytes(),catalog_output.read_bytes(),inventory(output))
            value={'schemaVersion':1,'id':'r3-false-generic','reviewedAt':'2026-11-12',
                   'sources':['https://www.mhi.com/technology/review/pdf/e624/e624120.pdf'],
                   'reason':'Generic artwork cannot masquerade as an exact H3 variant.',
                   'assets':[],'additions':[],'updates':[{'identity':'ll2:configuration:30',
                       'changes':{'currentPackAssetId':'generic','currentPackSpecific':True}}]}
            path=root/'invalid.json';path.write_bytes(canonical_bytes(value))
            result=execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,
                           '--amend',path,'--catalog-version','invalid.generic.r3','--output',catalog_output)
            self.assertEqual(result.returncode,1)
            self.assertIn('specific',result.stderr)
            self.assertEqual((source.read_bytes(),catalog_output.read_bytes(),inventory(output)),accepted)
            self.assertEqual(canonical_bytes(build_catalog(root)),catalog_output.read_bytes())

    def test_malformed_typed_export_root_retains_written_objects(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'objects'
            self.export(ROOT/'catalog/source.json',output,'ll2:configuration:44')
            accepted=inventory(output)
            result=execute(ROOT/'tools/export_visuals.py','--source',ROOT/'catalog/source.json',
                           '--output',output,'--root','configuration:44')
            self.assertEqual(result.returncode,1)
            self.assertIn('root',result.stderr)
            self.assertEqual(inventory(output),accepted)

    def test_exact_mit_asset_wrong_source_digest_is_atomic(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(Path(tmp)/'owner');source=root/'catalog/source.json'
            output=Path(tmp)/'objects';catalog_output=root/'build/catalog.json'
            self.export(source,output,'ll2:configuration:44')
            catalog_output.parent.mkdir(parents=True,exist_ok=True)
            catalog_output.write_bytes(canonical_bytes(build_catalog(root)))
            accepted=(source.read_bytes(),catalog_output.read_bytes(),inventory(output))
            value=loads_json((root/CURATION).read_bytes())
            value['id']='r3-rejected-digest';value['assets']=[value['assets'][0]];value['updates']=[value['updates'][0]]
            facts=value['assets'][0]['facts'];facts['id']='r3-poisoned-digest'
            facts['file']='assets/global/'+facts['file']
            facts['sourceSha256']='0'*64
            value['updates'][0]['changes']['currentPackAssetId']=facts['id']
            path=root/'invalid.json';path.write_bytes(canonical_bytes(value))
            result=execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,
                           '--amend',path,'--catalog-version','invalid.digest.r3','--output',catalog_output)
            self.assertEqual(result.returncode,1)
            self.assertIn('source digest mismatch',result.stderr)
            self.assertEqual((source.read_bytes(),catalog_output.read_bytes(),inventory(output)),accepted)
            self.assertEqual(canonical_bytes(build_catalog(root)),catalog_output.read_bytes())

    def test_explicit_operator_mark_stays_with_requested_organization(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest=self.export(ROOT/'catalog/source.json',Path(tmp)/'objects',
                                 'll2:organization:37','ll2:configuration:164')
            rows=manifest['selection']['dictionaries']
            # The requested JAXA identity and Falcon9 manufacturer SpaceX are
            # different typed organizations; neither can borrow the other's mark.
            self.assertEqual(rows['configurations']['ll2:configuration:164']['references']['manufacturer'],
                             'll2:organization:121')
            self.assertEqual(rows['organizations']['ll2:organization:37']['references']['badge'],
                             'spacefox:asset:content-r1-operator-37')
            self.assertEqual(rows['organizations']['ll2:organization:121']['references']['badge'],
                             'spacefox:asset:company-spacex')
            self.assertNotEqual(rows['organizations']['ll2:organization:37']['references']['badge'],
                                rows['organizations']['ll2:organization:121']['references']['badge'])

    def test_other_organization_mark_cannot_activate(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=temporary_catalog(Path(tmp)/'owner');source=root/'catalog/source.json'
            output=Path(tmp)/'objects';catalog_output=root/'build/catalog.json'
            self.export(source,output,'ll2:organization:37')
            catalog_output.parent.mkdir(parents=True,exist_ok=True)
            catalog_output.write_bytes(canonical_bytes(build_catalog(root)))
            accepted=(source.read_bytes(),catalog_output.read_bytes(),inventory(output))
            value={'schemaVersion':1,'id':'r3-wrong-operator-mark','reviewedAt':'2026-11-12',
                   'sources':['https://www.isas.jaxa.jp/en/'],
                   'reason':'An available other organization mark cannot replace the exact operator identity.',
                   'assets':[],'additions':[],'updates':[{'identity':'ll2:organization:37',
                       'changes':{'currentPackBadgeId':'operator-label-34'}}]}
            path=root/'invalid.json';path.write_bytes(canonical_bytes(value))
            result=execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,
                           '--amend',path,'--catalog-version','invalid.operator.r3','--output',catalog_output)
            self.assertEqual(result.returncode,1)
            self.assertIn('different organization',result.stderr)
            self.assertEqual((source.read_bytes(),catalog_output.read_bytes(),inventory(output)),accepted)
            self.assertEqual(canonical_bytes(build_catalog(root)),catalog_output.read_bytes())


if __name__=='__main__':
    unittest.main()
