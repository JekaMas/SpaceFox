"""Finite remaining-art admission through the maintained catalog and SFV ports.

Primary-source shape accuracy is a separately recorded visual review. These
checks prove data admission, exact identity, unchanged facts and bounded export;
they do not substitute for source review, worldwide coverage or native output.
"""
import copy
import hashlib
from pathlib import Path
import tempfile
import unittest

from tools.catalog import amend_recipe
from tools.spacefox.catalog import (CatalogError, build_catalog, canonical_bytes,
                                    coverage_report, loads_json, validate_catalog)
from tools.spacefox.graphics import (LIMITS, VisualError, assemble_visual,
                                     build_pack, canonical_visual, write_pack)
from tests.test_global_catalog import temporary_catalog, supplement, save_revision

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'openspec/changes/spacefox-watchface/evidence/remaining-art/r1'
HISTORICAL = ROOT/'tests/fixtures/catalog/global-before-remaining-art-source.json'
CURATION = ROOT/'assets/global/curation-20261112-remaining-r1.json'
NEW_IDS = {f'll2:configuration:{x}' for x in (
    46, 109, 115, 192, 193, 194, 216, 474, 478, 484, 492, 499, 504, 507, 508,
    509, 510, 517, 518, 521, 526, 531, 532, 533, 535, 538, 543, 544,
    546, 547, 548, 549, 551, 554, 556)} | {'spacefox:configuration:miura9'}
GAP_IDS = {f'll2:configuration:{x}' for x in (
    30, 39, 44, 74, 86, 94, 96, 123, 139, 142, 152, 196, 197, 200,
    217, 383, 384, 385, 480, 495, 502, 505, 522, 534, 536, 537, 545)}


class RemainingArtTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = build_catalog(ROOT)
        cls.previous = build_catalog(ROOT, HISTORICAL)
        cls.curation = loads_json(CURATION.read_bytes())

    def test_finite_reviews_and_unchanged_facts_positive(self):
        before = coverage_report(self.previous)
        after = coverage_report(self.current)
        self.assertEqual((before['counts']['assets'], before['configurations']['mappedArt']), (562, 108))
        self.assertEqual((after['counts']['assets'], after['configurations']['mappedArt']), (598, 144))
        self.assertEqual(after['configurations']['requiredNonPlaceholder'], 171)
        self.assertEqual(set(before['configurations']['missingArtIds']), NEW_IDS | GAP_IDS)
        self.assertEqual(set(after['configurations']['missingArtIds']), GAP_IDS)
        self.assertEqual({x['identity'] for x in self.curation['updates']}, NEW_IDS)
        research = loads_json((EVIDENCE/'research-review.json').read_bytes())
        self.assertEqual({x['identity'] for x in research['reviews']}, NEW_IDS | GAP_IDS)
        self.assertEqual(len(research['reviews']), 63)
        self.assertEqual({x['identity'] for x in research['reviews'] if x['status'] == 'mapped'}, NEW_IDS)
        self.assertEqual({x['identity'] for x in research['reviews'] if x['status'] == 'open'}, GAP_IDS)
        for table in ('countries', 'organizations', 'sites', 'assets'):
            for identity, row in self.previous['dictionaries'][table].items():
                self.assertEqual(self.current['dictionaries'][table][identity], row)
        for identity, old in self.previous['dictionaries']['configurations'].items():
            new = self.current['dictionaries']['configurations'][identity]
            self.assertEqual(new.get('originalFacts', new['facts']), old.get('originalFacts', old['facts']))
            for key, value in old['facts'].items():
                if key not in ('currentPackAssetId', 'currentPackSpecific'):
                    self.assertEqual(new['facts'][key], value, (identity, key))
            for key, value in old['references'].items():
                if key != 'visual':
                    self.assertEqual(new['references'][key], value, (identity, key))
        recipe = loads_json((ROOT/'catalog/source.json').read_bytes())
        previous_recipe = loads_json(HISTORICAL.read_bytes())
        for key in ('reference', 'assetSeed', 'geography', 'visualBridge'):
            self.assertEqual(recipe[key], previous_recipe[key])

    def test_all_new_geometry_and_exact_selector_positive(self):
        digests = {}
        for asset in self.curation['assets']:
            facts = asset['facts']; identity = 'spacefox:asset:'+facts['id']
            with self.subTest(asset=identity):
                pack = build_pack(ROOT, self.current, roots=[identity])
                entry = pack['manifest']['assets'][identity]
                wire = assemble_visual([pack['objects'][x['sha256']] for x in entry['shards']], entry['animation'])
                self.assertEqual(hashlib.sha256(canonical_visual(wire)).hexdigest(), entry['sha256'])
                self.assertEqual(wire[3], [64, 128])
                self.assertLessEqual(len(wire[6]), 512)
                self.assertLessEqual(len(wire[5]), 4096)
                self.assertLessEqual(max(len(x) for x in pack['objects'].values()), 4096)
                self.assertLessEqual(len(canonical_bytes(pack['manifest']))+sum(map(len, pack['objects'].values())), 1048576)
                self.assertEqual(entry['rights']['license'], 'MIT')
                self.assertEqual(entry['catalogRecord']['facts']['sourceSha256'], facts['sourceSha256'])
                self.assertEqual(set(facts['coverage']['configurationIds']) & NEW_IDS,
                                 {x['identity'] for x in self.curation['updates'] if x['changes']['currentPackAssetId'] == facts['id']})
                digests[facts['id']] = entry['sha256']
        for left, right in [('miura5-current', 'miura9'), ('smart-dragon1', 'smart-dragon3-335'),
                            ('lm12-52', 'lm12a'), ('hyperbola1-14', 'hyperbola3')]:
            self.assertNotEqual(digests['remaining-r1-'+left], digests['remaining-r1-'+right])
        self.assertEqual(LIMITS['selectionRoots'], 16)
        self.assertEqual(LIMITS['canvasPixels'], 256)

    def test_known_unknown_unmapped_and_retained_selectors_positive(self):
        roots = ['ll2:configuration:194', 'll2:configuration:511', 'll2:configuration:30', 'll2:organization:183']
        current = build_pack(ROOT, self.current, roots=roots)
        old = build_pack(ROOT, self.previous, roots=roots)
        rows = current['manifest']['selection']['dictionaries']
        kz = rows['configurations']['ll2:configuration:194']
        self.assertEqual(kz['references']['visual'], 'spacefox:asset:remaining-r1-kuaizhou11')
        self.assertEqual(kz['references']['manufacturer'], 'll2:organization:194')
        self.assertEqual(kz['references']['manufacturerCountries'], ['ll2:country:6'])
        self.assertIsNone(kz['references']['origin'])
        self.assertIsNone(rows['organizations']['ll2:organization:183']['references']['badge'])
        for identity in ('ll2:configuration:511', 'll2:configuration:30'):
            row = rows['configurations'][identity]
            self.assertFalse(row['facts']['currentPackSpecific'])
            self.assertEqual(row['references']['visual'], 'spacefox:asset:generic')
            self.assertIsNone(row['references']['origin'])
        self.assertEqual(old['manifest']['selection']['dictionaries']['configurations']['ll2:configuration:194']['references']['visual'], 'spacefox:asset:generic')
        # A retained recipe and unrelated selected geometry remain byte-identical.
        for identity in ('ll2:configuration:164', 'll2:configuration:100', 'll2:configuration:73'):
            a = build_pack(ROOT, self.previous, roots=[identity])
            b = build_pack(ROOT, self.current, roots=[identity])
            self.assertEqual(a['objects'], b['objects'])
            self.assertEqual(a['manifest']['selection']['dictionaries'], b['manifest']['selection']['dictionaries'])

    def test_mismatched_identity_unknown_roots_and_fallback_negative(self):
        for roots in ([], ['configuration:194'], ['ll2:configuration:999999'], [194]):
            with self.subTest(roots=roots), self.assertRaises(VisualError):
                build_pack(ROOT, self.current, roots=roots)
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp); source = root/'catalog/source.json'; before = source.read_bytes()
            for name, identity, changes in (
                ('wrong-exact-model', 'll2:configuration:194', {'currentPackAssetId':'remaining-r1-hyperbola1-14', 'currentPackSpecific':True}),
                ('false-fallback-coverage', 'll2:configuration:30', {'currentPackAssetId':'generic', 'currentPackSpecific':True})):
                revision = supplement(name); revision['updates'] = [{'identity':identity, 'changes':changes}]
                with self.subTest(name=name), self.assertRaises(CatalogError):
                    amend_recipe(root, source, save_revision(root, revision), 'refused.'+name)
                self.assertEqual(source.read_bytes(), before)

    def test_rights_and_malformed_shape_atomic_negative(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp); source = root/'catalog/source.json'; before = source.read_bytes()
            for name, license_value, svg in (
                ('rights', 'unknown', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 128"><path d="M32 8L40 116L24 116Z" fill="#fff"/></svg>'),
                ('external-image', 'MIT', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 128"><image href="https://invalid.example/official-photo.jpg"/></svg>'),
                ('zero-area', 'MIT', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 128"><path d="M1 1L2 2L3 3Z" fill="#fff"/></svg>')):
                revision = supplement('negative-'+name)
                asset = copy.deepcopy(self.curation['assets'][0]); facts = asset['facts']
                file = root/('negative-'+name+'.svg'); file.write_text(svg)
                facts.update(id='0-negative-'+name, file=file.name, license=license_value,
                             sourceSha256=hashlib.sha256(file.read_bytes()).hexdigest())
                facts['coverage']['configurationIds'] = ['ll2:configuration:194']
                revision['assets'] = [asset]
                revision['updates'] = [{'identity':'ll2:configuration:194', 'changes':{'currentPackAssetId':facts['id'], 'currentPackSpecific':True}}]
                with self.subTest(name=name), self.assertRaises((CatalogError, VisualError)):
                    amend_recipe(root, source, save_revision(root, revision), 'refused.'+name)
                self.assertEqual(source.read_bytes(), before)
                self.assertFalse(list((root/'catalog').glob('.recipe-*')))

    def test_data_only_replacement_reopen_new_generation_positive(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = temporary_catalog(tmp); source = root/'catalog/source.json'
            retained_recipe = root/'retained-recipe.json'; retained_recipe.write_bytes(source.read_bytes())
            before = build_catalog(root); selected_before = build_pack(root, before, roots=['ll2:configuration:194'])
            output = root/'export'; first = write_pack(output, selected_before)
            original = canonical_bytes(before['dictionaries']['configurations']['ll2:configuration:194']['originalFacts'])
            revision = supplement('literal-remaining-replacement')
            asset = copy.deepcopy(self.curation['assets'][0]); facts = asset['facts']
            file = root/'literal-replacement.svg'
            file.write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 128"><path d="M32 8L40 116L24 116Z" fill="#abcdef"/></svg>')
            facts.update(id='literal-remaining-replacement', file=file.name,
                         sourceSha256=hashlib.sha256(file.read_bytes()).hexdigest())
            facts['coverage'] = {'type':'specific', 'configurationIds':['ll2:configuration:194'],
                                 'features':['Literal test triangle, not accepted vehicle art.'],
                                 'limitations':'Isolated production-port test input only; no source-accuracy or artwork acceptance claim.'}
            revision['assets'] = [asset]
            revision['updates'] = [{'identity':'ll2:configuration:194', 'changes':{'currentPackAssetId':facts['id'], 'currentPackSpecific':True}}]
            amend_recipe(root, source, save_revision(root, revision), 'literal.remaining.next')
            reopened = build_catalog(root)
            self.assertEqual(reopened['catalogVersion'], 'literal.remaining.next')
            self.assertEqual(canonical_bytes(reopened['dictionaries']['configurations']['ll2:configuration:194']['originalFacts']), original)
            selected_after = build_pack(root, reopened, roots=['ll2:configuration:194'])
            second = write_pack(output, selected_after)
            self.assertNotEqual(first['manifestSha256'], second['manifestSha256'])
            self.assertNotEqual(selected_before['objects'], selected_after['objects'])
            self.assertEqual((output/'manifest.json').read_bytes(), canonical_bytes(selected_after['manifest']))
            for digest, data in selected_before['objects'].items():
                self.assertEqual((output/'objects'/(digest+'.json')).read_bytes(), data)
            retained = build_catalog(root, retained_recipe)
            self.assertEqual(build_pack(root, retained, roots=['ll2:configuration:194'])['objects'], selected_before['objects'])
            validate_catalog(reopened)


if __name__ == '__main__':
    unittest.main()
