"""Exact finite R2 data/CLI/immutable-store witnesses; shape review is separate."""
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
from tools.spacefox.graphics import assemble_visual, canonical_visual

ROOT = Path(__file__).resolve().parents[1]
HISTORICAL = ROOT/'tests/fixtures/catalog/global-before-further-art-r2-source.json'
CURATION = Path('assets/global/curation-20261112-further-r2.json')
RADIAL_CURATION = Path('assets/global/curation-20261112-further-r2-independent-v1.json')
EVIDENCE = ROOT/'tests/fixtures/further-art-r2'
EXPECTED = {
    123:('Long March 5/YZ-2','lm5-yz2-radial-firstflight'),
    197:('SARGE','sarge-published2016'),
    217:('Qased','qased-noor2020'),
    383:('Minotaur-C 1110','minotaur-c-1110'),
    384:('Minotaur-C 2110','minotaur-c-2110'),
    385:('Minotaur-C 2210','minotaur-c-2210'),
    480:('Orbex Prime','orbex-prime-2022'),
    522:('Starship V3','starship-v3-2026'),
    534:('Zéphyr','zephyr-cnes2025'),
    536:('Long March 10','lm10-crew-published'),
    537:('Long March 10A','lm10a-crew-published'),
    545:('Nebula-1','nebula1-published-current'),
}
EXPECTED = {f'll2:configuration:{n}':(name,'spacefox:asset:further-r2-'+asset)
            for n,(name,asset) in EXPECTED.items()}
GAPS = {f'll2:configuration:{n}' for n in
        (30,39,44,74,86,94,96,139,142,152,196,200,495,502,505)}


def execute(*args):
    return subprocess.run([sys.executable,'-B',*map(str,args)],
                          cwd=tempfile.gettempdir(),capture_output=True,
                          text=True,timeout=180)


def inventory(directory):
    return {str(p.relative_to(directory)):p.read_bytes()
            for p in directory.rglob('*') if p.is_file()}


class FurtherArtR2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.before = build_catalog(ROOT,HISTORICAL)
        cls.after = build_catalog(ROOT)

    def export(self,source,output,identity):
        result = execute(ROOT/'tools/export_visuals.py','--source',source,
                         '--output',output,'--root',identity)
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads((output/'manifest.json').read_bytes())

    def test_exact12_remaining15_and_preserved_source_contract(self):
        before,after = coverage_report(self.before),coverage_report(self.after)
        self.assertEqual((before['counts']['assets'],before['configurations']['mappedArt']),(598,144))
        self.assertEqual((after['counts']['assets'],after['configurations']['mappedArt']),(611,156))
        self.assertEqual(after['configurations']['requiredNonPlaceholder'],171)
        self.assertEqual(set(before['configurations']['missingArtIds']),set(EXPECTED)|GAPS)
        self.assertEqual(set(after['configurations']['missingArtIds']),GAPS)
        reviews = json.loads((EVIDENCE/'research-review.json').read_text())['reviews']
        self.assertEqual({r['identity'] for r in reviews},set(EXPECTED)|GAPS)
        self.assertEqual({r['identity'] for r in reviews if r['status']=='candidate-mapped'},set(EXPECTED))
        for table in ('countries','organizations','sites','assets'):
            for identity,row in self.before['dictionaries'][table].items():
                self.assertEqual(self.after['dictionaries'][table][identity],row)
        for identity,old in self.before['dictionaries']['configurations'].items():
            new = self.after['dictionaries']['configurations'][identity]
            self.assertEqual(new.get('originalFacts',new['facts']),old.get('originalFacts',old['facts']))
            for key,value in old['facts'].items():
                if key not in ('currentPackAssetId','currentPackSpecific'):
                    self.assertEqual(new['facts'][key],value,(identity,key))
            for key,value in old['references'].items():
                if key!='visual':
                    self.assertEqual(new['references'][key],value,(identity,key))
        old_recipe = json.loads(HISTORICAL.read_bytes())
        new_recipe = json.loads((ROOT/'catalog/source.json').read_bytes())
        self.assertEqual(new_recipe['curations'][:-2],old_recipe['curations'])
        self.assertEqual([x['path'] for x in new_recipe['curations'][-2:]],
                         [str(CURATION),str(RADIAL_CURATION)])
        self.assertEqual(new_recipe['curations'][-2]['sha256'],
                         '7f3d109f094d367b51c89d833cf28c299d4846c383cdaae74b2b4305635a13e7')
        old_lm5 = self.after['dictionaries']['assets']['spacefox:asset:further-r2-lm5-yz2-firstflight']
        self.assertEqual(old_lm5['facts']['sourceSha256'],
                         'fb3f18b7f3a92dcbc107076da134bc87f558f0616b27e2e40fca428d55b991aa')
        for key in ('reference','assetSeed','geography','visualBridge'):
            self.assertEqual(new_recipe[key],old_recipe[key])

    def test_all12_actual_export_cli_exact_identity_rights_and_geometry(self):
        wires = {}
        with tempfile.TemporaryDirectory() as tmp:
            for i,(identity,(name,asset)) in enumerate(EXPECTED.items()):
                output = Path(tmp)/str(i)
                manifest = self.export(ROOT/'catalog/source.json',output,identity)
                rows = manifest['selection']['dictionaries']['configurations']
                self.assertEqual(set(rows),{identity})
                row = rows[identity]
                self.assertEqual(row['facts']['fullName'],name)
                self.assertEqual(row['references']['visual'],asset)
                self.assertTrue(row['facts']['currentPackSpecific'])
                self.assertIsNone(row['references']['origin'])
                models = {k for k,v in manifest['assets'].items()
                          if v['catalogRecord']['seedCollection']=='models'}
                self.assertEqual(models,{asset})
                entry = manifest['assets'][asset]
                wire = assemble_visual([(output/s['path']).read_bytes()
                                        for s in entry['shards']],entry['animation'])
                self.assertEqual(wire[3],[64,128])
                self.assertLessEqual(len(wire[5]),4096)
                self.assertLessEqual(len(wire[6]),512)
                self.assertTrue(all((output/s['path']).stat().st_size<=4096
                                    for s in entry['shards']))
                self.assertEqual(hashlib.sha256(canonical_visual(wire)).hexdigest(),entry['sha256'])
                self.assertEqual(entry['rights']['license'],'MIT')
                self.assertIn('SpaceFox',entry['rights']['credit'])
                self.assertTrue(entry['catalogRecord']['facts']['sources'])
                self.assertEqual(entry['catalogRecord']['facts']['coverage']['configurationIds'],[identity])
                wires[identity]=entry['sha256']
        self.assertEqual(len(set(wires.values())),12)
        self.assertNotEqual(wires['ll2:configuration:536'],wires['ll2:configuration:537'])
        self.assertNotEqual(wires['ll2:configuration:383'],wires['ll2:configuration:384'])
        self.assertNotEqual(wires['ll2:configuration:384'],wires['ll2:configuration:385'])

    def test_cli_admission_reopen_retained_objects_and_atomic_refusal(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(Path(tmp)/'owner')
            source = root/'catalog/source.json'
            source.write_bytes(HISTORICAL.read_bytes())
            output = Path(tmp)/'visuals'
            old = self.export(source,output,'ll2:configuration:522')
            old_files = inventory(output)
            old_catalog = build_catalog(root)
            catalog_output = root/'build/catalog.json'
            admitted = execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,
                               '--amend',root/CURATION,'--catalog-version','literal.further.r2',
                               '--output',catalog_output)
            self.assertEqual(admitted.returncode,0,admitted.stderr)
            admitted = execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,
                               '--amend',root/RADIAL_CURATION,
                               '--catalog-version','literal.further.r2.radial',
                               '--output',catalog_output)
            self.assertEqual(admitted.returncode,0,admitted.stderr)
            reopened = build_catalog(root)
            self.assertEqual(catalog_output.read_bytes(),canonical_bytes(reopened))
            self.assertEqual(coverage_report(reopened)['configurations']['mappedArt'],156)
            new = self.export(source,output,'ll2:configuration:522')
            self.assertNotEqual(old['assets'],new['assets'])
            for path,data in old_files.items():
                if path!='manifest.json':
                    self.assertEqual((output/path).read_bytes(),data)
            for n in (30,511):
                m=self.export(source,Path(tmp)/str(n),f'll2:configuration:{n}')
                r=m['selection']['dictionaries']['configurations'][f'll2:configuration:{n}']
                self.assertEqual(r['references']['visual'],'spacefox:asset:generic')
                self.assertFalse(r['facts']['currentPackSpecific'])
                self.assertIsNone(r['references']['origin'])
            for table in ('countries','organizations','sites'):
                self.assertEqual(reopened['dictionaries'][table],old_catalog['dictionaries'][table])
            accepted=(source.read_bytes(),catalog_output.read_bytes(),inventory(output))
            bad={'schemaVersion':1,'id':'rejected-further-r2','reviewedAt':'2026-11-12',
                 'sources':['https://www.spacex.com/vehicles/starship'],
                 'reason':'Isolated atomic refusal discriminator.','assets':[],'additions':[],
                 'updates':[{'identity':'ll2:configuration:522','changes':{'name':'MUST NOT ACTIVATE'}},
                            {'identity':'ll2:configuration:30','changes':{'currentPackAssetId':'further-r2-starship-v3-2026','currentPackSpecific':True}}]}
            path=root/'rejected.json';path.write_bytes(canonical_bytes(bad))
            rejected=execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,
                             '--amend',path,'--catalog-version','rejected.next','--output',catalog_output)
            self.assertEqual(rejected.returncode,1)
            self.assertIn('art not reviewed for this exact configuration',rejected.stderr)
            self.assertEqual((source.read_bytes(),catalog_output.read_bytes(),inventory(output)),accepted)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))
            rights=loads_json((root/CURATION).read_bytes())
            rights['id']='rejected-rights-further-r2'
            rights['assets']=[copy.deepcopy(rights['assets'][0])]
            rights['assets'][0]['facts']['license']='unknown'
            rights['assets'][0]['facts']['id']='rejected-rights-asset'
            rights['updates']=[{'identity':'ll2:configuration:383','changes':{'currentPackAssetId':'rejected-rights-asset','currentPackSpecific':True}}]
            path.write_bytes(canonical_bytes(rights))
            rejected=execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,
                             '--amend',path,'--catalog-version','rejected.rights','--output',catalog_output)
            self.assertEqual(rejected.returncode,1)
            self.assertEqual((source.read_bytes(),catalog_output.read_bytes(),inventory(output)),accepted)
            refused=execute(ROOT/'tools/export_visuals.py','--source',source,'--output',output,
                            '--root','configuration:522')
            self.assertEqual(refused.returncode,1)
            self.assertEqual(inventory(output),accepted[2])


if __name__=='__main__':
    unittest.main()
