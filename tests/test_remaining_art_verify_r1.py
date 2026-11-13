"""Independent literal identities and actual CLI/filesystem producer witnesses.

The catalog source and original SVG files are real, copied to an isolated local
directory for mutation. No provider, publisher, SDK or native boundary is proved.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from tests.test_global_catalog import temporary_catalog
from tools.spacefox.catalog import build_catalog, canonical_bytes, coverage_report
from tools.spacefox.graphics import assemble_visual, canonical_visual

ROOT = Path(__file__).resolve().parents[1]
CURATION = Path('assets/global/curation-20261112-remaining-r1.json')
HISTORICAL = ROOT/'tests/fixtures/catalog/global-before-remaining-art-source.json'
# This independent oracle names every expected exact input ID and artwork ID.
# It is deliberately not derived from the curation or author review tables.
EXPECTED = {
    46:'proton-m-dm03', 109:'shared-lm7-yz1a', 115:'epsilon-s-block1',
    192:'smart-dragon1', 193:'hyperbola1-14', 194:'kuaizhou11', 216:'lm7a',
    474:'hapith1', 478:'lm6a', 484:'smart-dragon3-335', 492:'tianlong2',
    499:'sr75', 504:'shared-angara-a5-breezem', 507:'kairos', 508:'lm5b-yz2',
    509:'miura5-current', 510:'lm6c-335', 517:'lm12-52', 518:'lm8a',
    521:'soyuz5-411', 526:'astra4', 531:'sl1', 532:'vikram1',
    533:'nova-pathfinder', 535:'baguette-one', 538:'lm12a', 543:'hyperbola3',
    544:'gravity2', 546:'ceres2', 547:'maia-reusable', 548:'vega-c-block2',
    549:'vega-e', 551:'alpha-block2', 554:'lm10b', 556:'zhuque2e-block2',
}
EXPECTED = {f'll2:configuration:{key}':'spacefox:asset:remaining-r1-'+value for key,value in EXPECTED.items()}
EXPECTED['spacefox:configuration:miura9'] = 'spacefox:asset:remaining-r1-miura9'


def execute(*args):
    return subprocess.run([sys.executable,'-B',*map(str,args)], cwd=tempfile.gettempdir(),
                          capture_output=True, text=True, timeout=120)


def inventory(directory):
    return {str(p.relative_to(directory)):p.read_bytes() for p in directory.rglob('*') if p.is_file()}


class RemainingArtIndependentR1Test(unittest.TestCase):
    def export(self, source, output, roots):
        args = [ROOT/'tools/export_visuals.py','--source',source,'--output',output]
        for identity in roots:
            args += ['--root',identity]
        result = execute(*args)
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads((output/'manifest.json').read_bytes())

    def test_all36_public_export_exact_selection_and_shared_copy_pins(self):
        identities = list(EXPECTED)
        with tempfile.TemporaryDirectory() as tmp:
            # Rich source/curation metadata reaches the unchanged byte cap
            # before the 16-root cardinality cap. This is a bounded selection.
            refused = execute(ROOT/'tools/export_visuals.py','--output',Path(tmp)/'too-rich',
                               *[arg for identity in identities[:12] for arg in ('--root',identity)])
            self.assertEqual(refused.returncode,1)
            self.assertIn('selection manifest byte limit',refused.stderr)
            self.assertFalse((Path(tmp)/'too-rich').exists())
            # The face selects one configuration. Exercise that public port
            # for each identity; multi-model bulk export is not this contract.
            for offset, identity in enumerate(identities):
                roots = [identity]
                output = Path(tmp)/f'selection-{offset}'
                manifest = self.export(ROOT/'catalog/source.json',output,roots)
                rows = manifest['selection']['dictionaries']['configurations']
                self.assertEqual(set(rows),set(roots))
                models = {asset for asset,entry in manifest['assets'].items()
                          if entry['catalogRecord']['seedCollection'] == 'models'}
                self.assertEqual(models,{EXPECTED[x] for x in roots})
                for identity in roots:
                    with self.subTest(identity=identity):
                        asset = EXPECTED[identity]
                        self.assertEqual(rows[identity]['references']['visual'],asset)
                        self.assertTrue(rows[identity]['facts']['currentPackSpecific'])
                        self.assertIsNone(rows[identity]['references']['origin'])
                        entry = manifest['assets'][asset]
                        parts = [(output/s['path']).read_bytes() for s in entry['shards']]
                        wire = assemble_visual(parts,entry['animation'])
                        self.assertEqual(hashlib.sha256(canonical_visual(wire)).hexdigest(),entry['sha256'])
                        self.assertEqual(entry['rights']['license'],'MIT')
                        self.assertIn('SpaceFox',entry['rights']['credit'])
                        self.assertTrue(entry['catalogRecord']['facts']['sources'])
        c = build_catalog(ROOT)
        for new_id, old_model in [('shared-lm7-yz1a',100),('shared-angara-a5-breezem',73)]:
            new = c['dictionaries']['assets']['spacefox:asset:remaining-r1-'+new_id]
            old_visual = c['dictionaries']['configurations'][f'll2:configuration:{old_model}']['references']['visual']
            old = c['dictionaries']['assets'][old_visual]
            self.assertNotEqual(new['facts']['id'],old['facts']['id'])
            self.assertEqual((ROOT/new['content']['path']).read_bytes(),(ROOT/old['content']['path']).read_bytes())
            self.assertEqual(new['content']['sha256'],old['content']['sha256'])

    def test_actual_curation_cli_reopen_and_rejected_update_preserve_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(Path(tmp)/'catalog-owner')
            source = root/'catalog/source.json'
            source.write_bytes(HISTORICAL.read_bytes())
            before = build_catalog(root)
            initial_output = Path(tmp)/'visual-output'
            old_manifest = self.export(source,initial_output,['ll2:configuration:194','ll2:configuration:511','ll2:configuration:30'])
            old_files = inventory(initial_output)
            self.assertEqual(old_manifest['selection']['dictionaries']['configurations']['ll2:configuration:194']['references']['visual'],'spacefox:asset:generic')
            catalog_output = root/'build/reopened-catalog.json'
            admitted = execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,
                               '--amend',root/CURATION,'--catalog-version','independent.literal.remaining.1','--output',catalog_output)
            self.assertEqual(admitted.returncode,0,admitted.stderr)
            reopened = build_catalog(root)
            self.assertEqual(catalog_output.read_bytes(),canonical_bytes(reopened))
            self.assertEqual(coverage_report(reopened)['configurations']['mappedArt'],144)
            for identity, asset in EXPECTED.items():
                self.assertEqual(reopened['dictionaries']['configurations'][identity]['references']['visual'],asset)
            new_manifest = self.export(source,initial_output,['ll2:configuration:194','ll2:configuration:511','ll2:configuration:30'])
            self.assertNotEqual(old_manifest['assets'],new_manifest['assets'])
            for path,raw in old_files.items():
                if path != 'manifest.json':
                    self.assertEqual((initial_output/path).read_bytes(),raw)
            for identity in ('ll2:configuration:511','ll2:configuration:30'):
                row = new_manifest['selection']['dictionaries']['configurations'][identity]
                self.assertFalse(row['facts']['currentPackSpecific'])
                self.assertEqual(row['references']['visual'],'spacefox:asset:generic')
                self.assertIsNone(row['references']['origin'])
            kz = new_manifest['selection']['dictionaries']['configurations']['ll2:configuration:194']
            self.assertEqual(kz['references']['manufacturer'],'ll2:organization:194')
            self.assertEqual(kz['references']['manufacturerCountries'],['ll2:country:6'])
            self.assertIsNone(kz['references']['origin'])
            for table in ('countries','organizations','sites'):
                self.assertEqual(reopened['dictionaries'][table],before['dictionaries'][table])
            # A valid earlier change followed by a wrong-model final change
            # must leave recipe, previously generated catalog and output intact.
            bad = {'schemaVersion':1,'id':'independent-rejected-late-row','reviewedAt':'2026-11-12',
                   'sources':['https://www.cnsa.gov.cn/'], 'reason':'Isolated atomic rejection witness.',
                   'assets':[], 'additions':[], 'updates':[
                       {'identity':'ll2:configuration:194','changes':{'name':'MUST NOT ACTIVATE'}},
                       {'identity':'ll2:configuration:30','changes':{'currentPackAssetId':'remaining-r1-kuaizhou11','currentPackSpecific':True}}]}
            candidate = root/'rejected.json';candidate.write_bytes(canonical_bytes(bad))
            accepted_recipe, accepted_catalog, accepted_output = source.read_bytes(), catalog_output.read_bytes(), inventory(initial_output)
            rejected = execute(ROOT/'tools/catalog.py','--repo',root,'--source',source,'--amend',candidate,
                               '--catalog-version','independent.literal.remaining.rejected','--output',catalog_output)
            self.assertEqual(rejected.returncode,1)
            self.assertIn('art not reviewed for this exact configuration',rejected.stderr)
            self.assertEqual(source.read_bytes(),accepted_recipe)
            self.assertEqual(catalog_output.read_bytes(),accepted_catalog)
            self.assertEqual(inventory(initial_output),accepted_output)
            self.assertFalse(list((root/'catalog').glob('.recipe-*')))
            # The actual export CLI must reject a malformed typed selection
            # before changing an already accepted manifest or object store.
            rejected = execute(ROOT/'tools/export_visuals.py','--source',source,'--output',initial_output,'--root','configuration:194')
            self.assertEqual(rejected.returncode,1)
            self.assertEqual(inventory(initial_output),accepted_output)


if __name__ == '__main__':
    unittest.main()
